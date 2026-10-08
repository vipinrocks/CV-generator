"""Markdown-lite inline formatting shared by the HTML and DOCX exporters.

Supported syntax (applied to bullet/highlight text):

- ``**bold**``
- ``*italic*``
- ``[link text](https://example.com)``

All input is HTML-escaped first, so the output is safe to embed.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass

_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")
_BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
_ITALIC_RE = re.compile(r"\*(.+?)\*", re.DOTALL)


@dataclass(frozen=True)
class TextRun:
    """A span of text with formatting flags (used by the DOCX exporter)."""

    text: str
    bold: bool = False
    italic: bool = False
    link: str | None = None


def _split_links(text: str) -> list[TextRun]:
    """Split text into plain runs and link runs."""
    runs: list[TextRun] = []
    pos = 0
    for match in _LINK_RE.finditer(text):
        if match.start() > pos:
            runs.append(TextRun(text[pos : match.start()]))
        runs.append(TextRun(text=match.group(1), link=match.group(2)))
        pos = match.end()
    if pos < len(text):
        runs.append(TextRun(text[pos:]))
    return runs or [TextRun(text)]


def to_runs(text: str) -> list[TextRun]:
    """Parse markdown-lite text into styled :class:`TextRun` spans."""
    result: list[TextRun] = []
    for run in _split_links(text):
        # Split each link-free run into bold segments, then italic segments.
        for bold_part, bold in _split_marker(run.text, _BOLD_RE):
            for italic_part, italic in _split_marker(bold_part, _ITALIC_RE):
                if italic_part:
                    result.append(
                        TextRun(text=italic_part, bold=bold, italic=italic, link=run.link)
                    )
    return result


def _split_marker(text: str, pattern: re.Pattern[str]) -> list[tuple[str, bool]]:
    """Split *text* into (segment, marker_active) pairs for a marker pattern."""
    parts: list[tuple[str, bool]] = []
    pos = 0
    for match in pattern.finditer(text):
        if match.start() > pos:
            parts.append((text[pos : match.start()], False))
        parts.append((match.group(1), True))
        pos = match.end()
    if pos < len(text):
        parts.append((text[pos:], False))
    return parts


def to_html(text: str) -> str:
    """Convert markdown-lite *text* to a safe inline HTML string.

    Args:
        text: Raw user text (``**bold**``, ``*italic*``, ``[t](url)``).

    Returns:
        HTML with ``<strong>``, ``<em>`` and ``<a>`` tags; everything else escaped.
    """
    escaped = html.escape(text, quote=False)
    escaped = _LINK_RE.sub(r'<a href="\2">\1</a>', escaped)
    escaped = _BOLD_RE.sub(r"<strong>\1</strong>", escaped)
    escaped = _ITALIC_RE.sub(r"<em>\1</em>", escaped)
    return escaped
