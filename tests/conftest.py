"""Shared pytest fixtures for the CVForge test suite."""

from __future__ import annotations

from pathlib import Path

import pytest

from cvforge.models import CV

SAMPLE_YAML = """\
basics:
  full_name: Ada Lovelace
  headline: Senior Software Engineer
  email: ada@example.com
  phone: "+44 20 7946 0958"
  location: London, UK
  website: https://ada.dev
  linkedin: https://www.linkedin.com/in/ada
  github: https://github.com/ada
  summary: >-
    Engineer with 8+ years of experience. Led a migration that **cut deploy
    time by 70%** and improved reliability.

experience:
  - company: Acme Cloud
    role: Senior Engineer
    location: London, UK
    start_date: 2021-03
    end_date: Present
    highlights:
      - "**Led** a team of 5, cutting deploy time by 70%."
      - "Reduced p95 latency from 900ms to 120ms."
  - company: Initech
    role: Engineer
    start_date: 2017-07
    end_date: 2021-02
    highlights:
      - "Built a billing service processing £3M/month."

education:
  - institution: University of Manchester
    degree: BSc
    field: Computer Science
    start_date: 2013-09
    end_date: 2017-06
    grade: First Class Honours

skills:
  - name: Languages
    skills: [Python, Go, SQL]
  - name: Infra
    skills: [Kubernetes, AWS]

projects:
  - name: cvforge
    url: https://github.com/ada/cvforge
    description: CV generator.
    tech: [Python]
    highlights:
      - "Shipped PDF/DOCX/HTML export."

certifications:
  - name: AWS Solutions Architect
    issuer: Amazon
    date: 2022-05

languages:
  - language: English
    proficiency: Native

awards:
  - name: Excellence Award
    issuer: Acme Cloud
    date: 2023-02

publications:
  - title: Probabilistic Data Structures at Scale
    venue: ACM Queue
    date: 2020-11

volunteering:
  - organization: CodeUK
    role: Mentor
    start_date: 2019-01
    end_date: Present
    highlights:
      - "Mentored 12 students."

interests: [Climbing, Board games]
"""


@pytest.fixture()
def sample_yaml() -> str:
    """A complete, valid CV as YAML text."""
    return SAMPLE_YAML


@pytest.fixture()
def sample_cv(sample_yaml: str) -> CV:
    """A complete, valid CV object."""
    from cvforge.loader import parse_data

    return parse_data(sample_yaml)


@pytest.fixture()
def photo_png(tmp_path: Path) -> Path:
    """A small square PNG suitable for the circular-crop code path."""
    from PIL import Image

    path = tmp_path / "photo.png"
    Image.new("RGB", (120, 160), color=(37, 99, 235)).save(path)
    return path
