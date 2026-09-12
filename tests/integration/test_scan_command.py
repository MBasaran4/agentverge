"""Integration tests for the `agentverge scan` CLI command."""

from pathlib import Path

from typer.testing import CliRunner

from agentverge.cli.main import app

runner = CliRunner()


def test_cli_scan_clean_directory(tmp_path: Path) -> None:
    """Verify `agentverge scan` on a clean directory succeeds with exit code 0."""
    (tmp_path / "hello.py").write_text('print("Hello world")\n', encoding="utf-8")

    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 0
    assert "No exposed secrets detected" in result.stdout


def test_cli_scan_detects_secret_and_fails(tmp_path: Path) -> None:
    """Verify `agentverge scan` fails with exit code 1 when a secret is detected."""
    raw_secret = "AKIA9988776655443322"
    (tmp_path / "creds.py").write_text(f'AWS_KEY = "{raw_secret}"\n', encoding="utf-8")

    result = runner.invoke(app, ["scan", str(tmp_path)])

    assert result.exit_code == 1
    assert "AGENTVERGE-SECRET-AWS-001" in result.stdout
    assert "CRITICAL" in result.stdout

    # Security invariant: raw secret never appears in stdout or stderr
    assert raw_secret not in result.stdout
    if result.stderr:
        assert raw_secret not in result.stderr

    # Safe masked evidence is rendered
    assert "AKIA****" in result.stdout


def test_cli_scan_nonexistent_directory() -> None:
    """Verify `agentverge scan nonexistent` exits with code 2 and outputs error."""
    result = runner.invoke(app, ["scan", "nonexistent_dir_12345"])

    assert result.exit_code == 2
    assert "Discovery Error" in result.stderr or "Discovery Error" in result.stdout


def test_cli_scan_with_custom_config(tmp_path: Path) -> None:
    """Verify `agentverge scan` respects custom config exclusions."""
    # Place secret in a directory that will be excluded by custom config
    ignored_dir = tmp_path / "ignored"
    ignored_dir.mkdir()
    (ignored_dir / "secret.py").write_text('AWS_KEY = "AKIA1122334455667788"\n', encoding="utf-8")

    cfg = tmp_path / "agentverge.yml"
    cfg.write_text("exclude_patterns:\n  - 'ignored/**'\n", encoding="utf-8")

    result = runner.invoke(app, ["scan", str(tmp_path), "--config", str(cfg)])

    assert result.exit_code == 0
    assert "No exposed secrets detected" in result.stdout
