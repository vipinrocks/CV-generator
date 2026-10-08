# Changelog

All notable changes to CVForge are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and the project adheres to [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-10-08

### Added

- Pydantic v2 data models with email/URL/date validation, friendly field-level
  errors, and automatic reverse-chronological sorting of experience, education
  and volunteering.
- YAML and JSON loading (`cvforge init`, `cvforge validate`) with UTF-8 support.
- Four built-in themes: `classic`, `modern`, `minimal`, `compact` — each a
  Jinja2 template + CSS + `theme.yaml` descriptor, discovered automatically
  (drop a folder to register a new theme).
- Configurable accent colour, font family (safe list), font size, page size
  and margins.
- Exporters: standalone HTML (inlined CSS), PDF via WeasyPrint (graceful
  fallback with clear instructions when system libraries are missing), and
  editable DOCX via python-docx.
- `cvforge` CLI: `init`, `wizard`, `validate`, `build`, `themes`, `preview`
  with `--verbose`/`--quiet`, Rich progress and output summaries.
- CV tips checker: summary length, action verbs, metrics, missing contact
  info, estimated page count.
- Optional circular-cropped profile photo (Pillow) embedded as data URI.
- Markdown-lite in bullets: `**bold**`, `*italic*`, `[links](URL)`.
- Streamlit web UI (`app.py`) with live preview, downloads and privacy notice.
- Test suite (80%+ coverage), ruff + mypy --strict clean, GitHub Actions CI
  (Ubuntu + Windows, Python 3.10-3.12), release workflow with trusted
  publishing, pre-commit hooks.
- Dockerfile and devcontainer for Codespaces.
