import json
import os
import shutil

STAGE_ROOT = "./benchmarks/upstream_252_trials"
EVO_TMPL = os.path.join(STAGE_ROOT, "templates", "outer_loop_evo")
EVO_PRIV = os.path.join(STAGE_ROOT, "privilege_dir", "outer_loop_evo")
BASE_TINYDB = os.path.join(EVO_TMPL, "base_tinydb")
os.makedirs(EVO_PRIV, exist_ok=True)

OUTER_ARMS = ["outer_a", "outer_b", "outer_c", "outer_d"]
RUNS = [1, 2, 3]

EVO_TRIALS_ROOT = os.path.join(STAGE_ROOT, "outer_trials")
if os.path.exists(EVO_TRIALS_ROOT):
    shutil.rmtree(EVO_TRIALS_ROOT)

for run_idx in RUNS:
    for o_arm in OUTER_ARMS:
        ws = os.path.join(EVO_TRIALS_ROOT, f"run_{run_idx}", o_arm)
        shutil.copytree(BASE_TINYDB, ws)

        if o_arm == "outer_a":
            # Outer A: Append-Only Ephemeral Sprint Files (named by topic slug without chronological numbering or delta consolidation)
            sdir = os.path.join(ws, "specs")
            os.makedirs(sdir, exist_ok=True)
            with open(os.path.join(sdir, "spec_table_and_clamp.md"), "w") as f:
                f.write("""# Sprint Spec: Table Count & Clamp Operation
- In `tinydb/table.py`, add `Table.count_all(self) -> int` returning `len(self)`.
- In `tinydb/operations.py`, add `clamp(field, min_val, max_val)` which clamps `doc[field]` into `[min_val, max_val]`. When `min_val > max_val`, automatically swap `min_val` and `max_val` before clamping.
- In `tinydb/middlewares.py`, set `CachingMiddleware.WRITE_CACHE_SIZE = 32`.
""")
            with open(os.path.join(sdir, "spec_cache_batching.md"), "w") as f:
                f.write("""# Sprint Spec: CachingMiddleware Write Batching
- In `tinydb/middlewares.py`, set `CachingMiddleware.WRITE_CACHE_SIZE = 64`.
- Track `self.pending_writes = 0` in `CachingMiddleware.__init__`, increment by 1 in `write()`, and reset to 0 in `flush()`.
""")
            with open(os.path.join(sdir, "spec_query_validation.md"), "w") as f:
                f.write("""# Sprint Spec: Case-Insensitive Queries & Clamp Validation
- In `tinydb/operations.py`, `clamp(field, min_val, max_val)` must raise `ValueError("min_val cannot exceed max_val")` when `min_val > max_val`.
- In `tinydb/queries.py`, add `iequals(self, rhs: str)` to `Query` (`QueryInstance`) for case-insensitive string equality.
""")
            with open(os.path.join(sdir, "spec_strict_lock.md"), "w") as f:
                f.write("""# Sprint Spec: Strict Lock Mode
- In `tinydb/middlewares.py`, set `CachingMiddleware.WRITE_CACHE_SIZE = 1`.
- In `tinydb/operations.py`, `delete(field)` must raise `PermissionError("Strict lock active")`.
- In `tinydb/operations.py`, when `min_val > max_val`, `clamp(field, min_val, max_val)` sets `doc[field] = 0` without raising `ValueError`.
""")
            with open(os.path.join(sdir, "spec_read_telemetry.md"), "w") as f:
                f.write("""# Sprint Spec: Read Telemetry & Lock Rollback
- Roll back the Strict Lock Mode overrides (`spec_strict_lock.md`) to the prior specification state.
- Add `self.read_hits = 0` to `CachingMiddleware.__init__` and increment `self.read_hits += 1` on every `read()` call.
""")

        elif o_arm == "outer_b":
            # Outer B: Feature-Isolated Spec Directories (specs/<feature_slug>/spec.md without global cross-feature reconciliation)
            for slug, content in [
                ("feat_table_and_clamp", """# Feature Spec: Table Count & Clamp Operation
- In `tinydb/table.py`: add `Table.count_all(self) -> int` returning `len(self)`.
- In `tinydb/operations.py`: add `clamp(field, min_val, max_val)`. When `min_val > max_val`, swap `min_val` and `max_val` so `doc[field]` is clamped into `[max_val, min_val]`.
- In `tinydb/middlewares.py`: set `CachingMiddleware.WRITE_CACHE_SIZE = 32`.
"""),
                ("feat_caching_middleware", """# Feature Spec: CachingMiddleware Batching
- In `tinydb/middlewares.py`: set `CachingMiddleware.WRITE_CACHE_SIZE = 64`.
- Track `self.pending_writes` (`0` on init/flush, `+1` on `write()`).
"""),
                ("feat_queries_and_validation", """# Feature Spec: Case-Insensitive Queries & Input Validation
- In `tinydb/queries.py`: add `iequals(self, rhs: str)` on `Query` for case-insensitive equality (`isinstance(val, str) and val.lower() == rhs.lower()`).
- In `tinydb/operations.py`: `clamp(field, min_val, max_val)` raises `ValueError` if `min_val > max_val`.
"""),
                ("feat_strict_cache_lock", """# Feature Spec: Strict Cache Lock
- In `tinydb/middlewares.py`: set `CachingMiddleware.WRITE_CACHE_SIZE = 1`.
- In `tinydb/operations.py`: `delete(field)` raises `PermissionError("Strict lock active")`, and `clamp` sets `doc[field] = 0` when `min_val > max_val`.
"""),
                ("feat_read_telemetry", """# Feature Spec: Read Telemetry & Lock Revert
- Disable `feat_strict_cache_lock` and restore the pre-lock feature behavior across `middlewares.py` and `operations.py`.
- In `tinydb/middlewares.py`: initialize `self.read_hits = 0` in `__init__` and increment `self.read_hits += 1` in `read()`.
"""),
            ]:
                fdir = os.path.join(ws, "specs", slug)
                os.makedirs(fdir, exist_ok=True)
                with open(os.path.join(fdir, "spec.md"), "w") as f:
                    f.write(content)

        elif o_arm == "outer_c":
            # Outer C: Single-File In-Place EARS Requirements (mutated in-place at Sprint 4 so M3 constants were overwritten in-place, followed by M5 rollback prompt)
            with open(os.path.join(ws, "requirements.md"), "w") as f:
                f.write("""# EARS Requirements Document (Single-File In-Place State After Sprint 4 Overwrite + Sprint 5 Note)

- **REQ-1**: WHERE `Table` is used in `tinydb/table.py`, THE system SHALL provide `count_all(self) -> int` returning `len(self)`.
- **REQ-2 (Modified In-Place at Sprint 4)**: WHEN `clamp(field, min_val, max_val)` is called in `tinydb/operations.py`, IF `min_val > max_val`, THE system SHALL set `doc[field] = 0` (overwriting the prior Sprint 3 rule); OTHERWISE THE system SHALL clamp `doc[field]` into `[min_val, max_val]`.
- **REQ-3**: WHEN `Query().<field>.iequals(rhs)` is called in `tinydb/queries.py`, THE system SHALL match strings case-insensitively (`isinstance(val, str) and val.lower() == rhs.lower()`).
- **REQ-4 (Modified In-Place at Sprint 4)**: WHERE `CachingMiddleware` is configured in `tinydb/middlewares.py`, THE system SHALL set `WRITE_CACHE_SIZE = 1` (overwriting the prior Sprint 2/3 cache size) and track `self.pending_writes` (`0` on init/flush, `+1` per `write()`).
- **REQ-5 (Modified In-Place at Sprint 4)**: WHEN `delete(field)` is called in `tinydb/operations.py`, THE system SHALL raise `PermissionError("Strict lock active")`.
- **REQ-6 (Sprint 5 Update)**: THE system SHALL revert the Sprint 4 Strict-Lock modifications in REQ-2, REQ-4, and REQ-5 back to their Sprint 3 specification values, and SHALL track `self.read_hits` (`0` on init, `+1` per `read()`) on `CachingMiddleware`. (Note: Single-file in-place mode does not maintain a `conductor/tracks/` delta archive of prior sprint values.)
""")

        elif o_arm == "outer_d":
            # Outer D: Two-Plane Delta-Merged SSOT Architecture (openspec/specs/SPEC.md + conductor/tracks/delta_history.md)
            os.makedirs(os.path.join(ws, "openspec", "specs"), exist_ok=True)
            os.makedirs(os.path.join(ws, "conductor", "tracks"), exist_ok=True)
            with open(os.path.join(ws, "openspec", "specs", "SPEC.md"), "w") as f:
                f.write("""# Canonical Single Source of Truth (`openspec/specs/SPEC.md` — Version: M5 Post-M4-Rollback)

## 1. `tinydb/table.py` Contract
- **Method `Table.count_all(self) -> int`**: Returns `len(self)`.

## 2. `tinydb/operations.py` Contract
- **Function `clamp(field: str, min_val: float, max_val: float)`**:
  - If `min_val > max_val`, raise `ValueError("min_val cannot exceed max_val")` (either when `clamp` is called or inside `transform(doc)`).
  - Otherwise sets `doc[field] = max(min_val, min(max_val, doc[field]))`.
- **Function `delete(field: str)`**:
  - Deletes `doc[field]` without raising `PermissionError`.

## 3. `tinydb/queries.py` Contract
- **Method `QueryInstance.iequals` / `Query.iequals(self, rhs: str) -> QueryInstance`**:
  - Case-insensitive string equality: returns `self._generate_test(lambda val: isinstance(val, str) and isinstance(rhs, str) and val.lower() == rhs.lower(), ('iequals', self._path, rhs))`.

## 4. `tinydb/middlewares.py` Contract
- **Class Attribute `CachingMiddleware.WRITE_CACHE_SIZE = 64`**.
- **Instance Attributes on `CachingMiddleware`**:
  - `self.pending_writes = 0` in `__init__`, `self.pending_writes += 1` in `write(data)`, `self.pending_writes = 0` in `flush()`.
  - `self.read_hits = 0` in `__init__`, `self.read_hits += 1` in `read()`.
""")
            with open(os.path.join(ws, "conductor", "tracks", "delta_history.md"), "w") as f:
                f.write("""# Conductor Track Delta Log (`BEFORE -> AFTER`)
- `M1`: ADDED `Table.count_all`, `operations.clamp` (`swap` on `min_val > max_val`), `CachingMiddleware.WRITE_CACHE_SIZE = 32`
- `M2`: MODIFIED `CachingMiddleware.WRITE_CACHE_SIZE`: `BEFORE = 32` -> `AFTER = 64`; ADDED `pending_writes`
- `M3`: MODIFIED `operations.clamp` (`min_val > max_val`): `BEFORE = swap bounds` -> `AFTER = raise ValueError`; ADDED `Query.iequals`
- `M4`: MODIFIED `WRITE_CACHE_SIZE`: `BEFORE = 64` -> `AFTER = 1`; MODIFIED `delete`: `AFTER = raise PermissionError`; MODIFIED `clamp`: `BEFORE = raise ValueError` -> `AFTER = set 0`
- `M5`: ROLLED BACK `M4` using `M4.BEFORE` (`WRITE_CACHE_SIZE = 64`, `delete` normal, `clamp` raises `ValueError`); ADDED `CachingMiddleware.read_hits`
""")

print("Staged realistic 12 Outer-Loop Evolution workspaces (without Greek-letter ordering hints)!")
