"""Config values (thresholds, rules) and YAML config loading."""

from dataclasses import dataclass
from pathlib import Path

import yaml

# Percentage at or above which a finding is flagged red in reports
# (below it but above zero is yellow, zero is green).
MISSING_ALERT_THRESHOLD = 10.0
DUPLICATE_ALERT_THRESHOLD = 10.0
TYPE_MISMATCH_ALERT_THRESHOLD = 10.0
OUTLIER_ALERT_THRESHOLD = 10.0

# YAML key (under "rules:") -> Thresholds field name.
_RULE_KEYS = {
    "missing_threshold": "missing",
    "duplicate_threshold": "duplicate",
    "type_mismatch_threshold": "type_mismatch",
    "outlier_threshold": "outlier",
}


class ConfigError(Exception):
    """Raised when a config file is missing or invalid; message is CLI-friendly."""


@dataclass
class Thresholds:
    missing: float = MISSING_ALERT_THRESHOLD
    duplicate: float = DUPLICATE_ALERT_THRESHOLD
    type_mismatch: float = TYPE_MISMATCH_ALERT_THRESHOLD
    outlier: float = OUTLIER_ALERT_THRESHOLD


def load_config(path: str | None) -> Thresholds:
    """Load threshold overrides from a YAML config file.

    With no path, returns the defaults. Raises ConfigError (with a clear
    message) if the file is missing, malformed, or contains invalid values —
    callers decide whether to exit or fall back to defaults with a warning.
    """
    if path is None:
        return Thresholds()

    file = Path(path)
    if not file.is_file():
        raise ConfigError(f"Config file not found: {path}")
    try:
        data = yaml.safe_load(file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"Malformed YAML in {path}: {exc}") from None

    if data is None:
        return Thresholds()
    if not isinstance(data, dict) or not isinstance(data.get("rules", {}), dict):
        raise ConfigError(f"Invalid config in {path}: expected a 'rules:' mapping.")

    kwargs = {}
    for key, value in (data.get("rules") or {}).items():
        field = _RULE_KEYS.get(key)
        if field is None:
            raise ConfigError(
                f"Unknown rule '{key}' in {path}. "
                f"Valid rules: {', '.join(_RULE_KEYS)}"
            )
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ConfigError(f"Invalid value for '{key}' in {path}: {value!r} is not a number.")
        if not 0 <= value <= 100:
            raise ConfigError(
                f"Invalid value for '{key}' in {path}: {value} must be between 0 and 100."
            )
        kwargs[field] = float(value)
    return Thresholds(**kwargs)
