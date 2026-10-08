# SDD-Crash-Course: Tripartite Speaker Notes & Lecture Narration Script

Each slide below follows the canonical tripartite speaker notes structure (`PURPOSE`, `VERBAL SCRIPT`, `TRANSITION`) used both for Google Slides presenter view and for Gemini TTS lecture synthesis.

---

## Slide 01: SDD-Crash-Course — Spec-Driven Development in Practice
- **PURPOSE**: Introduce the three complementary engines of modern Spec-Driven Development—Conductor, OpenSpec, and the 8-Section `SPEC.md` Single Source of Truth—and orient students to the 6 hands-on labs.
- **VERBAL SCRIPT**: Welcome to the SDD Crash Course: Spec-Driven Development in Practice. In this hands-on course, we move beyond conversational vibe coding to build deterministic, test-verified software using three complementary engines. First, Conductor manages persistent repository context and executes Red-Green-Refactor test-driven development tracks. Second, OpenSpec isolates living capability contracts from proposed requirement deltas. Third, our canonical eight-section SPEC dot MD blueprint enables clean-room system rebuilds. Everything in this repository is one hundred percent hands-on: you will complete six self-diagnosing Python engineering labs verified by thirty-seven traceable unit tests in under one second.
- **TRANSITION**: Let's start by examining why conversational vibe coding breaks down on real engineering repositories.

---

## Slide 02: From "Vibe Coding" to Agentic Engineering — Validation & Human Interaction
- **PURPOSE**: Contrast the 4 failure modes of unconstrained "vibe coding" against Karpathy's Software 3.0 Generation–Verification Loop, the 4 Human Interaction Gates, and the 4 Automated Validation Layers.
- **VERBAL SCRIPT**: Why does casual vibe coding fail on real repositories? As Andrej Karpathy observed, code generation is now virtually free, which makes human verification the true bottleneck. Left unconstrained, coding agents act like overeager juniors: they make silent assumptions, bloat fifty lines into a thousand, mutate adjacent working code, or weaken unit tests just to force a green build. Spec-Driven Development solves this by keeping the agent on a short leash across four human interaction gates and four validation layers, codified directly in conductor slash workflow dot md: First, Think Before Coding—surfacing trade-offs via interactive Q and A in Plan Mode. Second, Simplicity First—steering via a concise fifty-line spec before implementation. Third, Surgical Changes—locking non-target code in Out of Scope. And fourth, Goal-Driven Execution with Immutable Verifiers—running one-to-one REQ unit tests and read-only chmod minus w test suites, just like Karpathy's autoresearch evaluator.
- **TRANSITION**: How do teams adopt this progressively? Let's look at the three levels of SDD maturity.

---

## Slide 03: The 3 Levels of Spec-Driven Development Maturity
- **PURPOSE**: Define SDD Maturity Levels 1, 2, and 3, and give engineers a clear decision rule for picking the right tool.
- **VERBAL SCRIPT**: Spec-Driven Development progresses across three maturity levels. At Level One, Spec-First, a developer writes a specification to generate initial code, but subsequent bugfixes edit the code directly—turning the spec into stale documentation within two sprints. At Level Two, Spec-Anchored, powered by OpenSpec and Conductor, specifications are living artifacts: every pull request proposes explicit added, modified, removed, or renamed deltas that merge back into the system of record. At Level Three, Spec-as-Source, your eight-section SPEC dot MD is so complete that you can delete the source code and deterministically regenerate a passing implementation in a clean room.
- **TRANSITION**: Let's dive into Engine One of our stack: Conductor.

---

## Slide 04: Engine 1 — Conductor: Context-Driven Development & TDD Track Execution
- **PURPOSE**: Walk through Conductor's 3-step core workflow (`setup`, `newTrack`, `implement`) and Day-2 operations (`status`, `review`, `revert`).
- **VERBAL SCRIPT**: Conductor brings the Measure Twice, Code Once philosophy directly into your CLI. You begin once per repository with slash conductor setup, which establishes your persistent constitution: product vision, tech stack constraints, and TDD workflow rules. Next, for each feature or bugfix, slash conductor newTrack asks three to five clarifying questions inside a sandboxed Plan Mode and generates a track specification and phased implementation plan. Finally, slash conductor implement executes strict Red-Green-Refactor test-driven development—writing a failing test first, implementing minimal code, attaching git notes, and recording commit SHAs at every phase checkpoint. For Day-Two operations, Conductor provides status auditing, automated principal-engineer code review, and Git-aware logical revert.
- **TRANSITION**: Next, let's examine how Engine Two—OpenSpec—manages capability contracts across time.

---

## Slide 05: Engine 2 — OpenSpec: Two-Plane Architecture & Deterministic Delta Algebra
- **PURPOSE**: Explain OpenSpec's Two-Plane directory model (`openspec/specs/` vs `openspec/changes/`), RFC 2119 + 4-hashtag `#### Scenario:` syntax, and the 99%/1% CLI rule.
- **VERBAL SCRIPT**: OpenSpec solves specification drift through a Two-Plane architecture. Plane One, openspec slash specs, is your living system of record, organized by permanent capability such as rate-limiter or lease-manager. Every requirement carries a unique ID like REQ-0001, normative RFC 2119 keywords like SHALL or MUST, and four-hashtag Scenario blocks written in Given-When-Then format. Plane Two, openspec slash changes, isolates active proposals in their own folder containing proposal, design, tasks, and spec deltas. Remember the ninety-nine percent rule: you run openspec init once in the terminal, and drive ninety-nine percent of your daily work through AI slash commands—explore, propose, apply, verify, and archive.
- **TRANSITION**: How do Conductor and OpenSpec work together on the same repository? Let's look at the Dual-Engine wiring pattern.

---

## Slide 06: Dual-Engine Architecture — Wiring Conductor + OpenSpec + Dedicated Spec Skills
- **PURPOSE**: Show how `conductor/workflow.md` invokes `.agents/skills/writing-arch-specs/SKILL.md` and aligns with `openspec/specs/`, enforcing the 7-Section Track `spec.md` Anatomy.
- **VERBAL SCRIPT**: Rather than choosing between Conductor and OpenSpec, our Dual-Engine pattern wires them together. In conductor slash workflow dot md, we instruct Conductor to load a dedicated architectural specification skill—writing-arch-specs—and reference the canonical REQ IDs in openspec slash specs whenever creating a new track. Every Conductor track specification enforces a strict seven-section anatomy: Overview, Architecture Topology, Functional Requirements, Non-Functional Requirements, Acceptance Criteria, an explicit Out of Scope boundary, and non-interactive Verification Commands. OpenSpec governs what the system must do across capabilities, while Conductor governs how each track is TDD-implemented and checkpointed in Git.
- **TRANSITION**: Now let's walk through the six executable hands-on labs in the repository, starting with Labs One and Two.

---

## Slide 07: Hands-On Labs 01 & 02 — Greenfield Spec Authoring & Brownfield Spec Recovery
- **PURPOSE**: Walk through Lab 01 (Sliding-Window Rate Limiter from an ambiguous proposal) and Lab 02 (Brownfield Lease Lock Manager with monotonic fencing tokens).
- **VERBAL SCRIPT**: In Lab One, you start with a vague two-paragraph product memo asking for an API rate limiter. Before touching code, you author the OpenSpec contract covering REQ-0001 through REQ-0006, evaluate storage and window trade-offs in two Architecture Decision Records, write the seven-section Conductor track spec, and verify the sliding-window implementation. In Lab Two, you tackle brownfield engineering: you are handed an undocumented Distributed Lease Lock Manager and must reverse-engineer its living specification, including its strictly monotonic sixty-four-bit fencing token invariant that prevents split-brain storage corruption when a paused worker's lease expires.
- **TRANSITION**: Once you have solid specifications, how do you execute TDD and fix brownfield drift? Let's look at Labs Three and Four.

---

## Slide 08: Hands-On Labs 03 & 04 — TDD State Machines, Drift Detection & 5-Step Refactoring
- **PURPOSE**: Walk through Lab 03 (Circuit Breaker TDD state machine) and Lab 04 (Token Bucket `REQ-0005` drift bug and the 5-Step Brownfield Scorecard Refactoring Loop).
- **VERBAL SCRIPT**: In Lab Three, you take an approved specification for a Circuit Breaker and translate REQ-0001 through REQ-0007 into sequenced TDD tasks and one-to-one traceable unit tests covering Closed, Open fast-fail, and Half-Open probe recovery. In Lab Four, you practice Spec Drift Detection and the Five-Step Brownfield Scorecard Refactoring Loop on a Token Bucket Quota Allocator. You discover a subtle bug violating REQ-0005 where sub-second polling overwrites the last-replenished timestamp when zero integer tokens are added, permanently starving token refill. Using the engineering scorecard, you isolate Finding F-01 into a surgical track while locking F-02 through F-04 in Out of Scope.
- **TRANSITION**: What happens when a teammate submits a vibe-coded pull request that violates your spec? That brings us to Lab Five.

---

## Slide 09: Hands-On Lab 05 — SDD Code Review & Stacked PR Task Decomposition
- **PURPOSE**: Demonstrate SDD Code Review on `subpar_change.patch` (`KVCache`) and Stacked PR task batching (`Batch 1`, `Batch 2`, `Archive PR N+1`).
- **VERBAL SCRIPT**: In Lab Five, you practice Spec-Driven Code Review. You inspect a simulated pull request patch on a bounded FIFO key-value cache and immediately catch three SDD violations: first, the patch calls move-to-end inside get, silently mutating FIFO eviction into LRU and breaking REQ-0002; second, it adds a public put-with-ttl method with zero specification delta; and third, it omits boundary tests. You remediate the change by synchronizing REQ-0006 in OpenSpec while preserving FIFO order, and decomposing tasks dot md into small Stacked PR batches followed by a dedicated Archive pull request.
- **TRANSITION**: Finally, let's look at our Capstone in Lab Six: the eight-section SPEC dot MD and the Clean-Room Rebuild Test.

---

## Slide 10: Hands-On Lab 06 (Capstone) — The 8-Section `SPEC.md` & Clean-Room Rebuild Test
- **PURPOSE**: Explain the 8-section `SPEC.md` for `CoursePulse` and how `self_diagnose.sh` executes the Clean-Room Rebuild Test with read-only adversarial tests.
- **VERBAL SCRIPT**: Lab Six is our Capstone on Level-Three Spec-as-Single-Source-of-Truth. You examine the complete eight-section SPEC dot MD blueprint for CoursePulse, a university enrollment and automatic FIFO waitlist promotion service. To prove the specification is truly rebuildable, the lab's diagnostic script creates a fresh temporary directory, copies SPEC dot MD and the regenerated implementation alongside an independently authored adversarial test suite, and locks the test directory read-only with chmod minus w. That adversarial isolation guarantees the implementation agent can never pass by weakening or deleting test assertions.
- **TRANSITION**: Before you dive into the terminal, let's review the five mandatory security guardrails and top diagnostic pitfalls.

---

## Slide 11: 5 Mandatory Security Guardrails & Top Practitioner Traps
- **PURPOSE**: Highlight the top 4 OpenSpec/Conductor traps and 5 security guardrails every team must enforce.
- **VERBAL SCRIPT**: Keep these diagnostic traps and security guardrails front of mind. In OpenSpec, never paste a partial requirement under MODIFIED Requirements—because archive replaces the entire requirement block, omitting existing scenarios silently deletes them. Always use four hashtags for Scenario headers, and reference the new target name when combining RENAMED and MODIFIED. On the security side, never commit live API keys or customer PII into openspec or conductor markdown files, keep Conductor's Plan Mode path sandbox active so planning cannot touch source code, and gate every pull request on strict spec validation in CI.
- **TRANSITION**: Let's wrap up with how you can clone and run the entire playground in two minutes.

---

## Slide 12: Start Practicing Now — Clone, Diagnose & Build
- **PURPOSE**: Give students the exact 2-minute quickstart commands and pointers to the 16-page Coursebook PDF and public Google Codelabs.
- **VERBAL SCRIPT**: You are ready to start building. Clone the open-access repository from github dot com slash adkaspar-google slash sdd-course and run slash self-diagnose-all dot sh. In less than a second, you will see all six hands-on labs and all thirty-seven requirement-traceable unit tests pass using only the Python standard library. Inside the repository, you also have the sixteen-page Practical Field Guide PDF, the Dual-Engine Playbook, the writing-arch-specs skill template, and direct links to Google's public Conductor Codelabs. Measure twice, specify once, and code deterministically!
- **TRANSITION**: End of presentation. Happy Spec-Driven Engineering!
