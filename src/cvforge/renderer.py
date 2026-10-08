"""Render a :class:`~cvforge.models.CV` into standalone HTML using Jinja2 themes.

The output is a single self-contained HTML document (CSS inlined), which is
also the source for the PDF exporter.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup

from cvforge.markdown_lite import to_html
from cvforge.models import CV
from cvforge.photo import circular_photo_data_uri
from cvforge.themes import Theme, theme_css

#: Curated, safe font families (all widely available or free).
SAFE_FONTS: dict[str, str] = {
    "auto": "",  # theme decides
    "sans": "'Helvetica Neue', Arial, 'Noto Sans', 'Segoe UI', sans-serif",
    "serif": "Georgia, 'Times New Roman', 'Noto Serif', serif",
    "georgia": "Georgia, 'Times New Roman', serif",
    "times": "'Times New Roman', Times, serif",
    "arial": "Arial, Helvetica, sans-serif",
    "helvetica": "'Helvetica Neue', Helvetica, Arial, sans-serif",
    "noto sans": "'Noto Sans', Arial, sans-serif",
    "verdana": "Verdana, Geneva, sans-serif",
}

_MONTHS = [
    "",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


def format_date(value: str | None) -> str:
    """Format ``YYYY-MM`` as ``Mon YYYY``; pass through ``YYYY`` and ``Present``."""
    if not value:
        return ""
    if value == "Present" or len(value) == 4:
        return value
    parts = value.split("-")
    try:
        month = int(parts[1])
        if 1 <= month <= 12:
            return f"{_MONTHS[month]} {parts[0]}"
    except (IndexError, ValueError):
        pass
    return value


@dataclass
class ThemeOptions:
    """User-selectable rendering options shared by all themes."""

    accent_color: str = "#2563EB"
    font_family: str = "auto"  # key of SAFE_FONTS
    font_size: int = 10  # pt
    page_size: str = "A4"  # "A4" or "Letter"
    margins: str = "16mm"

    def font_css(self) -> str:
        """The CSS ``font-family`` value, or ``''`` to use the theme default."""
        return SAFE_FONTS.get(self.font_family.lower(), "")

    def validate(self) -> list[str]:
        """Return human-readable problems with the option values (may be empty)."""
        problems: list[str] = []
        if not self.accent_color.startswith("#") or len(self.accent_color) not in (4, 7):
            problems.append(f"accent_color '{self.accent_color}' is not a hex colour like #2563EB.")
        if self.font_family.lower() not in SAFE_FONTS:
            problems.append(
                f"font_family '{self.font_family}' is not in the safe list: "
                + ", ".join(sorted(SAFE_FONTS))
            )
        if not 7 <= self.font_size <= 14:
            problems.append(f"font_size {self.font_size}pt is outside the supported 7-14pt range.")
        if self.page_size not in ("A4", "Letter"):
            problems.append(f"page_size '{self.page_size}' must be 'A4' or 'Letter'.")
        return problems


class ThemeNotFoundError(Exception):
    """Raised when the requested theme does not exist."""


def _build_environment() -> Environment:
    """Create the shared Jinja2 environment with custom filters."""
    env = Environment(
        loader=PackageLoader("cvforge", "templates"),
        autoescape=select_autoescape(("html", "j2")),
    )
    env.filters["md"] = lambda text: Markup(to_html(text))
    env.filters["fmt_date"] = format_date
    return env


_ENV = _build_environment()


def _option_css(options: ThemeOptions, theme: Theme) -> str:
    """Build the CSS override block from user options."""
    lines = [":root {"]
    lines.append(f"  --accent: {options.accent_color};")
    if font := options.font_css():
        lines.append(f"  --font-body: {font};")
    lines.append(f"  --font-size: {options.font_size}pt;")
    lines.append("}")
    lines.append(f"@page {{ size: {options.page_size}; margin: {options.margins}; }}")
    # Make sure background colours survive printing (accent sidebars etc.).
    lines.append("* { -webkit-print-color-adjust: exact; print-color-adjust: exact; }")
    if not theme.supports_photo:
        lines.append(".photo { display: none; }")
    return "\n".join(lines)


def _photo_uri(cv: CV, theme: Theme) -> str | None:
    """Resolve the basics.photo path to a data URI, if usable."""
    photo = cv.basics.photo
    if not photo or not theme.supports_photo:
        return None
    try:
        return circular_photo_data_uri(photo)
    except Exception:
        return None


def render_html(cv: CV, theme: str | Theme = "classic", options: ThemeOptions | None = None) -> str:
    """Render *cv* to a standalone HTML string using the given theme.

    Args:
        cv: The validated CV data.
        theme: Theme name or :class:`Theme` instance.
        options: Accent colour / fonts / page setup overrides.

    Returns:
        A complete HTML document with inlined CSS.

    Raises:
        ThemeNotFoundError: If the theme name is unknown.
    """
    theme_obj = theme if isinstance(theme, Theme) else _lookup_theme(theme)
    opts = options or ThemeOptions()

    context: dict[str, Any] = {
        "cv": cv,
        "theme": theme_obj,
        "theme_css": theme_css(theme_obj.name),
        "option_css": _option_css(opts, theme_obj),
        "photo_uri": _photo_uri(cv, theme_obj),
    }
    template = _ENV.get_template(theme_obj.template_name)
    return template.render(**context)


def _lookup_theme(name: str) -> Theme:
    """Find a theme by name, converting errors to :class:`ThemeNotFoundError`."""
    from cvforge.themes import ThemeError, get_theme

    try:
        return get_theme(name)
    except ThemeError as exc:
        raise ThemeNotFoundError(str(exc)) from exc
