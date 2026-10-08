# Contributing to CVForge

Thanks for your interest in improving CVForge! 🎉

## Development setup

```bash
git clone https://github.com/cvforge/cvforge
cd cvforge
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
pre-commit install
```

## Quality gates

CI runs these on Ubuntu and Windows (Python 3.10-3.12) — run them locally first:

```bash
ruff check . && ruff format --check .
mypy              # --strict on src/
pytest --cov=src/cvforge   # coverage must stay at 80%+
```

## How to contribute

1. **Discuss first** for bigger changes: open an issue (feature request) so we
   can agree on the approach before you write code.
2. **Branch** from `main`: `git checkout -b feat/my-feature`.
3. **Commit** small and focused; follow the existing style (imperative subject,
   blank line, explanation of the *why*).
4. **Test**: add pytest coverage for anything behavioural — model validation,
   exporters, CLI commands, checker rules.
5. **Docs**: update `README.md` and record any non-obvious choice in
   `docs/DECISIONS.md`.

## Adding a theme

Themes are folders in `src/cvforge/templates/<name>/` containing
`template.html.j2`, `style.css` and `theme.yaml`. No Python changes are needed
— the folder registers itself. See the README's "Creating a custom theme"
section, and start from `classic/` as a reference. Please include a screenshot
in `docs/` with your PR.

## Reporting bugs

Please include the exact command, the CV data snippet (fictional data only!),
your OS/Python version, and whether PDF export is involved (WeasyPrint system
dependencies are the most common cause — see README Troubleshooting).

## Code of Conduct

By participating you agree to our [Code of Conduct](CODE_OF_CONDUCT.md).
