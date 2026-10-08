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
"""Builds the 7 Step-by-Step Module Videos and the Master 36-Slide Course Lecture Video.

Pipeline:
1. Parses all 36 `VERBAL SCRIPT` entries from `SPEAKER_NOTES.md`.
2. Synthesizes `audio/slide-01.wav` .. `audio/slide-36.wav` in parallel via Gemini TTS (`Kore`).
3. Renders `segments/seg-01.mp4` .. `segments/seg-36.mp4` in parallel via `ffmpeg` (`1920x1080`).
4. Concatenates each module's slides into 7 standalone MP4 videos under `modules/`:
   - `Module_01_Foundations_and_Dual_Engine.mp4` (Slides 01-06)
   - `Module_02_Lab01_Greenfield_Rate_Limiter.mp4` (Slides 07-11)
   - `Module_03_Lab02_Brownfield_Lease_Manager.mp4` (Slides 12-16)
   - `Module_04_Lab03_TDD_Circuit_Breaker.mp4` (Slides 17-21)
   - `Module_05_Lab04_Drift_and_Scorecard_Refactoring.mp4` (Slides 22-26)
   - `Module_06_Lab05_SDD_Code_Review_and_Stacked_PRs.mp4` (Slides 27-31)
   - `Module_07_Lab06_Capstone_SSOT_and_Rebuild_Test.mp4` (Slides 32-36)
5. Concatenates all 36 segments into `SDD_Crash_Course_Lecture.mp4`.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
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
SEG_DIR = SLIDES_DIR / "segments"
MODULES_DIR = SLIDES_DIR / "modules"
MASTER_VIDEO = SLIDES_DIR / "SDD_Crash_Course_Lecture.mp4"

GENERATE_CLI = os.environ.get("GEMINI_TTS_BIN", "generate")
VOICE = "Kore"

MODULES = [
    ("Module_01_Foundations_and_Dual_Engine.mp4", 1, 6),
    ("Module_02_Lab01_Greenfield_Rate_Limiter.mp4", 7, 11),
    ("Module_03_Lab02_Brownfield_Lease_Manager.mp4", 12, 16),
    ("Module_04_Lab03_TDD_Circuit_Breaker.mp4", 17, 21),
    ("Module_05_Lab04_Drift_and_Scorecard_Refactoring.mp4", 22, 26),
    ("Module_06_Lab05_SDD_Code_Review_and_Stacked_PRs.mp4", 27, 31),
    ("Module_07_Lab06_Capstone_SSOT_and_Rebuild_Test.mp4", 32, 36),
]


def parse_scripts(md_path: pathlib.Path) -> list[str]:
  text = md_path.read_text(encoding="utf-8")
  pattern = re.compile(r"-\s+\*\*VERBAL SCRIPT:\*\*\s*(.+)")
  scripts = [m.group(1).strip() for m in pattern.finditer(text)]
  if not scripts:
    raise RuntimeError(f"No VERBAL SCRIPT entries found in {md_path}")
  return scripts


def synthesize_one_tts(idx: int, script: str) -> tuple[int, float]:
  wav_path = AUDIO_DIR / f"slide-{idx:02d}.wav"
  if wav_path.exists() and wav_path.stat().st_size > 10000:
    return idx, 0.0
  t0 = time.time()
  for attempt in range(1, 6):
    cmd = [
        GENERATE_CLI,
        f"-output={wav_path}",
        "tts",
        f"-voice={VOICE}",
        script,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode == 0 and wav_path.exists() and wav_path.stat().st_size > 10000:
      return idx, time.time() - t0
    time.sleep(1.5 * attempt)
  raise RuntimeError(f"Failed TTS for slide {idx:02d} after 5 attempts")


def render_one_segment(idx: int) -> tuple[int, float]:
  png_path = PNG_DIR / f"slide-{idx:02d}.png"
  wav_path = AUDIO_DIR / f"slide-{idx:02d}.wav"
  seg_path = SEG_DIR / f"seg-{idx:02d}.mp4"
  if not png_path.exists():
    raise FileNotFoundError(f"Missing slide PNG: {png_path}")
  if not wav_path.exists():
    raise FileNotFoundError(f"Missing slide WAV: {wav_path}")

  probe = subprocess.run(
      [
          "ffprobe",
          "-v",
          "error",
          "-show_entries",
          "format=duration",
          "-of",
          "default=noprint_wrappers=1:nokey=1",
          str(wav_path),
      ],
      capture_output=True,
      text=True,
      check=True,
  )
  dur = float(probe.stdout.strip()) + 0.75
  cmd = [
      "ffmpeg",
      "-y",
      "-loop",
      "1",
      "-i",
      str(png_path),
      "-i",
      str(wav_path),
      "-vf",
      "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2:white,format=yuv420p",
      "-af",
      "apad=pad_dur=0.75",
      "-c:v",
      "libx264",
      "-preset",
      "veryfast",
      "-tune",
      "stillimage",
      "-r",
      "24",
      "-c:a",
      "aac",
      "-b:a",
      "192k",
      "-ar",
      "24000",
      "-t",
      f"{dur:.2f}",
      "-movflags",
      "+faststart",
      str(seg_path),
  ]
  subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
  return idx, dur


def concat_segments(out_path: pathlib.Path, start_idx: int, end_idx: int) -> float:
  concat_file = SEG_DIR / f"concat_{start_idx:02d}_{end_idx:02d}.txt"
  lines = [f"file '{SEG_DIR / f'seg-{i:02d}.mp4'}'" for i in range(start_idx, end_idx + 1)]
  concat_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
  subprocess.run(
      [
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
          str(out_path),
      ],
      check=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
  )
  probe = subprocess.run(
      [
          "ffprobe",
          "-v",
          "error",
          "-show_entries",
          "format=duration",
          "-of",
          "default=noprint_wrappers=1:nokey=1",
          str(out_path),
      ],
      capture_output=True,
      text=True,
      check=True,
  )
  return float(probe.stdout.strip())


def main() -> int:
  AUDIO_DIR.mkdir(parents=True, exist_ok=True)
  SEG_DIR.mkdir(parents=True, exist_ok=True)
  MODULES_DIR.mkdir(parents=True, exist_ok=True)

  scripts = parse_scripts(NOTES_PATH)
  print(f"[1/4] Parsed {len(scripts)} slide scripts from {NOTES_PATH.name}", flush=True)

  print("[2/4] Synthesizing TTS audio tracks in parallel (max_workers=4)...", flush=True)
  with ThreadPoolExecutor(max_workers=4) as pool:
    futures = {
        pool.submit(synthesize_one_tts, i, script): i
        for i, script in enumerate(scripts, start=1)
    }
    for fut in as_completed(futures):
      idx, elapsed = fut.result()
      status = "cached" if elapsed == 0.0 else f"synthesized in {elapsed:.1f}s"
      print(f"  [TTS] Slide {idx:02d}/{len(scripts):02d}: {status}", flush=True)

  print("[3/4] Rendering 1080p MP4 slide segments in parallel (max_workers=6)...", flush=True)
  total_dur = 0.0
  with ThreadPoolExecutor(max_workers=6) as pool:
    futures = {pool.submit(render_one_segment, i): i for i in range(1, len(scripts) + 1)}
    for fut in as_completed(futures):
      idx, dur = fut.result()
      total_dur += dur
      print(f"  [SEG] Slide {idx:02d}/{len(scripts):02d}: {dur:.1f}s", flush=True)

  print("[4/4] Assembling 7 Module Videos + Master Full-Course Video...", flush=True)
  for mod_name, s_idx, e_idx in MODULES:
    mod_path = MODULES_DIR / mod_name
    dur = concat_segments(mod_path, s_idx, e_idx)
    size_mb = mod_path.stat().st_size / (1024 * 1024)
    print(
        f"  [MODULE] {mod_name} (Slides {s_idx:02d}-{e_idx:02d}): "
        f"{dur:.1f}s ({dur/60:.1f} min), {size_mb:.2f} MB",
        flush=True,
    )

  master_dur = concat_segments(MASTER_VIDEO, 1, len(scripts))
  master_mb = MASTER_VIDEO.stat().st_size / (1024 * 1024)
  print(
      f"  [MASTER] {MASTER_VIDEO.name} (Slides 01-{len(scripts):02d}): "
      f"{master_dur:.1f}s ({master_dur/60:.1f} min), {master_mb:.2f} MB",
      flush=True,
  )
  return 0


if __name__ == "__main__":
  sys.exit(main())
