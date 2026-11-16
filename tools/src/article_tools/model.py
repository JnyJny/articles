"""Articles, the lines they are made of, and the findings checks report."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

LINKS_MARKER = "<!-- Links -->"
FENCE = "```"
ROOT_MARKER = "STYLE.md"
MIN_WORDS = 60

META = "meta"
PROSE = "prose"
CODE = "code"
COMMENT = "comment"
FENCES = "fence"
LINKS = "links"


@dataclass(frozen=True)
class Line:
    """One line of an article, and what kind of text it is."""

    kind: str
    number: int
    text: str
    lang: str = ""


@dataclass(frozen=True)
class Finding:
    """One thing a check wants you to look at."""

    article: str
    rule: str
    line: int
    message: str
    context: str = ""

    def __str__(self) -> str:
        """Format the finding like a compiler diagnostic."""
        place = f"{self.article}:{self.line}" if self.line else self.article
        return f"{place}: [{self.rule}] {self.message}"


def classify(text: str) -> list[Line]:
    """Split article text into typed lines.

    A comment on the first line is the metadata block. Other HTML comments
    are comments. Fences mark code. Everything after the links marker is
    the link reference block.
    """
    lines: list[Line] = []
    in_meta = False
    in_comment = False
    in_fence = False
    in_links = False
    lang = ""
    for number, text_line in enumerate(text.split("\n"), 1):
        if number == 1 and text_line.startswith("<!--"):
            in_meta = True
        if in_meta:
            lines.append(Line(META, number, text_line))
            in_meta = "-->" not in text_line
            continue
        if in_comment:
            lines.append(Line(COMMENT, number, text_line))
            in_comment = "-->" not in text_line
            continue
        opens_comment = text_line.strip().startswith("<!--")
        if opens_comment and not in_fence and text_line.strip() != LINKS_MARKER:
            lines.append(Line(COMMENT, number, text_line))
            in_comment = "-->" not in text_line
            continue
        if text_line.startswith(FENCE):
            in_fence = not in_fence
            lang = text_line[len(FENCE) :].strip() if in_fence else ""
            lines.append(Line(FENCES, number, text_line))
            continue
        if in_fence:
            lines.append(Line(CODE, number, text_line, lang))
            continue
        in_links = in_links or text_line.strip() == LINKS_MARKER
        lines.append(Line(LINKS if in_links else PROSE, number, text_line))
    return lines


@dataclass
class Article:
    """An article.md and its lines."""

    path: Path
    root: Path
    text: str
    lines: list[Line]

    @classmethod
    def load(cls, path: Path, root: Path) -> Article:
        """Read an article from disk."""
        text = path.read_text(encoding="utf-8")
        return cls(path=path, root=root, text=text, lines=classify(text))

    @property
    def name(self) -> str:
        """Return the article's directory relative to the repo root."""
        return self.path.parent.relative_to(self.root).as_posix()

    @property
    def words(self) -> int:
        """Count the words in the article."""
        return len(self.text.split())

    def of_kind(self, *kinds: str) -> list[Line]:
        """Return the lines of the given kinds, in order."""
        return [line for line in self.lines if line.kind in kinds]

    def c_code(self) -> list[Line]:
        """Return the lines inside C code blocks."""
        return [
            line
            for line in self.lines
            if line.kind == CODE and line.lang.lower() in {"c", "c++"}
        ]

    def finding(self, rule: str, line: int, message: str) -> Finding:
        """Make a finding about this article."""
        return Finding(self.name, rule, line, message)


def find_root(start: Path) -> Path:
    """Walk up from start to the directory that holds STYLE.md."""
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / ROOT_MARKER).is_file():
            return candidate
    message = f"no {ROOT_MARKER} in {start} or any parent directory"
    raise FileNotFoundError(message)


def find_articles(root: Path, *, include_stubs: bool = False) -> list[Article]:
    """Load every article under root, skipping stubs unless asked."""
    articles = [
        Article.load(path, root) for path in sorted(root.glob("*/*/article.md"))
    ]
    if include_stubs:
        return articles
    return [article for article in articles if article.words >= MIN_WORDS]
