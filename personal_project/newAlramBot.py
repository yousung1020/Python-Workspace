import logging
from logging.handlers import TimedRotatingFileHandler
from multiprocessing.connection import Client
from bs4 import BeautifulSoup
from datetime import datetime, time
import discord
from discord.ext import commands
import re
import aiohttp
import asyncio
import traceback

# 로깅 사전 설정
logger = logging.getLogger("alarm_bot") # logger 객체 생성
logger.setLevel(logging.INFO) # 로그 레벨 설정
handler = TimedRotatingFileHandler("bot_log/alarm_bot.log", when="midnight", interval=1, backupCount=5, encoding="utf-8") # time rotate handler 설정
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') # 로그 포맷팅
handler.setFormatter(formatter)
logger.addHandler(handler)

# push 할 때는 꼭 토큰 삭제하기!
token = ''
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 저녁 10시부터 6시까지 코드가 멈추게끔 하는 함수
async def pause_night():
    while True:
        now = datetime.now().time()

        if time(22, 00) <= now or now <= time(6, 0):
            print("밤 10시부터 아침 6시까지 동작이 중지됩니다.")
            logger.info("밤 10시이므로 잠 자러 감")
            await asyncio.sleep(60 * 60 * 8 + 5) # 8시간 동안 중지
            print("아침 6시가 되었으므로 코드가 재개되었습니다.")
            logger.info("아침 6시이므로 일을 시작함")
        else:
            break

# 비동기식 request에서 session을 받고 반환하는 함수
# 추가: 세션 연결에 실패하였을 경우 세 번을 더 세션 연결을 시도함
async def fetch(session, url, channels, name):
    for attempt in range(5):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as responce:
                return await responce.text()
            
        except aiohttp.ClientConnectorError as err:
            logger.error(f"연결 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 3)\n오류가 발생된 함수: {name} 공지 함수")
            channels[0].send(f"연결 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 3)\n오류가 발생된 함수: {name} 공지 함수")
            await asyncio.sleep(15)
        
        except asyncio.TimeoutError as err:
            logger.error(f"타임아웃 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 3)\n오류가 발생된 함수: {name} 함수")
            await channels[0].send(f"타임아웃 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 3)\n오류가 발생된 함수: {name} 함수")
            await asyncio.sleep(15)

    raise Exception("세션 연결에 실패하였습니다.")

# 대학 공지 url 및 제목을 추출하는 함수
async def get_univer_notice_info(soup_univer_compared, channels):
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

# 학과 공지 url 및 제목을 추출하는 함수
async def get_major_notice_info(soup_major_compared, name, channels):
    # 학과 공지 제목 추출
    title_major_raw = soup_major_compared.find('td', attrs={'class':'td-subject'})
    divide = title_major_raw.get_text().split()

    title_major = '제목: '
    
    for i in divide:
        title_major += i + ' '

    # 학과 공지 url 추출
    tr2 = soup_major_compared.find_all('tr', attrs={'class':''})
    del tr2[0]
    a = tr2[0].find('a')
    js_splits = re.findall("'([^']*)'", a['href'])
    link2 = f"\nhttps://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown \n"

    banner_major = f"새로운 {name} 공지가 올라왔습니다.\n\n"

    for channel in channels:
        await channel.send(banner_major + title_major + link2)


# 대학 공지에 대한 비동기 함수
async def univer_notice(channels):
    while True:
        async with aiohttp.ClientSession() as session:
            html_info = await fetch(session, 'https://www.dongyang.ac.kr/dongyang/129/subview.do', channels, "대학")
            soup_univer = BeautifulSoup(html_info, 'lxml')
            univer_num = soup_univer.find_all('tr', attrs={'class':''})
            univer_num.pop(0)
            univer_num = univer_num[0].find("td", class_="td-num").get_text()
            univer_num = int(univer_num)

            while True:
                await pause_night()
                html_info_compared = await fetch(session, 'https://www.dongyang.ac.kr/dongyang/129/subview.do', channels, "대학")
                soup_univer_compared = BeautifulSoup(html_info_compared, 'lxml')
                univer_num_compared = soup_univer_compared.find_all('tr', attrs={'class':''})
                univer_num_compared.pop(0)
                univer_num_compared = univer_num_compared[0].find().get_text()
                univer_num_compared = int(univer_num_compared)
                now = datetime.now()

                print("-------------------------------------------------------------------------------------")
                print("현재 대학 공지 univer_num 값과 univer_num_compared 값\n" + str(univer_num), "||", univer_num_compared, "||",now)
                print("-------------------------------------------------------------------------------------\n")
                logger.info(f"현재 대학 공지 univer_num 값과 univer_num_compared 값\n{univer_num} || {univer_num_compared}")

                if (univer_num_compared == univer_num + 1):
                    await get_univer_notice_info(univer_num_compared, "대학", channels)
                    break
                    
                elif(univer_num_compared > univer_num + 1):
                    target = int(univer_num_compared - univer_num)

                    await get_univer_notice_info(univer_num_compared, "대학", channels)

                    #-------------------------------------------------------------------------
                    
                    for channel in channels:
                        await channel.send(f"{target-1}개의 건너뛰어진 공지사항이 있습니다.")

                    for i in range(target-1):
                        title_univer = soup_univer_compared.find_all('tr', attrs={'class':''})
                        title_univer.pop(0)
                        title_raw_univer = title_univer[i+1].find('strong').get_text()
                        title_university = f"제목: {title_raw_univer}"

                        a1 = title_univer[i+1].find('a')
                        link1_before = a1['href']
                        link1_after = f"\nhttps://www.dongyang.ac.kr{link1_before}?layout=unknown \n"
                        banner_university = "새로운 대학 공지가 올라왔습니다.\n\n"

                        for channel in channels:
                            await channel.send(banner_university + title_university + link1_after)
                        await asyncio.sleep(1)

                    break

                elif (univer_num_compared < univer_num):
                    logger.info(f"{univer_num}번 대학 공지가 삭제되었습니다.")
                        
                    for channel in channels:
                        await channel.send(f"{univer_num}번 대학 공지가 삭제되었습니다\n")
                    break
                        
                await asyncio.sleep(60.0)

# 학과 공지(정통, 컴소과)에 대한 비동기 함수
async def major_notice(channels, name, url):
    while True:
        async with aiohttp.ClientSession() as session:
            html_info = await fetch(session, url, channels, name)
            soup_major = BeautifulSoup(html_info, 'lxml')
            major_num = soup_major.find_all('tr', attrs={'class':""})
            major_num.pop(0)
            major_num = int(major_num[0].find("td", class_="td-num").get_text().replace(" ", "").replace("\n", ""))
            now = datetime.now()

            while True:
                await pause_night()
                html_info_compared = await fetch(session, url, channels, name)
                soup_major_compared = BeautifulSoup(html_info_compared, 'lxml')
                major_num_compared = soup_major_compared.find_all('tr', attrs={'class':''})
                major_num_compared.pop(0)
                major_num_compared = int(major_num_compared[0].find("td", class_="td-num").get_text().replace(" ", "").replace("\n", ""))
                
                now = datetime.now()

                print("-------------------------------------------------------------------------------------")
                print(f"현재 {name} 공지 major_num 값과 major_num_compared 값\n" + str(major_num), "||", major_num_compared, "||",now)
                print("-------------------------------------------------------------------------------------\n")
                logger.info(f"현재 {name} 공지 major_num 값과 major_num_compared 값\n{major_num} || {major_num}")

                if (major_num_compared == major_num + 1):
                    await get_major_notice_info(major_num_compared, name, channels)
                    break

                elif(major_num_compared > major_num + 1):
                    target = int(major_num_compared - major_num)

                    await get_major_notice_info(major_num_compared, name, channels)

                    # ------------------------------------------------------------

                    for channel in channels:
                        await channel.send(f"안내: {target-1}개의 건너뛰어진 공지사항이 있습니다.")

                    for i in range(target-1):

                        # 컴소과 공지 제목 추출
                        title_major_raw = soup_major_compared.find_all('td', attrs={'class':'td-subject'})
                        del title_major_raw[0]
                        divide = title_major_raw[i+1].get_text().split()

                        title_major = '제목: '
            
                        for j in divide:
                            title_major += j + ' '

                        # 컴소과 공지 url 추출
                        tr2 = soup_major_compared.find_all('tr', attrs={'class':''})
                        tr2.pop(0)
                        a = tr2[i+1].find('a')
                        js_splits = re.findall("'([^']*)'", a['href'])
                        link2 = f"\nhttps://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown \n"
                        banner_major = f"{i+1}.\n"

                        for channel in channels:
                            await channel.send(banner_major + title_major + link2)

                        await asyncio.sleep(1)

                    break
                    
                elif (major_num_compared < major_num):
                    logger.info(f"{major_num}번 {name} 공지가 삭제되었습니다.")

                    for channel in channels:
                        await channel.send(f"{major_num}번 {name} 공지가 삭제되었습니다\n")

                    break

                await asyncio.sleep(60.0)

@bot.event
async def on_ready():
    # 채널 id 입력, 채널 변수가 더 필요할 경우 추가할 것
    channelId_forTEST = bot.get_channel()
    channelId_forICE = bot.get_channel() # 정통과 채널 id 입력
    channelId_forCSE = bot.get_channel() # 컴소과 채널 id 입력
    channelIds_univer = [channelId_forTEST, channelId_forICE, channelId_forCSE] # 대학 공지를 보낼 채널 입력
    channelIds_CSE = [channelId_forTEST, channelId_forCSE] # 정통과 공지를 보낼 채널 입력
    channelIds_ICE = [channelId_forTEST, channelId_forICE] # 컴소과 공지를 보낼 채널 입력
    await channelId_forTEST.send("봇 준비 완료!")
    await bot.change_presence(status=discord.Status.online)
    await asyncio.sleep(1.0)
    try:
        await asyncio.gather(univer_notice(channelIds_univer), 
                            asyncio.sleep(0.5),
                            major_notice(channelIds_CSE, "컴소과", "http://www.dmu.ac.kr/dmu_23222/1797/subview.do"), # 학과 공지 함수의 인수: (채널 아이디, 학과 이름, 해당 학과 공지의 url)
                            asyncio.sleep(0.5),
                            major_notice(channelIds_ICE, "정통과", "http://www.dmu.ac.kr/dmu_23218/1776/subview.do"))

    except Exception as err_msg:
        now = datetime.now()
        await channelId_forTEST.send(f"홀리쒯, 오류가 발생하였네요!!! 호다닥 확인을 해야겠죠?\n힌트!: {str(err_msg)}")
        print("오류가 발생하였습니다. 오류 메세지는 다음과 같습니다.\n" + str(err_msg))
        print("해당 오류가 발생한 시간:", now)
        print("해당 오류가 발생한 위치:")
        traceback.print_exc()
        traceback_msg = traceback.format_exc()
        logger.info(f"{str(err_msg)} 오류가 발생하였습니다.")
        logger.error(f"TraceBack 정보: \n {traceback_msg}")
        pass

@bot.command(name="식단표")
async def meal(ctx):
    test_channel = bot.get_channel()
    async with aiohttp.ClientSession() as session:
        meal_info = await fetch(session, "http://www.dmu.ac.kr/dongyang/130/subview.do", test_channel, "식단표 함수수")
        soup_meal = BeautifulSoup(meal_info, "lxml")
        meal_info = soup_meal.find_all()

    info_msg = ("이번주 식단표는 다음과 같습니다.\n\n"
                "한식\n"
                )

bot.run(token)