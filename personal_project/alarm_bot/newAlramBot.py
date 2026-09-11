import logging
from logging.handlers import TimedRotatingFileHandler
from multiprocessing.connection import Client
from bs4 import BeautifulSoup
from datetime import datetime, time, timedelta
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

# push 할 때는 꼭 토큰 값 삭제하기!
token = ''

# 봇 인스턴스 생성
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# 함수 중복 호출 방지 플래그
is_bot_ready = False

# 비동기식 request에서 session을 받고 반환하는 함수
# 추가: 세션 연결에 실패하였을 경우 다섯 번까지 세션 연결을 시도함
async def fetch(session, url, channelIds, name):
    # 오류 메세지를 보낼 채널 추출
    if isinstance(channelIds, (list, tuple)):
        error_channel = channelIds[0] if channelIds else None
    else:
        error_channel = channelIds

    for attempt in range(5):
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=30),
                headers={"User-Agent": "Mozilla/5.0"}
            ) as responce:
                html_info = await responce.text(errors="replace")

                # HTTP 오류 페이지를 정상적인 HTML로 잘못 파싱하지 않게 하기
                if responce.status != 200:
                    raise RuntimeError(
                        f"HTTP 상태 코드가 {responce.status}입니다. "
                        f"응답 길이: {len(html_info)}"
                    )

                if not html_info.strip():
                    raise RuntimeError("빈 응답을 받았습니다.")

                return html_info
                
        except (aiohttp.ClientError, RuntimeError) as err:
            logger.error(f"연결 또는 응답 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 5)\n오류가 발생된 함수: {name} 함수")
            if error_channel is not None:
                await error_channel.send(f"연결 또는 응답 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 5)\n오류가 발생된 함수: {name} 함수")
            await asyncio.sleep(15)
            
        except asyncio.TimeoutError as err:
            logger.error(f"타임아웃 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 5)\n오류가 발생된 함수: {name} 함수")
            if error_channel is not None:
                await error_channel.send(f"타임아웃 오류가 발생하였습니다. : {str(err)} (재시도: {attempt + 1} / 5)\n오류가 발생된 함수: {name} 함수")
            await asyncio.sleep(15)

    raise RuntimeError("세션 연결에 실패하였습니다.")

# -------------------------------------------------------------------------------------------------
# 공지사항 관련 항목들을 관리하는 클래스
class Notice:
    def __init__(self, channelIds, name, url):
        self.channelIds = channelIds
        self.name = name
        self.url = url

    # 저녁 10시부터 6시까지 코드가 멈추게끔 하는 함수
    async def pause_night(self):
        now = datetime.now().time()

        if time(22, 00) <= now or now <= time(6, 0):
            print("밤 10시부터 아침 6시까지 동작이 중지됩니다.")
            logger.info("밤 10시이므로 잠 자러 감")
            await asyncio.sleep(60 * 60 * 8 + 5) # 8시간 동안 중지
            print("아침 6시가 되었으므로 코드가 재개되었습니다.")
            logger.info("아침 6시이므로 일을 시작함")
        else:
            return
    
    # 대학 공지 url 및 제목을 추출하는 함수
    async def get_univer_notice_info(self, soup_univer_compared):

        # 대학 공지 제목 추출
        title_univer = soup_univer_compared.find_all('tr', attrs={'class':''})
        del title_univer[0]
        title_raw_univer = title_univer[0].find('strong').get_text().replace("\n", "")
        title_raw_univer = re.sub(r'\s+', ' ', title_raw_univer).strip()
        title_university = f"📜 제목: {title_raw_univer}"

        # 대학 공지 url 추출
        a1 = title_univer[0].find('a')
        link1_before = a1['href']
        link1_after = f"\nhttps://www.dongyang.ac.kr{link1_before}?layout=unknown \n"
        banner_university = f"📌 새로운 {self.name} 공지가 올라왔습니다! 📌\n\n"

        for channel in self.channelIds:
            await channel.send(banner_university + title_university + link1_after)

    # 학과 공지 url 및 제목을 추출하는 함수
    async def get_major_notice_info(self, soup_major_compared):

        major_info =  soup_major_compared.find_all('tr', attrs={'class':''})
        del major_info[0]

        # 학과 공지 제목 추출
        title_major_raw = major_info[0].find('td', attrs={'class':'td-subject'})
        divide = title_major_raw.get_text().split()

        title_major = "📜 제목: "
        
        for i in divide:
            title_major += i + ' '

        # 학과 공지 url 추출
        a = major_info[0].find('a')
        js_splits = re.findall("'([^']*)'", a['href'])
        link2 = f"\nhttps://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown \n"

        banner_major = f"📌 새로운 {self.name} 공지가 올라왔습니다! 📌\n\n"

        for channel in self.channelIds:
            await channel.send(banner_major + title_major + link2)

    # 대학 공지에 대한 비동기 함수
    async def univer_notice(self):
        while True:
            async with aiohttp.ClientSession() as session:
                html_info = await fetch(session, self.url, self.channelIds, self.name)

            soup_univer = BeautifulSoup(html_info, 'lxml')
            univer_num = soup_univer.find_all('tr', attrs={'class':''})
            del univer_num[0]
            univer_num = univer_num[0].find("td", class_="td-num").get_text()
            univer_num = int(univer_num)

            while True:
                await self.pause_night()
                
                async with aiohttp.ClientSession() as session:
                    html_info_compared = await fetch(session, self.url, self.channelIds, self.name)

                soup_univer_compared = BeautifulSoup(html_info_compared, 'lxml')
                univer_num_compared = soup_univer_compared.find_all('tr', attrs={'class':''})
                del univer_num_compared[0]
                univer_num_compared = univer_num_compared[0].find("td", class_="td-num").get_text()
                univer_num_compared = int(univer_num_compared)
                now = datetime.now()

                print("-------------------------------------------------------------------------------------")
                print(f"현재 {self.name} 공지 univer_num 값과 univer_num_compared 값\n" + str(univer_num), "||", univer_num_compared, "||",now)
                print("-------------------------------------------------------------------------------------\n")
                logger.info(f"현재 {self.name} 공지 univer_num 값과 univer_num_compared 값\n{univer_num} || {univer_num_compared}")

                if (univer_num_compared == univer_num + 1):
                    await self.get_univer_notice_info(soup_univer_compared)
                    break
                        
                elif(univer_num_compared > univer_num + 1):
                    target = int(univer_num_compared - univer_num)

                    await self.get_univer_notice_info(soup_univer_compared)
                    
                    for channel in self.channelIds:
                        await channel.send(f"📌 {target-1}개의 건너뛰어진 공지사항이 있습니다. 📌")

                    for i in range(target-1):
                        title_univer = soup_univer_compared.find_all('tr', attrs={'class':''})
                        title_univer.pop(0)
                        title_raw_univer = title_univer[i+1].find('strong').get_text()
                        title_university = f"제목: {title_raw_univer}"

                        a1 = title_univer[i+1].find('a')
                        link1_before = a1['href']
                        link1_after = f"\nhttps://www.dongyang.ac.kr{link1_before}?layout=unknown \n"
                        banner_university = "📌 새로운 대학 공지가 올라왔습니다! 📌\n\n"

                        for channel in self.channelIds:
                            await channel.send(banner_university + title_university + link1_after)
                        await asyncio.sleep(1)

                    break

                elif (univer_num_compared < univer_num):
                    logger.info(f"📌 {univer_num}번 대학 공지가 삭제되었습니다. 📌")
                        
                    for channel in self.channelIds:
                        await channel.send(f"📌 {univer_num}번 대학 공지가 삭제되었습니다. 📌\n")
                    break
                        
                await asyncio.sleep(60.0)
            await asyncio.sleep(5)

    # 학과 공지(정통, 컴소과)에 대한 비동기 함수
    async def major_notice(self):
        while True:
            async with aiohttp.ClientSession() as session:
                html_info = await fetch(session, self.url, self.channelIds, self.name)

            soup_major = BeautifulSoup(html_info, 'lxml')
            major_num = soup_major.find_all('tr', attrs={'class':""})
            del major_num[0]
            major_num = int(major_num[0].find("td", class_="td-num").get_text().replace(" ", "").replace("\n", ""))
            now = datetime.now()

            while True:
                await self.pause_night()

                async with aiohttp.ClientSession() as session:
                    html_info_compared = await fetch(session, self.url, self.channelIds, self.name)

                soup_major_compared = BeautifulSoup(html_info_compared, 'lxml')
                major_num_compared = soup_major_compared.find_all('tr', attrs={'class':''})
                del major_num_compared[0]
                major_num_compared = int(major_num_compared[0].find("td", class_="td-num").get_text().replace(" ", "").replace("\n", ""))
                
                now = datetime.now()

                print("-------------------------------------------------------------------------------------")
                print(f"현재 {self.name} 공지 major_num 값과 major_num_compared 값\n" + str(major_num), "||", major_num_compared, "||",now)
                print("-------------------------------------------------------------------------------------\n")
                logger.info(f"현재 {self.name} 공지 major_num 값과 major_num_compared 값\n{major_num} || {major_num}")

                if (major_num_compared == major_num + 1):
                    await self.get_major_notice_info(soup_major_compared)
                    break

                elif(major_num_compared > major_num + 1):
                    target = int(major_num_compared - major_num)

                    await self.get_major_notice_info(soup_major_compared)

                    for channel in self.channelIds:
                        await channel.send(f"📌 안내: {target-1}개의 건너뛰어진 공지사항이 있습니다. 📌")

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

                        for channel in self.channelIds:
                            await channel.send(banner_major + title_major + link2)

                        await asyncio.sleep(1)

                    break
                    
                elif (major_num_compared < major_num):
                    logger.info(f"📌 {major_num}번 {self.name} 공지가 삭제되었습니다. 📌")

                    for channel in self.channelIds:
                        await channel.send(f"📌 {major_num}번 {self.name} 공지가 삭제되었습니다. 📌\n")

                    break

                await asyncio.sleep(60.0)
            await asyncio.sleep(5)
# ------------------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------------------
# 식단표 HTML 구조를 확인하고 한식 메뉴 행을 추출하는 함수
def get_korean_menu_info(soup_meal):
    # 식단표 테이블 추출
    table_meal = soup_meal.select_one(".dietWrap .table_1 table")

    if table_meal is None:
        raise ValueError("식단표 테이블을 찾지 못했습니다.")

    # 식단표의 요일 헤더 추출
    headers_meal = table_meal.select("thead th")

    if not headers_meal:
        raise ValueError("식단표 요일 헤더를 찾지 못했습니다.")

    # 한식 메뉴 제목 다음에 있는 메뉴 행 추출
    rows_meal = table_meal.select("tbody tr")
    korean_menu_row = None

    for i, row in enumerate(rows_meal):
        title = row.find("td", attrs={"class": "tit"})

        if title is not None and "한식 메뉴" in title.get_text(" ", strip=True):
            if i + 1 < len(rows_meal):
                korean_menu_row = rows_meal[i + 1]
            break

    if korean_menu_row is None:
        raise ValueError("한식 메뉴 행을 찾지 못했습니다.")

    menu_cells = korean_menu_row.find_all("td", recursive=False)

    if len(menu_cells) != len(headers_meal):
        raise ValueError(
            f"요일 수와 메뉴 셀 수가 다릅니다. 요일: {len(headers_meal)}, 메뉴: {len(menu_cells)}"
        )

    return headers_meal, menu_cells


# 식단표 알림 기능을 하는 클래스
class Menu:
    def __init__(self, channelIds):
        self.channelIds = channelIds

    # 채널에 보낼 식단 메세지 비동기 함수
    async def menu_msg_format(self, menu):
        menu = ("🍚 오늘의 한식 메뉴! 🍚\n"
                f"```{menu}```")
        return menu

    # 식단 메뉴에 대한 비동기 함수
    async def today_menu(self):
        channelId_for_test = bot.get_channel(1350807050162274327) # 여기에 테스트 채널 id 입력
        async with aiohttp.ClientSession() as session:
            meal_info = await fetch(session, "https://www.dongyang.ac.kr/dmu/4902/subview.do", channelId_for_test, "식단표 함수")

        soup_meal = BeautifulSoup(meal_info, "lxml")
        headers_meal, menu_cells = get_korean_menu_info(soup_meal)
        today = datetime.now().strftime("%Y.%m.%d")
        today_index = None

        for i, header in enumerate(headers_meal):
            if today in header.get_text(" ", strip=True):
                today_index = i
                break

        # 토요일과 일요일은 식단표에 해당 날짜 열이 없음
        if today_index is None:
            logger.info("오늘 날짜에 해당하는 식단표가 없습니다.")
            return

        meal_info = menu_cells[today_index].get_text(" ", strip=True).replace("[점심]", "").strip()

        if meal_info != "-" and meal_info:
            menu = await self.menu_msg_format(meal_info)
            for channel in self.channelIds:
                await channel.send(menu)
        
        else:
            for channel in self.channelIds:
                await channel.send("오늘은 한식 메뉴가 없습니다! 😱")

    # 하루에 한 번씩만 호출되게끔 하는 스케쥴링 함수
    async def schedule_today_meal(self):
        while True:
            now = datetime.now()
            target_time = datetime.combine(now.date(), time(9, 0))

            # 코드를 재가동 했을 때의 시간이 오전 9시 이후라면, 목표 시간을 다음 날로 설정
            if now >= target_time:
                target_time += timedelta(days=1)

            delay = (target_time - now).total_seconds()  # 다음 실행까지의 대기 시간(초 단위)
            print(str(float((delay / 60) / 60)) + "시간 기다린 후에 해당 식단표 함수 가동")
            await asyncio.sleep(delay)

            # 식단표 서버 오류 또는 HTML 구조 오류가 발생하면 당일에 다시 시도
            while True:
                try:
                    await self.today_menu()
                    break

                except Exception as err_msg:
                    logger.error(f"식단표 처리 중 오류가 발생하였습니다: {str(err_msg)}")
                    logger.error(traceback.format_exc())
                    await asyncio.sleep(10 * 60)
# --------------------------------------------------------------------------------------------------

@bot.event
async def on_ready():
    # 해당 함수의 중복 실행 방지
    global is_bot_ready
    if is_bot_ready:
        return
    is_bot_ready = True

    logger.info("on_ready 함수가 호출되었습니다.")

    # 채널 id 입력, 채널 변수가 더 필요할 경우 추가할 것
    channelId_for_test = bot.get_channel(1041374554368520232) # 테스트 채널 id 입력
    channelId_for_ice = bot.get_channel(1016710195398848524) # 정통과 채널 id 입력
    channelId_for_cse = bot.get_channel(1350807050162274327) # 컴소과 채널 id 입력

    # 식단표 메뉴를 보낼 채널 id 입력
    channelId_for_menu_ice = bot.get_channel(1344666105762943046) # 정통과 식단표 채널
    channelId_for_menu_cse = bot.get_channel(1350807234703265842) # 컴소과 식단표 채널

    channelIds_univer = [channelId_for_test, channelId_for_ice, channelId_for_cse] # 대학 공지를 보낼 채널 입력
    channelIds_CSE = [channelId_for_test, channelId_for_cse] # 컴소과 공지를 보낼 채널 입력
    channelIds_ICE = [channelId_for_test, channelId_for_ice] # 정통과 공지를 보낼 채널 입력
    channelIds_MENU = [channelId_for_test, channelId_for_menu_ice, channelId_for_menu_cse] # 식단표 메뉴를 보낼 채널 입력

    await channelId_for_test.send("봇 준비 완료!")
    await bot.change_presence(status=discord.Status.online)
    while True:
        try:
            # 인스턴스를 생성할 때: (채널 아이디, 이름, url) 순으로 인수 값 입력
            # 공지 관련 인스턴스
            univer_notice_instance = Notice(channelIds_univer, "대학", "https://www.dongyang.ac.kr/dmu/4904/subview.do")
            major_notice_CSE_instance = Notice(channelIds_CSE, "컴소과", "https://www.dongyang.ac.kr/dmu/4580/subview.do")
            major_notice_ICE_instance = Notice(channelIds_ICE, "정통과", "https://www.dongyang.ac.kr/dmu/4543/subview.do")

            # 식단 관련 인스턴스
            meal_instance = Menu(channelIds_MENU)

            # task 객체 생성
            tasks = [
                asyncio.create_task(univer_notice_instance.univer_notice()),
                asyncio.create_task(major_notice_CSE_instance.major_notice()),
                asyncio.create_task(major_notice_ICE_instance.major_notice()),
                asyncio.create_task(meal_instance.schedule_today_meal())
            ]

            await asyncio.sleep(1.0)
            await asyncio.gather(*tasks, return_exceptions=False)

        except Exception as err_msg:

            now = datetime.now()
            await channelId_for_test.send(f"홀리쒯, 오류가 발생하였네요!!! 호다닥 확인을 해야겠죠?\n힌트!: {str(err_msg)}")
            print("오류가 발생하였습니다. 오류 메세지는 다음과 같습니다.\n" + str(err_msg))
            print("해당 오류가 발생한 시간:", now)
            print("해당 오류가 발생한 위치:")
            traceback.print_exc()
            traceback_msg = traceback.format_exc()
            logger.info(f"{str(err_msg)} 오류가 발생하였습니다.")
            logger.error(f"TraceBack 정보: \n {traceback_msg}")
        
        finally:
            # 모든 task 취소
            for task in tasks:
                if not task.done():
                    task.cancel()

            for task in tasks:
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                
                except Exception:
                    pass
        
        logger.info("예외처리 후 함수를 재호출합니다.")
        await channelId_for_test.send("예외처리 후 함수를 재호출합니다.")
            
        
# !식단표 라는 명령어를 입력했을 때
@bot.command(name="식단표")
async def meal(ctx):
    channelId_for_test = bot.get_channel(1041374554368520232) # 여기에 테스트 채널 id 입력
    async with aiohttp.ClientSession() as session:
        meal_info = await fetch(session, "https://www.dongyang.ac.kr/dmu/4902/subview.do", channelId_for_test, "식단표 함수")

    soup_meal = BeautifulSoup(meal_info, "lxml")
    headers_meal, menu_cells = get_korean_menu_info(soup_meal)
    div_meal = []

    # 메뉴가 비어있으면 (-) 메뉴가 없다고 하기
    for i in menu_cells:
        menu = i.get_text(" ", strip=True).replace("[점심]", "").strip()

        if menu == "-" or not menu:
            div_meal.append("메뉴가 없습니다! 😱")
        else:
            div_meal.append(menu)

    info_msg = (
        "📌 이번주 식단표는 다음과 같습니다. 📌\n\n"
        "🔎 요일별 고정 메뉴!\n\n"
        "📝 월요일 ~ 금요일\n"
        "```라면 / 치즈 라면 / 해물짬뽕 라면 / 짜파게티 / 짜계치 & 공깃밥\n가격(순서대로): 3,500원 / 4,000원 / 4,500원 / 3,500원 / 4,000원```\n"
        "```불닭볶음면 / 까르보 불닭볶음면 / 치즈 불닭볶음면 & 계란후라이 & 공깃밥\n가격(순서대로): 3,500원 / 3,800원 / 4,000원 ```\n"
        "```돈까스, 치즈 돈까스, 통가슴살 치킨까스, 고구마 치즈 돈까스, 수제 왕 돈까스\n가격(순서대로): 5,000원 / 5,500원 / 5,200원 / 6,000원 / 6,000원```\n"
        "📝 월요일 ~ 화요일\n"
        "```스팸 김치 볶음밥\n가격: 4,900원```\n"
        "📝 수요일\n"
        "```치킨 마요 덮밥\n가격: 4,900원```\n"
        "```불닭 마요 덮밥\n가격: 4,900원```\n"
        "📝 목요일\n"
        "```삼겹살 덮밥\n가격: 5,500원```\n"
        "📝 금요일\n"
        "```장조림 버터 비빔밥\n가격: 4,500원```\n"
        "💸 한식 가격은 6,000원으로 고정입니다! 💸\n"
        "🍚 월요일 한식 🍚\n"
        f"```{div_meal[0]}```\n"
        "🍚 화요일 한식 🍚\n"
        f"```{div_meal[1]}```\n"
        "🍚 수요일 한식 🍚\n"
        f"```{div_meal[2]}```\n"
        "🍚 목요일 한식 🍚\n"
        f"```{div_meal[3]}```\n"
        "🍚 금요일 한식 🍚\n"
        f"```{div_meal[4]}```"
        )

    await ctx.send(info_msg)
bot.run(token)
