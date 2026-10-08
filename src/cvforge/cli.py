"""The ``cvforge`` command-line interface, built with Typer and Rich."""

from __future__ import annotations

import json
import sys
import tempfile
import webbrowser
from contextlib import suppress
from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from cvforge.checker import check_cv
from cvforge.exporters.docx import export_docx
from cvforge.exporters.html import export_html
from cvforge.exporters.pdf import export_pdf
from cvforge.loader import LoadError, load_cv, parse_data, save_yaml
from cvforge.models import CV, CVForgeError, ExportError, ValidationErrorCV
from cvforge.renderer import SAFE_FONTS, ThemeOptions
from cvforge.sample import SAMPLE_YAML
from cvforge.themes import ThemeError, list_themes

app = typer.Typer(
    name="cvforge",
    help="Generate professional, ATS-friendly CVs as PDF, DOCX and HTML.",
    no_args_is_help=True,
    add_completion=False,
)

console = Console()
err_console = Console(stderr=True)


def _force_utf8_stdio() -> None:
    """Make Unicode output work on Windows consoles (cp1252 default)."""
    for stream in (sys.stdout, sys.stderr):
        if stream is not None and hasattr(stream, "reconfigure"):
            with suppress(OSError, ValueError):  # pragma: no cover - exotic streams
                stream.reconfigure(encoding="utf-8")


_force_utf8_stdio()

#: Set by the global callback; controls output noise.
_quiet = False
_verbose = False


def _info(message: str) -> None:
    """Print unless ``--quiet``."""
    if not _quiet:
        console.print(message)


def _warn(message: str) -> None:
    """Print a warning unless ``--quiet``."""
    if not _quiet:
        err_console.print(f"[yellow]![/yellow] {message}")


def _fail(message: str, code: int = 1) -> None:
    """Print an error panel and exit with *code*."""
    err_console.print(Panel(message, title="Error", border_style="red"))
    raise typer.Exit(code)


def _set_verbosity(verbose: bool, quiet: bool) -> None:
    """Apply verbosity flags, usable from the global callback or any command."""
    global _quiet, _verbose
    _quiet = quiet
    _verbose = verbose and not quiet


#: Options block shared by every command so ``--quiet`` works both before and
#: after the subcommand (e.g. ``cvforge build --quiet cv.yaml``).
VerboseOpt = Annotated[bool, typer.Option("--verbose", "-v", help="Show detailed output.")]
QuietOpt = Annotated[bool, typer.Option("--quiet", "-q", help="Only show errors.")]


@app.callback()
def _main(
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
) -> None:
    """CVForge — generate professional CVs from YAML/JSON data."""
    _set_verbosity(verbose, quiet)


@app.command()
def init(
    path: Path = typer.Argument(Path("cv.yaml"), help="Where to write the sample CV."),
    force: bool = typer.Option(False, "--force", "-f", help="Overwrite an existing file."),
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
) -> None:
    """Create a sample cv.yaml to edit."""
    _set_verbosity(verbose, quiet)
    if path.exists() and not force:
        _fail(f"'{path}' already exists. Use --force to overwrite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(SAMPLE_YAML, encoding="utf-8")
    _info(
        f"[green]✓[/green] Created [bold]{path}[/bold] — edit it, then run:\n"
        f"  cvforge validate {path}\n  cvforge build {path} --theme modern"
    )


@app.command()
def wizard(
    output: Path = typer.Option(Path("cv.yaml"), "--output", "-o", help="File to write."),
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
) -> None:
    """Interactive Q&A that builds a cv.yaml step by step."""
    _set_verbosity(verbose, quiet)
    _info("[bold]CVForge wizard[/bold] — press Enter to skip any question.\n")

    def ask(label: str, default: str = "") -> str:
        """Prompt once, returning the trimmed answer or the default."""
        answer = typer.prompt(label, default=default, show_default=False)
        return str(answer).strip()

    basics: dict[str, Any] = {"full_name": ask("Full name")}
    headline = ask("Headline / job title")
    if headline:
        basics["headline"] = headline
    for field in ("email", "phone", "location", "website", "linkedin", "github"):
        value = ask(field)
        if value:
            basics[field] = value
    summary = ask("Professional summary (2-3 sentences)")
    if summary:
        basics["summary"] = summary

    experience: list[dict[str, Any]] = []
    while typer.confirm("Add an experience entry?", default=bool(experience) or False):
        company = ask("Company")
        role = ask("Role")
        entry: dict[str, Any] = {"company": company, "role": role}
        if loc := ask("Location"):
            entry["location"] = loc
        entry["start_date"] = ask("Start date (YYYY-MM)")
        entry["end_date"] = ask("End date (YYYY-MM or 'Present')", "Present")
        highlights = []
        while typer.confirm("Add a bullet point?", default=True):
            highlights.append(ask("Bullet (e.g. 'Led X, reducing Y by 30%')"))
            if not typer.confirm("Add another bullet?", default=False):
                break
        if highlights:
            entry["highlights"] = highlights
        experience.append(entry)

    skills: list[dict[str, Any]] = []
    while typer.confirm("Add a skill group?", default=False):
        name = ask("Group name (e.g. 'Languages')")
        items = [s.strip() for s in ask("Skills (comma-separated)").split(",") if s.strip()]
        if items:
            skills.append({"name": name, "skills": items})

    data: dict[str, Any] = {"basics": basics}
    if experience:
        data["experience"] = experience
    if skills:
        data["skills"] = skills

    with console.status("Saving…"):
        cv = parse_data(json.dumps(data), "wizard")
        out = save_yaml(cv, output)
    _info(f"[green]✓[/green] Saved [bold]{out}[/bold]. Build it with:\n  cvforge build {out}")


@app.command()
def validate(
    file: Path = typer.Argument(..., exists=True, readable=True, help="CV file."),
    tips: bool = typer.Option(True, "--tips/--no-tips", help="Also run CV tips."),
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
) -> None:
    """Validate a CV file and print readable errors or a success summary."""
    _set_verbosity(verbose, quiet)
    try:
        cv = load_cv(file)
    except (LoadError, ValidationErrorCV) as exc:
        _fail(str(exc), code=2)
    _info(
        f"[green]✓[/green] [bold]{file}[/bold] is valid "
        f"({cv.basics.full_name}, {len(cv.experience)} experience entries)."
    )
    if tips:
        _print_tips(cv)


def _print_tips(cv: CV) -> None:
    """Print checker findings as a compact list."""
    findings = check_cv(cv)
    if not findings:
        _info("[green]✓[/green] No CV tips — looks great!")
        return
    _info(f"[bold]{len(findings)} tip(s) to improve this CV:[/bold]")
    for finding in findings:
        icon = {"error": "✘", "warning": "⚠", "info": "ℹ"}[finding.severity]
        color = {"error": "red", "warning": "yellow", "info": "cyan"}[finding.severity]
        console.print(f"  [{color}]{icon}[/{color}] [dim]{finding.section}[/dim] {finding.message}")


@app.command()
def themes() -> None:
    """List available themes."""
    table = Table(title="Available themes")
    table.add_column("Theme", style="bold")
    table.add_column("Description")
    table.add_column("Photo", justify="center")
    for theme in list_themes():
        table.add_row(theme.name, theme.description, "✓" if theme.supports_photo else "—")
    console.print(table)


@app.command()
def build(
    file: Path = typer.Argument(..., exists=True, readable=True, help="CV file."),
    theme: str = typer.Option("classic", "--theme", "-t", help="Theme name."),
    fmt: str = typer.Option(
        "pdf,docx,html", "--format", "-f", help="Comma-separated formats: pdf,docx,html."
    ),
    out: Path = typer.Option(Path("./dist"), "--out", "-o", help="Output directory."),
    accent: str = typer.Option("#2563EB", "--accent", help="Accent colour (hex)."),
    font: str = typer.Option(
        "auto", "--font", help=f"Font family. Safe list: {', '.join(sorted(SAFE_FONTS))}."
    ),
    font_size: int = typer.Option(10, "--font-size", min=7, max=14, help="Base font size (pt)."),
    page_size: str = typer.Option("A4", "--page-size", help="Page size: A4 or Letter."),
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
) -> None:
    """Build PDF/DOCX/HTML files from a CV file."""
    _set_verbosity(verbose, quiet)
    try:
        cv = load_cv(file)
    except (LoadError, ValidationErrorCV) as exc:
        _fail(str(exc), code=2)

    options = ThemeOptions(
        accent_color=accent, font_family=font, font_size=font_size, page_size=page_size
    )
    if problems := options.validate():
        _fail("Invalid options:\n" + "\n".join(f"  - {p}" for p in problems), code=2)

    stems = {
        "pdf": out / f"{_safe_stem(file.stem)}_{theme}.pdf",
        "docx": out / f"{_safe_stem(file.stem)}_{theme}.docx",
        "html": out / f"{_safe_stem(file.stem)}_{theme}.html",
    }
    exporters = {"pdf": export_pdf, "docx": export_docx, "html": export_html}

    wanted = [f.strip().lower() for f in fmt.split(",") if f.strip()]
    unknown = [f for f in wanted if f not in exporters]
    if unknown:
        _fail(f"Unknown format(s): {', '.join(unknown)}. Choose from: pdf, docx, html.", code=2)

    produced: list[Path] = []
    failed: list[str] = []
    with console.status(f"[bold]Building with theme '{theme}'…") as status:
        for name in wanted:
            status.update(f"[bold]Exporting {name.upper()}…")
            try:
                produced.append(exporters[name](cv, stems[name], theme, options))
            except ExportError as exc:
                failed.append(f"{name.upper()}: {exc}")
            except (CVForgeError, OSError) as exc:
                failed.append(f"{name.upper()}: {exc}")
                if _verbose:
                    err_console.print_exception()

    table = Table(title="Build complete", show_lines=False)
    table.add_column("Format", style="bold")
    table.add_column("Output")
    for path in produced:
        label = path.suffix.lstrip(".").upper()
        table.add_row(label, str(path))
    if produced and not _quiet:
        console.print(table)
    for failure in failed:
        _warn(failure)
    if failed and not produced:
        _fail("No files were produced.", code=1)
    _info(f"[green]✓[/green] {len(produced)} file(s) written to [bold]{out.resolve()}[/bold].")

    findings = check_cv(cv)
    if findings and not _quiet:
        _info("")
        _print_tips(cv)


def _safe_stem(name: str) -> str:
    """Make a file-name-safe stem from the CV file name."""
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name) or "cv"


@app.command()
def preview(
    file: Path = typer.Argument(..., exists=True, readable=True, help="CV file."),
    theme: str = typer.Option("classic", "--theme", "-t", help="Theme name."),
    verbose: VerboseOpt = False,
    quiet: QuietOpt = False,
) -> None:
    """Render the CV and open the HTML in the default browser."""
    _set_verbosity(verbose, quiet)
    try:
        cv = load_cv(file)
    except (LoadError, ValidationErrorCV) as exc:
        _fail(str(exc), code=2)
    try:
        from cvforge.exporters.html import export_html

        tmp = Path(tempfile.gettempdir()) / f"cvforge_preview_{_safe_stem(file.stem)}.html"
        export_html(cv, tmp, theme=theme)
    except (CVForgeError, ThemeError) as exc:
        _fail(str(exc))
    _info(f"[green]✓[/green] Preview written to [bold]{tmp}[/bold] — opening browser…")
    webbrowser.open(tmp.as_uri())


def main() -> None:
    """Entry point for the ``cvforge`` console script."""
    app()


if __name__ == "__main__":
    main()
