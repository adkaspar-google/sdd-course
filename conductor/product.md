# Product Definition: SDD-Crash-Course & TaskFlow Workspace

## Vision
Provide a self-contained, beginner-friendly hands-on playground for mastering **Specificational Coding / Spec-Driven Development (SDD)**, **Conductor**, **OpenSpec**, and **Spec-as-Single-Source-of-Truth (`SPEC.md`)** through one unified, everyday application: **`TaskFlow` (Personal Task & Habit Tracker)**.

## Target Personas
1. **Software Engineering Students & Developers**: Learning how to move from conversational "Vibe Coding" and ephemeral planning mode to persistent, test-verified Spec-Driven Development.
2. **Engineering Leads & Architects**: Adopting Dual-Engine SDD (`OpenSpec` capability deltas + `Conductor` TDD tracks + `SPEC.md` clean-room rebuild testing) on greenfield and brownfield codebases.

## Unified Application Evolution (`TaskFlow` Across 6 Progressive Labs)
- **Lab 01 (`todo-list`)**: Greenfield To-Do List (`todo_list.py`) — turning an informal product proposal into an OpenSpec capability contract (`REQ-0001..REQ-0004`), Socratic clarification answers ("The Grill"), ADRs, and a 7-section Conductor Track Spec.
- **Lab 02 (`task-organizer`)**: Brownfield Tag & Priority Organizer (`task_organizer.py`) — reverse-engineering undocumented working code into a synchronized OpenSpec contract (`Sync Spec`) and ADR without touching production code.
- **Lab 03 (`habit-tracker`)**: Daily Habit Streak Counter (`habit_tracker.py`) — actuating an approved spec (`Act on Spec` / `Apply`) into 1-to-1 traceable Red-Green-Refactor TDD tests (`test_req0001..0004`) and code.
- **Lab 04 (`daily-planner`)**: Daily Time-Budget Planner (`daily_planner.py`) — catching a 1-character off-by-one spec drift bug (`>=` vs. `>`) on exact budget fit (`REQ-0003`) and locking non-critical ideas in `Out of Scope`.
- **Lab 05 (`notes-board`)**: Quick Notes Board (`notes_board.py`) — reviewing a flawed PR patch (`subpar_change.patch`) that broke chronological ordering (`REQ-0002`) and added `pin_note` without updating the spec (`REQ-0004`), then decomposing into Stacked PR batches.
- **Lab 06 (`taskflow-board`)**: Unified `TaskFlowBoard` Kanban Service (`taskflow_app.py`) — executing a Clean-Room Rebuild Test where source code is generated as a compiled artifact of the 8-section `SPEC.md` alone and verified against read-only adversarial tests.
