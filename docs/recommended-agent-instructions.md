# Recommended Agent Instructions

Add this to your agent instruction file (for example `AGENTS.md`) so the
agent proactively uses memory tools.

You can add this automatically with:

```bash
consolidation-memory setup-memory --path AGENTS.md
```

Or copy the snippet below manually:

---

```markdown
## Memory

**Recall**: At the start of every new conversation, call `memory_recall`
with a query matching the user's opening message topic. This is your
persistent memory - always check it before responding.

**Store**: Proactively call `memory_store` whenever you:
- Learn something new about the user's setup, environment, or projects
- Solve a non-trivial problem (store both the problem AND the solution)
- Discover a user preference or workflow pattern
- Complete a significant task (summarize what was done and where)
- Encounter something surprising or noteworthy

Write each memory as a self-contained note that future-you can understand
without context. Use appropriate `content_type` (fact, solution, preference,
exchange) and add `tags` for organization. Do NOT store trivial exchanges
like greetings or simple Q&A.
```

---

## Optional Session-Start Reminder

If your agent platform supports startup hooks, add a lightweight reminder hook
that confirms memory tooling is active for the session.
