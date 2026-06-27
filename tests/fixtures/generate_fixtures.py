"""Generate test audio fixtures from YAML scripts using edge-tts.

YAML script format:
  output: <filename.mp3>
  speakers:
    - id: hr
      voice: zh-CN-XiaoxiaoNeural
    - id: employee
      voice: zh-CN-YunxiNeural
  segments:
    - speaker: hr
      text: "今天找你来谈件事。"
      pause_after: 0.5
    - speaker: employee
      text: "您说。"
"""
import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

import edge_tts
import yaml

def load_script(script_path: Path) -> dict[str, Any]:
    with script_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)

async def synth_segment(text: str, voice: str, output_path: Path) -> None:
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(str(output_path))

async def generate(script: dict[str, Any], output_dir: Path) -> Path:
    output_path = output_dir / script["output"]
    voices = {s["id"]: s["voice"] for s in script["speakers"]}

    segments_dir = output_dir / "_segments"
    segments_dir.mkdir(parents=True, exist_ok=True)

    segment_files = []
    for i, seg in enumerate(script["segments"]):
        seg_file = segments_dir / f"seg_{i:03d}.mp3"
        await synth_segment(seg["text"], voices[seg["speaker"]], seg_file)
        segment_files.append(seg_file)

    # Concatenate using ffmpeg
    list_file = segments_dir / "concat.txt"
    with list_file.open("w", encoding="utf-8") as f:
        for sf in segment_files:
            f.write(f"file '{sf.name}'\n")

    import subprocess
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c", "copy", str(output_path)],
        cwd=str(segments_dir), check=True, capture_output=True
    )
    return output_path

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path, help="YAML script path")
    parser.add_argument("--output-dir", type=Path, default=Path("tests/fixtures"))
    args = parser.parse_args()

    script = load_script(args.script)
    output = asyncio.run(generate(script, args.output_dir))
    print(f"Generated: {output}")

if __name__ == "__main__":
    main()
