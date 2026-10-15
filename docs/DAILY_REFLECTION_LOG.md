# Daily Course Reflection & Self-Improvement Ledger (`SDD-Crash-Course`)

> **Course:** `SDD-Crash-Course` (`Conductor` + `OpenSpec` + `SPEC.md` Single Source of Truth)  
> **Author:** Alejandro Kaspar - AI Forward Deployed Engineer  
> **Operating Policy (`Improve Only If Needed`):**  
> Every daily reflection performs deep research across trending Spec-Driven Development (SDD) courses, video tutorials, practitioner benchmarks, and upstream tool releases (`Conductor`, `OpenSpec`, `GitHub Spec Kit`, `Kiro`, `Tessl`, `BMAD`).  
> - If the course is already aligned and superior on all researched dimensions, log `Decision: NO_CHANGE_NEEDED` and make **zero** unnecessary edits to labs, slides, or the Coursebook.  
> - If a genuine misalignment, stale reference, upstream CLI change, or high-signal new SDD topic is identified, log `Decision: IMPROVE`, apply the surgical improvement across `main` and `claude`, verify `./self_diagnose_all.sh` + `tests/claude_track` + `cross`, and push.

---

## 2026-10-15 — Day 1 Deep Research & Course Reflection

- **Decision:** `IMPROVE` (Surgical alignment + stale-reference remediation)
- **External & Upstream Sources Researched:**
  1. **`Fission-AI/OpenSpec` (`@fission-ai/openspec` 2026 Changelog & Docs)**:
     - Checked CLI command surface (`openspec init`, `openspec list --specs`, `openspec validate --all --strict`, `openspec update`) and `/opsx:*` workflow (`explore`, `propose`, `apply`, `verify`, `archive`).
     - *New Upstream Guardrail Found:* Requirement descriptions exceeding `500` characters (`MAX_REQUIREMENT_DESCRIPTION_LENGTH = 500`) now trigger warnings that fail `openspec validate --strict` in CI. Checking off all tracked tasks in `tasks.md` also explicitly cues `/opsx:verify` before `/opsx:archive`.
  2. **`gemini-cli-extensions/conductor` (2026 Releases)**:
     - Checked `/conductor:setup`, `/conductor:newTrack`, `/conductor:implement`, `/conductor:review` (`/conductor:conductor-review` on Claude Code), `/conductor:status`, and `/conductor:revert`. Confirmed automated post-implementation review and `## Phase: Review Fixes` alignment.
  3. **Trending 2025–2026 SDD Courses, Videos & Industry Analyses**:
     - Birgitta Böckeler (Thoughtworks / `martinfowler.com`): *"Understanding Spec-Driven Development: Kiro, spec-kit, and Tessl"* (3-level SDD maturity taxonomy: `Spec-First`, `Spec-Anchored`, `Spec-as-Source`).
     - Paul Everitt (JetBrains / YouTube): *"Full Course: Spec-Driven Development with Coding Agents"* (project constitutions, legacy brownfield onboarding, portable agent skills).
     - Comparative evaluations of **OpenSpec** vs. **GitHub Spec Kit (`spec-kit`)**, **Amazon Kiro**, **Tessl**, and **BMAD**.
- **Repository Alignment Audit Findings:**
  1. **Stale Reference Scan (`main` & `claude`):** Found 14 residual references to the retired distributed-systems lab names (`ratelimiter`, `leasemanager`, `circuitbreaker`, `kvcache`, `coursepulse`) inside `slides/README.md`, `slides/build_video.py`, `README.md` (video table), and the filenames of `Module_02..04` in `slides/modules/`.
  2. **Playbook Ecosystem & Validator Gap:** `playbooks/DUAL_ENGINE_CONDUCTOR_OPENSPEC_PLAYBOOK.md` lacked a direct comparison table contrasting `Conductor + OpenSpec + SPEC.md` against `GitHub Spec Kit`, `Amazon Kiro`, and `Tessl`, as well as OpenSpec's 2026 `MAX_REQUIREMENT_DESCRIPTION_LENGTH = 500` `openspec validate --strict` rule.
- **Surgical Improvements Applied & Verified:**
  1. Updated `slides/README.md`, `slides/build_video.py`, and `README.md` and renamed `Module_02_Lab01_Greenfield_Todo_List.mp4`, `Module_03_Lab02_Brownfield_Task_Organizer.mp4`, and `Module_04_Lab03_TDD_Habit_Tracker.mp4` (`0` stale references remaining across the entire repository).
  2. Added **Section 9 (`2026 SDD Tooling Ecosystem Comparison & Strict CI Validation Rules`)** to `playbooks/DUAL_ENGINE_CONDUCTOR_OPENSPEC_PLAYBOOK.md`.
  3. **Metaskill Alignment (`technical-course-creator` Stage 4):** Synthesized internal course/pedagogy skills (`learn-ask-quiz`, `codelab-creation`, `google-drawings-creator`, `strategy-slides-designer`, `vivid-storyteller`, `eli5`, `jetski-labs-courseweaver`) and external open-source course skills (`zarazhangrui/codebase-to-course`, `weihaoqu/gemini-curriculum-designer`, `narosemena/master-instructional-design`, `GarethManning/claude-education-skills`, `full-stack-skills/teaching-skills`) into `~/.gemini/config/skills/technical-course-creator/SKILL.md` and added [`docs/interactive_visual_guide.html`](./interactive_visual_guide.html) (featuring the *Blueprint Metaphor vs. Under-the-Hood* toggle, clickable `①`–`⑤` architecture hotspots, interactive Lab 04 boundary drift simulator, *Common Misconception* `✕` vs. `✓` cards, and a 3-rung graduated hint quiz).
  4. Verified `./self_diagnose_all.sh` (`6/6` labs, `24/24` tests), `tests/claude_track/test_claude_track.py` (`12/12` tests), and `cross` (`✅ All checks passed`).
