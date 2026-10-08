"""PDF exporter using WeasyPrint.

If WeasyPrint (or its system libraries, e.g. Pango) is unavailable, a clear
:class:`~cvforge.models.ExportError` is raised so callers can fall back to
DOCX and HTML with a helpful message instead of a traceback.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

from cvforge.models import CV, ExportError
from cvforge.renderer import ThemeOptions, render_html
from cvforge.themes import Theme

_IS_AVAILABLE: bool | None = None
_IMPORT_ERROR: str | None = None


def _import_weasyprint() -> tuple[bool, str]:
    """Try importing WeasyPrint, capturing its banner output.

    WeasyPrint prints its own "missing libraries" banner with a plain
    ``print()`` at import time, so we temporarily redirect std streams.

    Returns:
        ``(available, message)`` where *message* is empty on success.
    """
    stdout_capture, stderr_capture = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(
            stderr_capture
        ):
            import weasyprint  # noqa: F401
    except Exception as exc:  # noqa: BLE001 - OSError on missing Pango, ImportError...
        detail = f"{type(exc).__name__}: {exc}"
        banner = (stdout_capture.getvalue() + stderr_capture.getvalue()).strip()
        return False, f"{detail}\n{banner}" if banner else detail
    return True, ""


def is_pdf_available() -> bool:
    """Return True if WeasyPrint can be imported (system libs present)."""
    global _IS_AVAILABLE, _IMPORT_ERROR
    if _IS_AVAILABLE is None:
        _IS_AVAILABLE, _IMPORT_ERROR = _import_weasyprint()
    return _IS_AVAILABLE


def pdf_unavailable_reason() -> str:
    """Return the exception message from the last failed WeasyPrint import."""
    is_pdf_available()
    if _IMPORT_ERROR:
        return _IMPORT_ERROR
    return "WeasyPrint is available."


def export_pdf(
    cv: CV,
    out_path: str | Path,
    theme: str | Theme = "classic",
    options: ThemeOptions | None = None,
) -> Path:
    """Render *cv* to a text-selectable, ATS-parsable PDF via WeasyPrint.

    Args:
        cv: The validated CV data.
        out_path: Destination file path (``.pdf``).
        theme: Theme name or instance.
        options: Rendering options.

    Returns:
        The resolved output path.

    Raises:
        ExportError: If WeasyPrint or its system dependencies are missing.
    """
    if not is_pdf_available():
        raise ExportError(
            "PDF export is unavailable because WeasyPrint could not be loaded.\n"
            f"Reason: {pdf_unavailable_reason()}\n"
            "Install the system dependencies for your OS (see README > Troubleshooting):\n"
            "  - Debian/Ubuntu: sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b\n"
            "  - macOS: brew install pango\n"
            "  - Windows: install the GTK3 runtime (MSYS2) and add its bin folder to PATH\n"
            "DOCX and HTML exports still work without WeasyPrint."
        )

    import weasyprint

    html = render_html(cv, theme=theme, options=options)
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    document = weasyprint.HTML(string=html, base_url=".")
    document.write_pdf(out)
    return out
