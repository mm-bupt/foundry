import asyncio
import json as _json
import os
import subprocess
from pathlib import Path

from pydantic_ai import Agent, RunContext
from foundry_app.agent.deps import AgentDeps
from foundry_app.logger import get_logger

logger = get_logger("agent.tools")


def _utf8_env() -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["LANG"] = "en_US.UTF-8"
    env["LC_ALL"] = "en_US.UTF-8"
    return env


def register_file_tools(agent: Agent):
    @agent.tool
    async def read_file(ctx: RunContext[AgentDeps], path: str) -> str:
        """Read the content of a file. Relative paths are resolved against the working directory.

        Args:
            path: File path (relative or absolute).
        """
        try:
            logger.debug("tool exec: read_file | path=%s", path)
            target = _resolve_path(ctx.deps.work_dir, path)
            if not target.is_file():
                return f"Error: '{path}' is not a file or does not exist."
            content = target.read_text(encoding="utf-8", errors="replace")
            return content
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error reading file: {e}"

    @agent.tool
    async def write_file(ctx: RunContext[AgentDeps], path: str, content: str) -> str:
        """Write content to a file. Relative paths are resolved against the working directory.
        Creates parent directories if needed.

        Args:
            path: File path (relative or absolute).
            content: Content to write.
        """
        try:
            logger.debug("tool exec: write_file | path=%s content_len=%d", path, len(content))
            target = _resolve_path(ctx.deps.work_dir, path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return f"Successfully wrote {len(content)} chars to '{path}'."
        except PermissionError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Error writing file: {e}"

    @agent.tool
    async def run_command(
        ctx: RunContext[AgentDeps], command: str, timeout: int = 120
    ) -> str:
        """Execute a shell command in the working directory.

        Args:
            command: The shell command to run.
            timeout: Timeout in seconds (default 120).
        """
        try:
            logger.debug("tool exec: run_command | cmd=%s timeout=%d", command, timeout)
            proc = await asyncio.to_thread(
                subprocess.run,
                command,
                shell=True,
                capture_output=True,
                cwd=ctx.deps.work_dir,
                timeout=timeout,
                env=_utf8_env(),
                encoding="utf-8",
                errors="replace",
            )
            output = ""
            if proc.stdout:
                output += proc.stdout
            if proc.stderr:
                output += proc.stderr
            if proc.returncode != 0:
                output += f"\n(exit code: {proc.returncode})"
            return output or "(no output)"
        except asyncio.TimeoutError:
            return f"Error: command timed out after {timeout}s."
        except Exception as e:
            return f"Error running command: {e}"


def register_search_tools(agent: Agent):
    """Register file search tools (glob, grep). Requires ripgrep."""

    _RG_INSTALL_HINT = (
        "Error: ripgrep (rg) is not installed.\n"
        "Install with:\n"
        "  Windows: winget install BurntSushi.ripgrep\n"
        "  macOS:   brew install ripgrep\n"
        "  Linux:   apt install ripgrep / pacman -S ripgrep\n"
        "  Or visit: https://github.com/BurntSushi/ripgrep"
    )

    @agent.tool
    async def glob(ctx: RunContext[AgentDeps], pattern: str, path: str = "") -> str:
        """Fast file pattern matching tool that works with any codebase size.
        Supports glob patterns like "**/*.py" or "src/**/*.ts".
        Returns matching file paths sorted by modification time (newest first).

        Args:
            pattern: The glob pattern to match files against (e.g. "**/*.js").
            path: The directory to search in. Defaults to working directory.
        """
        try:
            logger.debug("tool exec: glob | pattern=%s path=%s", pattern, path)
            search_dir = _resolve_path(ctx.deps.work_dir, path) if path else Path(ctx.deps.work_dir).resolve()
            if not search_dir.is_dir():
                return f"Error: '{path}' is not a directory."

            args = [
                "rg", "--no-config", "--files",
                "--glob=!.git/*", f"--glob={pattern}", ".",
            ]
            proc = await asyncio.to_thread(
                subprocess.run,
                args,
                capture_output=True,
                cwd=str(search_dir),
                timeout=30,
                env=_utf8_env(),
                encoding="utf-8",
                errors="replace",
            )

            if proc.returncode == 2:
                return f"Error: ripgrep failed — {proc.stderr}"

            raw = proc.stdout.strip()
            lines = raw.split("\n") if raw else []
            logger.debug("glob result | rc=%d raw_len=%d lines=%d cwd=%s", proc.returncode, len(raw), len(lines), str(search_dir))
            if not lines:
                return "No files found"

            limit = 100
            files = []
            for line in lines:
                full = search_dir / line
                try:
                    mtime = full.stat().st_mtime
                    files.append((str(full), mtime))
                except OSError:
                    continue

            files.sort(key=lambda x: x[1], reverse=True)
            truncated = len(files) > limit
            files = files[:limit]

            result = "\n".join(f[0] for f in files)
            if truncated:
                result += "\n(Results are truncated. Consider using a more specific path or pattern.)"
            return result
        except FileNotFoundError:
            logger.debug("glob error: rg not found (FileNotFoundError)")
            return _RG_INSTALL_HINT
        except asyncio.TimeoutError:
            return "Error: glob search timed out."
        except Exception as e:
            logger.debug("glob error: %s: %s", type(e).__name__, repr(e))
            return f"Error: {e}"

    @agent.tool
    async def grep(
        ctx: RunContext[AgentDeps],
        pattern: str,
        path: str = "",
        include: str = "",
    ) -> str:
        """Fast content search tool that works with any codebase size.
        Searches file contents using regular expressions.
        Filter files by pattern with the include parameter.

        Args:
            pattern: The regex pattern to search for in file contents.
            path: The directory to search in. Defaults to working directory.
            include: File pattern to include (e.g. "*.py", "*.{ts,tsx}").
        """
        try:
            logger.debug("tool exec: grep | pattern=%s path=%s include=%s", pattern, path, include)
            search_dir = _resolve_path(ctx.deps.work_dir, path) if path else Path(ctx.deps.work_dir).resolve()
            if not search_dir.is_dir():
                return f"Error: '{path}' is not a directory."

            args = [
                "rg", "--no-config", "--json", "--hidden",
                "--glob=!.git/*", "--no-messages",
            ]
            if include:
                args.append(f"--glob={include}")
            args.extend(["--", pattern, "."])

            proc = await asyncio.to_thread(
                subprocess.run,
                args,
                capture_output=True,
                cwd=str(search_dir),
                timeout=30,
                env=_utf8_env(),
                encoding="utf-8",
                errors="replace",
            )

            if not proc.stdout.strip():
                return "No files found"

            file_matches: dict[str, list[tuple[int, str]]] = {}
            for line in proc.stdout.strip().split("\n"):
                try:
                    data = _json.loads(line)
                    if data.get("type") != "match":
                        continue
                    d = data["data"]
                    filepath = str(search_dir / d["path"]["text"])
                    ln = d["line_number"]
                    text = d["lines"]["text"].rstrip("\n")
                    if len(text) > 2000:
                        text = text[:2000] + "..."
                    file_matches.setdefault(filepath, []).append((ln, text))
                except (_json.JSONDecodeError, KeyError):
                    continue

            if not file_matches:
                return "No files found"

            sorted_files = sorted(
                file_matches.items(),
                key=lambda x: Path(x[0]).stat().st_mtime if Path(x[0]).exists() else 0,
                reverse=True,
            )

            total = sum(len(v) for _, v in sorted_files)
            limit = 100
            truncated = total > limit

            parts: list[str] = []
            count = 0
            for filepath, matches in sorted_files:
                parts.append(f"\n{filepath}:")
                for ln, text in matches:
                    if count >= limit:
                        break
                    parts.append(f"  Line {ln}: {text}")
                    count += 1
                if count >= limit:
                    break

            if truncated:
                parts.append(
                    f"\n(Results are truncated: showing first {limit} matches. "
                    "Consider using a more specific path or pattern.)"
                )

            return f"Found {total} matches\n" + "\n".join(parts)
        except FileNotFoundError:
            logger.debug("grep error: rg not found (FileNotFoundError)")
            return _RG_INSTALL_HINT
        except asyncio.TimeoutError:
            return "Error: grep search timed out."
        except Exception as e:
            logger.debug("grep error: %s: %s", type(e).__name__, repr(e))
            return f"Error: {e}"


def register_skill_tools(agent: Agent):
    """Register skill loading tool."""

    @agent.tool
    async def skill(ctx: RunContext[AgentDeps], name: str) -> str:
        """Load a specialized skill when the task at hand matches one of the skills listed in the system prompt.
        Use this tool to inject the skill's instructions and resources into current conversation.
        The output may contain detailed workflow guidance as well as references to scripts, files, etc
        in the same directory as the skill.
        The skill name must match one of the skills listed in your system prompt.

        Args:
            name: The name of the skill from available_skills.
        """
        try:
            from foundry_app.agent.system_prompt import _scan_skills

            skills = _scan_skills(ctx.deps.work_dir)
            matched = None
            for s in skills:
                if s["name"] == name:
                    matched = s
                    break

            if matched is None:
                available = ", ".join(s["name"] for s in skills) if skills else "none"
                return (
                    f'Error: Skill "{name}" not found. '
                    f"Available skills: {available}"
                )

            location = matched["location"]
            if location.startswith("file:///"):
                from urllib.parse import unquote as _unquote
                skill_path = Path(_unquote(location[7:]))
            else:
                skill_path = Path(location)

            if not skill_path.is_file():
                return f"Error: Skill file not found at {skill_path}"

            content = skill_path.read_text(encoding="utf-8", errors="replace")
            body = _strip_frontmatter(content)
            skill_dir = skill_path.parent

            files = _list_skill_files(skill_dir)

            base_uri = skill_dir.as_uri()
            parts = [
                f'<skill_content name="{name}">',
                f"# Skill: {name}",
                "",
                body.strip(),
                "",
                f"Base directory for this skill: {base_uri}",
                "Relative paths in this skill (e.g., scripts/, reference/) are relative to this base directory.",
                "Note: file list is sampled.",
                "",
                "<skill_files>",
            ]
            parts.extend(f"<file>{f}</file>" for f in files)
            parts.append("</skill_files>")
            parts.append("</skill_content>")

            return "\n".join(parts)
        except Exception as e:
            return f"Error loading skill: {e}"


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---"):
        return text
    end = text.find("---", 3)
    if end == -1:
        return text
    return text[end + 3:].strip()


def _list_skill_files(skill_dir: Path, limit: int = 10) -> list[str]:
    files: list[str] = []
    try:
        for child in sorted(skill_dir.rglob("*")):
            if child.is_file() and child.name != "SKILL.md":
                files.append(str(child))
                if len(files) >= limit:
                    break
    except Exception:
        pass
    return files


def _resolve_path(work_dir: str, path: str) -> Path:
    base = Path(work_dir).resolve()
    target = (base / path).resolve() if not Path(path).is_absolute() else Path(path).resolve()
    if not str(target).startswith(str(base)):
        raise PermissionError(f"Path '{path}' is outside working directory")
    return target
