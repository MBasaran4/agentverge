"""Unit tests for SecretScanner execution, safety invariants, and security boundaries."""

from pathlib import Path
from unittest.mock import patch

from agentverge.models import ProjectContext, ProjectStructure, Scanner, ScanResult, Severity
from agentverge.models.context import AgentContext, McpContext
from agentverge.scanners import SecretScanner


def _create_test_context(root: Path, files: list[Path]) -> ProjectContext:
    """Helper to create a ProjectContext with given candidate files."""
    return ProjectContext(
        root_path=root,
        structure=ProjectStructure(
            root_path=root,
            is_git_repo=True,
            is_python_project=True,
        ),
        agent_context=AgentContext(),
        mcp_context=McpContext(),
        candidate_files=files,
        candidate_files_count=len(files),
    )


def test_secret_scanner_conforms_to_scanner_protocol() -> None:
    """Verify SecretScanner conforms to the Scanner protocol contract."""
    scanner = SecretScanner()
    assert isinstance(scanner, Scanner)
    assert scanner.name == "Secret & Credential Scanner"
    assert scanner.scanner_id == "secret_scanner"


def test_secret_scanner_detects_aws_key_and_redacts(tmp_path: Path) -> None:
    """Verify detection of AWS Access Key ID and strict redaction in findings."""
    raw_secret = "AKIA1122334455667788"
    file_path = tmp_path / "config.py"
    file_path.write_text(f'AWS_ACCESS_KEY_ID = "{raw_secret}"\n', encoding="utf-8")

    context = _create_test_context(tmp_path, [file_path])
    scanner = SecretScanner()
    result = scanner.scan(context)

    assert isinstance(result, ScanResult)
    assert result.has_findings is True
    assert result.finding_count == 1

    finding = result.findings[0]
    assert finding.id == "AGENTVERGE-SECRET-AWS-001"
    assert finding.severity == Severity.CRITICAL
    assert finding.line == 1
    assert finding.file == Path("config.py")

    # Invariant: raw secret NEVER appears in any domain model field
    assert finding.evidence is not None
    assert finding.remediation is not None
    assert raw_secret not in finding.evidence
    assert raw_secret not in finding.description
    assert raw_secret not in finding.title
    assert raw_secret not in finding.remediation
    assert raw_secret not in str(result.metadata)

    # Verify masked format
    assert "AKIA****************" in finding.evidence


def test_secret_scanner_detects_github_token_and_private_key(tmp_path: Path) -> None:
    """Verify GitHub token and private key PEM header detection."""
    raw_ghp = "ghp_ABCDEF1234567890ABCDEF12345678901234"
    app_file = tmp_path / "app.js"
    app_file.write_text(
        f"const token = \"{raw_ghp}\";\nconst dummy = 'some_regular_value';\n",
        encoding="utf-8",
    )

    key_file = tmp_path / "server.key"
    key_file.write_text(
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA0Y1234567890abcdefghijklmnopqrstuvwxyz\n"
        "-----END RSA PRIVATE KEY-----\n",
        encoding="utf-8",
    )

    context = _create_test_context(tmp_path, [app_file, key_file])
    scanner = SecretScanner()
    result = scanner.scan(context)

    assert result.finding_count == 2
    rule_ids = {f.id for f in result.findings}
    assert "AGENTVERGE-SECRET-GITHUB-001" in rule_ids
    assert "AGENTVERGE-SECRET-PRIVATE-KEY-001" in rule_ids

    # Find private key finding
    pk_finding = next(f for f in result.findings if f.id == "AGENTVERGE-SECRET-PRIVATE-KEY-001")
    assert pk_finding.evidence is not None
    assert "[REDACTED KEY MATERIAL]" in pk_finding.evidence
    assert "MIIEowIBAAKCAQEA0Y1234567890" not in pk_finding.evidence

    # Find GitHub token finding
    gh_finding = next(f for f in result.findings if f.id == "AGENTVERGE-SECRET-GITHUB-001")
    assert gh_finding.evidence is not None
    assert raw_ghp not in gh_finding.evidence
    assert "ghp_************************************" in gh_finding.evidence


def test_secret_scanner_detects_env_file_credentials(tmp_path: Path) -> None:
    """Verify .env credential assignments are flagged with HIGH severity."""
    raw_pass = "super_secret_db_pass_123"
    env_file = tmp_path / ".env"
    env_file.write_text(
        f"DATABASE_PASSWORD={raw_pass}\nDEBUG=True\n",
        encoding="utf-8",
    )

    context = _create_test_context(tmp_path, [env_file])
    scanner = SecretScanner()
    result = scanner.scan(context)

    assert result.finding_count == 1
    finding = result.findings[0]
    assert finding.id == "AGENTVERGE-SECRET-ENV-CRED-001"
    assert finding.severity == Severity.HIGH
    assert finding.evidence is not None
    assert raw_pass not in finding.evidence
    assert "DATABASE_PASSWORD=" in finding.evidence


def test_secret_scanner_skips_binary_files(tmp_path: Path) -> None:
    """Verify binary files (e.g. .png, files with null bytes) are safely skipped."""
    raw_secret = "AKIA1122334455667788"

    png_file = tmp_path / "image.png"
    png_file.write_bytes(b"\x89PNG\r\n\x1a\n" + raw_secret.encode())

    null_file = tmp_path / "data.bin"
    null_file.write_bytes(b"some\x00data" + raw_secret.encode())

    context = _create_test_context(tmp_path, [png_file, null_file])
    scanner = SecretScanner()
    result = scanner.scan(context)

    assert result.finding_count == 0
    assert result.files_scanned == 0


def test_secret_scanner_skips_oversized_files(tmp_path: Path) -> None:
    """Verify files exceeding maximum file size threshold are skipped."""
    oversized_file = tmp_path / "huge.txt"
    # Create file > 5 MB
    oversized_file.write_bytes(b"A" * (5_242_880 + 100))

    context = _create_test_context(tmp_path, [oversized_file])
    scanner = SecretScanner()
    result = scanner.scan(context)

    assert result.finding_count == 0
    assert result.files_scanned == 0


def test_secret_scanner_ignores_placeholders(tmp_path: Path) -> None:
    """Verify placeholder values and doc examples produce zero findings."""
    doc_file = tmp_path / "example.py"
    doc_file.write_text(
        'AWS_KEY = "AKIAIOSFODNN7EXAMPLE"\n'
        'API_KEY = "YOUR_API_KEY_HERE"\n'
        'PASSWORD = "CHANGE_ME"\n'
        'TOKEN = "${PROCESS_ENV_TOKEN}"\n',
        encoding="utf-8",
    )

    context = _create_test_context(tmp_path, [doc_file])
    scanner = SecretScanner()
    result = scanner.scan(context)

    assert result.finding_count == 0


def test_secret_scanner_security_boundaries(tmp_path: Path) -> None:
    """Verify scanner executes strictly read-only: no subprocess, no network, no writes."""
    test_file = tmp_path / "service.py"
    initial_content = 'api_key = "SYNTHETIC_TEST_SECRET_VALUE_987654321"\n'
    test_file.write_text(initial_content, encoding="utf-8")

    context = _create_test_context(tmp_path, [test_file])
    scanner = SecretScanner()

    with (
        patch("subprocess.run") as mock_subproc,
        patch("subprocess.Popen") as mock_popen,
        patch("socket.socket") as mock_socket,
    ):
        result = scanner.scan(context)

        # Assert zero subprocess executions
        assert mock_subproc.call_count == 0
        assert mock_popen.call_count == 0

        # Assert zero network socket creations
        assert mock_socket.call_count == 0

    # Assert target project file was never modified
    assert test_file.read_text(encoding="utf-8") == initial_content
    assert result.finding_count == 1
