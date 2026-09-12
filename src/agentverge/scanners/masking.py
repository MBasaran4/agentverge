"""Deterministic secret masking and safe evidence generation."""

import re

MAX_EVIDENCE_LINE_LENGTH: int = 200

# Private key PEM pattern to detect header
_PEM_HEADER_REGEX: re.Pattern[str] = re.compile(
    r"^-----\s*BEGIN\s+(?:[A-Z0-9_-]+\s+)?PRIVATE\s+KEY\s*-----$", re.IGNORECASE
)


def mask_secret(secret: str, rule_id: str | None = None) -> str:
    """Mask a detected secret string safely and deterministically.

    Never exposes plaintext secret material. Preserves safe structural prefixes
    (e.g. 'AKIA', 'ghp_') where useful for triage while completely replacing
    sensitive credential material with asterisks.

    Args:
        secret: The raw credential match.
        rule_id: Optional rule identifier to inform prefix handling.

    Returns:
        A safely redacted string.
    """
    secret = secret.strip()
    if not secret:
        return "********"

    # Private key header handling
    if _PEM_HEADER_REGEX.match(secret):
        return f"{secret}\n[REDACTED KEY MATERIAL]"

    # AWS Access Key IDs (AKIA / ASIA followed by 16 alphanumeric characters)
    if secret.startswith(("AKIA", "ASIA")) and len(secret) == 20:
        return f"{secret[:4]}{'*' * 16}"

    # GitHub token prefixes
    if secret.startswith("github_pat_"):
        prefix = "github_pat_"
        return f"{prefix}{'*' * max(16, len(secret) - len(prefix))}"
    for gh_prefix in ("ghp_", "gho_", "ghu_", "ghs_", "ghr_"):
        if secret.startswith(gh_prefix):
            return f"{gh_prefix}{'*' * max(16, len(secret) - len(gh_prefix))}"

    # Short secret values (<= 8 chars): fully redact
    if len(secret) <= 8:
        return "*" * len(secret)

    # Generic long secrets: keep first 4 chars prefix, redact the rest
    prefix_len = 4
    return f"{secret[:prefix_len]}{'*' * (len(secret) - prefix_len)}"


def mask_line_evidence(
    line: str,
    match_start: int,
    match_end: int,
    masked_secret: str,
    max_length: int = MAX_EVIDENCE_LINE_LENGTH,
) -> str:
    """Generate safe, redacted single-line evidence for a finding.

    Replaces the raw match span with the masked string and bounds overall
    line length to avoid log bloat.

    Args:
        line: The full unredacted source code line.
        match_start: Starting 0-indexed column of the secret in line.
        match_end: Ending 0-indexed column of the secret in line.
        masked_secret: Pre-masked secret replacement string.
        max_length: Maximum allowed output string length.

    Returns:
        Redacted single line evidence snippet.
    """
    # Replace matched span with masked representation
    safe_line = line[:match_start] + masked_secret + line[match_end:]
    # Strip line endings
    safe_line = safe_line.rstrip("\r\n")

    if len(safe_line) <= max_length:
        return safe_line

    # If exceeding max_length, center truncation window around the masked secret
    new_secret_start = match_start
    new_secret_end = match_start + len(masked_secret)

    if new_secret_end <= max_length - 3:
        return safe_line[: max_length - 3] + "..."

    # Center window around the masked portion
    half_window = (max_length - len(masked_secret) - 6) // 2
    start_cut = max(0, new_secret_start - max(10, half_window))
    end_cut = min(len(safe_line), new_secret_end + max(10, half_window))

    snippet = safe_line[start_cut:end_cut]
    if start_cut > 0:
        snippet = "..." + snippet
    if end_cut < len(safe_line):
        snippet = snippet + "..."

    return snippet
