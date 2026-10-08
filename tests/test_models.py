"""Tests for the pydantic data models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cvforge.loader import parse_data
from cvforge.models import CV, Basics, ExperienceItem, format_validation_error


class TestBasics:
    def test_minimal_valid(self) -> None:
        basics = Basics(full_name="Ada Lovelace")
        assert basics.full_name == "Ada Lovelace"
        assert basics.email is None

    def test_email_validation_rejects_bad(self) -> None:
        with pytest.raises(ValidationError, match="not a valid email"):
            Basics(full_name="Ada", email="not-an-email")

    def test_url_validation_rejects_bad(self) -> None:
        with pytest.raises(ValidationError, match="not a valid URL"):
            Basics(full_name="Ada", website="ada.dev")

    def test_contact_items_skip_empty(self) -> None:
        basics = Basics(full_name="Ada", email="a@b.co", location="London")
        assert basics.contact_items == ["a@b.co", "London"]

    def test_extra_field_forbidden(self) -> None:
        with pytest.raises(ValidationError, match="extra"):
            Basics(full_name="Ada", nicknane="Ada")


class TestExperience:
    def test_end_date_present_allowed(self) -> None:
        item = ExperienceItem(company="X", role="Y", start_date="2020-01", end_date="Present")
        assert item.end_date == "Present"

    def test_bad_date_format_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperienceItem(company="X", role="Y", start_date="Jan 2020")

    def test_bad_end_date_rejected(self) -> None:
        with pytest.raises(ValidationError):
            ExperienceItem(company="X", role="Y", start_date="2020-01", end_date="yesterday")


class TestSorting:
    def test_experience_sorted_reverse_chronological(self, sample_yaml: str) -> None:
        cv = parse_data(sample_yaml)
        assert cv.experience[0].company == "Acme Cloud"

    def test_input_order_does_not_matter(self) -> None:
        raw = {
            "basics": {"full_name": "A"},
            "experience": [
                {"company": "Old", "role": "Dev", "start_date": "2015-01", "end_date": "2016-01"},
                {"company": "New", "role": "Dev", "start_date": "2020-01", "end_date": "Present"},
            ],
        }
        cv = CV.model_validate(raw)
        assert [e.company for e in cv.experience] == ["New", "Old"]

    def test_present_sorts_after_fixed_dates(self) -> None:
        raw = {
            "basics": {"full_name": "A"},
            "education": [
                {
                    "institution": "B",
                    "degree": "MSc",
                    "start_date": "2010-01",
                    "end_date": "2011-01",
                },
                {
                    "institution": "C",
                    "degree": "BSc",
                    "start_date": "2008-01",
                    "end_date": "2010-01",
                },
            ],
        }
        cv = CV.model_validate(raw)
        assert [e.degree for e in cv.education] == ["MSc", "BSc"]


class TestFriendlyErrors:
    def test_unknown_field_message_points_at_field(self) -> None:
        with pytest.raises(Exception) as excinfo:
            parse_data("basics:\n  full_name: A\n  favourite_colour: blue\n")
        assert "favourite_colour" in str(excinfo.value)

    def test_format_validation_error_contains_loc(self) -> None:
        with pytest.raises(ValidationError) as excinfo:
            CV.model_validate({"basics": {"full_name": "A", "email": "bad"}})
        messages = format_validation_error(excinfo.value, "test.yaml")
        assert any("basics.email" in m for m in messages)
        assert any("test.yaml" in m for m in messages)

    def test_missing_required_field_message(self) -> None:
        with pytest.raises(Exception) as excinfo:
            parse_data("experience: []")
        assert "basics" in str(excinfo.value)

    def test_non_mapping_document(self) -> None:
        from cvforge.loader import LoadError

        with pytest.raises(LoadError, match="mapping"):
            parse_data("- just\n- a\n- list\n")

    def test_empty_document(self) -> None:
        from cvforge.loader import LoadError

        with pytest.raises(LoadError, match="empty"):
            parse_data("")


class TestDateSortKey:
    def test_key_ordering(self) -> None:
        from cvforge.models import _date_sort_key

        assert _date_sort_key(None) < _date_sort_key("2019-01")
        assert _date_sort_key("2019-01") < _date_sort_key("2021-06")
        assert _date_sort_key("2021-06") < _date_sort_key("2021")
        assert _date_sort_key("2021") < _date_sort_key("Present")
