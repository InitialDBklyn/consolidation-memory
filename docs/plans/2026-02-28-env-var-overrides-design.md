# Environment Variable Overrides for Config

## Problem

Docker users and CI environments need to configure consolidation-memory without creating a TOML file. Currently only `CONSOLIDATION_MEMORY_CONFIG` (config path) and `CONSOLIDATION_MEMORY_PROJECT` (project name) are supported as env vars.

## Design

### Approach: Post-construction override loop in `_build_config()`

After building the Config from TOML, iterate over all `dataclasses.fields(Config)`, check `os.environ` for `CONSOLIDATION_MEMORY_<FIELD_NAME>`, and if present, cast to the field's type and override.

### Priority order

```
defaults < TOML file < environment variables < reset_config() overrides (tests)
```

### Env var naming

All env vars use prefix `CONSOLIDATION_MEMORY_` + the exact dataclass field name:

- `CONSOLIDATION_MEMORY_EMBEDDING_BACKEND=lmstudio`
- `CONSOLIDATION_MEMORY_LLM_API_BASE=http://host:1234/v1`
- `CONSOLIDATION_MEMORY_CONSOLIDATION_INTERVAL_HOURS=12`

### Type coercion

| Python type | Coercion rule |
|-------------|---------------|
| `str` | Used as-is |
| `int` | `int(value)` |
| `float` | `float(value)` |
| `bool` | `value.lower() in ("1", "true", "yes")` |
| `frozenset` | Skip (not practical as env var) |
| `dict` | Skip (not practical as env var) |
| `Path` | Skip (derived from `_base_data_dir`, not set directly) |
| `_base_data_dir` | Special-cased via `CONSOLIDATION_MEMORY_DATA_DIR` |

### Special cases

- **`_base_data_dir`**: Mapped from `CONSOLIDATION_MEMORY_DATA_DIR` (public name, not the internal `_base_data_dir` field name). Applied before `_recompute_paths()`.
- **Fields starting with `_`**: Skipped by the auto-loop.
- **`active_project`**: Already handled by `CONSOLIDATION_MEMORY_PROJECT`. Skipped.
- **Path fields** (`DATA_DIR`, `DB_PATH`, etc.): Derived from `_base_data_dir` via `_recompute_paths()`. Skipped — users set `CONSOLIDATION_MEMORY_DATA_DIR` instead.

### Implementation location

Single function `_apply_env_overrides(config: Config)` called inside `_build_config()`, after TOML construction, before `overrides` kwargs and `_recompute_paths()`.

### Changes

1. **`config.py`**: Add `_apply_env_overrides()`, call it in `_build_config()`, add `_ENV_PREFIX` constant.
2. **Tests**: Add tests for env var overrides (str, int, float, bool, unknown env var ignored, DATA_DIR special case, test overrides still win).
3. **README.md**: Add "Environment Variables" section documenting the pattern and listing key examples.
