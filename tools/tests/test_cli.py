"""test article_tools CLI: article-tools."""

import importlib
from pathlib import Path

import pytest
from typer.testing import CliRunner

from article_tools.model import Finding

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


def test_accept_then_audit_skips_what_was_accepted(
    repo: MakeRepo, tmp_path: Path
) -> None:
    """--accept writes tools/accepted.toml, and the next audit skips those findings."""
    files = {"c/a/article.md": BAD_ARTICLE}
    code, output = run(repo, files, "audit", "--accept", "--rule", "binary-units")
    assert code == 0
    assert "accepted 1 finding(s)" in output
    assert (tmp_path / "tools" / "accepted.toml").is_file()
    _, output = run(repo, files, "audit", "--rule", "binary-units")
    assert "ok    binary-units" in output
    assert "1 accepted finding(s) skipped" in output
    _, output = run(repo, files, "audit", "--rule", "binary-units", "--no-baseline")
    assert "1  binary-units" in output


def test_accept_only_takes_the_rules_asked_for(repo: MakeRepo) -> None:
    """Other rules still report after accepting one."""
    files = {"c/a/article.md": BAD_ARTICLE}
    run(repo, files, "audit", "--accept", "--rule", "binary-units")
    _, output = run(repo, files, "audit")
    assert "ok    binary-units" in output
    assert "1  avoid-words" in output


def test_strict_audit_ignores_accepted_findings(repo: MakeRepo) -> None:
    """With everything accepted, --strict exits 0, and a new finding brings back 1."""
    files = {"c/a/article.md": BAD_ARTICLE}
    assert run(repo, files, "audit", "--strict")[0] == 1
    run(repo, files, "audit", "--accept")
    assert run(repo, files, "audit", "--strict")[0] == 0
    worse = BAD_ARTICLE.replace("simply", "genuinely quietly")
    assert run(repo, {"c/a/article.md": worse}, "audit", "--strict")[0] == 1


def test_stale_entries_are_reported(repo: MakeRepo) -> None:
    """An accepted entry whose line was fixed is reported as stale."""
    files = {"c/a/article.md": BAD_ARTICLE}
    run(repo, files, "audit", "--accept", "--rule", "binary-units")
    fixed = {"c/a/article.md": BAD_ARTICLE.replace("128 KiB", "128 KB")}
    _, output = run(repo, fixed, "audit", "--rule", "binary-units", "--details")
    assert "1 stale accepted entr(ies)" in output
    assert "c/a [binary-units]" in output
    _, output = run(repo, fixed, "audit", "--rule", "avoid-words")
    assert "stale" not in output


def test_accept_rejects_no_baseline(repo: MakeRepo) -> None:
    """Accepting while ignoring the file would lose its entries."""
    code, output = run(
        repo, {"c/a/article.md": GOOD_ARTICLE}, "audit", "--accept", "--no-baseline"
    )
    assert code == 2
    assert "cannot be used together" in output


def test_baseline_path_option_and_a_broken_file(repo: MakeRepo, tmp_path: Path) -> None:
    """--baseline picks the file, and a malformed one is a usage error."""
    files = {"c/a/article.md": BAD_ARTICLE}
    custom = tmp_path / "mine.toml"
    code, _ = run(repo, files, "audit", "--accept", "--baseline", str(custom))
    assert code == 0
    assert custom.is_file()
    custom.write_text("not [valid toml", encoding="utf-8")
    code, output = run(repo, files, "audit", "--baseline", str(custom))
    assert code == 2
    assert "mine.toml" in output


def test_stub_command_creates_the_stub(repo: MakeRepo, tmp_path: Path) -> None:
    """The stub command makes the directory, the symlink and the README row."""
    files = {
        "c/a/article.md": GOOD_ARTICLE,
        "README.md": "## C Programming\n\n| A | B |\n|---|---|\n",
    }
    code, output = run(
        repo,
        files,
        "stub",
        "c/data-types",
        "--title",
        "What Is Data?",
        "--note",
        "one",
        "--note",
        "two",
        "--date",
        "May 2026",
    )
    assert code == 0
    assert "created c/data-types" in output
    assert "added a Planned row" in output
    text = (tmp_path / "c" / "data-types" / "article.md").read_text(encoding="utf-8")
    assert "- one\n- two" in text
    assert "Date: May 2026" in text
    assert "| What Is Data? | Planned |" in (tmp_path / "README.md").read_text(
        encoding="utf-8"
    )


def test_stub_command_without_a_readme_table(repo: MakeRepo) -> None:
    """No table to add to is said, not hidden."""
    code, output = run(repo, {"c/a/article.md": GOOD_ARTICLE}, "stub", "c/new")
    assert code == 0
    assert "README.md not changed" in output


def test_stub_command_refuses_a_bad_request(repo: MakeRepo) -> None:
    """An existing article and a bad slug are usage errors."""
    files = {"c/a/article.md": GOOD_ARTICLE}
    assert run(repo, files, "stub", "c/a")[0] == 2
    code, output = run(repo, files, "stub", "c/Bad_Slug")
    assert code == 2
    assert "kebab-case" in output


def test_links_suggest_the_stub_command(repo: MakeRepo) -> None:
    """A bare slug with no stub says how to make one."""
    _, output = run(repo, {"c/a/article.md": BAD_ARTICLE}, "links")
    assert "article-tools stub c/nowhere" in output


def test_links_external_fails_only_on_dead_links(
    repo: MakeRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A dead URL fails the command. An unreachable one is only reported."""
    files = {"c/a/article.md": GOOD_ARTICLE}
    seen: list[float] = []

    def fake(_articles: list, *, timeout: float) -> list:
        seen.append(timeout)
        return [Finding("c/a", rule, 3, "[x] http://x.test: bad") for rule in answers]

    answers = ["unreachable-link"]
    monkeypatch.setattr(main_module, "check_external", fake)
    code, output = run(repo, files, "links", "--external", "--timeout", "3")
    assert code == 0
    assert "1 unreachable" in output
    assert seen == [3.0]
    answers.append("dead-link")
    code, output = run(repo, files, "links", "--external")
    assert code == 1
    assert "dead-link" in output


def test_layout_command_and_check_report_a_broken_stub(
    repo: MakeRepo, tmp_path: Path
) -> None:
    """The layout command and check both fail on a dangling README symlink."""
    files = {"c/a/article.md": GOOD_ARTICLE, "unix/sc/sc.md": "### T\n"}
    run(repo, files, "layout")
    (tmp_path / "unix" / "sc" / "README.md").symlink_to("article.md")
    code, output = run(repo, files, "layout")
    assert code == 1
    assert "unix/sc" in output
    code, output = run(repo, files, "check")
    assert code == 1
    assert "[layout]" in output
    assert (
        run(
            repo,
            {"c/a/article.md": GOOD_ARTICLE, "unix/sc/article.md": "# T\n"},
            "layout",
        )[0]
        == 0
    )
