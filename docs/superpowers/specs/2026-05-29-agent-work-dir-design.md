# Agent Work Directory (work_dir) Design

## Summary

Add a configurable working directory for the Dream Foundry agent. All file operation tools (read, write, list, run command) will resolve relative paths against this directory. The work directory is a global setting (not per-session).

## Configuration Priority (highest to lowest)

1. **CLI argument**: `--work-dir /path/to/project`
2. **Environment variable**: `DREAM_FOUNDRY_WORK_DIR=/path/to/project`
3. **YAML config**: `workDir: /path/to/project` in `~/.config/foundry/config.yaml`
4. **Default**: `os.getcwd()` (current process working directory)

## Changes

### 1. `config.py` — New setting

Add `work_dir: Path` field with default `Path.cwd()`. After `Settings` is constructed, resolve the value to an absolute path.

### 2. `yaml_config.py` — Parse `workDir`

Add `work_dir: str` to `FoundryConfig`. Parse `workDir` from YAML top-level key. Apply to `settings.work_dir` in the existing config merge block.

### 3. `__main__.py` — CLI argument

Parse `--work-dir` argument via `argparse` before starting uvicorn. Set `settings.work_dir` if provided.

### 4. `agent/core.py` — Inject work_dir into deps and prompt

- Add `work_dir: str` to `AgentDeps` dataclass
- Append work_dir info to system prompt: `Your working directory is: {work_dir}`
- Pass `settings.work_dir` when creating `AgentDeps` in `stream_chat()`

### 5. `agent/tools.py` — New file operation tools

Add tools that operate relative to `work_dir`:

- **`read_file(path: str)`** — Read file content. Relative paths resolved against `work_dir`.
- **`write_file(path: str, content: str)`** — Write content to file.
- **`list_files(path: str = ".")`** — List directory contents.
- **`run_command(command: str)`** — Execute shell command with `cwd=work_dir`.

All paths are resolved to absolute and validated to be within `work_dir` (prevent path traversal). Errors returned as descriptive strings.

### 6. `api/sessions.py` — New endpoint

Add `GET /api/config` returning `{"work_dir": str}` so TUI/frontend can display the current working directory.

## Path Safety

Every file operation tool must:

1. Resolve the input path: `work_dir / path` (for relative) or `Path(path)` (for absolute)
2. Call `.resolve()` to eliminate `..` components
3. Verify `resolved_path.is_relative_to(work_dir.resolve())`
4. Reject with clear error message if outside work_dir

## Open Questions

None — design is complete.
