"""Unit tests for hotword merging logic (no FunASR required)."""
import json
from pathlib import Path

from scripts.hotword_utils import merge_hotwords, load_static_hotwords


def test_load_static_hotwords_returns_list():
    """Static hotwords file should load as a list of strings."""
    hotwords = load_static_hotwords()
    assert isinstance(hotwords, list)
    assert len(hotwords) > 50, "Expected at least 50 static hotwords"
    assert all(isinstance(w, str) for w in hotwords)
    assert "解除" in hotwords


def test_merge_hotwords_dedupes():
    """Merging should dedupe overlapping words."""
    static = ["解除", "合同", "经济补偿"]
    dynamic = ["解除", "恒生电子", "产品经理"]
    merged = merge_hotwords(static, dynamic)
    assert sorted(merged) == sorted(["解除", "合同", "经济补偿", "恒生电子", "产品经理"])


def test_merge_hotwords_handles_empty_dynamic():
    """Empty dynamic list should return static."""
    static = ["解除", "合同"]
    merged = merge_hotwords(static, [])
    assert merged == static


def test_merge_hotwords_filters_short():
    """Single-character 'words' should be filtered (no ASR bias benefit)."""
    static = ["解除", "合同"]
    dynamic = ["A", "解", "恒生电子"]
    merged = merge_hotwords(static, dynamic)
    assert "A" not in merged
    assert "解" not in merged
    assert "恒生电子" in merged


def test_merge_hotwords_writes_json(tmp_path: Path):
    """Merged result should be writable to JSON for process.py consumption."""
    static = ["解除", "合同"]
    dynamic = ["恒生电子"]
    out = tmp_path / "hotwords.json"
    merge_hotwords(static, dynamic, output_path=out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert "hotwords" in data
    assert "恒生电子" in data["hotwords"]
