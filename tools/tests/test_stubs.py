"""Test creating the stub for a promised article."""

from pathlib import Path

import pytest

from article_tools.model import classify, find_articles
from article_tools.rules import RULES, definitions
from article_tools.stubs import (
    StubError,
    add_readme_row,
    create_stub,
    default_title,
    split_path,
)

from .conftest import MakeRepo

README = (
    "# Articles\n\n## C Programming\n\n| Article | Status |\n|---|---|\n"
    "| Old | Published |\n\n## Unix\n\n| Article | Status |\n|---|---|\n"
)


def build(repo: MakeRepo, readme: str = README) -> Path:
    """Make a repo with a C directory and a README."""
    return repo({"README.md": readme, "c/old/article.md": "# Old\n"})


def test_split_path_accepts_category_and_slug() -> None:
    """A good path splits into its two parts, slashes at the edges forgiven."""
    assert split_path("c/data-types") == ("c", "data-types")
    assert split_path("/unix/signals/") == ("unix", "signals")


@pytest.mark.parametrize(
    ("path", "complaint"),
    [
        ("data-types", "CATEGORY/SLUG"),
        ("c/a/b", "CATEGORY/SLUG"),
        ("rust/thing", "unknown category"),
        ("c/Data_Types", "kebab-case"),
        ("c/XX-linker", "kebab-case"),
    ],
)
def test_split_path_rejects_bad_paths(path: str, complaint: str) -> None:
    """Each kind of bad path says what is wrong."""
    with pytest.raises(StubError, match=complaint):
        split_path(path)


def test_default_title() -> None:
    """A slug becomes a title."""
    assert default_title("data-types") == "Data Types"


def test_create_stub_writes_the_article_symlink_and_row(repo: MakeRepo) -> None:
    """A stub is a directory with a metadata block, a title, a symlink and a row."""
    root = build(repo)
    stub = create_stub(
        root,
        "c/data-types",
        title="What Is Data?",
        notes=["how-i-write-main: returns a [signed integer]"],
        date="November 2026",
    )
    article = (stub.directory / "article.md").read_text(encoding="utf-8")
    assert article.startswith(
        "<!--\nAuthor: Erik O'Shaughnessy\nDate: November 2026\nStatus: stub\n"
    )
    assert "Series: C Programming" in article
    assert "# What Is Data?" in article
    assert "Promised in:\n- how-i-write-main: returns a [signed integer]" in article
    assert (stub.directory / "README.md").is_symlink()
    assert (stub.directory / "README.md").resolve() == (
        stub.directory / "article.md"
    ).resolve()
    assert stub.row_added
    assert "| What Is Data? | Planned |" in (root / "README.md").read_text(
        encoding="utf-8"
    )


def test_a_stub_passes_the_style_checks_that_apply_to_it(repo: MakeRepo) -> None:
    """The metadata block a stub gets satisfies the metadata rule."""
    root = build(repo)
    create_stub(root, "c/data-types", date="November 2026")
    article = next(
        a for a in find_articles(root, include_stubs=True) if a.name == "c/data-types"
    )
    assert not RULES["metadata"](article)
    assert next(line.kind for line in classify(article.text)) == "meta"
    assert definitions(article) == {}


def test_create_stub_without_notes_has_no_comment(repo: MakeRepo) -> None:
    """With nothing to say about where it was promised, there is no comment."""
    root = build(repo)
    stub = create_stub(root, "c/plain", date="May 2026")
    assert "Promised" not in (stub.directory / "article.md").read_text(encoding="utf-8")


def test_series_override_and_default_date(repo: MakeRepo) -> None:
    """--series wins, and the date defaults to this month."""
    root = build(repo)
    stub = create_stub(root, "c/odd", series="Odds and Ends")
    article = (stub.directory / "article.md").read_text(encoding="utf-8")
    assert "Series: Odds and Ends" in article
    assert "Date: " in article
    assert "Date: Month" not in article


def test_create_stub_refuses_to_overwrite(repo: MakeRepo) -> None:
    """An existing article is never touched."""
    root = build(repo)
    with pytest.raises(StubError, match="already exists"):
        create_stub(root, "c/old")
    assert (root / "c" / "old" / "article.md").read_text(encoding="utf-8") == "# Old\n"


def test_create_stub_needs_the_category_directory(repo: MakeRepo) -> None:
    """A category with no directory is an error."""
    root = build(repo)
    with pytest.raises(StubError, match="no python/ directory"):
        create_stub(root, "python/thing")


def test_create_stub_without_a_readme(repo: MakeRepo) -> None:
    """No README, no row, and no failure."""
    root = repo({"c/old/article.md": "# Old\n"})
    assert not create_stub(root, "c/new").row_added


def test_add_readme_row_skips_duplicates_and_missing_sections(repo: MakeRepo) -> None:
    """A title already listed, or a heading that is not there, adds nothing."""
    root = build(repo)
    readme = root / "README.md"
    assert add_readme_row(readme, "Unix", "Signals")
    assert not add_readme_row(readme, "Unix", "Signals")
    assert not add_readme_row(readme, "Python", "Packaging")
    assert not add_readme_row(readme, "Unix", "Old")
    text = readme.read_text(encoding="utf-8")
    assert text.count("| Signals | Planned |") == 1
    assert text.index("| Signals | Planned |") > text.index("## Unix")


def test_add_readme_row_needs_a_table(repo: MakeRepo) -> None:
    """A heading with no table under it adds nothing."""
    root = repo({"README.md": "## C Programming\n\ntext only\n", "c/a/article.md": "x"})
    assert not add_readme_row(root / "README.md", "C Programming", "Thing")
