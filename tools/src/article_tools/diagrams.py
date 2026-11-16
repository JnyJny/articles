"""Check that box diagrams line up."""

from __future__ import annotations

from .model import CODE, Article, Finding

RULE = "diagram"
BORDER = set("┌┬┐├┼┤└┴┘│")
TOP_BORDER = set("┌┬┐")
TABLE_START = "┌"
TABLE_LINES = set("┌│├└")
ELBOWS = set("┐┘│")


def code_blocks(article: Article) -> list[tuple[int, list[str]]]:
    """Return each code block as (first line number, its lines)."""
    blocks: list[tuple[int, list[str]]] = []
    current: list[str] = []
    start = 0
    for line in article.lines:
        if line.kind == CODE:
            if not current:
                start = line.number
            current.append(line.text)
        elif current:
            blocks.append((start, current))
            current = []
    if current:
        blocks.append((start, current))
    return blocks


def indent_of(text: str) -> int:
    """Return how many spaces a line is indented."""
    return len(text) - len(text.lstrip())


def tables(block: list[str]) -> list[tuple[int, list[str]]]:
    """Find the boxes in a block, as (index of the top border, its lines)."""
    found: list[tuple[int, list[str]]] = []
    index = 0
    while index < len(block):
        if not block[index].lstrip().startswith(TABLE_START):
            index += 1
            continue
        indent = indent_of(block[index])
        end = index
        while (
            end < len(block)
            and block[end].strip()
            and block[end].lstrip()[0] in TABLE_LINES
            and indent_of(block[end]) == indent
        ):
            end += 1
        found.append((index, block[index:end]))
        index = end
    return found


def column_problems(first: int, box: list[str]) -> list[tuple[int, str]]:
    """Check that every cell divider in a box lines up with the top border."""
    columns = [column for column, char in enumerate(box[0]) if char in TOP_BORDER]
    problems: list[tuple[int, str]] = []
    for offset, text in enumerate(box):
        for column in columns:
            char = text[column] if column < len(text) else " "
            if char not in BORDER:
                message = f"border column {column} is {char!r}: {text.strip()[:40]}"
                problems.append((first + offset, message))
    return problems


def elbow_problems(
    start: int,
    block: list[str],
    boxes: list[tuple[int, list[str]]],
) -> list[tuple[int, str]]:
    """Check that an arrow's corners and vertical bar share one column."""
    edge = max(
        max((column for column, char in enumerate(box[0]) if char == "┐"), default=0)
        for _, box in boxes
    )
    seen: dict[int, str] = {}
    for text in block:
        for column, char in enumerate(text):
            if column > edge and char in ELBOWS:
                seen[column] = seen.get(column, "") + char
    if len(seen) <= 1:
        return []
    columns = ", ".join(
        f"column {column} has {chars}" for column, chars in sorted(seen.items())
    )
    return [(start, f"arrow elbows sit in different columns: {columns}")]


def check_diagrams(articles: list[Article]) -> list[Finding]:
    """Check every box diagram in every article."""
    findings: list[Finding] = []
    for article in articles:
        for start, block in code_blocks(article):
            boxes = tables(block)
            if not boxes:
                continue
            for index, box in boxes:
                for number, message in column_problems(start + index, box):
                    findings.append(article.finding(RULE, number, message))
            for number, message in elbow_problems(start, block, boxes):
                findings.append(article.finding(RULE, number, message))
    return findings
