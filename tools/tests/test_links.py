"""Test the link check: resolution, anchors and the findings it reports."""

from article_tools.links import (
    check_links,
    github_anchor,
    heading_anchors,
    resolve,
    slug_index,
)
from article_tools.model import find_articles

from .conftest import META, MakeRepo


def kinds_for(repo: MakeRepo, target: str, files: dict[str, str] | None = None) -> str:
    """Resolve a link target from c/a/article.md and return the kind."""
    root = repo(
        {
            "c/a/article.md": META + "# A\n",
            "c/b/article.md": META + "# B\n\n## Sub Part\n",
            **(files or {}),
        }
    )
    articles = find_articles(root, include_stubs=True)
    article = next(item for item in articles if item.name == "c/a")
    return resolve(article, target, slug_index(articles)).kind


def test_github_anchor() -> None:
    """Anchors are lowercase, unpunctuated and hyphenated."""
    assert (
        github_anchor("**NULL**: The Billion Dollar Mistake")
        == "null-the-billion-dollar-mistake"
    )
    assert github_anchor("`main()` and friends") == "main-and-friends"


def test_heading_anchors_ignore_code() -> None:
    """A # comment inside a code block is not a heading."""
    text = "# Title\n```\n# not a heading\n```\n## Real One\n"
    assert heading_anchors(text) == {"title", "real-one"}


def test_resolve_external(repo: MakeRepo) -> None:
    """URLs are not checked."""
    assert kinds_for(repo, "https://example.org/x") == "external"
    assert kinds_for(repo, "mailto:a@b.c") == "external"


def test_resolve_relative_article(repo: MakeRepo) -> None:
    """A relative path to an article, or its directory, resolves."""
    assert kinds_for(repo, "../b/article.md") == "ok"
    assert kinds_for(repo, "../b") == "ok"
    assert kinds_for(repo, "../b/article.md#sub-part") == "ok"


def test_resolve_dangling(repo: MakeRepo) -> None:
    """A path that leads nowhere is dangling."""
    assert kinds_for(repo, "../nope/article.md") == "dangling-link"


def test_resolve_bare_slug(repo: MakeRepo) -> None:
    """A bare slug is never a link, even when a directory has that name."""
    assert kinds_for(repo, "b") == "bare-slug"
    assert kinds_for(repo, "no-such-article") == "bare-slug"


def test_resolve_anchors(repo: MakeRepo) -> None:
    """A fragment must name a heading, in this file or another."""
    assert kinds_for(repo, "#a") == "ok"
    assert kinds_for(repo, "#missing") == "broken-anchor"
    assert kinds_for(repo, "../b/article.md#missing") == "broken-anchor"


def test_resolve_multi_word_target_is_not_a_link(repo: MakeRepo) -> None:
    """Words with no quoted title are not a URL or a path."""
    assert kinds_for(repo, "Down to Program") == "dangling-link"
    assert kinds_for(repo, 'https://example.org/x "A Title"') == "external"


def test_resolve_directory_without_article(repo: MakeRepo) -> None:
    """A plain directory is a fine target."""
    assert kinds_for(repo, "../data", {"c/data/notes.txt": "x"}) == "ok"


def test_check_links_reports_each_kind(repo: MakeRepo) -> None:
    """The report names the reference, line and advice for each problem."""
    text = (
        META
        + "# A\n\nsee [one][one] [two][two] [three][three] [four][four]\n"
        + "and [five][five] and [six][\n\n<!-- Links -->\n"
        + "[one]: b\n[two]: nowhere\n[three]: ../b/article.md#gone\n"
        + "[four]: ../nope/article.md\n"
        + "[five]: Down to Program\n"
    )
    root = repo({"c/a/article.md": text, "c/b/article.md": META + "# B\n"})
    findings = check_links(find_articles(root, include_stubs=True))
    messages = {
        rule: [f.message for f in findings if f.rule == rule]
        for rule in {f.rule for f in findings}
    }
    assert any("use ../b/article.md" in message for message in messages["bare-slug"])
    assert any("no article or stub" in message for message in messages["bare-slug"])
    assert "no heading makes #gone" in messages["broken-anchor"][0]
    assert any("does not exist" in message for message in messages["dangling-link"])
    assert "unclosed" in messages["malformed-reference"][0]
    assert "undefined-reference" not in messages


def test_check_links_undefined_reference(repo: MakeRepo) -> None:
    """A reference nothing defines is reported at its first use."""
    root = repo({"c/a/article.md": META + "# A\n\nsee [x][gone] and `a[i][j]`\n"})
    findings = check_links(find_articles(root, include_stubs=True))
    assert [(finding.rule, finding.line) for finding in findings] == [
        ("undefined-reference", 12)
    ]


def test_check_links_clean_repo(repo: MakeRepo) -> None:
    """A repo with good links has no findings."""
    text = (
        META
        + "# A\n\nsee [b][b] and [site][s]\n\n<!-- Links -->\n"
        + "[b]: ../b/article.md\n[s]: https://x.org\n"
    )
    root = repo({"c/a/article.md": text, "c/b/article.md": META + "# B\n"})
    assert check_links(find_articles(root, include_stubs=True)) == []
