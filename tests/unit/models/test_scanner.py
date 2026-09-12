"""Unit tests for the Scanner protocol contract."""

from pathlib import Path

from agentverge.models import (
    Finding,
    ProjectContext,
    ProjectStructure,
    Scanner,
    ScanResult,
    Severity,
)
from agentverge.models.context import AgentContext, McpContext
from agentverge.scanners import Scanner as ScannersScanner


class TinyFakeScanner:
    """A minimal fake scanner conforming to the Scanner protocol."""

    name: str = "Tiny Fake Scanner"
    description: str = "A fake scanner used for protocol contract unit testing."

    def scan(self, context: ProjectContext) -> ScanResult:
        findings: list[Finding] = []
        if not context.structure.is_git_repo:
            findings.append(
                Finding(
                    id="FAKE-001",
                    title="Not a Git Repository",
                    description="Repository is missing git markers.",
                    severity=Severity.INFO,
                    category="metadata",
                )
            )
        return ScanResult(
            scanner_name=self.name,
            findings=findings,
            files_scanned=context.candidate_files_count,
            duration_ms=1.25,
            metadata={"fake_mode": True},
        )


class MissingNameScanner:
    description: str = "Missing name"

    def scan(self, context: ProjectContext) -> ScanResult:
        return ScanResult(scanner_name="dummy")


class MissingDescriptionScanner:
    name: str = "Missing description"

    def scan(self, context: ProjectContext) -> ScanResult:
        return ScanResult(scanner_name=self.name)


class MissingScanMethodScanner:
    name: str = "Missing scan method"
    description: str = "No scan method"


def test_scanner_protocol_conformance() -> None:
    """Verify TinyFakeScanner conforms to the Scanner protocol via runtime check."""
    scanner = TinyFakeScanner()
    assert isinstance(scanner, Scanner)
    assert isinstance(scanner, ScannersScanner)
    assert scanner.name == "Tiny Fake Scanner"
    assert scanner.description == "A fake scanner used for protocol contract unit testing."


def test_invalid_scanners_fail_protocol_check() -> None:
    """Verify objects missing name, description, or scan method fail the Scanner check."""
    assert not isinstance(MissingNameScanner(), Scanner)
    assert not isinstance(MissingDescriptionScanner(), Scanner)
    assert not isinstance(MissingScanMethodScanner(), Scanner)


def test_fake_scanner_execution_with_project_context(tmp_path: Path) -> None:
    """Verify executing scanner.scan(context) receives ProjectContext and returns ScanResult."""
    context = ProjectContext(
        root_path=tmp_path,
        structure=ProjectStructure(
            root_path=tmp_path,
            is_git_repo=False,
            is_python_project=True,
        ),
        agent_context=AgentContext(),
        mcp_context=McpContext(),
        candidate_files_count=3,
    )

    scanner = TinyFakeScanner()
    result = scanner.scan(context)

    assert isinstance(result, ScanResult)
    assert result.scanner_name == "Tiny Fake Scanner"
    assert result.files_scanned == 3
    assert result.duration_ms == 1.25
    assert result.has_findings is True
    assert result.finding_count == 1
    assert result.findings[0].id == "FAKE-001"
    assert result.findings[0].severity == Severity.INFO
    assert result.metadata == {"fake_mode": True}


def test_fake_scanner_zero_findings_execution(tmp_path: Path) -> None:
    """Verify fake scanner returns ScanResult with zero findings when condition not met."""
    context = ProjectContext(
        root_path=tmp_path,
        structure=ProjectStructure(
            root_path=tmp_path,
            is_git_repo=True,
            is_python_project=True,
        ),
        agent_context=AgentContext(),
        mcp_context=McpContext(),
        candidate_files_count=10,
    )

    scanner = TinyFakeScanner()
    result = scanner.scan(context)

    assert isinstance(result, ScanResult)
    assert result.has_findings is False
    assert result.finding_count == 0
    assert result.findings == []
    assert result.files_scanned == 10
