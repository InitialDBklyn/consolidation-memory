"""Tests for multi-project namespace support: validation and project switching."""

from unittest.mock import patch

import pytest

from consolidation_memory.config import (
    validate_project_name,
    get_active_project,
    set_active_project,
)
from consolidation_memory import config


# ── Project name validation ──────────────────────────────────────────────────


class TestProjectNameValidation:
    """Tests for validate_project_name()."""

    @pytest.mark.parametrize(
        "name",
        [
            "default",
            "my-project",
            "project_1",
            "a",
            "0test",
            "abc-def_ghi",
            "a" * 64,  # max length
        ],
    )
    def test_valid_names(self, name):
        assert validate_project_name(name) == name

    def test_empty_name_raises(self):
        with pytest.raises(ValueError, match="must not be empty"):
            validate_project_name("")

    @pytest.mark.parametrize(
        "name",
        [
            "UPPER",
            "Mixed",
            "has space",
            "special!char",
            "path/../traversal",
            "a/b",
            "a\\b",
            ".hidden",
        ],
    )
    def test_invalid_special_chars(self, name):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name(name)

    def test_too_long_raises(self):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name("a" * 65)

    def test_starts_with_hyphen_raises(self):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name("-bad-start")

    def test_starts_with_underscore_raises(self):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name("_bad-start")

    def test_path_traversal_raises(self):
        with pytest.raises(ValueError, match="Invalid project name"):
            validate_project_name("..")


# ── set_active_project ───────────────────────────────────────────────────────


class TestSetActiveProject:
    """Tests for set_active_project() and get_active_project()."""

    def test_default_project(self, tmp_data_dir):
        """The fixture sets up 'default' as the active project."""
        assert get_active_project() == "default"

    def test_set_custom_project(self, tmp_data_dir):
        """Switching to a custom project updates _active_project and paths."""
        base = config._base_data_dir
        result = set_active_project("my-project")
        assert result == "my-project"
        assert get_active_project() == "my-project"
        assert config.DATA_DIR == base / "projects" / "my-project"

    def test_all_paths_recalculated(self, tmp_data_dir):
        """All path globals should point into the new project directory."""
        base = config._base_data_dir
        set_active_project("alpha")
        expected_data = base / "projects" / "alpha"

        assert config.DATA_DIR == expected_data
        assert config.DB_PATH == expected_data / "memory.db"
        assert config.FAISS_INDEX_PATH == expected_data / "faiss_index.bin"
        assert config.FAISS_ID_MAP_PATH == expected_data / "faiss_id_map.json"
        assert config.FAISS_TOMBSTONE_PATH == expected_data / "faiss_tombstones.json"
        assert config.FAISS_RELOAD_SIGNAL == expected_data / ".faiss_reload"
        assert config.KNOWLEDGE_DIR == expected_data / "knowledge"
        assert config.KNOWLEDGE_VERSIONS_DIR == expected_data / "knowledge" / "versions"
        assert config.CONSOLIDATION_LOG_DIR == expected_data / "consolidation_logs"
        assert config.BACKUP_DIR == expected_data / "backups"

    def test_log_dir_shared_across_projects(self, tmp_data_dir):
        """LOG_DIR is shared and must NOT change when project changes."""
        log_before = config.LOG_DIR
        set_active_project("other-project")
        assert config.LOG_DIR == log_before

    def test_none_resolves_to_env_default(self, tmp_data_dir):
        """None without env var falls back to 'default'."""
        with patch.dict("os.environ", {}, clear=False):
            # Remove the env var if set
            import os
            os.environ.pop("CONSOLIDATION_MEMORY_PROJECT", None)
            result = set_active_project(None)
        assert result == "default"
        assert get_active_project() == "default"

    def test_none_resolves_from_env_var(self, tmp_data_dir):
        """None with env var reads from CONSOLIDATION_MEMORY_PROJECT."""
        with patch.dict("os.environ", {"CONSOLIDATION_MEMORY_PROJECT": "from-env"}):
            result = set_active_project(None)
        assert result == "from-env"
        assert get_active_project() == "from-env"

    def test_invalid_name_raises(self, tmp_data_dir):
        """Invalid project names must raise ValueError."""
        with pytest.raises(ValueError):
            set_active_project("INVALID")
        with pytest.raises(ValueError):
            set_active_project("")
        with pytest.raises(ValueError):
            set_active_project("../escape")
