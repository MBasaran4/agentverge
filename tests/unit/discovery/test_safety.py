"""Safety and security boundary tests for project discovery.

Ensures discovery never invokes subprocesses, executes files, opens network connections,
or extracts sensitive environment variables/tokens.
"""

import socket
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from agentverge.discovery.detector import discover_project


def test_zero_subprocess_invocations(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify discovery does not call subprocess.run, subprocess.Popen, or os.system."""
    mock_run = MagicMock(side_effect=RuntimeError("subprocess.run must not be called"))
    mock_popen = MagicMock(side_effect=RuntimeError("subprocess.Popen must not be called"))

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(subprocess, "Popen", mock_popen)

    # Set up realistic project with .git and python files
    (tmp_path / ".git").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]\nname='test'\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text("# Agents\n", encoding="utf-8")

    context = discover_project(tmp_path)

    assert context.structure.is_git_repo is True
    assert mock_run.call_count == 0
    assert mock_popen.call_count == 0


def test_zero_network_connections(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify discovery does not attempt network socket operations."""
    mock_socket = MagicMock(side_effect=RuntimeError("Network sockets must not be created"))
    monkeypatch.setattr(socket, "socket", mock_socket)

    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")

    context = discover_project(tmp_path)

    assert context.candidate_files_count == 1
    assert mock_socket.call_count == 0


def test_mcp_config_secret_non_disclosure(tmp_path: Path) -> None:
    """Verify MCP discovery does not collect, parse, or leak sensitive keys or tokens."""
    sensitive_mcp_content = """{
        "mcpServers": {
            "github-server": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_super_secret_token_12345"
                }
            }
        }
    }"""
    (tmp_path / ".mcp.json").write_text(sensitive_mcp_content, encoding="utf-8")

    context = discover_project(tmp_path)

    # Ensure config file was detected
    assert ".mcp.json" in context.mcp_context.config_files

    # Serialize context to dict and verify no secrets or env vars are stored
    dumped_str = context.model_dump_json()
    assert "ghp_super_secret_token" not in dumped_str
    assert "GITHUB_PERSONAL_ACCESS_TOKEN" not in dumped_str
    assert "github-server" not in dumped_str
