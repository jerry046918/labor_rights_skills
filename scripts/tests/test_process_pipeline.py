"""Integration tests for process.py - requires FunASR installed."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.schema import validate_result_json


pytestmark = pytest.mark.integration


def _run_process(audio_path: Path, output_path: Path, hotwords_path: Path) -> dict:
    """Run process.py as subprocess, return parsed result.json."""
    cmd = [
        sys.executable, "scripts/process.py",
        "--audio", str(audio_path),
        "--hotwords", str(hotwords_path),
        "--output", str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert result.returncode == 0, f"process.py failed: {result.stderr}"
    return json.loads(output_path.read_text(encoding="utf-8"))


def test_dismissal_audio_produces_valid_result(
    dismissal_audio: Path, tmp_evidence_dir: Path, sample_hotwords: list[str]
):
    """Process dismissal audio; result must pass schema validation."""
    hotwords_path = tmp_evidence_dir / "hotwords.json"
    hotwords_path.write_text(
        json.dumps({"hotwords": sample_hotwords}), encoding="utf-8"
    )
    output_path = tmp_evidence_dir / "result.json"

    data = _run_process(dismissal_audio, output_path, hotwords_path)
    validate_result_json(data)


def test_dismissal_audio_finds_keywords(
    dismissal_audio: Path, tmp_evidence_dir: Path, sample_hotwords: list[str]
):
    """Transcript must contain key dismissal-related terms."""
    hotwords_path = tmp_evidence_dir / "hotwords.json"
    hotwords_path.write_text(
        json.dumps({"hotwords": sample_hotwords}), encoding="utf-8"
    )
    output_path = tmp_evidence_dir / "result.json"

    data = _run_process(dismissal_audio, output_path, hotwords_path)
    full_text = data["full_text"]
    assert "解除" in full_text, f"Expected '解除' in transcript: {full_text}"
    assert "合同" in full_text


def test_dismissal_audio_detects_multiple_speakers(
    dismissal_audio: Path, tmp_evidence_dir: Path, sample_hotwords: list[str]
):
    """Diarization should find >=2 speakers."""
    hotwords_path = tmp_evidence_dir / "hotwords.json"
    hotwords_path.write_text(
        json.dumps({"hotwords": sample_hotwords}), encoding="utf-8"
    )
    output_path = tmp_evidence_dir / "result.json"

    data = _run_process(dismissal_audio, output_path, hotwords_path)
    assert len(data["speakers"]) >= 2, f"Expected >=2 speakers, got: {data['speakers']}"


def test_process_writes_error_json_on_invalid_audio(
    tmp_evidence_dir: Path, sample_hotwords: list[str]
):
    """Invalid audio path should produce error.json, not crash."""
    hotwords_path = tmp_evidence_dir / "hotwords.json"
    hotwords_path.write_text(
        json.dumps({"hotwords": sample_hotwords}), encoding="utf-8"
    )
    output_path = tmp_evidence_dir / "result.json"
    error_path = tmp_evidence_dir / "error.json"

    cmd = [
        sys.executable, "scripts/process.py",
        "--audio", "/nonexistent/audio.mp3",
        "--hotwords", str(hotwords_path),
        "--output", str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
    assert error_path.exists(), "error.json should be written on failure"
    error_data = json.loads(error_path.read_text(encoding="utf-8"))
    assert "error_type" in error_data
    assert "message" in error_data
