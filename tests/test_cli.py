"""Tests for CLI commands, particularly `consolidation-memory test`."""

import pytest
from unittest.mock import patch, MagicMock

from consolidation_memory.database import ensure_schema
from helpers import make_normalized_vec as _make_normalized_vec


class TestCmdTest:
    """Tests for the `consolidation-memory test` CLI subcommand."""

    def test_all_checks_pass(self, capsys):
        """Happy path: all steps succeed, exit normally (no sys.exit)."""
        ensure_schema()
        vec = _make_normalized_vec()

        mock_backend = MagicMock()
        mock_backend.encode_documents.return_value = vec.reshape(1, -1)
        mock_backend.encode_query.return_value = vec.reshape(1, -1)
        mock_backend.dimension = 384

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "OK"

        with (
            patch("consolidation_memory.backends.get_embedding_backend", return_value=mock_backend),
            patch("consolidation_memory.backends.get_llm_backend", return_value=mock_llm),
        ):
            from consolidation_memory.cli import cmd_test
            cmd_test()

        captured = capsys.readouterr()
        assert "checks passed" in captured.out
        # All checks should pass — no X marks
        assert "\u2717" not in captured.out

    def test_all_checks_pass_llm_disabled(self, capsys):
        """When LLM is disabled, it should be skipped (not failed)."""
        from consolidation_memory.config import override_config

        ensure_schema()
        vec = _make_normalized_vec()

        mock_backend = MagicMock()
        mock_backend.encode_documents.return_value = vec.reshape(1, -1)
        mock_backend.encode_query.return_value = vec.reshape(1, -1)
        mock_backend.dimension = 384

        with (
            override_config(LLM_BACKEND="disabled"),
            patch("consolidation_memory.backends.get_embedding_backend", return_value=mock_backend),
        ):
            from consolidation_memory.cli import cmd_test
            cmd_test()

        captured = capsys.readouterr()
        assert "checks passed" in captured.out
        assert "disabled" in captured.out
        # LLM skipped, but no failures
        assert "\u2717" not in captured.out

    def test_embedding_failure_reports_and_cleans_up(self, capsys):
        """When embedding backend fails, recall is skipped and test episode is cleaned up."""
        ensure_schema()

        mock_backend = MagicMock()
        mock_backend.encode_documents.side_effect = ConnectionError("server unreachable")

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "OK"

        with (
            patch("consolidation_memory.backends.get_embedding_backend", return_value=mock_backend),
            patch("consolidation_memory.backends.get_llm_backend", return_value=mock_llm),
            pytest.raises(SystemExit) as exc_info,
        ):
            from consolidation_memory.cli import cmd_test
            cmd_test()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        assert "server unreachable" in captured.out

    def test_cleanup_on_failure(self):
        """Test episode is soft-deleted even when recall fails."""
        ensure_schema()
        vec = _make_normalized_vec()

        mock_backend = MagicMock()
        mock_backend.encode_documents.return_value = vec.reshape(1, -1)
        # Make encode_query fail so recall fails
        mock_backend.encode_query.side_effect = ConnectionError("query failed")
        mock_backend.dimension = 384

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "OK"

        with (
            patch("consolidation_memory.backends.get_embedding_backend", return_value=mock_backend),
            patch("consolidation_memory.backends.get_llm_backend", return_value=mock_llm),
            pytest.raises(SystemExit),
        ):
            from consolidation_memory.cli import cmd_test
            cmd_test()

        # Verify no test episodes remain in the database
        from consolidation_memory.database import get_all_episodes
        episodes = get_all_episodes(include_deleted=False)
        test_eps = [e for e in episodes if "consolidation-memory-test" in e["content"]]
        assert test_eps == [], "Test episode was not cleaned up after failure"

    def test_no_color_when_env_set(self, capsys, monkeypatch):
        """NO_COLOR env var suppresses ANSI escape codes."""
        monkeypatch.setenv("NO_COLOR", "1")
        ensure_schema()
        vec = _make_normalized_vec()

        mock_backend = MagicMock()
        mock_backend.encode_documents.return_value = vec.reshape(1, -1)
        mock_backend.encode_query.return_value = vec.reshape(1, -1)
        mock_backend.dimension = 384

        mock_llm = MagicMock()
        mock_llm.generate.return_value = "OK"

        with (
            patch("consolidation_memory.backends.get_embedding_backend", return_value=mock_backend),
            patch("consolidation_memory.backends.get_llm_backend", return_value=mock_llm),
        ):
            from consolidation_memory.cli import cmd_test
            cmd_test()

        captured = capsys.readouterr()
        # No ANSI escape sequences
        assert "\033[" not in captured.out


class TestMainDispatch:
    """Test that 'test' subcommand is wired up in main()."""

    def test_test_subcommand_registered(self):
        """argparse recognizes 'test' as a valid subcommand."""
        from consolidation_memory.cli import main

        # Parse just the 'test' command to verify it's registered
        with (
            patch("sys.argv", ["consolidation-memory", "test"]),
            patch("consolidation_memory.cli.cmd_test") as mock_cmd,
        ):
            main()
            mock_cmd.assert_called_once()
