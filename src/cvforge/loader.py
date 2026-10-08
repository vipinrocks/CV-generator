"""Load CV data from YAML or JSON files and validate it.

All errors are converted into friendly, field-level messages via
:func:`cvforge.models.format_validation_error`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from cvforge.models import CV, CVForgeError, ValidationErrorCV, format_validation_error

SUPPORTED_SUFFIXES = {".yaml", ".yml", ".json"}


class LoadError(CVForgeError):
    """Raised when a CV file cannot be found, read or parsed."""


def parse_data(raw: str, source_name: str = "CV") -> CV:
    """Parse and validate a YAML or JSON string into a :class:`CV`.

    Args:
        raw: The file contents as text.
        source_name: A label used in error messages (usually the file name).

    Returns:
        A validated :class:`CV` instance.

    Raises:
        LoadError: If the content is not valid YAML/JSON.
        ValidationErrorCV: If the data does not match the CV schema.
    """
    try:
        data: Any = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise LoadError(f"{source_name} is not valid YAML/JSON: {exc}") from exc

    if data is None:
        raise LoadError(f"{source_name} is empty. Add at least a 'basics' section.")
    if not isinstance(data, dict):
        raise LoadError(
            f"{source_name} must contain a mapping (key: value pairs), got {type(data).__name__}."
        )

    try:
        return CV.model_validate(data)
    except Exception as exc:
        from pydantic import ValidationError  # local import keeps mypy happy

        if isinstance(exc, ValidationError):
            raise ValidationErrorCV(format_validation_error(exc, source_name)) from exc
        raise LoadError(f"{source_name}: {exc}") from exc


def load_cv(path: str | Path) -> CV:
    """Load and validate a CV from a ``.yaml``, ``.yml`` or ``.json`` file.

    Args:
        path: Path to the CV file.

    Returns:
        A validated :class:`CV`.

    Raises:
        LoadError: If the file is missing, unreadable, or not YAML/JSON.
        ValidationErrorCV: If the data does not match the CV schema.
    """
    file_path = Path(path)
    if not file_path.is_file():
        raise LoadError(f"File not found: '{file_path}'. Run 'cvforge init' to create one.")
    if file_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_SUFFIXES))
        raise LoadError(f"'{file_path.name}' is not a supported format. Use one of: {supported}.")

    try:
        raw = file_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LoadError(f"Could not read '{file_path}': {exc}") from exc

    return parse_data(raw, file_path.name)


def cv_to_dict(cv: CV) -> dict[str, Any]:
    """Serialise a :class:`CV` back into a plain dict (for YAML/JSON export)."""
    return cv.model_dump(mode="json", exclude_none=True)


def save_yaml(cv: CV, path: str | Path) -> Path:
    """Write a :class:`CV` to *path* as YAML and return the resolved path."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = cv_to_dict(cv)
    out_path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return out_path


def save_json(cv: CV, path: str | Path) -> Path:
    """Write a :class:`CV` to *path* as JSON and return the resolved path."""
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    data = cv_to_dict(cv)
    out_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
