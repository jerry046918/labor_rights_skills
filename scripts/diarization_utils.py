"""Pure utility functions for diarization result analysis.

Kept separate from process.py so unit tests can run without FunASR
(FunASR is a ~3GB install). Anything in this module must be a pure
function with no funasr/torch/etc imports.
"""
from __future__ import annotations


def detect_diarization_degradation(res: list, duration_seconds: float) -> bool:
    """Detect ASR-text-complete-but-diarization-failed scenario.

    Returns True when full_text is substantial but sentence_info is nearly
    empty on a non-trivial audio. This typically happens when the punc
    model emits a length-mismatched token count vs the ASR timestamp
    array, which breaks sentence_info assembly and leaves only the first
    1-2 fragments.

    Heuristic thresholds:
    - text length > 50 chars (substantive content)
    - sentence_info count < 3 (suspiciously sparse)
    - duration > 30s (long enough that sparsity is unexpected)
    """
    for item in res:
        text = item.get("text", "")
        si = item.get("sentence_info", [])
        if len(text) > 50 and len(si) < 3 and duration_seconds > 30:
            return True
    return False
