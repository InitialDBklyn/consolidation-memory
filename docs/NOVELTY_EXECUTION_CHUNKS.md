# Novelty Execution Playbook (Micro-Chunks for Fresh Chats)

This version is optimized for fresh-context chats.
It uses small, dependency-ordered prompts so each chat can finish one narrow unit of work with low regression risk.

## Execution Rules
1. Run chunks in order.
2. Use one fresh chat per chunk.
3. Paste one chunk prompt exactly as written.
4. Do not start the next chunk until the current chunk passes its acceptance criteria.
5. Keep each chunk focused. If scope creeps, stop and create a follow-up chunk.

## Global Completion Contract
Ask each chat to return:
1. Files changed
2. Tests run and outcomes
3. Risks or follow-ups
4. Ready for next chunk: `yes` or `no`

---

## Chunk Index
| Chunk | Focus | Depends On |
|---|---|---|
| CH-01 | Wedge doc | None |
| CH-02 | Novelty metrics doc | CH-01 |
| CH-03 | Release gates doc + roadmap links | CH-02 |
| CH-04 | Claim graph schema migration | CH-03 |
| CH-05 | Claim DB methods | CH-04 |
| CH-06 | Anchor/drift DB methods + types | CH-05 |
| CH-07 | Claim graph DB tests | CH-06 |
| CH-08 | Anchor extractor module | CH-07 |
| CH-09 | Store path anchor integration | CH-08 |
| CH-10 | Anchor ingestion tests | CH-09 |
| CH-11 | Claim canonicalization module | CH-10 |
| CH-12 | Consolidation emits claims + edges/events | CH-11 |
| CH-13 | Claim emission tests | CH-12 |
| CH-14 | Claim retrieval fusion + `as_of` | CH-13 |
| CH-15 | API surface for claims | CH-14 |
| CH-16 | Retrieval/API tests | CH-15 |
| CH-17 | Drift detection module + wiring | CH-16 |
| CH-18 | Drift tests | CH-17 |
| CH-19 | Utility-driven consolidation scheduler | CH-18 |
| CH-20 | Scheduler tests | CH-19 |
| CH-21 | Novelty eval harness + docs | CH-20 |
| CH-22 | CI gates + export/import + final hardening | CH-21 |

---

## CH-01: Product Wedge Document
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Create docs/NOVELTY_WEDGE.md.

Include:
- Positioning: "Temporal, auditable, code-state-aware memory for coding agents."
- Primary user profile.
- Top 3 concrete use cases.
- Top 3 non-goals.
- A short "why now" section.

Constraints:
- No runtime code changes in this chunk.
- Keep wording specific, not marketing-heavy.

Acceptance criteria:
- File exists and is specific enough to drive implementation decisions.
```

---

## CH-02: Novelty Metrics Document
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Create docs/NOVELTY_METRICS.md with measurable pass/fail gates.

Required metric sections:
- Belief freshness after code drift
- Contradiction resolution latency
- Provenance coverage
- Claim retrieval precision@k
- Task success lift vs current baseline

For each metric include:
- Exact definition
- Measurement method
- Threshold for pass
- Frequency of measurement

Constraints:
- No runtime code changes in this chunk.
- Use numeric targets, not qualitative language.

Acceptance criteria:
- Every metric has objective measurement and explicit threshold.
```

---

## CH-03: Release Gates Wiring
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Wire novelty docs into release governance.

Steps:
1. Create docs/RELEASE_GATES.md that references:
   - docs/NOVELTY_WEDGE.md
   - docs/NOVELTY_METRICS.md
2. Update docs/ROADMAP.md to mark these gates as mandatory for release.
3. Add a short "fail closed" policy in RELEASE_GATES.md.

Constraints:
- Documentation-only chunk.

Acceptance criteria:
- Roadmap explicitly references release gates.
- Release gates doc defines go/no-go logic.
```

---

## CH-04: Claim Graph Schema Migration
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add claim-graph schema migration in src/consolidation_memory/database.py.

Implement:
- Bump CURRENT_SCHEMA_VERSION by +1.
- Add migration with tables:
  - claims
  - claim_edges
  - claim_sources
  - claim_events
  - episode_anchors
- Add indexes for:
  - temporal claim queries
  - claim status
  - source episode lookup
  - anchor lookup

Constraints:
- Backward compatible migration.
- Keep current schema and data intact.

Acceptance criteria:
- Migration applies on a clean DB.
- Existing tests unrelated to claims still import/load schema without breakage.
```

---

## CH-05: Claim Graph DB Methods
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add claim DB API methods to src/consolidation_memory/database.py.

Required methods:
- upsert_claim(...)
- get_active_claims(...)
- get_claims_as_of(...)
- expire_claim(...)
- insert_claim_edge(...)
- insert_claim_sources(...)
- insert_claim_event(...)

Constraints:
- Parameterized SQL only.
- Preserve existing patterns and naming style in database.py.

Acceptance criteria:
- Methods exist with deterministic behavior and no schema assumptions beyond CH-04.
```

---

## CH-06: Anchor/Drift DB Methods + Types
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add anchor and drift-support DB methods, and minimal types.

Implement in database.py:
- insert_episode_anchors(...)
- get_claims_by_anchor(...)
- mark_claims_challenged_by_anchors(...) or equivalent helper

Implement in types.py:
- dataclass or TypedDict result types for claim query results and drift output.

Constraints:
- Keep types additive and backward compatible.

Acceptance criteria:
- New methods/types compile and fit existing project patterns.
```

---

## CH-07: Claim Graph DB Tests
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add tests for the new claim graph DB layer.

Create tests/test_claim_graph.py with coverage for:
- migration created new tables
- claim upsert idempotency
- temporal as_of claim retrieval
- claim edge insert/read
- claim source insert/read
- claim event insert/read
- anchor insert and claim lookup by anchor

Run:
- pytest tests/test_claim_graph.py -q
- pytest tests/test_records.py tests/test_schemas.py -q

Acceptance criteria:
- New tests pass.
- Existing record/schema tests remain green.
```

---

## CH-08: Anchor Extractor Module
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add src/consolidation_memory/anchors.py.

Implement extractors for:
- file paths (Windows + POSIX style)
- commit hashes
- tool references (pytest, uvicorn, docker, git, etc.)

Expose:
- extract_anchors(text: str) -> list[dict] or equivalent typed structure

Constraints:
- Pure parser module, no DB writes in this chunk.
- Keep regex conservative to reduce false positives.

Acceptance criteria:
- Module is importable and returns stable structured output.
```

---

## CH-09: Integrate Anchors Into Store Paths
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Persist anchors during ingestion.

Implement:
- In MemoryClient.store: after successful episode insert + vector add, parse anchors and persist.
- In MemoryClient.store_batch: do the same for each stored episode.

Use database helper from prior chunks for persistence.

Constraints:
- No API contract change for store/store_batch return types.
- Anchor extraction failures should not fail storage.

Acceptance criteria:
- Stored episodes now have persisted anchors when anchors are present in content.
```

---

## CH-10: Anchor Ingestion Tests
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add tests for anchor extraction and ingestion integration.

Create tests/test_episode_anchors.py with:
- path extraction
- commit hash extraction
- low false-positive sanity check
- store integration writes anchors
- store_batch integration writes anchors for accepted items

Run:
- pytest tests/test_episode_anchors.py tests/test_core.py -q

Acceptance criteria:
- Tests validate both parser behavior and MemoryClient integration.
```

---

## CH-11: Claim Canonicalization Module
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add src/consolidation_memory/claim_graph.py for deterministic claim generation.

Implement:
- canonical claim id generation from record payload
- mapping from record types (fact/solution/preference/procedure) to claim representation
- normalization rules to reduce duplicate claims

Constraints:
- Deterministic output required for repeatability.
- Keep module independent of transport layers.

Acceptance criteria:
- Module produces stable IDs and normalized claim objects for identical input.
```

---

## CH-12: Consolidation Emits Claims + Contradiction Edges
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Integrate claim graph writes into consolidation pipeline.

In consolidation/engine.py:
- On create/update, emit claims for merged records.
- Link claims to source episodes/topics via claim_sources.
- Write claim_events for create/update/expire.
- On contradictions, create claim_edges with edge_type="contradicts".
- Record contradiction details in claim_events.

Constraints:
- Preserve existing topic/record behavior.
- If claim emission fails for one record, handle gracefully and continue where safe.

Acceptance criteria:
- Consolidation now writes claims + edges/events in addition to current artifacts.
```

---

## CH-13: Claim Emission Tests
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add tests for claim emission path.

Create tests/test_claim_emission.py covering:
- claims emitted on topic create
- claims updated on merge
- contradiction creates claim edge + event
- temporal validity stays consistent with record valid_from/valid_until

Run:
- pytest tests/test_claim_emission.py tests/test_contradictions.py tests/test_temporal_records.py -q

Acceptance criteria:
- Claim emission behavior is validated end-to-end for consolidation cases.
```

---

## CH-14: Claim Retrieval Fusion (`as_of` Included)
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add claim retrieval to recall flow.

In context_assembler.py:
- Add _search_claims path.
- Rank claims with semantic + keyword signals.
- Support temporal filtering when as_of is provided.
- Add uncertainty labels for low-confidence or recently contradicted claims.

In types.py:
- Extend RecallResult to include claims.

In client.py:
- Return claims in MemoryClient.recall.

Constraints:
- Backward compatible: existing fields must remain unchanged.

Acceptance criteria:
- recall() returns claims without breaking existing consumers.
```

---

## CH-15: API Surface for Claims
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Expose claim retrieval in public interfaces.

Update:
- src/consolidation_memory/schemas.py
- src/consolidation_memory/server.py
- src/consolidation_memory/rest.py

Add endpoints/tools for:
- claim browse/search
- claim temporal query (as_of)

Update docs:
- README.md sections for new tools/endpoints

Constraints:
- Keep existing tool names and behavior backward compatible.

Acceptance criteria:
- Claims are available through MCP/REST/OpenAI tool schemas.
```

---

## CH-16: Retrieval/API Tests
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add tests for claim retrieval and API wiring.

Required coverage:
- claim results included in recall response
- claim as_of behavior
- MCP tool dispatch for claim calls
- REST request/response validation for claims
- backward compatibility checks for existing recall consumers

Run:
- pytest tests/test_claim_retrieval.py tests/test_schemas.py tests/test_rest.py tests/test_client.py -q

Acceptance criteria:
- New retrieval/API behavior is covered and backward compatibility is protected.
```

---

## CH-17: Drift Detection Module + Wiring
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Implement automatic belief challenge on code drift.

Add src/consolidation_memory/drift.py:
- get changed files via git diff (working tree and optional base_ref)
- map changed files to anchored episodes/claims
- produce impacted claim list

Wire into:
- MemoryClient.detect_drift(...)
- CLI command: consolidation-memory detect-drift
- REST endpoint for drift detection

DB updates:
- mark impacted claims as challenged (or confidence downshift)
- write claim_event "code_drift_detected"

Acceptance criteria:
- drift command and API return deterministic impacted claims with audit events.
```

---

## CH-18: Drift Tests
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add tests for drift detection and invalidation.

Create tests/test_drift_invalidation.py:
- mocked git diff output maps to anchors
- impacted claims are marked challenged
- claim_event logged
- CLI and REST wrappers behave correctly

Run:
- pytest tests/test_drift_invalidation.py tests/test_cli.py tests/test_rest.py -q

Acceptance criteria:
- Drift behavior is test-covered and deterministic.
```

---

## CH-19: Utility-Driven Consolidation Scheduler
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add utility-based consolidation triggering.

Implement:
- new utility scoring logic (module in consolidation package or client support module)
- score inputs:
  - unconsolidated backlog
  - recall miss/fallback signal
  - contradiction spike
  - challenged claim backlog from drift

Integrate in MemoryClient background loop:
- run consolidation when score >= threshold
- keep interval timer as fallback safety trigger

Config:
- add utility weights + threshold in config.py
- include config validation

Acceptance criteria:
- Scheduler can trigger by utility score with deterministic config behavior.
```

---

## CH-20: Scheduler Tests
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Add tests for adaptive scheduler.

Create tests/test_adaptive_consolidation.py:
- high utility triggers consolidation
- low utility skips
- interval fallback still triggers
- status output exposes utility scheduler state

Run:
- pytest tests/test_adaptive_consolidation.py tests/test_client.py tests/test_core.py -q

Acceptance criteria:
- Adaptive scheduler logic is validated and stable.
```

---

## CH-21: Novelty Eval Harness + Guide
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Build novelty eval harness and documentation.

Implement:
- benchmarks/novelty_eval.py with scenarios:
  - stale belief after code change
  - contradiction evolution
  - temporal belief reconstruction
  - provenance trace completeness
- Output JSON schema aligned to docs/NOVELTY_METRICS.md
- docs/NOVELTY_EVAL_GUIDE.md with run instructions and interpretation

Command:
- python -m benchmarks.novelty_eval --mode quick

Constraints:
- Default run should avoid cloud dependencies where possible.

Acceptance criteria:
- Eval script produces pass/fail against novelty metrics.
```

---

## CH-22: CI Gates + Export/Import + Final Hardening
Paste in a fresh chat:

```text
You are working in C:\Users\gore\consolidation-memory.

Task:
Finalize release hardening and enforce novelty in CI.

Implement:
1. CI:
   - update .github/workflows to run:
     - claim graph tests
     - drift tests
     - adaptive scheduler tests
     - novelty eval quick mode
   - fail build on metric gate miss
2. Data portability:
   - include claims/edges/sources/events/anchors in export/import flows
3. Docs:
   - update docs/ARCHITECTURE.md with claim graph + drift + scheduler design
   - update README.md with new commands and APIs
4. Integration:
   - add/extend integration tests for:
     store -> consolidate -> claim retrieval -> drift -> recall

Run:
- pytest tests/test_integration.py tests/test_rest.py tests/test_schemas.py tests/test_client.py -q

Acceptance criteria:
- CI gates novelty metrics.
- Export/import round-trip includes new graph entities.
- End-to-end integration remains stable.
```

---

## Standard Handoff Note (Use After Every Chunk)
Copy this format exactly:

1. Scope completed
2. Files changed
3. Tests run and results
4. Remaining risks
5. Ready for next chunk: `yes` or `no`
