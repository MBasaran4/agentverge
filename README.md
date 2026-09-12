# AgentVerge

Deterministic verification and safety infrastructure for AI coding agents.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

AgentVerge is a local-first, zero-paid-API verification tool designed to audit, validate, and constrain AI agent outputs and repositories with 100% deterministic checks.

---

## Project Status

**Current Version**: `v0.1.0` (Milestones AV-001 through AV-004 complete)

- **AV-001**: Project Scaffolding, CLI, Linting & Type Infrastructure
- **AV-002**: Project Discovery & Configuration Subsystem (`agentverge.toml` / `pyproject.toml`)
- **AV-003**: Domain Models & Scanner Architecture
- **AV-004**: Secret & Credential Scanner v0.1 (High-Entropy & Pattern Detection)

---

## Current Capabilities

* **Deterministic Secret Scanner**: Scans source files and diffs for leaked API keys, tokens, and credentials (AWS, OpenAI, GitHub, Slack, SSH/PGP Private Keys, and generic high-entropy secrets) with safe redaction.
* **Context & Project Discovery**: Safely discovers target files while strictly honoring `.gitignore`, file limits, and maximum file size thresholds.
* **Hierarchical Configuration**: Supports configuration via `agentverge.toml` or `pyproject.toml` with zero-config defaults.
* **CLI Interface**: Built with Typer and Rich for clear, structured diagnostic reports and severity filtering.

---

## Quick Start

### Prerequisites

* Python 3.12+

### Installation & Setup

Clone the repository and install dependencies in a virtual environment:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### CLI Usage

```bash
# Run security scanners on current directory
agentverge scan .

# Scan a specific directory or file
agentverge scan src/

# Run full project verification
agentverge check .

# Display help or version
agentverge --help
agentverge --version
```

---

## Development & Verification

Run the full verification suite:

```bash
# Run tests
pytest

# Lint checks
ruff check .

# Formatting checks
ruff format --check .

# Static type checking
mypy src tests
```

---

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md) for details on planned features, including:
* Dangerous execution (AST) and unsafe file operation scanners
* Deterministic behavioral evaluators
* SARIF reporting & GitHub Action integration
* Tool-use safety & MCP capability auditing

---

## License

This project is licensed under the [MIT License](LICENSE).
