# Environment Variable Config Overrides — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Allow every scalar Config field to be overridden via `CONSOLIDATION_MEMORY_<FIELD>` environment variables, so Docker/CI users can configure without a TOML file.

**Architecture:** Add `_apply_env_overrides(config)` in `config.py` that loops over `dataclasses.fields(Config)`, checks `os.environ` for `CONSOLIDATION_MEMORY_<field.name>`, and casts to the field's type. Called inside `_build_config()` after TOML construction but before `overrides` kwargs. Priority: defaults < TOML < env vars < reset_config() overrides.

**Tech Stack:** Python dataclasses, os.environ, existing config.py infrastructure.

---

### Task 1: Add `_apply_env_overrides()` to config.py

**Files:**
- Modify: `src/consolidation_memory/config.py:235-348` (`_build_config` and surrounding area)

**Step 1: Write the failing test**

Add a new test class `TestEnvVarOverrides` in `tests/test_core.py` after the existing `TestConfigDefaults` class (around line 1218).

```python
class TestEnvVarOverrides:
    """Env vars with CONSOLIDATION_MEMORY_ prefix override TOML values."""

    def test_string_override(self, monkeypatch, tmp_data_dir):
        monkeypatch.setenv("CONSOLIDATION_MEMORY_EMBEDDING_BACKEND", "lmstudio")
        from consolidation_memory.config import reset_config, get_config
        cfg = reset_config(
            _base_data_dir=tmp_data_dir / "data",
            EMBEDDING_DIMENSION=384,
        )
        # reset_config uses empty TOML + overrides, but _apply_env_overrides
        # should NOT run for reset_config (tests must be isolated).
        # So test via _build_config with load_env=True:
        from consolidation_memory.config import _build_config
        cfg = _build_config({}, _load_env=True)
        assert cfg.EMBEDDING_BACKEND == "lmstudio"

    def test_int_override(self, monkeypatch):
        monkeypatch.setenv("CONSOLIDATION_MEMORY_LLM_MAX_TOKENS", "4096")
        from consolidation_memory.config import _build_config
        cfg = _build_config({}, _load_env=True)
        assert cfg.LLM_MAX_TOKENS == 4096

    def test_float_override(self, monkeypatch):
        monkeypatch.setenv("CONSOLIDATION_MEMORY_LLM_TEMPERATURE", "0.7")
        from consolidation_memory.config import _build_config
        cfg = _build_config({}, _load_env=True)
        assert cfg.LLM_TEMPERATURE == 0.7

    def test_bool_true_variants(self, monkeypatch):
        for val in ("1", "true", "True", "yes", "YES"):
            monkeypatch.setenv("CONSOLIDATION_MEMORY_CONSOLIDATION_PRUNE_ENABLED", val)
            from consolidation_memory.config import _build_config
            cfg = _build_config({}, _load_env=True)
            assert cfg.CONSOLIDATION_PRUNE_ENABLED is True, f"Failed for {val!r}"

    def test_bool_false_variants(self, monkeypatch):
        for val in ("0", "false", "False", "no", "NO"):
            monkeypatch.setenv("CONSOLIDATION_MEMORY_CONSOLIDATION_PRUNE_ENABLED", val)
            from consolidation_memory.config import _build_config
            cfg = _build_config({}, _load_env=True)
            assert cfg.CONSOLIDATION_PRUNE_ENABLED is False, f"Failed for {val!r}"

    def test_data_dir_override(self, monkeypatch, tmp_path):
        custom_dir = tmp_path / "custom_data"
        custom_dir.mkdir()
        monkeypatch.setenv("CONSOLIDATION_MEMORY_DATA_DIR", str(custom_dir))
        from consolidation_memory.config import _build_config
        cfg = _build_config({}, _load_env=True)
        assert cfg._base_data_dir == custom_dir

    def test_env_overrides_toml(self, monkeypatch):
        """Env var wins over TOML value."""
        monkeypatch.setenv("CONSOLIDATION_MEMORY_LLM_MODEL", "gpt-4")
        toml = {"llm": {"model": "qwen2.5-7b-instruct"}}
        from consolidation_memory.config import _build_config
        cfg = _build_config(toml, _load_env=True)
        assert cfg.LLM_MODEL == "gpt-4"

    def test_reset_config_ignores_env(self, monkeypatch):
        """reset_config() must not pick up env vars (test isolation)."""
        monkeypatch.setenv("CONSOLIDATION_MEMORY_LLM_MODEL", "gpt-4")
        from consolidation_memory.config import reset_config
        cfg = reset_config()
        assert cfg.LLM_MODEL == "qwen2.5-7b-instruct"  # default, not env

    def test_unknown_env_var_ignored(self, monkeypatch):
        """Env vars that don't match a field are silently ignored."""
        monkeypatch.setenv("CONSOLIDATION_MEMORY_NONEXISTENT_FIELD", "value")
        from consolidation_memory.config import _build_config
        cfg = _build_config({}, _load_env=True)  # should not raise
        assert not hasattr(cfg, "NONEXISTENT_FIELD")

    def test_complex_fields_skipped(self, monkeypatch):
        """frozenset and dict fields are not overridable via env."""
        monkeypatch.setenv("CONSOLIDATION_MEMORY_CONSOLIDATION_STOPWORDS", "foo,bar")
        from consolidation_memory.config import _build_config
        cfg = _build_config({}, _load_env=True)
        # Should still have the default stopwords, not "foo,bar"
        assert "the" in cfg.CONSOLIDATION_STOPWORDS

    def test_invalid_int_raises(self, monkeypatch):
        monkeypatch.setenv("CONSOLIDATION_MEMORY_LLM_MAX_TOKENS", "not_a_number")
        from consolidation_memory.config import _build_config
        import pytest
        with pytest.raises(ValueError, match="CONSOLIDATION_MEMORY_LLM_MAX_TOKENS"):
            _build_config({}, _load_env=True)
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_core.py::TestEnvVarOverrides -v`
Expected: FAIL — `_build_config()` does not accept `_load_env` parameter.

**Step 3: Implement `_apply_env_overrides()` and update `_build_config()`**

In `src/consolidation_memory/config.py`, add the following:

1. Add constant after `_KNOWN_LLM_BACKENDS`:

```python
_ENV_PREFIX = "CONSOLIDATION_MEMORY_"

# Types eligible for env var override (primitives only)
_ENV_COERCIBLE_TYPES = (str, int, float, bool)
```

2. Add `_apply_env_overrides()` function before `_build_config()`:

```python
def _apply_env_overrides(c: Config) -> None:
    """Override Config fields from CONSOLIDATION_MEMORY_* env vars.

    Handles str, int, float, bool fields.  Skips private fields (``_``
    prefix), Path fields, and complex types (frozenset, dict).

    Special case: ``CONSOLIDATION_MEMORY_DATA_DIR`` sets ``_base_data_dir``.
    """
    import dataclasses as _dc

    # Special: DATA_DIR -> _base_data_dir (not a regular field loop candidate)
    data_dir_env = os.environ.get(f"{_ENV_PREFIX}DATA_DIR")
    if data_dir_env:
        c._base_data_dir = Path(data_dir_env).expanduser().resolve()

    for f in _dc.fields(c):
        if f.name.startswith("_"):
            continue
        if f.name == "active_project":
            continue  # handled by CONSOLIDATION_MEMORY_PROJECT

        env_key = f"{_ENV_PREFIX}{f.name}"
        env_val = os.environ.get(env_key)
        if env_val is None:
            continue

        # Resolve the actual type (strip Optional, etc.)
        field_type = type(getattr(c, f.name))

        if field_type not in _ENV_COERCIBLE_TYPES:
            continue  # skip Path, frozenset, dict, etc.

        try:
            if field_type is bool:
                coerced = env_val.lower() in ("1", "true", "yes")
            else:
                coerced = field_type(env_val)
        except (ValueError, TypeError) as exc:
            raise ValueError(
                f"{env_key}={env_val!r}: cannot convert to "
                f"{field_type.__name__}: {exc}"
            ) from exc

        object.__setattr__(c, f.name, coerced)
```

3. Update `_build_config()` signature and body — add `_load_env: bool = False` parameter:

```python
def _build_config(toml: dict | None = None, *, _load_env: bool = False, **overrides: object) -> Config:
```

After constructing `c = Config(...)` and before the `overrides` loop, add:

```python
    if _load_env:
        _apply_env_overrides(c)
```

4. Update `get_config()` to pass `_load_env=True`:

```python
    _config_instance = _build_config(toml, _load_env=True)
```

5. `reset_config()` stays as-is — it already passes `_load_env=False` by default, so tests remain isolated.

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_core.py::TestEnvVarOverrides -v`
Expected: All 11 tests PASS.

**Step 5: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS. The autouse `tmp_data_dir` fixture calls `reset_config()` which doesn't load env vars, so existing tests are unaffected.

**Step 6: Run linter**

Run: `ruff check src/consolidation_memory/config.py tests/test_core.py`
Expected: Clean.

**Step 7: Commit**

```bash
git add src/consolidation_memory/config.py tests/test_core.py
git commit -m "feat: add CONSOLIDATION_MEMORY_* env var overrides for all config fields"
```

---

### Task 2: Document env vars in README

**Files:**
- Modify: `README.md:248` (after the `</details>` closing the manual configuration section)

**Step 1: Add environment variables section**

Insert the following after line 248 (`</details>`) and before `## CLI`:

```markdown

<details>
<summary>Environment variable overrides</summary>

Every config setting can be overridden with an environment variable. The naming convention is `CONSOLIDATION_MEMORY_<FIELD_NAME>`:

```bash
# Embedding
CONSOLIDATION_MEMORY_EMBEDDING_BACKEND=lmstudio
CONSOLIDATION_MEMORY_EMBEDDING_MODEL_NAME=text-embedding-nomic-embed-text-v1.5
CONSOLIDATION_MEMORY_EMBEDDING_DIMENSION=768
CONSOLIDATION_MEMORY_EMBEDDING_API_BASE=http://localhost:1234/v1
CONSOLIDATION_MEMORY_EMBEDDING_API_KEY=sk-...

# LLM
CONSOLIDATION_MEMORY_LLM_BACKEND=openai
CONSOLIDATION_MEMORY_LLM_API_BASE=https://api.openai.com/v1
CONSOLIDATION_MEMORY_LLM_MODEL=gpt-4o-mini
CONSOLIDATION_MEMORY_LLM_API_KEY=sk-...

# Data directory
CONSOLIDATION_MEMORY_DATA_DIR=/data/consolidation-memory

# Consolidation
CONSOLIDATION_MEMORY_CONSOLIDATION_INTERVAL_HOURS=12
CONSOLIDATION_MEMORY_CONSOLIDATION_AUTO_RUN=false
```

**Priority:** defaults < TOML file < environment variables < `reset_config()` (tests).

**Type coercion:** Strings are used as-is. Integers and floats are parsed. Booleans accept `1/true/yes` (true) and `0/false/no` (false). Complex types (frozenset, dict) cannot be set via env vars.

**Docker example:**

```bash
docker run -e CONSOLIDATION_MEMORY_EMBEDDING_BACKEND=openai \
           -e CONSOLIDATION_MEMORY_EMBEDDING_API_KEY=sk-... \
           -e CONSOLIDATION_MEMORY_LLM_BACKEND=openai \
           -e CONSOLIDATION_MEMORY_LLM_API_KEY=sk-... \
           -e CONSOLIDATION_MEMORY_DATA_DIR=/data \
           consolidation-memory serve
```

**CI example (GitHub Actions):**

```yaml
env:
  CONSOLIDATION_MEMORY_EMBEDDING_BACKEND: fastembed
  CONSOLIDATION_MEMORY_LLM_BACKEND: disabled
  CONSOLIDATION_MEMORY_CONSOLIDATION_AUTO_RUN: "false"
```

</details>
```

**Step 2: Verify README renders correctly**

Skim the README diff to ensure markdown formatting is correct.

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document CONSOLIDATION_MEMORY_* env var overrides"
```

---

### Task 3: Final verification

**Step 1: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS.

**Step 2: Run linter on all modified files**

Run: `ruff check src/ tests/`
Expected: Clean.

**Step 3: Manual smoke test**

```bash
CONSOLIDATION_MEMORY_LLM_BACKEND=disabled CONSOLIDATION_MEMORY_EMBEDDING_BACKEND=fastembed consolidation-memory status
```

Expected: Status output shows `LLM backend: disabled`, `Embedding backend: fastembed`.
