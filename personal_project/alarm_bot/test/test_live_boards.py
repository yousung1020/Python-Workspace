"""실제 학교 게시판에 요청을 보내는 테스트.

기본 실행에서는 제외되며, `pytest test/ -m live`로 실행합니다.
게시판 HTML 구조나 삭제 안내 문구가 바뀌었는지 확인하는 용도입니다.
"""
import re

import aiohttp
import pytest
from bs4 import BeautifulSoup

from conftest import CSE_LIST_URL, ICE_LIST_URL, UNIV_LIST_URL

pytestmark = pytest.mark.live

BOARDS = [
    pytest.param("대학", UNIV_LIST_URL, id="univ"),
    pytest.param("컴소과", CSE_LIST_URL, id="cse"),
    pytest.param("정통과", ICE_LIST_URL, id="ice"),
]


async def fetch_notices(bot, notice):
    async with aiohttp.ClientSession() as session:
        html = await bot.fetch(session, notice.url, notice.channelIds, notice.name)
    return notice.get_notice_list(BeautifulSoup(html, "lxml"))


@pytest.mark.parametrize("name, url", BOARDS)
async def test_실제_게시판_목록을_파싱함(bot, make_notice, name, url):
    notices = await fetch_notices(bot, make_notice(name, url))
    numbers = [int(notice["number"]) for notice in notices]

    assert len(notices) >= 5
    assert numbers == sorted(numbers, reverse=True)
    assert len({notice["id"] for notice in notices}) == len(notices)


@pytest.mark.parametrize("name, url", BOARDS)
async def test_첫_페이지_공지는_모두_존재로_판정(bot, make_notice, name, url):
    notice = make_notice(name, url)
    notices = await fetch_notices(bot, notice)

    results = {item["number"]: await notice.check_notice_exists(item) for item in notices}

    assert all(result is True for result in results.values()), results


@pytest.mark.parametrize("name, url", BOARDS)
async def test_존재하지_않는_글은_삭제로_판정(bot, make_notice, name, url):
    notice = make_notice(name, url)
    top = (await fetch_notices(bot, notice))[0]
    pattern = r"/\d+/artclView\.do" if name == "대학" else r"/\d+/view\.do"
    replacement = "/999999999/artclView.do" if name == "대학" else "/999999999/view.do"
    fake = dict(top, id="fake", title="존재하지 않는 테스트 공지", url=re.sub(pattern, replacement, top["url"]))

    assert await notice.check_notice_exists(fake) is False
