"""Domain models for AgentVerge configuration."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

DEFAULT_EXCLUDE_PATTERNS: list[str] = [
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
    ".tox",
    ".eggs",
    "*.egg-info",
]


class SeverityThresholds(BaseModel):
    """Configuration for severity failure thresholds."""

    model_config = ConfigDict(frozen=True)

    fail_on: list[str] = Field(default_factory=lambda: ["high", "critical"])


class ScannerSettings(BaseModel):
    """Configuration settings for security scanners."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    rules: dict[str, Any] = Field(default_factory=dict)


class EvaluationSettings(BaseModel):
    """Configuration settings for behavioral evaluators."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    manifest_path: str | None = None


class ReportSettings(BaseModel):
    """Configuration settings for reporting formats and destinations."""

    model_config = ConfigDict(frozen=True)

    formats: list[str] = Field(default_factory=lambda: ["terminal"])
    output_dir: str | None = None


class CISettings(BaseModel):
    """Configuration settings for CI/CD environments."""

    model_config = ConfigDict(frozen=True)

    strict: bool = False
    exit_code_on_failure: int = 1


class AgentVergeConfig(BaseModel):
    """Top-level configuration model for AgentVerge.

    Designed to be extensible for future scanner, evaluation, and CI rules.
    Note on immutability:
        `frozen=True` prevents direct attribute reassignment.
    """

    model_config = ConfigDict(frozen=True)

    version: str = "1"
    exclude_patterns: list[str] = Field(default_factory=lambda: list(DEFAULT_EXCLUDE_PATTERNS))
    include_patterns: list[str] = Field(default_factory=lambda: ["*"])
    max_file_size_bytes: int = 5_242_880  # 5 MB
    scanners: dict[str, ScannerSettings] = Field(default_factory=dict)
    evaluation: EvaluationSettings = Field(default_factory=EvaluationSettings)
    thresholds: SeverityThresholds = Field(default_factory=SeverityThresholds)
    reporting: ReportSettings = Field(default_factory=ReportSettings)
    ci: CISettings = Field(default_factory=CISettings)
