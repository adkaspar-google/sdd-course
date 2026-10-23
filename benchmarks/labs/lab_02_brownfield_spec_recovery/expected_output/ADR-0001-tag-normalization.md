# ADR-0001: Write-Time Lowercase Tag Normalization (`tag_normalization`)

- **Status**: Accepted (Recovered from Brownfield `service/task_organizer.py`)
- **Context**: Users tag tasks with inconsistent casing and whitespace (e.g., `"Work"`, `" work "`, `"WORK"`). Without normalization, tag searches miss tasks or store duplicate tags.
- **Decision**: Normalize all tags via `raw_tag.strip().lower()` (`tag_normalization`) inside `add_task()` at write-time and deduplicate while preserving first-seen order.
- **Consequences**: `filter_by_tag(tag)` only needs to normalize the search query once (`tag.strip().lower()`) and check membership in $O(k)$ time with zero case-mismatch bugs.
