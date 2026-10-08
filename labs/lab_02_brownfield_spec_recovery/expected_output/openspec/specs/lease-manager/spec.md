# Lease Manager Capability Specification

## Purpose
The `lease-manager` capability provides thread-safe, time-bounded exclusive resource leases with strictly monotonic 64-bit fencing tokens to prevent split-brain writes from zombie workers.

## Requirements

### Requirement: Exclusive Lease Acquisition and Expiry Takeover (REQ-0001)
The system SHALL grant a `Lease` when `acquire(resource_id, holder_id, ttl_seconds)` is called on a resource with no active lease (or whose prior lease has `expires_at <= now`), or when called by the same `holder_id`.

#### Scenario: Acquiring an unheld resource succeeds
- **GIVEN** resource `"shard-1"` has no active lease at `t=100.0`
- **WHEN** `"worker-a"` calls `acquire("shard-1", "worker-a", ttl_seconds=10.0)`
- **THEN** the system MUST return a `Lease` with `holder_id="worker-a"` and `expires_at=110.0`

#### Scenario: Acquiring an expired resource transfers ownership
- **GIVEN** `"worker-a"` holds a lease on `"shard-1"` with `expires_at=110.0`
- **WHEN** the clock reaches `t=110.0` and `"worker-b"` calls `acquire("shard-1", "worker-b", ttl_seconds=15.0)`
- **THEN** the expired lease MUST be purged and `"worker-b"` MUST receive a new `Lease` with `expires_at=125.0`

### Requirement: Strictly Monotonic Fencing Tokens (REQ-0002)
The system SHALL assign a strictly increasing integer `fencing_token` (`1, 2, 3, ...`) to every successful `acquire` or `renew` operation across the lifetime of the `LeaseManager` instance, never resetting even when leases expire or are released.

#### Scenario: Fencing token increments across release and re-acquisition
- **GIVEN** `"w1"` acquires `"res-a"` with `fencing_token=1` and releases it
- **WHEN** `"w2"` acquires `"res-a"`
- **THEN** the newly issued `Lease` MUST have `fencing_token=2`

### Requirement: Contended Lease Rejection (REQ-0003)
When `acquire` is invoked for a `resource_id` that has an unexpired lease (`expires_at > now`) held by a different `holder_id`, the system SHALL return `None` without modifying the existing lease.

#### Scenario: Competing holder cannot steal an active lease
- **GIVEN** `"node-1"` holds an unexpired lease on `"db-lock"` (`expires_at=80.0`) at `t=50.0`
- **WHEN** `"node-2"` calls `acquire("db-lock", "node-2", ttl_seconds=30.0)`
- **THEN** the system MUST return `None`

### Requirement: Token-Verified Lease Renewal (REQ-0004)
The system SHALL renew an active lease via `renew(resource_id, holder_id, fencing_token, ttl_seconds)` only when the resource is currently held by `holder_id` with matching `fencing_token` and `expires_at > now`, issuing a new monotonic `fencing_token` and setting `expires_at = now + ttl_seconds`.

#### Scenario: Valid holder and fencing token renews lease
- **GIVEN** `"worker-1"` holds `"job-1"` with `fencing_token=1` and `expires_at=30.0` at `t=25.0`
- **WHEN** `"worker-1"` calls `renew("job-1", "worker-1", fencing_token=1, ttl_seconds=20.0)`
- **THEN** the system MUST return a `Lease` with `fencing_token=2` and `expires_at=45.0`

### Requirement: Holder and Token-Verified Lease Release (REQ-0005)
The system SHALL release an active lease via `release(resource_id, holder_id, fencing_token)` and return `True` only if the lease is unexpired and matches both `holder_id` and `fencing_token`; otherwise it SHALL return `False`.

#### Scenario: Release with wrong fencing token is rejected
- **GIVEN** `"owner-1"` holds `"lock-x"` with `fencing_token=1`
- **WHEN** a caller invokes `release("lock-x", "owner-1", fencing_token=99)`
- **THEN** the system MUST return `False` and `"lock-x"` MUST remain leased to `"owner-1"`

### Requirement: Bulk Expiration Eviction and Input Validation (REQ-0006)
The system SHALL validate non-empty identifiers and `ttl_seconds > 0` (`ValueError` on violation) and SHALL provide `evict_expired()` returning the count of expired leases removed at `now`.

#### Scenario: Bulk eviction removes only expired leases
- **GIVEN** `"r1"` expires at `t=5.0` and `"r2"` expires at `t=20.0`
- **WHEN** `evict_expired()` is called at `t=10.0`
- **THEN** the system MUST return `1`, remove `"r1"`, and retain `"r2"`
