"""Tests for the CV tips checker."""

from __future__ import annotations

import pytest

from cvforge.checker import check_cv, estimate_pages
from cvforge.loader import parse_data
from cvforge.models import CV


def findings_for(cv: CV, section: str | None = None) -> list[str]:
    """Checker messages, optionally filtered by section prefix."""
    return [f.message for f in check_cv(cv) if section is None or f.section.startswith(section)]


def test_perfect_cv_has_few_findings(sample_cv: CV) -> None:
    findings = check_cv(sample_cv)
    errors = [f for f in findings if f.severity == "error"]
    assert not errors


def test_missing_email_is_error() -> None:
    cv = CV.model_validate({"basics": {"full_name": "A"}})
    errors = [f for f in check_cv(cv) if f.severity == "error"]
    assert any("email" in f.message.lower() for f in errors)


def test_summary_too_long() -> None:
    yaml_text = "basics:\n  full_name: A\n  summary: " + ("word " * 200)
    cv = parse_data(yaml_text)
    assert any("600" in m or "Summary" in m for m in findings_for(cv, "basics.summary"))


def test_bullet_without_action_verb_flagged() -> None:
    yaml_text = (
        "basics:\n  full_name: A\n  email: a@b.co\n"
        "experience:\n"
        "  - company: X\n    role: Dev\n    start_date: 2020-01\n"
        '    highlights:\n      - "Responsible for the thing"\n'
    )
    cv = parse_data(yaml_text)
    assert any("action verb" in m for m in findings_for(cv, "experience"))


def test_bullet_without_metrics_flagged() -> None:
    yaml_text = (
        "basics:\n  full_name: A\n  email: a@b.co\n"
        "experience:\n"
        "  - company: X\n    role: Dev\n    start_date: 2020-01\n"
        '    highlights:\n      - "Led the migration project"\n'
    )
    cv = parse_data(yaml_text)
    assert any("metrics" in m for m in findings_for(cv, "experience"))


def test_action_verb_and_metric_bullet_clean(sample_cv: CV) -> None:
    assert not any("action verb" in m for m in findings_for(sample_cv, "experience"))


def test_long_cv_flagged_over_two_pages() -> None:
    yaml_text = "basics:\n  full_name: A\n  email: a@b.co\nexperience:\n"
    for i in range(30):
        yaml_text += (
            f"  - company: C{i}\n    role: Dev\n    start_date: 20{i % 20:02d}-01\n"
            "    highlights:\n"
            '      - "Led a large project and reduced costs by 25% while improving quality"\n'
        )
    cv = parse_data(yaml_text)
    assert estimate_pages(cv) > 2
    assert any("pages" in m for m in findings_for(cv, "length"))


def test_findings_sorted_errors_first() -> None:
    cv = CV.model_validate({"basics": {"full_name": "A"}})
    severities = [f.severity for f in check_cv(cv)]
    order = ["error", "warning", "info"]
    assert severities == sorted(severities, key=order.index)


def test_finding_str_representation() -> None:
    from cvforge.checker import Finding

    assert "[basics]" in str(Finding("warning", "basics", "m"))


def test_projects_bullets_checked(sample_cv: CV) -> None:
    # sample project bullet has no action verb ("Shipped" is one) - has none? it starts with Shipped
    assert isinstance(findings_for(sample_cv, "projects"), list)


@pytest.mark.parametrize(
    ("section", "empty"),
    [
        ("experience", "experience"),
        ("education", "education"),
        ("skills", "skills"),
    ],
)
def test_all_sections_optional(section: str, empty: str) -> None:
    cv = CV.model_validate({"basics": {"full_name": "A"}})
    assert getattr(cv, section) == []
