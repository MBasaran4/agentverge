"""Domain models for scanner findings and severities."""

from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class Severity(StrEnum):
    """Enumeration of finding severity levels."""

    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Finding(BaseModel):
    """Domain model representing an individual scanner finding.

    Attributes:
        id: Unique identifier for the finding or rule.
        title: Short descriptive title of the issue.
        description: Detailed explanation of the detected problem.
        severity: Finding severity level.
        category: Category of the finding (e.g. 'security', 'syntax').
        file: Optional path to the file where the finding was detected.
        line: Optional 1-indexed line number in the source file.
        evidence: Optional code snippet or matched pattern evidence.
        remediation: Optional remediation guidance or fix advice.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: Severity
    category: str = Field(min_length=1)
    file: Path | None = None
    line: int | None = Field(default=None, ge=1)
    evidence: str | None = None
    remediation: str | None = None

    @field_validator("id", "title", "description", "category")
    @classmethod
    def _validate_non_empty(cls, v: str, info: ValidationInfo) -> str:
        if not v.strip():
            raise ValueError(f"'{info.field_name}' cannot be empty or whitespace only")
        return v

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("file", mode="before")
    @classmethod
    def _normalize_file(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        return Path(v)
