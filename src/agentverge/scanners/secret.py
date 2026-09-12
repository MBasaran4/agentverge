"""Secret & Credential Scanner (AV-004 v0.1)."""

import time
from pathlib import Path
from typing import Final

from agentverge.models.context import ProjectContext
from agentverge.models.finding import Finding
from agentverge.models.result import ScanResult
from agentverge.scanners.masking import mask_line_evidence, mask_secret
from agentverge.scanners.patterns import (
    ALL_SECRET_RULES,
    RULE_ENV_CREDENTIAL,
    RULE_GENERIC_API_KEY,
    RULE_PRIVATE_KEY,
    is_false_positive,
)

# Known binary extensions that should be safely bypassed without regex evaluation
KNOWN_BINARY_EXTENSIONS: Final[frozenset[str]] = frozenset(
    {
        ".bin",
        ".dat",
        ".db",
        ".dll",
        ".dylib",
        ".ear",
        ".exe",
        ".gif",
        ".gz",
        ".ico",
        ".jar",
        ".jpeg",
        ".jpg",
        ".pdf",
        ".png",
        ".pyc",
        ".pyd",
        ".pyo",
        ".so",
        ".sqlite",
        ".sqlite3",
        ".tar",
        ".tgz",
        ".ttf",
        ".war",
        ".wasm",
        ".webp",
        ".woff",
        ".woff2",
        ".zip",
        ".7z",
    }
)

DEFAULT_MAX_FILE_SIZE_BYTES: Final[int] = 5_242_880  # 5 MB
BINARY_PROBE_BYTES: Final[int] = 1024


def _is_binary_file(file_path: Path) -> bool:
    """Passively detect if a file is binary without raising exceptions."""
    if file_path.suffix.lower() in KNOWN_BINARY_EXTENSIONS:
        return True

    try:
        with file_path.open("rb") as f:
            chunk = f.read(BINARY_PROBE_BYTES)
            if b"\x00" in chunk:
                return True
    except OSError:
        return True

    return False


def _is_env_file(file_path: Path) -> bool:
    """Check if the given file represents an environment variable configuration file."""
    name = file_path.name.lower()
    return name.startswith(".env") or name.endswith((".env", ".env.local", ".env.production"))


class SecretScanner:
    """Static scanner for detecting exposed secrets and credentials in project files.

    Conforms to the AgentVerge `Scanner` protocol. Ensures all detected secret
    values are strictly redacted so that raw credentials are never persisted into
    `Finding` models, metadata, or output.
    """

    name: str = "Secret & Credential Scanner"
    description: str = "Detects exposed API keys, access tokens, credentials, and private keys."
    scanner_id: str = "secret_scanner"

    def scan(self, context: ProjectContext) -> ScanResult:
        """Execute static secret scanning on all candidate files in the context.

        Args:
            context: Discovered project context containing candidate files and boundaries.

        Returns:
            ScanResult containing safely redacted findings and scan metadata.
        """
        start_time = time.perf_counter()
        findings: list[Finding] = []
        files_scanned = 0

        # Retrieve candidate files from context
        target_files = context.candidate_files
        root_path = context.root_path.resolve()

        for file_path in target_files:
            resolved_path = file_path if file_path.is_absolute() else (root_path / file_path)

            # Skip non-existent files or directories
            if not resolved_path.is_file():
                continue

            # Respect maximum file size
            try:
                if resolved_path.stat().st_size > DEFAULT_MAX_FILE_SIZE_BYTES:
                    continue
            except OSError:
                continue

            # Skip binary files
            if _is_binary_file(resolved_path):
                continue

            # Determine relative path for cleaner finding representation
            try:
                display_path = resolved_path.relative_to(root_path)
            except ValueError:
                display_path = resolved_path

            is_env = _is_env_file(resolved_path)

            try:
                with resolved_path.open("r", encoding="utf-8", errors="replace") as f:
                    files_scanned += 1
                    for line_no, raw_line in enumerate(f, start=1):
                        self._scan_line(
                            line=raw_line,
                            line_no=line_no,
                            display_path=display_path,
                            is_env=is_env,
                            findings=findings,
                        )
            except OSError:
                # File unreadable due to permissions or locking; skip gracefully
                continue

        # Sort findings deterministically by file, line number, and rule ID
        findings.sort(key=lambda f: (str(f.file or ""), f.line or 0, f.id))

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return ScanResult(
            scanner_name=self.name,
            findings=findings,
            files_scanned=files_scanned,
            duration_ms=round(elapsed_ms, 2),
            metadata={
                "scanned_files_count": files_scanned,
                "findings_count": len(findings),
            },
        )

    def _scan_line(
        self,
        line: str,
        line_no: int,
        display_path: Path,
        is_env: bool,
        findings: list[Finding],
    ) -> None:
        """Scan a single line of text against all configured secret rules."""
        stripped = line.strip()
        if not stripped:
            return

        for rule in ALL_SECRET_RULES:
            # Rule restricted to .env files
            if rule.is_env_only and not is_env:
                continue

            # Handle Private Key rule (PEM header detection)
            if rule == RULE_PRIVATE_KEY:
                match = rule.pattern.search(line)
                if match:
                    header = match.group(0).strip()
                    safe_evidence = f"{header}\n[REDACTED KEY MATERIAL]"
                    findings.append(
                        Finding(
                            id=rule.rule_id,
                            title=rule.title,
                            description=rule.description,
                            severity=rule.severity,
                            category=rule.category,
                            file=display_path,
                            line=line_no,
                            evidence=safe_evidence,
                            remediation=rule.remediation,
                        )
                    )
                continue

            # Handle regex matching rules
            for match in rule.pattern.finditer(line):
                # Extract candidate secret string based on rule type
                if rule == RULE_GENERIC_API_KEY:
                    secret_val = match.group(2)
                    secret_start = match.start(2)
                    secret_end = match.end(2)
                elif rule == RULE_ENV_CREDENTIAL:
                    secret_val = match.group(3)
                    secret_start = match.start(3)
                    secret_end = match.end(3)
                else:
                    secret_val = match.group(1)
                    secret_start = match.start(1)
                    secret_end = match.end(1)

                # Evaluate false-positive heuristics
                if is_false_positive(secret_val, line):
                    continue

                # Strictly redact secret before finding creation
                masked_val = mask_secret(secret_val, rule.rule_id)
                safe_evidence = mask_line_evidence(
                    line=line,
                    match_start=secret_start,
                    match_end=secret_end,
                    masked_secret=masked_val,
                )

                findings.append(
                    Finding(
                        id=rule.rule_id,
                        title=rule.title,
                        description=rule.description,
                        severity=rule.severity,
                        category=rule.category,
                        file=display_path,
                        line=line_no,
                        evidence=safe_evidence,
                        remediation=rule.remediation,
                    )
                )
