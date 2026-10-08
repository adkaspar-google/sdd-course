#!/usr/bin/env python3
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Synthesizes slide narration audio and builds the 1080p MP4 course lecture."""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
import sys
import time


SLIDES_DIR = pathlib.Path(__file__).resolve().parent
NOTES_PATH = SLIDES_DIR / "SPEAKER_NOTES.md"
PNG_DIR = SLIDES_DIR / "png"
AUDIO_DIR = SLIDES_DIR / "audio"
SEGMENTS_DIR = SLIDES_DIR / "segments"
OUTPUT_MP4 = SLIDES_DIR / "SDD_Crash_Course_Lecture.mp4"
GENERATE_BIN = os.environ.get("GEMINI_TTS_BIN", "generate")


def parse_speaker_notes(md_path: pathlib.Path) -> list[dict[str, str]]:
    """Extracts structured slide notes from SPEAKER_NOTES.md."""
    text = md_path.read_text(encoding="utf-8")
    blocks = re.split(r"^## Slide (\d+):\s*(.+)$", text, flags=re.MULTILINE)
    slides: list[dict[str, str]] = []
    # blocks[0] is header; then groups of (num, title, body)
    for idx in range(1, len(blocks), 3):
        slide_num = int(blocks[idx])
        title = blocks[idx + 1].strip()
        body = blocks[idx + 2]

        purpose_m = re.search(r"-\s*\*\*PURPOSE\*\*:\s*(.+)", body)
        script_m = re.search(r"-\s*\*\*VERBAL SCRIPT\*\*:\s*(.+)", body)
        trans_m = re.search(r"-\s*\*\*TRANSITION\*\*:\s*(.+)", body)

        purpose = purpose_m.group(1).strip() if purpose_m else ""
        verbal_script = script_m.group(1).strip() if script_m else ""
        transition = trans_m.group(1).strip() if trans_m else ""

        slides.append(
            {
                "num": f"{slide_num:02d}",
                "title": title,
                "purpose": purpose,
                "verbal_script": verbal_script,
                "transition": transition,
                "full_notes": (
                    f"PURPOSE:\n{purpose}\n\n"
                    f"VERBAL SCRIPT:\n{verbal_script}\n\n"
                    f"TRANSITION:\n{transition}"
                ),
            }
        )
    return slides


def get_audio_duration(wav_path: pathlib.Path) -> float:
    """Returns the duration in seconds of an audio file via ffprobe."""
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(wav_path),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return float(res.stdout.strip())


def synthesize_tts(slide: dict[str, str], voice: str = "Kore") -> pathlib.Path:
    """Generates WAV audio for a slide using Gemini TTS with retries."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    wav_path = AUDIO_DIR / f"slide-{slide['num']}.wav"
    if wav_path.exists() and wav_path.stat().st_size > 10000:
        print(f"  [TTS] Reusing existing {wav_path.name}")
        return wav_path

    prompt = slide["verbal_script"]
    for attempt in range(1, 5):
        print(f"  [TTS] Generating {wav_path.name} (attempt {attempt})...")
        cmd = [
            GENERATE_BIN,
            f"-output={wav_path}",
            "tts",
            f"-voice={voice}",
            prompt,
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and wav_path.exists() and wav_path.stat().st_size > 10000:
            dur = get_audio_duration(wav_path)
            print(f"  [TTS] Created {wav_path.name} ({dur:.1f}s)")
            return wav_path
        print(f"  [TTS] Warning on attempt {attempt}: {res.stderr.strip()}")
        time.sleep(2 * attempt)

    raise RuntimeError(f"Failed to synthesize TTS for slide {slide['num']}")


def render_segment(slide: dict[str, str], wav_path: pathlib.Path) -> pathlib.Path:
    """Renders a single 1920x1080 MP4 slide segment with 0.6s audio padding."""
    SEGMENTS_DIR.mkdir(parents=True, exist_ok=True)
    png_path = PNG_DIR / f"slide-{slide['num']}.png"
    seg_path = SEGMENTS_DIR / f"seg-{slide['num']}.mp4"
    dur = get_audio_duration(wav_path) + 0.6

    cmd = [
        "ffmpeg",
        "-y",
        "-loop",
        "1",
        "-framerate",
        "30",
        "-i",
        str(png_path),
        "-i",
        str(wav_path),
        "-filter_complex",
        "[1:a]aformat=sample_rates=44100:channel_layouts=stereo,apad=pad_dur=0.6[aout]",
        "-map",
        "0:v",
        "-map",
        "[aout]",
        "-c:v",
        "libx264",
        "-tune",
        "stillimage",
        "-pix_fmt",
        "yuv420p",
        "-r",
        "30",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-t",
        f"{dur:.2f}",
        str(seg_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    return seg_path


def concat_segments(segment_paths: list[pathlib.Path], output_path: pathlib.Path) -> None:
    """Concatenates all MP4 segments losslessly and verifies with ffprobe."""
    concat_file = SEGMENTS_DIR / "concat_list.txt"
    lines = [f"file '{p.resolve()}'" for p in segment_paths]
    concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, check=True)

    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration,size:stream=codec_name,width,height,sample_rate,channels",
        "-of",
        "json",
        str(output_path),
    ]
    probe_res = subprocess.run(probe_cmd, capture_output=True, text=True, check=True)
    info = json.loads(probe_res.stdout)
    total_dur = float(info["format"]["duration"])
    size_mb = int(info["format"]["size"]) / (1024 * 1024)
    print(f"\n[VIDEO READY] {output_path} ({total_dur:.1f}s / {total_dur/60:.1f} min, {size_mb:.2f} MB)")


def main() -> int:
    slides = parse_speaker_notes(NOTES_PATH)
    print(f"Parsed {len(slides)} slides from {NOTES_PATH.name}")
    segment_paths: list[pathlib.Path] = []
    for slide in slides:
        wav_path = synthesize_tts(slide)
        seg_path = render_segment(slide, wav_path)
        segment_paths.append(seg_path)
    concat_segments(segment_paths, OUTPUT_MP4)
    return 0


if __name__ == "__main__":
    sys.exit(main())
