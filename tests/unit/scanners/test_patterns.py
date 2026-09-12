"""Unit tests for secret detection regex patterns and false-positive filtering."""

from agentverge.scanners.patterns import (
    RULE_AWS_ACCESS_KEY,
    RULE_ENV_CREDENTIAL,
    RULE_GENERIC_API_KEY,
    RULE_GITHUB_TOKEN,
    RULE_PRIVATE_KEY,
    is_false_positive,
)


def test_aws_access_key_rule_matches() -> None:
    """Verify AWS access key pattern matches AKIA and ASIA keys."""
    line = 'aws_key = "AKIA1234567890ABCDEF"'
    match = RULE_AWS_ACCESS_KEY.pattern.search(line)
    assert match is not None
    assert match.group(1) == "AKIA1234567890ABCDEF"

    asia_line = "ASIA9876543210FEDCBA"
    match_asia = RULE_AWS_ACCESS_KEY.pattern.search(asia_line)
    assert match_asia is not None
    assert match_asia.group(1) == "ASIA9876543210FEDCBA"


def test_github_token_rule_matches() -> None:
    """Verify GitHub token pattern matches personal access tokens."""
    line = "token = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'"
    match = RULE_GITHUB_TOKEN.pattern.search(line)
    assert match is not None
    assert match.group(1) == "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890"

    pat_line = (
        "export GITHUB_TOKEN="
        "github_pat_11AAAAAAA_bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    )
    match_pat = RULE_GITHUB_TOKEN.pattern.search(pat_line)
    assert match_pat is not None
    assert match_pat.group(1).startswith("github_pat_")


def test_private_key_rule_matches() -> None:
    """Verify private key rule matches various PEM headers."""
    headers = [
        "-----BEGIN PRIVATE KEY-----",
        "-----BEGIN RSA PRIVATE KEY-----",
        "-----BEGIN EC PRIVATE KEY-----",
        "-----BEGIN OPENSSH PRIVATE KEY-----",
    ]
    for header in headers:
        assert RULE_PRIVATE_KEY.pattern.search(header) is not None


def test_generic_api_key_rule_matches() -> None:
    """Verify generic API key assignment matches key-value pairs."""
    line = 'api_key = "SYNTHETIC_TEST_SECRET_VALUE_987654321"'
    match = RULE_GENERIC_API_KEY.pattern.search(line)
    assert match is not None
    assert match.group(2) == "SYNTHETIC_TEST_SECRET_VALUE_987654321"

    token_line = 'secret_key: "abcdef1234567890abcdef123456"'
    match_token = RULE_GENERIC_API_KEY.pattern.search(token_line)
    assert match_token is not None
    assert match_token.group(2) == "abcdef1234567890abcdef123456"


def test_env_credential_rule_matches() -> None:
    """Verify .env credential assignment matches environment declarations."""
    line = 'DATABASE_PASSWORD="super_secret_db_pass_123"'
    match = RULE_ENV_CREDENTIAL.pattern.search(line)
    assert match is not None
    assert match.group(1) == "DATABASE_PASSWORD"
    assert match.group(3) == "super_secret_db_pass_123"


def test_false_positive_placeholders() -> None:
    """Verify common placeholders are identified as false positives."""
    assert is_false_positive("YOUR_API_KEY_HERE", "api_key = 'YOUR_API_KEY_HERE'") is True
    assert is_false_positive("CHANGE_ME", "password = 'CHANGE_ME'") is True
    assert is_false_positive("REPLACE_ME", "secret = 'REPLACE_ME'") is True
    assert is_false_positive("example_api_key_value", "key: example_api_key_value") is True
    assert is_false_positive("DUMMY_TOKEN_VALUE", "token = 'DUMMY_TOKEN_VALUE'") is True
    assert is_false_positive("AKIAIOSFODNN7EXAMPLE", "AWS_KEY = AKIAIOSFODNN7EXAMPLE") is True


def test_false_positive_variables() -> None:
    """Verify environment variable references are identified as false positives."""
    assert is_false_positive("${API_KEY}", 'api_key = "${API_KEY}"') is True
    assert is_false_positive("{{ secrets.GH_TOKEN }}", "token: '{{ secrets.GH_TOKEN }}'") is True
    assert is_false_positive("$MY_SECRET", 'auth = "$MY_SECRET"') is True


def test_false_positive_repetitive_characters() -> None:
    """Verify low-diversity dummy strings are identified as false positives."""
    assert is_false_positive("00000000000000000000", 'key = "00000000000000000000"') is True
    assert is_false_positive("xxxxxxxxxxxxxxxxxxxx", 'key = "xxxxxxxxxxxxxxxxxxxx"') is True


def test_genuine_secrets_not_flagged_as_false_positive() -> None:
    """Verify genuine high-entropy keys are recognized as real secrets."""
    assert (
        is_false_positive(
            "AKIA1234567890ABCDEF",
            'aws_key = "AKIA1234567890ABCDEF"',
        )
        is False
    )
    assert (
        is_false_positive(
            "ghp_123456789012345678901234567890123456",
            'token = "ghp_123456789012345678901234567890123456"',
        )
        is False
    )
