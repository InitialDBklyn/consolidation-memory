"""Shared knowledge record embedding cache for recall.

Caches embedded record texts for vector search. Invalidated when records change
(after consolidation or correction). Thread-safe.

Same race-condition prevention pattern as topic_cache: version counter guards
against stale writes when invalidation happens during a cache-miss fetch.
"""

import logging
import threading

import numpy as np

from consolidation_memory.database import get_all_active_records
from consolidation_memory.backends import encode_documents

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_version: int = 0
_cache: dict = {
    "version": -1,
    "texts": [],
    "vecs": None,
    "records": [],
}


def invalidate() -> None:
    """Force re-embedding on next get_record_vecs() call."""
    global _version
    with _lock:
        _version += 1


def get_record_vecs() -> tuple[list[dict], np.ndarray | None]:
    """Return (records, embedding_matrix) with caching.

    Cache is valid as long as its version matches the current version.
    Returns ([], None) if no records exist.
    """
    with _lock:
        if _cache["version"] == _version and _cache["vecs"] is not None:
            return _cache["records"], _cache["vecs"]
        fetch_version = _version

    records = get_all_active_records()
    if not records:
        return [], None

    texts = [r["embedding_text"] for r in records]
    try:
        vecs = encode_documents(texts)
    except Exception as e:
        logger.warning("Failed to embed record texts: %s", e, exc_info=True)
        return records, None

    with _lock:
        if _version == fetch_version:
            _cache["version"] = fetch_version
            _cache["texts"] = texts
            _cache["vecs"] = vecs
            _cache["records"] = records
        else:
            logger.debug(
                "Record cache populate discarded: version changed %d -> %d during fetch",
                fetch_version, _version,
            )

    return records, vecs
