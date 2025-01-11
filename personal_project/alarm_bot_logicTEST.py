from multiprocessing.connection import Client
from bs4 import BeautifulSoup
from datetime import datetime
import discord
import re
import aiohttp
import asyncio

# push 할 때는 꼭 토큰 삭제하기!
token = ''
clt = discord.Client(intents=discord.Intents.default())

# 비동기식 request에서 session을 받고 반환하는 함수
async def fetch(session, url):
    async with session.get(url) as responce:
        return await responce.text()

# 대학 공지에 대한 비동기 함수
async def univer_notice():
    channel = clt.get_channel() # 테스트 채널 id
    while True:
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

                    if (univer_num_compared == univer_num + 1):
                        # 대학 공지 제목 추출
                        title_univer = soup_univer_compared.find_all('tr', attrs={'class':''})
                        title_univer.pop(0)
                        title_raw_univer = title_univer[0].find('strong').get_text()
                        title_university = f"제목: {title_raw_univer}"

                        # 대학 공지 url 추출
                        a1 = title_univer[0].find('a')
                        link1_before = a1['href']
                        link1_after = f"\nhttps://www.dongyang.ac.kr{link1_before}?layout=unknown"
                        banner_university = "새로운 대학 공지가 올라왔다 멍!! 으르렁 안보면 물어버리겠다! 왈왈\n\n"

                        await channel.send(banner_university + title_university + link1_after)
                        
                        break
                    
                    elif (univer_num_compared == univer_num - 1):
                        with open("removed notice.txt", "a+", encoding="utf8") as report_file:
                            report_file.write("대학 공지가 삭제 되었음" + "\n")

                        await channel.send("대학 공지가 삭제되었음")    

                        break
                        
                    await asyncio.sleep(10.0)

# 학과 공지에 대한 비동기 함수
async def major_notice():
    channel = clt.get_channel() # 테스트 채널 id
    while True:
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
                    print("현재 major_num 값과 major_num_compared 값\n" + str(major_num), "||", major_num_compared, "||",now)
                    print("-------------------------------------------------------------------------------------\n")

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
                        link2 = f"\nhttps://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown"
                        banner_major = "새로운 학과 공지가 올라왔다 멍!! 으르렁 안보면 물어버리겠다! 왈왈\n\n"

                        await channel.send(banner_major + title_major + link2)

                        break
                    
                    elif (major_num_compared == major_num - 1):
                        with open("removed notice.txt", "a+", encoding="utf8") as report_file:
                            report_file.write("학과 공지가 삭제 되었음" + "\n")

                        await channel.send("학과 공지가 삭제되었음")
                        break

                    await asyncio.sleep(10.0)

@clt.event
async def on_ready():
    channel = clt.get_channel() # 테스트 채널 id
    await channel.send("봇 준비 완료!")
    await clt.change_presence(status=discord.Status.online)
    await asyncio.sleep(3.0)
    try:
        await asyncio.gather(univer_notice(), major_notice())

    except Exception as err_msg:
        pass
        now = datetime.now()
        print("오류가 발생하였습니다. 오류 메세지는 다음과 같습니다.\n" + str(err_msg))
        print("해당 오류가 발생한 시간:", now)
        with open("Error report.txt", "a+", encoding="utf8") as error_report:
            error_report.write(str(err_msg) + " 오류가 발생하였습니다." + "\n" )

clt.run(token)
