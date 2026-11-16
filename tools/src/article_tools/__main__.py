"""article-tools CLI implementation.

Checks for the articles repo: metadata, links, diagrams and style rules.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import typer
from loguru import logger

from . import baseline
from .diagrams import check_diagrams
from .external import UNREACHABLE, check_external
from .layout import check_layout
from .links import check_links
from .model import Article, Finding, find_articles, find_root
from .rules import RULES, run_rules
from .self_subcommand import cli as self_cli
from .stubs import StubError, create_stub

cli = typer.Typer()

cli.add_typer(
    self_cli,
    name="self",
    help="Manage the article-tools command.",
)

RootOption = typer.Option(
    None,
    "--root",
    help="The articles repo. Default: the nearest parent that holds STYLE.md.",
)


def fail(message: str) -> typer.Exit:
    """Print an error and return the exit that ends the command."""
    typer.secho(message, fg=typer.colors.RED, err=True)
    return typer.Exit(code=2)


def repo_root(root: Path | None) -> Path:
    """Find the articles repo, or exit with a message."""
    try:
        return root.resolve() if root else find_root(Path.cwd())
    except FileNotFoundError as error:
        raise fail(str(error)) from None


def load(root: Path | None, *, stubs: bool) -> list[Article]:
    """Find the repo and load its articles, or exit with a message."""
    return find_articles(repo_root(root), include_stubs=stubs)


def show(findings: list[Finding]) -> None:
    """Print each finding on its own line."""
    for finding in findings:
        typer.echo(finding)


def summarize(findings: list[Finding], names: list[str]) -> None:
    """Print one line per rule, with a count per article underneath."""
    by_rule: dict[str, Counter[str]] = {name: Counter() for name in names}
    for finding in findings:
        by_rule[finding.rule][finding.article.rsplit("/", 1)[-1]] += 1
    for name, counts in by_rule.items():
        if not counts:
            typer.echo(f"ok    {name}")
            continue
        typer.echo(f"{sum(counts.values()):4d}  {name}")
        typer.echo(
            "        "
            + ", ".join(f"{article} {count}" for article, count in counts.items())
        )


@cli.callback(invoke_without_command=True, no_args_is_help=True)
def global_callback(
    ctx: typer.Context,  # noqa: ARG001
    debug: bool = typer.Option(
        False,
        "--debug",
        "-D",
        help="Enable debugging output.",
    ),
) -> None:
    """Check the articles repo: metadata, links, diagrams and style rules."""
    (logger.enable if debug else logger.disable)("article_tools")
    logger.info(f"{debug=}")


@cli.command()
def audit(  # noqa: PLR0913, PLR0917
    root: Path | None = RootOption,
    rule: list[str] | None = typer.Option(
        None, "--rule", "-r", help="Only run this rule."
    ),
    details: bool = typer.Option(False, "--details", "-d", help="List every finding."),
    stubs: bool = typer.Option(
        False, "--stubs", help="Include stubs and empty articles."
    ),
    strict: bool = typer.Option(
        False, "--strict", help="Exit 1 if there are new findings."
    ),
    baseline_path: Path | None = typer.Option(
        None,
        "--baseline",
        help="File of accepted findings. Default: tools/accepted.toml in the repo.",
    ),
    no_baseline: bool = typer.Option(
        False, "--no-baseline", help="Report accepted findings too."
    ),
    accept: bool = typer.Option(
        False,
        "--accept",
        help="Add the new findings to the accepted file. Review the diff.",
    ),
) -> None:
    """Count the style findings for each rule, or list them with --details.

    Findings listed in the accepted file are skipped and counted at the end.
    """
    if accept and no_baseline:
        message = "--accept and --no-baseline cannot be used together"
        raise fail(message)
    base = repo_root(root)
    articles = find_articles(base, include_stubs=stubs)
    try:
        findings = run_rules(articles, rule)
        path = baseline_path or base / "tools" / baseline.DEFAULT_NAME
        accepted = [] if no_baseline else baseline.read(path)
    except (KeyError, ValueError) as error:
        raise fail(str(error.args[0])) from None
    names = rule or list(RULES)
    applied = baseline.apply(
        findings,
        accepted,
        rules=set(names),
        articles={article.name for article in articles},
    )
    if accept:
        baseline.write(path, baseline.accept(applied.new, accepted))
        typer.echo(f"accepted {len(applied.new)} finding(s) into {path}")
        return
    if details:
        show(applied.new)
    else:
        summarize(applied.new, names)
    shown = path.relative_to(base) if path.is_relative_to(base) else path
    report_baseline(shown, applied, details=details)
    if strict and applied.new:
        raise typer.Exit(code=1)


def report_baseline(
    path: Path,
    applied: baseline.Applied,
    *,
    details: bool,
) -> None:
    """Say what the accepted file skipped and which entries have gone stale."""
    if applied.skipped:
        typer.echo(f"{len(applied.skipped)} accepted finding(s) skipped ({path})")
    if applied.stale:
        typer.echo(
            f"{len(applied.stale)} stale accepted entr(ies): the finding is gone"
        )
        if details:
            for entry in applied.stale:
                typer.echo(f"  {entry.article} [{entry.rule}] {entry.context[:60]}")


@cli.command()
def links(
    root: Path | None = RootOption,
    external: bool = typer.Option(
        False, "--external", help="Also fetch every external URL (needs the network)."
    ),
    timeout: float = typer.Option(10.0, "--timeout", help="Seconds to wait per URL."),
) -> None:
    """Check that every link reference resolves, anchors included."""
    articles = load(root, stubs=True)
    findings = check_links(articles)
    if external:
        findings += check_external(articles, timeout=timeout)
    show(findings)
    failures = [finding for finding in findings if finding.rule != UNREACHABLE]
    if len(failures) != len(findings):
        typer.echo(
            f"{len(findings) - len(failures)} unreachable (the site may be down or "
            "may refuse automated checks): not counted as failures"
        )
    if failures:
        raise typer.Exit(code=1)


@cli.command()
def layout(root: Path | None = RootOption) -> None:
    """Check article directories: a working README symlink, no stray .md files."""
    findings = check_layout(repo_root(root))
    show(findings)
    if findings:
        raise typer.Exit(code=1)


@cli.command()
def diagrams(root: Path | None = RootOption) -> None:
    """Check that box diagrams and their arrows line up."""
    findings = check_diagrams(load(root, stubs=False))
    show(findings)
    if findings:
        raise typer.Exit(code=1)


@cli.command()
def stub(  # noqa: PLR0913, PLR0917
    path: str = typer.Argument(..., help="CATEGORY/SLUG, like c/data-types."),
    title: str | None = typer.Option(None, "--title", help="Default: from the slug."),
    series: str | None = typer.Option(
        None, "--series", help="Default: from the category."
    ),
    note: list[str] | None = typer.Option(
        None, "--note", help="Where it was promised. Repeat for more than one."
    ),
    date: str | None = typer.Option(None, "--date", help="Default: this month."),
    root: Path | None = RootOption,
) -> None:
    """Create the stub for a promised article, and a Planned row in the README."""
    base = repo_root(root)
    try:
        made = create_stub(
            base, path, title=title, series=series, notes=note or (), date=date
        )
    except StubError as error:
        raise fail(str(error)) from None
    typer.echo(f"created {made.directory.relative_to(base)} (article.md, README.md)")
    typer.echo(
        "added a Planned row to README.md"
        if made.row_added
        else "README.md not changed: no table for this category, or already listed"
    )


@cli.command()
def check(root: Path | None = RootOption) -> None:
    """Run the checks that must pass before a push: links, diagrams and layout."""
    findings = (
        check_links(load(root, stubs=True))
        + check_diagrams(load(root, stubs=False))
        + check_layout(repo_root(root))
    )
    show(findings)
    typer.echo(
        f"{len(findings)} problem(s). Run `article-tools audit` for style findings."
    )
    if findings:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    sys.exit(cli())
