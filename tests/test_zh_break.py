import pytest

import zh_break as Z


def test_words_numbers_and_counted_nouns_stay_whole():
    assert "八倍" in Z.break_units("他说一百年后经济会增长八倍")
    assert "生产力" in Z.break_units("富足和生产力提升")
    assert Z.break_units("只是我们每周工作80小时")[-3:] == ["每周", "工作", "80小时"]
    assert "一项预测" in Z.break_units("凯恩斯对工业革命做了一项预测")


def test_units_always_rebuild_the_text():
    for text in ("他说一百年后经济会增长八倍", "我们获得了巨大的富足和生产力提升", "用DNA里的信息，做AI模型", "先行动，再自信。"):
        assert "".join(Z.break_units(text)).replace(" ", "") == text.replace(" ", "")


def test_latin_words_and_numbers_with_units_are_single_units():
    units = Z.break_units("每周工作15小时，使用GitHub Actions")
    assert "15小时" in units and "GitHub " in units or "GitHub" in units


def test_empty_text_has_no_units():
    assert Z.break_units("") == [] and Z.break_units("   ") == []


def test_without_the_word_list_every_character_is_a_unit(monkeypatch, tmp_path):
    monkeypatch.setattr(Z, "LEXICON", tmp_path / "missing.gz")
    Z._lexicon.cache_clear()
    try:
        assert Z.break_units("生产力提升") == list("生产力提升")
    finally:
        Z._lexicon.cache_clear()


def test_zh_units_returns_none_for_text_with_no_chinese():
    assert Z.zh_units("Act first, then feel confident") is None
    assert "".join(Z.zh_units("先行动，再自信")) == "先行动，再自信"


def test_with_units_adds_units_only_for_chinese_and_only_when_enabled():
    cues = [{"zh": "他说一百年后经济会增长八倍", "en": "a"}, {"zh": "", "en": "b"}]
    on = Z.with_units(cues)
    assert on[0]["zhUnits"] == Z.break_units(cues[0]["zh"]) and "zhUnits" not in on[1]
    assert "zhUnits" not in cues[0]                     # the input is not changed
    assert Z.with_units(cues, enabled=False) == cues


def test_punctuation_never_starts_a_unit_it_could_start_a_line_with():
    units = Z.zh_units("回到1930年，凯恩斯预测八倍。“先行动”，再自信！")
    assert "".join(units) == "回到1930年，凯恩斯预测八倍。“先行动”，再自信！"
    assert not any(u[0] in "，。、！？：；”）》" for u in units)       # closing marks stay with the word before
    assert not any(u[-1] in "“（《" for u in units)                  # opening marks stay with the word after
    assert any(u.endswith("，") for u in units)


def test_the_ported_code_and_word_list_are_credited_and_licensed():
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent
    notice = (root / "NOTICE").read_text(encoding="utf-8")
    assert "autoclip" in notice and "jieba" in notice and "scripts/zh_break.py" in notice
    assert "Sun Junyi" in (root / "LICENSES" / "MIT-jieba.txt").read_text(encoding="utf-8")
    assert "AutoClip Team" in (root / "LICENSES" / "MIT-autoclip.txt").read_text(encoding="utf-8")
    assert "autoclip" in Z.__doc__ and "MIT" in Z.__doc__
    assert Z.LEXICON.is_file()


def test_a_space_after_a_chinese_character_does_not_split_the_word():
    # "运行 AI": the space follows 行 but 运行 is still one word; the space stays in the text.
    units = Z.zh_units("按计划运行 AI 智能体的 Mac 应用")
    assert "运行 " in units and "运" not in units and "行 " not in units
    assert "".join(units) == "按计划运行 AI 智能体的 Mac 应用"
    assert "交给 " in Z.zh_units("琐事交给 LoopX，你专注")


def test_spaces_between_latin_words_and_chinese_are_kept_in_the_units():
    units = Z.zh_units("issue 没人管，紧急邮件")
    assert "".join(units) == "issue 没人管，紧急邮件" and units[0] == "issue "
