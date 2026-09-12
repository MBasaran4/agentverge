# AgentVerge Product & Technical Roadmap

## Phase 0: Architecture & Foundations (Current)
* [x] Formulate product mission and architectural boundaries.
* [x] Design core domain models (Finding, Severity, EvaluationResult, VerificationReport).
* [x] Formalize strict separation between Code Scanning, Behavior Eval, Tool Safety, and Runtime Monitoring.
* [x] Establish architectural decision records (ADRs) and threat model.
* [x] Define developer and agent guidelines (`AGENTS.md`).

---

## Phase 1: MVP - Core CLI & Deterministic Engine
**Target**: Compact, standalone, zero-paid-API local CLI verification tool.

* **1.1 Project Discovery & Context**:
  * Implement directory walker with `.gitignore` and pattern support (`fnmatch`).
  * Discovers source files, agent configuration files, and project diffs.
  * Build immutable `ProjectContext`.
* **1.2 Configuration Subsystem**:
  * Implement `AgentVergeConfig` loader supporting `agentverge.toml` and `pyproject.toml`.
  * Sensible zero-config defaults (scans current working directory).
* **1.3 Core Domain Models**:
  * Pydantic v2 models: `Severity`, `SourceLocation`, `Finding`, `EvaluationStatus`, `EvaluationResult`, `VerificationReport`.
* **1.4 Baseline Security Scanners (Static)**:
  * `SecretScanner`: High-entropy string detection and token formats (AWS keys, GitHub tokens, OpenAI keys, generic secrets).
  * `DangerousExecutionScanner`: AST-based detection of unvalidated `eval`, `exec`, `subprocess.run(shell=True)`.
  * `UnsafeFileOpsScanner`: Path traversal and arbitrary write detection.
* **1.5 Baseline Deterministic Evaluator**:
  * `FileExistenceEvaluator`: Assert generation of mandatory files.
  * `ContentAssertionEvaluator`: Regex / JSON schema verification of agent output artifacts.
  * `DiffBoundaryEvaluator`: Ensure agent edits do not escape authorized subdirectories.
* **1.6 Scoring & Policy Engine**:
  * Weighted risk score calculation (0–100 score).
  * Gate validation based on configurable severity thresholds (`fail_on`).
* **1.7 Reporting**:
  * `TerminalReporter`: Clean CLI formatting with color coding and actionable remediation.
  * `JsonReporter`: Deterministic JSON output for CI parsing.
* **1.8 CLI Commands**:
  * `agentverge scan [path]`: Run security scanners on codebase or agent diffs.
  * `agentverge check [path]`: Run full verification (scanners + behavioral evaluations).
  * `agentverge init`: Generate sample `agentverge.toml` configuration.
* **1.9 Test Suite**:
  * 100% deterministic unit and integration test coverage using `pytest`.

---

## Phase 2: CI/CD Quality Gates & GitHub Integration
* [ ] **SARIF Reporter**: Export findings to standard SARIF v2.1.0 for native GitHub Code Scanning integration.
* [ ] **Git Diff Mode**: Scan only files modified in the current branch or commit (`agentverge scan --diff main`).
* [ ] **Official GitHub Action**: `agentverge/action` providing automated PR scanning, step summary, and status checks.
* [ ] **Inline PR Comments**: Generate formatted GitHub PR review comments highlighting unsafe agent-generated lines.

---

## Phase 3: Tool-Use Safety & MCP Auditing
* [ ] **Tool Call Validator**: Standalone verification of tool invocations prior to agent execution.
* [ ] **MCP Capability Auditor**: Parse and audit Model Context Protocol (MCP) server manifests, detecting dangerous tool definitions, excessive privileges, and unconstrained arguments.
* [ ] **Command & Bash Sandboxing Policy**: Deterministic blacklist/whitelist for shell commands proposed by coding agents.

---

## Phase 4: Agent Behavioral Regression & Benchmarks
* [ ] **Trace & Trajectory Evaluation**: Ingest standardized agent execution traces (e.g., step sequences, tool call histories) and evaluate task completion.
* [ ] **Behavioral Regression Suite**: Run benchmark tasks against multiple agent configurations or prompt revisions to detect capability regressions.
* [ ] **Jailbreak / Prompt Injection Test Kit**: Local-first deterministic suite for testing system prompt resistance to prompt injection.

---

## Phase 5: Policy-as-Code & Advanced Observability
* [ ] **Policy-as-Code Engine**: Declarative policy rules using YAML or OPA/Rego compatibility to define fine-grained agent guardrails.
* [ ] **OpenTelemetry (OTEL) Export**: Export agent evaluation metrics and audit trails to standard observability backends (Grafana, Jaeger, Datadog).
* [ ] **Cost & Latency Estimator**: Compute token usage and cost bounds across multi-turn agent runs.
