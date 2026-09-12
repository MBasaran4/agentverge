"""Contract definition for AgentVerge static security scanners."""

from typing import Protocol, runtime_checkable

from agentverge.models.context import ProjectContext
from agentverge.models.result import ScanResult


@runtime_checkable
class Scanner(Protocol):
    """Minimal protocol contract for all AgentVerge scanners.

    Every scanner must expose a human-readable name, a description,
    and a deterministic scan method that processes a ProjectContext
    and returns a ScanResult.
    """

    name: str
    description: str

    def scan(self, context: ProjectContext) -> ScanResult:
        """Execute static security checks on the target project context.

        Args:
            context: Discovered project context containing root path,
                project structure, agent context, and markers.

        Returns:
            ScanResult containing scanner name, findings, files scanned,
            duration, and optional metadata.
        """
        ...
