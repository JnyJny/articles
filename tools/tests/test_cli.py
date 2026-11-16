"""test article_tools CLI: article-tools."""

import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from .conftest import META, MakeRepo

main_module_name = "article_tools.__main__"
main_module = importlib.import_module(main_module_name)
runner = CliRunner()


def test_cli_no_arguments() -> None:
    """Test the main command-line interface with no arguments."""
    result = runner.invoke(main_module.cli)
    assert result.exit_code != 0
    assert "Usage:" in result.output


def test_cli_help() -> None:
    """Test the main command-line interface help flag."""
    result = runner.invoke(main_module.cli, ["--help"])
    assert result.exit_code == 0


def test_cli_self_no_arguments() -> None:
    """Test the self subcommand with no arguments."""
    result = runner.invoke(main_module.cli, ["self"])
    assert result.exit_code != 0
    assert "Usage:" in result.output


def test_cli_self_help() -> None:
    """Test the self subcommand help flag."""
    result = runner.invoke(main_module.cli, ["self", "--help"])
    assert result.exit_code == 0


def test_cli_self_version(project_version: str) -> None:
    """Test the version self subcommand."""
    result = runner.invoke(main_module.cli, ["self", "version"])
    assert result.exit_code == 0
    assert result.output.strip() == project_version


BODY = "\n".join(" ".join(["word"] * 10) for _ in range(8)) + "\n"
GOOD_ARTICLE = META + "# A\n\n" + BODY
BAD_ARTICLE = (
    META
    + "# A\n\nit is simply true, and 128 KiB "
    + "word " * 70
    + "\n\n<!-- Links -->\n[x]: nowhere\n"
)


def run(repo: MakeRepo, files: dict[str, str], *args: str) -> tuple[int, str]:
    """Build a repo and run the CLI against it with --root."""
    root = repo(files)
    result = runner.invoke(main_module.cli, [args[0], "--root", str(root), *args[1:]])
    return result.exit_code, result.output


def test_audit_summarizes_by_rule(repo: MakeRepo) -> None:
    """The default audit prints one line per rule, with counts per article."""
    code, output = run(repo, {"c/a/article.md": BAD_ARTICLE}, "audit")
    assert code == 0
    assert "1  avoid-words" in output
    assert "1  binary-units" in output
    assert "ok    headings" in output
    assert "        a 1" in output


def test_audit_details_lists_findings(repo: MakeRepo) -> None:
    """--details prints each finding with its place."""
    code, output = run(
        repo,
        {"c/a/article.md": BAD_ARTICLE},
        "audit",
        "--details",
        "--rule",
        "binary-units",
    )
    assert code == 0
    assert "c/a:12: [binary-units] KiB" in output


def test_audit_strict_exits_nonzero(repo: MakeRepo) -> None:
    """--strict turns findings into a failing exit."""
    assert run(repo, {"c/a/article.md": BAD_ARTICLE}, "audit", "--strict")[0] == 1
    assert run(repo, {"c/a/article.md": GOOD_ARTICLE}, "audit", "--strict")[0] == 0


def test_audit_unknown_rule(repo: MakeRepo) -> None:
    """An unknown rule is a usage error."""
    code, output = run(
        repo, {"c/a/article.md": GOOD_ARTICLE}, "audit", "--rule", "nonsense"
    )
    assert code == 2
    assert "nonsense" in output


def test_audit_stubs_flag(repo: MakeRepo) -> None:
    """Stubs are skipped unless --stubs asks for them."""
    files = {"c/a/article.md": GOOD_ARTICLE, "c/stub/article.md": "# stub\n"}
    assert "metadata" in run(repo, files, "audit", "--details", "--stubs")[1]
    assert "stub" not in run(repo, files, "audit", "--details")[1]


def test_links_fail_and_pass(repo: MakeRepo) -> None:
    """The links command exits 1 on a dangling link and 0 on a clean repo."""
    code, output = run(repo, {"c/a/article.md": BAD_ARTICLE}, "links")
    assert code == 1
    assert "bare-slug" in output
    assert run(repo, {"c/a/article.md": GOOD_ARTICLE}, "links") == (0, "")


def test_diagrams_fail_and_pass(repo: MakeRepo) -> None:
    """The diagrams command exits 1 on a misaligned arrow."""
    box = """\
```
    ┌───┬───┐
    │ a │ b │─ ─ ┐
    ├───┼───┤     │
    │ c │ d │◄─ ─ ┘
    └───┴───┘
```
"""
    bad = GOOD_ARTICLE + box
    code, output = run(repo, {"c/a/article.md": bad}, "diagrams")
    assert code == 1
    assert "different columns" in output
    assert run(repo, {"c/a/article.md": GOOD_ARTICLE}, "diagrams") == (0, "")


def test_check_runs_links_and_diagrams(repo: MakeRepo) -> None:
    """The check command combines the checks that must pass before a push."""
    code, output = run(repo, {"c/a/article.md": BAD_ARTICLE}, "check")
    assert code == 1
    assert "bare-slug" in output
    assert "1 problem(s)" in output
    assert run(repo, {"c/a/article.md": GOOD_ARTICLE}, "check")[0] == 0


def test_root_found_from_the_working_directory(
    repo: MakeRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without --root the CLI walks up to the directory holding STYLE.md."""
    root = repo({"c/a/article.md": GOOD_ARTICLE})
    monkeypatch.chdir(root / "c" / "a")
    result = runner.invoke(main_module.cli, ["links"])
    assert result.exit_code == 0


def test_no_root_is_an_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Outside any articles repo the CLI says so and exits 2."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(main_module.cli, ["links"])
    assert result.exit_code == 2
    assert "STYLE.md" in result.output


def test_debug_flag(repo: MakeRepo) -> None:
    """--debug is accepted ahead of a command."""
    root = repo({"c/a/article.md": GOOD_ARTICLE})
    result = runner.invoke(main_module.cli, ["--debug", "links", "--root", str(root)])
    assert result.exit_code == 0
