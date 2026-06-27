"""JSON schema validation for process.py outputs."""
REQUIRED_RESULT_FIELDS = [
    "audio_path", "duration_seconds", "asr_model", "spk_model",
    "punctuation_model", "processed_at", "hotwords_used",
    "hotwords_applied", "speakers", "segments", "full_text",
    "asr_text_chars", "diarization_status",
]
VALID_DIARIZATION_STATUS = {"ok", "degraded", "failed"}
REQUIRED_SEGMENT_FIELDS = ["start", "end", "speaker_id", "text"]
REQUIRED_SPEAKER_FIELDS = ["id", "total_speaking_seconds"]
REQUIRED_ERROR_FIELDS = [
    "audio_path", "failed_at", "exit_code", "stage",
    "error_type", "message", "log_tail",
]


def validate_result_json(data: dict) -> None:
    """Raise ValueError if data doesn't conform to result.json schema."""
    for field in REQUIRED_RESULT_FIELDS:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")

    status = data["diarization_status"]
    if status not in VALID_DIARIZATION_STATUS:
        raise ValueError(
            f"diarization_status must be one of "
            f"{sorted(VALID_DIARIZATION_STATUS)}, got: {status!r}"
        )

    for s in data["speakers"]:
        for f in REQUIRED_SPEAKER_FIELDS:
            if f not in s:
                raise ValueError(f"Speaker missing field: {f}")

    speaker_ids = {s["id"] for s in data["speakers"]}
    for seg in data["segments"]:
        for f in REQUIRED_SEGMENT_FIELDS:
            if f not in seg:
                raise ValueError(f"Segment missing field: {f}")
        if seg["speaker_id"] not in speaker_ids:
            raise ValueError(
                f"Segment references unknown speaker_id: {seg['speaker_id']}"
            )


def validate_error_json(data: dict) -> None:
    for field in REQUIRED_ERROR_FIELDS:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
