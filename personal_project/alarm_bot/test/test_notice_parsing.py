"""게시판 목록 HTML에서 공지 정보를 추출하는 로직 테스트."""
import pytest
from bs4 import BeautifulSoup

from conftest import CSE_LIST_URL, ICE_LIST_URL, UNIV_LIST_URL, read_fixture


def parse(bot, name, url, html):
    notice = bot.Notice([], name, url)
    return notice.get_notice_list(BeautifulSoup(html, "lxml"))


BOARDS = [
    pytest.param(
        "대학", UNIV_LIST_URL, "univ_list.html",
        "5611", "[시설] 화재 관련 안전관리 및 예방 안내",
        "https://www.dongyang.ac.kr/bbs/dmu/677/252174/artclView.do?layout=unknown",
        id="univ",
    ),
    pytest.param(
        "컴소과", CSE_LIST_URL, "cse_list.html",
        "551", None,
        "https://www.dongyang.ac.kr/combBbs/dmu/84/252166/view.do?layout=unknown",
        id="cse",
    ),
    pytest.param(
        "정통과", ICE_LIST_URL, "ice_list.html",
        "921", None,
        "https://www.dongyang.ac.kr/combBbs/dmu/90/252155/view.do?layout=unknown",
        id="ice",
    ),
]


@pytest.mark.parametrize("name, url, fixture, top_number, top_title, top_url", BOARDS)
def test_최신_공지가_목록의_첫_번째로_추출됨(bot, name, url, fixture, top_number, top_title, top_url):
    notices = parse(bot, name, url, read_fixture(fixture))

    assert notices[0]["number"] == top_number
    assert notices[0]["url"] == top_url
    if top_title is not None:
        assert notices[0]["title"] == top_title


@pytest.mark.parametrize("name, url, fixture, top_number, top_title, top_url", BOARDS)
def test_목록_형식이_올바름(bot, name, url, fixture, top_number, top_title, top_url):
    notices = parse(bot, name, url, read_fixture(fixture))
    numbers = [int(notice["number"]) for notice in notices]

    assert len(notices) == 10
    assert numbers == sorted(numbers, reverse=True)
    assert len({notice["id"] for notice in notices}) == len(notices)
    assert all(notice["title"] for notice in notices)
    assert all("  " not in notice["title"] and "\xa0" not in notice["title"] for notice in notices)
    assert all(notice["url"].startswith("https://www.dongyang.ac.kr/") for notice in notices)
    assert all(notice["url"].endswith("layout=unknown") for notice in notices)


def test_대학_고정_공지_행은_제외됨(bot):
    html = read_fixture("univ_list.html")
    soup = BeautifulSoup(html, "lxml")
    pinned_rows = soup.select("tr.notice")
    notices = parse(bot, "대학", UNIV_LIST_URL, html)

    # 고정 공지는 일반 목록에도 같은 글로 다시 나오므로, 제외하지 않으면 중복 알림이 발생
    assert len(pinned_rows) == 5
    assert all(notice["number"].isdigit() for notice in notices)


def test_학과_공지_URL은_자바스크립트_링크에서_생성됨(bot):
    html = """
    <table class="board-table"><tbody>
      <tr class=""><td class="td-num">7</td>
        <td class="td-subject"><a href="javascript:jf_combBbs_view('dmu','84','320','111');"> 제목\xa0 테스트 </a></td>
      </tr>
    </tbody></table>
    """
    notices = parse(bot, "컴소과", CSE_LIST_URL, html)

    assert notices == [{
        "id": "javascript:jf_combBbs_view('dmu','84','320','111');",
        "number": "7",
        "title": "제목 테스트",
        "url": "https://www.dongyang.ac.kr/combBbs/dmu/84/111/view.do?layout=unknown",
    }]


def test_공지_행이_없으면_오류(bot):
    with pytest.raises(ValueError, match="공지사항 행을 찾지 못했습니다"):
        parse(bot, "컴소과", CSE_LIST_URL, "<html><body><p>점검 중</p></body></html>")


def test_공지_링크가_없으면_오류(bot):
    html = '<table class="board-table"><tr><td class="td-num">1</td><td class="td-subject">제목</td></tr></table>'

    with pytest.raises(ValueError, match="공지사항 필수 정보를 찾지 못했습니다"):
        parse(bot, "컴소과", CSE_LIST_URL, html)


def test_학과_링크_형식이_다르면_오류(bot):
    html = (
        '<table class="board-table"><tr><td class="td-num">1</td>'
        '<td class="td-subject"><a href="/view.do?id=1">제목</a></td></tr></table>'
    )

    with pytest.raises(ValueError, match="학과 공지 URL 정보를 해석하지 못했습니다"):
        parse(bot, "컴소과", CSE_LIST_URL, html)
