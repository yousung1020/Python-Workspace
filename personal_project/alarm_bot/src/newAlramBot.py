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
import os
import json
import tempfile
from dotenv import load_dotenv

# 프로젝트 루트 경로 (src/의 상위 디렉터리, .env와 bot_data/의 기준 위치)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 환경변수 파일 불러오기
env_path = os.path.join(BASE_DIR, ".env")
load_dotenv(env_path)

# 로깅 사전 설정
logger = logging.getLogger("alarm_bot") # logger 객체 생성
logger.setLevel(logging.INFO) # 로그 레벨 설정
handler = TimedRotatingFileHandler("bot_log/alarm_bot.log", when="midnight", interval=1, backupCount=5, encoding="utf-8") # time rotate handler 설정
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s') # 로그 포맷팅
handler.setFormatter(formatter)
logger.addHandler(handler)

# Discord 봇 토큰 및 채널 ID를 환경변수에서 불러오는 함수
def get_required_channel_id(env_name):
    channel_id = os.getenv(env_name)

    if channel_id is None or channel_id.strip() == "":
        raise RuntimeError(f"{env_name} 환경변수가 없습니다.")

    try:
        return int(channel_id)
    except ValueError:
        raise RuntimeError(f"{env_name} 환경변수는 숫자여야 합니다.")


token = os.getenv("DISCORD_BOT_TOKEN")

if token is None or token.strip() == "":
    raise RuntimeError("DISCORD_BOT_TOKEN 환경변수가 없습니다.")

token = token.strip()

channel_id_config = {
    "test": get_required_channel_id("TEST_CHANNEL_ID"),
    "ice": get_required_channel_id("ICE_CHANNEL_ID"),
    "cse": get_required_channel_id("CSE_CHANNEL_ID"),
    "menu_ice": get_required_channel_id("MENU_ICE_CHANNEL_ID"),
    "menu_cse": get_required_channel_id("MENU_CSE_CHANNEL_ID")
}

# 공지사항 상태 파일 경로 설정
notice_state_file = os.getenv(
    "NOTICE_STATE_FILE",
    os.path.join(BASE_DIR, "bot_data", "notice_state.json")
)

if not os.path.isabs(notice_state_file):
    notice_state_file = os.path.join(BASE_DIR, notice_state_file)

# 봇 인스턴스 생성
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)


# 환경변수로 설정된 Discord 채널을 불러오는 함수
def get_configured_channel(channel_id, channel_name):
    channel = bot.get_channel(channel_id)

    if channel is None:
        raise RuntimeError(f"{channel_name} 채널을 찾지 못했습니다. 채널 ID를 확인해주세요.")

    return channel


# 공지사항 상태를 불러오는 함수
def load_notice_state(board_name):
    if not os.path.exists(notice_state_file):
        return None

    try:
        with open(notice_state_file, "r", encoding="utf-8") as state_file:
            state = json.load(state_file)

        if not isinstance(state, dict):
            raise json.JSONDecodeError("상태 파일 형식이 올바르지 않습니다.", "", 0)

        if not isinstance(state.get("boards", {}), dict):
            raise json.JSONDecodeError("게시판 상태 형식이 올바르지 않습니다.", "", 0)

        return state.get("boards", {}).get(board_name)

    except (OSError, json.JSONDecodeError) as err:
        logger.error(f"{board_name} 공지사항 상태 파일을 읽지 못했습니다: {str(err)}")
        return None


# 공지사항 상태를 저장하는 함수
def save_notice_state(board_name, board_state):
    state_directory = os.path.dirname(notice_state_file)
    os.makedirs(state_directory, exist_ok=True)

    state = {"version": 1, "boards": {}}

    if os.path.exists(notice_state_file):
        try:
            with open(notice_state_file, "r", encoding="utf-8") as state_file:
                state = json.load(state_file)

            if not isinstance(state, dict):
                state = {"version": 1, "boards": {}}
        except (OSError, json.JSONDecodeError) as err:
            logger.error(f"기존 공지사항 상태 파일을 읽지 못했습니다: {str(err)}")
            state = {"version": 1, "boards": {}}

    state.setdefault("version", 1)
    state.setdefault("boards", {})
    state["boards"][board_name] = board_state

    temporary_file = None

    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=state_directory,
            prefix="notice_state_",
            suffix=".tmp",
            delete=False
        ) as state_file:
            json.dump(state, state_file, ensure_ascii=False, indent=2)
            temporary_file = state_file.name

        os.replace(temporary_file, notice_state_file)

    except OSError as err:
        logger.error(f"{board_name} 공지사항 상태 파일을 저장하지 못했습니다: {str(err)}")

        if temporary_file is not None and os.path.exists(temporary_file):
            os.remove(temporary_file)

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
    
    # 공지사항 목록의 행을 추출하는 함수
    def get_notice_rows(self, soup_notice):
        # 공지사항 테이블을 먼저 찾고, 없으면 모든 tr 태그를 찾음
        notice_table = soup_notice.select_one("table.board-table")

        if notice_table is None:
            notice_rows = soup_notice.find_all("tr")
        else:
            notice_rows = notice_table.find_all("tr")

        valid_rows = []

        for row in notice_rows:
            number_cell = row.find("td", attrs={"class": "td-num"})

            if number_cell is None:
                continue

            notice_number = re.sub(r"\s+", "", number_cell.get_text())

            # 고정 공지의 '공지' 행은 제외하고 숫자형 공지만 추출
            if notice_number.isdigit():
                valid_rows.append(row)

        if not valid_rows:
            raise ValueError("공지사항 행을 찾지 못했습니다.")

        return valid_rows

    # 공지사항 목록의 고유 정보들을 추출하는 함수
    def get_notice_list(self, soup_notice):
        notice_rows = self.get_notice_rows(soup_notice)
        notice_list = []

        for row in notice_rows:
            number_cell = row.find("td", attrs={"class": "td-num"})
            subject_cell = row.find("td", attrs={"class": "td-subject"})
            notice_link = row.find("a", href=True)

            if number_cell is None or subject_cell is None or notice_link is None:
                raise ValueError("공지사항 필수 정보를 찾지 못했습니다.")

            number = re.sub(r"\s+", "", number_cell.get_text())
            href = notice_link["href"]

            if self.name == "대학":
                title_cell = row.find("strong")

                if title_cell is None:
                    title_cell = subject_cell

                title = re.sub(r"\s+", " ", title_cell.get_text()).strip()

                if href.startswith("http"):
                    notice_url = href
                else:
                    notice_url = f"https://www.dongyang.ac.kr{href}"

                notice_url += "&layout=unknown" if "?" in notice_url else "?layout=unknown"

            else:
                title = re.sub(r"\s+", " ", subject_cell.get_text()).strip()
                js_splits = re.findall("'([^']*)'", href)

                if len(js_splits) < 4:
                    raise ValueError("학과 공지 URL 정보를 해석하지 못했습니다.")

                notice_url = f"https://www.dongyang.ac.kr/combBbs/{js_splits[0]}/{js_splits[1]}/{js_splits[3]}/view.do?layout=unknown"

            notice_list.append({
                "id": href,
                "number": number,
                "title": title,
                "url": notice_url
            })

        return notice_list

    # 대학 공지 url 및 제목을 추출하는 함수
    async def get_univer_notice_info(self, notice):
        title_university = f"📜 제목: {notice['title']}"
        link1_after = f"\n{notice['url']} \n"
        banner_university = f"📌 새로운 {self.name} 공지가 올라왔습니다! 📌\n\n"

        for channel in self.channelIds:
            await channel.send(banner_university + title_university + link1_after)

    # 학과 공지 url 및 제목을 추출하는 함수
    async def get_major_notice_info(self, notice):
        title_major = f"📜 제목: {notice['title']}"
        link2 = f"\n{notice['url']} \n"
        banner_major = f"📌 새로운 {self.name} 공지가 올라왔습니다! 📌\n\n"

        for channel in self.channelIds:
            await channel.send(banner_major + title_major + link2)

    # 신규 공지를 오래된 순서대로 보내는 함수
    async def send_new_notices(self, notices):
        if len(notices) > 1:
            for channel in self.channelIds:
                await channel.send(f"📌 {len(notices)}개의 새로운 {self.name} 공지를 순서대로 전송합니다. 📌")

        # 공지사항 페이지는 최신 공지부터 표시되므로 역순으로 전송
        for notice in reversed(notices):
            if self.name == "대학":
                await self.get_univer_notice_info(notice)
            else:
                await self.get_major_notice_info(notice)

            await asyncio.sleep(1)

    # 이전 공지사항과 현재 공지사항의 차이를 계산하는 함수
    def get_notice_changes(self, previous_notices, current_notices):
        previous_ids = {notice["id"] for notice in previous_notices}
        current_ids = {notice["id"] for notice in current_notices}

        new_notices = [
            notice for notice in current_notices
            if notice["id"] not in previous_ids
        ]
        missing_notices = [
            notice for notice in previous_notices
            if notice["id"] not in current_ids
        ]

        return new_notices, missing_notices

    # 삭제된 공지사항이 실제로 삭제되었는지 확인하는 함수
    async def check_notice_exists(self, notice):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    notice["url"],
                    timeout=aiohttp.ClientTimeout(total=30),
                    headers={"User-Agent": "Mozilla/5.0"}
                ) as responce:
                    html_info = await responce.text(errors="replace")

                    if responce.status == 404:
                        return False

                    if responce.status != 200:
                        return None

                    # 대학 게시판은 '원하시는 페이지를 찾을 수가 없습니다',
                    # 학과 게시판은 '게시물이(가) 없습니다.' 문구로 삭제된 글을 표시함
                    error_messages = [
                        "게시물에 접근할 수 없습니다",
                        "내용보기할 권한이 없습니다",
                        "존재하지 않는 게시물",
                        "페이지를 찾을 수 없습니다",
                        "페이지를 찾을 수가 없습니다",
                        "게시물이(가) 없습니다"
                    ]

                    for error_message in error_messages:
                        if error_message in html_info:
                            return False

                    # 공지 번호는 짧은 숫자라 페이지 어디에나 포함될 수 있으므로 제목으로만 확인
                    # 목록 제목과 같은 방식으로 공백(\xa0 포함)을 정규화한 뒤 비교
                    page_text = re.sub(r"\s+", " ", BeautifulSoup(html_info, "lxml").get_text(" ", strip=True))

                    if notice["title"] in page_text:
                        return True

                    return None

        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            logger.error(f"{self.name} 공지 삭제 여부 확인 중 오류가 발생하였습니다: {str(err)}")
            return None

    # 공지사항 목록을 주기적으로 확인하는 함수
    async def monitor_notices(self):
        saved_state = load_notice_state(self.name)

        if (
            saved_state is None
            or not isinstance(saved_state.get("notices"), list)
            or not saved_state.get("notices")
        ):
            previous_notices = None
            missing_candidates = {}
        else:
            previous_notices = saved_state.get("notices", [])
            missing_candidates = saved_state.get("missing_candidates", {})

            if not isinstance(missing_candidates, dict):
                missing_candidates = {}

        while True:
            await self.pause_night()

            try:
                async with aiohttp.ClientSession() as session:
                    html_info = await fetch(session, self.url, self.channelIds, self.name)

                soup_notice = BeautifulSoup(html_info, "lxml")
                current_notices = self.get_notice_list(soup_notice)

                # 최초 실행 시 현재 목록을 기준으로만 저장
                if previous_notices is None:
                    previous_notices = current_notices
                    missing_candidates = {}
                    save_notice_state(self.name, {
                        "notices": previous_notices,
                        "missing_candidates": missing_candidates,
                        "updated_at": datetime.now().isoformat(timespec="seconds")
                    })
                    logger.info(f"{self.name} 공지사항 초기 상태를 저장했습니다.")
                    await asyncio.sleep(60.0)
                    continue

                new_notices, missing_notices = self.get_notice_changes(
                    previous_notices,
                    current_notices
                )

                if new_notices:
                    await self.send_new_notices(new_notices)

                next_missing_candidates = {}
                pending_notices = []

                for previous_notice in missing_notices:
                    notice_id = previous_notice["id"]

                    notice_exists = await self.check_notice_exists(previous_notice)

                    if notice_exists is True:
                        # 첫 페이지에서 다음 페이지로 이동한 공지
                        continue

                    if notice_exists is False:
                        missing_count = int(missing_candidates.get(notice_id, 0)) + 1

                        if missing_count >= 2:
                            logger.info(f"📌 {previous_notice['number']}번 {self.name} 공지가 삭제되었습니다. 📌")

                            for channel in self.channelIds:
                                await channel.send(
                                    f"📌 {previous_notice['number']}번 {self.name} 공지가 삭제되었습니다. 📌\n"
                                )
                            continue

                        next_missing_candidates[notice_id] = missing_count
                        pending_notices.append(previous_notice)

                    else:
                        # 응답이 불확실하면 삭제로 판단하지 않음
                        next_missing_candidates[notice_id] = missing_candidates.get(notice_id, 0)
                        pending_notices.append(previous_notice)

                previous_notices = current_notices + pending_notices
                missing_candidates = next_missing_candidates

                save_notice_state(self.name, {
                    "notices": previous_notices,
                    "missing_candidates": missing_candidates,
                    "updated_at": datetime.now().isoformat(timespec="seconds")
                })

                logger.info(
                    f"현재 {self.name} 공지 이전 공지 수와 현재 공지 수\n"
                    f"{len(previous_notices)} || {len(current_notices)}"
                )

            except Exception as err_msg:
                logger.error(f"{self.name} 공지사항 확인 중 오류가 발생하였습니다: {str(err_msg)}")
                logger.error(traceback.format_exc())

            await asyncio.sleep(60.0)

    # 대학 공지에 대한 비동기 함수
    async def univer_notice(self):
        await self.monitor_notices()

    # 학과 공지(정통, 컴소과)에 대한 비동기 함수
    async def major_notice(self):
        await self.monitor_notices()
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
        channelId_for_error = get_configured_channel(channel_id_config["cse"], "컴소과")
        async with aiohttp.ClientSession() as session:
            meal_info = await fetch(session, "https://www.dongyang.ac.kr/dmu/4902/subview.do", channelId_for_error, "식단표 함수")

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

    # 환경변수에 설정된 채널 id로 채널을 불러옴
    channelId_for_test = get_configured_channel(channel_id_config["test"], "테스트")
    channelId_for_ice = get_configured_channel(channel_id_config["ice"], "정통과")
    channelId_for_cse = get_configured_channel(channel_id_config["cse"], "컴소과")

    # 식단표 메뉴를 보낼 채널 id 입력
    channelId_for_menu_ice = get_configured_channel(channel_id_config["menu_ice"], "정통과 식단표")
    channelId_for_menu_cse = get_configured_channel(channel_id_config["menu_cse"], "컴소과 식단표")

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
    channelId_for_test = get_configured_channel(channel_id_config["test"], "테스트")
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


# 테스트에서 모듈을 import할 때는 봇이 실행되지 않도록 직접 실행할 때만 봇을 가동
if __name__ == "__main__":
    bot.run(token)
