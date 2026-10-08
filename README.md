# 📄 CVForge

**A professional, ATS-friendly CV/resume generator.** Fill in your details as YAML/JSON (or via the web UI) and get a beautifully designed CV as **PDF**, **DOCX** and **HTML** — all processed locally, no accounts, no telemetry.

<p align="center">
  <a href="https://github.com/cvforge/cvforge/actions"><img alt="CI" src="https://github.com/cvforge/cvforge/actions/workflows/ci.yml/badge.svg"></a>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-green.svg"></a>
  <a href="https://share.streamlit.io"><img alt="Live demo" src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg"></a>
</p>

> **Live demo:** the badge above is a placeholder — after deploying to Streamlit
> Community Cloud, point it at your app URL (see [Deployment](#-deployment)).

## ✨ Features

- **4 built-in themes** — `classic` (ATS-safe serif), `modern` (coloured sidebar),
  `minimal` (whitespace-heavy), `compact` (one page). Plugin-style: drop a folder
  into `src/cvforge/templates/` and it registers automatically.
- **3 output formats** — selectable-text PDF (via WeasyPrint), editable DOCX
  (python-docx), standalone HTML with inlined CSS. Build all three in one command.
- **Validation with friendly errors** — pydantic v2 under the hood; problems point
  at the exact field, e.g. `basics.email: 'foo' is not a valid email address`.
- **CV tips checker** — flags overlong summaries, bullets without action verbs or
  metrics, missing contact info, and CVs estimated at 3+ pages.
- **Optional circular-cropped profile photo**, markdown-lite in bullets
  (`**bold**`, `*italic*`, `[links](https://…)`) and UTF-8 everywhere.
- **Web UI** — Streamlit app with live preview and downloads. Nothing is stored
  server-side.

## 🚀 Quick start

```bash
# 1. Install (from a clone)
git clone https://github.com/cvforge/cvforge
cd cvforge
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install .

# 2. Create your CV data
cvforge init            # writes cv.yaml with a fully-commented sample
cvforge validate cv.yaml

# 3. Build
cvforge build cv.yaml --theme modern --format pdf,docx,html --out ./dist
```

Outputs land in `./dist/`: `cv_modern.pdf`, `cv_modern.docx`, `cv_modern.html`.

Other commands:

```bash
cvforge wizard          # interactive Q&A that builds cv.yaml
cvforge themes          # list available themes
cvforge preview cv.yaml # open the HTML in your browser
cvforge build --help    # accent colour, font, font size, page size flags
```

### Web UI

```bash
pip install streamlit
streamlit run app.py
```

## 🎨 Theme gallery

| Theme | Look | Photo | Best for |
|---|---|---|---|
| `classic` | Single column, serif, conservative | — | ATS maximum compatibility |
| `modern` | Two-column, coloured sidebar | ✓ | Tech / creative roles |
| `minimal` | Whitespace, thin dividers | ✓ | Design-conscious applicants |
| `compact` | Dense one-page, two columns | ✓ | Senior profiles, career changers |

*(Screenshots live in [`docs/`](docs/) — see the theme gallery there.)*

Configure any theme with `--accent`, `--font`, `--font-size` and `--page-size`:

```bash
cvforge build cv.yaml --theme minimal --accent "#0F766E" --font noto_sans --page-size Letter
```

## 📝 YAML schema reference

Only `basics` is required; every other section is optional and hidden when empty.
Dates are `YYYY` or `YYYY-MM`; experience `end_date` may also be `Present`.
Experience and education are sorted newest-first automatically.

```yaml
basics:                       # REQUIRED
  full_name: Ada Lovelace     # required
  headline: Senior Software Engineer
  email: ada@example.com      # validated
  phone: "+44 20 7946 0958"
  location: London, UK
  website: https://ada.dev    # must be http(s) URL
  linkedin: https://www.linkedin.com/in/ada
  github: https://github.com/ada
  summary: >-                 # markdown-lite allowed: **bold**, *italic*, [links](URL)
    Engineer with 8+ years of experience. **Led** a migration cutting
    deploy time by 70%.
  photo: photo.jpg            # optional; circular-cropped in themes that support it

experience:
  - company: Acme Cloud
    role: Senior Software Engineer
    location: London, UK
    start_date: 2021-03
    end_date: Present         # or a date, or omit
    highlights:
      - "**Led** a team of 5, cutting deploy time by 70%."

education:
  - institution: University of Manchester
    degree: BSc
    field: Computer Science
    start_date: 2013-09
    end_date: 2017-06
    grade: First Class Honours
    notes: Dissertation on probabilistic data structures.

skills:
  - name: Languages
    skills: [Python, Go, SQL]

projects:
  - name: cvforge
    url: https://github.com/ada/cvforge
    description: CV generator.
    tech: [Python, pydantic]
    highlights:
      - "Shipped PDF/DOCX/HTML export."

certifications:
  - name: AWS Solutions Architect
    issuer: Amazon
    date: 2022-05
    url: https://aws.amazon.com/verification

languages:
  - language: English
    proficiency: Native

awards:
  - name: Excellence Award
    issuer: Acme Cloud
    date: 2023-02
    description: For the microservices migration.

publications:
  - title: Probabilistic Data Structures at Scale
    venue: ACM Queue
    date: 2020-11
    url: https://example.com/paper

volunteering:
  - organization: CodeUK
    role: Mentor
    start_date: 2019-01
    end_date: Present
    highlights:
      - "Mentored 12 students."

interests: [Climbing, Board games]
```

Full runnable examples: [`examples/sample_cv.yaml`](examples/sample_cv.yaml) and
[`examples/sample_cv.json`](examples/sample_cv.json).

## 🖥️ WeasyPrint system dependencies (PDF)

WeasyPrint needs Pango/HarfBuzz system libraries. HTML and DOCX exports work
without them — if WeasyPrint is missing, CVForge prints a clear message and
still produces DOCX and HTML.

| OS | Install |
|---|---|
| Debian/Ubuntu | `sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b` |
| macOS | `brew install pango` |
| Windows | Install the **GTK3 runtime** via MSYS2: `pacman -S mingw-w64-x86_64-pango`, then add `C:\msys64\mingw64\bin` to your `PATH` (or install the [GTK3 runtime installer](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer)) |

## 🌍 Fonts / non-Latin scripts

PDFs render with your system fonts. For Hindi and other non-Latin scripts,
install [Noto Sans](https://fonts.google.com/noto) (SIL Open Font License) and
use `--font "Noto Sans"`. All processing is UTF-8 end to end.

## 🎨 Creating a custom theme

1. Create a folder `src/cvforge/templates/mytheme/` containing:
   - `template.html.j2` — Jinja2 template (see `classic/` for a reference; shared
     macros are in `templates/_macros.html.j2`)
   - `style.css` — the theme stylesheet (use the CSS variables `--accent`,
     `--font-body`, `--font-size`)
   - `theme.yaml` — descriptor: `name`, `description`, `supports_photo`, `options`
2. Reinstall (`pip install -e .`) or, if already editable-installed, nothing —
   the theme is discovered automatically.

## ☁️ Deployment

### Streamlit Community Cloud (free)

1. Fork/push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app** → pick your repo.
3. Main file: `app.py`. Streamlit Cloud reads `requirements.txt` and
   `packages.txt` (APT deps for WeasyPrint) automatically.
4. Deploy — the badge at the top becomes your live demo link.

### Docker (optional)

```bash
docker build -t cvforge .
docker run -p 8501:8501 cvforge
```

### GitHub Pages (optional)

`docs/index.html` is a static landing page with the theme gallery — enable
GitHub Pages on the `main` branch `/docs` folder.

## 🧪 Development

```bash
pip install -e '.[dev]'
pre-commit install
pytest --cov=src/cvforge     # tests + coverage (80%+ enforced in CI)
ruff check . && ruff format --check .
mypy                          # --strict on src/
```

## 🩺 Troubleshooting

- **"PDF export is unavailable"** — install the WeasyPrint system deps for your
  OS (table above). DOCX/HTML still work.
- **Non-Latin text shows as boxes in the PDF** — install Noto Sans for your
  language and pass `--font "Noto Sans"`.
- **`pip install` fails on Windows** — WeasyPrint is a normal pip package; the
  failure is usually the missing GTK runtime *at render time*, not install time.
- **Theme not found** — check the folder name matches `theme.yaml`'s `name` and
  that the folder sits directly under `src/cvforge/templates/`.

## 🗺️ Roadmap

- [ ] Live reload preview server (`cvforge serve`)
- [ ] Cover-letter generator sharing the same data
- [ ] More themes (timeline, executive)
- [ ] PDF/A export for long-term archiving

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and our
[Code of Conduct](CODE_OF_CONDUCT.md). Design decisions are recorded in
[docs/DECISIONS.md](docs/DECISIONS.md).

## 📄 License

[MIT](LICENSE) — free and open source, forever.
