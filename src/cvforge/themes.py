"""Theme discovery for CVForge.

Themes live in ``cvforge/templates/<name>/``. Each theme folder contains a
``template.html.j2``, a ``style.css`` and a ``theme.yaml`` descriptor. Dropping
a new folder into the templates directory automatically registers a new theme.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from importlib import resources
from typing import Any

if sys.version_info >= (3, 11):
    from importlib.resources.abc import Traversable
else:  # pragma: no cover - Python 3.10 fallback
    from importlib.abc import Traversable

import yaml

from cvforge.models import CVForgeError

#: Fields recognised in a ``theme.yaml`` descriptor.
KNOWN_OPTIONS = ("accent_color", "font_family", "font_size", "page_size", "margins")


class ThemeError(CVForgeError):
    """Raised when a theme cannot be found or its descriptor is invalid."""


@dataclass(frozen=True)
class Theme:
    """A discovered CV theme."""

    name: str
    description: str
    supports_photo: bool
    options: list[str] = field(default_factory=list)

    @property
    def template_name(self) -> str:
        """Jinja2 template path relative to the ``cvforge/templates`` loader root."""
        return f"{self.name}/template.html.j2"


def templates_root() -> Traversable:
    """Return a traversable handle on the package templates directory."""
    return resources.files("cvforge") / "templates"


def _theme_dirs() -> list[str]:
    """Names of all sub-directories of the templates package."""
    root = templates_root()
    names: list[str] = []
    try:
        for entry in root.iterdir():
            if entry.name.startswith("_") or entry.name.startswith("."):
                continue
            if entry.is_dir() and (entry / "theme.yaml").is_file():
                names.append(entry.name)
    except FileNotFoundError:
        pass
    return sorted(names)


def _read_theme_yaml(name: str) -> dict[str, Any]:
    """Read and parse a theme descriptor, raising a friendly error on failure."""
    desc_file = templates_root() / name / "theme.yaml"
    try:
        raw = desc_file.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        raise ThemeError(f"Theme '{name}' has an invalid theme.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise ThemeError(f"Theme '{name}' has an invalid theme.yaml (expected a mapping).")
    return data


def list_themes() -> list[Theme]:
    """Discover all registered themes, sorted by name.

    Returns:
        A list of :class:`Theme` objects; empty if the package is broken.
    """
    themes: list[Theme] = []
    for name in _theme_dirs():
        data = _read_theme_yaml(name)
        themes.append(
            Theme(
                name=str(data.get("name", name)),
                description=str(data.get("description", "")),
                supports_photo=bool(data.get("supports_photo", False)),
                options=[str(o) for o in data.get("options", []) if o in KNOWN_OPTIONS],
            )
        )
    return themes


def get_theme(name: str) -> Theme:
    """Look up a theme by folder name.

    Args:
        name: Theme folder name (e.g. ``"modern"``).

    Returns:
        The matching :class:`Theme`.

    Raises:
        ThemeError: If no theme with that name exists (lists valid names).
    """
    for theme in list_themes():
        if theme.name == name:
            return theme
    available = ", ".join(t.name for t in list_themes()) or "(none)"
    raise ThemeError(f"Unknown theme '{name}'. Available themes: {available}.")


def theme_css(name: str) -> str:
    """Return the CSS stylesheet for a theme."""
    css_file = templates_root() / name / "style.css"
    try:
        return str(css_file.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ThemeError(f"Theme '{name}' is missing its style.css: {exc}") from exc
