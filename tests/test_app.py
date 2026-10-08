"""Smoke tests for the Streamlit app using streamlit.testing.AppTest."""

from __future__ import annotations

from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit")


@pytest.fixture()
def app_path() -> Path:
    """Path to the Streamlit app at the repository root."""
    return Path(__file__).parent.parent / "app.py"


def test_app_runs_without_exceptions(app_path: Path) -> None:
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(app_path, default_timeout=120)
    at.run()
    assert [e.value for e in at.exception] == []


def test_app_loads_sample_data(app_path: Path) -> None:
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(app_path, default_timeout=120)
    at.run()
    # Click "Load sample data" and make sure the app still runs cleanly.
    at.button[0].click().run()
    assert [e.value for e in at.exception] == []
