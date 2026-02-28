"""Consolidation package.

Re-exports all public and private APIs so that existing imports of the form
    from consolidation_memory.consolidation import X
continue to work without modification.
"""

from consolidation_memory.consolidation.clustering import (
    _compute_cluster_confidence,
    _find_similar_topic,
)
from consolidation_memory.consolidation.engine import (
    _detect_contradictions,
    _merge_into_existing,
    _process_cluster,
    _update_index,
    _version_knowledge_file,
    run_consolidation,
)
from consolidation_memory.consolidation.prompting import (
    _LLM_SYSTEM_PROMPT,
    _SANITIZE_RE,
    _build_contradiction_prompt,
    _build_distillation_prompt,
    _build_extraction_prompt,
    _build_merge_extraction_prompt,
    _call_llm,
    _count_facts,
    _embedding_text_for_record,
    _get_llm_circuit,
    _llm_circuit_lock,
    _llm_extract_with_validation,
    _llm_with_validation,
    _normalize_output,
    _parse_fm_lines,
    _parse_frontmatter,
    _parse_llm_json,
    _render_markdown_from_records,
    _sanitize_for_prompt,
    _slugify,
    _strip_code_fences,
    _validate_extraction_output,
    _validate_llm_output,
)
from consolidation_memory.consolidation.scoring import _adjust_surprise_scores

__all__ = [
    # engine
    "run_consolidation",
    "_version_knowledge_file",
    "_detect_contradictions",
    "_merge_into_existing",
    "_process_cluster",
    "_update_index",
    # clustering
    "_compute_cluster_confidence",
    "_find_similar_topic",
    # prompting
    "_LLM_SYSTEM_PROMPT",
    "_SANITIZE_RE",
    "_sanitize_for_prompt",
    "_slugify",
    "_get_llm_circuit",
    "_llm_circuit_lock",
    "_call_llm",
    "_strip_code_fences",
    "_normalize_output",
    "_parse_frontmatter",
    "_parse_fm_lines",
    "_count_facts",
    "_parse_llm_json",
    "_embedding_text_for_record",
    "_build_extraction_prompt",
    "_build_distillation_prompt",
    "_build_merge_extraction_prompt",
    "_build_contradiction_prompt",
    "_validate_extraction_output",
    "_validate_llm_output",
    "_llm_extract_with_validation",
    "_llm_with_validation",
    "_render_markdown_from_records",
    # scoring
    "_adjust_surprise_scores",
]
