# Novelty Eval Guide

This guide covers the local novelty benchmark harness at:

- `python -m benchmarks.novelty_eval`

The harness is designed to validate novelty wedge behavior against metrics in [NOVELTY_METRICS.md](./NOVELTY_METRICS.md) using deterministic, local scenarios.

## What It Evaluates

The harness runs four scenario groups:

1. Stale belief after code change
2. Contradiction evolution
3. Temporal belief reconstruction
4. Provenance trace completeness

These align to the metrics sections:

- `1) Belief Freshness After Code Drift`
- `2) Contradiction Resolution Latency`
- `3) Provenance Coverage`
- `4) Claim Retrieval Precision@k` (temporal slice)

## Local-First Behavior

Default execution avoids cloud dependencies:

- Uses local temporary project data
- Uses deterministic local embedding patches (no remote embedding API/model download)
- Forces config to `EMBEDDING_BACKEND=fastembed`, `LLM_BACKEND=disabled`
- Does not call OpenAI or remote LLM APIs

## Run Instructions

Quick run (recommended for PR checks):

```bash
python -m benchmarks.novelty_eval --mode quick
```

Full run:

```bash
python -m benchmarks.novelty_eval --mode full
```

Optional output path:

```bash
python -m benchmarks.novelty_eval --mode quick --output benchmarks/results/novelty_eval_quick.json
```

## Output JSON Schema

Top-level:

- `benchmark`: `"novelty_eval"`
- `run_id`: unique benchmark run identifier
- `mode`: `"quick"` or `"full"`
- `generated_at`: ISO-8601 UTC timestamp
- `cloud_dependencies_used`: boolean
- `aligned_metrics_doc`: path string
- `sections`: per-metric section objects
- `overall_pass`: boolean (all sections pass)

Each section includes:

- `aligned_metric_section`
- `formula`
- `thresholds`
- `measured`
- `pass`
- scenario/query detail rows

## Interpreting Results

- `overall_pass=true` means all measured novelty sections passed in the same run.
- For drift freshness, inspect:
  - `freshness_after_drift`
  - `stale_claim_leak_rate`
  - `p95_challenge_lag_seconds`
- For contradiction evolution, inspect:
  - `median_latency_seconds`
  - `p95_latency_seconds`
  - `unresolved_contradiction_scenarios`
- For temporal reconstruction, inspect:
  - `overall_macro_precision_at_5`
  - per-query `precision_at_5`
- For provenance completeness, inspect:
  - `provenance_coverage`
  - `missing_provenance_claims_per_1000`

If a section fails, use its scenario/query details to locate regressions quickly.

## Release Gate Validation

Validate a Full-run artifact against release policy gates:

```bash
python scripts/verify_release_gates.py \
  --novelty-result benchmarks/results/novelty_eval_full.json \
  --scope-use-case "Drift-aware debugging memory" \
  --output benchmarks/results/release_gate_report.json
```

The command fails closed (exit code 1) when any mandatory gate fails.
