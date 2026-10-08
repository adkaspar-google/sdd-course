# Claude Code Native Track Playbook (`claude_code_native`)

This playbook documents how `SDD-Crash-Course` runs natively in **Claude Code** on the `claude` branch by combining the Claude Code support shipped by **Conductor (`0.3.0`)** and **OpenSpec (`1.14.1`)** with Claude Code's built-in session, permission, and review primitives.

---

## 1. Ownership & Component Topology

Nothing in this track re-implements a capability that Conductor, OpenSpec, or Claude Code already provides:

| Stage | Owner | Interface |
| :--- | :--- | :--- |
| **Project context** | Conductor | `conductor/index.md` and the files it links, re-read by every Conductor skill |
| **Clarify, spec, plan** | Conductor, OpenSpec | `/conductor:conductor-new-track`, `/opsx:explore`, `/opsx:propose` |
| **Spec format rules** | This repo | `.agents/skills/writing-arch-specs/SKILL.md`, `openspec/config.yaml` |
| **TDD implementation** | Conductor, OpenSpec | `/conductor:conductor-implement`, `/opsx:apply` |
| **Review against the spec** | Conductor, OpenSpec | `/conductor:conductor-review`, `/opsx:verify` |
| **Bug review** | Claude Code | built-in `/code-review` |
| **Read-only exploration** | Claude Code | `plan mode` |
| **Clean context for implementation** | Claude Code | a new session, or `/clear` |
| **Keep working until done** | Claude Code | `/goal` |
| **Locked files** | Claude Code | `permissions.deny` rules |
| **Deterministic pass/fail** | This repo | `labs/*/self_diagnose.sh`, CI |

### Conductor Skill Names in Claude Code
When installed via `claude plugin install conductor@conductor --scope project`, Conductor exposes six skills under the `/conductor:` namespace:
- `/conductor:conductor-setup`
- `/conductor:conductor-new-track`
- `/conductor:conductor-implement`
- `/conductor:conductor-review`
- `/conductor:conductor-revert`
- `/conductor:conductor-status`

Note that `.agents/skills/writing-arch-specs/` remains at `.agents/skills/writing-arch-specs/` because Conductor's skills resolve project skills from `.agents/skills/`.

---

## 2. Learner Session Flow

1. From the repository root, on a personal branch, launch learner mode:
   ```bash
   claude --settings .claude/learner.settings.json
   ```
2. **Explore in `plan mode`**: Inspect the starting proposal, specification, or brownfield code. Nothing is written during exploration.
3. **Specify with Conductor and OpenSpec**: Run the Conductor (`/conductor:conductor-new-track`) and OpenSpec (`/opsx:explore`, `/opsx:propose`) commands named in the lab's walkthrough. These tools write to the root `conductor/tracks/<id>/` and `openspec/changes/<id>/`; collect your lab deliverables under `labs/<lab>/work/` following the layout in Section 3 below.
4. **Human approval checkpoint**: Read the generated spec and plan, run `git status --short`, and confirm only specification artifacts changed before any implementation begins.
5. **Start a new session for implementation and set a `/goal`**: In labs 03 through 06, start a clean session (or run `/clear`) and set the `/goal` defined in the lab's `## Claude Code Track` section.
6. **Run targetable self-diagnosis**:
   ```bash
   ./labs/<lab>/self_diagnose.sh work
   ```

---

## 3. What `TARGET_DIR` (`work/`) Must Contain Per Lab

Each `labs/*/self_diagnose.sh` accepts an optional `TARGET_DIR` positional argument (defaulting to `expected_output`). When grading your own work via `./labs/<lab>/self_diagnose.sh work`, place the following files in `labs/<lab>/work/`:

| Lab | Read from `TARGET_DIR` (`work/`) | Always read from the lab |
| :--- | :--- | :--- |
| **`01`** | `openspec/specs/rate-limiter/spec.md`, `conductor/tracks/rate_limiter_mvp/spec.md`, `ADR-0001-storage-engine.md`, `ADR-0002-sync-protocol.md`; `test_*.py` optional | none |
| **`02`** | `openspec/specs/lease-manager/spec.md`, `ADR-0001-fencing-tokens.md` | `service/` tests |
| **`03`** | `test_circuitbreaker.py` and the module it imports (`circuitbreaker.py`) | none |
| **`04`** | `spec.md`, `test_*.py` and the module they import | `service/quota_allocator.py` (must still show the bug) |
| **`05`** | `openspec/specs/kv-cache/spec.md`, `tasks.md`, `test_*.py` and the module they import | none |
| **`06`** | `coursepulse.py` | `SPEC.md`, `adversarial_tests/` |

---

## 4. Guarantees & Verification Authority

- **File-tool permission rules vs. OS sandboxing**: The `permissions.deny` rules in `.claude/settings.json` (`Edit(**/adversarial_tests/**)`) and `.claude/learner.settings.json` (`Read(**/expected_output/**)` and `Edit(**/adversarial_tests/**)`) guard Claude's file tools (`Read`, `Edit`, `Write`) and are **not** an operating-system security boundary against arbitrary shell commands.
- **Model-judged `/goal` vs. deterministic grading**: In Claude Code, `/goal` completion is judged by a model from the conversation transcript.
- **Deterministic authority**: The deterministic authority for pass/fail grading is always `./labs/<lab>/self_diagnose.sh` (and `./self_diagnose_all.sh` in CI).
