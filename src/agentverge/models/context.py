"""Domain models for project discovery context."""

from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field


class ProjectStructure(BaseModel):
    """Structural metadata about the discovered project repository.

    Note on immutability:
        `frozen=True` prevents attribute reassignment on this model.
        Inner Python lists should not be mutated after creation.
    """

    model_config = ConfigDict(frozen=True)

    root_path: Path
    is_git_repo: bool
    is_python_project: bool
    package_managers: list[str] = Field(default_factory=list)
    project_files: list[str] = Field(default_factory=list)
    has_github_workflows: bool = False
    workflow_files: list[str] = Field(default_factory=list)


class AgentContext(BaseModel):
    """Discovered AI agent instructions and configuration markers.

    Note on immutability:
        `frozen=True` prevents attribute reassignment on this model.
    """

    model_config = ConfigDict(frozen=True)

    instruction_files: list[str] = Field(default_factory=list)
    agent_config_files: list[str] = Field(default_factory=list)


class McpContext(BaseModel):
    """Discovered Model Context Protocol (MCP) configuration markers.

    Minimal discovery representation: records configuration files and JSON validity
    without extracting or storing server arguments, environment variables, or secrets.
    """

    model_config = ConfigDict(frozen=True)

    config_files: list[str] = Field(default_factory=list)
    valid_configs_count: int = 0


class ProjectContext(BaseModel):
    """Aggregate discovery context container for the target project.

    Attributes:
        root_path: Absolute resolved path to project root.
        structure: General repository and project metadata.
        agent_context: AI agent instructions and rule files.
        mcp_context: MCP configuration files.
        config_file: Path to loaded AgentVerge config file if any.
        candidate_files: Discovered candidate file paths for inspection.
        candidate_files_count: Count of candidate files discovered for potential analysis.
        discovered_at: Timezone-aware UTC timestamp of discovery.

    Note on immutability:
        `frozen=True` prevents direct attribute reassignment on this model.
        Inner Python lists are not deeply immutable.
    """

    model_config = ConfigDict(frozen=True)

    root_path: Path
    structure: ProjectStructure
    agent_context: AgentContext
    mcp_context: McpContext
    config_file: Path | None = None
    candidate_files: list[Path] = Field(default_factory=list)
    candidate_files_count: int = 0
    discovered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def target_files(self) -> list[Path]:
        """Alias for candidate_files for scanner protocol ergonomics."""
        return self.candidate_files
