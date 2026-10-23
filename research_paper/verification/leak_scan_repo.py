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
"""Open-Source Hygiene & Vendor-Neutral Nomenclature Scanner for dualloop-sdd-benchmark.

Scans all text, code, JSON, Markdown, and LaTeX files in the repository to verify:
  1. Zero internal workstation paths, internal hostnames, or internal tool identifiers.
  2. Zero non-neutral competitor product names (enforcing vendor-neutral academic nomenclature).
"""

from __future__ import annotations

import pathlib
import re
import sys

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SELF_PATH = pathlib.Path(__file__).resolve()

BANNED_PATTERNS = [
    (r"/usr/local/google/home/", "Internal workstation home path"),
    (r"/google/src/cloud/", "Internal CitC workspace path"),
    (r"/google/src/files/", "Internal Piper snapshot path"),
    (r"\.corp\.google\.com", "Internal corp domain"),
    (r"\.c\.googlers\.com", "Internal cloudtop hostname"),
    (r"(?i)\bjetski\b", "Internal agent code name"),
    (r"(?i)\bevalin\b", "Internal evaluation CLI name"),
    (r"(?i)\binvoke_subagent\b", "Internal subagent tool identifier"),
    (r"~/memory/default", "Internal memory path"),
    (r"\\textasciitilde\{\}/memory/default", "TeX-escaped internal memory path"),
    (r"(?i)\bmfs search\b", "Internal memory CLI"),
    (r"(?i)\bvisibility:\s*PINNED\b", "Internal memory frontmatter"),
    (r"(?i)\bsuperpowers\b", "Non-neutral inner-loop skill brand name"),
    (r"(?i)\bgithub spec kit\b", "Non-neutral competitor brand name"),
    (r"(?i)\bamazon kiro\b", "Non-neutral competitor brand name"),
]

BINARY_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".pyc", ".whl", ".tar", ".gz"}


def main() -> int:
    violations: list[str] = []
    files_scanned = 0

    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if path.resolve() == SELF_PATH:
            continue
        if path.suffix.lower() in BINARY_EXTENSIONS:
            continue

        files_scanned += 1
        txt = path.read_text(encoding="utf-8", errors="ignore")
        rel = path.relative_to(REPO_ROOT)
        for pattern, desc in BANNED_PATTERNS:
            for match in re.finditer(pattern, txt):
                line_no = txt[:match.start()].count("\n") + 1
                violations.append(f"{rel}:{line_no}: [{desc}] matched '{match.group(0)}'")

    print("=" * 80)
    print(f"OPEN-SOURCE HYGIENE & NOMENCLATURE SCAN ({files_scanned} files scanned)")
    print("=" * 80)
    if violations:
        print(f"[FAIL] Found {len(violations)} violation(s):")
        for v in violations[:50]:
            print(f"  - {v}")
        return 1

    print("[PASS] 0 internal path/term leaks and 0 banned brand names across all repository files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
