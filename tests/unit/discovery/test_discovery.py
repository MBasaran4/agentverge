"""Unit tests for the project discovery subsystem."""

import os
from pathlib import Path

import pytest

from agentverge.discovery.detector import (
    ProjectDiscoveryError,
    discover_project,
)
from agentverge.models.config import AgentVergeConfig


def test_valid_project_path(tmp_path: Path) -> None:
    """Verify discovery succeeds on a valid directory."""
    (tmp_path / "main.py").write_text("print('hello')", encoding="utf-8")
    context = discover_project(tmp_path)

    assert context.root_path == tmp_path.resolve()
    assert context.structure.is_python_project is True
    assert context.candidate_files_count == 1
    assert context.discovered_at.tzinfo is not None


def test_invalid_project_path_nonexistent(tmp_path: Path) -> None:
    """Verify discovery raises ProjectDiscoveryError on non-existent path."""
    nonexistent = tmp_path / "does_not_exist"
    with pytest.raises(ProjectDiscoveryError, match="does not exist"):
        discover_project(nonexistent)


def test_invalid_project_path_is_file(tmp_path: Path) -> None:
    """Verify discovery raises ProjectDiscoveryError when target is a file."""
    regular_file = tmp_path / "file.txt"
    regular_file.write_text("sample", encoding="utf-8")
    with pytest.raises(ProjectDiscoveryError, match="not a directory"):
        discover_project(regular_file)


def test_git_directory_detection(tmp_path: Path) -> None:
    """Verify .git directory is detected as a Git repository."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    context = discover_project(tmp_path)
    assert context.structure.is_git_repo is True


def test_git_worktree_file_detection(tmp_path: Path) -> None:
    """Verify .git file (e.g. in Git worktrees/submodules) is detected as a Git repository."""
    git_file = tmp_path / ".git"
    git_file.write_text("gitdir: /path/to/parent/gitdir", encoding="utf-8")
    context = discover_project(tmp_path)
    assert context.structure.is_git_repo is True


def test_no_git_detection(tmp_path: Path) -> None:
    """Verify non-git directory reports is_git_repo as False."""
    context = discover_project(tmp_path)
    assert context.structure.is_git_repo is False


def test_python_markers_and_package_managers(tmp_path: Path) -> None:
    """Verify detection of Python project markers and package managers."""
    (tmp_path / "pyproject.toml").write_text(
        """
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
""",
        encoding="utf-8",
    )
    (tmp_path / "poetry.lock").write_text("", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text("pydantic>=2.0\n", encoding="utf-8")

    context = discover_project(tmp_path)

    assert context.structure.is_python_project is True
    assert "pyproject.toml" in context.structure.project_files
    assert "requirements.txt" in context.structure.project_files
    assert "hatch" in context.structure.package_managers
    assert "poetry" in context.structure.package_managers
    assert "pip" in context.structure.package_managers


def test_ai_instruction_files_detection(tmp_path: Path) -> None:
    """Verify discovery of AI instruction and agent rule files."""
    (tmp_path / "AGENTS.md").write_text("# Developer rules", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text("# Claude rules", encoding="utf-8")
    (tmp_path / ".cursorrules").write_text("# Cursor rules", encoding="utf-8")

    github_dir = tmp_path / ".github"
    github_dir.mkdir()
    (github_dir / "copilot-instructions.md").write_text("# Copilot rules", encoding="utf-8")

    context = discover_project(tmp_path)

    instructions = context.agent_context.instruction_files
    assert "AGENTS.md" in instructions
    assert "CLAUDE.md" in instructions
    assert ".cursorrules" in instructions
    assert ".github/copilot-instructions.md" in instructions


def test_mcp_config_detection(tmp_path: Path) -> None:
    """Verify discovery of MCP configuration files and JSON validity counting."""
    (tmp_path / ".mcp.json").write_text('{"mcpServers": {"test": {}}}', encoding="utf-8")
    (tmp_path / "claude_desktop_config.json").write_text("INVALID JSON", encoding="utf-8")

    context = discover_project(tmp_path)

    assert ".mcp.json" in context.mcp_context.config_files
    assert "claude_desktop_config.json" in context.mcp_context.config_files
    # Only .mcp.json is valid JSON
    assert context.mcp_context.valid_configs_count == 1


def test_github_workflows_detection(tmp_path: Path) -> None:
    """Verify discovery of GitHub Actions workflow files."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI", encoding="utf-8")
    (workflows / "release.yaml").write_text("name: Release", encoding="utf-8")
    (workflows / "readme.txt").write_text("not a workflow", encoding="utf-8")

    context = discover_project(tmp_path)

    assert context.structure.has_github_workflows is True
    assert ".github/workflows/ci.yml" in context.structure.workflow_files
    assert ".github/workflows/release.yaml" in context.structure.workflow_files
    assert len(context.structure.workflow_files) == 2


def test_candidate_files_count_and_excludes(tmp_path: Path) -> None:
    """Verify candidate file counting respects exclude patterns."""
    (tmp_path / "app.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "README.md").write_text("docs", encoding="utf-8")

    # Excluded directories
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "lib.py").write_text("x = 2", encoding="utf-8")

    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("git config", encoding="utf-8")

    config = AgentVergeConfig(exclude_patterns=[".venv", ".git"])
    context = discover_project(tmp_path, config=config)

    # Only app.py and README.md should be counted
    assert context.candidate_files_count == 2


def test_symlink_escape_protection(tmp_path: Path) -> None:
    """Verify symlinks pointing outside the project root are ignored."""
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    secret_file = outside_dir / "secret.txt"
    secret_file.write_text("super_secret", encoding="utf-8")

    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "safe.py").write_text("safe = True", encoding="utf-8")

    link_path = project_dir / "outside_link"
    try:
        os.symlink(outside_dir, link_path)
    except (OSError, NotImplementedError):
        pytest.skip("Symlink creation not supported or not permitted on this environment.")

    context = discover_project(project_dir)
    # Only safe.py should be counted; the out-of-bounds symlink is skipped
    assert context.candidate_files_count == 1


def test_symlink_escape_protection_logic(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that entries resolving outside root_path are strictly skipped."""
    (tmp_path / "safe.py").write_text("safe = True", encoding="utf-8")

    fake_symlink = tmp_path / "evil_symlink"
    fake_symlink.write_text("dummy", encoding="utf-8")

    outside_path = Path("C:/Windows/System32") if os.name == "nt" else Path("/etc")

    original_resolve = Path.resolve

    def mock_resolve(self: Path) -> Path:
        if self.name == "evil_symlink":
            return outside_path
        return original_resolve(self)

    monkeypatch.setattr(Path, "resolve", mock_resolve)

    context = discover_project(tmp_path)
    assert context.candidate_files_count == 1


def test_windows_path_handling_posix_normalization(tmp_path: Path) -> None:
    """Verify relative paths are always formatted as POSIX strings with forward slashes."""
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "check.yml").write_text("name: Check", encoding="utf-8")

    github = tmp_path / ".github"
    (github / "copilot-instructions.md").write_text("instructions", encoding="utf-8")

    context = discover_project(tmp_path)

    for wf in context.structure.workflow_files:
        assert "\\" not in wf
        assert "/" in wf

    for instruction in context.agent_context.instruction_files:
        assert "\\" not in instruction


def test_candidate_files_population(tmp_path: Path) -> None:
    """Verify discover_project populates candidate_files and target_files."""
    file1 = tmp_path / "a.py"
    file1.write_text("x = 1", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    file2 = sub / "b.json"
    file2.write_text("{}", encoding="utf-8")

    context = discover_project(tmp_path)

    assert context.candidate_files_count == 2
    assert len(context.candidate_files) == 2
    assert context.target_files == context.candidate_files
    assert all(p.is_absolute() for p in context.candidate_files)
    assert file1.resolve() in context.candidate_files
    assert file2.resolve() in context.candidate_files
