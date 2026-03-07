# Canonical Query Semantics

Date: 2026-03-07  
Status: Implemented

## Purpose

Define the canonical trust-preserving query semantics for `consolidation-memory` and the adapter contract that MCP, REST, Python, and future adapters must follow.

## Canonical Service Layer

The first-class query service is `CanonicalQueryService` in `src/consolidation_memory/query_service.py`.

Canonical query envelopes:

- `RecallQuery`
- `EpisodeSearchQuery`
- `ClaimBrowseQuery`
- `ClaimSearchQuery`
- `DriftQuery`

Canonical adapter-facing `MemoryClient` entrypoints:

- `query_recall(...)`
- `query_search(...)`
- `query_browse_claims(...)`
- `query_search_claims(...)`
- `query_detect_drift(...)`

Backward-compatible methods (`recall`, `recall_with_scope`, `search`, `search_with_scope`, `browse_claims`, `search_claims`, `detect_drift`) remain thin wrappers over the canonical entrypoints.

## Trust Semantics Invariants

### 1. Temporal Query Invariant

Every adapter must preserve temporal fields exactly:

- `as_of`
- `after`
- `before`
- `include_expired`

`query_recall` and `query_browse_claims`/`query_search_claims` must execute against snapshot-aware data paths (`get_records_as_of`, `get_claims_as_of`, and `context_assembler.recall` temporal behavior) so results represent belief state at time `T`.

### 2. Provenance-Aware Recall Invariant

Canonical recall responses must keep provenance fields intact when present:

- `source_episodes`
- `source_dates`
- `source_summary`

Adapters must pass these fields through unchanged.

### 3. Contradiction-Aware Recall Invariant

Canonical recall responses must preserve contradiction uncertainty signaling:

- per-record/topic/claim uncertainty markers
- aggregate warnings list

Adapters must not strip or reinterpret contradiction warnings.

### 4. Drift-Aware Invalidation/Challenge Invariant

All drift detection must go through canonical `query_detect_drift` semantics, which:

- computes changed anchors
- maps impacted claims
- challenges valid active claims via anchor matches
- emits drift impact payloads consistently

Adapters must not implement custom drift challenge logic.

### 5. Scope Isolation Invariant

Scope-aware query inputs must be resolved through `MemoryClient.build_operation_context(...)` and applied to canonical query execution. Adapters must pass scope as structured data and avoid custom scope filtering rules.

When claim browse/search receives an explicit scope envelope, filtering must be provenance-based (via claim source scope rows), not heuristic string matching.

## Adapter Contract

### Current Surface Mapping

- MCP:
  - `memory_recall` -> `MemoryClient.query_recall`
  - `memory_search` -> `MemoryClient.query_search`
  - `memory_claim_browse` -> `MemoryClient.query_browse_claims`
  - `memory_claim_search` -> `MemoryClient.query_search_claims`
  - `memory_detect_drift` -> `MemoryClient.query_detect_drift`
- REST:
  - `/memory/recall` -> `query_recall`
  - `/memory/search` -> `query_search`
  - `/memory/claims/browse` -> `query_browse_claims`
  - `/memory/claims/search` -> `query_search_claims`
  - `/memory/detect-drift` -> `query_detect_drift`
- OpenAI tool dispatch (`schemas.py`):
  - `memory_recall` -> `query_recall`
  - `memory_search` -> `query_search`
  - `memory_claim_browse` -> `query_browse_claims`
  - `memory_claim_search` -> `query_search_claims`
  - `memory_detect_drift` -> `query_detect_drift`
- Python SDK:
  - external callers can use canonical `query_*` methods directly.

### Required Rules For Future Adapters

1. Always route through `MemoryClient.query_*` methods for query/read operations.
2. Never call `context_assembler`, `database`, or `drift` directly from adapters.
3. Preserve input semantics without reinterpretation:
   - temporal fields
   - limit bounds
   - scope envelope
4. Return canonical result shapes unchanged (`RecallResult`, `SearchResult`, `ClaimBrowseResult`, `ClaimSearchResult`, `DriftOutput`).

## Verification Strategy

The refactor is validated by:

- canonical service tests: `tests/test_query_service.py`
- adapter routing tests:
  - `tests/test_server.py`
  - `tests/test_rest.py`
  - `tests/test_schemas.py`
  - `tests/test_claim_retrieval.py`
  - `tests/test_temporal_belief_queries.py`
- full suite regression run (`pytest -q`)
