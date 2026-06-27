"""Tests for detect_diarization_degradation heuristic.

Pure-function tests — no FunASR runtime needed. Covers the bug reported
in issue-report.md where punc length-mismatch leaves sentence_info with
only 1-2 fragments while full_text is complete.
"""
import pytest

from scripts.diarization_utils import detect_diarization_degradation


def _item(text: str, sentence_info_count: int) -> dict:
    """Build a fake FunASR result item."""
    si = [{"text": "片段", "start": 0, "end": 1000, "spk": 0}
          for _ in range(sentence_info_count)]
    return {"text": text, "sentence_info": si, "timestamp": []}


def test_long_text_full_sentence_info_not_degraded():
    """Healthy output: text + matching sentence_info."""
    res = [_item("公司决定从今天起解除与你的劳动合同，" * 10, 20)]
    assert detect_diarization_degradation(res, duration_seconds=180.0) is False


def test_long_text_sparse_sentence_info_flagged():
    """The actual bug: text complete but sentence_info has only 1-2 entries."""
    long_text = "公司决定从今天起解除与你的劳动合同，" * 30
    res = [_item(long_text, 2)]
    assert detect_diarization_degradation(res, duration_seconds=180.0) is True


def test_short_text_sparse_not_flagged():
    """Short text naturally has few segments — don't false-positive."""
    res = [_item("你好", 1)]
    assert detect_diarization_degradation(res, duration_seconds=180.0) is False


def test_long_text_sparse_but_short_duration_not_flagged():
    """Very short audio may legitimately have few sentence_info entries."""
    long_text = "解除劳动合同" * 30
    res = [_item(long_text, 2)]
    assert detect_diarization_degradation(res, duration_seconds=10.0) is False


def test_empty_result_not_flagged():
    assert detect_diarization_degradation([], duration_seconds=180.0) is False


def test_multiple_items_any_degraded_flags():
    """If any item in the list is degraded, flag it."""
    res = [
        _item("正常文本", 5),
        _item("异常" * 50, 1),
    ]
    assert detect_diarization_degradation(res, duration_seconds=180.0) is True
