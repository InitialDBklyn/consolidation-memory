# Novelty Wedge

## Positioning
**Temporal, auditable, code-state-aware memory for coding agents.**

This wedge is not "better retrieval" in general. It is about making agent memory dependable when codebases and beliefs change over time.

## Primary User Profile
Primary user: a senior IC or tech lead who uses coding agents daily on a real repository (not toy prompts), across many short sessions.

What this user needs:
- Memory that survives chat resets and tool/client switching.
- Recall that can answer "what was true then vs now?" with timestamps.
- Auditability: every recalled claim must point to source episodes/records.
- Protection against stale guidance after file or commit-level code drift.

## Top 3 Concrete Use Cases
1. **Drift-aware debugging memory**
   An agent recalls a prior fix tied to `src/api/auth.py`. After refactors touch that file, the old claim is marked challenged, and recall surfaces uncertainty instead of confidently repeating stale instructions.

2. **Contradiction-aware operational runbooks**
   Two valid fixes exist across time for the same failure mode (before and after a dependency upgrade). The system keeps both with temporal validity and contradiction events, so `as_of` queries return the correct one for a target date.

3. **Auditable handoff across sessions/agents**
   A second agent (or same agent in a fresh chat) asks why a config decision was made. Recall returns the claim plus provenance (episode IDs, timestamps, related topic/record links) so the user can verify and correct quickly.

## Top 3 Non-Goals
1. **Not a generic personal knowledge app**
   This wedge is for coding workflows and repository-grounded memory, not life logging or broad note-taking.

2. **Not full autonomous code understanding**
   It does not attempt full-repo semantic reasoning or static analysis replacement; it tracks anchored claims and their validity.

3. **Not cloud-first team synchronization**
   Multi-tenant sync, permissions, and hosted collaboration are out of scope for this wedge.

## Why Now
Coding-agent usage has shifted from isolated prompts to ongoing repository work, where stale memory causes real regressions. Existing vector-memory patterns are weak on temporal validity and provenance, which blocks trust in production workflows. consolidation-memory already has local-first storage, consolidation, temporal records, and contradiction tracking; adding claim-level audit trails plus code-state drift handling is a focused, high-leverage extension rather than a platform rewrite.

## Implementation Direction Implied by This Wedge
- Model memory as **claims with lifecycle state** (active/challenged/expired), not just untyped snippets.
- Store **explicit provenance links** from claims to episodes/topics/records.
- Support **time-scoped retrieval** (`as_of`) as a first-class query path.
- Add **code anchors** (file paths, commits, tools) at ingestion for drift mapping.
- Treat drift and contradictions as **events** written to durable audit history.
