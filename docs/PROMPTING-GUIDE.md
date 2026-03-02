# Prompting Guide: Working with Claude on This Project

How to get the best results from Claude Code sessions on consolidation-memory.

---

## The Setup (already done)

1. **CLAUDE.md** — loaded automatically every session. Contains project structure,
   conventions, code style, architecture decisions, and a pointer to the roadmap.
2. **docs/ROADMAP.md** — the full multi-phase plan. Claude reads it on demand.
3. **docs/ARCHITECTURE.md** — detailed internals with Mermaid diagrams.

Claude reads CLAUDE.md at session start. It does NOT automatically read the
roadmap or architecture docs — you need to reference them.

---

## Prompting Patterns

### Continue the roadmap

```
continue the roadmap
```

Claude will read `docs/ROADMAP.md`, find the next incomplete item, enter plan
mode to design the approach, then implement it. This is the default workflow
for feature work.

### Implement a specific item

```
implement roadmap item 2.1 (hybrid search with BM25 + FTS5)
```

More targeted. Claude goes straight to that item. Use when you want to skip
ahead or revisit something.

### Implement with constraints

```
implement 2.1 hybrid search, but keep it behind a config flag so the old
pure-semantic path still works as a fallback
```

Add constraints inline. Claude will incorporate them into its plan.

### Review before implementing

```
plan out how you'd implement 2.1 hybrid search — show me the approach
before writing code
```

Forces plan mode. You'll see the file list, migration strategy, and test
approach before any code is written. Approve or redirect.

### Bug fix / investigation

```
recall is returning irrelevant results when querying for exact function
names like "get_connection". investigate and fix.
```

For bugs, describe the symptom. Claude will grep, read, diagnose, and fix.
Don't prescribe the solution unless you know the root cause.

### Code review

```
/review
```

Uses the review skill. Reviews recent changes for bugs, style issues, and
architectural concerns.

### Release

```
/release
```

Runs the release skill. Bumps version, updates changelog, tags, pushes.

---

## What Makes a Good Prompt

### Be specific about scope

Bad: "improve recall"
Good: "implement BM25 hybrid search as described in roadmap 2.1"

### State the acceptance criteria

Bad: "add FTS5 search"
Good: "add FTS5 search. schema migration, config flags for weights,
tests showing it finds exact matches that pure semantic misses"

### Tell Claude what NOT to do

The roadmap already has a "What NOT to Do" section, but for individual tasks:

"implement 2.3 query expansion. don't add a new MCP tool for this — it
should be transparent inside the existing recall flow"

### Reference files when relevant

"the scoring logic in context_assembler.py needs to blend BM25 scores
with the existing cosine similarity. read that file first."

Claude reads CLAUDE.md automatically but won't read arbitrary files unless
you tell it to or it decides to during exploration.

---

## Session Management

### Fresh session, continuing work

```
continue the roadmap
```

or

```
I'm working on phase 2. Last session I finished 2.1 (hybrid search).
pick up with 2.2 (diff-aware merge validation).
```

Giving context about what's done helps Claude orient faster than
re-reading the whole roadmap.

### Long session, multiple features

Commit between features:

```
commit that, then move on to 2.2
```

Claude will commit with a descriptive message, then start the next item.
This keeps the git history clean and makes rollback easy.

### When Claude goes off track

```
stop. that's overengineered. I just need [simpler thing].
revert what you wrote and try again with [constraint].
```

Be direct. Claude won't be offended. The clearer your redirect, the
faster it course-corrects.

---

## Anti-Patterns to Avoid

### Don't dump the entire roadmap as a prompt

The roadmap is a reference document, not a prompt. Say "continue the
roadmap" and let Claude read the file. Pasting the whole thing wastes
context window.

### Don't ask for everything at once

Bad: "implement all of phase 2"
Good: "implement 2.1" → commit → "implement 2.2" → commit → ...

Each item should be a discrete commit. This gives you review points
and rollback granularity.

### Don't skip the plan step for big features

For anything touching multiple files or adding schema migrations,
let Claude enter plan mode first. The 2 minutes spent reviewing a
plan saves 20 minutes of undoing wrong assumptions.

### Don't say "make it production ready"

Vague quality directives lead to over-engineering. If you want specific
improvements (error handling, edge cases, performance), name them.

---

## Updating the Roadmap

When a phase is complete or priorities change:

```
update docs/ROADMAP.md — mark 2.1 as done, add a new item 2.5 for
[description]. update CLAUDE.md if the current phase pointer changed.
```

Keep the roadmap as the single source of truth for project direction.
CLAUDE.md just points at it.
