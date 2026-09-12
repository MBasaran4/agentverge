"""Domain models for scan results."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from agentverge.models.finding import Finding


class ScanResult(BaseModel):
    """Execution result produced by a static scanner.

    Attributes:
        scanner_name: Name of the scanner that produced this result.
        findings: Sequence of findings detected during the scan.
        files_scanned: Number of files inspected (must be >= 0).
        duration_ms: Total duration of the scan in milliseconds (must be >= 0.0).
        metadata: Optional dictionary of additional diagnostic metadata.

    Note on immutability:
        `ConfigDict(frozen=True)` prevents attribute reassignment on this model.
        It does not guarantee deep immutability of nested mutable collections.
    """

    model_config = ConfigDict(frozen=True)

    scanner_name: str = Field(min_length=1)
    findings: list[Finding] = Field(default_factory=list)
    files_scanned: int = Field(default=0, ge=0)
    duration_ms: float = Field(default=0.0, ge=0.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("scanner_name")
    @classmethod
    def _validate_scanner_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("'scanner_name' cannot be empty or whitespace only")
        return v

    @model_validator(mode="before")
    @classmethod
    def _normalize_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            d = dict(data)
            if "name" in d and "scanner_name" not in d:
                d["scanner_name"] = d.pop("name")
            if "scan_duration" in d and "duration_ms" not in d:
                d["duration_ms"] = d.pop("scan_duration")
            elif "duration" in d and "duration_ms" not in d:
                d["duration_ms"] = d.pop("duration")
            return d
        return data

    @property
    def name(self) -> str:
        """Alias for scanner_name."""
        return self.scanner_name

    @property
    def duration(self) -> float:
        """Alias for duration_ms."""
        return self.duration_ms

    @property
    def scan_duration(self) -> float:
        """Alias for duration_ms."""
        return self.duration_ms

    @property
    def has_findings(self) -> bool:
        """Return True if any findings were recorded."""
        return len(self.findings) > 0

    @property
    def finding_count(self) -> int:
        """Return the count of findings recorded."""
        return len(self.findings)
