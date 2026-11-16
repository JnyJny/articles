"""article-tools CLI implementation.

Checks for the articles repo: metadata, links, diagrams and style rules.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import typer
from loguru import logger

from .diagrams import check_diagrams
from .links import check_links
from .model import Article, Finding, find_articles, find_root
from .rules import RULES, run_rules
from .self_subcommand import cli as self_cli

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


def load(root: Path | None, *, stubs: bool) -> list[Article]:
    """Find the repo and load its articles, or exit with a message."""
    try:
        base = root.resolve() if root else find_root(Path.cwd())
    except FileNotFoundError as error:
        typer.secho(str(error), fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None
    return find_articles(base, include_stubs=stubs)


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
def audit(
    root: Path | None = RootOption,
    rule: list[str] | None = typer.Option(
        None, "--rule", "-r", help="Only run this rule."
    ),
    details: bool = typer.Option(False, "--details", "-d", help="List every finding."),
    stubs: bool = typer.Option(
        False, "--stubs", help="Include stubs and empty articles."
    ),
    strict: bool = typer.Option(False, "--strict", help="Exit 1 if anything is found."),
) -> None:
    """Count the style findings for each rule, or list them with --details."""
    articles = load(root, stubs=stubs)
    try:
        findings = run_rules(articles, rule)
    except KeyError as error:
        typer.secho(error.args[0], fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from None
    if details:
        show(findings)
    else:
        summarize(findings, rule or list(RULES))
    if strict and findings:
        raise typer.Exit(code=1)


@cli.command()
def links(root: Path | None = RootOption) -> None:
    """Check that every link reference resolves, anchors included."""
    findings = check_links(load(root, stubs=True))
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
def check(root: Path | None = RootOption) -> None:
    """Run the checks that must pass before a push: links and diagrams."""
    findings = check_links(load(root, stubs=True)) + check_diagrams(
        load(root, stubs=False)
    )
    show(findings)
    typer.echo(
        f"{len(findings)} problem(s). Run `article-tools audit` for style findings."
    )
    if findings:
        raise typer.Exit(code=1)


if __name__ == "__main__":
    sys.exit(cli())
