from multiprocessing.connection import Client
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import discord
import re
import asyncio

# push 할 때는 꼭 토큰 삭제하기!
token = ''
clt = discord.Client(intents=discord.Intents.default())


async def test():
    channel = clt.get_channel(1042426467931398215) # 테스트 채널 id
    # channel_B = clt.get_channel(1045561219630780476) # B반 딧코 서버 id
    # channel_C = clt.get_channel(1016710195398848524) # C반 딧코 서버 id

    while True:
        try:
            # 탈출 조건 변수 값 초기화
            Escape_num_1 = 0
            Escape_num_2 = 0

            # 대학공지 url 입력
            url_1 = 'https://www.dongyang.ac.kr/dongyang/129/subview.do'

            # 학과공지 url 
            url_2 = 'https://www.dongyang.ac.kr/dmu_23218/1776/subview.do' 
            
            # 대학 공지에 대한 웹 스크래핑
            res_1 = requests.get(url_1)
            res_1.raise_for_status()
            soup = BeautifulSoup(res_1.text, "lxml")

            # 학과 공지에 대한 웹 스크래핑
            res_2 = requests.get(url_2)
            res_2.raise_for_status()
            soup_2 = BeautifulSoup(res_2.text, "lxml")

            # 대학공지와 학과공지의 비교 텍스트를 각각의 비교 할 변수에 저장
            # compare_1, 2 비교, 그 후  3, 4 각각 비교

            # 학교 공지인 경우 notice 공지와 일반공지가 나뉘어 있어, 비교 할 문자열을 추출 후 소거하는 방식으로 스크래핑

            compare_text_1 = 0
            Division = soup.find_all('td', attrs={'class':'td-num'})

            for i in Division:
                Str = i.find(string='일반공지')
                if Str == '일반공지':
                    continue
                else:
                    compare_text_1 = i.text
                    break

            compare_text_1 = int(compare_text_1) # 객체의 자료형이 tag형이기 때문에 정수형으로 변환 
            
            compare_text_3 = soup_2.find("td", attrs={"class":"td-num"})
            compare_text_3 = int(compare_text_3.string)
            

            # 성공적으로 스크래핑이 되었는지 체크

            print("현재 compare_text_1 값:", compare_text_1)
            print("현재 compare_text_3 값:", compare_text_3)

            # 스크래핑한 텍스트가 다시 스크래핑한 텍스트보다 1이 더 크면 알람을 보내는 알고리즘

            while True:
                now = datetime.now()
                if(Escape_num_1 == 1):
                    break
                elif(Escape_num_2 == 2):
                    break
                url_1 = 'https://www.dongyang.ac.kr/dongyang/129/subview.do'
                url_2 = 'https://www.dongyang.ac.kr/dmu_23218/1776/subview.do' 

                res_1 = requests.get(url_1)
                res_1.raise_for_status()
                soup = BeautifulSoup(res_1.text, "lxml")

                res_2 = requests.get(url_2)
                res_2.raise_for_status()
                soup_2 = BeautifulSoup(res_2.text, "lxml")

                compare_text_2 = 0
                Division = soup.find_all('td', attrs={'class':'td-num'})

                for i in Division:
                    Str = i.find(string='일반공지')
                    if Str == '일반공지':
                        continue
                    else:
                        compare_text_2 = i.text
                        break
                compare_text_2 = int(compare_text_2)
                print("현재 compare_text_2 값:", compare_text_2)

                compare_text_4 = soup_2.find("td", attrs={"class":"td-num"})
                compare_text_4 = int(compare_text_4.string)
                print("현재 compare_text_4 값:", compare_text_4)

                if (compare_text_2 == compare_text_1 + 1):

                    tr1 = soup.find_all('tr', class_="")
                    tr1.pop(0)
                    title1_raw = tr1[0].find('strong')
                    title_university = f"제목: {title1_raw.string}"

                    a1 = tr1[0].find('a')
                    link1_before = a1['href']
                    link1_after = f"\nhttps://www.dongyang.ac.kr{link1_before}?layout=unknown"

                    banner_university = "새로운 대학 공지가 올라왔다 멍!! 으르렁 안보면 물어버리겠다! 왈왈\n\n"

                    await channel.send(banner_university + title_university + link1_after)
                    # await channel_B.send(banner_university + title_university + link1_after)
                    # await channel_C.send(banner_university + title_university + link1_after)

                    print("학교 공지가 올라온 시간: ", now)
                    time.sleep(10)
                    # 반복문 탈출 조건 변수 값 1
                    Escape_num_1 = 1
                
                elif (compare_text_2 == compare_text_1 - 1):
                    
                    print("대학 공지가 삭제되었음을 알림")
                    print("대학 공지가 삭제된 시간:", now)

                    await channel.send("대학 공지가 삭제되었습니다.")

                    Escape_num_1 = 1

                else:
                    pass
                
                if (compare_text_4 == compare_text_3 + 1):

                    title2_raw = soup_2.find('td', attrs={'class':'td-subject'})
                    divide = title2_raw.get_text().split()
        
                    title_major = '제목: '
        
                    for index, ele in enumerate(divide):
                        
                        title_major += ele + ' '

                    tr2 = soup_2.find_all('tr', class_="")
                    tr2.pop(0)
                    a = tr2[0].find('a')
                    js_splits = re.findall("'([^']*)'", a['href'])
                    link2 = f"\nhttps://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown"

                    banner_major = '새로운 학과 공지가 올라왔다 멍!! 으르렁 안보면 물어버리겠다! 왈왈\n\n'

                    await channel.send(banner_major + title_major + link2)
                    # await channel_B.send(banner_major + title_major + link2)
                    # await channel_C.send(banner_major + title_major + link2)

                    print("학과 공지가 올라온 시간: ", now)
                    time.sleep(10)

                    # 반복문 탈출 조건 변수 값 2 
                    Escape_num_2 = 2
                
                elif (compare_text_4 == (compare_text_3 - 1)):
                    print("학과 공지가 삭제되었음을 알림")
                    print("학과 공지가 삭제된 시간:", now)

                    await channel.send("학과 공지가 삭제되었습니다.")

                    Escape_num_2 = 2
                    
                else:
                    pass

                await asyncio.sleep(3)

        except Exception as err_msg:
            pass
            print("오류가 발생하였습니다. 오류 메세지는 다음과 같습니다.\n" + str(err_msg))
            print("해당 오류가 발생한 시간:", now)

####
@clt.event
async def on_message(msg):
    await test()
####

####
@clt.event
async def on_ready():
    channel = clt.get_channel(1042426467931398215) # 테스트 채널 id
    # channel_B = clt.get_channel(1045561219630780476) # B반 딧코 서버 id
    # channel_C = clt.get_channel(1016710195398848524) # C반 딧코 서버 id

    await clt.change_presence(status=discord.Status.offline) #
    print("봇 준비 완료!")
    msg = "봇 준비 완료!"
    await channel.send(msg)
####
clt.run(token)
