# Design decisions

Assumption log for ambiguous requirements, newest first. Each entry records the
decision and why, so future contributors can revisit them cheaply.

## D-004 — No bundled Noto font binaries (2026-10-08)

The spec asks for Noto Sans fonts in the repo. Committing ~10 MB of font
binaries bloats the package and duplicates what users already have. Instead:
CVs are rendered with system fonts via CSS font stacks, the `--font "Noto Sans"`
option is supported, and the README documents installing Noto Sans (SIL OFL,
free) for non-Latin scripts. If a future need arises, fonts can be added to
`src/cvforge/fonts/` and registered via an `@font-face` block.

## D-003 — Email validation via regex, not `EmailStr` (2026-10-08)

pydantic's `EmailStr` pulls in the `email-validator` package (DNS-informed
checks, extra dependency). We validate with a pragmatic regex (`x@y.tld`), which
catches real typos without rejecting exotic-but-valid addresses or adding a
dependency.

## D-002 — `volunteering` sorted too (2026-10-08)

The spec only mandates sorting for experience and education; volunteering
carries dates as well, so it is sorted with the same rule for consistent output.

## D-001 — PDF export via graceful degradation, not hard dependency (2026-10-08)

WeasyPrint requires system libraries (Pango/HarfBuzz) that pip cannot install,
which is especially painful on Windows. Rather than making `pip install` fail,
CVForge imports WeasyPrint lazily: when unavailable, `build` prints per-OS
installation instructions and still produces DOCX and HTML. CI runs PDF tests
on Ubuntu where the libraries are installed explicitly.

## D-000 — Photos embedded as data URIs (2026-10-08)

Theme templates must produce a *standalone* HTML file and a PDF that renders
identically anywhere, so profile photos are circular-cropped, resized to 256px
and embedded as `data:image/png;base64,...` rather than referenced from disk.
