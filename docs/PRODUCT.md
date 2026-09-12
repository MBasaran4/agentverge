# AgentVerge Product Specification

## 1. Vision & Mission

**AgentVerge** is an open-source, local-first verification infrastructure for autonomous AI agents and AI-generated code.

As software engineering increasingly shifts toward autonomous agents (coding agents, multi-agent frameworks, PR-generating bots, and MCP-integrated toolchains), developers face an unprecedented trust gap:
* How do we ensure agent-generated code does not introduce security vulnerabilities or secrets?
* How do we guarantee an agent completed its assigned task correctly without hallucinating success?
* How do we prevent destructive or malicious tool calls before they run?
* How do we catch behavioral regressions across agent model updates or system prompt revisions?

AgentVerge solves this by providing a unified, deterministic, and privacy-preserving verification pipeline that acts as a quality and security gate for agents—both locally during development and in automated CI/CD environments.

---

## 2. Core Principles & Philosophy

* **Open-Source & Transparent**: Fully open-source under a permissive license (MIT), with no hidden enterprise paywalls in core verification features.
* **Local-First & Privacy-Friendly**: Runs entirely on the developer's workstation or private CI runner. Never transmits proprietary code, prompts, or traces to third parties.
* **Framework-Agnostic**: Operates independently of underlying agent frameworks (LangChain, AutoGen, CrewAI, Claude Code, Cursor, custom agents, etc.).
* **Zero Mandatory Paid APIs**: Does not require proprietary LLM API keys for core verification, scanning, or evaluation. Uses deterministic static analysis, schema validation, and formal assertions.
* **CLI-First & CI/CD-Ready**: Intuitive terminal UX with standard exit codes, SARIF/JSON outputs, and seamless GitHub Actions integration.
* **Extensible & Modular**: Pluggable architecture allowing contributors to build custom scanners, behavioral assertions, and agent adapters easily.
* **Lean Architecture**: Minimal external dependencies, fast startup time (< 200ms), and no mandatory databases or heavy background services for core execution.

---

## 3. Product Domains: The Four Pillars

A central architectural requirement is to never conflate the four distinct operational domains of agent verification:

```
+-------------------------------------------------------------------------------+
|                                AGENTVERGE                                     |
+----------------------+--------------------+-------------------+---------------+
|  1. Source-Code      | 2. Agent Behavior  | 3. Tool-Use       | 4. Runtime    |
|     Security Scan    |    Evaluation      |    Safety         |    Monitoring |
| (Static / Artifact)  | (Task & Traces)    | (Pre-execution)   | (Telemetry)   |
+----------------------+--------------------+-------------------+---------------+
```

### Pillar 1: Source-Code Security Scanning
* **Focus**: The static artifacts (files, diffs, PR patches) produced by the agent.
* **Mechanism**: AST analysis, regex pattern matching, semantic pattern rules, dependency vulnerability checks.
* **Examples**: Detection of hardcoded API keys, shell injection (`subprocess.run(..., shell=True)`), insecure deserialization, dangerous file operations, path traversals.

### Pillar 2: Agent Behavior Evaluation
* **Focus**: The reasoning trajectory, task completion fidelity, and behavioral consistency of the agent.
* **Mechanism**: Deterministic assertion suites, golden dataset comparisons, goal satisfaction checks, jailbreak/prompt injection robustness checks.
* **Examples**: Verifying that an agent tasked with fixing an issue actually added a test, modified only the allowed files, and satisfied deterministic acceptance criteria.

### Pillar 3: Tool-Use Safety
* **Focus**: The actions, function calls, and MCP invocations an agent attempts to execute.
* **Mechanism**: Schema validation, parameter boundary checking, destructive command pattern matching, sandbox policy enforcement.
* **Examples**: Intercepting or evaluating tool calls like `execute_bash("rm -rf /")` or SQL drop statements before execution occurs.

### Pillar 4: Runtime Monitoring & Observability *(Future / Post-MVP)*
* **Focus**: In-flight telemetry, step counts, token usage, loop detection, and multi-agent message routing.
* **Mechanism**: OpenTelemetry-compatible traces, streaming event listeners, watchdog timeouts.
* **Note**: Deliberately segregated from static scanning and deterministic evaluation to keep the core engine lightweight and deterministic.

---

## 4. Long-Term Product Scope (10 Areas)

1. **Security Scanning**: Static analysis of generated code, diffs, and prompts for security flaws and secrets.
2. **Agent Behavior Evaluation**: Framework-agnostic assertion testing, benchmark runs, and functional verification.
3. **Tool-Use Safety**: Policy enforcement on tool arguments, MCP calls, file system modifications, and network access.
4. **Behavioral Regression Detection**: Comparing agent performance across prompt revisions, model upgrades, and code changes.
5. **CI/CD Quality Gates**: Automated pass/fail enforcement in CI pipelines with customizable thresholds.
6. **GitHub Integration**: PR review bot, status checks, inline annotations, and SARIF upload.
7. **Agent Observability**: Standardized event logging, span tracing, and execution replay analysis.
8. **Cost and Performance Analysis**: Token consumption tracking, latency profiling, and cost estimation per task.
9. **MCP Security/Evaluation**: Formal auditing and permission vetting for Model Context Protocol (MCP) servers and tool schemas.
10. **Policy-as-Code**: Declarative rule definitions (YAML/Python DSL) to govern what an agent can read, write, or call.

---

## 5. MVP Scope vs Non-MVP Scope

### In Scope for MVP:
* **Project Discovery**: Automatic detection of project structure, agent configurations, and target files.
* **Configuration Loading**: Parsing `agentverge.toml` / `pyproject.toml` configuration with sensible defaults.
* **Finding Model & Severity**: Typed Pydantic models for findings (`RuleId`, `Severity`, `Location`, `Recommendation`).
* **Built-in Security Checks**: Baseline static scanners (hardcoded secrets, unsafe shell/exec calls, dangerous file writes).
* **Deterministic Evaluation Foundation**: Base assertion engine for checking task outputs, expected files, and state diffs.
* **Scoring Engine**: Standardized risk score and compliance pass/fail calculation.
* **Terminal Report**: Rich, readable terminal output with color-coded severity and remediation guidance.
* **JSON Report**: Machine-readable JSON output for CI pipeline integration.
* **CLI Interface**: Clean CLI command structure (`agentverge scan`, `agentverge check`, `agentverge init`).
* **Test Suite**: Comprehensive pytest test suite with 100% deterministic tests.

### Explicitly Excluded from MVP (Later Phases):
* React / Web Dashboard
* Cloud backend / SaaS infrastructure
* Database dependencies (PostgreSQL, SQLite, Redis)
* Non-deterministic LLM-as-a-judge evaluation
* MCP runtime interception / dynamic proxy
* Live runtime agent process interception / sandboxing daemon
* User authentication and RBAC
