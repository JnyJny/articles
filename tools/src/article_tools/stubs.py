"""Create the stub for an article that has been promised."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

AUTHOR = "Erik O'Shaughnessy"
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

# category directory: (series, heading of its table in the README)
CATEGORIES = {
    "c": ("C Programming", "C Programming"),
    "unix": ("Unix", "Unix"),
    "python": ("Python", "Python"),
    "misc": ("Miscellaneous", "Miscellaneous"),
}


class StubError(ValueError):
    """The stub cannot be created, and why."""


@dataclass(frozen=True)
class Stub:
    """What creating a stub did."""

    directory: Path
    row_added: bool


def split_path(path: str) -> tuple[str, str]:
    """Split category/slug, or say what is wrong with it."""
    category, _, slug = path.strip("/").partition("/")
    if not slug or "/" in slug:
        message = f"expected CATEGORY/SLUG, like c/data-types, not {path!r}"
        raise StubError(message)
    if category not in CATEGORIES:
        message = f"unknown category {category!r}; use one of {', '.join(CATEGORIES)}"
        raise StubError(message)
    if not SLUG.match(slug):
        message = f"{slug!r} is not a kebab-case directory name"
        raise StubError(message)
    return category, slug


def default_title(slug: str) -> str:
    """Make a title from a slug: data-types becomes Data Types."""
    return " ".join(word.capitalize() for word in slug.split("-"))


def render(
    *,
    title: str,
    series: str,
    notes: Sequence[str],
    author: str,
    date: str,
) -> str:
    """Return the text of a stub article."""
    meta = (
        f"<!--\nAuthor: {author}\nDate: {date}\nStatus: stub\nSeries: {series}\n"
        "Prerequisites: none\nNext: none\n-->\n\n"
    )
    promised = ""
    if notes:
        listed = "\n".join(f"- {note}" for note in notes)
        promised = f"\n<!--\nPromised in:\n{listed}\n-->\n"
    return f"{meta}# {title}\n{promised}"


def add_readme_row(readme: Path, heading: str, title: str) -> bool:
    """Add a Planned row to the table under a README heading.

    Returns False when the heading or its table is missing, or the title is
    already listed.
    """
    lines = readme.read_text(encoding="utf-8").split("\n")
    start = next(
        (n for n, line in enumerate(lines) if line.strip() == f"## {heading}"), None
    )
    if start is None:
        return False
    last = None
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            break
        if lines[index].startswith("|"):
            last = index
    listed = (f"| {title} |", f"| [{title}]")
    if last is None or any(line.startswith(listed) for line in lines):
        return False
    lines.insert(last + 1, f"| {title} | Planned |")
    readme.write_text("\n".join(lines), encoding="utf-8")
    return True


def create_stub(  # noqa: PLR0913
    root: Path,
    path: str,
    *,
    title: str | None = None,
    series: str | None = None,
    notes: Sequence[str] = (),
    author: str = AUTHOR,
    date: str | None = None,
) -> Stub:
    """Create category/slug/article.md, its README.md symlink and a README row."""
    category, slug = split_path(path)
    if not (root / category).is_dir():
        message = f"no {category}/ directory under {root}"
        raise StubError(message)
    directory = root / category / slug
    if directory.exists():
        message = f"{category}/{slug} already exists"
        raise StubError(message)
    default_series, heading = CATEGORIES[category]
    title = title or default_title(slug)
    directory.mkdir()
    (directory / "article.md").write_text(
        render(
            title=title,
            series=series or default_series,
            notes=notes,
            author=author,
            date=date or datetime.now(tz=UTC).strftime("%B %Y"),
        ),
        encoding="utf-8",
    )
    (directory / "README.md").symlink_to("article.md")
    readme = root / "README.md"
    added = readme.is_file() and add_readme_row(readme, heading, title)
    return Stub(directory, added)
