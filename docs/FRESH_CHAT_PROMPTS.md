# Fresh-Chat Prompt Pack (All Memory Features)

Use one block at a time in a new chat that already has memory tools available.

## 0) Session Bootstrap (Recall + Grounding)
```text
Before answering, call memory_recall with a query that matches my opening request. Summarize relevant episodes, knowledge topics, and records. Then answer using that context and explicitly note any uncertainty.
```

## 1) `memory_store`
```text
Store this as one memory using memory_store:
content_type: solution
tags: ["build", "python", "windows"]
content: "Problem: pytest failed due temp-dir permission behavior on Windows sandbox. Fix: run tests with a repo-local basetemp and enforce PYTHONPATH to the local src tree when multiple checkouts exist."
surprise: 0.7
```

## 2) `memory_store_batch`
```text
Store these as a batch with memory_store_batch:
1) content_type=fact, tags=["repo"], content="Project uses SQLite + FAISS with structured knowledge records."
2) content_type=preference, tags=["workflow"], content="User prefers objective, direct feedback over hype."
3) content_type=solution, tags=["testing"], content="When pytest imports wrong checkout, set PYTHONPATH to active repo/src."
Use surprise=0.5 unless clearly novel.
```

## 3) `memory_recall`
```text
Run memory_recall for query: "recent fixes for memory consistency and path traversal". Return top 10 with include_knowledge=true. Then give me a concise synthesis of what changed and why it matters.
```

## 4) `memory_search`
```text
Run memory_search with query="path traversal", limit=20, content_types=["solution","fact"]. Return exact matches and a short summary of recurring patterns.
```

## 5) `memory_status`
```text
Call memory_status and give me an operational snapshot: episode totals, knowledge topic count, record count, index health, and anything that suggests maintenance is needed.
```

## 6) `memory_forget`
```text
Forget this episode id with memory_forget: "<EPISODE_ID>". Then confirm status and explain whether compaction should be run now or deferred.
```

## 7) `memory_export`
```text
Call memory_export. Return the export path plus counts (episodes, topics, records). Also tell me if this should be treated as a release checkpoint backup.
```

## 8) `memory_correct`
```text
Use memory_correct on topic_filename="<TOPIC_FILE.md>".
Correction:
"The previous guidance is outdated. Replace old behavior with: use strict resolve/is_relative_to guards for knowledge file reads, and keep knowledge_records synchronized during corrections by expiring active records and inserting updated records."
After correction, summarize what changed.
```

## 9) `memory_compact`
```text
Run memory_compact now. Report tombstones removed, resulting index size, and whether any follow-up action is needed.
```

## 10) `memory_consolidate`
```text
Run memory_consolidate now. When complete, summarize topics created/updated, contradictions found, pruned episodes, and any warnings that need review.
```

## 11) `memory_protect`
```text
Protect memory from pruning with memory_protect:
tag="critical-context"
Then confirm how many episodes are now protected and suggest a tagging strategy for long-term safety.
```

## 12) `memory_timeline`
```text
Run memory_timeline for topic: "python version guidance". Show chronological belief changes, including superseded records, and explain the current best belief.
```

## 13) `memory_contradictions`
```text
Call memory_contradictions with no filter. Rank the most important contradiction clusters and propose what to correct first.
```

## 14) `memory_browse`
```text
Call memory_browse and return all topics sorted by update recency. Highlight low-confidence topics and topics with high record churn.
```

## 15) `memory_read_topic`
```text
Use memory_read_topic for filename="<TOPIC_FILE.md>".
Then produce:
1) short summary
2) risky/outdated claims
3) concrete correction proposal
```

## 16) `memory_decay_report`
```text
Run memory_decay_report and give me:
1) what would be forgotten now
2) what should be protected
3) whether to run consolidation before pruning
```

## 17) `memory_consolidation_log`
```text
Call memory_consolidation_log with last_n=10. Summarize trend lines: consolidation quality, contradiction frequency, and pruning behavior.
```

## Composite Prompts

### A) Incident Triage
```text
Do a full incident-memory pass:
1) memory_recall for "recent failures related to this issue"
2) memory_search for exact error substrings in my message
3) answer with a fix plan
4) store the final problem+solution via memory_store
```

### B) Weekly Memory Hygiene
```text
Run weekly hygiene:
1) memory_status
2) memory_decay_report
3) memory_contradictions
4) memory_consolidation_log(last_n=5)
Then give a prioritized maintenance checklist.
```

### C) Knowledge Refresh Loop
```text
Refresh one topic end-to-end:
1) memory_browse and pick the stalest low-confidence topic
2) memory_read_topic
3) memory_correct with improved content
4) memory_timeline to verify belief transition
5) summarize final state and remaining uncertainty
```
