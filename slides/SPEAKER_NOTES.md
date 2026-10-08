# SDD-Crash-Course — Complete 36-Slide End-to-End Speaker Notes (`SPEAKER_NOTES.md`)

---

## MODULE 01: SDD FOUNDATIONS, KARPATHY'S SOFTWARE 3.0 LOOP & DUAL-ENGINE ARCHITECTURE (SLIDES 01–06)

### Slide 01 — Course Cover: SDD-Crash-Course
- **PURPOSE:** Introduce the 7-module step-by-step curriculum and set expectations for hands-on, executable verification across all 6 labs.
- **VERBAL SCRIPT:** Welcome to the Spec-Driven Development Crash Course! In this end-to-end engineering course, we move beyond ad-hoc conversational prompting—often called Vibe Coding—and learn how to turn Specifications into our Single Source of Truth using two complementary open-source engines: Conductor and OpenSpec. Across seven focused modules, we will walk step by step through every file, architectural decision record, specification, test suite, and terminal command across all six progressive labs.
- **TRANSITION:** Let's begin in Module 1 by examining why conversational prompting breaks down at scale and how Andrej Karpathy's Software 3.0 loop transforms how we engineer with AI agents.

### Slide 02 — Why Vibe Coding Fails & Karpathy's Software 3.0 Loop
- **PURPOSE:** Contrast the Vibe Coding Amnesia Loop with Andrej Karpathy's Software 3.0 Generation–Verification Loop and 4 Coding Agent Rules.
- **VERBAL SCRIPT:** Why does conversational Vibe Coding fail on real codebases? Because every time a chat window resets, architectural intent evaporates. Without a durable spec, an AI agent silently mutates public contracts, overcomplicates simple modules, or edits its own tests just to make the build pass. As Andrej Karpathy emphasizes in Software 3.0, human engineering shifts from typing boilerplate to maximizing the speed and determinism of the Generation-Verification loop, governed by four core rules: Think Before Coding, Simplicity First, Surgical Changes, and Goal-Driven Execution.
- **TRANSITION:** How do we operationalize those four rules inside a repository? Let's trace the three levels of Spec-Driven Development maturity.

### Slide 03 — The 3 SDD Maturity Levels & The Clean-Room Rebuild Test
- **PURPOSE:** Define Level 1 (Spec-First), Level 2 (Spec-Anchored), and Level 3 (Spec-as-Source / SSOT), plus the Clean-Room Rebuild Test.
- **VERBAL SCRIPT:** Spec-Driven Development matures across three distinct levels. At Level 1, Spec-First, you write a specification before coding, but let it go stale afterward. At Level 2, Spec-Anchored, your specifications live permanently in the repository and evolve through structured delta merges on every pull request. At Level 3, Spec-as-Source, your canonical eight-section SPEC.md captures 100 percent of essential behavior, schemas, and interfaces so that an agent can regenerate the entire service from scratch in an empty directory and pass a read-only adversarial test suite on the first run.
- **TRANSITION:** Now let's inspect the two open-source engines we combine to achieve Level 2 and Level 3 maturity: Conductor and OpenSpec.

### Slide 04 — Engine 1: Conductor (Context & Track TDD Execution)
- **PURPOSE:** Explain Conductor's persistent `conductor/` directory, `/conductor:newTrack`, and `/conductor:implement` Red-Green-Refactor TDD workflow.
- **VERBAL SCRIPT:** Our first engine is Conductor, which serves as the tactical execution engine. Conductor establishes a persistent repository constitution inside the conductor directory—storing product intent, tech-stack constraints, and TDD workflow rules. When you run conductor newTrack, it scaffolds a seven-section track specification and a hierarchical execution plan. Then, conductor implement executes strict Red-Green-Refactor Test-Driven Development, recording task telemetry in git notes and pausing for human verification at every phase checkpoint.
- **TRANSITION:** While Conductor excels at track execution, how do we maintain long-lived normative specifications across capabilities? Enter Engine 2: OpenSpec.

### Slide 05 — Engine 2: OpenSpec (Two-Plane Spec & Delta Algebra)
- **PURPOSE:** Explain OpenSpec's Two-Plane architecture (`openspec/specs/` vs `openspec/changes/`) and deterministic 5-step archive merge order.
- **VERBAL SCRIPT:** Our second engine is OpenSpec, which serves as the normative specification engine. OpenSpec separates your repository into two planes: openspec specs, which holds the current system truth using RFC 2119 SHALL and MUST keywords and four-hashtag Gherkin scenarios, and openspec changes, which isolates proposed deltas. When a change is verified and archived via opsx archive, OpenSpec deterministically merges your deltas in five strict steps: Pre-Validation, RENAMED, REMOVED, MODIFIED, and ADDED.
- **TRANSITION:** Let's see how we wire Conductor and OpenSpec together with a shared architectural specification skill so they never collide.

### Slide 06 — Dual-Engine Wiring & The `@writing-arch-specs` Skill
- **PURPOSE:** Show the 6-step dual-engine lifecycle and the 4 artifact templates provided by `.agents/skills/writing-arch-specs/`.
- **VERBAL SCRIPT:** Instead of choosing between Conductor and OpenSpec, we wire them together into a single six-step pipeline, reinforced by our custom writing-arch-specs skill. OpenSpec governs what the system must do and why—backed by Architecture Decision Records, RFC 2119 requirement IDs, and four-hashtag Gherkin scenarios. Conductor governs how the agent executes the work—enforcing Red-Green-Refactor TDD, git notes, and phase checkpoints. Let's now jump into Module 2 and apply this exact workflow step by step in Lab 1!
- **TRANSITION:** Let's open Lab 1 in the terminal and build a greenfield sliding-window rate limiter from scratch.

---

## MODULE 02: LAB 01 STEP-BY-STEP — GREENFIELD PROPOSALS TO SPECS & TDD (SLIDES 07–11)

### Slide 07 — Lab 01 Step 1: Auditing the Ambiguous Proposal & Interactive Q&A
- **PURPOSE:** Walk through `labs/lab_01_greenfield_proposals_to_specs/proposal.md` and show how `/opsx:explore` & `/conductor:newTrack` surface the 5 clarifying questions.
- **VERBAL SCRIPT:** Welcome to Module 2, where we walk step by step through Lab 1: Greenfield Proposals to Specs. If you inspect labs slash lab 01 greenfield proposals to specs slash proposal.md, you'll see a typical vague product memo: We need an in-memory API Rate Limiter in Python so noisy tenants stop overloading our backend endpoints; please ship this fast! Why does Vibe Coding fail here? Because a raw coding agent immediately guesses fixed-window versus sliding-window, ignores clock drift in tests, and forgets thread safety. Instead, in Step 1, we apply Karpathy's Rule 1—Think Before Coding—by running opsx explore and conductor newTrack in Plan Mode, surfacing five clarifying questions covering exact sliding-window semantics, weighted cost support, structured RateLimitDecision responses, injectable clock callables, and RLock concurrency.
- **TRANSITION:** Once the human engineer answers those five questions, let's move to Step 2 and author our normative OpenSpec capability contract.

### Slide 08 — Lab 01 Step 2: Authoring the OpenSpec Capability Contract
- **PURPOSE:** Walk through `expected_output/openspec/specs/rate-limiter/spec.md` (`REQ-0001..REQ-0006`) and its 4-hashtag Gherkin scenarios.
- **VERBAL SCRIPT:** In Step 2 of Lab 1, we translate those clarified requirements into expected output slash openspec slash specs slash rate-limiter slash spec.md. Look at the exact contract excerpt on the left: every requirement has a stable bracketed identifier—REQ-0001 through REQ-0006—uses uppercase RFC 2119 SHALL and MUST keywords, and includes a four-hashtag Scenario block with GIVEN, WHEN, and THEN clauses. On the right, our six requirements cover sliding-window allowance, quota exhaustion with exact retry-after calculation, input validation, injectable clock determinism, RLock thread safety, and per-key reset.
- **TRANSITION:** Now that we have defined WHAT the rate limiter must do in OpenSpec, how do we record WHY we chose an exact sliding-window deque over a fixed counter or Redis? Let's write our ADRs in Step 3.

### Slide 09 — Lab 01 Step 3: Recording Architecture Decision Records (ADRs)
- **PURPOSE:** Explain `ADR-0001-storage-engine.md` (In-Memory `dict[str, deque]` + `RLock`) and `ADR-0002-sync-protocol.md` (Exact Sliding-Window Log vs Fixed Counter).
- **VERBAL SCRIPT:** In Step 3, we author two Architecture Decision Records inside expected output slash docs slash adr. In ADR-0001, we evaluate three storage options—an in-memory dictionary of deques guarded by RLock, a Redis Sorted Set, and a SQL table—and accept the in-memory deque for zero-dependency sub-millisecond performance. In ADR-0002, we evaluate Exact Sliding-Window Log against Fixed-Window Counter and Approximate Sliding Counter. Because a fixed-window counter permits a 2x traffic burst right at the window boundary, we accept the Exact Sliding-Window Log. Recording these ADRs prevents any future AI session from refactoring our exact sliding window back into a buggy fixed counter!
- **TRANSITION:** With our OpenSpec contract and ADRs locked in, let's move to Step 4 and bridge them into Conductor's 7-section track `spec.md` and phased `plan.md`.

### Slide 10 — Lab 01 Step 4: Authoring the 7-Section Conductor Track `spec.md` & `plan.md`
- **PURPOSE:** Inspect the exact contents of `expected_output/spec.md` and `expected_output/plan.md` in Lab 01.
- **VERBAL SCRIPT:** In Step 4, we author the seven-section Conductor track specification in expected output slash spec.md and the phased TDD execution plan in expected output slash plan.md. Look at Section 6 of spec.md on the left: we explicitly place distributed Redis cluster sync and HTTP middleware wrappers under Out of Scope so the coding agent cannot write 800 lines of unrequested boilerplate. On the right, plan.md sequences the implementation across three phases of Red-Green-Refactor tasks, with User Manual Verification checkpoints and seven-character commit SHAs recorded at the end of each phase.
- **TRANSITION:** Now let's move to Step 5, inspect the reference implementation in `ratelimiter.py`, and run `./self_diagnose.sh`!

### Slide 11 — Lab 01 Step 5: Implementing `ratelimiter.py` & Running `./self_diagnose.sh`
- **PURPOSE:** Walk through `allow()` in `expected_output/ratelimiter.py` and the live output of `./labs/lab_01_greenfield_proposals_to_specs/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 5, we implement SlidingWindowRateLimiter inside ratelimiter.py and execute dot slash labs slash lab 01 greenfield proposals to specs slash self diagnose dot sh. Look at allow on the left: inside with self dot lock, we compute cutoff equals now minus self dot window seconds and pop expired timestamps from the left of the deque while q zero zero is less than or equal to cutoff. If used plus cost is within self dot limit, we append now comma cost and return Allowed true; otherwise we walk the deque to compute the exact retry after seconds until enough tokens expire. When we run self diagnose dot sh on the right, all six requirement-traceable unit tests—REQ-0001 through REQ-0006—pass in one millisecond!
- **TRANSITION:** Now that we've mastered greenfield specification and TDD in Lab 1, what happens when you inherit a complex legacy codebase with zero specs? Let's enter Module 3 for Lab 2!

---

## MODULE 03: LAB 02 STEP-BY-STEP — BROWNFIELD SPEC RECOVERY (SLIDES 12–16)

### Slide 12 — Lab 02 Step 1: Auditing an Un-Specced Legacy Service (`leasemanager.py`)
- **PURPOSE:** Introduce `labs/lab_02_brownfield_spec_recovery/service/leasemanager.py` and the `/opsx:explore` brownfield workflow.
- **VERBAL SCRIPT:** Welcome to Module 3, where we tackle Lab 2: Brownfield Spec Recovery. In the real world, 90 percent of engineering happens in brownfield repositories where code exists, tests pass, and architectural documentation is completely missing. If you inspect labs slash lab 02 brownfield spec recovery slash service slash leasemanager.py, you'll find a production LeaseLockManager that coordinates distributed resource leases. Our goal is to run an OpenSpec explore pass—reading the code and tests without modifying a single line of production code—to reverse-engineer its normative OpenSpec specification, design doc, and fencing-token ADR.
- **TRANSITION:** Let's trace the methods and invariants inside `leasemanager.py` in Step 2 to extract its six normative requirements.

### Slide 13 — Lab 02 Step 2: Extracting the 6 Hidden Behavioral Invariants (`REQ-0001..REQ-0006`)
- **PURPOSE:** Trace `acquire()`, `renew()`, `release()`, and `evict_expired()` in `leasemanager.py` to map `REQ-0001..REQ-0006`.
- **VERBAL SCRIPT:** In Step 2, we trace leasemanager.py line by line. Look at the acquire method on the left: whenever a lease is granted—or renewed in renew—the manager increments self dot fencing counter and attaches that integer to the returned Lease object. Furthermore, if the resource is already held by another active owner whose expires at is strictly greater than now, acquire returns None; unless the same owner re-acquires, which extends the TTL and issues a fresh fencing token! From this code audit, we extract six exact requirements: REQ-0001 through REQ-0006, covering mutual exclusion, monotonic 64-bit fencing tokens, lazy expiration, active renewal, holder-verified release, and batch eviction.
- **TRANSITION:** Why does `leasemanager.py` never reset `_fencing_counter` when a lease is released? Let's document the distributed systems proof in Step 3!

### Slide 14 — Lab 02 Step 3: Documenting the Split-Brain Fencing Token Proof (`ADR-0001`)
- **PURPOSE:** Explain Martin Kleppmann's GC-pause split-brain hazard and how `ADR-0001-fencing-tokens.md` prevents a naive refactoring disaster.
- **VERBAL SCRIPT:** In Step 3, we author ADR-0001-fencing-tokens.md to explain why the fencing counter must be strictly monotonic across the entire lifetime of the manager. Imagine Worker A acquires a lease with a five-second TTL and enters a six-second garbage collection pause before writing to storage. At t equals 5.1 seconds, Worker A's lease expires, and Worker B acquires the lease and writes to storage. At t equals 6.0 seconds, Worker A wakes up from its GC pause and sends its delayed write! Because Worker A holds fencing token 101 and storage has already seen Worker B's fencing token 102, storage rejects Worker A's stale write. Recording this in ADR-0001 stops any future engineer or AI agent from accidentally resetting the counter on release.
- **TRANSITION:** Now let's translate our six extracted invariants into a strict RFC 2119 and Gherkin specification in Step 4.

### Slide 15 — Lab 02 Step 4: Authoring `openspec/specs/lease-manager/spec.md` & `design.md`
- **PURPOSE:** Inspect the recovered `spec.md` (`REQ-0002` excerpt) and `design.md` in `labs/lab_02_brownfield_spec_recovery/expected_output/`.
- **VERBAL SCRIPT:** In Step 4, we author expected output slash openspec slash specs slash lease-manager slash spec.md and expected output slash design.md. Look at the excerpt of REQ-0002 on the left: it uses uppercase RFC 2119 SHALL and MUST keywords, followed by a four-hashtag Scenario block with GIVEN, WHEN, and THEN clauses specifying exact timestamps and fencing token values. On the right, our recovered design.md documents the frozen Lease dataclass, the single-process mutual exclusion boundary, and the RLock concurrency invariant.
- **TRANSITION:** Let's run Lab 2's self-diagnosis script in Step 5 to verify our recovered specification and confirm zero regressions in the legacy service.

### Slide 16 — Lab 02 Step 5: Verifying Zero-Regression Brownfield Recovery
- **PURPOSE:** Walk through `./labs/lab_02_brownfield_spec_recovery/self_diagnose.sh` checks and live terminal output.
- **VERBAL SCRIPT:** In Step 5, we run dot slash labs slash lab 02 brownfield spec recovery slash self diagnose dot sh. The script verifies that REQ-0001 through REQ-0006 are documented with uppercase SHALL or MUST keywords and four-hashtag Scenario headers, checks ADR-0001 and design.md, and runs all six unit tests in service slash test leasemanager dot py. All six tests pass in under a millisecond, and our legacy lease manager is now officially upgraded to SDD Maturity Level 2: Spec-Anchored!
- **TRANSITION:** Now that we know how to write and recover specifications, how do we drive a complex state-machine implementation purely from approved specs using Red-Green-Refactor TDD? Let's enter Module 4 for Lab 3!

---

## MODULE 04: LAB 03 STEP-BY-STEP — FROM SPECS TO TDD CODE (SLIDES 17–21)

### Slide 17 — Lab 03 Step 1: Inspecting the Approved Circuit Breaker Contract
- **PURPOSE:** Walk through `labs/lab_03_from_specs_to_tdd_code/specs/spec.md` (`REQ-0001..REQ-0007`) and the 3-state machine (`CLOSED`, `OPEN`, `HALF_OPEN`).
- **VERBAL SCRIPT:** Welcome to Module 4, where we walk step by step through Lab 3: From Specs to TDD Code. Inside labs slash lab 03 from specs to tdd code slash specs, you are given an already-approved OpenSpec contract and design document for a three-state fault-isolation Circuit Breaker. As shown on the left, the circuit breaker transitions between CLOSED, OPEN, and HALF_OPEN states across seven normative requirements, REQ-0001 through REQ-0007. Our mission is to practice Karpathy's Rule 4—Goal-Driven Execution—by turning each requirement into a sequenced TDD task and a one-to-one traceable unit test before writing the state-machine code.
- **TRANSITION:** Let's start in Step 2 by decomposing those seven requirements into a sequenced two-batch TDD task plan in `tasks.md`.

### Slide 18 — Lab 03 Step 2: Decomposing Requirements into Sequenced TDD Tasks
- **PURPOSE:** Inspect `expected_output/tasks.md` and explain why 1-to-1 `test_reqXXXX_*` naming creates bidirectional traceability.
- **VERBAL SCRIPT:** In Step 2, we author expected output slash tasks.md, grouping the seven requirements into two logical TDD batches: Batch 1 covers the core state model and CLOSED-to-OPEN tripping for REQ-0001, REQ-0002, and REQ-0007; Batch 2 covers OPEN fast-fail and HALF_OPEN probe recovery for REQ-0003 through REQ-0006. Notice our strict naming convention: every single unit test is named test underscore reqXXXX underscore behavior, with Verifies REQ-XXXX in its docstring. That creates a deterministic, greppable link between every requirement in spec.md and the exact test method that verifies it!
- **TRANSITION:** Let's execute Batch 1 and REQ-0003 in Step 3, examining both the unit tests in `test_circuitbreaker.py` and the implementation in `circuitbreaker.py`.

### Slide 19 — Lab 03 Step 3: Red-Green-Refactor Batch 1 (`CLOSED` & `OPEN` Fast-Fail)
- **PURPOSE:** Walk through `test_req0002` and `test_req0003` in `test_circuitbreaker.py` and the fast-fail guard in `circuitbreaker.py`.
- **VERBAL SCRIPT:** In Step 3, we write our failing tests first, verify they fail, and then write the minimal code in circuitbreaker.py. Look closely at test req0003 open state fails fast without invoking callable on the bottom left: after tripping the circuit breaker to OPEN, it calls cb dot call with a tracked callable and explicitly asserts self dot assertEqual invocations comma zero. Why? Because a classic AI coding bug is invoking the downstream function before checking if the circuit is OPEN! Because REQ-0003's Gherkin scenario states without invoking the wrapped callable, our unit test enforces that exact invariant.
- **TRANSITION:** Next, let's move to Step 4 and implement Batch 2: the cooldown transition from `OPEN` to `HALF_OPEN` and single-probe recovery.

### Slide 20 — Lab 03 Step 4: Red-Green-Refactor Batch 2 (`HALF_OPEN` Probe Recovery)
- **PURPOSE:** Walk through `_evaluate_state_unlocked()` and single-probe gating (`_half_open_in_flight`) for `REQ-0004..REQ-0006`.
- **VERBAL SCRIPT:** In Step 4, we implement the HALF_OPEN probe state machine for REQ-0004, REQ-0005, and REQ-0006. Look at evaluate state unlocked on the left: when the circuit is OPEN and the elapsed time on our injected monotonic clock is greater than or equal to recovery timeout seconds, the state transitions lazily to HALF_OPEN and resets half open in flight to zero. While in HALF_OPEN, only half open max calls probes are admitted. If the probe succeeds—REQ-0005—the failure count resets to zero and the circuit closes. If the probe raises an exception—REQ-0006—the circuit immediately re-opens for another full cooldown cycle!
- **TRANSITION:** Let's complete Lab 3 in Step 5 by recording our Conductor `git notes` audit trail and running `./self_diagnose.sh`.

### Slide 21 — Lab 03 Step 5: Git Notes Audit Trail & Running `./self_diagnose.sh`
- **PURPOSE:** Show how Conductor attaches structured `git notes` to commits and verify all 7 tests pass via `./self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 5, we see how Conductor records task completion without polluting git commit messages: after committing our feature, we attach structured task metadata using git notes add, and append the seven-character checkpoint SHA to the phase header in plan.md. When we run dot slash labs slash lab 03 from specs to tdd code slash self diagnose dot sh on the right, it verifies that tasks.md is complete, checks that testreq0001 through testreq0007 all exist, and runs all seven unit tests in one millisecond with 100 percent pass rate!
- **TRANSITION:** What happens when a production service is already Spec-Anchored, but a subtle bug causes the code to drift away from its spec? Let's enter Module 5 for Lab 4!

---

## MODULE 05: LAB 04 STEP-BY-STEP — DRIFT DETECTION & 5-STEP REFACTORING (SLIDES 22–26)

### Slide 22 — Lab 04 Step 1: Detecting Spec-to-Code Drift (`REQ-0005` Starvation Bug)
- **PURPOSE:** Compare `specs/spec.md` (`REQ-0005`) against the buggy `_replenish()` method in `service/quota_allocator.py`.
- **VERBAL SCRIPT:** Welcome to Module 5, where we walk step by step through Lab 4: Spec-to-Code Drift Detection and the 5-Step Brownfield Scorecard Refactoring Loop. In labs slash lab 04, we inspect a production TokenBucketQuotaAllocator whose existing happy-path unit tests all pass, yet production tenants polling at high frequency are suffering total quota starvation! Look at REQ-0005 in specs slash spec.md on the left: calls that occur before a full integer token has accumulated MUST NOT discard fractional elapsed time. Now look at line 802 of service slash quota allocator dot py on the right: replenish computes added equals int of elapsed times rate, and then unconditionally overwrites bucket dot last replenished equals now—even when added is zero! Every time a client polls at 0.4 seconds, added is zero and last replenished resets, starving the bucket forever.
- **TRANSITION:** When we audit a brownfield module and find a critical bug alongside several minor tech-debt ideas, how do we keep an AI agent focused? Let's inspect the Scorecard in Step 2.

### Slide 23 — Lab 04 Step 2: The 5-Step Brownfield Scorecard Refactoring Loop
- **PURPOSE:** Walk through `labs/lab_04_drift_detection_and_5step_refactoring/scorecard.md` and the 5-Step Brownfield Refactoring Loop.
- **VERBAL SCRIPT:** In Step 2, we apply the 5-Step Brownfield Scorecard Refactoring Loop. Look at scorecard.md on the left: our engineering audit surfaced four findings—F-01, the critical REQ-0005 fractional timestamp overwrite bug; F-02, adding Prometheus metrics; F-03, migrating to a Redis cluster; and F-04, rewriting docstrings into NumPy format. If you dump all four findings into an AI agent at once, you get an unreviewable 500-line diff that mixes a critical production bugfix with a Redis rewrite! Instead, in Step 2 of the loop, the lead engineer performs a human Go/No-Go triage: marking F-01 as ACCEPTED_FOR_REFACTOR, deferring F-02 and F-03, and rejecting F-04.
- **TRANSITION:** How do we mechanically enforce that Go/No-Go triage so the coding agent cannot touch `F-02`, `F-03`, or `F-04`? Let's look at Step 3!

### Slide 24 — Lab 04 Step 3: Enforcing Karpathy's "Surgical Changes" Rule
- **PURPOSE:** Show how `expected_output/spec.md` locks `F-02`, `F-03`, and `F-04` inside `## 6. Out of Scope`.
- **VERBAL SCRIPT:** In Step 3, we translate our triaged scorecard into a surgical Conductor track spec at expected output slash spec.md. Look at Section 6, Out of Scope, on the bottom left: we explicitly list F-02 Prometheus metrics, F-03 Redis backend migration, and F-04 NumPy docstring reformatting under Out of Scope. This operationalizes Karpathy's Rule 3—Surgical Changes—as a hard contract: during conductor implement, the agent is forbidden from touching anything in Out of Scope, and during conductor review, any diff touching those items triggers an automatic Plan Compliance Violation.
- **TRANSITION:** Now let's move to Step 4 and write the failing `REQ-0005` regression test followed by the surgical 6-line fix in `_replenish()`.

### Slide 25 — Lab 04 Step 4: Writing the Regression Test & Surgical Code Fix
- **PURPOSE:** Walk through `test_req0005_sub_quantum_polling_preserves_fractional_elapsed_time` and the exact math in `quota_allocator_fixed.py`.
- **VERBAL SCRIPT:** In Step 4, we execute our Red-Green-Refactor cycle. First, on the left, we write test req0005 sub quantum polling preserves fractional elapsed time: we drain a bucket of capacity 2 to zero at t equals 0, poll consume at t equals 0.4 seconds and t equals 0.8 seconds—both returning False—and then poll at t equals 1.2 seconds, asserting that consume returns True because 1.2 seconds have elapsed at 1 token per second. On the buggy service, this test fails! Next, on the right, we apply the surgical fix in quota allocator fixed dot py: we only advance bucket dot last replenished when added is strictly greater than zero, advancing it by added divided by refill rate per sec—preserving the 0.2 seconds of leftover fractional time!
- **TRANSITION:** Let's run Lab 4's self-diagnosis script in Step 5 to see how it runs a differential test against both the buggy service and our fixed implementation.

### Slide 26 — Lab 04 Step 5: Differential Bug/Fix Verification in `./self_diagnose.sh`
- **PURPOSE:** Explain the negative control (buggy service must fail `test_req0005`) and positive control (fixed service passes 6/6 tests) in `lab_04/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 5, we run dot slash labs slash lab 04 drift detection and 5step refactoring slash self diagnose dot sh. Notice how rigorous this verification script is: first, it runs a Negative Control, executing our new test suite against the unpatched service slash quota allocator dot py and verifying that test req0005 genuinely fails! Second, it runs a Positive Control against expected output slash quota allocator fixed dot py and verifies that all six tests—REQ-0001 through REQ-0006—pass. Finally, it audits expected output slash spec.md to confirm that F-02, F-03, and F-04 are locked in Out of Scope.
- **TRANSITION:** Now that we can detect and fix spec drift in our own code, how do we review incoming pull requests from other engineers or AI agents? Let's enter Module 6 for Lab 5!

---

## MODULE 06: LAB 05 STEP-BY-STEP — SDD CODE REVIEW & STACKED PRS (SLIDES 27–31)

### Slide 27 — Lab 05 Step 1: Auditing an Incoming "Vibe-Coded" Pull Request
- **PURPOSE:** Compare `base/openspec/specs/kv-cache/spec.md` (`REQ-0002` FIFO eviction) against `simulated_review/subpar_change.patch`.
- **VERBAL SCRIPT:** Welcome to Module 6, where we walk step by step through Lab 5: Spec-Driven Code Review and Stacked Multi-PR Workflows. In labs slash lab 05, we maintain an in-memory KVCache governed by base slash openspec slash specs slash kv-cache slash spec.md. Look at REQ-0002 on the left: when inserting a new key at capacity, KVCache MUST evict the oldest inserted key in strict First-In-First-Out order, and reading a key via get MUST NOT alter eviction order. Now look at the incoming pull request in simulated review slash subpar change dot patch on the right: an agent added self dot store dot move to end key inside get with the comment Optimized cache hits, and bolted on a put with ttl method using time dot time!
- **TRANSITION:** Why would a traditional code review rubber-stamp this patch, and how does `/conductor:review` catch every flaw? Let's examine the three violations in Step 2.

### Slide 28 — Lab 05 Step 2: Catching All 3 SDD Violations via `/conductor:review`
- **PURPOSE:** Detail the 3 SDD violations in `subpar_change.patch`: Spec Contradiction (`REQ-0002`), Un-Specced API (`put_with_ttl`), and Untested/Non-Hermetic code.
- **VERBAL SCRIPT:** In Step 2, we audit subpar change dot patch through the lens of Spec-Driven Code Review and immediately flag three blocking violations. Violation 1 is a Spec Contradiction: calling move to end inside get silently mutates REQ-0002's FIFO eviction contract into Least-Recently-Used eviction! Violation 2 is an Un-Specced Public API: the patch adds put with ttl without adding a corresponding REQ-0006 requirement to spec.md, and forgets to purge expired keys before evicting valid FIFO keys at capacity. Violation 3 is Untested and Non-Hermetic Code: it calls hardcoded time dot time instead of an injectable clock and ships zero unit tests.
- **TRANSITION:** Let's remediate this pull request properly, starting in Step 3 by updating the OpenSpec contract first!

### Slide 29 — Lab 05 Step 3: Synchronizing the OpenSpec Contract (`REQ-0006`)
- **PURPOSE:** Walk through `REQ-0006` in `expected_output/openspec/specs/kv-cache/spec.md`, showing how spec authoring exposes the capacity-reclamation edge case.
- **VERBAL SCRIPT:** In Step 3, we follow the SDD Golden Rule—update the specification first—by adding REQ-0006 to expected output slash openspec slash specs slash kv-cache slash spec.md while keeping REQ-0002's FIFO contract untouched. Look at the Gherkin scenario we write for REQ-0006 on the left: given a KVCache of max size 2 containing k1 with a 5-second TTL and k2 with no TTL, when the clock advances to t equals 6.0 seconds and k3 is inserted, expired k1 SHALL be purged first so k2 is NOT evicted! Writing the Gherkin scenario exposed a subtle bug that the vibe-coded patch completely missed.
- **TRANSITION:** Now let's move to Step 4 and inspect the compliant `kvcache.py` implementation and `test_kvcache.py` suite.

### Slide 30 — Lab 05 Step 4: Remediating `kvcache.py` & Verifying `test_kvcache.py`
- **PURPOSE:** Inspect `_purge_expired_unlocked()` and `get()` in `expected_output/kvcache.py` and the 6 tests in `expected_output/test_kvcache.py`.
- **VERBAL SCRIPT:** In Step 4, we remediate kvcache.py in expected output. Look at get on the bottom left: we check whether the key has expired using our injected clock, purge it lazily if expired, and otherwise return self dot store dot get key—without calling move to end, thereby preserving REQ-0002 FIFO order! Furthermore, inside put and put with ttl, we call purge expired unlocked before checking capacity so expired entries are reclaimed before any live FIFO entry is evicted. On the right, test kvcache dot py verifies all six requirements, REQ-0001 through REQ-0006.
- **TRANSITION:** When shipping a feature like this across a stacked chain of pull requests in Git or Jujutsu, how do we prevent OpenSpec merge conflicts? Let's look at Step 5!

### Slide 31 — Lab 05 Step 5: Stacked Multi-PR Decomposition & Archive PR `N+1`
- **PURPOSE:** Explain the 4 Stacked Multi-PR rules (`expected_output/tasks.md` batching and Dedicated Archive PR `N+1`).
- **VERBAL SCRIPT:** In Step 5, we structure expected output slash tasks.md for a Stacked Multi-PR workflow. When decomposing a feature into smaller reviewable pull requests—PR 1 for the spec delta and clock state, and PR 2 for TTL eviction and tests—we follow four critical rules: keep one change folder for the feature, group tasks.md checkboxes by PR batch, only mark checkboxes x for code included in that exact PR, and never run opsx archive mid-stack! Why? Because opsx archive moves the entire change directory into openspec slash changes slash archive, which would trigger massive tree-rename conflicts on every downstream PR in your stack. Instead, always run opsx archive in a final, docs-only PR N plus 1 after all code PRs have merged.
- **TRANSITION:** We have now reached our final module—Module 7—where we bring everything together in Lab 6: authoring an 8-Section `SPEC.md` and passing the Clean-Room Rebuild Test!

---

## MODULE 07: LAB 06 STEP-BY-STEP — CAPSTONE SPEC.MD & CLEAN-ROOM REBUILD (SLIDES 32–36)

### Slide 32 — Lab 06 Step 1: The 8-Section `SPEC.md` (Sections 1–4)
- **PURPOSE:** Walk through Sections 1–4 of `labs/lab_06_capstone_ssot_and_rebuild_test/SPEC.md` for `CoursePulse`.
- **VERBAL SCRIPT:** Welcome to Module 7, our Capstone Lab: Authoring an 8-Section Single Source of Truth SPEC.md and executing the Clean-Room Rebuild Test. If you open labs slash lab 06 capstone ssot and rebuild test slash SPEC.md, you'll see a complete Level-3 specification for CoursePulse, a university course enrollment and automatic FIFO waitlist engine. In Step 1, we inspect Sections 1 through 4: Section 1 defines the domain intent; Section 2 defines the thread-safe in-memory RLock architecture; Section 3 specifies the exact frozen dataclasses EnrollmentResult, DropResult, and CourseRoster; and Section 4 specifies the exact method signatures and exception types for create course, enroll, drop, and get roster.
- **TRANSITION:** Let's continue in Step 2 through Sections 5 to 8 of `SPEC.md`, including the 3-Phase Clean-Room Rebuild Recipe.

### Slide 33 — Lab 06 Step 2: The 8-Section `SPEC.md` (Sections 5–8)
- **PURPOSE:** Walk through Sections 5–8 of `SPEC.md`, highlighting `REQ-0004` (automatic FIFO waitlist promotion) and the 3-Phase Rebuild Recipe.
- **VERBAL SCRIPT:** In Step 2, we inspect Sections 5 through 8 of SPEC.md. Section 5 defines the six normative requirements, REQ-0001 through REQ-0006, including REQ-0003 idempotent duplicate enrollment and REQ-0004: whenever an enrolled student drops a full course, the student at the head of the FIFO waitlist must be atomically promoted into the vacated seat! Sections 6 and 7 define the single-file module layout coursepulse.py and environment parameterization. Finally, Section 8 provides the 3-Phase Clean-Room Rebuild Recipe: Phase A generates the data models and validators; Phase B implements the core enrollment and FIFO waitlist engine; and Phase C executes the read-only adversarial verification suite in an isolated clean room.
- **TRANSITION:** How does `lab_06/self_diagnose.sh` execute that Clean-Room Rebuild Test while enforcing Karpathy's immutable verifier pattern? Let's inspect the shell script in Step 3!

### Slide 34 — Lab 06 Step 3: Clean-Room Rebuild & `chmod -w` Adversarial Isolation
- **PURPOSE:** Show the exact bash commands in `labs/lab_06_capstone_ssot_and_rebuild_test/self_diagnose.sh` that create `/tmp/sdd_rebuild_XXXXXX` and lock `tests/` with `chmod -R a-w`.
- **VERBAL SCRIPT:** In Step 3, look at the exact bash harness inside labs slash lab 06 slash self diagnose dot sh on the left. First, it creates a brand-new temporary directory in slash tmp using mktemp dash d. Second, it copies only SPEC.md, the regenerated coursepulse.py implementation, and the adversarial contract test suite test rebuild contract dot py into that isolated clean room. Third—look at line 1169—it runs chmod dash R a minus w on CLEAN_ROOM slash tests, locking the entire test directory read-only before running unittest! Just like Karpathy's autoresearch locks prepare.py out of the agent's write scope, chmod dash w guarantees the implementation passes the true specification contract with zero test tampering and zero hidden dependencies on the parent repository.
- **TRANSITION:** Let's inspect the regenerated `coursepulse.py` code and watch the Clean-Room Rebuild Test execute in Step 4!

### Slide 35 — Lab 06 Step 4: Inspecting `coursepulse.py` & `test_rebuild_contract.py`
- **PURPOSE:** Walk through `drop()` in `expected_output/coursepulse.py` and the live output of `./labs/lab_06_capstone_ssot_and_rebuild_test/self_diagnose.sh`.
- **VERBAL SCRIPT:** In Step 4, look at the drop implementation inside expected output slash coursepulse.py on the left: inside with self dot lock, when an enrolled student is removed, a while loop pops the oldest candidate from the FIFO waitlist deque, removes them from waitlisted set, appends them to course dot enrolled, and returns DropResult with promoted student id set to that candidate! On the right, when we run dot slash labs slash lab 06 slash self diagnose dot sh, all six read-only adversarial contract tests—REQ-0001 through REQ-0006, including defensive roster snapshot immutability—pass inside the isolated slash tmp clean room in one millisecond!
- **TRANSITION:** Let's conclude our course on Slide 36 with the Master Diagnostic Checklist and a full end-to-end run of `./self_diagnose_all.sh` across all six labs!

### Slide 36 — Course Graduation: Master Diagnostic Checklist & Running `./self_diagnose_all.sh`
- **PURPOSE:** Summarize the top 4 practitioner traps and run `./self_diagnose_all.sh` across all 6 labs (37 traceable tests).
- **VERBAL SCRIPT:** Congratulations on completing all seven modules of the Spec-Driven Development Crash Course! On the left, keep these four diagnostic rules at your fingertips: always include the complete requirement block and all existing scenarios in an OpenSpec MODIFIED delta; always use four hashtags for Scenario headers; always target the new TO name when combining RENAMED and MODIFIED; and always run opsx archive in a dedicated final pull request N plus 1. On the right, whenever you clone the repository, run dot slash self diagnose all dot sh at the root to execute all six hands-on labs and all 37 traceable unit tests in under one second. Thank you for joining the course, and happy spec-driven building!
- **TRANSITION:** End of course lecture.
