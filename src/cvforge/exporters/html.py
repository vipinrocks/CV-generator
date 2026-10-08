"""HTML exporter: writes a standalone single-file HTML document."""

from __future__ import annotations

from pathlib import Path

from cvforge.models import CV
from cvforge.renderer import ThemeOptions, render_html
from cvforge.themes import Theme


def export_html(
    cv: CV,
    out_path: str | Path,
    theme: str | Theme = "classic",
    options: ThemeOptions | None = None,
) -> Path:
    """Render *cv* and write a standalone HTML file.

    Args:
        cv: The validated CV data.
        out_path: Destination file path (``.html``).
        theme: Theme name or instance.
        options: Rendering options.

    Returns:
        The resolved output path.
    """
    html = render_html(cv, theme=theme, options=options)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out
