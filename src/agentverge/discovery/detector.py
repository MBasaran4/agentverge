"""Passive filesystem discovery for project repositories."""

import contextlib
import fnmatch
import json
import tomllib
from datetime import UTC, datetime
from pathlib import Path

from agentverge.models.config import AgentVergeConfig
from agentverge.models.context import (
    AgentContext,
    McpContext,
    ProjectContext,
    ProjectStructure,
)


class ProjectDiscoveryError(Exception):
    """Raised when project discovery fails due to invalid paths or inaccessible directories."""


AI_INSTRUCTION_CANDIDATES: tuple[str, ...] = (
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".cursorrules",
    ".windsurfrules",
    ".github/copilot-instructions.md",
)

MCP_CONFIG_CANDIDATES: tuple[str, ...] = (
    ".mcp.json",
    "mcp.json",
    "claude_desktop_config.json",
    ".cursor/mcp.json",
    ".vscode/mcp.json",
)

PYTHON_MARKER_FILES: tuple[str, ...] = (
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "Pipfile",
    "Pipfile.lock",
    "poetry.lock",
    "uv.lock",
    "pdm.lock",
)

MAX_INSPECTION_FILE_SIZE_BYTES: int = 1_048_576  # 1 MB


def _detect_git_repo(root: Path) -> bool:
    """Passively detect if the target directory is a Git repository or worktree.

    Does not execute git CLI or any subprocess.
    """
    git_path = root / ".git"
    return git_path.exists()


def _detect_package_managers(root: Path, project_files: list[str]) -> list[str]:
    """Identify package managers based on project configuration files."""
    managers: list[str] = []

    if "poetry.lock" in project_files:
        managers.append("poetry")
    if "uv.lock" in project_files:
        managers.append("uv")
    if "pdm.lock" in project_files:
        managers.append("pdm")
    if "Pipfile" in project_files or "Pipfile.lock" in project_files:
        managers.append("pipenv")
    if "requirements.txt" in project_files and "pip" not in managers:
        managers.append("pip")
    if (
        "setup.py" in project_files or "setup.cfg" in project_files
    ) and "setuptools" not in managers:
        managers.append("setuptools")

    # Inspect pyproject.toml build-system and tools if present
    pyproject_path = root / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            if pyproject_path.stat().st_size <= MAX_INSPECTION_FILE_SIZE_BYTES:
                content = pyproject_path.read_text(encoding="utf-8")
                parsed = tomllib.loads(content)

                build_backend = parsed.get("build-system", {}).get("build-backend", "")
                if "hatchling" in build_backend and "hatch" not in managers:
                    managers.append("hatch")
                if "flit" in build_backend and "flit" not in managers:
                    managers.append("flit")
                if "poetry" in build_backend and "poetry" not in managers:
                    managers.append("poetry")

                tool_section = parsed.get("tool", {})
                if isinstance(tool_section, dict):
                    if "poetry" in tool_section and "poetry" not in managers:
                        managers.append("poetry")
                    if "pdm" in tool_section and "pdm" not in managers:
                        managers.append("pdm")
                    if "uv" in tool_section and "uv" not in managers:
                        managers.append("uv")
        except Exception:
            # Inspection failure on malformed pyproject should not break discovery
            pass

    return managers


def _detect_workflows(root: Path) -> list[str]:
    """Find GitHub Actions workflow files."""
    workflows_dir = root / ".github" / "workflows"
    if not workflows_dir.is_dir():
        return []

    workflow_files: list[str] = []
    try:
        for entry in sorted(workflows_dir.iterdir()):
            if entry.is_file() and entry.suffix.lower() in (".yml", ".yaml"):
                workflow_files.append(entry.relative_to(root).as_posix())
    except OSError:
        pass
    return workflow_files


def _detect_ai_instructions(root: Path) -> list[str]:
    """Find AI coding agent instruction files."""
    discovered: list[str] = []
    for candidate in AI_INSTRUCTION_CANDIDATES:
        target = root / candidate
        if target.is_file():
            discovered.append(target.relative_to(root).as_posix())

    # Check .agentverge rules / prompts directories if present
    agentverge_dir = root / ".agentverge"
    if agentverge_dir.is_dir():
        for sub in ("rules", "prompts"):
            sub_dir = agentverge_dir / sub
            if sub_dir.is_dir():
                discovered.append(sub_dir.relative_to(root).as_posix())

    return discovered


def _detect_mcp_configs(root: Path) -> tuple[list[str], int]:
    """Discover MCP configuration files and verify JSON validity without extracting secrets."""
    config_files: list[str] = []
    valid_count = 0

    for candidate in MCP_CONFIG_CANDIDATES:
        target = root / candidate
        if target.is_file():
            rel_path = target.relative_to(root).as_posix()
            config_files.append(rel_path)
            try:
                if target.stat().st_size <= MAX_INSPECTION_FILE_SIZE_BYTES:
                    raw = target.read_text(encoding="utf-8")
                    json.loads(raw)
                    valid_count += 1
            except Exception:
                # Malformed JSON or read error
                pass

    return config_files, valid_count


def _discover_candidate_files(root: Path, exclude_patterns: list[str]) -> list[Path]:
    """Safely discover candidate files, honoring excludes and preventing symlink escapes."""
    discovered: list[Path] = []
    resolved_root = root.resolve()

    # Recursively traverse directory
    def _walk_dir(current_dir: Path, visited_real_paths: set[Path]) -> None:
        try:
            entries = sorted(current_dir.iterdir(), key=lambda p: p.name)
        except OSError:
            return

        for entry in entries:
            name = entry.name

            # Check if name or relative path matches any exclude pattern
            try:
                rel_path = entry.relative_to(root).as_posix()
            except ValueError:
                continue

            should_exclude = any(
                fnmatch.fnmatch(name, pat) or fnmatch.fnmatch(rel_path, pat)
                for pat in exclude_patterns
            )
            if should_exclude:
                continue

            # Check symlink target to prevent path traversal / directory escapes
            try:
                resolved_entry = entry.resolve()
                if not resolved_entry.is_relative_to(resolved_root):
                    # Out of bounds symlink, ignore safely
                    continue
            except (OSError, ValueError):
                continue

            if entry.is_symlink() and resolved_entry in visited_real_paths:
                # Avoid symlink recursion loops
                continue

            if entry.is_file():
                discovered.append(resolved_entry)
            elif entry.is_dir():
                new_visited = visited_real_paths | {resolved_entry}
                _walk_dir(entry, new_visited)

    _walk_dir(root, {resolved_root})
    return discovered


def _count_candidate_files(root: Path, exclude_patterns: list[str]) -> int:
    """Safely count candidate files, honoring excludes and preventing symlink escapes."""
    return len(_discover_candidate_files(root, exclude_patterns))


def discover_project(
    target_path: Path | str,
    config: AgentVergeConfig | None = None,
    config_file_path: Path | None = None,
) -> ProjectContext:
    """Discover project characteristics, AI agent instructions, and MCP markers safely.

    Args:
        target_path: Path to target directory.
        config: Optional pre-loaded AgentVergeConfig.
        config_file_path: Optional path to the configuration file used.

    Returns:
        An immutable ProjectContext describing the target project.

    Raises:
        ProjectDiscoveryError: If the target path does not exist or is not a directory.
    """
    raw_path = Path(target_path)
    if not raw_path.exists():
        raise ProjectDiscoveryError(f"Target path '{target_path}' does not exist.")
    if not raw_path.is_dir():
        raise ProjectDiscoveryError(f"Target path '{target_path}' is not a directory.")

    root = raw_path.resolve()
    active_config = config or AgentVergeConfig()

    # 1. Detect Git repository
    is_git_repo = _detect_git_repo(root)

    # 2. Detect Project Markers & Package Managers
    project_files: list[str] = [
        marker for marker in PYTHON_MARKER_FILES if (root / marker).is_file()
    ]
    package_managers = _detect_package_managers(root, project_files)

    # Determine if Python project
    has_python_files = bool(project_files)
    if not has_python_files:
        with contextlib.suppress(OSError):
            has_python_files = any(root.glob("*.py"))

    # 3. Detect GitHub Workflows
    workflow_files = _detect_workflows(root)

    structure = ProjectStructure(
        root_path=root,
        is_git_repo=is_git_repo,
        is_python_project=has_python_files,
        package_managers=package_managers,
        project_files=project_files,
        has_github_workflows=bool(workflow_files),
        workflow_files=workflow_files,
    )

    # 4. Detect AI Agent Instructions
    instruction_files = _detect_ai_instructions(root)
    agent_context = AgentContext(
        instruction_files=instruction_files,
        agent_config_files=[],
    )

    # 5. Detect MCP configurations
    mcp_files, valid_mcp_count = _detect_mcp_configs(root)
    mcp_context = McpContext(
        config_files=mcp_files,
        valid_configs_count=valid_mcp_count,
    )

    # 6. Discover candidate files
    candidate_files = _discover_candidate_files(
        root,
        active_config.exclude_patterns,
    )

    return ProjectContext(
        root_path=root,
        structure=structure,
        agent_context=agent_context,
        mcp_context=mcp_context,
        config_file=config_file_path,
        candidate_files=candidate_files,
        candidate_files_count=len(candidate_files),
        discovered_at=datetime.now(UTC),
    )
