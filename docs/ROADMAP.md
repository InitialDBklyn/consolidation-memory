# consolidation-memory Roadmap

> Local-first episodic-to-knowledge consolidation. No competitor does hierarchical
> clustering + LLM synthesis + structured knowledge extraction locally. That's the moat.

## Strategic Principles

- **Don't chase feature parity with Mem0/Zep** — lean into local-first, consolidation, transparency
- **Best-in-class local recall quality** — if recall is noticeably better, everything else follows
- **Zero-friction adoption** — `pip install` + one JSON config = working memory across all tools
- **Transparency and trust** — users can see, curate, and understand their AI's memory

### What NOT to Do

- Don't add a cloud/SaaS layer — local-first is the moat
- Don't chase LangChain/CrewAI integrations — MCP is the universal protocol
- Don't add auth to MCP server — MCP is local stdio, auth adds complexity for no gain
- Don't build a sync protocol — leverage existing file sync tools
- Don't add image/audio embedding — stay focused on text memory

---

## Phase 1: Ship What's Built (v0.11.0) — DONE

- [x] Fix plugin system config gap (PLUGINS_ENABLED in Config)
- [x] Wire plugin hooks into MemoryClient (startup, shutdown, store, recall, forget)
- [x] Complete OpenAI function calling schemas (6 missing tools)
- [x] Complete REST API parity (7 missing endpoints)
- [x] Fix correct() ThreadPoolExecutor leak
- [x] Update ARCHITECTURE.md (schema v6 → v9)

---

## Phase 2: Recall Quality Leap (v0.12.0 – v0.13.0)

**Goal**: Make recall noticeably better. Highest-leverage work.

### 2.1 Hybrid search: BM25 + semantic

- **Current**: Recall is pure FAISS cosine similarity + priority scoring
- **Problem**: Semantic search fails on exact terms, acronyms, proper nouns.
  "Fix the CORS bug in AuthService" retrieves episodes about authentication
  generally, not the specific CORS fix.
- **Solution**: Add SQLite FTS5 alongside FAISS.
  `score = semantic_weight * cosine_sim + keyword_weight * bm25_score`
- **Files**: `database.py` (add FTS5 virtual table, schema migration),
  `context_assembler.py` (hybrid scoring)
- **Why**: Every competitor has hybrid search. This is table stakes.

### 2.2 Diff-aware merge validation

- After LLM merge, compare merged output against pre-merge records
- Flag any pre-merge claim with no semantic match (< 0.5) in merged output
  as "potentially dropped"
- Log to contradiction_log with resolution=`silent_drop`
- **Files**: `consolidation/engine.py`, `database.py`
- **Why**: Silent merge drift is the #1 trust issue with consolidation

### 2.3 Query expansion for recall

- When a recall query is short or ambiguous, use the LLM to expand it
- Example: "auth" → "authentication, login, JWT, session, OAuth, user credentials"
- Gate behind config flag, only when LLM backend != disabled
- **Files**: `context_assembler.py`, `client.py`

### 2.4 Recall result deduplication

- Currently, recall can return an episode AND a knowledge record derived from
  that same episode
- Deduplicate by checking if a record's source episodes overlap with returned episodes
- **Files**: `context_assembler.py`

---

## Phase 3: Entity & Relationship Layer (v0.14.0 – v1.0.0)

**Goal**: Move from flat episodes to a lightweight knowledge graph. Local-first
alternative to Mem0's graph memory.

### 3.1 Entity extraction during store

- Extract named entities (people, projects, tools, concepts) from episodes
- New `entities` table + `episode_entities` junction table
- Simple NLP (regex + heuristics), no LLM dependency
- Schema migration v10

### 3.2 Relationship extraction during consolidation

- Extend consolidation LLM prompt to extract relationships between entities
- New `entity_relationships` table
- Types: `uses`, `depends_on`, `prefers`, `replaced`, `related_to`

### 3.3 Entity-aware recall

- When query mentions a known entity, boost related episodes/records
- New recall path: query → extract entities → graph lookup → boost

### 3.4 New MCP tools

- `memory_entities(query?)` — list known entities
- `memory_entity_graph(entity)` — show entity relationships

### 3.5 v1.0.0 criteria

- All APIs at parity (MCP = REST = OpenAI schemas)
- Entity layer working
- Hybrid search (BM25 + semantic)
- Plugin system complete
- Comprehensive test coverage (target 400+)
- `disallow_untyped_defs = true` in mypy
- Updated ARCHITECTURE.md with entity layer docs

---

## Phase 4: Ecosystem & Adoption (post-1.0)

### 4.1 First-party plugins

- Git plugin: auto-store commit summaries
- Project context plugin: read CLAUDE.md/pyproject.toml as structured facts
- Export plugins: Obsidian vault, Logseq, Notion formats

### 4.2 TypeScript/Node SDK

- Thin client connecting to REST API
- `npm install consolidation-memory-client`

### 4.3 Dashboard upgrades

- Interactive: edit/delete episodes, resolve contradictions, manage entities
- Search/filter in episode browser
- Entity relationship graph visualization

### 4.4 Multi-machine sync

- Document how to sync SQLite + FAISS via git, Syncthing, or rsync
- Don't build a sync protocol — leverage existing tools

---

## Implementation Priority

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| **Done** | Phase 1 (fix, polish, ship) | 1-2 days | Unblocks everything |
| **Next** | 2.1 Hybrid search (BM25 + FTS5) | 2-3 days | Biggest recall improvement |
| **Next** | 2.2 Diff-aware merge validation | 1 day | Trust/safety |
| **Soon** | 2.3 Query expansion | 1 day | Better recall for short queries |
| **Soon** | 2.4 Result deduplication | Half day | Polish |
| **Later** | Phase 3 entity layer | 1-2 weeks | Major differentiator |
| **Future** | Phase 4 ecosystem | Ongoing | Adoption |
