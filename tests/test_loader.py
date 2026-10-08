"""Tests for the YAML/JSON loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cvforge.loader import (
    LoadError,
    ValidationErrorCV,
    cv_to_dict,
    load_cv,
    parse_data,
    save_json,
    save_yaml,
)
from cvforge.models import CV


class TestParseData:
    def test_yaml_roundtrip(self, sample_yaml: str) -> None:
        cv = parse_data(sample_yaml)
        assert cv.basics.full_name == "Ada Lovelace"

    def test_json_also_accepted(self, sample_yaml: str) -> None:
        import yaml

        data = yaml.safe_load(sample_yaml)
        cv = parse_data(json.dumps(data))
        assert cv.basics.email == "ada@example.com"

    def test_invalid_yaml_raises_load_error(self) -> None:
        with pytest.raises(LoadError, match="not valid YAML"):
            parse_data("basics: [unclosed")

    def test_validation_error_carries_messages(self) -> None:
        with pytest.raises(ValidationErrorCV) as excinfo:
            parse_data("basics:\n  full_name: A\n  email: nope\n")
        assert any("email" in m for m in excinfo.value.messages)


class TestLoadCV:
    def test_load_yaml_file(self, tmp_path: Path, sample_yaml: str) -> None:
        path = tmp_path / "cv.yaml"
        path.write_text(sample_yaml, encoding="utf-8")
        cv = load_cv(path)
        assert isinstance(cv, CV)

    def test_load_json_file(self, tmp_path: Path, sample_yaml: str) -> None:
        import yaml

        path = tmp_path / "cv.json"
        path.write_text(json.dumps(yaml.safe_load(sample_yaml)), encoding="utf-8")
        cv = load_cv(path)
        assert isinstance(cv, CV)

    def test_missing_file(self) -> None:
        with pytest.raises(LoadError, match="not found"):
            load_cv("does_not_exist.yaml")

    def test_unsupported_suffix(self, tmp_path: Path) -> None:
        path = tmp_path / "cv.txt"
        path.write_text("basics: {}", encoding="utf-8")
        with pytest.raises(LoadError, match="supported format"):
            load_cv(path)


class TestSave:
    def test_save_yaml_roundtrip(self, tmp_path: Path, sample_cv: CV) -> None:
        out = save_yaml(sample_cv, tmp_path / "out" / "cv.yaml")
        assert out.is_file()
        assert load_cv(out).basics.full_name == sample_cv.basics.full_name

    def test_save_json_roundtrip(self, tmp_path: Path, sample_cv: CV) -> None:
        out = save_json(sample_cv, tmp_path / "cv.json")
        assert out.is_file()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["basics"]["full_name"] == sample_cv.basics.full_name

    def test_cv_to_dict_excludes_none(self, sample_cv: CV) -> None:
        data = cv_to_dict(sample_cv)
        assert "None" not in str(data)
