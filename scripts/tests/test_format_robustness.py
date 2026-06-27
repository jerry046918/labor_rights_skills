"""Test process.py handles mp3/wav/Chinese-path inputs."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def _convert_audio(src: Path, dst: Path):
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(src), str(dst)],
        check=True, capture_output=True
    )


def test_process_handles_mp3(dismissal_audio: Path, tmp_evidence_dir: Path):
    """mp3 input should work."""
    hotwords_file = tmp_evidence_dir / "hotwords.json"
    hotwords_file.write_text(json.dumps({"hotwords": []}), encoding="utf-8")
    output = tmp_evidence_dir / "result.json"
    subprocess.run(
        [sys.executable, "scripts/process.py",
         "--audio", str(dismissal_audio),
         "--hotwords", str(hotwords_file),
         "--output", str(output)],
        check=True, capture_output=True, text=True
    )
    assert output.exists()


def test_process_handles_wav(dismissal_audio: Path, tmp_evidence_dir: Path):
    """wav input should work (convert from mp3)."""
    wav_path = tmp_evidence_dir / "test.wav"
    _convert_audio(dismissal_audio, wav_path)

    hotwords_file = tmp_evidence_dir / "hotwords.json"
    hotwords_file.write_text(json.dumps({"hotwords": []}), encoding="utf-8")
    output = tmp_evidence_dir / "result_wav.json"
    subprocess.run(
        [sys.executable, "scripts/process.py",
         "--audio", str(wav_path),
         "--hotwords", str(hotwords_file),
         "--output", str(output)],
        check=True, capture_output=True, text=True
    )
    assert output.exists()


def test_process_handles_chinese_path(dismissal_audio: Path, tmp_path: Path):
    """Chinese characters in file path should work."""
    chinese_dir = tmp_path / "录音证据_测试"
    chinese_dir.mkdir()
    audio_copy = chinese_dir / "谈判录音.mp3"
    import shutil
    shutil.copy(dismissal_audio, audio_copy)

    hotwords_file = chinese_dir / "hotwords.json"
    hotwords_file.write_text(json.dumps({"hotwords": []}), encoding="utf-8")
    output = chinese_dir / "result.json"
    subprocess.run(
        [sys.executable, "scripts/process.py",
         "--audio", str(audio_copy),
         "--hotwords", str(hotwords_file),
         "--output", str(output)],
        check=True, capture_output=True, text=True
    )
    assert output.exists()
