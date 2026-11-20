"""첫 페이지에서 사라진 공지의 실제 삭제 여부 판정 테스트.

반환값: True(존재함, 다음 페이지로 밀림), False(삭제됨), None(판단 불가)
"""
import pytest

from conftest import CSE_LIST_URL, UNIV_LIST_URL, read_fixture

# 목록에서 추출한 제목은 공백(\xa0 포함)이 일반 공백으로 정규화되어 있음
DETAIL_TITLE = "2027학년도 컴퓨터소프트웨어공학과 학사학위전공심화과정 모집 설명회 안내"


def notice_for(url, title=DETAIL_TITLE, number="548"):
    return {"id": url, "number": number, "title": title, "url": url}


@pytest.mark.parametrize("name, list_url, fixture", [
    pytest.param("대학", UNIV_LIST_URL, "univ_deleted.html", id="univ-page-not-found"),
    pytest.param("컴소과", CSE_LIST_URL, "major_deleted.html", id="major-no-post"),
])
async def test_실제_삭제_안내_페이지는_삭제로_판정(make_notice, board_server, name, list_url, fixture):
    board_server.routes["/deleted"] = (200, read_fixture(fixture))
    notice = make_notice(name, list_url)

    assert await notice.check_notice_exists(notice_for(board_server.url("/deleted"))) is False


async def test_제목에_nbsp가_있는_실제_글은_존재로_판정(make_notice, board_server):
    detail_html = read_fixture("major_detail.html")
    assert "\xa0" in detail_html or "&nbsp;" in detail_html
    board_server.routes["/detail"] = (200, detail_html)
    notice = make_notice("컴소과", CSE_LIST_URL)

    assert await notice.check_notice_exists(notice_for(board_server.url("/detail"))) is True


async def test_공지_번호만_포함된_페이지는_존재로_판정하지_않음(make_notice, board_server):
    # 실제 페이지에는 메뉴·스크립트 등에 짧은 숫자가 많아 번호 검사는 오판정을 일으킴
    board_server.routes["/unknown"] = (200, "<html><body><div>548 5480 2026.11.20</div></body></html>")
    notice = make_notice("컴소과", CSE_LIST_URL)

    assert await notice.check_notice_exists(notice_for(board_server.url("/unknown"))) is None


async def test_HTTP_404는_삭제로_판정(make_notice, board_server):
    notice = make_notice("컴소과", CSE_LIST_URL)

    assert await notice.check_notice_exists(notice_for(board_server.url("/not-registered"))) is False


async def test_서버_오류는_판단_불가(make_notice, board_server):
    board_server.routes["/error"] = (500, "Internal Server Error")
    notice = make_notice("컴소과", CSE_LIST_URL)

    assert await notice.check_notice_exists(notice_for(board_server.url("/error"))) is None


async def test_연결_실패는_판단_불가(make_notice):
    notice = make_notice("컴소과", CSE_LIST_URL)

    # 1번 포트는 열려 있지 않으므로 즉시 연결 거부
    assert await notice.check_notice_exists(notice_for("http://127.0.0.1:1/detail")) is None
