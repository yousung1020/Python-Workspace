"""공지사항 상태 파일 저장·불러오기 테스트."""
import json


def board_state(*ids):
    return {
        "notices": [{"id": str(item), "number": str(item), "title": "t", "url": "u"} for item in ids],
        "missing_candidates": {},
        "updated_at": "2026-11-20T00:00:00",
    }


def test_상태_파일이_없으면_None(bot, state_file):
    assert not state_file.exists()
    assert bot.load_notice_state("대학") is None


def test_저장한_상태를_그대로_불러옴(bot, state_file):
    bot.save_notice_state("대학", board_state(1, 2))

    assert bot.load_notice_state("대학") == board_state(1, 2)
    saved = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved["version"] == 1
    assert set(saved["boards"]) == {"대학"}


def test_게시판별_상태가_서로_덮어쓰지_않음(bot):
    bot.save_notice_state("대학", board_state(1))
    bot.save_notice_state("컴소과", board_state(2))
    bot.save_notice_state("대학", board_state(3))

    assert bot.load_notice_state("대학") == board_state(3)
    assert bot.load_notice_state("컴소과") == board_state(2)
    assert bot.load_notice_state("정통과") is None


def test_저장_후_임시_파일이_남지_않음(bot, state_file):
    bot.save_notice_state("대학", board_state(1))

    assert sorted(path.name for path in state_file.parent.iterdir()) == ["notice_state.json"]


def test_손상된_상태_파일은_None으로_처리(bot, state_file):
    state_file.parent.mkdir(parents=True)
    state_file.write_text("{깨진 json", encoding="utf-8")

    assert bot.load_notice_state("대학") is None


def test_손상된_상태_파일에도_새_상태를_저장함(bot, state_file):
    state_file.parent.mkdir(parents=True)
    state_file.write_text("[]", encoding="utf-8")

    bot.save_notice_state("대학", board_state(1))

    assert bot.load_notice_state("대학") == board_state(1)
