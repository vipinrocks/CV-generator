"""CVForge web UI, built with Streamlit.

Run locally with:  streamlit run app.py

No data leaves your machine — everything is processed in the browser session
and nothing is stored server-side.
"""

from __future__ import annotations

import io
import json
from typing import Any

import streamlit as st
import yaml

from cvforge.checker import check_cv
from cvforge.exporters.docx import export_docx
from cvforge.exporters.pdf import export_pdf, is_pdf_available
from cvforge.models import CV
from cvforge.renderer import SAFE_FONTS, ThemeOptions
from cvforge.sample import SAMPLE_YAML
from cvforge.themes import list_themes

st.set_page_config(page_title="CVForge", page_icon="📄", layout="wide")

SECTION_LABELS: list[tuple[str, str]] = [
    ("experience", "Experience"),
    ("education", "Education"),
    ("skills", "Skills"),
    ("projects", "Projects"),
    ("certifications", "Certifications"),
    ("languages", "Languages"),
    ("awards", "Awards"),
    ("publications", "Publications"),
    ("volunteering", "Volunteering"),
    ("interests", "Interests"),
]


def init_state() -> None:
    """Seed session state once per browser session."""
    defaults: dict[str, Any] = {
        "theme": "modern",
        "accent_color": "#2563EB",
        "font_family": "auto",
        "font_size": 10,
        "page_size": "A4",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def current_options() -> ThemeOptions:
    """Theme options from the sidebar widgets."""
    return ThemeOptions(
        accent_color=st.session_state.accent_color,
        font_family=st.session_state.font_family,
        font_size=st.session_state.font_size,
        page_size=st.session_state.page_size,
    )


def build_cv_from_state() -> CV | None:
    """Assemble a CV object from the session-state editor widgets."""
    data: dict[str, Any] = {"basics": dict(st.session_state.get("basics", {}))}
    for section, _ in SECTION_LABELS:
        rows = st.session_state.get(section)
        if rows:
            if section == "interests":
                data[section] = [r for r in rows if r and str(r).strip()]
            else:
                cleaned: list[dict[str, Any]] = []
                for row in rows:
                    item = {k: v for k, v in row.items() if v not in (None, "")}
                    if item:
                        cleaned.append(item)
                if cleaned:
                    data[section] = cleaned
    try:
        return CV.model_validate(data)
    except Exception:
        return None


def load_sample() -> None:
    """Replace editor state with the embedded sample CV."""
    data = yaml.safe_load(SAMPLE_YAML)
    st.session_state["basics"] = data["basics"]
    for section, _ in SECTION_LABELS:
        rows = data.get(section, [])
        if section == "interests":
            rows = [{0: tag} for tag in rows]  # placeholder, editor below handles lists
        st.session_state[section] = _to_rows(section, data.get(section, []))
    st.rerun()


def _to_rows(section: str, items: list[Any]) -> list[dict[str, Any]]:
    """Normalise loaded items into row dicts for st.data_editor."""
    if section == "interests":
        return [{"interest": tag} for tag in items]
    return [dict(item) for item in items]


def upload_file() -> None:
    """Load an uploaded YAML/JSON file into the editor state."""
    file = st.session_state.get("uploaded")
    if not file:
        return
    try:
        data = yaml.safe_load(file.getvalue().decode("utf-8"))
        cv = CV.model_validate(data)
    except Exception as exc:
        st.sidebar.error(f"Could not load file: {exc}")
        return
    st.session_state["basics"] = dict(cv.basics.model_dump(exclude_none=True))
    for section, _ in SECTION_LABELS:
        st.session_state[section] = _to_rows(section, getattr(cv, section))
    st.sidebar.success("Loaded!")


def main() -> None:
    """Render the CVForge web app."""
    init_state()

    with st.sidebar:
        st.header("⚙️ Options")
        themes = {t.name: t for t in list_themes()}
        st.selectbox(
            "Theme",
            options=list(themes),
            key="theme",
            help=themes[st.session_state.theme].description,
        )
        if not themes[st.session_state.theme].supports_photo:
            st.caption("This theme hides photos.")
        st.color_picker("Accent colour", key="accent_color")
        st.selectbox("Font", options=list(SAFE_FONTS), key="font_family")
        st.slider("Font size (pt)", 7, 14, key="font_size")
        st.selectbox("Page size", ["A4", "Letter"], key="page_size")

        st.divider()
        st.subheader("📂 Data")
        st.button("📋 Load sample data", on_click=load_sample, width="stretch")
        st.file_uploader(
            "Upload YAML/JSON",
            type=["yaml", "yml", "json"],
            key="uploaded",
            on_change=upload_file,
        )

    st.title("📄 CVForge")
    tabs = st.tabs(["Basics"] + [label for _, label in SECTION_LABELS] + ["✅ Tips"])

    # --- Basics tab ---------------------------------------------------------
    with tabs[0]:
        basics = st.session_state.get("basics", {})
        cols = st.columns(2)
        with cols[0]:
            basics["full_name"] = st.text_input("Full name *", basics.get("full_name", ""))
            basics["headline"] = st.text_input("Headline", basics.get("headline") or "")
            basics["email"] = st.text_input("Email", basics.get("email") or "")
            basics["phone"] = st.text_input("Phone", basics.get("phone") or "")
        with cols[1]:
            basics["location"] = st.text_input("Location", basics.get("location") or "")
            basics["website"] = st.text_input("Website", basics.get("website") or "")
            basics["linkedin"] = st.text_input("LinkedIn URL", basics.get("linkedin") or "")
            basics["github"] = st.text_input("GitHub URL", basics.get("github") or "")
        basics["summary"] = st.text_area("Summary", basics.get("summary") or "", height=120)
        uploaded_photo = st.file_uploader(
            "Profile photo (optional, circular crop)", type=["png", "jpg", "jpeg", "webp"]
        )
        if uploaded_photo:
            from cvforge.photo import PhotoError, circular_photo_data_uri

            st.session_state["photo_bytes"] = uploaded_photo.getvalue()
            st.session_state["photo_name"] = uploaded_photo.name
            try:
                st.image(
                    circular_photo_data_uri(io.BytesIO(st.session_state["photo_bytes"])), width=100
                )
            except PhotoError as exc:
                st.warning(str(exc))
        elif "photo_bytes" in st.session_state:
            del st.session_state["photo_bytes"]
        st.session_state["basics"] = basics

    # --- List-section tabs ---------------------------------------------------
    column_configs = {
        "experience": {
            "company": "Company",
            "role": "Role",
            "location": "Location",
            "start_date": "Start (YYYY-MM)",
            "end_date": "End / Present",
            "highlights": st.column_config.ListColumn("Highlights"),
        },
        "education": {
            "institution": "Institution",
            "degree": "Degree",
            "field": "Field",
            "start_date": "Start",
            "end_date": "End",
            "grade": "Grade",
            "notes": "Notes",
        },
        "skills": {
            "name": "Group",
            "skills": st.column_config.ListColumn("Skills"),
        },
        "projects": {
            "name": "Name",
            "url": "URL",
            "description": "Description",
            "highlights": st.column_config.ListColumn("Highlights"),
            "tech": st.column_config.ListColumn("Tech"),
        },
        "certifications": {
            "name": "Name",
            "issuer": "Issuer",
            "date": "Date",
            "url": "URL",
        },
        "languages": {"language": "Language", "proficiency": "Proficiency"},
        "awards": {
            "name": "Name",
            "issuer": "Issuer",
            "date": "Date",
            "description": "Description",
        },
        "publications": {"title": "Title", "venue": "Venue", "date": "Date", "url": "URL"},
        "volunteering": {
            "organization": "Organization",
            "role": "Role",
            "start_date": "Start",
            "end_date": "End",
            "highlights": st.column_config.ListColumn("Highlights"),
        },
        "interests": {"interest": "Interest"},
    }

    for i, (section, _) in enumerate(SECTION_LABELS, start=1):
        with tabs[i]:
            rows = st.session_state.get(section) or []
            edited = st.data_editor(
                rows,
                num_rows="dynamic",
                width="stretch",
                column_config=column_configs[section],
                key=f"editor_{section}",
            )
            st.session_state[section] = edited if isinstance(edited, list) else list(edited)

    # --- Tips tab -------------------------------------------------------------
    cv = build_cv_from_state()
    with tabs[-1]:
        if cv is None:
            st.warning("Fill in at least the full name to validate.")
        else:
            findings = check_cv(cv)
            if not findings:
                st.success("No issues found — great CV!")
            for f in findings:
                icon = {"error": "🔴", "warning": "🟠", "info": "🔵"}[f.severity]
                st.markdown(f"{icon} **{f.section}** — {f.message}")

    # --- Downloads -------------------------------------------------------------
    st.divider()
    dl1, dl2, dl3 = st.columns(3)
    if cv is not None:
        options = current_options()
        try:
            html_str = _render_html_str(cv, st.session_state.theme, options)
        except Exception as exc:
            st.error(f"Render failed: {exc}")
            html_str = None

        if html_str:
            with dl1:
                st.download_button(
                    "⬇️ Download HTML", html_str, "cv.html", "text/html", width="stretch"
                )
            with dl2:
                st.download_button(
                    "⬇️ Download YAML",
                    yaml.safe_dump(
                        json.loads(cv.model_dump_json()), allow_unicode=True, sort_keys=False
                    ),
                    "cv.yaml",
                    "text/yaml",
                    width="stretch",
                )
            with dl3:
                st.download_button(
                    "⬇️ Download JSON",
                    cv.model_dump_json(indent=2),
                    "cv.json",
                    "application/json",
                    width="stretch",
                )

            try:
                docx_buffer = _render_docx_bytes(cv)
                with dl2:
                    st.download_button(
                        "⬇️ Download DOCX",
                        docx_buffer,
                        "cv.docx",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        width="stretch",
                    )
            except Exception as exc:
                st.error(f"DOCX export failed: {exc}")

            if is_pdf_available():
                try:
                    pdf_bytes = _render_pdf_bytes(cv, st.session_state.theme, options)
                    with dl1:
                        st.download_button(
                            "⬇️ Download PDF",
                            pdf_bytes,
                            "cv.pdf",
                            "application/pdf",
                            width="stretch",
                        )
                except Exception as exc:
                    st.error(f"PDF export failed: {exc}")
            else:
                st.info(
                    "PDF export needs WeasyPrint system libraries (see README). "
                    "HTML and DOCX downloads still work."
                )

        # --- Live preview ---
        if html_str:
            st.subheader("Live preview")
            st.components.v1.html(html_str, height=900, scrolling=True)

    st.markdown(
        "<hr style='margin-top:2rem'><p style='color:gray;font-size:0.85em'>"
        "🔒 Privacy: everything is processed locally in your browser session — "
        "no data is stored server-side.</p>",
        unsafe_allow_html=True,
    )


def _render_html_str(cv: CV, theme: str, options: ThemeOptions) -> str:
    """Render CV to an HTML string (not a file)."""
    from cvforge.renderer import render_html

    return render_html(cv, theme=theme, options=options)


def _render_docx_bytes(cv: CV) -> bytes:
    """Export CV to DOCX and return the bytes."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cv.docx"
        export_docx(cv, path)
        return path.read_bytes()


def _render_pdf_bytes(cv: CV, theme: str, options: ThemeOptions) -> bytes:
    """Export CV to PDF and return the bytes."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "cv.pdf"
        export_pdf(cv, path, theme=theme, options=options)
        return path.read_bytes()


if __name__ == "__main__":
    main()
