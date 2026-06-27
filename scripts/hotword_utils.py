"""Hotword utilities for FunASR seaco-paraformer."""
import json
from pathlib import Path
from typing import Optional

STATIC_KEYWORDS_FILE = Path(__file__).resolve().parent.parent / "references" / "audio-keywords.md"
MIN_HOTWORD_LEN = 2


def load_static_hotwords(path: Optional[Path] = None) -> list[str]:
    """Parse audio-keywords.md and extract hotword list.

    The markdown file has categories as ## headers, with comma-separated
    terms below each header. This function flattens them into a single list.
    """
    path = path or STATIC_KEYWORDS_FILE
    content = path.read_text(encoding="utf-8")
    words = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        for word in line.split("、"):
            word = word.strip()
            if word and len(word) >= MIN_HOTWORD_LEN:
                words.append(word)
    return words


def merge_hotwords(
    static: list[str],
    dynamic: list[str],
    output_path: Optional[Path] = None,
) -> list[str]:
    """Merge static baseline with case-specific dynamic hotwords.

    - Dedupes (case-sensitive)
    - Filters words shorter than MIN_HOTWORD_LEN (no ASR benefit)
    - Optionally writes JSON {"hotwords": [...]} for process.py
    """
    seen = set()
    merged = []
    for w in static + dynamic:
        if len(w) < MIN_HOTWORD_LEN:
            continue
        if w in seen:
            continue
        seen.add(w)
        merged.append(w)
    if output_path:
        output_path.write_text(
            json.dumps({"hotwords": merged}, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    return merged
