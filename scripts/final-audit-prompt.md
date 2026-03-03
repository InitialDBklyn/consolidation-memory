# Final Essential Audit — consolidation-memory

You are auditing `D:\consolidation-memory`, a local-first persistent memory system for AI agents. It's a Python package (~11K lines, 31 source files, 27 test files, 526 tests). The codebase has already been through two hardening passes but recurring classes of bugs keep surfacing. Your job is to do the FINAL pass that catches everything.

## Project structure

```
src/consolidation_memory/
  __init__.py          # version
  __main__.py          # entry point
  client.py            # MemoryClient — main API surface (~800 lines)
  database.py          # SQLite + FTS5 layer (~500 lines)
  server.py            # MCP server (FastMCP, stdio transport)
  rest.py              # FastAPI REST server
  schemas.py           # OpenAI-compatible function-call schemas
  config.py            # TOML config, singleton
  context_assembler.py # retrieval ranking + context window assembly
  plugins.py           # hook-based plugin system
  circuit_breaker.py   # circuit breaker for embedding backends
  backends/            # embedding backends (fastembed, openai, stub)
  consolidation/
    engine.py          # consolidation orchestrator (~600 lines)
    prompting.py       # LLM prompt construction + parsing
    clustering.py      # FAISS-based semantic clustering
  dashboard.py         # Textual TUI
  dashboard_data.py    # read-only SQLite queries for dashboard
  vector_store.py      # FAISS index wrapper
  record_cache.py      # LRU cache for knowledge records
  types.py             # shared type aliases
  utils.py             # shared helpers
scripts/
  release.py           # release automation
tests/                 # 27 test files, 526 tests
```

## What you are looking for

You are NOT looking for style issues, missing docstrings, or nice-to-haves. You are looking for bugs that will cause incorrect behavior, data loss, crashes, or security issues in production. Specifically:

### 1. Data consistency — the #1 priority

Every path that writes to SQLite, FAISS, or the filesystem must be checked for:

- **Atomicity**: If an operation writes to multiple stores (SQLite episode + FAISS vector + FTS index), can a crash between steps leave them inconsistent? Is the FTS insert/delete inside the same `get_connection()` context as the episode insert/delete?
- **FAISS ↔ SQLite drift**: After every FAISS operation (add, remove, tombstone), does the id_map/tombstone sidecar get saved? Can a crash lose the FAISS state but keep the SQLite state?
- **Record counts**: `browse()` returns per-topic `record_counts` that currently show all zeros even though 26 records exist globally. Trace the `browse()` method in `client.py` through `dashboard_data.py` and `database.py` to find why per-topic counts are wrong. This is a KNOWN BUG — find and fix it.
- **Consolidation state machine**: Episodes transition through `pending → consolidated → pruned`. Verify that every code path that changes `consolidated` status does so atomically with any related side effects.

### 2. API surface parity

There are THREE API surfaces that must behave identically:
- `server.py` (MCP tools)
- `rest.py` (FastAPI endpoints)
- `schemas.py` (OpenAI function-call dispatch)

For EVERY operation (store, recall, search, forget, consolidate, correct, compact, protect, export, browse, read_topic, timeline, contradictions, consolidation_log, decay_report, store_batch, status), verify:

- Same parameter validation (content length, batch size, n_results bounds, filename safety)
- Same error handling (try/except returning error JSON, not crashing)
- Same return format
- REST endpoints use `asyncio.to_thread()` for all blocking `client.*` calls
- MCP handlers use `await asyncio.to_thread()` for all blocking calls

### 3. Thread safety

The system runs in multithreaded contexts (MCP server, background consolidation thread, REST with uvicorn workers). Check:

- Every singleton (`get_config()`, `get_plugin_manager()`, backend instances) uses proper locking
- `get_connection()` nest counting uses thread-local storage correctly
- Background consolidation thread checks stop event AND pool liveness before submitting work
- No mutable class-level defaults (lists, dicts) that would be shared across instances
- `circuit_breaker.py` state transitions are atomic under lock

### 4. Input validation & injection

- Every string that reaches an LLM prompt passes through `_sanitize_for_prompt()`
- Every filename parameter (topic filenames in correct, read_topic) is validated against path traversal (`..`, `/`, `\`)
- `content_type` is validated to the allowed set (`exchange`, `fact`, `solution`, `preference`)
- `surprise` is coerced to float with fallback
- Batch operations validate each element

### 5. Error paths that silently corrupt

These are the worst bugs — things that fail quietly:

- `json.dumps()` calls without `default=str` will crash on datetime objects
- `bool("false")` is `True` in Python — any TOML config boolean parsed from string must use proper coercion
- ISO datetime string comparison (`"2025-01-01" > "2024-12-31"`) works but `"2025-1-1" > "2024-12-31"` does NOT — verify all datetime comparisons use parsed datetime objects, not string ordering
- `.get()` on a sqlite3.Row does NOT work like dict.get() in all Python versions — verify Row access patterns
- `re.sub(..., count=1)` returns the original string if no match — version substitution in release.py must verify the change took effect

### 6. Resource cleanup

- `ThreadPoolExecutor.shutdown()` must use `wait=True, cancel_futures=True`
- File handles opened for FAISS/JSON sidecar files must be closed
- Database connections: verify `_all_connections` cleanup doesn't grow unboundedly
- Background threads must be daemonic OR have explicit shutdown paths

### 7. Consolidation engine correctness

`engine.py` is the most complex module. Verify:

- Every early return path fires `on_consolidation_complete` plugin hook
- Error reports include all required numeric fields (zeroed, not missing)
- Version file timestamps have enough resolution to avoid collisions (microseconds)
- `_merge_into_existing` validates the target filename before writing
- The consolidation lock prevents concurrent runs
- Pruning only deletes episodes that are both consolidated AND old enough

## How to execute this audit

1. **Read every source file** in `src/consolidation_memory/`. All 31 of them. Do not skip any.
2. **Trace data flows end-to-end**: pick each public API method (store, recall, forget, consolidate, etc.) and trace it from the API surface through client.py, database.py, vector_store.py, and back.
3. **For each bug found**: describe the exact file, line, root cause, impact, and fix.
4. **Categorize findings**: CRITICAL (data loss/corruption/security), HIGH (crashes/wrong results), MEDIUM (edge case failures), LOW (cosmetic/defensive).
5. **Fix everything CRITICAL and HIGH**. Fix MEDIUM if straightforward.
6. **Run `python -m pytest tests/ -x -q` AND `python -m ruff check src/ tests/` BEFORE any commit**. Do not push without green tests.
7. **After fixing, re-read the files you changed** to verify your edits are correct. Don't trust that an edit landed right — confirm it.

## Known issues to fix immediately

1. **`browse()` record_counts mismatch**: Per-topic record counts show all zeros. The bug is likely in how `client.py`'s `browse()` method queries or assembles the record counts. Trace through database.py's topic/record queries.

2. **Stale test count in knowledge topic**: Topic "Release and Implementation of Temporal Belief Queries" says 494 tests — actual is 526. Use `memory_correct` to fix after finding root cause of why consolidation produced stale data.

3. **Solution descriptions too terse**: The consolidation LLM produced solutions like "Ensured atomic operations" without explaining HOW. Check if `_build_merge_extraction_prompt` in `prompting.py` instructs the LLM to include implementation details. If not, improve the prompt.

## What "done" looks like

- Zero CRITICAL or HIGH findings remaining
- All tests pass (should be 526+)
- Ruff clean
- The `browse()` record count bug is fixed and verified
- You can explain, for every public API method, exactly what validation, error handling, and atomicity guarantees it provides
