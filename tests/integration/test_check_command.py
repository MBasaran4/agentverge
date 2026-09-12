"""Integration tests for the `agentverge check` CLI command."""

from pathlib import Path

from typer.testing import CliRunner

from agentverge.cli.main import app

runner = CliRunner()


def test_cli_check_current_repository() -> None:
    """Verify `agentverge check .` on the active repository succeeds with exit code 0."""
    result = runner.invoke(app, ["check", "."])

    assert result.exit_code == 0
    assert "AgentVerge Discovery" in result.stdout
    assert "Git Repository" in result.stdout
    assert "Python Project" in result.stdout
    assert "AGENTS.md" in result.stdout


def test_cli_check_nonexistent_directory() -> None:
    """Verify `agentverge check nonexistent` exits with code 2 and outputs a clean error."""
    result = runner.invoke(app, ["check", "nonexistent_directory_xyz"])

    assert result.exit_code == 2
    assert "Discovery Error" in result.stderr or "Discovery Error" in result.stdout


def test_cli_check_with_valid_custom_config(tmp_path: Path) -> None:
    """Verify `agentverge check` respects an explicit --config flag."""
    (tmp_path / "main.py").write_text("print('test')", encoding="utf-8")
    cfg = tmp_path / "custom.yml"
    cfg.write_text("version: '2'\n", encoding="utf-8")

    result = runner.invoke(app, ["check", str(tmp_path), "--config", str(cfg)])

    assert result.exit_code == 0
    assert "custom.yml" in result.stdout


def test_cli_check_with_malformed_config(tmp_path: Path) -> None:
    """Verify `agentverge check` with malformed config exits with code 2."""
    bad_cfg = tmp_path / "bad.yml"
    bad_cfg.write_text("unclosed: [array", encoding="utf-8")

    result = runner.invoke(app, ["check", str(tmp_path), "--config", str(bad_cfg)])

    assert result.exit_code == 2
    assert "Configuration Error" in result.stderr or "Configuration Error" in result.stdout
