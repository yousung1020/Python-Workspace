import logging
from logging.handlers import TimedRotatingFileHandler
from multiprocessing.connection import Client
from bs4 import BeautifulSoup
from datetime import datetime, time
import discord
import re
import aiohttp
import asyncio
import traceback

# 로깅 사전 설정
logger = logging.getLogger("alarm_bot") # logger 객체 생성
logger.setLevel(logging.INFO) # 로그 레벨 설정
handler = TimedRotatingFileHandler("alarm_bot.log", when="midnight", interval=1, backupCount=5, encoding="utf-8") # time rotate handler 설정
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') # 로그 포맷팅
handler.setFormatter(formatter)
logger.addHandler(handler) 

# push 할 때는 꼭 토큰 삭제하기!
token = ''
clt = discord.Client(intents=discord.Intents.default())

# 비동기식 request에서 session을 받고 반환하는 함수
# 추가: 세션 연결에 실패하였을 경우 세 번을 더 세션 연결을 시도함
async def fetch(session, url):
    for attempt in range(3):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as responce:
                return await responce.text()
        except aiohttp.ClientConnectorError as err:
            logger.error(f"연결 오류가 발생하였습니다. : {err} (재시도: {attempt + 1} / 3)")
            asyncio.sleep(3)
    raise Exception("세션 연결에 실패하였습니다.")
        

# 대학 공지에 대한 비동기 함수
async def univer_notice(channels):
    while True:
        await pause_night()
        async with aiohttp.ClientSession() as session:
                html_info = await fetch(session, 'https://www.dongyang.ac.kr/dongyang/129/subview.do')
                soup_univer = BeautifulSoup(html_info, 'lxml')
                univer_num = soup_univer.find_all('tr', attrs={'class':''})
                univer_num.pop(0)
                univer_num = univer_num[0].find("td", class_="td-num").get_text()
                univer_num = int(univer_num)

                while True:
                    html_info_compared = await fetch(session, 'https://www.dongyang.ac.kr/dongyang/129/subview.do')
                    soup_univer_compared = BeautifulSoup(html_info_compared, 'lxml')
                    univer_num_compared = soup_univer_compared.find_all('tr', attrs={'class':''})
                    univer_num_compared.pop(0)
                    univer_num_compared = univer_num_compared[0].find().get_text()
                    univer_num_compared = int(univer_num_compared)
                    now = datetime.now()

                    print("-------------------------------------------------------------------------------------")
                    print("현재 univer_num 값과 univer_num_compared 값\n" + str(univer_num), "||", univer_num_compared, "||",now)
                    print("-------------------------------------------------------------------------------------\n")
                    logger.info(f"현재 univer_num 값과 univer_num_compared 값\n{univer_num} || {univer_num_compared}")

                    if (univer_num_compared == univer_num + 1):
                        # 대학 공지 제목 추출
                        title_univer = soup_univer_compared.find_all('tr', attrs={'class':''})
                        title_univer.pop(0)
                        title_raw_univer = title_univer[0].find('strong').get_text()
                        title_university = f"제목: {title_raw_univer}"

                        # 대학 공지 url 추출
                        a1 = title_univer[0].find('a')
                        link1_before = a1['href']
                        link1_after = f"\nhttps://www.dongyang.ac.kr{link1_before}?layout=unknown \n"
                        banner_university = "새로운 대학 공지가 올라왔습니다.\n\n"

                        for channel in channels:
                            await channel.send(banner_university + title_university + link1_after)
                        
                        break
                    
                    elif (univer_num_compared == univer_num - 1):
                        logger.info("대학 공지가 삭제되었습니다.")
                        
                        for channel in channels:
                            await channel.send("대학 공지가 삭제되었음\n")
                        break
                        
                    await asyncio.sleep(30.0)

# 학과 공지(컴소과)에 대한 비동기 함수
async def major_notice_CSE(channels):
    while True:
        await pause_night()
        async with aiohttp.ClientSession() as session:
                html_info = await fetch(session, 'http://www.dmu.ac.kr/dmu_23222/1797/subview.do')
                soup_major = BeautifulSoup(html_info, 'lxml')
                major_num = soup_major.find_all('tr', attrs={'class':""})
                major_num.pop(0)
                major_num.pop(0)
                major_num = int(major_num[0].find("td", class_="td-num").get_text().replace(" ", "").replace("\n", ""))
                now = datetime.now()

                while True:
                    html_info_compared = await fetch(session, 'http://www.dmu.ac.kr/dmu_23222/1797/subview.do')
                    soup_major_compared = BeautifulSoup(html_info_compared, 'lxml')
                    major_num_compared = soup_major_compared.find_all('tr', attrs={'class':''})
                    major_num_compared.pop(0)
                    major_num_compared.pop(0)
                    major_num_compared = int(major_num_compared[0].find("td", class_="td-num").get_text().replace(" ", "").replace("\n", ""))
                    

                    now = datetime.now()

                    print("-------------------------------------------------------------------------------------")
                    print("현재 컴소과 major_num 값과 major_num_compared 값\n" + str(major_num), "||", major_num_compared, "||",now)
                    print("-------------------------------------------------------------------------------------\n")
                    logger.info(f"현재 major_num 값과 major_num_compared 값\n{major_num} || {major_num}")

                    if (major_num_compared == major_num + 1):
                        # 학과 공지 제목 추출
                        title_major_raw = soup_major_compared.find('td', attrs={'class':'td-subject'})
                        divide = title_major_raw.get_text().split()

                        title_major = '제목: '
            
                        for i in divide:
                            title_major += i + ' '
                    
                        # 학과 공지 url 추출
                        tr2 = soup_major_compared.find_all('tr', attrs={'class':''})
                        tr2.pop(0)
                        tr2.pop(0)
                        a = tr2[0].find('a')
                        js_splits = re.findall("'([^']*)'", a['href'])
                        link2 = f"\nhttps://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown \n"
                        banner_major = "새로운 학과 공지가 올라왔습니다.\n\n"

                        for channel in channels:
                            await channel.send(banner_major + title_major + link2)

                        break

                    
                    elif (major_num_compared == major_num - 1):
                        logger.info("컴소과 학과 공지가 삭제되었습니다.")

                        for channel in channels:
                            await channel.send("학과 공지가 삭제되었음\n")
                        break

                    await asyncio.sleep(30.0)

# 학과 공지(정통과)에 대한 비동기 함수
async def major_notice_ICE(channels):
    while True:
        await pause_night()
        async with aiohttp.ClientSession() as session:
                html_info = await fetch(session, 'https://www.dongyang.ac.kr/dmu_23218/1776/subview.do')
                soup_major = BeautifulSoup(html_info, 'lxml')
                major_num = soup_major.find_all('tr', attrs={'class':""})
                major_num.pop(0)
                major_num = int(major_num[0].find().get_text().replace(" ", "").replace("\n", ""))
                
                now = datetime.now()

                while True:
                    html_info_compared = await fetch(session, 'https://www.dongyang.ac.kr/dmu_23218/1776/subview.do')
                    soup_major_compared = BeautifulSoup(html_info_compared, 'lxml')
                    major_num_compared = soup_major_compared.find_all('tr', attrs={'class':''})
                    major_num_compared.pop(0)
                    major_num_compared = major_num_compared[0].find().get_text()
                    major_num_compared = int(major_num_compared.replace(" ", "").replace("\n", ""))
                    
                    now = datetime.now()

                    print("-------------------------------------------------------------------------------------")
                    print("현재 정통과 major_num 값과 major_num_compared 값\n" + str(major_num), "||", major_num_compared, "||",now)
                    print("-------------------------------------------------------------------------------------\n")
                    logger.info(f"현재 major_num 값과 major_num_compared 값\n{major_num} || {major_num_compared}")

                    if (major_num_compared == major_num + 1):
                        # 학과 공지 제목 추출
                        title_major_raw = soup_major_compared.find('td', attrs={'class':'td-subject'})
                        divide = title_major_raw.get_text().split()

                        title_major = '제목: '
            
                        for i in divide:
                            title_major += i + ' '
                    
                        # 학과 공지 url 추출
                        tr2 = soup_major_compared.find_all('tr', attrs={'class':''})
                        tr2.pop(0)
                        a = tr2[0].find('a')
                        js_splits = re.findall("'([^']*)'", a['href'])
                        link2 = f"\nhttps://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown \n"
                        banner_major = "새로운 학과 공지가 올라왔습니다.\n\n"

                        for channel in channels:
                            await channel.send(banner_major + title_major + link2)

                        break
                    
                    elif (major_num_compared == major_num - 1):
                        logger.info("정통과 학과 공지가 삭제되었습니다.")

                        for channel in channels:
                            await channel.send("학과 공지가 삭제되었음\n")

                        break

                    await asyncio.sleep(30.0)

@clt.event
async def on_ready():
    # 채널 id 입력, 채널 변수가 더 필요할 경우 추가할 것
    channelId_forTEST = clt.get_channel()
    channelId_forICE = clt.get_channel() # 정통과 채널 id 입력
    channelId_forCSE = clt.get_channel() # 컴소과 채널 id 입력
    channelIds_univer = [channelId_forICE, channelId_forCSE] # 대학 공지를 보낼 채널 입력
    channelIds_CSE = [channelId_forCSE] # 정통과 공지를 보낼 채널 입력
    channelIds_ICE = [channelId_forICE] # 컴소과 공지를 보낼 채널 입력
    await channelId_forTEST.send("봇 준비 완료!")
    await clt.change_presence(status=discord.Status.online)
    await asyncio.sleep(3.0)
    try:
        await asyncio.gather(univer_notice(channelIds_univer), major_notice_CSE(channelIds_CSE), major_notice_ICE(channelIds_ICE))

    except Exception as err_msg:
        pass
        now = datetime.now()
        await channelId_forTEST.send("홀리쒯, 오류가 발생하였네요!!! 호다닥 확인을 해야겠죠?\n")
        print("오류가 발생하였습니다. 오류 메세지는 다음과 같습니다.\n" + str(err_msg))
        print("해당 오류가 발생한 시간:", now)
        print("해당 오류가 발생한 위치:")
        traceback.print_exc()
        logger.info(f"{err_msg} 오류가 발생하였습니다.")

clt.run(token)