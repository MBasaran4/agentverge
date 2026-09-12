"""Unit tests for the Finding domain model and Severity enum."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agentverge.models.finding import Finding, Severity


def test_valid_finding_full_fields() -> None:
    """Verify creation of a Finding with all fields explicitly provided."""
    finding = Finding(
        id="SEC-001",
        title="Command Injection Vulnerability",
        description="Unsanitized user input passed directly to os.system.",
        severity=Severity.HIGH,
        category="security",
        file=Path("src/utils/exec.py"),
        line=42,
        evidence="os.system(user_param)",
        remediation="Use subprocess.run with a list of arguments and shell=False.",
    )

    assert finding.id == "SEC-001"
    assert finding.title == "Command Injection Vulnerability"
    assert finding.description == "Unsanitized user input passed directly to os.system."
    assert finding.severity == Severity.HIGH
    assert finding.category == "security"
    assert finding.file == Path("src/utils/exec.py")
    assert finding.line == 42
    assert finding.evidence == "os.system(user_param)"
    assert finding.remediation == "Use subprocess.run with a list of arguments and shell=False."


def test_valid_finding_minimal_fields() -> None:
    """Verify creation of a Finding with only required fields and default None values."""
    finding = Finding(
        id="CFG-002",
        title="Missing Security Marker",
        description="AGENTS.md was not found in the project root.",
        severity=Severity.INFO,
        category="compliance",
    )

    assert finding.id == "CFG-002"
    assert finding.title == "Missing Security Marker"
    assert finding.description == "AGENTS.md was not found in the project root."
    assert finding.severity == Severity.INFO
    assert finding.category == "compliance"
    assert finding.file is None
    assert finding.line is None
    assert finding.evidence is None
    assert finding.remediation is None


@pytest.mark.parametrize(
    ("severity_val", "expected_enum"),
    [
        (Severity.INFO, Severity.INFO),
        (Severity.LOW, Severity.LOW),
        (Severity.MEDIUM, Severity.MEDIUM),
        (Severity.HIGH, Severity.HIGH),
        (Severity.CRITICAL, Severity.CRITICAL),
        ("INFO", Severity.INFO),
        ("LOW", Severity.LOW),
        ("MEDIUM", Severity.MEDIUM),
        ("HIGH", Severity.HIGH),
        ("CRITICAL", Severity.CRITICAL),
        ("info", Severity.INFO),
        ("low", Severity.LOW),
        ("medium", Severity.MEDIUM),
        ("high", Severity.HIGH),
        ("critical", Severity.CRITICAL),
        (" High ", Severity.HIGH),
    ],
)
def test_all_severity_levels_and_normalization(
    severity_val: Severity | str,
    expected_enum: Severity,
) -> None:
    """Verify all valid severity levels are accepted and normalized."""
    finding = Finding(
        id="RULE-01",
        title="Check Severity",
        description="Severity normalization test",
        severity=severity_val,  # type: ignore[arg-type]
        category="test",
    )
    assert finding.severity == expected_enum
    assert finding.severity.value == expected_enum.value


@pytest.mark.parametrize(
    "invalid_severity",
    [
        "UNKNOWN",
        "MODERATE",
        "BLOCKER",
        "SEVERE",
        "",
        123,
    ],
)
def test_invalid_severity_raises_validation_error(invalid_severity: object) -> None:
    """Verify invalid severity strings/types raise ValidationError."""
    with pytest.raises(ValidationError):
        Finding(
            id="RULE-01",
            title="Check Severity",
            description="Invalid severity test",
            severity=invalid_severity,  # type: ignore[arg-type]
            category="test",
        )


@pytest.mark.parametrize(
    "missing_field",
    ["id", "title", "description", "severity", "category"],
)
def test_required_field_validation_missing(missing_field: str) -> None:
    """Verify omission of any required field raises ValidationError."""
    valid_data = {
        "id": "SEC-01",
        "title": "Title",
        "description": "Description",
        "severity": Severity.LOW,
        "category": "security",
    }
    valid_data.pop(missing_field)

    with pytest.raises(ValidationError):
        Finding(**valid_data)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "empty_field",
    ["id", "title", "description", "category"],
)
def test_required_string_fields_cannot_be_empty_or_whitespace(empty_field: str) -> None:
    """Verify required string fields reject empty or whitespace-only strings."""
    valid_data = {
        "id": "SEC-01",
        "title": "Title",
        "description": "Description",
        "severity": Severity.LOW,
        "category": "security",
    }
    valid_data[empty_field] = "   "

    with pytest.raises(ValidationError):
        Finding(**valid_data)  # type: ignore[arg-type]


def test_optional_file_and_line_handling() -> None:
    """Verify file path coercion and line number bounds validation."""
    # Coercion from string to Path via model_validate
    finding_str_path = Finding.model_validate(
        {
            "id": "F1",
            "title": "T",
            "description": "D",
            "severity": "LOW",
            "category": "C",
            "file": "relative/path/to/file.py",
            "line": 1,
        }
    )
    assert isinstance(finding_str_path.file, Path)
    assert finding_str_path.file == Path("relative/path/to/file.py")
    assert finding_str_path.line == 1

    # Preservation of Path instance
    finding_path_obj = Finding(
        id="F2",
        title="T",
        description="D",
        severity=Severity.LOW,
        category="C",
        file=Path("another/file.py"),
        line=999,
    )
    assert finding_path_obj.file == Path("another/file.py")
    assert finding_path_obj.line == 999

    # Empty string file path normalized to None
    finding_empty_file = Finding.model_validate(
        {
            "id": "F3",
            "title": "T",
            "description": "D",
            "severity": "LOW",
            "category": "C",
            "file": "",
            "line": None,
        }
    )
    assert finding_empty_file.file is None


@pytest.mark.parametrize("invalid_line", [0, -1, -100])
def test_invalid_line_numbers_raise_validation_error(invalid_line: int) -> None:
    """Verify source lines must be positive integers (>= 1)."""
    with pytest.raises(ValidationError):
        Finding(
            id="F4",
            title="T",
            description="D",
            severity=Severity.LOW,
            category="C",
            line=invalid_line,
        )


def test_finding_is_frozen() -> None:
    """Verify Finding attributes cannot be mutated after instantiation."""
    finding = Finding(
        id="F-FROZEN",
        title="Immutable Finding",
        description="Frozen model test",
        severity=Severity.MEDIUM,
        category="test",
    )

    with pytest.raises(ValidationError):
        finding.title = "Mutated Title"


def test_finding_json_serialization() -> None:
    """Verify Finding serializes cleanly to JSON and dictionary."""
    finding = Finding(
        id="F-SERIAL",
        title="Serialization Test",
        description="Verifying serialization round-trip",
        severity=Severity.CRITICAL,
        category="security",
        file=Path("app.py"),
        line=10,
        evidence="token = '123'",
        remediation="Remove token",
    )

    data = finding.model_dump()
    assert data["id"] == "F-SERIAL"
    assert data["severity"] == "CRITICAL"
    assert data["file"] == Path("app.py")

    json_str = finding.model_dump_json()
    assert '"severity":"CRITICAL"' in json_str
    assert '"id":"F-SERIAL"' in json_str
