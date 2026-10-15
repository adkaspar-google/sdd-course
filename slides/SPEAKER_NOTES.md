# SDD-Crash-Course — Complete 36-Slide End-to-End Speaker Notes (`SPEAKER_NOTES.md`)

---

## MODULE 01: SDD FOUNDATIONS, THE SPEC TRIANGLE & DUAL-ENGINE ARCHITECTURE (SLIDES 01–06)

### Slide 01 — Course Cover: SDD-Crash-Course
- **PURPOSE:** Introduce the 7-module step-by-step curriculum and the unified `TaskFlow` productivity application across all 6 hands-on Python labs.
- **VERBAL SCRIPT:** Welcome to the Spec-Driven Development Crash Course! In this end-to-end engineering course, we move beyond conversational prompting—often called Vibe Coding—and learn how to turn Specifications into our Single Source of Truth using Conductor, OpenSpec, and canonical SPEC dot MD blueprints. Across seven focused modules, we will progressively build and verify TaskFlow—a clean, lightweight personal productivity application—walking step by step through every specification, Architecture Decision Record, test suite, and terminal command across all six labs.
- **TRANSITION:** Let's begin in Module 1 by contrasting conversational Vibe Coding against Specificational Coding and Andrej Karpathy's Software 3.0 loop.

### Slide 02 — Specificational Coding vs. Conversational "Vibe Coding"
- **PURPOSE:** Contrast conversational Vibe Coding with Specificational Coding (Spec-Driven Development and Spec-Driven Testing) and Karpathy's 4 Coding Agent Rules.
- **VERBAL SCRIPT:** Why does conversational Vibe Coding break down on real projects? Because chat prompts disappear as soon as a pull request merges. Without a durable specification, an AI agent silently guesses edge cases—like whether blank task titles are allowed or whether an exact 100 percent time budget should be rejected—and writes sycophantic tests that rubber-stamp broken code. Specificational Coding flips the workflow: the engineer edits and approves a persistent specification artifact, and the agent compiles that spec into production code and one-to-one traceable tests, governed by Karpathy's four rules: Think Before Coding, Simplicity First, Surgical Changes, and Goal-Driven Execution.
- **TRANSITION:** How do Specifications, Code, and Tests stay synchronized over time? Let's examine the Spec Triangle and the three levels of SDD maturity.

### Slide 03 — The Spec Triangle (`Apply`, `Sync`, `Clean`) & 3 SDD Maturity Levels
- **PURPOSE:** Define the 3 Core Spec Actions (`Apply`, `Sync`, `Clean`) across the Spec–Code–Tests triangle and the 3 SDD Maturity Levels.
- **VERBAL SCRIPT:** Every workflow in Spec-Driven Development maps to three fundamental actions on the Spec-Code-Tests triangle. Action 1 is Apply—acting on an approved specification via conductor implement or opsx apply to compile requirement contracts into failing Red tests and minimal Green code, which we practice in Labs 1 and 3. Action 2 is Sync—reconciling code and specifications via opsx explore, opsx verify, and conductor review to extract baseline specs from legacy code in Lab 2 or catch drift in Labs 4 and 5. Action 3 is Clean—archiving active delta changes into openspec specs in Lab 5 and proving in Lab 6 that SPEC dot MD can regenerate the application from scratch in a clean room.
- **TRANSITION:** Now let's inspect the first of our two open-source engines: Conductor.

### Slide 04 — Engine 1: Conductor (Context-Driven Development & TDD Track Execution)
- **PURPOSE:** Explain Conductor's three-step loop (`/conductor:setup`, `/conductor:newTrack`, `/conductor:implement`) and Day-2 commands (`status`, `review`, `revert`).
- **VERBAL SCRIPT:** Our first engine is Conductor, which embodies the rule Measure Twice, Code Once. Running slash conductor setup once initializes your repository constitution inside the conductor directory: product dot MD, tech-stack dot MD, workflow dot MD, and tracks dot MD. Next, slash conductor newTrack runs inside a Plan Mode sandbox—blocking writes outside conductor—and conducts interactive Q and A before emitting a seven-section track spec and phased plan. Finally, slash conductor implement executes strict Red-Green-Refactor Test-Driven Development, recording structured task telemetry in git notes and pausing at phase checkpoints.
- **TRANSITION:** While Conductor governs track execution, how do we manage long-lived capability contracts and feature deltas? Enter Engine 2: OpenSpec.

### Slide 05 — Engine 2: OpenSpec (Two-Plane Architecture, Socratic Grilling & Delta Algebra)
- **PURPOSE:** Explain OpenSpec's Two-Plane model (`openspec/specs/` vs. `openspec/changes/`), Interactive Socratic Prompting ("The Grill"), and the 5-stage archive merge.
- **VERBAL SCRIPT:** Our second engine is OpenSpec, which separates your repository into two planes. Plane 1, openspec specs, is the Elephant—your living system of record organized by capability domain such as todo-list, task-organizer, and notes-board, written with RFC 2119 SHALL and MUST keywords and four-hashtag Gherkin scenarios. Plane 2, openspec changes, is the Goldfish—an isolated delta workspace. When you propose a change, OpenSpec compares the baseline spec against your request and runs Interactive Socratic Grilling—asking three to five targeted boundary questions before writing ADDED, MODIFIED, REMOVED, or RENAMED requirement deltas.
- **TRANSITION:** Let's see how Conductor, OpenSpec, and our `@writing-arch-specs` skill lock together in one repository.

### Slide 06 — Wiring Conductor + OpenSpec + `@writing-arch-specs`
- **PURPOSE:** Show the `conductor/workflow.md` and `conductor/index.md` handshake and the canonical 7-section Track `spec.md` anatomy.
- **VERBAL SCRIPT:** On Slide 6, we wire Conductor and OpenSpec together through conductor index dot MD and conductor workflow dot MD. Whenever a track begins, the agent loads our writing-arch-specs skill, maps every functional requirement in the seven-section Conductor track spec one-to-one to a bracketed REQ-XXXX contract in openspec specs, and enforces one-to-one test naming via test underscore reqXXXX. Together, OpenSpec provides permanent capability contracts and delta merges, while Conductor provides stack locks, TDD checkpoints, and logical git revert.
- **TRANSITION:** Let's jump into Module 2 and apply this exact workflow step by step in Lab 1 on TaskFlow's core To-Do List!

---

## MODULE 02: LAB 01 STEP-BY-STEP — GREENFIELD PROPOSALS TO SPECS (SLIDES 07–11)

### Slide 07 — Lab 01 Step 1: Auditing the Vague Proposal & Socratic Grilling
- **PURPOSE:** Walk through `labs/lab_01_greenfield_proposals_to_specs/proposal.md` and resolve its 3 ambiguities via Socratic Grilling.
- **VERBAL SCRIPT:** Welcome to Module 2, where we walk step by step through Lab 1: Greenfield Proposals to Specs. If you inspect labs slash lab 01 greenfield proposals to specs slash proposal dot MD, you'll see a short product note for TaskFlow's core TodoList class: allow users to add tasks, mark tasks completed, list pending or completed tasks, and delete tasks. Why does Vibe Coding fail here? Because without a spec, an agent guesses whether whitespace-only titles are valid, whether completing an unknown ID raises an error or returns False, and whether deleted IDs get reused. In Step 1, Socratic Grilling asks three crisp questions and locks the answers: trim titles and raise ValueError if empty, raise KeyError in complete task but return a boolean in delete task, and preserve creation order.
- **TRANSITION:** With those three boundary decisions answered, let's move to Step 2 and write our OpenSpec capability contract.

### Slide 08 — Lab 01 Step 2: Authoring the OpenSpec Capability Contract
- **PURPOSE:** Walk through `expected_output/openspec/specs/todo-list/spec.md` (`REQ-0001..REQ-0004`) and its 4-hashtag Gherkin scenarios.
- **VERBAL SCRIPT:** In Step 2 of Lab 1, we author expected output slash openspec slash specs slash todo-list slash spec dot MD. Look at the contract on the left: every requirement has a stable identifier from REQ-0001 through REQ-0004, uses uppercase SHALL and MUST keywords, and includes a four-hashtag Scenario block with GIVEN, WHEN, and THEN clauses. REQ-0001 governs task creation and blank-title validation; REQ-0002 governs marking a task completed and raising KeyError on unknown IDs; REQ-0003 governs get pending and get completed in creation order; and REQ-0004 governs delete task returning True or False.
- **TRANSITION:** Next, in Step 3, let's record WHY we chose an insertion-ordered dictionary and a monotonic ID counter in two Architecture Decision Records.

### Slide 09 — Lab 01 Step 3: Recording Architecture Decision Records (ADRs)
- **PURPOSE:** Explain `ADR-0001-storage-engine.md` (`dict[int, Task]`) and `ADR-0002-id-assignment.md` (monotonic `_next_id` counter vs. `len(tasks) + 1`).
- **VERBAL SCRIPT:** In Step 3, we author two concise Architecture Decision Records. In ADR-0001, we choose Python's insertion-ordered dictionary keyed by integer task ID over a plain list, giving us order-one lookup on complete task and delete task while naturally preserving creation order for get pending and get completed. In ADR-0002, we choose a strictly monotonic next ID counter over len of tasks plus 1. Why? Because if a user creates two tasks, deletes task 1, and adds another task, len of tasks plus 1 would assign ID 2 again and overwrite existing task 2! Recording ADR-0002 prevents any future agent session from introducing ID collision bugs.
- **TRANSITION:** Now let's move to Step 4 and bridge our OpenSpec contract and ADRs into Conductor's 7-section track `spec.md` and phased `plan.md`.

### Slide 10 — Lab 01 Step 4: Authoring the 7-Section Conductor Track `spec.md` & `plan.md`
- **PURPOSE:** Inspect `expected_output/conductor/tracks/todo_list_mvp/spec.md` and `plan.md` in Lab 01.
- **VERBAL SCRIPT:** In Step 4, we generate Conductor's seven-section track spec and two-phase TDD plan under expected output slash conductor slash tracks slash todo list mvp. Look at Section 6, Out of Scope, on the left: we explicitly exclude SQLite persistence, multi-user authentication, and recurring tasks so the agent stays laser-focused on our fifty-line in-memory domain model. On the right, plan dot MD groups the work into Phase 1 for task creation and completion and Phase 2 for filtering and deletion, complete with manual verification checkpoints.
- **TRANSITION:** Let's move to Step 5, inspect the 50-line `todo_list.py` implementation, and run `./self_diagnose.sh`!

### Slide 11 — Lab 01 Step 5: Implementing `todo_list.py` & Running `./self_diagnose.sh`
- **PURPOSE:** Walk through `expected_output/todo_list.py` and the live output of `./labs/lab_01_greenfield_proposals_to_specs/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 5, we inspect expected output slash todo list dot py and run Lab 1's self-diagnosis script. Because our Task dataclass is frozen and immutable, complete task constructs an updated Task instance with completed set to True and stores it at self dot tasks of task ID. When we run self diagnose dot sh on the right, all four requirement-traceable unit tests—test req0001 through test req0004—pass in one millisecond!
- **TRANSITION:** Now that we've built TaskFlow's core To-Do List from scratch, what happens when we inherit an undocumented brownfield module? Let's enter Module 3 for Lab 2!

---

## MODULE 03: LAB 02 STEP-BY-STEP — BROWNFIELD SPEC RECOVERY (SLIDES 12–16)

### Slide 12 — Lab 02 Step 1: Auditing an Undocumented Brownfield Codebase (`task_organizer.py`)
- **PURPOSE:** Introduce `labs/lab_02_brownfield_spec_recovery/service/task_organizer.py` and the read-only `/opsx:explore` (`Sync Spec`) workflow.
- **VERBAL SCRIPT:** Welcome to Module 3, where we walk through Lab 2: Brownfield Spec Recovery. Here, you inherit service slash task organizer dot py—TaskFlow's Tag and Priority Organizer—along with its unit tests, but zero specification files. If you ask an agent to refactor this code without a spec, it might replace the tag normalization loop with a raw tuple or set, silently breaking case-insensitive tag filtering and tag order. Instead, in Step 1, we practice the Sync Spec action by running opsx explore in read-only mode to map every invariant in task organizer dot py before touching anything.
- **TRANSITION:** Let's examine the four behavioral invariants that `/opsx:explore` uncovers inside `task_organizer.py`.

### Slide 13 — Lab 02 Step 2: Extracting the 4 Hidden Behavioral Invariants (`REQ-0001..REQ-0004`)
- **PURPOSE:** Map `add_task`, `filter_by_tag`, and `list_by_priority` in `task_organizer.py` to `REQ-0001..REQ-0004`.
- **VERBAL SCRIPT:** In Step 2, we extract four crisp requirements from task organizer dot py. REQ-0001 validates that titles are non-empty and normalizes priority to high, medium, or low, raising ValueError otherwise. REQ-0002 strips whitespace, lowercases every tag, drops empty strings, and deduplicates tags in first-seen order. REQ-0003 performs case-insensitive tag filtering in filter by tag and returns matching tasks in creation order. Finally, REQ-0004 orders tasks in list by priority from high to medium to low, breaking ties by ascending creation ID.
- **TRANSITION:** Why is write-time tag normalization so important? Let's document that architectural decision in `ADR-0001` in Step 3.

### Slide 14 — Lab 02 Step 3: Why Un-Normalized Tags Break Filtering (`ADR-0001`)
- **PURPOSE:** Walk through `expected_output/ADR-0001-tag-normalization.md` explaining write-time tag normalization and deduplication.
- **VERBAL SCRIPT:** On Slide 14, we capture the data-hygiene rationale in ADR-0001-tag-normalization dot MD. Without write-time normalization, one user tags a task with capital Urgent and another with lowercase urgent plus trailing spaces. As a result, a task accumulates duplicate tags, and calling filter by tag breaks unpredictably. By normalizing every tag via strip dot lower at write time, discarding empty strings, and deduplicating into an immutable tuple in first-seen order, both storage and queries remain 100 percent deterministic.
- **TRANSITION:** Let's move to Step 4 and author the recovered OpenSpec specification and design document.

### Slide 15 — Lab 02 Step 4: Authoring `openspec/specs/task-organizer/spec.md` & `design.md`
- **PURPOSE:** Inspect `expected_output/openspec/specs/task-organizer/spec.md` and `expected_output/design.md`.
- **VERBAL SCRIPT:** In Step 4, we write expected output slash openspec slash specs slash task-organizer slash spec dot MD and expected output slash design dot MD. Look at the recovered REQ-0002 block on the left: when add task is called with tags Urgent, spaced urgent, Backend, and an empty string, the returned OrganizedTask must have tags equal to the lowercase tuple urgent comma backend. Once verified, this spec is promoted to openspec specs, upgrading a legacy module to SDD Maturity Level 2: Spec-Anchored!
- **TRANSITION:** Let's run `./labs/lab_02_brownfield_spec_recovery/self_diagnose.sh` in Step 5 to verify our brownfield recovery.

### Slide 16 — Lab 02 Step 5: Verifying Zero-Regression Brownfield Recovery
- **PURPOSE:** Walk through the checks and terminal output of `./labs/lab_02_brownfield_spec_recovery/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 5, we run Lab 2's self-diagnosis script. It checks that REQ-0001 through REQ-0004 are documented with uppercase RFC 2119 keywords and four-hashtag scenarios, confirms that ADR-0001 and design dot MD are complete, and executes all four brownfield unit tests in service slash test task organizer dot py with zero regressions.
- **TRANSITION:** Now that we can create greenfield specs in Lab 1 and recover brownfield specs in Lab 2, let's enter Module 4 for Lab 3 and drive strict Red-Green-Refactor TDD from an approved specification!

---

## MODULE 04: LAB 03 STEP-BY-STEP — FROM SPECS TO TDD CODE (SLIDES 17–21)

### Slide 17 — Lab 03 Step 1: Inspecting the Approved Habit Tracker Contract
- **PURPOSE:** Walk through `labs/lab_03_from_specs_to_tdd_code/specs/spec.md` (`REQ-0001..REQ-0004`) for TaskFlow's `HabitTracker`.
- **VERBAL SCRIPT:** Welcome to Module 4, where we walk step by step through Lab 3: From Specs to TDD Code. Here, TaskFlow's Daily Habit Streak Tracker already has an approved specification in specs slash spec dot MD with four requirements: REQ-0001 registers a trimmed habit name starting at streak zero; REQ-0002 makes same-day check-ins idempotent so checking in twice on day 10 keeps the streak unchanged, while rejecting past days; REQ-0003 increments the streak by 1 on consecutive next-day check-ins and resets the streak to 1 after a multi-day gap; and REQ-0004 raises KeyError when checking in or querying an unknown habit.
- **TRANSITION:** How do we turn those four requirements into a disciplined TDD execution plan? Let's inspect `tasks.md` in Step 2.

### Slide 18 — Lab 03 Step 2: Decomposing Requirements into Sequenced TDD Tasks
- **PURPOSE:** Show `expected_output/tasks.md` and explain why every requirement maps 1:1 to a `test_reqXXXX_*` unit test.
- **VERBAL SCRIPT:** In Step 2, we decompose REQ-0001 through REQ-0004 into two TDD batches inside expected output slash tasks dot MD. Batch 1 pairs REQ-0001 and REQ-0002 with their failing unit tests first, and Batch 2 pairs REQ-0003 and REQ-0004 with their unit tests. Naming every test method test underscore reqXXXX creates an auditable bi-directional link between your specification and your test suite: whenever a requirement changes in a future pull request, you know immediately which test must be updated first in the Red phase.
- **TRANSITION:** Let's execute Batch 1 (`REQ-0001` and `REQ-0002`) in Step 3.

### Slide 19 — Lab 03 Step 3: Red-Green-Refactor Batch 1 (Registration & Idempotency)
- **PURPOSE:** Compare the failing Red tests (`test_req0001`, `test_req0002`) with the minimal Green implementation in `habit_tracker.py`.
- **VERBAL SCRIPT:** In Step 3, we write test req0001 and test req0002 first in test habit tracker dot py and watch them fail. Look at test req0002 on the bottom left: we check in on Exercise at day 10, which returns streak 1, and immediately check in again at day 10, asserting the streak remains 1 instead of double-counting to 2. On the right, we write the minimal Green code in habit tracker dot py: when day equals last, record checkin returns the current streak immediately as an idempotent no-op.
- **TRANSITION:** Now let's execute Batch 2 (`REQ-0003` Consecutive Streak vs. Gap Reset and `REQ-0004` Unknown Habit `KeyError`) in Step 4.

### Slide 20 — Lab 03 Step 4: Red-Green-Refactor Batch 2 (Streaks & Missing Keys)
- **PURPOSE:** Walk through `record_checkin()` in `expected_output/habit_tracker.py` and `test_req0003` / `test_req0004`.
- **VERBAL SCRIPT:** In Step 4, we implement consecutive streak arithmetic and gap resets in record checkin. Look at the clean branching logic on the left: if key is not in self dot streaks, raise KeyError; if day is less than last, raise ValueError; if day equals last plus 1, increment self dot streaks of key by 1; otherwise—when day is greater than last plus 1 after a missed day—reset self dot streaks of key back to 1. Because we use integer ordinal days rather than wall-clock timestamps, our tests verify multi-day streaks and gap resets in under a millisecond.
- **TRANSITION:** Let's move to Step 5, record our Conductor `git notes` checkpoint, and run `./self_diagnose.sh`!

### Slide 21 — Lab 03 Step 5: Git Notes Audit Trail & Running `./self_diagnose.sh`
- **PURPOSE:** Show Conductor's `git notes` audit trail and the live output of `./labs/lab_03_from_specs_to_tdd_code/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 5, Conductor commits our code, attaches a structured git note linking the commit to REQ-0001 through REQ-0004, and records the phase checkpoint SHA in plan dot MD. When we run Lab 3's self-diagnosis script on the right, all four requirement-traceable unit tests pass in one millisecond!
- **TRANSITION:** What happens when a brownfield service already has a spec, but a subtle bug in the code drifts away from that spec? Let's enter Module 5 for Lab 4!

---

## MODULE 05: LAB 04 STEP-BY-STEP — DRIFT DETECTION & 5-STEP REFACTORING (SLIDES 22–26)

### Slide 22 — Lab 04 Step 1: Detecting Spec-to-Code Drift (`REQ-0003` Off-by-One Bug)
- **PURPOSE:** Compare `specs/spec.md` (`REQ-0003`) against the off-by-one `>=` bug in `labs/lab_04_drift_detection_and_5step_refactoring/service/daily_planner.py`.
- **VERBAL SCRIPT:** Welcome to Module 5, where we walk step by step through Lab 4: Drift Detection and 5-Step Scorecard Refactoring on TaskFlow's Daily Time-Budget Planner. Look at REQ-0003 in specs slash spec dot MD on the left: schedule must admit a task when used minutes plus minutes is less than or equal to max minutes—including an exact 100 percent budget fit—and return False only when it strictly exceeds max minutes. Now look at service slash daily planner dot py on the right: the developer wrote if self dot used minutes plus minutes is greater than or equal to self dot max minutes, return False! Because of that single off-by-one greater-than-or-equal operator, a user with 20 minutes remaining in a 60-minute budget is rejected when scheduling a 20-minute task!
- **TRANSITION:** When we audit `daily_planner.py`, we also find three other feature suggestions. How do we prevent the agent from mixing a bugfix with scope creep? Let's use the 5-Step Brownfield Scorecard in Step 2!

### Slide 23 — Lab 04 Step 2: The 5-Step Brownfield Scorecard Refactoring Loop
- **PURPOSE:** Walk through `labs/lab_04_drift_detection_and_5step_refactoring/scorecard.md` and the 5-Step Refactoring Loop.
- **VERBAL SCRIPT:** In Step 2, we triage all four audit findings inside scorecard dot MD before writing any code. Finding F-01 is the critical REQ-0003 off-by-one boundary bug, which we mark ACCEPTED FOR REFACTOR. Findings F-02 and F-03 propose adding Google Calendar OAuth sync and Pomodoro sound notifications, which we mark DEFERRED. Finding F-04 suggests renaming schedule to book slot, which we mark REJECTED because it breaks the public API contract. This human Go/No-Go triage gate stops mega-prompt disasters in their tracks.
- **TRANSITION:** How do we enforce that triage decision mechanically during agent execution? Let's inspect `expected_output/spec.md` in Step 3.

### Slide 24 — Lab 04 Step 3: Enforcing Karpathy's "Surgical Changes" Rule
- **PURPOSE:** Show how `F-02`, `F-03`, and `F-04` are locked inside Section 6 (`Out of Scope`) of `expected_output/spec.md`.
- **VERBAL SCRIPT:** In Step 3, we author our seven-section Conductor track spec in expected output slash spec dot MD. Look at Section 6, Out of Scope, on the left: we explicitly list F-02 Google Calendar OAuth, F-03 Pomodoro timer notifications, and F-04 renaming schedule to book slot. During conductor implement, the agent is forbidden from touching anything in Out of Scope, turning what could have been a 500-line rewrite into a one-line surgical diff that takes ten seconds to review.
- **TRANSITION:** Let's move to Step 4, write the failing `REQ-0003` boundary regression test, and apply the surgical fix!

### Slide 25 — Lab 04 Step 4: Writing the Regression Test & Surgical Code Fix
- **PURPOSE:** Show `test_req0003_exact_budget_fit_and_over_budget_rejection` and the `>` fix in `daily_planner_fixed.py`.
- **VERBAL SCRIPT:** In Step 4, we write test req0003 exact budget fit and over budget rejection in test daily planner dot py. Look at the test on the left: on a 60-minute planner, we schedule a 40-minute block, then schedule a 20-minute block that fills the exact remaining budget, asserting schedule returns True and remaining minutes is 0, before asserting an extra 5-minute block returns False. On the buggy service, this test fails immediately—completing our Red phase. On the right, in daily planner fixed dot py, we change greater-than-or-equal to strictly greater-than, turning the test Green!
- **TRANSITION:** Let's run `./labs/lab_04_drift_detection_and_5step_refactoring/self_diagnose.sh` in Step 5 to verify both the negative control and the positive fix.

### Slide 26 — Lab 04 Step 5: Differential Bug/Fix Verification in `./self_diagnose.sh`
- **PURPOSE:** Explain the negative/positive control verification in `lab_04/self_diagnose.sh` and inspect the output.
- **VERBAL SCRIPT:** In Step 5, Lab 4's self-diagnosis script performs a differential test: first, it runs our new test suite against the unedited buggy service slash daily planner dot py and verifies that test req0003 fails—proving our test genuinely catches the bug. Second, it runs the suite against expected output slash daily planner fixed dot py and confirms all four tests pass!
- **TRANSITION:** Now let's enter Module 6 for Lab 5 and learn how Spec-Driven Code Review catches subtle regressions in incoming pull requests and how to ship multi-batch changes as Stacked PRs!

---

## MODULE 06: LAB 05 STEP-BY-STEP — SDD CODE REVIEW & STACKED PRS (SLIDES 27–31)

### Slide 27 — Lab 05 Step 1: Auditing an Incoming "Vibe-Coded" Pull Request
- **PURPOSE:** Compare `base/openspec/specs/notes-board/spec.md` against `simulated_review/subpar_change.patch` on TaskFlow's `NotesBoard`.
- **VERBAL SCRIPT:** Welcome to Module 6, where we walk step by step through Lab 5: SDD Code Review and Stacked Pull Requests on TaskFlow's Quick Notes Board. On the left, our baseline OpenSpec contract in base slash openspec slash specs slash notes-board slash spec dot MD defines three requirements: REQ-0001 note creation, REQ-0002 listing notes in chronological creation order, and REQ-0003 note deletion. On the right, a teammate submits simulated review slash subpar change dot patch to add note pinning. At a quick syntax glance, the Python code looks tiny—but when we compare it against our specification, three major violations jump out!
- **TRANSITION:** Let's break down all three Spec-Driven Development violations on Slide 28.

### Slide 28 — Lab 05 Step 2: Catching All 3 SDD Violations via `/conductor:review`
- **PURPOSE:** Detail the 3 SDD violations in `subpar_change.patch`: breaking `REQ-0002` order, missing `REQ-0004` spec delta, and silent error handling with zero tests.
- **VERBAL SCRIPT:** When we run slash conductor review and slash opsx verify against the incoming patch, we catch three blocking violations. Violation 1: the patch wraps list notes in reversed, silently breaking REQ-0002's chronological creation-order guarantee! Violation 2: it introduces two new public methods—pin note and get pinned notes—with zero REQ-0004 specification delta in openspec specs. Violation 3: calling pin note on a non-existent note ID silently does nothing instead of raising KeyError, and the patch includes zero unit tests. In SDD, we always review the Spec Diff first and block any PR where code and spec disagree.
- **TRANSITION:** Let's remediate this change properly in Step 3 by authoring the `REQ-0004` OpenSpec delta contract first.

### Slide 29 — Lab 05 Step 3: Synchronizing the OpenSpec Contract (`REQ-0004`)
- **PURPOSE:** Walk through `REQ-0004` in `expected_output/openspec/specs/notes-board/spec.md`.
- **VERBAL SCRIPT:** In Step 3, we synchronize expected output slash openspec slash specs slash notes-board slash spec dot MD by keeping REQ-0001 through REQ-0003 intact and appending REQ-0004: Pin Note and List Pinned Notes. Look at the normative contract on the left: pin note must mark an existing note with pinned equal to True and raise KeyError if the note ID does not exist, while get pinned notes returns all pinned notes in chronological creation order without altering list notes.
- **TRANSITION:** With `REQ-0004` specified, let's remediate `notes_board.py` and `test_notes_board.py` in Step 4.

### Slide 30 — Lab 05 Step 4: Remediating `notes_board.py` & Verifying `test_notes_board.py`
- **PURPOSE:** Show the compliant `notes_board.py` implementation and the 4 passing tests in `test_notes_board.py`.
- **VERBAL SCRIPT:** In Step 4, we remediate expected output slash notes board dot py. First, list notes returns list of self dot notes dot values in strict creation order, preserving REQ-0002. Second, pin note checks if note ID is in self dot notes—raising KeyError if missing—and constructs a new frozen Note dataclass with pinned set to True. On the right, test notes board dot py verifies all four requirements, including asserting that pinning note 3 never alters the chronological order of list notes.
- **TRANSITION:** How do we ship a multi-part feature across clean, reviewable Stacked Pull Requests without merge conflicts? Let's inspect `tasks.md` in Step 5!

### Slide 31 — Lab 05 Step 5: Stacked Multi-PR Decomposition & Archive PR `N+1`
- **PURPOSE:** Explain the 4 Stacked Multi-PR rules and `expected_output/tasks.md` batches in Lab 05.
- **VERBAL SCRIPT:** In Step 5, we structure expected output slash tasks dot MD into Stacked Pull Request batches. Rule 1: keep one change folder for the entire feature. Rule 2: group tasks dot MD into PR batches—Batch 1 for the REQ-0004 spec delta and creation-order guard, and Batch 2 for pin note implementation and tests. Rule 3: only check off tasks whose code and tests ship in that specific PR. Rule 4: never run opsx archive mid-stack, because moving files into archive breaks downstream branch rebases! Instead, run opsx archive in a dedicated docs-only Pull Request N plus 1 after all code PRs merge.
- **TRANSITION:** Now let's enter our final module—Module 7, Lab 6—where we bring everything together for TaskFlow's Capstone Clean-Room Rebuild Test!

---

## MODULE 07: LAB 06 STEP-BY-STEP — CAPSTONE SPEC.MD & CLEAN-ROOM REBUILD (SLIDES 32–36)

### Slide 32 — Lab 06 Step 1: The 8-Section `SPEC.md` (Sections 1–4)
- **PURPOSE:** Walk through Sections 1 to 4 of `labs/lab_06_capstone_ssot_and_rebuild_test/SPEC.md` for `TaskFlowBoard`.
- **VERBAL SCRIPT:** Welcome to Module 7, our Capstone walkthrough of Lab 6: Spec-as-Single-Source-of-Truth and the Clean-Room Rebuild Test! In Lab 6, we unify TaskFlow into TaskFlowBoard—a three-column Kanban board with todo, doing, and done columns and strict Work-In-Progress limit enforcement. On Slide 32, we inspect Sections 1 through 4 of our canonical eight-section SPEC dot MD: Section 1 defines the domain intent; Section 2 defines the stdlib-only component topology; Section 3 defines the immutable Card dataclass and VALID COLUMNS tuple; and Section 4 defines the exact method signatures and exception contracts for create card, move card, get column, and get wip summary.
- **TRANSITION:** Let's inspect Sections 5 through 8 of `SPEC.md` on Slide 33.

### Slide 33 — Lab 06 Step 2: The 8-Section `SPEC.md` (Sections 5–8)
- **PURPOSE:** Walk through Sections 5 to 8 of `SPEC.md`, including `REQ-0001..REQ-0004` and the 3-Phase Clean-Room Rebuild Recipe.
- **VERBAL SCRIPT:** On Slide 33, Section 5 of SPEC dot MD defines four normative workflows: REQ-0001 creates cards in the todo column and validates that doing wip limit is at least 1; REQ-0002 moves cards across valid columns and raises KeyError on unknown card IDs; REQ-0003 enforces the Work-In-Progress limit on the doing column—raising ValueError whenever moving another card into doing would exceed doing wip limit, while allowing an already-doing card to stay in doing as a no-op; and REQ-0004 returns column lists and WIP summary counts. Section 8 then provides the three-phase Clean-Room Rebuild Recipe.
- **TRANSITION:** How does `lab_06/self_diagnose.sh` prove that `SPEC.md` is a true Level-3 Single Source of Truth? Let's look at the Clean-Room Rebuild harness in Step 3!

### Slide 34 — Lab 06 Step 3: Clean-Room Rebuild & `chmod -w` Adversarial Isolation
- **PURPOSE:** Explain the `/tmp` clean-room rebuild harness and `chmod -R a-w` read-only adversarial test lock in `lab_06/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 3, look at how lab 06 slash self diagnose dot sh executes the Clean-Room Rebuild Test. First, it creates a brand-new isolated temporary directory in slash tmp with zero access to the parent repository. Second, it copies SPEC dot MD, the regenerated taskflow app dot py module, and the adversarial test suite into that clean room. Third, it runs chmod minus R a-minus-w on the tests directory—making the adversarial tests strictly read-only! Just like Karpathy's autoresearch harness locks the evaluation script out of the agent's write permissions, locking tests read-only guarantees the implementation agent cannot weaken or delete assertions to fake a passing build.
- **TRANSITION:** Let's inspect the regenerated `taskflow_app.py` implementation and live test output in Step 4!

### Slide 35 — Lab 06 Step 4: Inspecting `taskflow_app.py` & `test_rebuild_contract.py`
- **PURPOSE:** Walk through `move_card()` in `expected_output/taskflow_app.py` and the live output of `./labs/lab_06_capstone_ssot_and_rebuild_test/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 4, look at move card in expected output slash taskflow app dot py on the left: when moving a card into doing from another column, it counts how many cards are currently in doing and raises ValueError if doing count is greater than or equal to self dot doing wip limit. When we run Lab 6's self-diagnosis script on the right, all four read-only adversarial contract tests—REQ-0001 through REQ-0004—pass inside the isolated clean room in one millisecond!
- **TRANSITION:** Let's wrap up the course on Slide 36 with our Master Diagnostic Checklist and full-repo verification command.

### Slide 36 — Master Diagnostic Checklist & Running `./self_diagnose_all.sh`
- **PURPOSE:** Summarize the top 4 practitioner traps to avoid and run `./self_diagnose_all.sh` across all 6 `TaskFlow` labs (`24/24` tests).
- **VERBAL SCRIPT:** Congratulations on completing the Spec-Driven Development Crash Course! Before you ship in production, remember the four practitioner traps on the left: never write a partial MODIFIED block in OpenSpec because MODIFIED replaces the entire requirement; always use four hashtags for Scenario headers; reference the new TO header when combining RENAMED and MODIFIED; and only run opsx archive in your final pull request N plus 1. When you run dot slash self diagnose all dot sh at the repository root on the right, all six progressive TaskFlow labs and all 24 traceable unit tests pass in under a tenth of a second. Thank you for joining, and happy Spec-Driven Engineering!
- **TRANSITION:** Course complete — clone the repository, run `./self_diagnose_all.sh`, and start practicing!
