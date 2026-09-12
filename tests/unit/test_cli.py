"""Tests for AgentVerge CLI and package initialization."""

from typer.testing import CliRunner

import agentverge
from agentverge.cli.main import app

runner = CliRunner()


def test_package_import() -> None:
    """Verify package can be imported and exports valid version."""
    assert hasattr(agentverge, "__version__")
    assert agentverge.__version__ == "0.1.0"


def test_cli_help() -> None:
    """Verify agentverge --help exits with 0 and contains AgentVerge."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AgentVerge" in result.stdout


def test_cli_version() -> None:
    """Verify agentverge --version exits with 0 and outputs correct version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout
    assert "agentverge" in result.stdout
