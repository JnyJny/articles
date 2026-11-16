"""Test the style rules: each one flags a bad case and passes a good one."""

from pathlib import Path

import pytest

from article_tools.model import Article, classify
from article_tools.rules import (
    RULES,
    definitions,
    run_rules,
    used_references,
)

from .conftest import META


def article(text: str) -> Article:
    """Build an article from text without touching the disk."""
    return Article(Path("c/x/article.md"), Path(), text, classify(text))


def hits(rule: str, text: str) -> list[tuple[int, str]]:
    """Run one rule on some text."""
    return RULES[rule](article(text))


def c_block(code: str) -> str:
    """Wrap code in a C fence."""
    return f"```C\n{code}\n```\n"


BAD = [
    ("metadata", "# T\n"),
    ("metadata", "<!--\nAuthor: Erik\nDate: May 2025\n-->\n# T\n"),
    ("headings", "# A\n# B\n"),
    ("headings", "# A\n#### deep\n"),
    ("headings", "## no title\n"),
    ("embedded-links", "# T\nsee [it](http://x.org)\n"),
    ("unused-reference", "# T\n<!-- Links -->\n[a]: http://x.org\n"),
    ("link-text", "# T\nread [A Map of Memory][m]\n"),
    ("link-text", "# T\nclick [here][m]\n"),
    ("order-wording", "# T\nsee the last article\n"),
    ("order-wording", "# T\nin the next article we go\n"),
    ("avoid-words", "# T\nit is simply true\n"),
    ("avoid-words", "# T\nHonestly, a modern thing\n"),
    ("not-y", "# T\nIt's a tool, not a toy.\n"),
    ("not-y", "# T\nA parser in an overcoat\n"),
    ("binary-units", "# T\n128 KiB of memory\n"),
    ("bare-null", "# T\na NULL pointer\n"),
    ("long-lines", "# T\n" + "word " * 20 + "\n"),
    ("whitespace", "# T\ntrailing \n"),
    ("whitespace", "# T\ntab\there\n"),
    ("emoji", "# T\nhello \U0001f600\n"),
    ("markdown-in-code", "# T\n```console\n**bold**\n```\n"),
    ("c-star-on-type", "# T\n" + c_block("int* p;")),
    ("c-line-comments", "# T\n" + c_block("int x; // note")),
    ("c-status-codes", "# T\n" + c_block("return 0;")),
    ("c-status-codes", "# T\n" + c_block("exit(1);")),
    ("c-uncast-null", "# T\n" + c_block("char *p = NULL;")),
    ("c-typedef-name", "# T\n" + c_block("typedef struct { int a; } point;")),
    ("c-typedef-name", "# T\n" + c_block("typedef unsigned int uint;")),
    ("c-uncast-allocator", "# T\n" + c_block("p = malloc(4);")),
    ("c-sizeof-type", "# T\n" + c_block("p = (int *)malloc(n * sizeof(int));")),
    ("c-sizeof-type", "# T\n" + c_block("putchar('x');")),
]

GOOD = [
    ("metadata", META + "# T\n"),
    ("headings", "# A\n## B\n### C\n"),
    ("embedded-links", "# T\nsee [it][a]\n<!-- Links -->\n[a]: http://x.org\n"),
    ("unused-reference", "# T\nsee [it][a]\n<!-- Links -->\n[a]: http://x.org\n"),
    ("unused-reference", "# T\nsee [a][] now\n<!-- Links -->\n[a]: http://x.org\n"),
    ("unused-reference", "# T\nsee [a] now\n<!-- Links -->\n[a]: http://x.org\n"),
    ("link-text", "# T\nread [a map of memory][m] and [Sir Tony][h]\n"),
    ("order-wording", "# T\nsee [memory allocation][m]\n"),
    ("avoid-words", "# T\nspecific and concrete\n"),
    ("not-y", "# T\nA tool for the job.\n"),
    ("binary-units", "# T\n128 KB of memory\n"),
    ("bare-null", "# T\na **NULL** pointer and `NULL` in code\n"),
    ("long-lines", "# T\n| " + "cell " * 30 + "|\n"),
    ("whitespace", "<!--\nAuthor: x \n-->\n# T\n"),
    ("whitespace", "# T\n```console\ntext\tsize\n```\n"),
    ("emoji", "# T\nplain text\n"),
    ("markdown-in-code", "# T\n```python\nf(**a, **b)\n```\n"),
    ("c-star-on-type", "# T\n" + c_block("int *p; size_t n = sizeof(int* );")),
    (
        "c-line-comments",
        "# T\n" + c_block('int x; /* note */\nputs("http://x"); // see'),
    ),
    ("c-status-codes", "# T\n" + c_block("return EXIT_SUCCESS;")),
    ("c-uncast-null", "# T\n" + c_block("char *p = (char *)NULL;\n#define NULL 0")),
    (
        "c-typedef-name",
        "# T\n"
        + c_block("typedef struct { int a; } point_t;\ntypedef unsigned uint_t;"),
    ),
    ("c-uncast-allocator", "# T\n" + c_block("p = (int *)malloc(4);")),
    ("c-sizeof-type", "# T\n" + c_block("p = (int *)malloc(n * sizeof(*p));")),
]


@pytest.mark.parametrize(("rule", "text"), BAD)
def test_rule_flags_bad_text(rule: str, text: str) -> None:
    """Each rule finds the thing it is looking for."""
    assert hits(rule, text), f"{rule} missed it"


@pytest.mark.parametrize(("rule", "text"), GOOD)
def test_rule_passes_good_text(rule: str, text: str) -> None:
    """Each rule leaves good text alone."""
    assert not hits(rule, text), f"{rule} flagged: {hits(rule, text)}"


def test_every_rule_has_a_bad_case() -> None:
    """Every registered rule is exercised by a failing case."""
    assert {rule for rule, _ in BAD} == set(RULES)


def test_metadata_names_the_missing_fields() -> None:
    """The metadata rule says which fields are missing."""
    found = hits("metadata", "<!--\nAuthor: Erik\n-->\n")
    assert "Date" in found[0][1]
    assert "Author" not in found[0][1]


def test_typedef_reports_the_line() -> None:
    """The typedef rule points at the line holding the name."""
    found = hits(
        "c-typedef-name", "# T\n" + c_block("typedef struct {\n  int a;\n} point;")
    )
    assert found[0][0] == 5


def test_definitions_and_used_references() -> None:
    """Definitions and uses are read from prose and the links block."""
    text = (
        "# T\nsee [a][one] and `x[i][j]` code\n<!-- Links -->\n"
        "[one]: http://x.org\n[two]: y\n"
    )
    parsed = article(text)
    assert definitions(parsed) == {"one": (4, "http://x.org"), "two": (5, "y")}
    assert used_references(parsed) == {"one"}


def test_run_rules_filters_and_collects() -> None:
    """Findings carry the article and rule, and a rule list narrows the run."""
    parsed = article("# T\nit is simply true\n128 KiB\n")
    everything = run_rules([parsed])
    only = run_rules([parsed], ["binary-units"])
    assert {finding.rule for finding in only} == {"binary-units"}
    assert len(everything) > len(only)
    assert only[0].article == "c/x"
    assert only[0].line == 3


def test_run_rules_rejects_unknown_rules() -> None:
    """A misspelled rule name is an error, not silence."""
    with pytest.raises(KeyError, match="nonsense"):
        run_rules([article("# T\n")], ["nonsense"])


def test_comments_are_not_checked_as_prose() -> None:
    """A hidden comment can hold a NULL or a long line without a finding."""
    text = "# T\n<!--\nPromised in: a NULL pointer " + "word " * 20 + "\n-->\n"
    assert not hits("bare-null", text)
    assert not hits("long-lines", text)


def test_void_destinations_need_no_cast() -> None:
    """The allocator rule accepts a void * destination, array element or not."""
    code = (
        "void *block = NULL;\nvoid *blocks[2];\n"
        "block = malloc(4);\nblocks[1] = malloc(4);\nchar *s = malloc(4);"
    )
    found = hits("c-uncast-allocator", "# T\n" + c_block(code))
    assert [line for line, _ in found] == [7]


def test_comparators_may_return_bare_integers() -> None:
    """qsort() comparators return -1, 0 and 1 by convention."""
    code = (
        "int compare_ints(const void *a, const void *b) {\n    return -1;\n}\n"
        "int main(void) {\n    return 0;\n}"
    )
    found = hits("c-status-codes", "# T\n" + c_block(code))
    assert [line for line, _ in found] == [7]
