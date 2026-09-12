"""CLI entry point for AgentVerge."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from agentverge import __version__
from agentverge.config import ConfigurationError, load_config
from agentverge.discovery import ProjectDiscoveryError, discover_project
from agentverge.models.context import ProjectContext
from agentverge.models.result import ScanResult
from agentverge.scanners import SecretScanner

app = typer.Typer(
    name="agentverge",
    help="AgentVerge: Open-source verification infrastructure for AI agents.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()
error_console = Console(stderr=True)


def version_callback(value: bool) -> None:
    """Print the package version and exit."""
    if value:
        console.print(f"agentverge {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """AgentVerge: Open-source verification infrastructure for AI agents."""


def _render_discovery_summary(context: ProjectContext) -> None:
    """Format and render the project discovery summary using Rich."""
    table = Table(title="Project Discovery Summary", show_header=False, box=None, padding=(0, 1))
    table.add_column("Property", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="white")

    # Project root
    table.add_row("Project Root", str(context.root_path))

    # Git repository
    git_val = (
        "[bold green]Yes[/bold green] (.git marker found)"
        if context.structure.is_git_repo
        else "[yellow]No[/yellow]"
    )
    table.add_row("Git Repository", git_val)

    # Python project & managers
    if context.structure.is_python_project:
        managers = ", ".join(context.structure.package_managers) or "none detected"
        table.add_row(
            "Python Project",
            f"[bold green]Yes[/bold green] (package managers: {managers})",
        )
    else:
        table.add_row("Python Project", "[yellow]No[/yellow]")

    # Project markers
    if context.structure.project_files:
        table.add_row("Project Files", ", ".join(context.structure.project_files))

    # GitHub Workflows
    if context.structure.has_github_workflows:
        table.add_row("GitHub Workflows", ", ".join(context.structure.workflow_files))
    else:
        table.add_row("GitHub Workflows", "[dim]None[/dim]")

    # AI Agent instructions
    if context.agent_context.instruction_files:
        table.add_row(
            "AI Instructions",
            "[bold green]" + ", ".join(context.agent_context.instruction_files) + "[/bold green]",
        )
    else:
        table.add_row("AI Instructions", "[dim]None detected[/dim]")

    # MCP Configurations
    if context.mcp_context.config_files:
        mcp_desc = ", ".join(f"{cfg} (valid JSON)" for cfg in context.mcp_context.config_files)
        table.add_row("MCP Configs", mcp_desc)
    else:
        table.add_row("MCP Configs", "[dim]None detected[/dim]")

    # Active configuration
    if context.config_file:
        table.add_row(
            "Configuration",
            f"[green]{context.config_file.name}[/green] ({context.config_file})",
        )
    else:
        table.add_row("Configuration", "[dim]Default (zero-config)[/dim]")

    # Candidate files
    table.add_row("Candidate Files", str(context.candidate_files_count))

    console.print(Panel(table, title="[bold]AgentVerge Discovery[/bold]", border_style="cyan"))


@app.command(name="check")
def check_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to target directory to inspect.",
        ),
    ] = Path("."),
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to custom config file (.agentverge.yml, .agentverge.yaml, pyproject.toml).",
        ),
    ] = None,
) -> None:
    """Discover project structure, AI agent instruction files, and configuration."""
    try:
        loaded_config, config_file_path = load_config(root_path=path, explicit_config_path=config)
        context = discover_project(
            target_path=path,
            config=loaded_config,
            config_file_path=config_file_path,
        )
    except ConfigurationError as exc:
        error_console.print(f"[bold red]Configuration Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc
    except ProjectDiscoveryError as exc:
        error_console.print(f"[bold red]Discovery Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc

    _render_discovery_summary(context)


def _render_scan_summary(result: ScanResult) -> None:
    """Format and render the scan results using Rich."""
    if not result.has_findings:
        console.print(
            f"[bold green]No exposed secrets detected.[/bold green] "
            f"[dim]({result.files_scanned} files scanned in {result.duration_ms:.1f}ms)[/dim]"
        )
        return

    table = Table(title="Security Findings: Exposed Credentials", border_style="red")
    table.add_column("Severity", justify="center", no_wrap=True)
    table.add_column("Rule ID", style="cyan", no_wrap=True)
    table.add_column("Location", style="white", no_wrap=True)
    table.add_column("Description", style="dim", max_width=40)
    table.add_column("Evidence", style="yellow", overflow="fold")

    for finding in result.findings:
        sev = finding.severity.value
        sev_styled = (
            f"[bold red]{sev}[/bold red]"
            if sev == "CRITICAL"
            else f"[bold yellow]{sev}[/bold yellow]"
        )
        loc = f"{finding.file}:{finding.line}" if finding.line else str(finding.file or "")
        evidence_snippet = (finding.evidence or "").split("\n")[0]
        table.add_row(
            sev_styled,
            finding.id,
            loc,
            finding.description,
            evidence_snippet,
        )

    console.print(table)
    error_console.print(
        f"[bold red]Scan failed:[/bold red] {result.finding_count} finding(s) detected across "
        f"{result.files_scanned} files ({result.duration_ms:.1f}ms)."
    )


@app.command(name="scan")
def scan_command(
    path: Annotated[
        Path,
        typer.Argument(
            help="Path to target directory to scan for secrets.",
        ),
    ] = Path("."),
    config: Annotated[
        Path | None,
        typer.Option(
            "--config",
            "-c",
            help="Path to custom config file (.agentverge.yml, .agentverge.yaml, pyproject.toml).",
        ),
    ] = None,
) -> None:
    """Scan codebase for exposed credentials, API keys, and private keys."""
    try:
        loaded_config, config_file_path = load_config(root_path=path, explicit_config_path=config)
        context = discover_project(
            target_path=path,
            config=loaded_config,
            config_file_path=config_file_path,
        )
    except ConfigurationError as exc:
        error_console.print(f"[bold red]Configuration Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc
    except ProjectDiscoveryError as exc:
        error_console.print(f"[bold red]Discovery Error:[/bold red] {exc}")
        raise typer.Exit(code=2) from exc

    scanner = SecretScanner()
    result = scanner.scan(context)

    _render_scan_summary(result)

    fail_thresholds = [s.strip().upper() for s in loaded_config.thresholds.fail_on]
    has_failing_findings = any(f.severity.value in fail_thresholds for f in result.findings)
    if has_failing_findings:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()
