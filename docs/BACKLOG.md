# AgentVerge Canonical Engineering Backlog

This document serves as the official tracking registry for AgentVerge milestones, tasks, and engineering increments. It maps historical development phases to verifiable Git commits, active test suites, and planned future milestones.

---

## Completed Milestones (`v0.1.0`)

The following milestones establish the `v0.1.0` foundation. They were developed in the sequential order verified by Git commit history and automated test coverage.

### AV-001: Project Scaffolding & Engineering Foundations
* **Status**: `COMPLETED`
* **Domain**: Tooling, Project Structure & Governance
* **Description**:
  * Established repository architecture, directory layout (`src/agentverge`, `tests`, `docs`), and packaging specification via `pyproject.toml` (`hatchling` build backend).
  * Configured modern linting, formatting, and strict type checking (`ruff`, `mypy` strict mode for Python 3.12+).
  * Formulated foundational project governance documents: `AGENTS.md`, `LICENSE` (MIT), `docs/PRODUCT.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, and `docs/THREAT_MODEL.md`.
* **Associated Commits**:
  * `8006422` (*Initial commit*)
  * `494c998` (*feat: implement AgentVerge v0.1 foundation and secret scanner*)
* **Verification / Tests**:
  * Baseline test and lint configurations verified in `pyproject.toml`.

---

### AV-002: Project Discovery & Configuration Subsystem
* **Status**: `COMPLETED`
* **Domain**: Discovery & Configuration
* **Description**:
  * Implemented directory walker in `agentverge.discovery.detector` with root boundary enforcement, `.gitignore` parsing, custom exclusion patterns, and symlink escape defenses.
  * Extracted project markers (`.git`), package managers (`hatch`, `poetry`, `pip`), candidate source files, and AI context files (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `mcp.json`).
  * Implemented hierarchical configuration loader in `agentverge.config.loader` supporting zero-config discovery, `pyproject.toml` (`[tool.agentverge]`), and `.agentverge.yml` / `.agentverge.yaml`.
* **Implementation Modules**:
  * `src/agentverge/discovery/detector.py`
  * `src/agentverge/config/loader.py`
* **Associated Commits**:
  * `494c998` (*feat: implement AgentVerge v0.1 foundation and secret scanner*)
* **Verification / Tests**:
  * 28 unit tests passing:
    * `tests/unit/discovery/test_discovery.py` (15 tests)
    * `tests/unit/discovery/test_safety.py` (3 tests)
    * `tests/unit/config/test_config.py` (10 tests)

---

### AV-003: Core Domain Models & Protocol Layer
* **Status**: `COMPLETED`
* **Domain**: Data Models & Protocols
* **Description**:
  * Implemented Pydantic v2 immutable models (`frozen=True`) with strict validation:
    * `Severity` enum: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
    * `Finding`: Normalized fields, non-empty validation, zero raw credential persistence.
    * `EvaluationStatus` & `EvaluationResult`: Behavioral test outcomes.
    * `ScanResult` & `VerificationReport`: Aggregate finding metrics and scan summaries.
  * Formalized `Scanner` protocol contract using standard Python `typing.Protocol`.
* **Implementation Modules**:
  * `src/agentverge/models/finding.py`
  * `src/agentverge/models/result.py`
  * `src/agentverge/models/scanner.py`
  * `src/agentverge/models/context.py`
  * `src/agentverge/models/config.py`
* **Associated Commits**:
  * `494c998` (*feat: implement AgentVerge v0.1 foundation and secret scanner*)
* **Verification / Tests**:
  * 69 unit tests passing:
    * `tests/unit/models/test_finding.py` (39 tests)
    * `tests/unit/models/test_result.py` (24 tests)
    * `tests/unit/models/test_scanner.py` (4 tests)
    * `tests/unit/models/test_isolation.py` (2 tests)

---

### AV-004: Baseline Security Scanner — Secret & Credential Detection
* **Status**: `COMPLETED`
* **Domain**: Static Security Scanning
* **Description**:
  * Implemented regex and pattern-matching rules for exposed credentials:
    * `AGENTVERGE-SECRET-AWS-001`: AWS Access Key IDs (`AKIA` / `ASIA`).
    * `AGENTVERGE-SECRET-GITHUB-001`: GitHub Personal Access Tokens (`ghp_`, `github_pat_`).
    * `AGENTVERGE-SECRET-PRIVATE-KEY-001`: Cryptographic PEM Private Key headers.
    * `AGENTVERGE-SECRET-GENERIC-API-KEY-001`: Hardcoded credential assignments.
    * `AGENTVERGE-SECRET-ENV-CRED-001`: Plaintext credentials inside `.env` files.
  * Implemented strict redaction and evidence truncation (`masking.py`) ensuring sensitive credentials are never stored or logged in cleartext.
  * Built false-positive heuristics filtering documentation examples, template interpolations (`${...}`, `{{ ... }}`), and common dummy placeholders.
* **Implementation Modules**:
  * `src/agentverge/scanners/patterns.py`
  * `src/agentverge/scanners/masking.py`
  * `src/agentverge/scanners/secret.py`
* **Associated Commits**:
  * `494c998` (*feat: implement AgentVerge v0.1 foundation and secret scanner*)
* **Verification / Tests**:
  * 24 unit tests passing:
    * `tests/unit/scanners/test_secret_scanner.py` (8 tests)
    * `tests/unit/scanners/test_patterns.py` (9 tests)
    * `tests/unit/scanners/test_masking.py` (7 tests)

---

### AV-005: CLI Interface & Diagnostic Presentation
* **Status**: `COMPLETED`
* **Domain**: Command-Line Interface
* **Description**:
  * Implemented Typer-based CLI application with Rich terminal formatting:
    * `agentverge check [path]`: Inspect project layout, candidate files, and AI context.
    * `agentverge scan [path]`: Execute secret and credential scanning.
    * `--version` / `-v`: Display active version.
  * Enforced standardized process exit codes:
    * `0`: Clean execution, no findings exceeding threshold.
    * `1`: Verification failed (findings exceeded severity threshold).
    * `2`: Discovery error or invalid configuration.
* **Implementation Modules**:
  * `src/agentverge/cli/main.py`
* **Associated Commits**:
  * `494c998` (*feat: implement AgentVerge v0.1 foundation and secret scanner*)
  * `1e4f4e2` (*docs: enhance README with v0.1.0 positioning, architecture, and CLI examples*)
* **Verification / Tests**:
  * 11 unit & integration tests passing:
    * `tests/unit/test_cli.py` (3 tests)
    * `tests/integration/test_check_command.py` (4 tests)
    * `tests/integration/test_scan_command.py` (4 tests)

---

### AV-006: Continuous Integration & Quality Automation Pipeline
* **Status**: `COMPLETED`
* **Domain**: CI/CD & Automation
* **Description**:
  * Created GitHub Actions workflow (`ci.yml`) triggering on pushes and pull requests targeting `main`.
  * Configured multi-step validation: dependency installation, `pytest` test suite, `ruff check`, `ruff format --check`, and `mypy` strict type checking on Python 3.12.
* **Implementation Modules**:
  * `.github/workflows/ci.yml`
* **Associated Commits**:
  * `fee8135` (*Create ci.yml*)
  * `63d8f24` (*Merge pull request #1 from MBasaran4/MBasaran4-patch-1*)
* **Verification / Tests**:
  * GitHub Actions Run ID `34704450529` successfully passing on `main`.

---

## Future Backlog Milestones (Prioritized by Roadmap)

### Phase 2: Core Static Safety Expansion (`v0.2.0`)

#### AV-007: AST-Based Dangerous Execution Scanner
* **Status**: `PLANNED`
* **Target Version**: `v0.2.0`
* **Domain**: Static Code Security
* **Scope**:
  * Implement `DangerousExecutionScanner` conforming to the `Scanner` protocol.
  * Inspect Python AST for unvalidated execution primitives: `eval()`, `exec()`, `__import__()`, and `subprocess.run(shell=True)`.
  * Include AST bomb protections (file size bounds, recursion error handling).

#### AV-008: Unsafe File Operations & Path Traversal Scanner
* **Status**: `PLANNED`
* **Target Version**: `v0.2.0`
* **Domain**: Static Code Security
* **Scope**:
  * Implement `UnsafeFileOpsScanner` detecting arbitrary write patterns and unvalidated path traversal escapes (`../`, `/etc/`, absolute overrides).

#### AV-009: Baseline Deterministic Evaluator Subsystem
* **Status**: `PLANNED`
* **Target Version**: `v0.2.0`
* **Domain**: Agent Behavior Evaluation
* **Scope**:
  * Implement `FileExistenceEvaluator` (verifying mandatory artifact creation).
  * Implement `DiffBoundaryEvaluator` (verifying agent edits stay within permitted directories).
  * Implement `ContentAssertionEvaluator` (regex and JSON schema matching on agent outputs).
  * Formalize task manifest specification contract (`agentverge.eval.toml` or `task_spec.json`).

#### AV-010: Core Engine Orchestration & Decoupled Reporters
* **Status**: `PLANNED`
* **Target Version**: `v0.2.0`
* **Domain**: Core Engine & Reporting
* **Scope**:
  * Implement `VerificationEngine` in `agentverge.core` with scanner and evaluator registries.
  * Decouple presentation: implement `JsonReporter` and `TerminalReporter` in `agentverge.reporters`.

#### AV-011: Configuration Template Generator (`agentverge init`)
* **Status**: `PLANNED`
* **Target Version**: `v0.2.0`
* **Domain**: CLI Usability
* **Scope**:
  * Implement `agentverge init` CLI command generating a standard `.agentverge.yml` template with customizable severity thresholds and exclusion lists.

---

### Phase 3: CI/CD Quality Gates & GitHub Integration (`v0.3.0`)

#### AV-012: SARIF v2.1.0 Export Subsystem
* **Status**: `PLANNED`
* **Target Version**: `v0.3.0`
* **Domain**: CI/CD & Reporting
* **Scope**:
  * Implement `SarifReporter` exporting findings according to the OASIS SARIF v2.1.0 specification.
  * Enable native integration with GitHub Code Scanning alerts.

#### AV-013: Git Diff Scanning Mode
* **Status**: `PLANNED`
* **Target Version**: `v0.3.0`
* **Domain**: Developer Ergonomics
* **Scope**:
  * Implement `--diff <ref>` flag (e.g. `agentverge scan --diff main`) to scan only changed files and modified hunks in the active Git branch.

#### AV-014: Official GitHub Action (`agentverge/action`)
* **Status**: `PLANNED`
* **Target Version**: `v0.3.0`
* **Domain**: Ecosystem Integration
* **Scope**:
  * Publish composite GitHub Action providing automated PR scanning, step summaries, and inline code annotations.

---

### Phase 4: Tool Safety & MCP Auditing (`v0.4.0+`)

#### AV-015: MCP Capability Auditor & Pre-execution Tool Safety
* **Status**: `PLANNED`
* **Target Version**: `v0.4.0`
* **Domain**: Tool-Use Safety
* **Scope**:
  * Audit Model Context Protocol (MCP) server manifests (`mcp.json`) for dangerous permissions and unconstrained parameters.
  * Pre-execution tool parameter validation before autonomous commands run.
