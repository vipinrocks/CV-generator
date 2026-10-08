"""CV tips checker: friendly lint rules that improve a CV's impact.

Rules include: summary too long, bullets without action verbs or measurable
results, missing contact information, and estimated length over two pages.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cvforge.models import CV

Severity = Literal["info", "warning", "error"]

#: Common action verbs recruiters look for at the start of bullets.
_ACTION_VERB_WORDS = [
    "achieved",
    "administered",
    "advised",
    "analysed",
    "architected",
    "automated",
    "built",
    "chaired",
    "coached",
    "collaborated",
    "conceived",
    "conducted",
    "consolidated",
    "created",
    "delivered",
    "designed",
    "developed",
    "directed",
    "drove",
    "enabled",
    "engineered",
    "enhanced",
    "established",
    "evaluated",
    "executed",
    "expanded",
    "facilitated",
    "forecast",
    "founded",
    "grew",
    "guided",
    "implemented",
    "improved",
    "increased",
    "influenced",
    "initiated",
    "introduced",
    "launched",
    "led",
    "maintained",
    "managed",
    "mentored",
    "migrated",
    "modernised",
    "optimized",
    "organised",
    "oversaw",
    "owned",
    "performed",
    "pioneered",
    "planned",
    "presented",
    "prioritised",
    "produced",
    "programmed",
    "reduced",
    "refactored",
    "redesigned",
    "resolved",
    "restructured",
    "revamped",
    "reviewed",
    "saved",
    "scaled",
    "secured",
    "shipped",
    "simplified",
    "solved",
    "spearheaded",
    "standardised",
    "streamlined",
    "supervised",
    "supported",
    "tested",
    "trained",
    "transformed",
    "troubleshot",
    "unified",
    "upgraded",
    "wrote",
]
ACTION_VERBS: frozenset[str] = frozenset(_ACTION_VERB_WORDS)

#: Rough words-per-page density used to estimate CV length.
_WORDS_PER_PAGE = 450
_MAX_PAGES = 2
_MAX_SUMMARY_CHARS = 600


@dataclass(frozen=True)
class Finding:
    """A single tip or warning about the CV."""

    severity: Severity
    section: str
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        icon = {"info": "ℹ", "warning": "⚠", "error": "✘"}[self.severity]
        return f"{icon} [{self.section}] {self.message}"


def estimate_pages(cv: CV) -> float:
    """Estimate the rendered page count from the amount of content."""
    words = len(cv.basics.summary or "")
    words += sum(
        len(e.role) + len(e.company or "") + sum(len(h) for h in e.highlights)
        for e in cv.experience
    )
    words += sum(len(ed.degree) + len(ed.institution) for ed in cv.education)
    words += sum(sum(len(s) for s in g.skills) for g in cv.skills)
    words += sum(
        len(p.name) + len(p.description or "") + sum(len(h) for h in p.highlights)
        for p in cv.projects
    )
    words += sum(len(c.name) for c in cv.certifications)
    words += sum(len(a.name) + len(a.description or "") for a in cv.awards)
    words += sum(len(p.title) for p in cv.publications)
    words += sum(len(v.role or "") + sum(len(h) for h in v.highlights) for v in cv.volunteering)
    return max(1.0, round(words / _WORDS_PER_PAGE, 1))


def check_cv(cv: CV) -> list[Finding]:
    """Run all tip rules against *cv* and return the findings.

    Args:
        cv: The validated CV.

    Returns:
        A list of :class:`Finding`, ordered by severity (errors first).
    """
    findings: list[Finding] = []
    findings += _check_basics(cv)
    findings += _check_summary(cv)
    findings += _check_experience(cv)
    findings += _check_projects(cv)
    findings += _check_length(cv)

    order = {"error": 0, "warning": 1, "info": 2}
    return sorted(findings, key=lambda f: order[f.severity])


def _check_basics(cv: CV) -> list[Finding]:
    """Contact completeness checks."""
    findings: list[Finding] = []
    if not cv.basics.email:
        findings.append(
            Finding("error", "basics", "No email address — recruiters cannot reach you.")
        )
    if not cv.basics.phone:
        findings.append(Finding("warning", "basics", "No phone number provided."))
    if not cv.basics.location:
        findings.append(Finding("info", "basics", "No location — add at least a city and country."))
    if not cv.basics.headline:
        findings.append(
            Finding(
                "info", "basics", "No headline — a short title under your name helps ATS matching."
            )
        )
    if not (cv.basics.linkedin or cv.basics.github or cv.basics.website):
        findings.append(
            Finding("info", "basics", "Consider adding LinkedIn, GitHub or a personal website.")
        )
    return findings


def _check_summary(cv: CV) -> list[Finding]:
    """Summary quality checks."""
    if not cv.basics.summary:
        return [
            Finding("warning", "basics.summary", "No professional summary — add 2-3 sentences.")
        ]
    length = len(cv.basics.summary)
    if length > _MAX_SUMMARY_CHARS:
        return [
            Finding(
                "warning",
                "basics.summary",
                f"Summary is {length} characters (recommended max {_MAX_SUMMARY_CHARS}). "
                "Trim it to the highlights.",
            )
        ]
    return []


def _check_bullets(bullets: list[str], section: str) -> list[Finding]:
    """Check bullets for action verbs and measurable results."""
    findings: list[Finding] = []
    for i, bullet in enumerate(bullets, start=1):
        first_word = bullet.split(maxsplit=1)[0].strip("*,.") if bullet.split() else ""
        if first_word.lower() not in ACTION_VERBS:
            findings.append(
                Finding(
                    "info",
                    section,
                    f"Bullet {i} does not start with an action verb "
                    "(e.g. 'Led', 'Built', 'Reduced').",
                )
            )
        if not any(ch.isdigit() for ch in bullet):
            findings.append(
                Finding(
                    "info",
                    section,
                    f"Bullet {i} has no numbers or metrics — quantify the impact where possible.",
                )
            )
    return findings


def _check_experience(cv: CV) -> list[Finding]:
    """Experience section checks."""
    if not cv.experience:
        return [Finding("warning", "experience", "No experience listed.")]
    return _check_bullets([h for e in cv.experience for h in e.highlights], "experience")


def _check_projects(cv: CV) -> list[Finding]:
    """Project highlight checks (no error when absent)."""
    return _check_bullets([h for p in cv.projects for h in p.highlights], "projects")


def _check_length(cv: CV) -> list[Finding]:
    """Estimated page count check."""
    pages = estimate_pages(cv)
    if pages > _MAX_PAGES:
        return [
            Finding(
                "warning",
                "length",
                f"Estimated length is ~{pages} pages — aim for {_MAX_PAGES} or fewer "
                "(the 'compact' theme helps).",
            )
        ]
    return []
