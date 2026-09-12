# AGENTS.md: Developer Rules for AI Coding Agents

Welcome to **AgentVerge**. As an autonomous or assisted coding agent contributing to this repository, you must adhere strictly to the engineering rules, architectural boundaries, and coding standards outlined below.

---

## 1. Core Mission & Architectural Commandments

1. **Clean Separation Between CLI and Core Logic**:
   * NEVER import CLI modules (`agentverge.cli`), terminal formatters, or CLI argument parsers into `agentverge.core`, `agentverge.scanners`, `agentverge.eval`, or `agentverge.models`.
   * Core modules must be completely operable as a pure Python library without any terminal environment.
2. **Deterministic Core Logic**:
   * Verification must be 100% deterministic and reproducible.
   * NEVER use random number generators without a fixed deterministic seed.
   * NEVER make outbound HTTP/network requests in core scanners or evaluators.
   * NEVER introduce mandatory paid APIs or non-deterministic LLM-as-a-judge calls into core verification.
3. **Strict Domain Boundary**:
   * Do NOT conflate:
     * **Source-code security scanning** (static AST/regex checks on files/diffs)
     * **Agent behavior evaluation** (deterministic assertion of task completion / outputs)
     * **Tool-use safety** (pre-execution tool parameter validation)
     * **Runtime monitoring** (telemetry / traces)
   * Keep each in its designated package.
4. **Strong Typing & Pydantic Models**:
   * All code must be strictly typed using Python 3.10+ type hints (`X | Y`, `list[T]`, etc.).
   * Use Pydantic v2 (`pydantic>=2.0`) for domain models, validation schemas, and configuration models.
   * Domain models representing findings, evaluations, and reports should prefer `frozen=True` where immutability is desired.
5. **Dependency Injection**:
   * Core classes like `VerificationEngine` must accept their components (scanners, evaluators, config) via constructor parameters.
   * Avoid global mutable state or module-level singletons.
6. **Minimal Dependencies**:
   * Do NOT add new dependencies to `pyproject.toml` without explicit necessity.
   * Never introduce cloud SDKs (boto3, azure, etc.), database drivers, or web frameworks into core.
7. **Test-Driven & 100% Testable**:
   * Every scanner, evaluator, and reporter must have accompanying unit tests in `tests/`.
   * Unit tests must execute quickly and reliably without external network dependencies.

---

## 2. Directory Layout Conventions

```text
agentverge/
├── pyproject.toml              # Build & dependency specification
├── src/
│   └── agentverge/
│       ├── __init__.py         # Public library exports
│       ├── cli/                # CLI entry points and argument parsing ONLY
│       ├── core/               # Engine orchestration, registry, scoring
│       ├── models/             # Pydantic domain models (Finding, Severity, Report)
│       ├── discovery/          # File discovery and ProjectContext builder
│       ├── config/             # Configuration schemas and file loaders
│       ├── scanners/           # Static source code security scanners
│       ├── eval/               # Deterministic behavioral evaluators
│       └── reporters/          # Terminal, JSON, and SARIF formatters
└── tests/
    ├── unit/                   # Fast, deterministic unit tests
    └── integration/            # End-to-end CLI and verification tests
```

---

## 3. How to Implement a New Scanner

1. Ensure the scanner implements the `Scanner` protocol:
   ```python
   from agentverge.models import Finding, Severity, SourceLocation
   from agentverge.discovery import ProjectContext

   class MyCustomScanner:
       scanner_id: str = "my-custom-scanner"
       name: str = "My Custom Security Scanner"
       description: str = "Checks for specific unsafe patterns."

       def scan(self, context: ProjectContext) -> list[Finding]:
           findings: list[Finding] = []
           for file_path in context.target_files:
               # Perform static inspection (AST / regex)
               ...
           return findings
   ```
2. Place the scanner in `src/agentverge/scanners/`.
3. Register it in `src/agentverge/scanners/__init__.py`.
4. Add comprehensive unit tests in `tests/unit/scanners/test_my_custom_scanner.py`.

---

## 4. How to Implement a New Evaluator

1. Implement the `Evaluator` protocol:
   ```python
   from agentverge.models import EvaluationResult, EvaluationStatus
   from agentverge.discovery import ProjectContext

   class MyCustomEvaluator:
       evaluator_id: str = "my-custom-evaluator"
       name: str = "Output Verification Evaluator"

       def evaluate(self, context: ProjectContext) -> list[EvaluationResult]:
           results: list[EvaluationResult] = []
           # Deterministic assertions
           ...
           return results
   ```
2. Place the evaluator in `src/agentverge/eval/`.
3. Register it in `src/agentverge/eval/__init__.py`.
4. Add comprehensive unit tests in `tests/unit/eval/test_my_custom_evaluator.py`.

---

## 5. Coding & Style Rules

* **Formatting**: Follow PEP 8 with 4-space indentation.
* **Imports**: Standard library first, then third-party (e.g. `pydantic`), then local `agentverge` imports.
* **Error Handling**: Do not let unhandled exceptions crash the CLI. Scanners should catch file read errors locally, log or emit diagnostic findings, and allow other scanners to complete.
* **Exit Codes**:
  * `0`: Verification passed (all checks green, no findings exceeding threshold).
  * `1`: Verification failed (findings exceeded severity threshold or critical evaluation failed).
  * `2`: Configuration error or invalid arguments.
