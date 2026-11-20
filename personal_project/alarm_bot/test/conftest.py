"""공지 알림 봇 테스트 공통 설정.

- newAlramBot.py를 import하기 전에 더미 환경변수와 로그 폴더를 준비합니다.
- 실제 .env의 토큰, 채널, 상태 파일은 사용하지 않습니다.
- 오프라인 테스트는 로컬 aiohttp 서버가 test/fixtures의 HTML을 응답합니다.
"""
import asyncio
import os
import sys
import tempfile
import types
from pathlib import Path

import pytest

TEST_DIR = Path(__file__).resolve().parent
BOT_DIR = TEST_DIR.parent / "src"
FIXTURES_DIR = TEST_DIR / "fixtures"

# python.org 설치본처럼 CA 저장소가 비어 있는 환경에서도 실서버 테스트가 가능하도록
# aiohttp를 import하기 전에 certifi 인증서 묶음을 지정
if "SSL_CERT_FILE" not in os.environ:
    try:
        import certifi

        os.environ["SSL_CERT_FILE"] = certifi.where()
    except ImportError:
        pass

# Python 3.13 이상에서는 discord.py 2.4.0이 audioop 모듈 부재로 import되지 않으므로,
# 이 경우에만 테스트에 필요한 최소한의 가짜 모듈로 대체
try:
    import discord  # noqa: F401
    from discord.ext import commands  # noqa: F401
except ImportError:
    discord_module = types.ModuleType("discord")
    ext_module = types.ModuleType("discord.ext")
    commands_module = types.ModuleType("discord.ext.commands")

    class _Intents:
        @staticmethod
        def default():
            return types.SimpleNamespace(message_content=False)

    class _Bot:
        def __init__(self, *args, **kwargs):
            pass

        def event(self, func):
            return func

        def command(self, *args, **kwargs):
            return lambda func: func

        def get_channel(self, channel_id):
            return None

    discord_module.Intents = _Intents
    discord_module.Status = types.SimpleNamespace(online="online")
    commands_module.Bot = _Bot
    ext_module.commands = commands_module
    discord_module.ext = ext_module
    sys.modules.update({
        "discord": discord_module,
        "discord.ext": ext_module,
        "discord.ext.commands": commands_module,
    })

# 실제 .env 값 대신 더미 값을 사용 (load_dotenv는 이미 설정된 값을 덮어쓰지 않음)
_import_dir = Path(tempfile.mkdtemp(prefix="alarm_bot_test_"))
os.environ.update({
    "DISCORD_BOT_TOKEN": "test-token",
    "TEST_CHANNEL_ID": "1",
    "ICE_CHANNEL_ID": "2",
    "CSE_CHANNEL_ID": "3",
    "MENU_ICE_CHANNEL_ID": "4",
    "MENU_CSE_CHANNEL_ID": "5",
    "NOTICE_STATE_FILE": str(_import_dir / "bot_data" / "notice_state.json"),
})

# 로그 핸들러가 상대 경로 bot_log/를 사용하므로 임시 폴더에서 import
(_import_dir / "bot_log").mkdir()
_original_cwd = os.getcwd()
sys.path.insert(0, str(BOT_DIR))
os.chdir(_import_dir)
try:
    import newAlramBot  # noqa: E402
finally:
    os.chdir(_original_cwd)

from aiohttp import web  # noqa: E402

UNIV_LIST_URL = "https://www.dongyang.ac.kr/dmu/4904/subview.do"
CSE_LIST_URL = "https://www.dongyang.ac.kr/dmu/4580/subview.do"
ICE_LIST_URL = "https://www.dongyang.ac.kr/dmu/4543/subview.do"


class FakeChannel:
    """Discord 채널 대신 전송된 메시지를 기록하는 객체."""

    def __init__(self):
        self.messages = []

    async def send(self, message):
        self.messages.append(message)


class StopMonitor(BaseException):
    """monitor_notices의 무한 루프를 끝내기 위한 예외.

    monitor_notices는 Exception을 잡아 기록하므로 BaseException을 상속합니다.
    """


def read_fixture(name):
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


@pytest.fixture
def bot():
    return newAlramBot


@pytest.fixture(autouse=True)
def state_file(tmp_path, monkeypatch):
    """테스트마다 독립된 상태 파일을 사용."""
    path = tmp_path / "bot_data" / "notice_state.json"
    monkeypatch.setattr(newAlramBot, "notice_state_file", str(path))
    return path


@pytest.fixture
def channel():
    return FakeChannel()


@pytest.fixture
def make_notice(channel):
    """야간 중지 없이 동작하는 Notice 인스턴스를 생성."""

    def factory(name, url):
        notice = newAlramBot.Notice([channel], name, url)

        async def no_pause():
            return None

        notice.pause_night = no_pause
        return notice

    return factory


@pytest.fixture
async def board_server():
    """경로별 응답을 지정할 수 있는 로컬 게시판 서버.

    server.routes[path] = (status, html) 형태로 응답을 등록하고,
    server.url(path)로 요청 주소를 얻습니다. 등록되지 않은 경로는 404입니다.
    """
    routes = {}

    async def handler(request):
        status, body = routes.get(request.path, (404, "Not Found"))
        return web.Response(status=status, text=body, content_type="text/html")

    app = web.Application()
    app.router.add_route("GET", "/{tail:.*}", handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = site._server.sockets[0].getsockname()[1]

    server = types.SimpleNamespace(
        routes=routes,
        url=lambda path: f"http://127.0.0.1:{port}{path}",
    )
    yield server
    await runner.cleanup()


@pytest.fixture
def run_cycles(monkeypatch):
    """monitor_notices를 지정한 주기만큼 실행.

    60초 대기를 만날 때마다 한 주기로 세고, 그 밖의 대기는 즉시 넘어갑니다.
    """
    real_sleep = asyncio.sleep

    async def runner(notice, cycles):
        count = {"value": 0}

        async def fake_sleep(seconds, *args, **kwargs):
            if seconds == 60.0:
                count["value"] += 1
                if count["value"] >= cycles:
                    raise StopMonitor
            await real_sleep(0)

        monkeypatch.setattr(newAlramBot.asyncio, "sleep", fake_sleep)
        try:
            await notice.monitor_notices()
        except StopMonitor:
            pass
        finally:
            monkeypatch.setattr(newAlramBot.asyncio, "sleep", real_sleep)

    return runner
