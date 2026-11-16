"""Test the layout check: README symlinks and stray markdown files."""

from article_tools.layout import check_layout

from .conftest import MakeRepo


def test_a_good_stub_layout_passes(repo: MakeRepo) -> None:
    """article.md with a README.md symlink to it is fine."""
    root = repo({"c/good/article.md": "# Good\n"})
    (root / "c" / "good" / "README.md").symlink_to("article.md")
    assert check_layout(root) == []


def test_broken_symlink_and_stray_markdown_are_reported(repo: MakeRepo) -> None:
    """The unix/system-calls mistake: a dangling README link and a misnamed file."""
    root = repo({"unix/system-calls/system-calls.md": "### Title\n"})
    (root / "unix" / "system-calls" / "README.md").symlink_to("article.md")
    messages = [finding.message for finding in check_layout(root)]
    assert any("symlink to article.md, which does not exist" in m for m in messages)
    assert any("system-calls.md is here; rename it" in m for m in messages)
    assert {finding.article for finding in check_layout(root)} == {"unix/system-calls"}


def test_code_directories_are_not_articles(repo: MakeRepo) -> None:
    """A directory of scripts with its own README is not an article."""
    root = repo(
        {"python/lazy/benchmark.py": "x = 1\n", "python/lazy/README.md": "notes\n"}
    )
    assert check_layout(root) == []


def test_missing_category_directories_and_loose_files_are_ignored(
    repo: MakeRepo,
) -> None:
    """Only directories under existing categories are looked at."""
    root = repo({"c/loose.md": "x\n"})
    assert check_layout(root) == []
