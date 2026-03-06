# consolidation-memory Roadmap (Objective)

## North Star
Make consolidation-memory the default long-term memory layer for coding agents:
- high recall usefulness
- temporal belief correctness
- low operator overhead
- broad integration compatibility

## Success Metrics
- Recall precision@5 on coding benchmark >= 0.80
- Correction consistency (markdown/topic/records aligned) >= 99.5%
- Temporal query correctness (`as_of`) >= 99%
- Consolidation failure rate <= 2%
- Time-to-first-value for a new user <= 10 minutes

## Mandatory Release Gates
- Releases must satisfy `docs/RELEASE_GATES.md`; this is a hard go/no-go control, not advisory guidance.
- `docs/NOVELTY_WEDGE.md` is the scope contract for novelty claims and acceptable release scope.
- `docs/NOVELTY_METRICS.md` defines release-blocking pass/fail thresholds for novelty outcomes.
- Release is blocked if any required gate fails, lacks evidence, or has evidence older than 7 days (fail closed).

## Phase 1 (Weeks 1-4): Reliability + Eval Foundation
Focus:
- define memory invariants as testable contract
- make extraction/correction quality measurable

Deliverables:
- golden eval corpus for coding sessions (facts, solutions, preferences, procedures)
- benchmark runner with versioned metrics output
- invariant checks for:
  - topic markdown <-> topic metadata <-> knowledge records
  - contradiction/expiry timeline integrity
  - export/import round-trip consistency

Exit Criteria:
- CI runs eval harness
- no critical/high integrity regressions in core paths

## Phase 2 (Weeks 5-8): Coding-Agent Product Wedge
Focus:
- make day-to-day coding memory workflows obvious and reliable

Deliverables:
- improved task-level retrieval ranking for debugging/build workflows
- stronger correction workflow UX (clear before/after + confidence change visibility)
- memory health summary at a glance (decay, contradictions, stale topics)

Exit Criteria:
- weekly dogfood users report recall usefulness improvement
- correction workflow is predictable and auditable

## Phase 3 (Weeks 9-12): OpenAI-Compatible Agent Integration
Focus:
- frictionless use in tool-calling chat loops

Deliverables:
- canonical OpenAI tool-calling loop example kept production-grade
- prompt pack covering all memory tools and common multi-tool flows
- integration regression tests for tool dispatch contracts

Exit Criteria:
- reference integration can run end-to-end with no manual patching
- all tool contracts stable across patch releases

## Phase 4 (Weeks 13-18): Scale + Ops Hardening
Focus:
- resilience under larger memory volumes and long-lived usage

Deliverables:
- performance profile and targets for:
  - recall latency
  - consolidation duration
  - compaction overhead
- observability outputs for consolidation outcomes and contradiction trends
- safer migration/repair paths for storage/index drift

Exit Criteria:
- predictable performance at larger dataset sizes
- recovery runbooks validated by tests

## Phase 5 (Weeks 19-26): Platform Readiness
Focus:
- convert from useful project to dependable memory infrastructure

Deliverables:
- compatibility matrix (MCP/REST/OpenAI-compatible workflows)
- stronger multi-project isolation guarantees and tooling
- mandatory release gating enforcement via `docs/RELEASE_GATES.md`, including novelty wedge and novelty metrics evidence

Exit Criteria:
- release confidence built on measurable quality, not ad hoc validation
- clear differentiation: temporal, auditable, self-correcting agent memory

## Non-Goals (for This Roadmap)
- generic "AI memory for everything" positioning
- premature multi-tenant cloud service expansion
- broad feature expansion without reliability evidence
