"""Tests for the HTML, DOCX and PDF exporters."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from cvforge.exporters.docx import export_docx
from cvforge.exporters.html import export_html
from cvforge.exporters.pdf import export_pdf, is_pdf_available
from cvforge.models import CV, ExportError
from cvforge.renderer import ThemeOptions

ALL_THEMES = ["classic", "modern", "minimal", "compact"]


class TestHTMLExporter:
    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_writes_standalone_file(self, tmp_path: Path, sample_cv: CV, theme: str) -> None:
        out = export_html(sample_cv, tmp_path / f"{theme}.html", theme=theme)
        assert out.is_file()
        text = out.read_text(encoding="utf-8")
        assert text.startswith("<!doctype html>")
        assert "Ada Lovelace" in text
        assert "<style>" in text
        assert "<script" not in text.lower()

    def test_creates_parent_dirs(self, tmp_path: Path, sample_cv: CV) -> None:
        out = export_html(sample_cv, tmp_path / "a" / "b" / "cv.html")
        assert out.is_file()


class TestDocxExporter:
    def test_valid_docx_with_name(self, tmp_path: Path, sample_cv: CV) -> None:
        out = export_docx(sample_cv, tmp_path / "cv.docx")
        assert out.is_file()
        with zipfile.ZipFile(out) as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
        assert "Ada Lovelace" in doc
        assert "Acme Cloud" in doc
        assert "Experience" in doc
        assert "Skills" in doc

    def test_docx_has_bullets_and_hyperlink(self, tmp_path: Path, sample_cv: CV) -> None:
        out = export_docx(sample_cv, tmp_path / "cv.docx")
        with zipfile.ZipFile(out) as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
            rels = zf.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "ListBullet" in doc
        assert "hyperlink" in doc
        assert "github.com/ada/cvforge" in rels

    def test_minimal_cv_exports(self, tmp_path: Path) -> None:
        cv = CV.model_validate({"basics": {"full_name": "Just Name"}})
        out = export_docx(cv, tmp_path / "min.docx")
        with zipfile.ZipFile(out) as zf:
            doc = zf.read("word/document.xml").decode("utf-8")
        assert "Just Name" in doc

    def test_photo_embedded(self, tmp_path: Path, sample_cv: CV, photo_png: Path) -> None:
        sample_cv.basics.photo = str(photo_png)
        out = export_docx(sample_cv, tmp_path / "photo.docx")
        with zipfile.ZipFile(out) as zf:
            media = [n for n in zf.namelist() if n.startswith("word/media/")]
        assert media

    def test_broken_photo_ignored(self, tmp_path: Path, sample_cv: CV) -> None:
        sample_cv.basics.photo = str(tmp_path / "missing.png")
        out = export_docx(sample_cv, tmp_path / "cv.docx")
        assert out.is_file()


@pytest.mark.skipif(not is_pdf_available(), reason="WeasyPrint system libraries unavailable")
class TestPDFExporter:
    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_pdf_single_page_with_extractable_text(
        self, tmp_path: Path, sample_cv: CV, theme: str
    ) -> None:
        from pypdf import PdfReader

        out = export_pdf(sample_cv, tmp_path / f"{theme}.pdf", theme=theme)
        assert out.is_file() and out.stat().st_size > 1000

        reader = PdfReader(out)
        text = "".join(page.extract_text() or "" for page in reader.pages)
        assert "Ada Lovelace" in text
        assert "Acme Cloud" in text
        # The sample data must fit on a single page in every theme.
        assert len(reader.pages) == 1, f"{theme} overflowed to {len(reader.pages)} pages"

    def test_pdf_letter_page_size(self, tmp_path: Path, sample_cv: CV) -> None:
        from pypdf import PdfReader

        out = export_pdf(
            sample_cv,
            tmp_path / "letter.pdf",
            options=ThemeOptions(page_size="Letter"),
        )
        box = PdfReader(out).pages[0].mediabox
        assert abs(float(box.width) - 612) < 2  # Letter = 612x792pt
        assert abs(float(box.height) - 792) < 2


def test_pdf_fallback_error_when_unavailable(
    tmp_path: Path, sample_cv: CV, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Even when WeasyPrint works, callers must get a clean ExportError contract."""
    import cvforge.exporters.pdf as pdf_mod

    monkeypatch.setattr(pdf_mod, "is_pdf_available", lambda: False)
    with pytest.raises(ExportError, match="WeasyPrint"):
        export_pdf(sample_cv, tmp_path / "x.pdf")
