#!/usr/bin/env bash
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
# ==============================================================================
# Dual-Loop SDD + OO-Harness Installer for:
#   - Google Antigravity (`agy` / `~/.gemini/config/`)
#   - Claude Code (`claude` / `~/.claude/`)
#   - Gemini CLI (`gemini` / `~/.gemini/extensions/`)
#   - Project-local installation (`--project <path>`)
# ==============================================================================
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODE="project"
TARGET="all"
DEST_DIR=""

usage() {
  cat <<EOF
Usage: ./install.sh [OPTIONS]

Installs the Dual-Loop SDD + OO-Harness workflow (6 Skills, 3 Subagents,
6 Slash Commands, PreToolUse Test-Lock Hook, and \`sdd-harness\` CLI) into
Google Antigravity (\`agy\`), Claude Code (\`claude\`), Gemini CLI (\`gemini\`),
or any target project repository.

Options:
  --global              Install globally into ~/.gemini/config/ (Antigravity)
                        and ~/.claude/ (Claude Code) and ~/.local/bin/sdd-harness
  --project <DIR>       Install into a target project repository (default: current repo)
  --target <TARGET>     Target agent environment: agy | claude | gemini | all (default: all)
  --verify              Verify that all plugin manifests, skills, subagents, hooks, and CLI work
  -h, --help            Show this help message
EOF
}

VERIFY_ONLY=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --global)
      MODE="global"
      shift
      ;;
    --project)
      MODE="project"
      DEST_DIR="$2"
      shift 2
      ;;
    --target)
      TARGET="$2"
      shift 2
      ;;
    --verify)
      VERIFY_ONLY=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ "$VERIFY_ONLY" == "true" ]]; then
  echo "================================================================================"
  echo " Verifying Dual-Loop SDD + OO-Harness Installable Bundle (agy + claude + gemini)"
  echo "================================================================================"
  test -x "$REPO_DIR/bin/sdd-harness"
  test -f "$REPO_DIR/scripts/verify_test_lock_hook.py"
  test -f "$REPO_DIR/.agents/scripts/verify_test_lock_hook.py"
  test -f "$REPO_DIR/.agents/plugins/dualloop-sdd/scripts/verify_test_lock_hook.py"
  test -f "$REPO_DIR/.agents/plugins/dualloop-sdd/plugin.json"
  test -f "$REPO_DIR/.claude-plugin/plugin.json"
  test -f "$REPO_DIR/.claude-plugin/marketplace.json"
  test -f "$REPO_DIR/gemini-extension.json"
  test -f "$REPO_DIR/GEMINI.md"
  test -f "$REPO_DIR/CLAUDE.md"
  test -f "$REPO_DIR/AGENTS.md"
  for sk in writing-arch-specs socratic-brainstorming subagent-two-stage-review systematic-debugging-gate verification-before-completion sdd-contract-lock; do
    test -f "$REPO_DIR/.agents/skills/$sk/SKILL.md"
    test -f "$REPO_DIR/.claude/skills/$sk/SKILL.md"
  done
  for ag in goldfish-builder cold-auditor repair-agent; do
    test -f "$REPO_DIR/.agents/agents/$ag.md"
    test -f "$REPO_DIR/.claude/agents/$ag.md"
  done
  for cmd in sdd-grill sdd-lock sdd-implement sdd-audit sdd-archive sdd-rollback; do
    test -f "$REPO_DIR/.claude/commands/$cmd.md"
    test -f "$REPO_DIR/.agents/workflows/$cmd.md"
  done
  python3 "$REPO_DIR/bin/sdd-harness" audit-score --p0 0 --p1 0 --p2 1 >/dev/null
  echo "[PASS] All Antigravity (agy), Claude Code (claude), and Gemini CLI (gemini) plugin files verified!"
  exit 0
fi

if [[ "$MODE" == "global" ]]; then
  mkdir -p "$HOME/.local/bin"
  cp "$REPO_DIR/bin/sdd-harness" "$HOME/.local/bin/sdd-harness"
  chmod +x "$HOME/.local/bin/sdd-harness"
  echo "[+] Installed CLI: $HOME/.local/bin/sdd-harness"

  if [[ "$TARGET" == "all" || "$TARGET" == "agy" || "$TARGET" == "gemini" ]]; then
    AGY_CONFIG="$HOME/.gemini/config"
    mkdir -p "$AGY_CONFIG/plugins/dualloop-sdd" "$AGY_CONFIG/skills" "$AGY_CONFIG/agents"
    cp -r "$REPO_DIR/.agents/plugins/dualloop-sdd/"* "$AGY_CONFIG/plugins/dualloop-sdd/"
    cp -r "$REPO_DIR/.agents/skills/"* "$AGY_CONFIG/skills/"
    cp -r "$REPO_DIR/.agents/agents/"* "$AGY_CONFIG/agents/"
    echo "[+] Installed Google Antigravity (agy) plugin & skills into $AGY_CONFIG/"
  fi

  if [[ "$TARGET" == "all" || "$TARGET" == "claude" ]]; then
    CLAUDE_DIR="$HOME/.claude"
    mkdir -p "$CLAUDE_DIR/skills" "$CLAUDE_DIR/agents" "$CLAUDE_DIR/commands" "$CLAUDE_DIR/hooks"
    cp -r "$REPO_DIR/.claude/skills/"* "$CLAUDE_DIR/skills/"
    cp -r "$REPO_DIR/.claude/agents/"* "$CLAUDE_DIR/agents/"
    cp -r "$REPO_DIR/.claude/commands/"* "$CLAUDE_DIR/commands/"
    cp "$REPO_DIR/scripts/verify_test_lock_hook.py" "$CLAUDE_DIR/hooks/verify_test_lock_hook.py"
    chmod +x "$CLAUDE_DIR/hooks/verify_test_lock_hook.py"
    echo "[+] Installed Claude Code (claude) skills, subagents, slash commands, and hooks into $CLAUDE_DIR/"
  fi
else
  if [[ -z "$DEST_DIR" ]]; then
    DEST_DIR="$(pwd)"
  fi
  mkdir -p "$DEST_DIR/bin" "$DEST_DIR/scripts"
  if [[ "$(cd "$DEST_DIR" && pwd)" != "$REPO_DIR" ]]; then
    cp "$REPO_DIR/bin/sdd-harness" "$DEST_DIR/bin/sdd-harness"
    chmod +x "$DEST_DIR/bin/sdd-harness"
    cp "$REPO_DIR/scripts/verify_test_lock_hook.py" "$DEST_DIR/scripts/verify_test_lock_hook.py"
    chmod +x "$DEST_DIR/scripts/verify_test_lock_hook.py"
    cp -r "$REPO_DIR/.agents" "$DEST_DIR/"
    cp -r "$REPO_DIR/.claude" "$DEST_DIR/"
    cp -r "$REPO_DIR/.claude-plugin" "$DEST_DIR/"
    cp "$REPO_DIR/gemini-extension.json" "$DEST_DIR/"
    for doc in GEMINI.md CLAUDE.md AGENTS.md; do
      if [[ ! -f "$DEST_DIR/$doc" ]]; then
        cp "$REPO_DIR/$doc" "$DEST_DIR/$doc"
      fi
    done
  fi
  python3 "$DEST_DIR/bin/sdd-harness" init --workspace "$DEST_DIR"
  echo "[+] Installed Dual-Loop SDD + OO-Harness into project: $DEST_DIR"
fi
