"""Schema validation for result.json / error.json."""
import json

import pytest

from scripts.schema import validate_result_json, validate_error_json


def _valid_result():
    return {
        "audio_path": "/test/audio.mp3",
        "duration_seconds": 100,
        "asr_model": "seaco-paraformer",
        "spk_model": "cam++",
        "punctuation_model": "ct-punc",
        "processed_at": "2026-06-27T15:30:00",
        "hotwords_used": 5,
        "hotwords_applied": ["解除", "合同"],
        "speakers": [{"id": "spk_0", "total_speaking_seconds": 50}],
        "segments": [{"start": 0.0, "end": 1.0, "speaker_id": "spk_0", "text": "test"}],
        "full_text": "test",
        "asr_text_chars": 4,
        "diarization_status": "ok",
    }


def test_valid_result_passes():
    validate_result_json(_valid_result())


def test_result_missing_required_field_fails():
    bad = _valid_result()
    del bad["asr_model"]
    with pytest.raises(ValueError, match="asr_model"):
        validate_result_json(bad)


def test_result_missing_hotwords_applied_fails():
    """hotwords_applied is required for audit trail."""
    bad = _valid_result()
    del bad["hotwords_applied"]
    with pytest.raises(ValueError, match="hotwords_applied"):
        validate_result_json(bad)


def test_result_segment_missing_speaker_id_fails():
    bad = _valid_result()
    bad["segments"][0].pop("speaker_id")
    with pytest.raises(ValueError, match="speaker_id"):
        validate_result_json(bad)


def test_result_speakers_count_mismatch_fails():
    """speakers list id set must match segment speaker_ids."""
    bad = _valid_result()
    bad["segments"][0]["speaker_id"] = "spk_nonexistent"
    with pytest.raises(ValueError, match="spk_nonexistent"):
        validate_result_json(bad)


def test_result_missing_asr_text_chars_fails():
    bad = _valid_result()
    del bad["asr_text_chars"]
    with pytest.raises(ValueError, match="asr_text_chars"):
        validate_result_json(bad)


def test_result_missing_diarization_status_fails():
    bad = _valid_result()
    del bad["diarization_status"]
    with pytest.raises(ValueError, match="diarization_status"):
        validate_result_json(bad)


@pytest.mark.parametrize("status", ["ok", "degraded", "failed"])
def test_result_diarization_status_valid(status):
    ok_result = _valid_result()
    ok_result["diarization_status"] = status
    validate_result_json(ok_result)


def test_result_diarization_status_invalid():
    bad = _valid_result()
    bad["diarization_status"] = "broken"
    with pytest.raises(ValueError, match="diarization_status"):
        validate_result_json(bad)


def _valid_error():
    return {
        "audio_path": "/test/audio.mp3",
        "failed_at": "2026-06-27T15:42:00",
        "exit_code": 1,
        "stage": "diarization",
        "error_type": "ModelLoadError",
        "message": "Failed to load cam++ model",
        "log_tail": "...",
    }


def test_valid_error_passes():
    validate_error_json(_valid_error())


def test_error_missing_error_type_fails():
    bad = _valid_error()
    del bad["error_type"]
    with pytest.raises(ValueError, match="error_type"):
        validate_error_json(bad)
