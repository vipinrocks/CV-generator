"""CLI tests via Typer's CliRunner."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

import cvforge.cli as cli_mod
from cvforge.cli import app

runner = CliRunner()


@pytest.fixture(autouse=True)
def _reset_flags() -> None:
    """Reset module-level verbosity flags between tests."""
    cli_mod._quiet = False
    cli_mod._verbose = False
    yield
    cli_mod._quiet = False
    cli_mod._verbose = False


def test_version_and_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "build" in result.output


class TestInit:
    def test_creates_sample(self, tmp_path: Path) -> None:
        out = tmp_path / "cv.yaml"
        result = runner.invoke(app, ["init", str(out)])
        assert result.exit_code == 0
        assert out.is_file()
        assert "full_name" in out.read_text(encoding="utf-8")

    def test_refuses_overwrite_without_force(self, tmp_path: Path) -> None:
        out = tmp_path / "cv.yaml"
        out.write_text("keep me", encoding="utf-8")
        result = runner.invoke(app, ["init", str(out)])
        assert result.exit_code == 1
        assert out.read_text(encoding="utf-8") == "keep me"

    def test_force_overwrites(self, tmp_path: Path) -> None:
        out = tmp_path / "cv.yaml"
        out.write_text("keep me", encoding="utf-8")
        result = runner.invoke(app, ["init", str(out), "--force"])
        assert result.exit_code == 0
        assert "full_name" in out.read_text(encoding="utf-8")


class TestValidate:
    def test_valid_file(self, tmp_path: Path, sample_yaml: str) -> None:
        path = tmp_path / "cv.yaml"
        path.write_text(sample_yaml, encoding="utf-8")
        result = runner.invoke(app, ["validate", str(path), "--no-tips"])
        assert result.exit_code == 0
        assert "valid" in result.output.lower()

    def test_invalid_file_exit_code_2(self, tmp_path: Path) -> None:
        path = tmp_path / "cv.yaml"
        path.write_text("basics:\n  full_name: A\n  email: nope\n", encoding="utf-8")
        result = runner.invoke(app, ["validate", str(path)])
        assert result.exit_code == 2
        assert "email" in result.output

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        result = runner.invoke(app, ["validate", str(tmp_path / "nope.yaml")])
        assert result.exit_code != 0


class TestThemes:
    def test_lists_all_themes(self) -> None:
        result = runner.invoke(app, ["themes"])
        assert result.exit_code == 0
        for theme in ("classic", "modern", "minimal", "compact"):
            assert theme in result.output


class TestBuild:
    def test_build_html_and_docx(self, tmp_path: Path, sample_yaml: str) -> None:
        cv_file = tmp_path / "cv.yaml"
        cv_file.write_text(sample_yaml, encoding="utf-8")
        out_dir = tmp_path / "dist"
        result = runner.invoke(
            app,
            [
                "build",
                str(cv_file),
                "--theme",
                "modern",
                "--format",
                "html,docx",
                "--out",
                str(out_dir),
            ],
        )
        assert result.exit_code == 0, result.output
        assert (out_dir / "cv_modern.html").is_file()
        assert (out_dir / "cv_modern.docx").is_file()

    def test_build_pdf_with_fallback(self, tmp_path: Path, sample_yaml: str) -> None:
        cv_file = tmp_path / "cv.yaml"
        cv_file.write_text(sample_yaml, encoding="utf-8")
        out_dir = tmp_path / "dist"
        result = runner.invoke(
            app,
            ["build", str(cv_file), "--format", "pdf,html", "--out", str(out_dir)],
        )
        assert result.exit_code == 0, result.output
        assert (out_dir / "cv_classic.html").is_file()
        if not cli_mod_export_pdf_available():
            assert not (out_dir / "cv_classic.pdf").exists()
            assert "PDF" in result.output  # warning shown

    def test_build_invalid_cv_exit_2(self, tmp_path: Path) -> None:
        cv_file = tmp_path / "cv.yaml"
        cv_file.write_text("basics: {}", encoding="utf-8")
        result = runner.invoke(app, ["build", str(cv_file)])
        assert result.exit_code == 2

    def test_unknown_format(self, tmp_path: Path, sample_yaml: str) -> None:
        cv_file = tmp_path / "cv.yaml"
        cv_file.write_text(sample_yaml, encoding="utf-8")
        result = runner.invoke(
            app, ["build", str(cv_file), "--format", "pptx", "--out", str(tmp_path)]
        )
        assert result.exit_code == 2
        assert "Unknown format" in result.output

    def test_bad_theme(self, tmp_path: Path, sample_yaml: str) -> None:
        cv_file = tmp_path / "cv.yaml"
        cv_file.write_text(sample_yaml, encoding="utf-8")
        result = runner.invoke(
            app,
            ["build", str(cv_file), "--theme", "nope", "--format", "html", "--out", str(tmp_path)],
        )
        assert result.exit_code != 0

    def test_quiet_flag_suppresses_info(self, tmp_path: Path, sample_yaml: str) -> None:
        cv_file = tmp_path / "cv.yaml"
        cv_file.write_text(sample_yaml, encoding="utf-8")
        out_dir = tmp_path / "dist"
        result = runner.invoke(
            app,
            ["--quiet", "build", str(cv_file), "--format", "html", "--out", str(out_dir)],
        )
        assert result.exit_code == 0
        assert (out_dir / "cv_classic.html").is_file()


def cli_mod_export_pdf_available() -> bool:
    """Whether this machine can actually render PDFs."""
    from cvforge.exporters.pdf import is_pdf_available

    return is_pdf_available()


class TestPreview:
    def test_preview_writes_html_and_skips_browser(
        self, tmp_path: Path, sample_yaml: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cv_file = tmp_path / "cv.yaml"
        cv_file.write_text(sample_yaml, encoding="utf-8")
        opened: list[str] = []
        monkeypatch.setattr("webbrowser.open", lambda uri: opened.append(uri) or True)
        result = runner.invoke(app, ["preview", str(cv_file)])
        assert result.exit_code == 0, result.output
        assert opened, "browser should have been opened"
        assert "cvforge_preview" in opened[0]


class TestWizard:
    def test_wizard_builds_yaml(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        # Simulate prompts: full name, headline, email/phone/location/website/
        # linkedin/github, summary, no experience, no skills.
        answers = iter(["Test User", "", "t@e.co", "", "", "", "", "", "A summary.", "n", "n"])
        monkeypatch.setattr("typer.prompt", lambda *a, **k: next(answers))
        monkeypatch.setattr("typer.confirm", lambda *a, **k: False)
        out = tmp_path / "wizard.yaml"
        result = runner.invoke(app, ["wizard", "--output", str(out)])
        assert result.exit_code == 0, result.output
        text = out.read_text(encoding="utf-8")
        assert "Test User" in text
        assert "t@e.co" in text
