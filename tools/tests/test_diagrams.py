"""Test the diagram check: dividers line up and arrows have clean elbows."""

from pathlib import Path

from article_tools.diagrams import check_diagrams
from article_tools.model import Article, classify

BOX = [
    "    ┌────────┬──────────┬────────┐",
    "    │ int x  │  0x4004  │     42 │{a}",
    "    ├────────┼──────────┼────────┤{b}",
    "    │ int *p │  0x4000  │ 0x4004 │{c}",
    "    └────────┴──────────┴────────┘",
]


def diagram(top: str = "", middle: str = "", bottom: str = "") -> str:
    """Return a fenced diagram with arrow text after the box edge."""
    rows = [row.format(a=top, b=middle, c=bottom) for row in BOX]
    return "# T\n```\n" + "\n".join(rows) + "\n```\n"


def check(text: str) -> list[str]:
    """Return the messages the diagram check reports for some text."""
    article = Article(Path("c/x/article.md"), Path(), text, classify(text))
    return [finding.message for finding in check_diagrams([article])]


def test_aligned_box_and_arrow_pass() -> None:
    """A tidy box with aligned elbows has no problems."""
    assert check(diagram("◄─ ──┐", "     │", "─ ─ ─┘")) == []


def test_arrow_elbows_in_different_columns() -> None:
    """The corner one column off the vertical bar is reported."""
    messages = check(diagram("◄─ ─ ┐", "     │", "─ ─ ┘"))
    assert len(messages) == 1
    assert "different columns" in messages[0]


def test_misaligned_divider() -> None:
    """A cell divider that drifts off the top border is reported."""
    text = diagram().replace("│  0x4004  │", "│  0x4004 │ ")
    assert any("border column" in message for message in check(text))


def test_blocks_without_boxes_are_ignored() -> None:
    """Plain code blocks and file trees are not diagrams."""
    assert check("# T\n```\n├── a\n└── b\n```\n") == []


def test_lone_connector_lines_are_not_table_rows() -> None:
    """A vertical bar between two boxes belongs to the arrow."""
    lines = [
        "    " + "┌───┬───┐",
        "    │ a │ b │─ ─ ─┐",
        "    └───┴───┘     │",
        "                  │",
        "    ┌───┬───┐     │",
        "    │ c │ d │◄─ ──┘",
        "    └───┴───┘",
    ]
    assert check("# T\n```\n" + "\n".join(lines) + "\n```\n") == []
