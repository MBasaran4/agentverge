"""Unit tests for the configuration loading subsystem."""

from pathlib import Path

import pytest

from agentverge.config.loader import (
    ConfigurationError,
    load_config,
)
from agentverge.models.config import AgentVergeConfig


def test_default_config_fallback(tmp_path: Path) -> None:
    """Verify default configuration is returned when no config file exists."""
    config, loaded_path = load_config(root_path=tmp_path)

    assert isinstance(config, AgentVergeConfig)
    assert loaded_path is None
    assert config.version == "1"
    assert ".git" in config.exclude_patterns


def test_load_agentverge_yml(tmp_path: Path) -> None:
    """Verify loading from .agentverge.yml."""
    yml_file = tmp_path / ".agentverge.yml"
    yml_file.write_text(
        """
version: "1"
exclude:
  - "custom_build"
  - "temp"
thresholds:
  fail_on:
    - "critical"
""",
        encoding="utf-8",
    )

    config, loaded_path = load_config(root_path=tmp_path)

    assert loaded_path == yml_file
    assert config.exclude_patterns == ["custom_build", "temp"]
    assert config.thresholds.fail_on == ["critical"]


def test_load_agentverge_yaml(tmp_path: Path) -> None:
    """Verify loading from .agentverge.yaml."""
    yaml_file = tmp_path / ".agentverge.yaml"
    yaml_file.write_text(
        """
version: "1"
exclude_patterns:
  - "dist"
""",
        encoding="utf-8",
    )

    config, loaded_path = load_config(root_path=tmp_path)

    assert loaded_path == yaml_file
    assert config.exclude_patterns == ["dist"]


def test_load_pyproject_toml_tool_section(tmp_path: Path) -> None:
    """Verify loading configuration from [tool.agentverge] in pyproject.toml."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "my-project"

[tool.agentverge]
exclude_patterns = ["tests/fixtures"]

[tool.agentverge.thresholds]
fail_on = ["high"]
""",
        encoding="utf-8",
    )

    config, loaded_path = load_config(root_path=tmp_path)

    assert loaded_path == pyproject
    assert config.exclude_patterns == ["tests/fixtures"]
    assert config.thresholds.fail_on == ["high"]


def test_config_precedence_yml_over_yaml_and_pyproject(tmp_path: Path) -> None:
    """Verify .agentverge.yml takes precedence over .agentverge.yaml and pyproject.toml."""
    (tmp_path / ".agentverge.yml").write_text('version: "from_yml"', encoding="utf-8")
    (tmp_path / ".agentverge.yaml").write_text('version: "from_yaml"', encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        '[tool.agentverge]\nversion = "from_pyproject"', encoding="utf-8"
    )

    config, loaded_path = load_config(root_path=tmp_path)

    assert loaded_path == tmp_path / ".agentverge.yml"
    assert config.version == "from_yml"


def test_explicit_config_precedence(tmp_path: Path) -> None:
    """Verify explicit config argument overrides project files."""
    (tmp_path / ".agentverge.yml").write_text('version: "from_yml"', encoding="utf-8")

    explicit = tmp_path / "custom_config.yaml"
    explicit.write_text('version: "from_explicit"', encoding="utf-8")

    config, loaded_path = load_config(root_path=tmp_path, explicit_config_path=explicit)

    assert loaded_path == explicit.resolve()
    assert config.version == "from_explicit"


def test_explicit_config_nonexistent(tmp_path: Path) -> None:
    """Verify ConfigurationError is raised when explicit config file does not exist."""
    missing = tmp_path / "missing.yml"
    with pytest.raises(ConfigurationError, match="does not exist"):
        load_config(root_path=tmp_path, explicit_config_path=missing)


def test_malformed_yaml_syntax(tmp_path: Path) -> None:
    """Verify ConfigurationError is raised on malformed YAML syntax."""
    bad_yml = tmp_path / ".agentverge.yml"
    bad_yml.write_text("invalid: yaml: [unclosed", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Failed to parse YAML"):
        load_config(root_path=tmp_path)


def test_malformed_toml_syntax(tmp_path: Path) -> None:
    """Verify ConfigurationError is raised on malformed TOML syntax."""
    bad_toml = tmp_path / "pyproject.toml"
    bad_toml.write_text("[tool.agentverge\nunclosed_bracket = 1", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Failed to parse TOML"):
        load_config(root_path=tmp_path)


def test_invalid_schema_types(tmp_path: Path) -> None:
    """Verify ConfigurationError is raised when configuration values violate schema types."""
    bad_schema = tmp_path / ".agentverge.yml"
    # max_file_size_bytes expects an int
    bad_schema.write_text("max_file_size_bytes: 'not_an_int'", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Configuration validation failed"):
        load_config(root_path=tmp_path)
