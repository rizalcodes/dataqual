import pytest

from dataqual.config import ConfigError, Thresholds, load_config


def _write(tmp_path, content):
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_no_path_returns_defaults():
    assert load_config(None) == Thresholds(
        missing=10.0, duplicate=10.0, type_mismatch=10.0, outlier=10.0
    )


def test_valid_overrides_applied(tmp_path):
    path = _write(
        tmp_path,
        """
rules:
  missing_threshold: 15
  duplicate_threshold: 5
""",
    )
    thresholds = load_config(path)
    assert thresholds.missing == 15.0
    assert thresholds.duplicate == 5.0
    # unspecified rules keep defaults
    assert thresholds.type_mismatch == 10.0
    assert thresholds.outlier == 10.0


def test_missing_file_raises_config_error():
    with pytest.raises(ConfigError, match="not found"):
        load_config("does_not_exist.yaml")


def test_malformed_yaml_raises_config_error(tmp_path):
    path = _write(tmp_path, "rules: [unclosed")
    with pytest.raises(ConfigError, match="Malformed YAML"):
        load_config(path)


def test_out_of_range_value_raises_config_error(tmp_path):
    path = _write(tmp_path, "rules:\n  missing_threshold: 150")
    with pytest.raises(ConfigError, match="between 0 and 100"):
        load_config(path)


def test_non_numeric_value_raises_config_error(tmp_path):
    path = _write(tmp_path, "rules:\n  missing_threshold: lots")
    with pytest.raises(ConfigError, match="not a number"):
        load_config(path)


def test_unknown_rule_raises_config_error(tmp_path):
    path = _write(tmp_path, "rules:\n  missng_threshold: 5")
    with pytest.raises(ConfigError, match="Unknown rule"):
        load_config(path)


def test_empty_file_returns_defaults(tmp_path):
    path = _write(tmp_path, "")
    assert load_config(path) == Thresholds()
