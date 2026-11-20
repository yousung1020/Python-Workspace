"""이전 목록과 현재 목록의 차이를 계산하는 로직 테스트."""


def notice(post_id, number):
    return {
        "id": f"/bbs/dmu/677/{post_id}/artclView.do",
        "number": str(number),
        "title": f"공지 {post_id}",
        "url": f"https://www.dongyang.ac.kr/bbs/dmu/677/{post_id}/artclView.do?layout=unknown",
    }


def changes(bot, previous, current):
    return bot.Notice([], "대학", "").get_notice_changes(previous, current)


def test_변화가_없으면_빈_결과(bot):
    current = [notice(3, 3), notice(2, 2), notice(1, 1)]

    assert changes(bot, current, list(current)) == ([], [])


def test_새_공지와_사라진_공지를_구분(bot):
    previous = [notice(3, 3), notice(2, 2), notice(1, 1)]
    current = [notice(5, 5), notice(4, 4), notice(3, 3)]

    new, missing = changes(bot, previous, current)

    assert [item["id"] for item in new] == [notice(5, 5)["id"], notice(4, 4)["id"]]
    assert [item["id"] for item in missing] == [notice(2, 2)["id"], notice(1, 1)["id"]]


def test_번호가_바뀌어도_같은_글이면_새_공지가_아님(bot):
    # 게시판 번호는 '전체 글 수 - 위치'로 다시 계산되므로, 숨김 글이나 삭제가 생기면
    # 같은 글의 번호가 바뀝니다. 번호를 기준으로 비교하면 직전 공지를 새 공지로 오인합니다.
    previous = [notice(3, 5611), notice(2, 5610)]
    current = [notice(3, 5612), notice(2, 5611)]

    assert changes(bot, previous, current) == ([], [])


def test_번호가_같아도_다른_글이면_새_공지(bot):
    # 오래된 글이 삭제되고 새 글이 올라오면 최상단 번호가 그대로일 수 있습니다.
    previous = [notice(3, 5611), notice(2, 5610)]
    current = [notice(4, 5611), notice(3, 5610)]

    new, missing = changes(bot, previous, current)

    assert [item["id"] for item in new] == [notice(4, 5611)["id"]]
    assert [item["id"] for item in missing] == [notice(2, 5610)["id"]]
