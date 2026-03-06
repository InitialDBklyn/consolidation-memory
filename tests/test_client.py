"""Tests for MemoryClient — the pure Python API.

Run with: python -m pytest tests/test_client.py -v
"""

import json
from unittest.mock import MagicMock, patch

from helpers import make_normalized_vec as _make_normalized_vec


class TestClientLifecycle:
    def test_construct_and_close(self):
        from consolidation_memory.database import ensure_schema
        ensure_schema()

        from consolidation_memory.client import MemoryClient
        client = MemoryClient(auto_consolidate=False)
        assert client._vector_store is not None
        client.close()

    def test_context_manager(self):
        from consolidation_memory.database import ensure_schema
        ensure_schema()

        from consolidation_memory.client import MemoryClient
        with MemoryClient(auto_consolidate=False) as client:
            assert client._vector_store is not None
        # after exit, thread should be stopped
        assert client._consolidation_thread is None

    def test_multiple_instances_safe(self):
        from consolidation_memory.database import ensure_schema
        ensure_schema()

        from consolidation_memory.client import MemoryClient
        c1 = MemoryClient(auto_consolidate=False)
        c2 = MemoryClient(auto_consolidate=False)
        c1.close()
        c2.close()


class TestClientStore:
    @patch("consolidation_memory.backends.encode_documents")
    def test_basic_store(self, mock_embed):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed.return_value = vec.reshape(1, -1)

        result = client.store("test content", content_type="fact", tags=["python"])
        assert result.status == "stored"
        assert result.id is not None
        assert result.content_type == "fact"
        assert result.tags == ["python"]

        client.close()

    @patch("consolidation_memory.backends.encode_documents")
    def test_surprise_clamping(self, mock_embed):
        from consolidation_memory.database import ensure_schema, get_episode
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed.return_value = vec.reshape(1, -1)

        # Surprise > 1.0 should clamp to 1.0
        r1 = client.store("high surprise", surprise=5.0)
        ep = get_episode(r1.id)
        assert ep["surprise_score"] == 1.0

        # Negative should clamp to 0.0
        vec2 = _make_normalized_vec(seed=99)
        mock_embed.return_value = vec2.reshape(1, -1)
        r2 = client.store("low surprise", surprise=-1.0)
        ep2 = get_episode(r2.id)
        assert ep2["surprise_score"] == 0.0

        client.close()


class TestClientRecall:
    @patch("consolidation_memory.backends.encode_query")
    @patch("consolidation_memory.backends.encode_documents")
    def test_basic_recall(self, mock_embed_docs, mock_embed_query):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed_docs.return_value = vec.reshape(1, -1)
        mock_embed_query.return_value = vec.reshape(1, -1)

        client.store("recall test content", content_type="fact")

        result = client.recall("recall test", n_results=5, include_knowledge=False)
        assert result.total_episodes == 1
        assert len(result.episodes) >= 1
        assert result.episodes[0]["content"] == "recall test content"

        client.close()

    @patch("consolidation_memory.backends.encode_query")
    @patch("consolidation_memory.backends.encode_documents")
    def test_empty_recall(self, mock_embed_docs, mock_embed_query):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed_query.return_value = vec.reshape(1, -1)

        result = client.recall("nothing here")
        assert result.total_episodes == 0
        assert len(result.episodes) == 0

        client.close()

    def test_recall_surfaces_claims_field(self):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)
        try:
            fake_recall = {
                "episodes": [],
                "knowledge": [],
                "records": [],
                "claims": [{"id": "claim-1", "canonical_text": "python runtime is 3.12"}],
                "warnings": [],
            }
            fake_stats = {
                "episodic_buffer": {"total": 0},
                "knowledge_base": {"total_topics": 0},
            }

            with (
                patch("consolidation_memory.context_assembler.recall", return_value=fake_recall),
                patch("consolidation_memory.database.get_stats", return_value=fake_stats),
            ):
                result = client.recall("python runtime")

            assert result.claims == fake_recall["claims"]
            assert result.episodes == []
            assert result.knowledge == []
            assert result.records == []
        finally:
            client.close()


class TestClientForget:
    @patch("consolidation_memory.backends.encode_documents")
    def test_forget_existing(self, mock_embed):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed.return_value = vec.reshape(1, -1)

        stored = client.store("forgettable content")
        result = client.forget(stored.id)
        assert result.status == "forgotten"
        assert result.id == stored.id

        client.close()

    def test_forget_nonexistent(self):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        result = client.forget("nonexistent-uuid")
        assert result.status == "not_found"

        client.close()


class TestClientStatus:
    @patch("consolidation_memory.backends.encode_documents")
    def test_status_counts(self, mock_embed):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed.return_value = vec.reshape(1, -1)

        client.store("status test episode")

        status = client.status()
        assert status.episodic_buffer["total"] == 1
        assert status.faiss_index_size == 1
        from consolidation_memory import __version__
        assert status.version == __version__
        assert status.embedding_backend != ""

        client.close()


class TestClientExport:
    @patch("consolidation_memory.backends.encode_documents")
    def test_export_round_trip(self, mock_embed):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed.return_value = vec.reshape(1, -1)

        client.store("export test", content_type="fact", tags=["test"])

        result = client.export()
        assert result.status == "exported"
        assert result.episodes == 1

        from pathlib import Path
        export_data = json.loads(Path(result.path).read_text(encoding="utf-8"))
        assert export_data["stats"]["episode_count"] == 1

        client.close()


class TestClientCompact:
    @patch("consolidation_memory.backends.encode_documents")
    def test_compact_with_tombstones(self, mock_embed):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec = _make_normalized_vec(seed=42)
        mock_embed.return_value = vec.reshape(1, -1)

        stored = client.store("tombstone test")
        client.forget(stored.id)

        result = client.compact()
        assert result.status == "compacted"
        assert result.tombstones_removed == 1
        assert result.index_size == 0

        client.close()

    def test_compact_no_tombstones(self):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        result = client.compact()
        assert result.status == "no_tombstones"
        assert result.tombstones_removed == 0

        client.close()

    @patch("consolidation_memory.backends.encode_documents")
    def test_compact_preserves_live_vectors(self, mock_embed):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        vec1 = _make_normalized_vec(seed=42)
        vec2 = _make_normalized_vec(seed=99)

        mock_embed.return_value = vec1.reshape(1, -1)
        client.store("keep this")

        mock_embed.return_value = vec2.reshape(1, -1)
        s2 = client.store("forget this")

        client.forget(s2.id)

        result = client.compact()
        assert result.status == "compacted"
        assert result.tombstones_removed == 1
        assert result.index_size == 1

        client.close()


class TestClientConsolidate:
    def test_consolidate_lock(self):
        from consolidation_memory.database import ensure_schema
        from consolidation_memory.client import MemoryClient

        ensure_schema()
        client = MemoryClient(auto_consolidate=False)

        # Acquire lock externally
        client._consolidation_lock.acquire()

        result = client.consolidate()
        assert result["status"] == "already_running"

        client._consolidation_lock.release()
        client.close()


class TestClientCorrect:
    def test_correct_updates_structured_records(self, tmp_data_dir):
        from consolidation_memory.client import MemoryClient
        from consolidation_memory.config import get_config
        from consolidation_memory.database import (
            ensure_schema,
            get_records_by_topic,
            insert_knowledge_records,
            upsert_knowledge_topic,
        )

        ensure_schema()
        cfg = get_config()
        filename = "python.md"
        (cfg.KNOWLEDGE_DIR / filename).write_text(
            "---\ntitle: Python\nsummary: Python 3.12\n---\n\n## Facts\n- **Python**: 3.12\n",
            encoding="utf-8",
        )
        topic_id = upsert_knowledge_topic(
            filename=filename,
            title="Python",
            summary="Python 3.12",
            source_episodes=["ep1"],
            fact_count=1,
            confidence=0.8,
        )
        insert_knowledge_records(
            topic_id,
            records=[{
                "record_type": "fact",
                "content": {"type": "fact", "subject": "Python", "info": "3.12"},
                "embedding_text": "Python: 3.12",
                "confidence": 0.8,
            }],
            source_episodes=["ep1"],
        )

        corrected_md = (
            "---\n"
            "title: Python\n"
            "summary: Python 3.13\n"
            "tags: [python]\n"
            "confidence: 0.9\n"
            "---\n\n"
            "## Facts\n"
            "- **Python**: 3.13\n"
        )
        mock_llm = MagicMock()
        mock_llm.generate.return_value = corrected_md

        client = MemoryClient(auto_consolidate=False)
        try:
            with patch("consolidation_memory.backends.get_llm_backend", return_value=mock_llm):
                result = client.correct(filename, "Python version changed to 3.13")

            assert result.status == "corrected"

            active = get_records_by_topic(topic_id, include_expired=False)
            assert len(active) == 1
            active_content = json.loads(active[0]["content"])
            assert active_content["info"] == "3.13"
            assert active[0]["valid_from"] is not None

            all_records = get_records_by_topic(topic_id, include_expired=True)
            assert len(all_records) == 2
            old = next(r for r in all_records if json.loads(r["content"]).get("info") == "3.12")
            assert old["valid_until"] is not None
        finally:
            client.close()
