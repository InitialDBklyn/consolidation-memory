# README Overhaul Design

**Date:** 2026-02-28
**Approach:** GitHub-native Markdown (no external assets, no build step)

## Goal

Complete overhaul of the consolidation-memory README into a best-in-class open source README. Pure Markdown + GitHub-flavored extensions. Must be visually distinctive, scannable, and tell a clear story.

## Structure

1. **Hero** — Centered `<div>`, title, tagline ("Your AI forgets everything between sessions. This fixes that."), one-line description, dark monochrome shield.io badges (PyPI, CI, Python, License) using `1a1a2e`/`0f0f1a` palette.

2. **Conversation example** — Tightened version of existing "build failing" example. Shows value proposition in context.

3. **Architecture diagram** — Mermaid flowchart replacing ASCII art. Three-stage pipeline: Store → Recall → Consolidate with data flow arrows.

4. **Feature pillars** — HTML table, three columns: Store / Recall / Consolidate. Each with icon-less one-line description emphasizing the key mechanic.

5. **Quick Start** — Two steps: `pip install` + `init`, then MCP config JSON block. Minimal friction.

6. **Integrations** — Collapsible `<details>` sections:
   - MCP Server (open by default) — config JSON + tools table
   - Python API — code example
   - OpenAI Function Calling — code example
   - REST API — install + endpoint table

7. **How Consolidation Works** — Mermaid sequence/flow diagram: fetch → cluster → match topics → LLM synthesize → write records → prune. Replaces dense paragraph.

8. **Backends** — Two tables: Embedding backends (FastEmbed/LM Studio/Ollama/OpenAI) and LLM backends.

9. **Configuration** — Collapsible `<details>`: TOML example + platform paths table.

10. **CLI Reference** — Command table.

11. **Data Storage** — Platform paths table + collapsible directory structure.

12. **Development** — Clone/install/test commands.

13. **License** — MIT, one line.

## Design Principles

- Dense reference content hidden in `<details>` — main scroll is narrative
- Mermaid diagrams for architecture (GitHub renders natively)
- Dark monochrome badge palette (`1a1a2e`/`0f0f1a`)
- No emoji section headers — clean `##` typography
- Story arc: hook → understand → install → integrate → configure → contribute
- Collapsible sections keep page length manageable while preserving all information

## Technical Constraints

- Pure GitHub-flavored Markdown + inline HTML
- Mermaid diagrams (supported natively by GitHub)
- shield.io badges (no custom image hosting)
- Must render correctly on GitHub, PyPI, and in terminal markdown viewers
- No external dependencies or build steps
