# Lab 01: Greenfield SDD — From Ambiguous Proposal to Dual-Engine Specs & ADRs

**Estimated Time**: 30–40 minutes  
**Frameworks Practiced**: OpenSpec (`/opsx:propose`) + Conductor (`/conductor:newTrack`) + ADR Trade-Off Tables

---

## 1. Learning Objective
In real-world engineering, features rarely start as formal specifications—they start as messy, ambiguous Slack messages or 2-paragraph product proposals (`proposal.md`). If you feed a vague proposal directly to a coding agent, the agent will silently guess critical architectural boundaries (storage backend, clock synchronization, concurrency semantics, failure modes).

In this hands-on lab, you will take an informal proposal for a **Distributed Rate Limiter** (`proposal.md`) and transform it into:
1. **OpenSpec Capability Contract** (`openspec/specs/rate-limiter/spec.md`) with numbered requirements (`REQ-0001` through `REQ-0006`), normative RFC 2119 keywords (`MUST`, `SHALL`), and 4-hashtag `#### Scenario:` blocks (`GIVEN / WHEN / THEN`).
2. **System Design & Architecture Decision Records** (`design.md`, `ADR-0001-storage-engine.md`, `ADR-0002-sync-protocol.md`) evaluating architectural trade-offs before writing code.
3. **Conductor Track Specification & TDD Plan** (`conductor/tracks/rate_limiter_mvp/spec.md` & `plan.md`) using the **7-Section Track Spec Anatomy**.

---

## 2. Starting Input
Inspect [`proposal.md`](./proposal.md) in this directory. Notice what is missing or ambiguous:
- What happens when `limit <= 0` or `window_seconds <= 0`?
- Is the sliding window approximate or exact per-client key?
- What should the rate limiter return when a request is rejected (`retry_after_seconds`, `remaining=0`)?
- How is thread safety guaranteed under concurrent requests?

---

## 3. Hands-On Exercise Steps

### Step 1: Generate the OpenSpec Capability Contract
Using OpenSpec (`/opsx:propose "add-distributed-rate-limiter"`) or manual authoring, create your specification so that it defines `REQ-0001` through `REQ-0006`:
- `REQ-0001`: Per-Key Sliding Window Allowance (`allow(key, cost=1)`)
- `REQ-0002`: Rejection & Retry-After Calculation when quota is exhausted
- `REQ-0003`: Configuration Validation (`limit >= 1`, `window_seconds > 0`, `cost >= 1`)
- `REQ-0004`: Deterministic Clock Injection (`clock: Callable[[], float]`)
- `REQ-0005`: Thread-Safe Concurrent Access (`threading.RLock`)
- `REQ-0006`: Explicit Key Reset (`reset(key)`)

### Step 2: Author `design.md` and Two ADRs
Document the component architecture in `design.md` and record two explicit Architecture Decision Records:
- `ADR-0001-storage-engine.md`: Comparing In-Memory Thread-Safe Deque Store vs. External Redis Lua Script vs. Relational DB.
- `ADR-0002-sync-protocol.md`: Comparing Exact Sliding-Window Timestamp Log vs. Fixed-Window Counter vs. Token Bucket.

### Step 3: Author the 7-Section Conductor Track `spec.md` & `plan.md`
Follow `.agents/skills/writing-arch-specs/SKILL.md` to create the 7-section Conductor track specification (`Overview`, `Architecture`, `Functional Requirements`, `Non-Functional Requirements`, `Acceptance Criteria`, `Out of Scope`, `Verification Commands`) and phased TDD `plan.md`.

---

## 4. Self-Diagnosis & Grading
Compare your work against [`expected_output/`](./expected_output/) and run the automated diagnostic script:

```bash
./self_diagnose.sh
```
