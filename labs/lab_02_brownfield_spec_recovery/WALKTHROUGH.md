# Lab 02: Brownfield Spec Recovery — Reverse-Engineering Legacy Code into Living Specs

**Estimated Time**: 35–45 minutes  
**Frameworks Practiced**: OpenSpec (`/opsx:explore` + Baseline Spec Extraction) + ADR Recovery

---

## 1. Learning Objective
Most production engineering happens in **brownfield repositories** where critical business invariants live exclusively inside undocumented source code and unit tests. Before modifying a brownfield subsystem with an AI coding agent, you must extract its **baseline behavioral specification** so future changes can be expressed as clean, verified deltas.

In this lab, you are given a working, undocumented **Distributed Lease Lock Manager** (`service/leasemanager.py` and `service/test_leasemanager.py`). Your mission is to reverse-engineer its exact behavioral invariants without breaking existing tests.

---

## 2. Starting Input
Inspect the brownfield codebase in [`service/`](./service/):
- [`service/leasemanager.py`](./service/leasemanager.py): Implements resource lease acquisition, monotonic 64-bit fencing tokens, lease renewal, holder-verified release, and automatic TTL expiration.
- [`service/test_leasemanager.py`](./service/test_leasemanager.py): Existing unit tests.

---

## 3. Hands-On Exercise Steps

### Step 1: Audit the Brownfield Code & Tests (`/opsx:explore`)
Trace every branch in `service/leasemanager.py` to uncover its 6 core behavioral invariants:
- `REQ-0001`: Exclusive lease acquisition on free or expired resources.
- `REQ-0002`: Monotonically increasing 64-bit fencing token across all acquisitions and renewals (`fencing_token` never resets even after release or expiration).
- `REQ-0003`: Contended acquisition rejection when an active lease is held by another owner.
- `REQ-0004`: Active lease renewal (`renew`) extending expiration and issuing a new monotonic fencing token for the current holder.
- `REQ-0005`: Holder-verified release (`release`) rejecting non-holders or stale fencing tokens.
- `REQ-0006`: Eviction of expired leases (`evict_expired`) and thread-safe `RLock` synchronization.

### Step 2: Author `openspec/specs/lease-manager/spec.md`, `design.md`, and `ADR-0001-fencing-tokens.md`
Write the complete RFC 2119 + `#### Scenario:` specification and document why monotonic fencing tokens are required to prevent split-brain storage corruption when a paused client's lease expires.

---

## 4. Self-Diagnosis & Grading
Run the diagnostic harness to execute the brownfield test suite and verify the recovered specification and ADR:

```bash
./self_diagnose.sh
```
