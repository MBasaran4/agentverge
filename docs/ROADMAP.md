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

* **1.1 Project Discovery & Context** `[x] Implemented in v0.1.0`:
  * Directory walker with `.gitignore` and pattern exclusion support.
  * Discovers source files, AI agent instructions (`AGENTS.md`, `CLAUDE.md`, `.cursorrules`), and MCP configs.
  * Builds immutable `ProjectContext`.
* **1.2 Configuration Subsystem** `[x] Implemented in v0.1.0`:
  * `AgentVergeConfig` loader supporting `pyproject.toml` and `.agentverge.yml` / `.agentverge.yaml`.
  * Sensible zero-config defaults (scans current working directory).
* **1.3 Core Domain Models** `[x] Implemented in v0.1.0`:
  * Pydantic v2 models: `Severity`, `Finding`, `EvaluationStatus`, `EvaluationResult`, `ScanResult`, `VerificationReport`.
* **1.4 Baseline Security Scanners (Static)**:
  * [x] `SecretScanner` *(v0.1.0)*: High-confidence token format and pattern detection (AWS keys, GitHub tokens, private keys, generic credentials, `.env` file secrets) with strict masking.
  * [ ] `DangerousExecutionScanner` *(Planned v0.2.0)*: AST-based detection of unvalidated `eval`, `exec`, `subprocess.run(shell=True)`.
  * [ ] `UnsafeFileOpsScanner` *(Planned v0.2.0)*: Path traversal and arbitrary write detection.
* **1.5 Baseline Deterministic Evaluator** *(Planned v0.2.0)*:
  * [ ] `FileExistenceEvaluator`: Assert generation of mandatory files.
  * [ ] `ContentAssertionEvaluator`: Regex / JSON schema verification of agent output artifacts.
  * [ ] `DiffBoundaryEvaluator`: Ensure agent edits do not escape authorized subdirectories.
* **1.6 Scoring & Policy Engine**:
  * [x] Policy threshold validation (`fail_on = ["high", "critical"]`) *(v0.1.0)*.
  * [ ] Weighted risk score calculation (0–100 score) *(Planned v0.2.0)*.
* **1.7 Reporting**:
  * [x] Rich terminal diagnostic output with color coding and remediation advice *(v0.1.0)*.
  * [ ] `JsonReporter` & SARIF output for CI parsing *(Planned v0.2.0)*.
* **1.8 CLI Commands**:
  * [x] `agentverge scan [path]`: Run security scanners on codebase or target directories *(v0.1.0)*.
  * [x] `agentverge check [path]`: Inspect project layout and discovered AI context *(v0.1.0)*.
  * [ ] `agentverge init`: Generate sample `agentverge.yml` configuration *(Planned v0.2.0)*.
* **1.9 Test Suite** `[x] Implemented in v0.1.0`:
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
