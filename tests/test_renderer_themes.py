"""Tests for theme discovery and HTML rendering."""

from __future__ import annotations

import pytest

from cvforge.markdown_lite import to_html, to_runs
from cvforge.photo import PhotoError, circular_photo_data_uri
from cvforge.renderer import ThemeNotFoundError, ThemeOptions, format_date, render_html
from cvforge.themes import ThemeError, get_theme, list_themes, theme_css

ALL_THEMES = ["classic", "modern", "minimal", "compact"]


class TestDiscovery:
    def test_all_builtin_themes_found(self) -> None:
        names = {t.name for t in list_themes()}
        assert set(ALL_THEMES) <= names

    def test_get_theme_known(self) -> None:
        assert get_theme("modern").supports_photo is True

    def test_get_theme_unknown_lists_available(self) -> None:
        with pytest.raises(ThemeError, match="classic"):
            get_theme("does-not-exist")

    def test_theme_css_loaded(self) -> None:
        assert "classic" in theme_css("classic") or "serif" in theme_css("classic")

    def test_css_missing_raises(self) -> None:
        with pytest.raises(ThemeError, match=r"style\.css"):
            theme_css("classic_nonexistent_dir")


class TestRenderHTML:
    @pytest.mark.parametrize("theme", ALL_THEMES)
    def test_each_theme_renders_standalone_html(self, sample_cv, theme: str) -> None:
        html = render_html(sample_cv, theme=theme)
        assert html.startswith("<!doctype html>")
        assert "Ada Lovelace" in html
        assert "<style>" in html  # CSS is inlined
        assert "Acme Cloud" in html
        assert "**" not in html  # markdown-lite was converted

    def test_markdown_bold_and_link(self, sample_cv) -> None:
        html = render_html(sample_cv, theme="classic")
        assert "<strong>" in html
        assert '<a href="https://github.com/ada/cvforge">cvforge</a>' in html

    def test_options_change_output(self, sample_cv) -> None:
        default = render_html(sample_cv, theme="modern")
        custom = render_html(
            sample_cv,
            theme="modern",
            options=ThemeOptions(accent_color="#FF0000", page_size="Letter"),
        )
        assert "--accent: #FF0000" in custom
        assert "size: Letter" in custom
        assert "--accent: #FF0000" not in default

    def test_photo_embedded_when_supported(self, sample_cv, photo_png) -> None:
        import yaml as yaml_mod

        from cvforge.loader import parse_data

        data = yaml_mod.safe_load(render_yaml_with_photo(photo_png))
        cv = parse_data(yaml_mod.safe_dump(data))
        html = render_html(cv, theme="modern")
        assert "data:image/png;base64," in html
        # classic does not support photos
        assert "data:image/png;base64," not in render_html(cv, theme="classic")

    def test_unknown_theme_raises(self, sample_cv) -> None:
        with pytest.raises(ThemeNotFoundError):
            render_html(sample_cv, theme="nope")

    def test_font_override(self, sample_cv) -> None:
        html = render_html(sample_cv, theme="classic", options=ThemeOptions(font_family="sans"))
        assert "Helvetica" in html


def render_yaml_with_photo(photo_path) -> str:
    """Build a minimal CV YAML with a photo field."""
    return f"basics:\n  full_name: Ada\n  photo: {photo_path.as_posix()}\n"


class TestFormatDate:
    def test_month_names(self) -> None:
        assert format_date("2021-03") == "Mar 2021"

    def test_year_only(self) -> None:
        assert format_date("2021") == "2021"

    def test_present(self) -> None:
        assert format_date("Present") == "Present"

    def test_empty(self) -> None:
        assert format_date(None) == ""
        assert format_date("") == ""

    def test_invalid_month_passes_through(self) -> None:
        assert format_date("2021-13") == "2021-13"


class TestOptions:
    def test_validate_problems(self) -> None:
        opts = ThemeOptions(accent_color="red", font_family="comic", font_size=99, page_size="A0")
        problems = opts.validate()
        assert len(problems) == 4

    def test_valid_options_no_problems(self) -> None:
        assert ThemeOptions().validate() == []


class TestMarkdownLite:
    def test_bold(self) -> None:
        assert to_html("**hi**") == "<strong>hi</strong>"

    def test_italic(self) -> None:
        assert to_html("*hi*") == "<em>hi</em>"

    def test_link(self) -> None:
        assert to_html("[x](https://e.com)") == '<a href="https://e.com">x</a>'

    def test_html_escaped(self) -> None:
        assert to_html("<script>") == "&lt;script&gt;"

    def test_to_runs(self) -> None:
        runs = to_runs("plain **bold** [link](https://e.com) end")
        texts = [r.text for r in runs]
        assert "plain " in texts and "bold" in texts and "link" in texts
        bold_run = next(r for r in runs if r.bold)
        assert bold_run.text == "bold"
        link_run = next(r for r in runs if r.link)
        assert link_run.link == "https://e.com"


class TestPhoto:
    def test_circular_crop(self, photo_png) -> None:
        uri = circular_photo_data_uri(photo_png, size=64)
        assert uri.startswith("data:image/png;base64,")

    def test_missing_photo_raises(self) -> None:
        with pytest.raises(PhotoError, match="not found"):
            circular_photo_data_uri("nope.png")

    def test_non_image_raises(self, tmp_path) -> None:
        path = tmp_path / "x.png"
        path.write_text("not an image", encoding="utf-8")
        with pytest.raises(PhotoError, match="Could not read"):
            circular_photo_data_uri(path)
