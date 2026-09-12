"""Unit tests for the ScanResult domain model."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agentverge.models.finding import Finding, Severity
from agentverge.models.result import ScanResult


def test_scan_result_with_zero_findings() -> None:
    """Verify ScanResult creation with zero findings."""
    result = ScanResult(
        scanner_name="secret-scanner",
        findings=[],
        files_scanned=10,
        duration_ms=45.2,
    )

    assert result.scanner_name == "secret-scanner"
    assert result.name == "secret-scanner"
    assert len(result.findings) == 0
    assert result.has_findings is False
    assert result.finding_count == 0
    assert result.files_scanned == 10
    assert result.duration_ms == 45.2
    assert result.duration == 45.2
    assert result.scan_duration == 45.2
    assert result.metadata == {}


def test_scan_result_with_multiple_findings() -> None:
    """Verify ScanResult correctly contains and exposes multiple findings."""
    f1 = Finding(
        id="RULE-1",
        title="Issue 1",
        description="First issue",
        severity=Severity.LOW,
        category="lint",
    )
    f2 = Finding(
        id="RULE-2",
        title="Issue 2",
        description="Second issue",
        severity=Severity.HIGH,
        category="security",
        file=Path("app.py"),
        line=25,
    )

    result = ScanResult(
        scanner_name="multi-scanner",
        findings=[f1, f2],
        files_scanned=2,
        duration_ms=12.0,
    )

    assert result.finding_count == 2
    assert result.has_findings is True
    assert len(result.findings) == 2
    assert result.findings[0] == f1
    assert result.findings[1] == f2


@pytest.mark.parametrize(
    "valid_duration",
    [0.0, 0, 1.5, 120.0, 5000.25],
)
def test_scan_result_duration_valid(valid_duration: float | int) -> None:
    """Verify non-negative durations are accepted."""
    result = ScanResult(
        scanner_name="timing-scanner",
        duration_ms=valid_duration,
    )
    assert result.duration_ms == float(valid_duration)


@pytest.mark.parametrize(
    "invalid_duration",
    [-0.001, -1.0, -100],
)
def test_scan_result_duration_negative_rejected(invalid_duration: float | int) -> None:
    """Verify negative durations raise ValidationError."""
    with pytest.raises(ValidationError):
        ScanResult(
            scanner_name="timing-scanner",
            duration_ms=invalid_duration,
        )


def test_scan_result_duration_aliases() -> None:
    """Verify duration and scan_duration keyword aliases populate duration_ms."""
    r1 = ScanResult.model_validate({"scanner_name": "test", "duration": 3.5})
    assert r1.duration_ms == 3.5

    r2 = ScanResult.model_validate({"scanner_name": "test", "scan_duration": 8.2})
    assert r2.duration_ms == 8.2


@pytest.mark.parametrize(
    "valid_files_scanned",
    [0, 1, 50, 1000],
)
def test_scan_result_files_scanned_valid(valid_files_scanned: int) -> None:
    """Verify non-negative integer files_scanned values are accepted."""
    result = ScanResult(
        scanner_name="counter-scanner",
        files_scanned=valid_files_scanned,
    )
    assert result.files_scanned == valid_files_scanned


@pytest.mark.parametrize(
    "invalid_files_scanned",
    [-1, -10, "not_an_int", ["file1.py", "file2.py"]],
)
def test_scan_result_files_scanned_invalid(invalid_files_scanned: object) -> None:
    """Verify negative integers and non-integer types are rejected."""
    with pytest.raises(ValidationError):
        ScanResult(
            scanner_name="counter-scanner",
            files_scanned=invalid_files_scanned,  # type: ignore[arg-type]
        )


def test_scan_result_name_alias() -> None:
    """Verify 'name' parameter alias populates scanner_name."""
    result = ScanResult.model_validate({"name": "alias-scanner"})
    assert result.scanner_name == "alias-scanner"
    assert result.name == "alias-scanner"


@pytest.mark.parametrize("empty_name", ["", "   "])
def test_scan_result_scanner_name_empty_rejected(empty_name: str) -> None:
    """Verify empty or whitespace-only scanner_name raises ValidationError."""
    with pytest.raises(ValidationError):
        ScanResult(scanner_name=empty_name)


def test_scan_result_metadata() -> None:
    """Verify custom metadata dictionary is preserved."""
    meta = {"rules_checked": 15, "skipped_rules": ["R-09"]}
    result = ScanResult(
        scanner_name="meta-scanner",
        metadata=meta,
    )
    assert result.metadata == meta
    assert result.metadata["rules_checked"] == 15


def test_scan_result_is_frozen() -> None:
    """Verify ScanResult attributes cannot be reassigned after creation."""
    result = ScanResult(
        scanner_name="frozen-scanner",
        files_scanned=5,
    )

    with pytest.raises(ValidationError):
        result.scanner_name = "reassigned"
