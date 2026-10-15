# `slides/` — 36-Slide Widescreen Deck & 7-Module End-to-End Video Curriculum

This directory contains the complete widescreen (`16:9`) presentation slide deck, tripartite speaker notes, and narrated `1080p` step-by-step lecture videos for **`SDD-Crash-Course`**.

## 1. Files in `slides/`

- **[`SDD_Crash_Course_Slides.pdf`](./SDD_Crash_Course_Slides.pdf)**: Compiled 36-slide widescreen (`16:9`) presentation PDF covering Foundations + `TaskFlow` Labs 01–06 step-by-step.
- **[`SDD_Crash_Course_Slides.tex`](./SDD_Crash_Course_Slides.tex)**: Editable LaTeX/TikZ source for all 36 slides.
- **[`SPEAKER_NOTES.md`](./SPEAKER_NOTES.md)**: Complete 36-slide instructor script with `PURPOSE`, `VERBAL SCRIPT`, and `TRANSITION` for every slide.
- **[`SDD_Crash_Course_Lecture.mp4`](./SDD_Crash_Course_Lecture.mp4)**: Master Full-Course `1080p` Narrated Lecture Video (all 36 slides, Modules 01–07 end-to-end).
- **[`build_video.py`](./build_video.py)**: Automated parallel TTS + FFmpeg video synthesis pipeline that builds both the 7 standalone module MP4s (`modules/`) and the master full-course video.

## 2. Step-by-Step Module Videos (`slides/modules/`)

| Module | Video File | Slide Range | Topics & `TaskFlow` Lab Walkthrough |
| :--- | :--- | :--- | :--- |
| **Module 01** | [`modules/Module_01_Foundations_and_Dual_Engine.mp4`](./modules/Module_01_Foundations_and_Dual_Engine.mp4) | Slides 01–06 | Specificational Coding vs. Conversational Coding, the Spec Triangle (`Apply`, `Sync`, `Clean`), Karpathy's Software 3.0 Generation–Verification Loop & 4 Agent Rules, 3 SDD Maturity Levels, Conductor Engine, OpenSpec Engine, and `@writing-arch-specs` Dual-Engine Wiring |
| **Module 02 (Lab 01)** | [`modules/Module_02_Lab01_Greenfield_Todo_List.mp4`](./modules/Module_02_Lab01_Greenfield_Todo_List.mp4) | Slides 07–11 | **Lab 01 Step-by-Step (`TodoList`)**: Greenfield Proposals to Specs via Socratic Grilling (`Q1..Q3`), `openspec/specs/todo-list/spec.md` (`REQ-0001..0004`), `ADR-0001` & `ADR-0002`, 7-Section Conductor `spec.md` & `plan.md`, `todo_list.py`, and `./self_diagnose.sh` |
| **Module 03 (Lab 02)** | [`modules/Module_03_Lab02_Brownfield_Task_Organizer.mp4`](./modules/Module_03_Lab02_Brownfield_Task_Organizer.mp4) | Slides 12–16 | **Lab 02 Step-by-Step (`TaskOrganizer`)**: Brownfield Spec Recovery on `service/task_organizer.py`, `REQ-0001..0004`, lowercase tag normalization & priority ordering (`ADR-0001-tag-normalization.md`), and `./self_diagnose.sh` |
| **Module 04 (Lab 03)** | [`modules/Module_04_Lab03_TDD_Habit_Tracker.mp4`](./modules/Module_04_Lab03_TDD_Habit_Tracker.mp4) | Slides 17–21 | **Lab 03 Step-by-Step (`HabitTracker`)**: From Approved Specs (`REQ-0001..0004`) to Red-Green-Refactor TDD on `habit_tracker.py`, 1:1 `test_req0001..0004` unit tests, `git notes` & `[checkpoint: sha]`, and `./self_diagnose.sh` |
| **Module 05 (Lab 04)** | [`modules/Module_05_Lab04_Drift_and_Scorecard_Refactoring.mp4`](./modules/Module_05_Lab04_Drift_and_Scorecard_Refactoring.mp4) | Slides 22–26 | **Lab 04 Step-by-Step (`DailyPlanner`)**: Detecting `REQ-0003` off-by-one boundary drift (`>=` vs. `>`) in `service/daily_planner.py`, 5-Step Scorecard Triage (`scorecard.md`), `Out of Scope` guardrail (`F-02..F-04`), surgical fix in `schedule_task()`, and `./self_diagnose.sh` |
| **Module 06 (Lab 05)** | [`modules/Module_06_Lab05_SDD_Code_Review_and_Stacked_PRs.mp4`](./modules/Module_06_Lab05_SDD_Code_Review_and_Stacked_PRs.mp4) | Slides 27–31 | **Lab 05 Step-by-Step (`NotesBoard`)**: SDD Code Review on `subpar_change.patch`, catching the 3 violations (`reversed()` breaking `REQ-0002`, un-specced `pin_note`, missing `KeyError`), syncing `REQ-0004`, Stacked Multi-PR `tasks.md` batching (`PR N+1`), and `./self_diagnose.sh` |
| **Module 07 (Lab 06)** | [`modules/Module_07_Lab06_Capstone_SSOT_and_Rebuild_Test.mp4`](./modules/Module_07_Lab06_Capstone_SSOT_and_Rebuild_Test.mp4) | Slides 32–36 | **Lab 06 Capstone Step-by-Step (`TaskFlowBoard`)**: The 8-Section `SPEC.md` for `TaskFlowBoard`, 3-Phase Clean-Room Rebuild Test with `chmod -R a-w` adversarial test isolation, Master Diagnostic Checklist, and `./self_diagnose_all.sh` (`24/24` tests) |
