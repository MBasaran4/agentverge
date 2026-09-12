"""Tests enforcing strict architectural isolation for domain models and scanner contracts.

Ensures models and scanner protocols have zero dependencies on CLI libraries (Typer, Rich),
zero subprocess execution, and zero outbound network calls.
"""

import ast
import socket
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import agentverge.models
import agentverge.models.finding
import agentverge.models.result
import agentverge.models.scanner
import agentverge.scanners
from agentverge.models import (
    Finding,
    ProjectContext,
    ProjectStructure,
    ScanResult,
    Severity,
)
from agentverge.models.context import AgentContext, McpContext
from tests.unit.models.test_scanner import TinyFakeScanner

FORBIDDEN_MODULES = {
    "typer",
    "rich",
    "agentverge.cli",
    "subprocess",
    "socket",
    "urllib",
    "http",
    "requests",
    "httpx",
}


def _extract_imported_modules(file_path: Path) -> set[str]:
    """Parse a python file AST and return all top-level imported module names."""
    tree = ast.parse(file_path.read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def test_models_have_zero_forbidden_imports() -> None:
    """Verify models and scanner contract files do not import forbidden modules."""
    files_to_check = [
        Path(agentverge.models.finding.__file__),
        Path(agentverge.models.result.__file__),
        Path(agentverge.models.scanner.__file__),
        Path(agentverge.models.__file__),
        Path(agentverge.scanners.__file__),
    ]

    for file_path in files_to_check:
        imports = _extract_imported_modules(file_path)
        for forbidden in FORBIDDEN_MODULES:
            for imported_mod in imports:
                assert not (
                    imported_mod == forbidden or imported_mod.startswith(f"{forbidden}.")
                ), f"Forbidden import '{imported_mod}' found in {file_path.name}"


def test_zero_subprocess_and_network_during_model_operations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify model operations invoke zero subprocesses or network calls."""
    mock_run = MagicMock(side_effect=RuntimeError("Subprocess execution is strictly forbidden"))
    mock_popen = MagicMock(side_effect=RuntimeError("Subprocess execution is strictly forbidden"))
    mock_socket = MagicMock(side_effect=RuntimeError("Network sockets are strictly forbidden"))

    monkeypatch.setattr(subprocess, "run", mock_run)
    monkeypatch.setattr(subprocess, "Popen", mock_popen)
    monkeypatch.setattr(socket, "socket", mock_socket)

    # Instantiate Finding
    finding = Finding(
        id="SEC-001",
        title="Sample Finding",
        description="Verifying runtime isolation",
        severity=Severity.HIGH,
        category="security",
        file=Path("app.py"),
        line=10,
    )

    # Instantiate ScanResult
    result = ScanResult(
        scanner_name="isolated-scanner",
        findings=[finding],
        files_scanned=1,
        duration_ms=5.0,
    )

    # Execute TinyFakeScanner
    context = ProjectContext(
        root_path=tmp_path,
        structure=ProjectStructure(
            root_path=tmp_path,
            is_git_repo=True,
            is_python_project=True,
        ),
        agent_context=AgentContext(),
        mcp_context=McpContext(),
        candidate_files_count=1,
    )
    scanner = TinyFakeScanner()
    scan_result = scanner.scan(context)

    assert result.has_findings is True
    assert scan_result.has_findings is False
    assert mock_run.call_count == 0
    assert mock_popen.call_count == 0
    assert mock_socket.call_count == 0
