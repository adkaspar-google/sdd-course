# ADR-0002: Rate-Limiting Window Algorithm Selection

- **Status**: Accepted
- **Related Requirements**: `REQ-0001`, `REQ-0002`

## Context
We must choose an algorithm that enforces per-key request limits without suffering from the "2x boundary burst" vulnerability at window edges, while computing an exact `retry_after_seconds` value (`REQ-0002`).

## Options Evaluated

| Algorithm | Boundary Burst Protection | Exact `retry_after_seconds` | Memory Complexity |
| :--- | :--- | :--- | :--- |
| **Fixed Window Counter** | Vulnerable (2x spike at window boundary) | Coarse (until next bucket) | $O(1)$ per key |
| **Exact Sliding Window Log (`deque`)** | Exact (zero boundary spike) | Exact to oldest expiring entry | $O(\text{limit})$ per active key |
| **Token Bucket** | Allows burst up to bucket size | Approximate | $O(1)$ per key |

## Decision
We choose **Exact Sliding Window Log (`collections.deque`)** so `REQ-0001` and `REQ-0002` provide strict sliding-window enforcement and exact `retry_after_seconds` calculation.
