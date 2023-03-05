from http import client
from multiprocessing.connection import Client
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime
import discord
import aiohttp

token = ''
clt = discord.Client(intents=discord.Intents.default())

@clt.event
async def on_message(msg):

    while True:

        # 탈출 조건 변수 값 초기화
        Escape_num_1 = 0
        Escape_num_2 = 0


        # 대학공지 url 입력
        url_1 = ''

        # 학과공지 url 
        url_2 = '' 
        
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
                print(i.text)
                break

        compare_text_3 = soup_2.find("td", attrs={"class":"td-num"})

        # 성공적으로 스크래핑이 되었는지 체크

        print(compare_text_1)
        print(compare_text_3.string)

        # 스크래핑한 텍스트와 10초 후 다시 스크래핑한 텍스트가 다르면 알람을 보내는 알고리즘

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
                    print(i.text)
                    break

            compare_text_4 = soup_2.find("td", attrs={"class":"td-num"})
            
            if (compare_text_1 == compare_text_2):
                time.sleep(1)
                print("학교 공지 넘버 값 비교:", compare_text_1, compare_text_2, "\n비교한 시간", now)

            else:
                channel = clt.get_channel(1041374554368520232) #  # 채널 id 입력
                await channel.send("새로운 대학 공지가 올라왔습니다! 공지사항 홈페이지를 참고해 주세요.\nhttps://www.dongyang.ac.kr/dongyang/129/subview.do")
                print("학교 공지가 올라온 시간: ", now)
                time.sleep(1)
                # 반복문 탈출 조건 변수 값 1
                Escape_num_1 = 1
            
            if(compare_text_3 == compare_text_4):
                time.sleep(1)
                print("학과 공지 넘버 값 비교:", compare_text_3.string, compare_text_4.string, "\n비교한 시간", now)
            
            else:
                channel = clt.get_channel() # 채널 id 입력

                title_raw = soup_2.find('td', attrs={'class':'td-subject'})
                divide = title_raw.get_text().split()
    
                title_major = '제목: '
    
                for index, ele in enumerate(divide):
                    
                    title_major += ele + ' '

                banner_major = '새로운 학과 공지가 올라왔다 멍!! 으르렁 안보면 물어버리겠다! 왈왈\n\n'
                url = '\nhttps://www.dongyang.ac.kr/dmu_23218/1776/subview.do'
                await channel.send(banner_major + title_major + url)
                
                print("학과 공지가 올라온 시간: ", now)
                time.sleep(1)
                # 반복문 탈출 조건 변수 값 2 
                Escape_num_2 = 2

            time.sleep(10)
clt.run(token)
