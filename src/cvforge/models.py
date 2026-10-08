"""Pydantic data models for CVForge.

Every section of the CV is optional except ``basics``. Models validate
emails, URLs and date formats, and automatically sort experience and
education in reverse-chronological order.
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StringConstraints,
    ValidationError,
    field_validator,
    model_validator,
)

#: Matches an email address loosely but usefully (user@domain.tld).
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]{2,}$")

#: Matches absolute http(s) URLs.
URL_RE = re.compile(r"^https?://\S+$")

#: Dates must be ``YYYY`` or ``YYYY-MM`` (``YYYY-MM-DD`` is tolerated too).
DATE_RE = re.compile(r"^\d{4}(-\d{2}(-\d{2})?)?$")

DateStr = Annotated[str, StringConstraints(pattern=DATE_RE)]


def _validate_presentable_date(value: str | None) -> str | None:
    """Validate an end date that may also be the literal ``Present``."""
    if value and value != "Present" and not DATE_RE.match(value):
        raise ValueError(f"'{value}' is not a valid date (use YYYY-MM, YYYY, or 'Present').")
    return value


Stripped = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CVForgeError(Exception):
    """Base class for all CVForge errors."""


class ValidationErrorCV(CVForgeError):
    """Raised when CV data fails validation; carries friendly messages."""

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        joined = "\n".join(f"  - {m}" for m in messages)
        super().__init__(f"The CV file has {len(messages)} problem(s):\n{joined}")


class ExportError(CVForgeError):
    """Raised when an exporter cannot produce output (e.g. missing WeasyPrint)."""


def _check_email(value: str | None) -> str | None:
    """Raise a ``ValueError`` if *value* is not a plausible email address."""
    if value and not EMAIL_RE.match(value):
        raise ValueError(f"'{value}' is not a valid email address (expected name@example.com).")
    return value


def _check_url(value: str | None) -> str | None:
    """Raise a ``ValueError`` if *value* is not an absolute http(s) URL."""
    if value and not URL_RE.match(value):
        raise ValueError(f"'{value}' is not a valid URL (must start with http:// or https://).")
    return value


class Basics(BaseModel):
    """Contact details and professional summary. The only required section."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    full_name: Stripped
    headline: Stripped | None = None
    email: Stripped | None = None
    phone: Stripped | None = None
    location: Stripped | None = None
    website: Stripped | None = None
    linkedin: Stripped | None = None
    github: Stripped | None = None
    summary: Stripped | None = None
    photo: str | None = None  # path to an image file, resolved by the caller

    @field_validator("email")
    @classmethod
    def _valid_email(cls, v: str | None) -> str | None:
        return _check_email(v)

    @field_validator("website", "linkedin", "github")
    @classmethod
    def _valid_urls(cls, v: str | None) -> str | None:
        return _check_url(v)

    @property
    def contact_items(self) -> list[str]:
        """Non-empty contact fields as display strings."""
        items = [self.email, self.phone, self.location]
        return [item for item in items if item]


class ExperienceItem(BaseModel):
    """A single role in the experience section."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    company: Stripped
    role: Stripped
    location: Stripped | None = None
    start_date: DateStr
    end_date: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None
    highlights: list[Stripped] = Field(default_factory=list)

    @field_validator("end_date")
    @classmethod
    def _valid_end_date(cls, v: str | None) -> str | None:
        return _validate_presentable_date(v)


class EducationItem(BaseModel):
    """A single entry in the education section."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    institution: Stripped
    degree: Stripped
    field: Stripped | None = None
    start_date: DateStr | None = None
    end_date: DateStr | None = None
    grade: Stripped | None = None
    notes: Stripped | None = None


class SkillGroup(BaseModel):
    """A named group of skills, e.g. ``Languages: Python, SQL``."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Stripped
    skills: list[Stripped] = Field(default_factory=list, min_length=1)


class ProjectItem(BaseModel):
    """A personal or open-source project."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Stripped
    url: Stripped | None = None
    description: Stripped | None = None
    highlights: list[Stripped] = Field(default_factory=list)
    tech: list[Stripped] = Field(default_factory=list)

    @field_validator("url")
    @classmethod
    def _valid_url(cls, v: str | None) -> str | None:
        return _check_url(v)


class CertificationItem(BaseModel):
    """A certification with optional issuer, date and URL."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Stripped
    issuer: Stripped | None = None
    date: DateStr | None = None
    url: Stripped | None = None

    @field_validator("url")
    @classmethod
    def _valid_url(cls, v: str | None) -> str | None:
        return _check_url(v)


class LanguageItem(BaseModel):
    """A spoken language and proficiency level."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    language: Stripped
    proficiency: Stripped | None = None


class AwardItem(BaseModel):
    """An award or honour."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: Stripped
    issuer: Stripped | None = None
    date: DateStr | None = None
    description: Stripped | None = None


class PublicationItem(BaseModel):
    """A publication with optional URL."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: Stripped
    venue: Stripped | None = None
    date: DateStr | None = None
    url: Stripped | None = None

    @field_validator("url")
    @classmethod
    def _valid_url(cls, v: str | None) -> str | None:
        return _check_url(v)


class VolunteeringItem(BaseModel):
    """A volunteering engagement."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    organization: Stripped
    role: Stripped | None = None
    start_date: DateStr | None = None
    end_date: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None
    highlights: list[Stripped] = Field(default_factory=list)

    @field_validator("end_date")
    @classmethod
    def _valid_end_date(cls, v: str | None) -> str | None:
        return _validate_presentable_date(v)


def _date_sort_key(value: str | None) -> tuple[int, int]:
    """Turn a date string into a sortable ``(year, month)`` tuple.

    ``"Present"`` sorts after everything; missing dates sort first.
    """
    if value is None or value == "":
        return (0, 0)
    if value == "Present":
        return (9999, 12)
    parts = value.split("-")
    year = int(parts[0])
    month = int(parts[1]) if len(parts) > 1 else 12
    return (year, month)


class CV(BaseModel):
    """The complete CV document."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    basics: Basics
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    skills: list[SkillGroup] = Field(default_factory=list)
    projects: list[ProjectItem] = Field(default_factory=list)
    certifications: list[CertificationItem] = Field(default_factory=list)
    languages: list[LanguageItem] = Field(default_factory=list)
    awards: list[AwardItem] = Field(default_factory=list)
    publications: list[PublicationItem] = Field(default_factory=list)
    volunteering: list[VolunteeringItem] = Field(default_factory=list)
    interests: list[Stripped] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _sort_sections(cls, data: Any) -> Any:
        """Sort experience/education reverse-chronologically before validation."""
        if isinstance(data, dict):
            data = dict(data)
            data["experience"] = _sorted_by_date(data.get("experience"), ("end_date", "start_date"))
            data["education"] = _sorted_by_date(data.get("education"), ("end_date", "start_date"))
            data["volunteering"] = _sorted_by_date(
                data.get("volunteering"), ("end_date", "start_date")
            )
        return data

    @property
    def has_employment_dates(self) -> bool:
        """True if at least one experience entry has dates."""
        return any(item.start_date for item in self.experience)


def _sorted_by_date(items: Any, keys: tuple[str, ...]) -> list[Any]:
    """Sort a list of raw dicts by the given date keys, newest first.

    Items that are not dicts are passed through untouched; malformed values
    are left in place so the pydantic validator can report them precisely.
    """
    if not items:
        return []
    if not isinstance(items, list):
        return list(items)
    dict_items = [i for i in items if isinstance(i, dict)]
    other = [i for i in items if not isinstance(i, dict)]

    def sort_key(item: dict[str, Any]) -> tuple[tuple[int, int], ...]:
        return tuple(_date_sort_key(item.get(key)) for key in keys)

    return sorted(dict_items, key=sort_key, reverse=True) + other


def format_validation_error(exc: ValidationError, source_name: str = "CV") -> list[str]:
    """Convert a pydantic :class:`ValidationError` into friendly messages.

    Each message points at the exact field that failed, e.g.
    ``basics.email: 'foo' is not a valid email address (...)``.
    """
    messages: list[str] = []
    for error in exc.errors():
        loc = ".".join(str(part) for part in error["loc"]) or "<root>"
        msg = error["msg"]
        if error["type"] == "extra_forbidden":
            messages.append(f"{loc}: unknown field. Check for typos in '{loc}'.")
        elif error["type"] == "missing":
            messages.append(f"{loc}: this field is required.")
        elif error["type"] == "string_pattern":
            messages.append(f"{loc}: {msg} Use YYYY or YYYY-MM (e.g. 2021-06).")
        else:
            messages.append(f"{loc}: {msg}")
    return [f"{source_name}: {m}" if not m.startswith(source_name) else m for m in messages]
