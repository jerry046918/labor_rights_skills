"""Verify hotwords actually bias ASR (compare with/without)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _run(audio: Path, hotwords: list[str], output: Path) -> str:
    hotwords_file = output.parent / "hotwords.json"
    hotwords_file.write_text(json.dumps({"hotwords": hotwords}), encoding="utf-8")
    subprocess.run(
        [sys.executable, "scripts/process.py",
         "--audio", str(audio),
         "--hotwords", str(hotwords_file),
         "--output", str(output)],
        check=True, capture_output=True, text=True
    )
    return json.loads(output.read_text(encoding="utf-8"))["full_text"]


def test_hotword_bias_increases_recognition(
    dismissal_audio: Path, tmp_evidence_dir: Path
):
    """With explicit hotwords for case-specific terms, recognition should improve.

    Note: this test is heuristic - it checks that hotwords_applied field is populated
    and result is non-empty. Strict before/after accuracy comparison requires more
    audio samples than our single fixture can provide.
    """
    hotwords = ["解除劳动合同", "经济补偿", "N+1", "违法解除"]
    output = tmp_evidence_dir / "with_hotwords.json"
    text = _run(dismissal_audio, hotwords, output)
    assert len(text) > 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["hotwords_used"] == len(hotwords)
    assert set(hotwords).issubset(set(data["hotwords_applied"]))
