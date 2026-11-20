"""monitor_notices 주기 실행 테스트.

로컬 서버가 실제 게시판 목록 HTML을 응답하고, 상태 파일로 이전 주기의 목록을 지정합니다.
"""
import pytest
from bs4 import BeautifulSoup

from conftest import read_fixture
from test_check_notice_exists import DETAIL_TITLE

BOARDS = [
    pytest.param("대학", "univ_list.html", id="univ"),
    pytest.param("컴소과", "cse_list.html", id="cse"),
    pytest.param("정통과", "ice_list.html", id="ice"),
]


def parsed_notices(bot, name, fixture):
    return bot.Notice([], name, "").get_notice_list(BeautifulSoup(read_fixture(fixture), "lxml"))


def save_previous(bot, name, notices, missing_candidates=None):
    bot.save_notice_state(name, {
        "notices": notices,
        "missing_candidates": missing_candidates or {},
        "updated_at": "test",
    })


def alerts(channel):
    return [message for message in channel.messages if "제목:" in message]


@pytest.fixture
def board(board_server, make_notice):
    """목록 HTML을 /list로 응답하는 게시판 Notice 인스턴스를 생성."""

    def factory(name, fixture):
        board_server.routes["/list"] = (200, read_fixture(fixture))
        return make_notice(name, board_server.url("/list"))

    return factory


@pytest.mark.parametrize("name, fixture", BOARDS)
async def test_최초_실행은_상태만_저장하고_알림하지_않음(bot, board, channel, run_cycles, name, fixture):
    await run_cycles(board(name, fixture), cycles=1)

    assert channel.messages == []
    assert bot.load_notice_state(name)["notices"] == parsed_notices(bot, name, fixture)


@pytest.mark.parametrize("name, fixture", BOARDS)
async def test_새_공지를_오래된_순서로_정확히_전송(bot, board, channel, run_cycles, name, fixture):
    current = parsed_notices(bot, name, fixture)
    save_previous(bot, name, current[2:])

    await run_cycles(board(name, fixture), cycles=1)

    sent = alerts(channel)
    assert channel.messages[0] == f"📌 2개의 새로운 {name} 공지를 순서대로 전송합니다. 📌"
    assert len(sent) == 2
    # 하나씩 밀리지 않고, 각 메시지의 제목과 링크가 같은 공지를 가리켜야 함
    for message, expected in zip(sent, [current[1], current[0]]):
        assert f"📜 제목: {expected['title']}" in message
        assert expected["url"] in message


@pytest.mark.parametrize("name, fixture", BOARDS)
async def test_같은_공지는_다음_주기에_다시_보내지_않음(bot, board, channel, run_cycles, name, fixture):
    save_previous(bot, name, parsed_notices(bot, name, fixture)[1:])

    await run_cycles(board(name, fixture), cycles=3)

    assert len(alerts(channel)) == 1


async def test_번호만_바뀐_목록은_새_공지로_보지_않음(bot, board, channel, run_cycles):
    # 이전 버전 코드에서 직전 공지를 새 공지로 보내던 원인(번호 재계산)에 대한 회귀 테스트
    renumbered = [
        dict(notice, number=str(int(notice["number"]) - 1))
        for notice in parsed_notices(bot, "대학", "univ_list.html")
    ]
    save_previous(bot, "대학", renumbered)

    await run_cycles(board("대학", "univ_list.html"), cycles=1)

    assert channel.messages == []


async def test_삭제된_공지는_두_번_확인한_뒤_한_번만_알림(bot, board, board_server, channel, run_cycles):
    board_server.routes["/deleted"] = (200, read_fixture("major_deleted.html"))
    deleted = {"id": "deleted-post", "number": "521", "title": "삭제된 공지", "url": board_server.url("/deleted")}
    save_previous(bot, "컴소과", parsed_notices(bot, "컴소과", "cse_list.html") + [deleted])
    notice = board("컴소과", "cse_list.html")

    # 1주기: 한 번만 확인되었으므로 대기
    await run_cycles(notice, cycles=1)
    state = bot.load_notice_state("컴소과")
    assert channel.messages == []
    assert state["missing_candidates"] == {"deleted-post": 1}
    assert deleted in state["notices"]

    # 2주기: 두 번째 확인에서 삭제 알림 후 상태에서 제거
    await run_cycles(notice, cycles=1)
    state = bot.load_notice_state("컴소과")
    assert channel.messages == ["📌 521번 컴소과 공지가 삭제되었습니다. 📌\n"]
    assert state["missing_candidates"] == {}
    assert deleted not in state["notices"]

    # 3주기: 이미 처리한 공지는 다시 알리지 않음
    await run_cycles(notice, cycles=1)
    assert len(channel.messages) == 1


async def test_다음_페이지로_밀린_공지는_알림_없이_정리(bot, board, board_server, channel, run_cycles):
    board_server.routes["/detail"] = (200, read_fixture("major_detail.html"))
    moved = {"id": "moved-post", "number": "540", "title": DETAIL_TITLE, "url": board_server.url("/detail")}
    save_previous(bot, "컴소과", parsed_notices(bot, "컴소과", "cse_list.html") + [moved])

    await run_cycles(board("컴소과", "cse_list.html"), cycles=1)

    assert channel.messages == []
    assert moved not in bot.load_notice_state("컴소과")["notices"]


async def test_판단_불가한_공지는_삭제하지_않고_계속_추적(bot, board, board_server, channel, run_cycles):
    board_server.routes["/error"] = (500, "Internal Server Error")
    unknown = {"id": "unknown-post", "number": "540", "title": "확인 불가", "url": board_server.url("/error")}
    save_previous(bot, "컴소과", parsed_notices(bot, "컴소과", "cse_list.html") + [unknown], {"unknown-post": 1})

    await run_cycles(board("컴소과", "cse_list.html"), cycles=2)

    state = bot.load_notice_state("컴소과")
    assert channel.messages == []
    assert unknown in state["notices"]
    # 판단 불가는 삭제 확인 횟수를 늘리지도 줄이지도 않음
    assert state["missing_candidates"] == {"unknown-post": 1}


async def test_목록_파싱에_실패해도_상태를_유지하고_감시를_계속함(bot, board, board_server, channel, run_cycles):
    previous = parsed_notices(bot, "컴소과", "cse_list.html")
    save_previous(bot, "컴소과", previous)
    notice = board("컴소과", "cse_list.html")
    board_server.routes["/list"] = (200, "<html><body>점검 중</body></html>")

    await run_cycles(notice, cycles=2)

    assert channel.messages == []
    assert bot.load_notice_state("컴소과")["notices"] == previous
