# AgentVerge Threat Model

## 1. System Context & Trust Boundaries

AgentVerge operates at the boundary between autonomous AI agents (untrusted or semi-trusted code generators) and production environments (trusted repositories and execution infrastructure).

```
   [Untrusted / Semi-Trusted Domain]
           +---------------------------------------+
           |  Autonomous Agent / LLM Generator    |
           +---------------------------------------+
                              |
                     Generates Code / Diffs / Tool Invocations
                              |
   ===========================V===========================  [Trust Boundary]
   [AgentVerge Verification Layer]
     * Discovery & Context Isolation
     * Static AST & Secret Scanners
     * Deterministic Assertion Evaluators
     * Policy Gate Enforcement
   ===========================|===========================  [Trust Boundary]
                              |
                   Safe Verification Verdict & Artifacts
                              V
   [Trusted Domain: Developer Workstation / CI Runner / Production Repo]
```

---

## 2. Threat Catalog

### Threat T1: Malicious / Hallucinated Code Injected into Production
* **Description**: An AI coding agent introduces remote code execution (RCE), arbitrary file modification, or insecure deserialization (either through model hallucination or indirect prompt injection).
* **Severity**: Critical
* **AgentVerge Defense**:
  * AST-based static scanners detect dangerous standard library calls (`exec`, `eval`, `subprocess.run(shell=True)`).
  * Path traversal scanners detect unconstrained filesystem access (`open(path)` with user inputs).
  * Policy gate immediately rejects PR/commit if critical findings are detected.

### Threat T2: Secrets & Credential Leakage in Generated Artifacts
* **Description**: Agent embeds hardcoded API keys, private tokens, or test credentials directly into source files, unit tests, or configuration artifacts.
* **Severity**: High / Critical
* **AgentVerge Defense**:
  * Entropy analysis combined with curated regex patterns for known cloud providers (AWS, GitHub, OpenAI, Anthropic, generic JWTs/tokens).
  * High-precision pattern matching to avoid noisy false positives while ensuring zero critical leaks.

### Threat T3: Destructive or Unauthorized Tool Invocations
* **Description**: Agent proposes or invokes tool calls that perform destructive actions (e.g., `rm -rf`, schema drops) or escape designated directories.
* **Severity**: Critical
* **AgentVerge Defense**:
  * Pre-execution tool call validation schema.
  * Deterministic directory boundary evaluator (`DiffBoundaryEvaluator`) verifying that changed files remain within the authorized project subtree.

### Threat T4: Indirect Prompt Injection via Context Files
* **Description**: Malicious repository files (READMEs, issue templates, third-party libraries) inject instructions that trick coding agents into introducing backdoors or bypassing security.
* **Severity**: High
* **AgentVerge Defense**:
  * AgentVerge evaluates the *resultant code and artifacts*, not the intent of the prompt. Even if an agent is tricked by prompt injection, the resulting dangerous code (e.g. outbound sockets, shell executions) is caught by static scanners.

### Threat T5: Scanner Evasion via Code Obfuscation
* **Description**: Agent or malicious PR author obscures dangerous calls (e.g., `getattr(__builtins__, 'ex' + 'ec')(...)` or base64 decoding).
* **Severity**: Medium / High
* **AgentVerge Defense**:
  * Python AST (Abstract Syntax Tree) traversal instead of pure regex matching.
  * Flagging dynamic code execution patterns (`getattr`, `importlib.import_module` with dynamic inputs, obfuscated base64 decoders).

### Threat T6: Denial of Service / Resource Exhaustion of Verifier
* **Description**: Verifier is targeted by massive files, deeply nested ASTs, or catastrophic backtracking regular expressions (ReDoS).
* **Severity**: Medium
* **AgentVerge Defense**:
  * Configurable file size limits (default 5MB max per scanned file).
  * Non-backtracking or pre-compiled atomic regex patterns.
  * AST parsing timeouts and defensive recursion depth limits.

---

## 3. Defense-in-Depth Summary Matrix

| Threat | Primary Layer | Secondary Layer | Fallback / Policy |
| :--- | :--- | :--- | :--- |
| **T1 (Insecure Code)** | AST Dangerous Scanner | Diff Boundary Evaluator | Zero-tolerance CI exit code |
| **T2 (Secret Leak)** | Regex & Entropy Scanner | Git Diff Scanner | Masked findings in terminal output |
| **T3 (Destructive Tool)** | Diff Boundary Evaluator | Pre-execution schema audit | Failure gate |
| **T4 (Indirect Injection)** | Static code AST scan | Acceptance assertions | Deterministic check failure |
| **T5 (Obfuscation)** | AST visitor for dynamic builtins | Severity escalation | Flag as suspicious for manual review |
| **T6 (Resource Exhaustion)** | File size & depth bounds | Pre-compiled regex | Skip oversized file with warning |
