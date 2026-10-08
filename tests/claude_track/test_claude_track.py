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

"""Verification suite for the Claude Code Native Track (REQ-0001..REQ-0010)."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[2]

LAB_NAMES = [
    "lab_01_greenfield_proposals_to_specs",
    "lab_02_brownfield_spec_recovery",
    "lab_03_from_specs_to_tdd_code",
    "lab_04_drift_detection_and_5step_refactoring",
    "lab_05_sdd_code_review_and_stacked_prs",
    "lab_06_capstone_ssot_and_rebuild_test",
]

EXPECTED_SEVEN_SECTIONS = [
    "Overview",
    "Architecture & Component Topology",
    "Functional Requirements",
    "Non-Functional Requirements",
    "Acceptance Criteria",
    "Out of Scope",
    "Verification Commands",
]


class TestClaudeCodeNativeTrack(unittest.TestCase):
  """Automated acceptance tests for REQ-0001 through REQ-0010."""

  def test_req0001_default_target_unchanged(self) -> None:
    proc = subprocess.run(
        [str(REPO_ROOT / "self_diagnose_all.sh")],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
    self.assertIn("[ALL PASSED] 6/6", proc.stdout)

  def test_req0001_empty_target_fails(self) -> None:
    for lab in LAB_NAMES:
      script = REPO_ROOT / "labs" / lab / "self_diagnose.sh"
      with tempfile.TemporaryDirectory() as tmpdir:
        proc = subprocess.run(
            [str(script), tmpdir],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(
            proc.returncode,
            0,
            msg=f"{lab} unexpectedly passed on empty target {tmpdir}",
        )
        combined = proc.stdout + "\n" + proc.stderr
        self.assertTrue(
            any(
                line.startswith("[FAIL]")
                for line in combined.splitlines()
            ),
            msg=f"{lab} did not print a line starting with [FAIL]: {combined}",
        )

    # Also verify Lab 01 prints a line starting with [SKIP] when test_*.py is absent
    lab01_dir = REPO_ROOT / "labs" / "lab_01_greenfield_proposals_to_specs"
    with tempfile.TemporaryDirectory() as tmpdir:
      tmp_path = Path(tmpdir)
      shutil.copytree(
          lab01_dir / "expected_output", tmp_path, dirs_exist_ok=True
      )
      for test_file in tmp_path.glob("test_*.py"):
        test_file.unlink()
      proc = subprocess.run(
          [str(lab01_dir / "self_diagnose.sh"), str(tmp_path)],
          cwd=str(REPO_ROOT),
          capture_output=True,
          text=True,
          check=False,
      )
      self.assertEqual(proc.returncode, 0, msg=proc.stdout + "\n" + proc.stderr)
      self.assertTrue(
          any(
              line.startswith("[SKIP]")
              for line in proc.stdout.splitlines()
          ),
          msg=f"Lab 01 did not print [SKIP] when test_*.py was omitted: {proc.stdout}",
      )

  def test_req0001_copied_reference_passes(self) -> None:
    for lab in LAB_NAMES:
      lab_dir = REPO_ROOT / "labs" / lab
      script = lab_dir / "self_diagnose.sh"
      with tempfile.TemporaryDirectory() as tmpdir:
        shutil.copytree(
            lab_dir / "expected_output", tmpdir, dirs_exist_ok=True
        )
        proc = subprocess.run(
            [str(script), tmpdir],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(
            proc.returncode,
            0,
            msg=f"{lab} failed on copied expected_output: {proc.stdout}\n{proc.stderr}",
        )

  def test_req0002_single_seven_section_anatomy(self) -> None:
    skill_text = (
        REPO_ROOT / ".agents" / "skills" / "writing-arch-specs" / "SKILL.md"
    ).read_text(encoding="utf-8")
    sec1_match = re.search(
        r"## 1\..*?(?=\n## 2\.)", skill_text, flags=re.DOTALL
    )
    self.assertIsNotNone(sec1_match)
    skill_sections = re.findall(
        r"^[1-7]\.\s+\*\*(.+?)\*\*", sec1_match.group(0), flags=re.MULTILINE
    )
    self.assertEqual(skill_sections, EXPECTED_SEVEN_SECTIONS)

    playbook_text = (
        REPO_ROOT / "playbooks" / "DUAL_ENGINE_CONDUCTOR_OPENSPEC_PLAYBOOK.md"
    ).read_text(encoding="utf-8")
    sec2_match = re.search(
        r"## 2\..*?(?=\n## 3\.)", playbook_text, flags=re.DOTALL
    )
    self.assertIsNotNone(sec2_match)
    sec2_text = sec2_match.group(0)
    playbook_sections = re.findall(
        r"^\s*[1-7]\.\s+\*\*(.+?)\*\*", sec2_text, flags=re.MULTILINE
    )
    self.assertEqual(playbook_sections, EXPECTED_SEVEN_SECTIONS)
    self.assertEqual(skill_sections, playbook_sections)

  def test_req0003_claude_md_budget_and_no_imports(self) -> None:
    claude_md = REPO_ROOT / "CLAUDE.md"
    self.assertTrue(claude_md.is_file(), "CLAUDE.md must exist at repo root")
    text = claude_md.read_text(encoding="utf-8")
    lines = text.splitlines()
    self.assertLessEqual(
        len(lines), 40, f"CLAUDE.md has {len(lines)} lines (max 40)"
    )
    self.assertIn("CI=true python3 -m unittest", text)
    self.assertIn("REQ-XXXX", text)
    self.assertIn("test_reqXXXX_*", text)
    self.assertIn("adversarial_tests/", text)
    self.assertIn("read-only", text)
    self.assertIn("`conductor/workflow.md`", text)
    self.assertIsNone(
        re.search(r"(?m)^\s*@\S+", text),
        "CLAUDE.md must not contain @path imports",
    )

  def test_req0004_workflow_has_change_tiering(self) -> None:
    workflow_text = (REPO_ROOT / "conductor" / "workflow.md").read_text(
        encoding="utf-8"
    )
    self.assertIn("## 5. Change Tiering", workflow_text)
    self.assertIn("REQ-XXXX", workflow_text)
    self.assertIn("public function", workflow_text)
    self.assertIn("dependency", workflow_text)
    self.assertIn("more than one non-test source file", workflow_text)

  def test_req0005_conductor_plugin_enabled_and_skill_not_duplicated(
      self,
  ) -> None:
    settings = json.loads(
        (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    self.assertEqual(
        settings.get("enabledPlugins", {}).get("conductor@conductor"), True
    )
    self.assertTrue(
        (
            REPO_ROOT / ".agents" / "skills" / "writing-arch-specs" / "SKILL.md"
        ).is_file()
    )
    self.assertFalse(
        (REPO_ROOT / ".claude" / "skills" / "writing-arch-specs").exists()
    )
    for subdir in ("hooks", "agents"):
      d = REPO_ROOT / ".claude" / subdir
      if d.exists():
        self.assertEqual(list(d.rglob("*")), [])
    skills_dir = REPO_ROOT / ".claude" / "skills"
    self.assertTrue(skills_dir.is_dir())
    for child in skills_dir.iterdir():
      self.assertTrue(
          child.name.startswith("openspec-"),
          f"Unexpected directory in .claude/skills/: {child.name}",
      )
    playbook_text = (
        REPO_ROOT / "playbooks" / "CLAUDE_CODE_PLAYBOOK.md"
    ).read_text(encoding="utf-8")
    for skill in (
        "/conductor:conductor-setup",
        "/conductor:conductor-new-track",
        "/conductor:conductor-implement",
        "/conductor:conductor-review",
        "/conductor:conductor-revert",
        "/conductor:conductor-status",
    ):
      self.assertIn(skill, playbook_text)

  def test_req0006_opsx_commands_present(self) -> None:
    opsx_dir = REPO_ROOT / ".claude" / "commands" / "opsx"
    for cmd in ("explore.md", "propose.md", "apply.md", "verify.md", "archive.md"):
      self.assertTrue(
          (opsx_dir / cmd).is_file(), f"Missing .claude/commands/opsx/{cmd}"
      )
    for skill_dir in (
        "openspec-explore",
        "openspec-propose",
        "openspec-apply-change",
        "openspec-verify-change",
        "openspec-archive-change",
    ):
      self.assertTrue(
          (REPO_ROOT / ".claude" / "skills" / skill_dir / "SKILL.md").is_file(),
          f"Missing .claude/skills/{skill_dir}/SKILL.md",
      )

  def test_req0007_locked_verifier_deny_rule(self) -> None:
    settings = json.loads(
        (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    deny_rules = settings.get("permissions", {}).get("deny", [])
    self.assertIn("Edit(**/adversarial_tests/**)", deny_rules)
    self.assertNotIn("Read(**/expected_output/**)", deny_rules)

  def test_req0008_learner_settings_deny_rules(self) -> None:
    learner_settings = json.loads(
        (REPO_ROOT / ".claude" / "learner.settings.json").read_text(
            encoding="utf-8"
        )
    )
    deny_rules = learner_settings.get("permissions", {}).get("deny", [])
    self.assertIn("Read(**/expected_output/**)", deny_rules)
    self.assertIn("Edit(**/adversarial_tests/**)", deny_rules)

  def test_req0009_walkthroughs_end_with_claude_track(self) -> None:
    for idx, lab in enumerate(LAB_NAMES, start=1):
      wt_path = REPO_ROOT / "labs" / lab / "WALKTHROUGH.md"
      text = wt_path.read_text(encoding="utf-8")
      h2_headings = re.findall(r"^##\s+(.+?)\s*$", text, flags=re.MULTILINE)
      self.assertTrue(h2_headings, f"No H2 headings in {wt_path}")
      self.assertEqual(
          h2_headings[-1],
          "Claude Code Track",
          f"Last H2 heading in {wt_path} must be 'Claude Code Track'",
      )

      section_text = text.split("## Claude Code Track", 1)[1]
      pos_start = section_text.find(
          "claude --settings .claude/learner.settings.json"
      )
      pos_checkpoint = section_text.find("git status --short")
      pos_final = section_text.rfind(f"./labs/{lab}/self_diagnose.sh work")

      self.assertNotEqual(
          pos_start, -1, f"Missing learner start command in {lab}"
      )
      self.assertNotEqual(
          pos_checkpoint, -1, f"Missing human approval checkpoint in {lab}"
      )
      self.assertNotEqual(
          pos_final, -1, f"Missing final self_diagnose.sh work command in {lab}"
      )
      self.assertLess(pos_start, pos_checkpoint, f"Order violation in {lab}")
      self.assertLess(pos_checkpoint, pos_final, f"Order violation in {lab}")

      if idx >= 3:
        pos_session = section_text.find("Start a new session")
        goal_line = (
            f"/goal ./labs/{lab}/self_diagnose.sh work exits 0, shown by"
            " running it; no file under adversarial_tests/ or"
            " expected_output/ is modified; or stop after 20 turns."
        )
        pos_goal = section_text.find(goal_line)
        self.assertNotEqual(
            pos_session, -1, f"Missing new session instruction in {lab}"
        )
        self.assertNotEqual(
            pos_goal, -1, f"Missing exact /goal line in {lab}"
        )
        self.assertLess(pos_checkpoint, pos_session, f"Order violation in {lab}")
        self.assertLess(pos_session, pos_goal, f"Order violation in {lab}")
        self.assertLess(pos_goal, pos_final, f"Order violation in {lab}")

      if idx == 2:
        self.assertIn("plan mode", section_text)
        self.assertIn("subagents", section_text)
        self.assertIn("service/leasemanager.py", section_text)
      elif idx == 4:
        self.assertIn("plan mode", section_text)
        self.assertIn("F-01", section_text)
      elif idx == 5:
        self.assertIn("/conductor:conductor-review", section_text)
        self.assertIn("/opsx:verify", section_text)
        self.assertIn("/code-review", section_text)
        self.assertIn("requirement or correctness gaps", section_text)
      elif idx == 6:
        self.assertIn("SPEC.md", section_text)
        self.assertIn("only input", section_text)

      # Verify existing content on main is untouched (added lines only)
      diff_proc = subprocess.run(
          ["git", "diff", "main", "--", str(wt_path)],
          cwd=str(REPO_ROOT),
          capture_output=True,
          text=True,
          check=False,
      )
      if diff_proc.returncode == 0 and diff_proc.stdout:
        removed_lines = [
            line
            for line in diff_proc.stdout.splitlines()
            if line.startswith("-") and not line.startswith("---")
        ]
        self.assertEqual(
            removed_lines,
            [],
            f"Existing lines were modified/removed in {wt_path}: {removed_lines}",
        )

  def test_req0010_playbook_and_readme_content(self) -> None:
    playbook_path = REPO_ROOT / "playbooks" / "CLAUDE_CODE_PLAYBOOK.md"
    self.assertTrue(playbook_path.is_file())
    playbook_text = playbook_path.read_text(encoding="utf-8")
    self.assertLessEqual(
        len(playbook_text.splitlines()),
        150,
        "playbooks/CLAUDE_CODE_PLAYBOOK.md must not exceed 150 lines",
    )
    self.assertNotIn("policies/conductor.toml", playbook_text)
    for required_item in (
        "/conductor:conductor-new-track",
        "/opsx:explore",
        "/opsx:propose",
        "/conductor:conductor-implement",
        "/opsx:apply",
        "/conductor:conductor-review",
        "/opsx:verify",
        "/code-review",
        "plan mode",
        "/goal",
        "permissions.deny",
        "claude --settings .claude/learner.settings.json",
        "file tools",
        "shell commands",
        "transcript",
        "self_diagnose.sh",
    ):
      self.assertIn(required_item, playbook_text)

    readme_text = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    for required_readme in (
        "claude plugin marketplace add gemini-cli-extensions/conductor",
        "claude plugin install conductor@conductor --scope project",
        "npm install -g @fission-ai/openspec@latest",
        "0.3.0",
        "1.14.1",
        "third-party",
        "permissions.deny",
    ):
      self.assertIn(required_readme, readme_text)


if __name__ == "__main__":
  unittest.main()
