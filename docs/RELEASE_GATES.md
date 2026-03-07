# Release Gates

This document defines mandatory go/no-go criteria for shipping releases.
These gates are tied to the novelty wedge and are release-blocking.

## Required Inputs
- `docs/NOVELTY_WEDGE.md`: product wedge scope, primary user, concrete use cases, and non-goals.
- `docs/NOVELTY_METRICS.md`: objective pass/fail thresholds and measurement frequencies.

## Go/No-Go Logic
Release decision is binary:

- **GO**: all required gates below pass.
- **NO-GO**: any required gate fails, is missing evidence, or has stale evidence.

Required gates:

1. **Scope alignment gate**
   Release changes must support at least one use case from `NOVELTY_WEDGE.md` and must not violate listed non-goals.

2. **Metric threshold gate**
   Latest Full novelty run passes every threshold in `NOVELTY_METRICS.md`:
   - Belief freshness after code drift
   - Contradiction resolution latency
   - Provenance coverage
   - Claim retrieval precision@k
   - Task success lift vs current baseline

3. **Evidence completeness gate**
   Release record includes:
   - benchmark run ID
   - benchmark timestamp
   - raw metric outputs
   - computed pass/fail status per metric section

4. **Evidence recency gate**
   Full-run evidence for release gating must be from the last 7 calendar days.

## Fail Closed Policy
If any gate cannot be evaluated exactly as specified (missing data, ambiguous result, benchmark failure, or stale evidence), default to **NO-GO** and block release until the gate is rerun and passes with complete evidence.

## Automation
- CI release enforcement script: `scripts/verify_release_gates.py`
- Nightly Full evidence workflow: `.github/workflows/novelty-full-nightly.yml`
- Tag publish workflow gate: `.github/workflows/publish.yml` (`release_gates` job)

The verification script is mandatory in release automation and writes a gate report that includes:
- benchmark run ID
- benchmark timestamp
- raw metric outputs
- computed pass/fail status per metric section
