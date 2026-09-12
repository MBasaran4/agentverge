# AgentVerge Architectural Decision Records (ADRs)

## ADR-001: Language Choice — Python 3.10+ with Modern Static Typing

### Context
AgentVerge targets AI engineers, agent framework developers, and Python-heavy AI ecosystems (LangChain, AutoGen, CrewAI, LlamaIndex). A lightweight, fast, and familiar language is required for both contributors and end-user adoption.

### Decision
We choose **Python >= 3.10** with full static type annotations (`mypy` / `pyright` strictness). We use modern union syntax (`X | Y`), structural pattern matching where suitable, and avoid legacy compatibility hacks.

### Consequences
* **Positive**: High contributor adoption, direct native parsing of Python ASTs via the standard library `ast` module, rich ecosystem of test tools.
* **Negative**: Slightly higher startup overhead compared to single-binary languages like Go or Rust; mitigated by keeping dependencies minimal to ensure sub-200ms CLI execution.

---

## ADR-002: Domain Model & Schema Layer — Pydantic v2

### Context
We need robust data validation, immutable schema representation, and serialization to and from JSON/dict for findings, configuration, and verification reports.

### Decision
Use **Pydantic v2** (`pydantic>=2.0`) for domain models (`Finding`, `EvaluationResult`, `VerificationReport`, `AgentVergeConfig`). Models are defined with `frozen=True` where appropriate to ensure immutability.

### Consequences
* **Positive**: Fast Rust-backed validation and serialization, standardized JSON schemas, excellent IDE autocompletion, type safety.
* **Negative**: Introduces a core dependency; mitigated because Pydantic v2 is already the standard in modern Python and AI ecosystems.

---

## ADR-003: Decoupling CLI and Core Engine

### Context
If CLI presentation logic, terminal coloring, or argument parsing leaks into core verification logic, AgentVerge cannot be cleanly integrated as a library, pre-commit hook, or automated CI step.

### Decision
Strictly decouple the application into:
* `agentverge.core`: Pure business logic, scanners, evaluators, and reporting data structures. Has zero imports from CLI or terminal formatting libraries.
* `agentverge.cli`: Entry point layer responsible for argument parsing, exit code mapping, and orchestrating reporters.

### Consequences
* **Positive**: 100% testable core without mocking CLI parameters; clean programmatic Python API (`from agentverge import VerificationEngine`).
* **Negative**: Requires maintaining explicit data models between layers, but guarantees long-term maintainability.

---

## ADR-004: Local-First & Zero Mandatory LLM/Cloud APIs for Core Verification

### Context
Many AI evaluation frameworks rely on calling OpenAI or Anthropic LLMs ("LLM-as-a-judge"). This introduces high latency, cost, network flakiness, privacy concerns, and non-deterministic results.

### Decision
The core engine of AgentVerge will be **strictly local-first and deterministic**. Security scanning and behavioral acceptance checks must run offline, without network access, and without requiring any API keys.

### Consequences
* **Positive**: 100% reproducible results, runs in air-gapped CI, zero cost per run, blazing-fast execution, zero privacy leakage.
* **Negative**: Cannot perform subjective or semantic "vibe checks" out-of-the-box; however, subjective evaluations can be added as optional plugins in later phases.

---

## ADR-005: Strict Boundary Between Verification Domains

### Context
AI tooling frequently conflates code linting, runtime tracing, tool sandboxing, and prompt evaluation into a single unstructured pipeline, causing confusion and fragile architecture.

### Decision
Explicitly separate:
1. **Source-Code Security Scan**: Static analysis of generated code/diffs.
2. **Agent Behavior Evaluation**: Deterministic assertion of task results against requirements.
3. **Tool-Use Safety**: Pre-execution contract and parameter safety.
4. **Runtime Monitoring**: Telemetry and trace supervision (deferred to Phase 5).

### Consequences
* **Positive**: Clear responsibilities, distinct inputs and outputs, independent maintainability and testing.
* **Negative**: None; provides architectural clarity.

---

## ADR-006: Protocol-Based Plugin Architecture

### Context
We want external developers to write custom scanners or evaluation checks without being forced to inherit from rigid base classes or depend on complex plugin managers.

### Decision
Use Python's standard `typing.Protocol` with `@runtime_checkable` to define `Scanner` and `Evaluator` interfaces. Plugin discovery uses standard Python `importlib.metadata.entry_points`.

### Consequences
* **Positive**: Duck typing with static verification; third-party packages can implement checks without tight coupling; easy testing.
* **Negative**: Runtime type checks must be validated via protocol checkers.

---

## ADR-007: Minimal External Dependencies

### Context
Bloated dependencies lead to version conflicts, slow installations, and security vulnerabilities.

### Decision
For the MVP, dependencies are kept strictly to:
* `pydantic>=2.0` (Domain models & config)
* `tomli` / `tomllib` (TOML configuration loading)
* `click` or `typer` (CLI parsing)
* `pytest` (Testing - dev only)

No cloud SDKs, no databases, no heavy web frameworks.
