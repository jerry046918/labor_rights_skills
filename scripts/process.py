"""FunASR single-pipeline audio processing.

Runs VAD → ASR (seaco-paraformer with hotwords) → punctuation → CAM++ diarization
in one AutoModel call. Outputs unified result.json or error.json.
"""
import argparse
import json
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

from funasr import AutoModel

try:
    # When imported as part of `scripts` package (e.g., from tests)
    from scripts.diarization_utils import detect_diarization_degradation
except ImportError:
    # When run as a script (python scripts/process.py)
    from diarization_utils import detect_diarization_degradation

SKILL_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = SKILL_ROOT / "models"
VAD_MODEL = "iic/speech_fsmn_vad_zh-cn-16k-common-pytorch"
ASR_MODEL = "iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch"
SPK_MODEL = "iic/speech_campplus_sv_zh-cn_16k-common"
PUNC_MODEL = "iic/punc_ct-transformer_zh-cn-common-vad_realtime-vocab272727"


def load_hotwords(path: Path) -> list[str]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("hotwords", [])


def get_audio_duration(audio_path: Path) -> float:
    """Get audio duration in seconds.

    Prefers ffprobe (fast, accurate). Falls back to librosa when ffprobe
    is unavailable (e.g., ffmpeg not on PATH in Git Bash on Windows —
    librosa is already a FunASR dependency so this adds no new install).
    """
    import subprocess
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True, check=True
        )
        return float(result.stdout.strip())
    except (FileNotFoundError, subprocess.CalledProcessError, ValueError):
        import librosa
        return float(librosa.get_duration(path=str(audio_path)))


def build_model(use_punc: bool = True):
    # VAD is required to segment audio — without it, CAM++ diarization
    # gets a single embedding for the whole file and can't split speakers.
    # Punc can be disabled as a fallback when it causes length-mismatch
    # warnings that break sentence_info assembly.
    kwargs = {
        "model": ASR_MODEL,
        "vad_model": VAD_MODEL,
        "spk_model": SPK_MODEL,
        "disable_update": True,
    }
    if use_punc:
        kwargs["punc_model"] = PUNC_MODEL
    return AutoModel(**kwargs)


def _clean_token_spaces(text: str) -> str:
    """Remove spaces between CJK characters.

    FunASR with punc disabled emits token-level output with a space
    between every Chinese character (e.g. "我 想 问"). Punc-enabled
    output has no such spaces. Strip inter-CJK spaces for readability
    while preserving spaces around latin/digit runs.
    """
    if not text:
        return text
    return re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)


def _parse_res(res: list, duration: float) -> tuple[list, list, str]:
    """Extract speakers, segments, full_text from FunASR result list.

    Handles the field-name inconsistency between punc-enabled and
    punc-disabled runs: with punc, sentence_info items use `text`;
    without punc, they use `sentence`. We accept either.
    """
    speakers = {}
    segments = []
    full_text_parts = []

    for item in res:
        sentence_info = item.get("sentence_info", [])
        if sentence_info:
            for sent in sentence_info:
                spk_id = f"spk_{sent.get('spk', 'unknown')}"
                start = sent.get("start", 0) / 1000.0
                end = sent.get("end", 0) / 1000.0
                # punc-on: sent['text']; punc-off: sent['sentence']
                raw = sent.get("text") or sent.get("sentence", "")
                text = _clean_token_spaces(raw)
                segments.append({
                    "start": start,
                    "end": end,
                    "speaker_id": spk_id,
                    "text": text,
                })
                full_text_parts.append(text)
                speakers[spk_id] = speakers.get(spk_id, 0) + max(0, end - start)
        else:
            # No sentence_info (older pipeline or no VAD) — fall back to
            # top-level text as a single segment with unknown speaker.
            text = _clean_token_spaces(item.get("text", ""))
            segments.append({
                "start": 0.0,
                "end": duration,
                "speaker_id": "spk_unknown",
                "text": text,
            })
            full_text_parts.append(text)
            speakers["spk_unknown"] = speakers.get("spk_unknown", 0) + duration

    speakers_list = [
        {"id": sid, "total_speaking_seconds": round(sec, 1)}
        for sid, sec in speakers.items()
    ]
    return speakers_list, segments, "".join(full_text_parts)


def process_audio(audio_path: Path, hotwords: list[str]) -> dict:
    duration = get_audio_duration(audio_path)
    hotword_str = " ".join(hotwords) if hotwords else None

    kwargs = dict(input=str(audio_path), batch_size_s=60)
    if hotword_str:
        kwargs["hotword"] = hotword_str

    # First attempt: full model (with punc)
    model = build_model(use_punc=True)
    res = model.generate(**kwargs)

    punc_used = True
    diarization_status = "ok"
    warning = None

    if detect_diarization_degradation(res, duration):
        # Auto-fallback: rerun without punc. Punc is the usual culprit
        # for length-mismatch warnings that break sentence_info.
        model_no_punc = build_model(use_punc=False)
        res = model_no_punc.generate(**kwargs)
        punc_used = False

        if detect_diarization_degradation(res, duration):
            diarization_status = "failed"
            warning = (
                "Diarization failed: ASR text is complete but speaker "
                "segmentation is unusable. Punc-disabled fallback was "
                "attempted but did not resolve. Recommend manual speaker "
                "annotation or switching to an alternative evidence path."
            )
        else:
            diarization_status = "degraded"
            warning = (
                "Diarization recovered via punc-disabled fallback. Text "
                "has no punctuation but speaker segmentation is usable."
            )

    speakers_list, segments, full_text = _parse_res(res, duration)

    result = {
        "audio_path": str(audio_path),
        "duration_seconds": round(duration, 1),
        "asr_model": "seaco-paraformer",
        "spk_model": "cam++",
        "punctuation_model": "ct-punc" if punc_used else "none",
        "processed_at": datetime.now().isoformat(timespec="seconds"),
        "hotwords_used": len(hotwords),
        "hotwords_applied": hotwords,
        "speakers": speakers_list,
        "segments": segments,
        "full_text": full_text,
        "asr_text_chars": len(full_text),
        "diarization_status": diarization_status,
    }
    if warning:
        result["warning"] = warning
    return result


def write_error(audio_path: Path, output_dir: Path, exc: Exception) -> None:
    error_data = {
        "audio_path": str(audio_path),
        "failed_at": datetime.now().isoformat(timespec="seconds"),
        "exit_code": 1,
        "stage": "process",
        "error_type": type(exc).__name__,
        "message": str(exc),
        "log_tail": traceback.format_exc()[-500:],
    }
    (output_dir / "error.json").write_text(
        json.dumps(error_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--audio", required=True, type=Path)
    parser.add_argument("--hotwords", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    output_path = args.output
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        if not args.audio.exists():
            raise FileNotFoundError(f"Audio file not found: {args.audio}")
        hotwords = load_hotwords(args.hotwords)
        result = process_audio(args.audio, hotwords)
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"OK: wrote {output_path}")
    except Exception as exc:
        write_error(args.audio, output_dir, exc)
        print(f"FAIL: wrote {output_dir / 'error.json'}: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
