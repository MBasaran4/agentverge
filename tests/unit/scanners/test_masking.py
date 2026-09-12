"""Unit tests for secret redaction and masking logic."""

from agentverge.scanners.masking import mask_line_evidence, mask_secret


def test_mask_aws_access_key() -> None:
    """Verify AWS access keys retain AKIA prefix and redact remaining 16 chars."""
    fake_key = "AKIA1234567890ABCDEF"
    masked = mask_secret(fake_key)

    assert masked == "AKIA****************"
    assert len(masked) == 20
    # Invariant: raw secret never leaks
    assert fake_key not in masked
    assert "1234567890ABCDEF" not in masked


def test_mask_asia_access_key() -> None:
    """Verify temporary ASIA access keys retain ASIA prefix and redact remaining 16 chars."""
    fake_key = "ASIA9876543210FEDCBA"
    masked = mask_secret(fake_key)

    assert masked == "ASIA****************"
    assert len(masked) == 20
    assert fake_key not in masked


def test_mask_github_tokens() -> None:
    """Verify GitHub tokens retain prefix and redact remainder."""
    ghp = "ghp_123456789012345678901234567890123456"
    masked_ghp = mask_secret(ghp)
    assert masked_ghp.startswith("ghp_")
    assert "123456789012345678901234567890123456" not in masked_ghp
    assert ghp not in masked_ghp

    pat = "github_pat_11ABCDE_999999999999999999999999999999999999999999999999999999999999999"
    masked_pat = mask_secret(pat)
    assert masked_pat.startswith("github_pat_")
    assert "11ABCDE" not in masked_pat
    assert pat not in masked_pat


def test_mask_private_key_header() -> None:
    """Verify private key PEM header is preserved and key material is redacted."""
    header = "-----BEGIN RSA PRIVATE KEY-----"
    masked = mask_secret(header)

    assert "-----BEGIN RSA PRIVATE KEY-----" in masked
    assert "[REDACTED KEY MATERIAL]" in masked


def test_mask_generic_secrets() -> None:
    """Verify generic secrets are safely redacted based on length."""
    # Short secret <= 8
    short_secret = "pass123"
    assert mask_secret(short_secret) == "*******"
    assert short_secret not in mask_secret(short_secret)

    # Long secret > 8
    long_secret = "super_secret_token_value_98765"
    masked_long = mask_secret(long_secret)
    assert masked_long.startswith("supe")
    assert "secret_token_value_98765" not in masked_long
    assert long_secret not in masked_long


def test_mask_line_evidence_replaces_secret() -> None:
    """Verify line evidence replaces raw match with masked secret."""
    raw_line = 'API_KEY = "SYNTHETIC_TEST_SECRET_VALUE_987654321"'
    secret_val = "SYNTHETIC_TEST_SECRET_VALUE_987654321"
    start = raw_line.index(secret_val)
    end = start + len(secret_val)

    masked_val = mask_secret(secret_val)
    evidence = mask_line_evidence(raw_line, start, end, masked_val)

    assert secret_val not in evidence
    assert masked_val in evidence
    assert 'API_KEY = "' in evidence


def test_mask_line_evidence_bounds_length() -> None:
    """Verify exceedingly long lines are clamped with ellipsis without exposing secret."""
    long_prefix = "x" * 250
    secret_val = "AKIA1111222233334444"
    line = f"{long_prefix} AWS_KEY={secret_val} suffix"
    start = line.index(secret_val)
    end = start + len(secret_val)

    masked_val = mask_secret(secret_val)
    evidence = mask_line_evidence(line, start, end, masked_val, max_length=100)

    assert len(evidence) <= 100
    assert secret_val not in evidence
    assert masked_val in evidence
