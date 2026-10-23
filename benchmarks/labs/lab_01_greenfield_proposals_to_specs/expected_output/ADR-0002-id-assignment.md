# ADR-0002: Sequential Auto-Incrementing Integer Task IDs

- **Status**: Accepted
- **Context**: `proposal.md` did not specify whether `task_id` should be a 36-character UUID or a sequential integer (`1, 2, 3...`).
- **Decision**: Assign sequential integer IDs starting at `1` (`self._next_id = 1`), incrementing by `1` on each valid `add_task()` call. Deleted IDs are never reused.
- **Consequences**: Users and unit tests can reference tasks easily (`complete_task(1)`, `delete_task(2)`) with deterministic, human-friendly IDs.
