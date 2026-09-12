"""Detection rule patterns, metadata definitions, and false-positive heuristics."""

import re
from dataclasses import dataclass
from typing import Final

from agentverge.models.finding import Severity

# Set of placeholder substrings indicating non-secret template/example values (case-insensitive)
PLACEHOLDER_SUBSTRINGS: Final[tuple[str, ...]] = (
    "YOUR_",
    "CHANGE_ME",
    "CHANGEME",
    "REPLACE_ME",
    "EXAMPLE",
    "DUMMY",
    "SAMPLE",
    "TEST_KEY",
    "INSERT_",
    "PLACEHOLDER",
    "MY_KEY",
    "MY_SECRET",
    "MY_TOKEN",
    "AKIAIOSFODNN7EXAMPLE",  # Official AWS documentation example key
    "00000000",
    "XXXXXXXX",
)

# Variable reference prefixes that indicate template variables rather than hardcoded credentials
VARIABLE_INDICATORS: Final[tuple[str, ...]] = (
    "${",
    "{{",
    "$",
    "process.env",
    "os.environ",
    "os.getenv",
    "System.getenv",
    "env(",
)


@dataclass(frozen=True)
class SecretRule:
    """Specification of a deterministic secret detection rule."""

    rule_id: str
    title: str
    description: str
    severity: Severity
    category: str
    remediation: str
    pattern: re.Pattern[str]
    is_env_only: bool = False


# High-confidence detection rules for v0.1
RULE_AWS_ACCESS_KEY: Final[SecretRule] = SecretRule(
    rule_id="AGENTVERGE-SECRET-AWS-001",
    title="Exposed AWS Access Key ID",
    description="A plaintext AWS Access Key ID was detected in source code or configuration.",
    severity=Severity.CRITICAL,
    category="secrets",
    remediation=(
        "Immediately revoke and rotate this key in the AWS IAM Console. "
        "Never commit credentials to version control."
    ),
    pattern=re.compile(r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b"),
)

RULE_GITHUB_TOKEN: Final[SecretRule] = SecretRule(
    rule_id="AGENTVERGE-SECRET-GITHUB-001",
    title="Exposed GitHub Personal Access Token",
    description="A plaintext GitHub Personal Access Token or credential token was detected.",
    severity=Severity.CRITICAL,
    category="secrets",
    remediation=(
        "Revoke this token immediately via GitHub Developer Settings "
        "and generate a replacement stored in environment secrets."
    ),
    pattern=re.compile(r"\b(gh[pousr]_[A-Za-z0-9_]{36,255}|github_pat_[A-Za-z0-9_]{82})\b"),
)

RULE_PRIVATE_KEY: Final[SecretRule] = SecretRule(
    rule_id="AGENTVERGE-SECRET-PRIVATE-KEY-001",
    title="Exposed Private Encryption Key",
    description="Private key material was detected in repository files.",
    severity=Severity.CRITICAL,
    category="secrets",
    remediation=(
        "Remove the private key file from version control immediately "
        "and re-issue cryptographic key pairs."
    ),
    pattern=re.compile(r"-----\s*BEGIN\s+(?:[A-Z0-9_-]+\s+)?PRIVATE\s+KEY\s*-----", re.IGNORECASE),
)

RULE_GENERIC_API_KEY: Final[SecretRule] = SecretRule(
    rule_id="AGENTVERGE-SECRET-GENERIC-API-KEY-001",
    title="Hardcoded API Key / Secret Assignment",
    description=(
        "A credential assignment matching generic API key or secret token patterns was detected."
    ),
    severity=Severity.HIGH,
    category="secrets",
    remediation=(
        "Extract hardcoded credentials to environment variables or an external secret store."
    ),
    pattern=re.compile(
        r"""(?i)\b(api[_-]?key|api[_-]?token|access[_-]?token|secret[_-]?key|client[_-]?secret)\s*[:=]\s*['"]([a-zA-Z0-9_\-]{20,80})['"]"""
    ),
)

RULE_ENV_CREDENTIAL: Final[SecretRule] = SecretRule(
    rule_id="AGENTVERGE-SECRET-ENV-CRED-001",
    title="Exposed Credential in Environment File",
    description=(
        "A credential-looking assignment matching a high-confidence secret pattern "
        "was detected in an environment configuration file."
    ),
    severity=Severity.HIGH,
    category="secrets",
    remediation=(
        "Add .env files to .gitignore and use template files (e.g. .env.example) "
        "without real secrets."
    ),
    pattern=re.compile(
        r"""^\s*(?:export\s+)?([A-Z0-9_]*(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|AUTH)[A-Z0-9_]*)\s*=\s*(['"]?)([^#\s\r\n"']{8,})\2"""
    ),
    is_env_only=True,
)

# Registry of active v0.1 rules
ALL_SECRET_RULES: Final[tuple[SecretRule, ...]] = (
    RULE_AWS_ACCESS_KEY,
    RULE_GITHUB_TOKEN,
    RULE_PRIVATE_KEY,
    RULE_GENERIC_API_KEY,
    RULE_ENV_CREDENTIAL,
)


def is_false_positive(value: str, context_line: str) -> bool:
    """Determine if a matched secret value is an obvious false positive or placeholder.

    Args:
        value: The matched potential secret string.
        context_line: The full unredacted line context.

    Returns:
        True if the candidate matches known placeholder or variable patterns;
        False if it should be flagged as a genuine finding.
    """
    stripped_val = value.strip().strip("'\"`")
    if not stripped_val:
        return True

    upper_val = stripped_val.upper()

    # 1. Check placeholder substrings
    for placeholder in PLACEHOLDER_SUBSTRINGS:
        if placeholder in upper_val:
            return True

    # 2. Check variable references and interpolation in value or line context
    stripped_line = context_line.strip()
    for indicator in VARIABLE_INDICATORS:
        if stripped_val.startswith(indicator):
            return True

    # If the value is purely a template interpolation like ${FOO} or {{BAR}}
    if stripped_val.startswith("${") and stripped_val.endswith("}"):
        return True
    if stripped_val.startswith("{{") and stripped_val.endswith("}}"):
        return True

    # 3. Check for low-diversity dummy strings (<= 2 distinct characters)
    if len(stripped_val) >= 8 and len(set(stripped_val.lower())) <= 2:
        return True

    # 4. Pure comments without actual credentials (e.g., `# TODO: api_key goes here`)
    return bool(
        (stripped_line.startswith("#") or stripped_line.startswith("//"))
        and ("TODO" in stripped_line.upper() or "FIXME" in stripped_line.upper())
        and not stripped_val.startswith(("AKIA", "ASIA", "ghp_", "gho_", "ghu_", "ghs_", "ghr_"))
    )
