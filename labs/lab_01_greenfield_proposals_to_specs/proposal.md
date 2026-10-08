# Informal Product Proposal: API Rate Limiter

**From**: Product Management  
**Subject**: Need a rate limiter for our public API endpoints ASAP

Hey team,

Several enterprise tenants are hammering our `/v1/query` endpoint with burst traffic and causing tail-latency spikes for everyone else. We need a rate limiter module that tracks requests per `client_id` and blocks callers when they exceed `N` requests in a sliding time window of `W` seconds.

Key asks:
1. Callers should be able to pass a `key` (like `tenant_123`) and optionally a `cost` (some heavy queries count as 5 tokens instead of 1).
2. The response should tell the caller whether the request is allowed, how many requests they have left in the current window, and—if blocked—how many seconds they need to wait before retrying.
3. Make sure it's thread-safe and easy to unit test without sleeping in CI.
4. Provide a way for admins or tests to reset a specific key's quota.

Let's get specs, ADRs, and a TDD execution plan ready before we write the implementation!
