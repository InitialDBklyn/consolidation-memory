# Novelty Metrics

This document defines objective pass/fail gates for the novelty wedge.
All thresholds are release-blocking unless explicitly marked as observational.

## Gate Evaluation Protocol
- Benchmark inputs are versioned and immutable per run (`benchmarks/` corpus + expected outputs).
- "Quick" runs use reduced sample sizes for PR feedback; "Full" runs are release-grade.
- A metric is `PASS` only if all thresholds in that section are met.
- Release gate status is `PASS` only if all five metric sections are `PASS` on the same Full run.

## 1) Belief Freshness After Code Drift
### Exact definition
`FreshnessAfterDrift = corrected_impacted_claims / total_impacted_claims`

Where:
- `total_impacted_claims` = claims linked to changed anchors in a drift scenario.
- `corrected_impacted_claims` = impacted claims that are marked `challenged` or `expired` within the allowed lag and are not returned as high-confidence active claims in top-5 recall for the scenario query.

### Measurement method
- Corpus: 120 drift scenarios with known changed files and expected impacted claim IDs.
- For each scenario:
  - Run drift detection against the changed file set.
  - Record time from drift detection to first challenge/expire event per impacted claim.
  - Run recall query and inspect top-5 claims.
- A stale claim counts as leaked if it appears as active with confidence `>= 0.60` and without uncertainty signal.

### Threshold for pass
- `FreshnessAfterDrift >= 0.97`
- stale-claim leak rate `<= 0.03`
- p95 challenge/expire event lag `<= 120` seconds

### Frequency of measurement
- Quick: every PR, 30 scenarios.
- Full: nightly, 120 scenarios.
- Release gate: required on latest Full run before release.

## 2) Contradiction Resolution Latency
### Exact definition
For each contradiction pair:
`resolution_latency_seconds = t(resolution_event) - t(contradicting_evidence_ingested)`

Section result reports median and p95 across all pairs.

### Measurement method
- Corpus: 80 contradiction scenarios with known contradictory statement pairs.
- Ingest first claim, then ingest contradiction, trigger consolidation, and read resulting claim events/edges.
- Resolution event must be present (`expired`, `challenged`, or equivalent contradiction resolution event) for each scenario.

### Threshold for pass
- median latency `<= 90` seconds
- p95 latency `<= 300` seconds
- unresolved contradiction scenarios `= 0`

### Frequency of measurement
- Quick: every PR, 20 scenarios.
- Full: nightly, 80 scenarios.
- Release gate: required on latest Full run before release.

## 3) Provenance Coverage
### Exact definition
`ProvenanceCoverage = claims_with_complete_provenance / claims_returned`

`complete_provenance` requires all of:
- claim ID
- claim timestamp (`created_at` or equivalent)
- at least 1 linked source episode
- at least 1 linked source record/topic
- at least 1 lifecycle/audit event

### Measurement method
- Run recall benchmark queries and inspect top-5 returned claims.
- Compute coverage over the full returned-claim set.
- Validate with DB/export audit query to ensure links/events exist, not just response formatting.

### Threshold for pass
- `ProvenanceCoverage >= 0.995`
- missing-provenance claims per Full run `<= 5` per 1000 returned claims

### Frequency of measurement
- Quick: every PR, 50 queries.
- Full: nightly, 200 queries.
- Release gate: required on latest Full run before release.

## 4) Claim Retrieval Precision@k
### Exact definition
`Precision@5 = relevant_claims_in_top5 / 5`, macro-averaged across queries.

`relevant` is judged against a labeled gold set per query (and `as_of` timestamp when provided).

### Measurement method
- Corpus: 300 labeled claim-retrieval queries, split across debugging, runbook, and handoff use cases.
- For each query:
  - Run recall with identical retrieval settings.
  - Compare top-5 claim IDs to gold relevant claim IDs.
- Report macro `Precision@5` overall and per use-case slice.

### Threshold for pass
- overall macro `Precision@5 >= 0.80`
- each use-case slice macro `Precision@5 >= 0.70`

### Frequency of measurement
- Quick: every PR, 60 queries.
- Full: nightly, 300 queries.
- Release gate: required on latest Full run before release.

## 5) Task Success Lift vs Current Baseline
### Exact definition
- `success_rate = completed_tasks / total_tasks`
- `absolute_lift = success_rate_novelty - success_rate_baseline`
- `relative_lift = absolute_lift / success_rate_baseline`

Task completion is binary: all task checks/tests pass within 15 minutes and with `<= 3` agent retries.

### Measurement method
- Paired A/B benchmark on identical 60 coding tasks.
- Baseline = current mainline behavior without novelty-claim/drift features enabled.
- Novelty = branch/config with novelty features enabled.
- Keep model, temperature, prompt seed, and tool budget fixed across A/B.
- Compute 95% bootstrap CI for `absolute_lift`.

### Threshold for pass
- `absolute_lift >= 0.08`
- `relative_lift >= 0.15`
- 95% CI lower bound for `absolute_lift > 0.00`

### Frequency of measurement
- Full only: nightly, 60 paired tasks.
- Release gate: required within 7 days prior to release.
