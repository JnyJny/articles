"""Test the article model: lines, articles, findings and discovery."""

from pathlib import Path

import pytest

from article_tools.model import (
    Article,
    Finding,
    classify,
    find_articles,
    find_root,
)

from .conftest import META, MakeRepo


def kinds(text: str) -> list[str]:
    """Return the kind of each line."""
    return [line.kind for line in classify(text)]


def test_classify_metadata_block() -> None:
    """A comment on the first line is metadata, to its closing marker."""
    assert kinds("<!--\nAuthor: x\n-->\nbody\n") == [
        "meta",
        "meta",
        "meta",
        "prose",
        "prose",
    ]


def test_classify_one_line_comment_is_metadata() -> None:
    """A one-line comment on line 1 is metadata and nothing more."""
    assert kinds("<!-- Prerequisite: x -->\nbody") == ["meta", "prose"]


def test_classify_comment_after_line_one_is_a_comment() -> None:
    """A comment anywhere but line 1 is a comment, not metadata."""
    assert kinds("title\n<!-- note -->\n") == ["prose", "comment", "prose"]


def test_classify_code_blocks_carry_the_language() -> None:
    """Lines between fences are code, tagged with the fence language."""
    lines = classify("```C\nint x;\n```\ntext")
    assert [line.kind for line in lines] == ["fence", "code", "fence", "prose"]
    assert lines[1].lang == "C"
    assert lines[3].lang == ""


def test_classify_links_block() -> None:
    """Everything from the links marker on is the link block."""
    lines = classify("text\n<!-- Links -->\n[a]: b\n")
    assert [line.kind for line in lines] == ["prose", "links", "links", "links"]


def test_finding_str_with_and_without_a_line() -> None:
    """A finding prints like a compiler diagnostic."""
    assert str(Finding("c/x", "rule", 3, "msg")) == "c/x:3: [rule] msg"
    assert str(Finding("c/x", "rule", 0, "msg")) == "c/x: [rule] msg"


def test_article_properties(repo: MakeRepo) -> None:
    """An article knows its name, word count, lines and C code."""
    root = repo({"c/x/article.md": "# T\n\n```C\nint a;\n```\n```python\nx = 1\n```\n"})
    article = Article.load(root / "c/x/article.md", root)
    assert article.name == "c/x"
    assert article.words == len(article.text.split())
    assert [line.text for line in article.c_code()] == ["int a;"]
    assert len(article.of_kind("fence")) == 4
    assert article.finding("r", 2, "m") == Finding("c/x", "r", 2, "m")


def test_find_root_walks_up(repo: MakeRepo) -> None:
    """The root is the nearest parent holding STYLE.md."""
    root = repo({"c/x/article.md": "x"})
    assert find_root(root / "c" / "x") == root.resolve()


def test_find_root_missing(tmp_path: Path) -> None:
    """No STYLE.md anywhere above is an error."""
    with pytest.raises(FileNotFoundError, match=r"STYLE\.md"):
        find_root(tmp_path)


def test_find_articles_skips_stubs_unless_asked(repo: MakeRepo) -> None:
    """Short stubs are left out of the audit by default."""
    root = repo(
        {"c/real/article.md": META + "word " * 80, "c/stub/article.md": "# stub\n"}
    )
    assert [article.name for article in find_articles(root)] == ["c/real"]
    assert len(find_articles(root, include_stubs=True)) == 2


def test_classify_comments_are_not_prose() -> None:
    """HTML comments after line one are comments, one line or several."""
    text = (
        "# T\n<!-- one line -->\n<!--\nlong note\n-->\nbody\n<!-- Links -->\n[a]: b\n"
    )
    assert kinds(text) == [
        "prose",
        "comment",
        "comment",
        "comment",
        "comment",
        "prose",
        "links",
        "links",
        "links",
    ]


def test_comment_markers_inside_code_stay_code() -> None:
    """A comment opener inside a fence is just code."""
    assert kinds("```html\n<!-- x\n```\n") == ["fence", "code", "fence", "prose"]
