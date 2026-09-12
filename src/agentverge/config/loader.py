"""Configuration loading and validation subsystem."""

import tomllib
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from agentverge.models.config import AgentVergeConfig


class ConfigurationError(Exception):
    """Raised when an AgentVerge configuration file cannot be found, read, or validated."""


CONFIG_FILENAMES: tuple[str, ...] = (
    ".agentverge.yml",
    ".agentverge.yaml",
    "pyproject.toml",
)


def _normalize_raw_config(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize user-friendly configuration keys to schema field names."""
    normalized = dict(data)
    if "exclude" in normalized and "exclude_patterns" not in normalized:
        normalized["exclude_patterns"] = normalized.pop("exclude")
    if "include" in normalized and "include_patterns" not in normalized:
        normalized["include_patterns"] = normalized.pop("include")
    return normalized


def _parse_yaml_file(path: Path) -> dict[str, Any]:
    """Safely parse a YAML configuration file."""
    try:
        content = path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        if parsed is None:
            return {}
        if not isinstance(parsed, dict):
            raise ConfigurationError(
                f"Configuration file '{path}' must contain a key-value mapping, "
                f"got {type(parsed).__name__}."
            )
        return parsed
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Failed to parse YAML configuration file '{path}': {exc}"
        ) from exc
    except OSError as exc:
        raise ConfigurationError(f"Failed to read configuration file '{path}': {exc}") from exc


def _parse_pyproject_toml(path: Path) -> dict[str, Any] | None:
    """Parse [tool.agentverge] section from pyproject.toml if present."""
    try:
        content = path.read_text(encoding="utf-8")
        data = tomllib.loads(content)
        tool_section = data.get("tool", {})
        if not isinstance(tool_section, dict):
            return None
        agentverge_section = tool_section.get("agentverge")
        if agentverge_section is None:
            return None
        if not isinstance(agentverge_section, dict):
            raise ConfigurationError(
                f"Section '[tool.agentverge]' in '{path}' must be a table, "
                f"got {type(agentverge_section).__name__}."
            )
        return agentverge_section
    except tomllib.TOMLDecodeError as exc:
        raise ConfigurationError(f"Failed to parse TOML file '{path}': {exc}") from exc
    except OSError as exc:
        raise ConfigurationError(f"Failed to read '{path}': {exc}") from exc


def _load_from_path(path: Path) -> dict[str, Any]:
    """Load raw config dictionary from an explicitly specified file path."""
    suffix = path.suffix.lower()
    if suffix in (".yml", ".yaml"):
        return _parse_yaml_file(path)
    if suffix == ".toml":
        try:
            content = path.read_text(encoding="utf-8")
            data = tomllib.loads(content)
            # If pyproject.toml format, look for [tool.agentverge]
            if "tool" in data and isinstance(data["tool"], dict) and "agentverge" in data["tool"]:
                tool_data = data["tool"]["agentverge"]
                if not isinstance(tool_data, dict):
                    raise ConfigurationError(
                        f"Section '[tool.agentverge]' in '{path}' must be a table."
                    )
                return tool_data
            return data
        except tomllib.TOMLDecodeError as exc:
            raise ConfigurationError(f"Failed to parse TOML configuration '{path}': {exc}") from exc
        except OSError as exc:
            raise ConfigurationError(f"Failed to read configuration '{path}': {exc}") from exc

    # Default to YAML parsing for unspecified extensions
    return _parse_yaml_file(path)


def load_config(
    root_path: Path,
    explicit_config_path: Path | None = None,
) -> tuple[AgentVergeConfig, Path | None]:
    """Load AgentVerge configuration from the target project or explicit path.

    Precedence order:
        1. Explicit `--config` path
        2. `<root>/.agentverge.yml`
        3. `<root>/.agentverge.yaml`
        4. `<root>/pyproject.toml` (under `[tool.agentverge]`)
        5. Default configuration if none found

    Args:
        root_path: Target project root path.
        explicit_config_path: Optional user-supplied path to configuration file.

    Returns:
        A tuple of (AgentVergeConfig, loaded_config_path_or_None).

    Raises:
        ConfigurationError: If the configuration file cannot be read, parsed, or validated.
    """
    resolved_root = root_path.resolve()

    # 1. Explicit config path takes highest precedence
    if explicit_config_path is not None:
        target_file = explicit_config_path.resolve()
        if not target_file.exists():
            raise ConfigurationError(
                f"Specified configuration file does not exist: {explicit_config_path}"
            )
        if not target_file.is_file():
            raise ConfigurationError(
                f"Specified configuration path is not a file: {explicit_config_path}"
            )
        raw_data = _load_from_path(target_file)
        normalized = _normalize_raw_config(raw_data)
        try:
            config = AgentVergeConfig.model_validate(normalized)
            return config, target_file
        except ValidationError as exc:
            raise ConfigurationError(
                f"Configuration validation failed for '{explicit_config_path}':\n{exc}"
            ) from exc

    # 2. Check standard project candidates
    candidate_yml = resolved_root / ".agentverge.yml"
    if candidate_yml.is_file():
        raw_data = _parse_yaml_file(candidate_yml)
        normalized = _normalize_raw_config(raw_data)
        try:
            return AgentVergeConfig.model_validate(normalized), candidate_yml
        except ValidationError as exc:
            raise ConfigurationError(
                f"Configuration validation failed for '{candidate_yml}':\n{exc}"
            ) from exc

    candidate_yaml = resolved_root / ".agentverge.yaml"
    if candidate_yaml.is_file():
        raw_data = _parse_yaml_file(candidate_yaml)
        normalized = _normalize_raw_config(raw_data)
        try:
            return AgentVergeConfig.model_validate(normalized), candidate_yaml
        except ValidationError as exc:
            raise ConfigurationError(
                f"Configuration validation failed for '{candidate_yaml}':\n{exc}"
            ) from exc

    candidate_pyproject = resolved_root / "pyproject.toml"
    if candidate_pyproject.is_file():
        pyproject_config = _parse_pyproject_toml(candidate_pyproject)
        if pyproject_config is not None:
            normalized = _normalize_raw_config(pyproject_config)
            try:
                return AgentVergeConfig.model_validate(normalized), candidate_pyproject
            except ValidationError as exc:
                raise ConfigurationError(
                    f"Configuration validation failed for [tool.agentverge] "
                    f"in '{candidate_pyproject}':\n{exc}"
                ) from exc

    # 5. Fallback to default zero-config
    return AgentVergeConfig(), None
