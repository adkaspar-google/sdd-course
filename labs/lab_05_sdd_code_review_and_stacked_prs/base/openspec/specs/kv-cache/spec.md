# Key-Value Cache Capability Specification (Baseline)

## Purpose
The `kv-cache` capability provides a bounded, thread-safe in-memory key-value store with deterministic FIFO eviction order.

## Requirements

### Requirement: Bounded Key-Value Storage and Retrieval (REQ-0001)
The cache SHALL store values by non-empty string `key` and return the stored value via `get(key)` (or `None` if absent).

#### Scenario: Put and get round-trip
- **GIVEN** a `KVCache(max_size=3)`
- **WHEN** `put("k1", "v1")` is called
- **THEN** `get("k1")` MUST return `"v1"` and `get("missing")` MUST return `None`

### Requirement: Deterministic FIFO Eviction When Full (REQ-0002)
When inserting a new key into a cache where `len(cache) == max_size`, the cache SHALL evict the earliest-inserted key (First-In, First-Out), regardless of read (`get`) access frequency.

#### Scenario: Reading an older key does NOT change FIFO eviction order
- **GIVEN** a `KVCache(max_size=2)` with `"k1"` inserted first and `"k2"` inserted second
- **WHEN** `get("k1")` is called, followed by `put("k3", "v3")`
- **THEN** `"k1"` MUST be evicted (`get("k1") is None`) and `"k2"` and `"k3"` MUST remain

### Requirement: In-Place Value Update Preserves Insertion Order (REQ-0003)
Updating an existing key via `put(key, new_value)` SHALL overwrite its value without evicting any entry or altering its FIFO insertion position.

#### Scenario: Updating an existing key at full capacity
- **GIVEN** a `KVCache(max_size=2)` containing `"k1"` and `"k2"`
- **WHEN** `put("k1", "updated")` is called
- **THEN** `len(cache)` MUST remain `2` and `get("k1")` MUST return `"updated"`

### Requirement: Explicit Key Deletion (REQ-0004)
`delete(key)` SHALL remove `key` and return `True` if present, or `False` if absent.

#### Scenario: Deleting existing and non-existent keys
- **GIVEN** a cache containing `"k1"`
- **WHEN** `delete("k1")` is called twice
- **THEN** the first call MUST return `True` and the second call MUST return `False`

### Requirement: Thread-Safe Synchronization and Size Validation (REQ-0005)
The cache SHALL raise `ValueError` if `max_size < 1` or `key == ""`, and SHALL guard all operations with `threading.RLock`.

#### Scenario: Invalid max_size raises ValueError
- **GIVEN** a caller passes `max_size=0`
- **WHEN** `KVCache(max_size=0)` is called
- **THEN** `ValueError` MUST be raised
