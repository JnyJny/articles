"""Test the accepted-findings file: reading, writing and applying it."""

from pathlib import Path

import pytest

from article_tools import baseline
from article_tools.baseline import Accepted
from article_tools.model import Finding


def finding(
    rule: str = "avoid-words",
    message: str = "Modern",
    context: str = "# Modern Python",
    article: str = "python/cli",
) -> Finding:
    """Build a finding."""
    return Finding(article, rule, 1, message, context)


def test_read_missing_file_is_empty(tmp_path: Path) -> None:
    """No file means nothing has been accepted."""
    assert baseline.read(tmp_path / "accepted.toml") == []


def test_round_trip_survives_awkward_text(tmp_path: Path) -> None:
    """Quotes, backslashes, tabs, unicode and DEL come back unchanged."""
    awkward = 'say "hi" \\ there\tcafé ─ ┐ \x7f'
    entry = Accepted("c/x", "rule", awkward, awkward, reason='why: "because"')
    path = tmp_path / "accepted.toml"
    baseline.write(path, [entry])
    assert baseline.read(path) == [entry]


def test_write_sorts_entries_and_keeps_the_header(tmp_path: Path) -> None:
    """Entries are sorted so the file diffs cleanly."""
    path = tmp_path / "accepted.toml"
    baseline.write(
        path,
        [Accepted("c/b", "r", "m", "x"), Accepted("c/a", "r", "m", "x")],
    )
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Findings from")
    assert text.index('"c/a"') < text.index('"c/b"')


def test_read_rejects_bad_files(tmp_path: Path) -> None:
    """A syntax error or a missing field is reported with the path."""
    path = tmp_path / "accepted.toml"
    path.write_text("[[accepted]\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r"accepted\.toml"):
        baseline.read(path)
    path.write_text('[[accepted]]\narticle = "c/x"\nrule = "r"\n', encoding="utf-8")
    with pytest.raises(ValueError, match="lacks message, context"):
        baseline.read(path)


def test_apply_splits_new_from_accepted() -> None:
    """Matching entries skip a finding. Anything else stays new."""
    accepted = [Accepted("python/cli", "avoid-words", "Modern", "# Modern Python")]
    mine = finding()
    other = finding(context="# Another Modern line")
    applied = baseline.apply(
        [mine, other],
        accepted,
        rules={"avoid-words"},
        articles={"python/cli"},
    )
    assert applied.skipped == [mine]
    assert applied.new == [other]
    assert applied.stale == []


def test_apply_reports_stale_entries_only_for_what_was_checked() -> None:
    """An entry whose finding is gone is stale, but only within the run's scope."""
    gone = Accepted("python/cli", "avoid-words", "Modern", "# deleted line")
    other_rule = Accepted("python/cli", "binary-units", "KiB", "128 KiB")
    other_article = Accepted("c/other", "avoid-words", "Modern", "# elsewhere")
    applied = baseline.apply(
        [],
        [gone, other_rule, other_article],
        rules={"avoid-words"},
        articles={"python/cli"},
    )
    assert applied.stale == [gone]


def test_accept_adds_new_entries_and_keeps_reasons() -> None:
    """Accepting never overwrites a reason someone wrote."""
    existing = Accepted(
        "python/cli", "avoid-words", "Modern", "# Modern Python", "kept"
    )
    result = baseline.accept(
        [finding(), finding(message="honest", context="honest")], [existing]
    )
    assert len(result) == 2
    assert existing in result
    assert next(entry for entry in result if entry.message == "honest").reason == ""
