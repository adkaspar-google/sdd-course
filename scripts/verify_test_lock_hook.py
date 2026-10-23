#!/usr/bin/env python3
"""PreToolUse Hook for Google Antigravity (`agy`) and Claude Code (`claude`).

Enforces Step 1 of the Contract-Locked Dual-Stage Harness (`Arm D`):
When `.sdd_test_lock.sha256` is present in the workspace, blocks any attempt by
the Goldfish Builder to modify, overwrite, or `chmod +w` a locked test file via
`edit_file`, `write_file`, `Write`, `Edit`, `MultiEdit`, or `Bash`/`run_command`.
"""

import json
import os
import pathlib
import sys


def main():
    lock_file = pathlib.Path(".sdd_test_lock.sha256")
    if not lock_file.exists():
        return 0

    try:
        locked_paths = set(json.loads(lock_file.read_text(encoding="utf-8")).keys())
    except Exception:
        return 0

    raw_stdin = sys.stdin.read().strip()
    if not raw_stdin:
        return 0

    try:
        payload = json.loads(raw_stdin)
    except Exception:
        return 0

    tool_input = payload.get("tool_input") or payload.get("arguments") or {}
    # Check file path fields across Claude Code (file_path) and Antigravity (Path, TargetFile)
    target_path = (
        tool_input.get("file_path")
        or tool_input.get("Path")
        or tool_input.get("TargetFile")
        or ""
    )
    if target_path:
        try:
            rel = str(pathlib.Path(target_path).resolve().relative_to(pathlib.Path.cwd().resolve()))
        except Exception:
            rel = target_path
        if rel in locked_paths or rel == ".sdd_test_lock.sha256":
            msg = (
                f"[SDD Contract-Lock Gate] BLOCKED modification to locked verifier file '{rel}'. "
                "Locked contract tests (.sdd_test_lock.sha256 / chmod 0444) are read-only during Builder execution."
            )
            print(msg, file=sys.stderr)
            return 2

    # Check shell commands for chmod +w or redirections onto locked test files
    cmd_str = tool_input.get("command") or tool_input.get("CommandLine") or ""
    if cmd_str:
        if ".sdd_test_lock.sha256" in cmd_str and "verify-lock" not in cmd_str:
            print("[SDD Contract-Lock Gate] BLOCKED shell mutation of .sdd_test_lock.sha256.", file=sys.stderr)
            return 2
        for lp in locked_paths:
            if lp in cmd_str and any(tok in cmd_str for tok in ("chmod", "rm ", "mv ", ">", "tee ", "sed -i")):
                print(
                    f"[SDD Contract-Lock Gate] BLOCKED shell command attempting to mutate locked test file '{lp}'.",
                    file=sys.stderr,
                )
                return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
