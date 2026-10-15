# Technical Design: TaskFlow Tag & Priority Organizer (`task-organizer`)

## Context
Recovered design documentation for `service/task_organizer.py`.

## Decisions
1. **Write-Time Tag Normalization (`ADR-0001`)**: Every tag is stripped, lowercased (`tag_normalization`), and deduplicated before storage.
2. **Deterministic Priority Sort**: `PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}` combined with the tuple sort key `(PRIORITY_RANK[t["priority"]], t["id"])` guarantees stable creation-order tie-breaking.
