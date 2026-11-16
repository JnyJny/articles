"""Check that every link reference goes somewhere that exists."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .model import PROSE, Article, Finding
from .rules import INLINE_CODE, definitions, used_references

if TYPE_CHECKING:
    from pathlib import Path

EXTERNAL = re.compile(r"^(?:https?|ftp|mailto):", re.IGNORECASE)
HEADING = re.compile(r"^#{1,6}\s+(.*)$")

EXTERNAL_KIND = "external"
OK_KIND = "ok"
BARE_SLUG = "bare-slug"
DANGLING = "dangling-link"
BROKEN_ANCHOR = "broken-anchor"
UNDEFINED = "undefined-reference"
MALFORMED = "malformed-reference"
UNCLOSED_LABEL = re.compile(r"\]\[(?![^\]\[\n]*\])")


@dataclass(frozen=True)
class Resolution:
    """Where a link target leads."""

    kind: str
    detail: str = ""


def github_anchor(heading: str) -> str:
    """Return the anchor GitHub makes for a heading."""
    text = re.sub(r"[`*]", "", heading.strip()).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def heading_anchors(text: str) -> set[str]:
    """Return the anchors of every heading outside code blocks."""
    anchors: set[str] = set()
    in_fence = False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_fence = not in_fence
            continue
        match = None if in_fence else HEADING.match(line)
        if match:
            anchors.add(github_anchor(match.group(1)))
    return anchors


def slug_index(articles: list[Article]) -> dict[str, Article]:
    """Map each article directory name to its article."""
    return {article.path.parent.name: article for article in articles}


def check_fragment(fragment: str, text: str) -> Resolution:
    """Check that a #fragment names a heading in the text."""
    if fragment in heading_anchors(text):
        return Resolution(OK_KIND)
    return Resolution(BROKEN_ANCHOR, f"#{fragment}")


def locate(candidate: Path) -> Path | None:
    """Find the file or directory a relative path leads to."""
    for option in (candidate, candidate / "article.md", candidate / "README.md"):
        if option.is_file():
            return option
    return candidate if candidate.is_dir() else None


def check_found(found: Path, fragment: str) -> Resolution:
    """Check a #fragment against the file a link leads to, if it is Markdown."""
    if fragment and found.is_file() and found.suffix == ".md":
        return check_fragment(fragment, found.read_text(encoding="utf-8"))
    return Resolution(OK_KIND)


def resolve(
    article: Article,
    target: str,
    slugs: dict[str, Article],
) -> Resolution:
    """Work out where a link target leads, relative to the article."""
    words = target.split(None, 1)
    if len(words) == 2 and not words[1].startswith(('"', "'", "(")):  # noqa: PLR2004
        return Resolution(DANGLING, target)
    target = words[0]
    if EXTERNAL.match(target):
        return Resolution(EXTERNAL_KIND)
    path_part, _, fragment = target.partition("#")
    if not path_part:
        return check_fragment(fragment, article.text)
    if "/" not in path_part and "." not in path_part:
        hint = slugs.get(path_part)
        return Resolution(BARE_SLUG, relative_article(article, hint) if hint else "")
    found = locate((article.path.parent / path_part).resolve())
    return check_found(found, fragment) if found else Resolution(DANGLING, path_part)


def relative_article(article: Article, other: Article) -> str:
    """Return the relative path from one article to another."""
    return os.path.relpath(other.path, article.path.parent).replace(os.sep, "/")


def reference_findings(article: Article, slugs: dict[str, Article]) -> list[Finding]:
    """Check every link reference definition in one article."""
    findings: list[Finding] = []
    for reference, (number, target) in definitions(article).items():
        resolution = resolve(article, target, slugs)
        if resolution.kind == BARE_SLUG:
            slug = target.split()[0]
            advice = (
                f"use {resolution.detail}"
                if resolution.detail
                else "no article or stub has that name"
            )
            message = f"[{reference}] is the bare slug '{slug}'; {advice}"
            findings.append(article.finding(BARE_SLUG, number, message))
        elif resolution.kind == DANGLING:
            message = (
                f"[{reference}] points at {resolution.detail}, which does not exist"
            )
            findings.append(article.finding(DANGLING, number, message))
        elif resolution.kind == BROKEN_ANCHOR:
            message = (
                f"[{reference}] points at {target}, "
                f"but no heading makes {resolution.detail}"
            )
            findings.append(article.finding(BROKEN_ANCHOR, number, message))
    return findings


def undefined_findings(article: Article) -> list[Finding]:
    """Find references the prose uses that nothing defines."""
    defined = set(definitions(article))
    findings: list[Finding] = []
    for reference in sorted(used_references(article, shorthand=False) - defined):
        number = first_use(article, reference)
        message = f"[{reference}] is used and never defined"
        findings.append(article.finding(UNDEFINED, number, message))
    return findings


def malformed_findings(article: Article) -> list[Finding]:
    """Find a reference whose label was never closed, like [text][."""
    return [
        article.finding(
            MALFORMED,
            line.number,
            f"unclosed reference label: {line.text.strip()[:60]}",
        )
        for line in article.of_kind(PROSE)
        if UNCLOSED_LABEL.search(INLINE_CODE.sub("", line.text))
    ]


def first_use(article: Article, reference: str) -> int:
    """Return the line number where a reference is first used."""
    for line in article.of_kind(PROSE):
        if f"][{reference}]" in line.text or f"[{reference}][]" in line.text:
            return line.number
    return 0


def check_links(articles: list[Article]) -> list[Finding]:
    """Check the link references of every article."""
    slugs = slug_index(articles)
    findings: list[Finding] = []
    for article in articles:
        findings += reference_findings(article, slugs)
        findings += undefined_findings(article)
        findings += malformed_findings(article)
    return findings
