# Contributing to SDD-Crash-Course

Thank you for contributing to **SDD-Crash-Course**! Every scenario in this repository is designed to be 100% self-contained, executable on any developer laptop without external cloud credentials, and verified via `./self_diagnose_all.sh`.

## SDD Compliance Checklist for Contributors

When adding a new lab scenario or updating reference outputs under `labs/`:

1. **Normative Language (`RFC 2119`)**: Use uppercase `MUST`, `SHALL`, `SHOULD`, and `MAY` in every `spec.md` requirement.
2. **4-Hashtag Gherkin Scenarios**: Every requirement block (`REQ-XXXX` or `### Requirement:`) MUST include at least one `#### Scenario:` block with `WHEN` and `THEN` clauses.
3. **1-to-1 Test Traceability**: Every unit test in `expected_output/test_*.py` must explicitly reference the requirement ID it verifies (e.g., `def test_req0001_...`).
4. **Automated Verification**: Run `./self_diagnose_all.sh` before opening a Pull Request and confirm all 6 labs pass with `0` errors.
5. **License**: All contributions are licensed under the [Apache 2.0 License](./LICENSE), and `.py`/`.yaml`/`.sh` files must include the standard Apache 2.0 header.
