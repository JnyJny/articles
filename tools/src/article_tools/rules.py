"""The style rules from STYLE.md that a script can check."""

from __future__ import annotations

import dataclasses
import re
from collections.abc import Callable

from .model import CODE, LINKS, META, PROSE, Article, Finding, Line

Hits = list[tuple[int, str]]
Rule = Callable[[Article], Hits]

RULES: dict[str, Rule] = {}

METADATA_FIELDS = ("Author", "Date", "Status", "Series", "Prerequisites", "Next")
MAX_HEADING_DEPTH = 3
MAX_PROSE_COLUMNS = 80
SNIPPET = 60
GENERIC_LABELS = {
    "here",
    "link",
    "this",
    "this article",
    "the article",
    "web version",
    "article",
    "read more",
}
PROPER_NOUNS = {"c", "i", "unix", "posix", "linux", "python", "glibc", "gcc", "null"}
AVOIDED = re.compile(
    r"\b(genuinely|ceremony|quietly|honest(?:ly)?|simply|obviously|professional|modern)\b",
    re.IGNORECASE,
)
ORDER_WORDING = re.compile(
    r"\b(?:the )?(?:last|next|previous|earlier|prior|following) "
    r"(?:article|post|piece|installment)\b",
    re.IGNORECASE,
)
NOT_Y = re.compile(
    r"\b[Ii]t'?s (?:not|just|only) [^.]*?, (?:it'?s|but)"
    r"|\b[Ii]t'?s [^.,]{2,40}, not [^.,]{2,40}[.,]"
    r"|\bnot [^.,]{2,30}, but\b",
)
CLICHES = re.compile(r"\b(masquerad|in an overcoat|short version is)", re.IGNORECASE)
EMOJI = re.compile("[\U0001f300-\U0001faff☀-⛿✀-➿]")
BINARY_UNIT = re.compile(r"\b[KMGT]iB\b")
EMBEDDED_LINK = re.compile(r"\[[^\]]*\]\([^)]*\)")
FULL_REFERENCE = re.compile(r"\]\[([^\]\[\n]+)\]")
COLLAPSED_REFERENCE = re.compile(r"\[([^\]\[\n]+)\]\[\]")
SHORTHAND_REFERENCE = re.compile(r"(?<!\])\[([^\]\[\n]+)\](?![(\[:])")
DEFINITION = re.compile(r"^\[([^\]]+)\]:\s*(\S.*)$")
LINK_TEXT = re.compile(r"\[([^\]]+)\]\[([^\]]+)\]")
INLINE_CODE = re.compile(r"`[^`]*`")
BOLD_NULL = re.compile(r"\*\*NULL\*\*")
BARE_NULL = re.compile(r"\bNULL\b")
BOLD = re.compile(r"\*\*[^*]+\*\*")
TYPE_NAMES = r"(?:int|char|void|float|double|long|size_t|\w+_t)"
STAR_ON_TYPE = re.compile(rf"\b{TYPE_NAMES}\*+\s+\w")
LINE_COMMENT = re.compile(r"(?<!:)//")
BARE_STATUS = re.compile(r"\breturn\s+(?:0|-1|1)\s*;|\bexit\s*\(\s*(?:0|1|-1)\s*\)")
UNCAST_NULL = re.compile(r"(?<!\))(?<!\)\s)\bNULL\b")
UNCAST_ALLOCATOR = re.compile(r"=\s*(?:malloc|calloc|realloc)\s*\(")
SIZEOF_TYPE = re.compile(
    r"(?:malloc|calloc)\s*\([^)]*sizeof\s*\(\s*(?:int|char|long|float|double|\w+_t)\s*\)",
)
PUTCHAR = re.compile(r"\bputchar\s*\(")
VOID_VARIABLE = re.compile(r"\bvoid\s*\*+\s*(\w+)")
ASSIGNED_ALLOCATION = re.compile(
    r"(\w+)(?:\[[^\]]*\])?\s*=\s*(?:malloc|calloc|realloc)\s*\(",
)
FUNCTION_DEFINITION = re.compile(r"^[A-Za-z_][\w\s*]*?\b(\w+)\s*\(.*\)\s*\{?\s*$")
COMPARATOR = re.compile(r"^(?:compare|cmp)", re.IGNORECASE)
MAIN_DEFINITION = re.compile(r"^(?:int|void)\s+main\s*\(")
STRUCT_TYPEDEF = re.compile(
    r"typedef\s+(?:struct|union|enum)\b[^;{]*\{[^}]*\}\s*(\w+)\s*;",
)
SIMPLE_TYPEDEF = re.compile(r"typedef\s+(?!struct|union|enum)[^;{(]+?\s\**(\w+)\s*;")


def rule(name: str) -> Callable[[Rule], Rule]:
    """Register a rule under a name."""

    def register(function: Rule) -> Rule:
        RULES[name] = function
        return function

    return register


def snippet(text: str) -> str:
    """Trim a line down to something that fits in a report."""
    return text.strip()[:SNIPPET]


def line_text(article: Article, number: int) -> str:
    """Return the stripped text of a numbered line, or nothing."""
    if 1 <= number <= len(article.lines):
        return article.lines[number - 1].text.strip()
    return ""


def prose_lines(article: Article) -> list[tuple[int, str]]:
    """Return (number, text) for every prose line."""
    return [(line.number, line.text) for line in article.of_kind(PROSE)]


def definitions(article: Article) -> dict[str, tuple[int, str]]:
    """Return the link reference definitions as {reference: (line, target)}."""
    found: dict[str, tuple[int, str]] = {}
    for line in article.of_kind(PROSE, LINKS):
        match = DEFINITION.match(line.text)
        if match:
            found[match.group(1)] = (line.number, match.group(2).strip())
    return found


def used_references(article: Article, *, shorthand: bool = True) -> set[str]:
    """Return the references the prose uses, in any of the three forms."""
    text = "\n".join(
        INLINE_CODE.sub("", line.text)
        for line in article.of_kind(PROSE, LINKS)
        if not DEFINITION.match(line.text)
    )
    used = set(FULL_REFERENCE.findall(text)) | set(COLLAPSED_REFERENCE.findall(text))
    if shorthand:
        used |= set(SHORTHAND_REFERENCE.findall(text))
    return used


@rule("metadata")
def metadata(article: Article) -> Hits:
    """Every article starts with a complete metadata comment."""
    block = [line.text for line in article.of_kind(META)]
    if not block:
        return [(1, "no metadata block")]
    present = {text.split(":", 1)[0].strip() for text in block if ":" in text}
    missing = [field for field in METADATA_FIELDS if field not in present]
    return [(1, f"metadata block lacks {', '.join(missing)}")] if missing else []


@rule("headings")
def headings(article: Article) -> Hits:
    """One H1 title, and nothing deeper than H3."""
    prose = prose_lines(article)
    hits: Hits = [
        (number, text[:SNIPPET])
        for number, text in prose
        if re.match(rf"#{{{MAX_HEADING_DEPTH + 1},}} ", text)
    ]
    titles = [number for number, text in prose if text.startswith("# ")]
    if len(titles) != 1:
        hits.append((1, f"expected one H1 title, found {len(titles)}"))
    return hits


@rule("embedded-links")
def embedded_links(article: Article) -> Hits:
    """Links are references, with the URLs at the bottom."""
    matches = [
        (number, EMBEDDED_LINK.search(text)) for number, text in prose_lines(article)
    ]
    return [(number, match.group(0)[:SNIPPET]) for number, match in matches if match]


@rule("unused-reference")
def unused_reference(article: Article) -> Hits:
    """Every defined link reference is used."""
    used = used_references(article)
    return [
        (number, f"[{reference}] is defined and never used")
        for reference, (number, _target) in definitions(article).items()
        if reference not in used
    ]


@rule("link-text")
def link_text(article: Article) -> Hits:
    """Link a lowercase phrase from the sentence, not a title or a label."""
    hits: Hits = []
    for number, text in prose_lines(article):
        for match in LINK_TEXT.finditer(text):
            words = re.findall(r"[A-Za-z']+", match.group(1))
            capitalized = [
                word
                for word in words[1:]
                if word[0].isupper() and word.lower() not in PROPER_NOUNS
            ]
            if len(words) >= 2 and len(capitalized) >= 2:  # noqa: PLR2004
                hits.append((number, f"title-cased link text [{match.group(1)}]"))
            if match.group(1).lower() in GENERIC_LABELS:
                hits.append((number, f"generic link text [{match.group(1)}]"))
    return hits


@rule("order-wording")
def order_wording(article: Article) -> Hits:
    """Never say "the last article" or "the next article"."""
    matches = [
        (number, ORDER_WORDING.search(text)) for number, text in prose_lines(article)
    ]
    return [(number, match.group(0)) for number, match in matches if match]


@rule("avoid-words")
def avoid_words(article: Article) -> Hits:
    """Words the style guide asks you to avoid."""
    return [
        (number, match.group(0))
        for number, text in prose_lines(article)
        for match in AVOIDED.finditer(text)
    ]


@rule("not-y")
def not_y(article: Article) -> Hits:
    """Flag the "It's X, not Y" construction and its cousins."""
    hits: Hits = []
    for number, text in prose_lines(article):
        if NOT_Y.search(text):
            hits.append((number, f"it's X, not Y: {snippet(text)}"))
        if CLICHES.search(text):
            hits.append((number, f"cliche: {snippet(text)}"))
    return hits


@rule("binary-units")
def binary_units(article: Article) -> Hits:
    """Write KB, MB and GB for 1024-based sizes."""
    return [
        (number, match.group(0))
        for number, text in prose_lines(article)
        for match in BINARY_UNIT.finditer(text)
    ]


@rule("bare-null")
def bare_null(article: Article) -> Hits:
    """NULL is bold in prose."""
    hits: Hits = []
    for number, text in prose_lines(article):
        if text.startswith(("#", "[", "|")):
            continue
        plain = BOLD_NULL.sub("", INLINE_CODE.sub("", text))
        if BARE_NULL.search(plain):
            hits.append((number, snippet(text)))
    return hits


@rule("long-lines")
def long_lines(article: Article) -> Hits:
    """Prose lines stay within 80 columns."""
    return [
        (number, f"{len(text)} columns")
        for number, text in prose_lines(article)
        if len(text) > MAX_PROSE_COLUMNS and not text.startswith(("|", "["))
    ]


@rule("whitespace")
def whitespace(article: Article) -> Hits:
    """No trailing whitespace, and no tabs in prose."""
    hits: Hits = []
    for line in article.lines:
        if line.kind == META:
            continue
        if line.text != line.text.rstrip():
            hits.append((line.number, "trailing whitespace"))
        elif "\t" in line.text and line.kind != CODE:
            hits.append((line.number, "tab"))
    return hits


@rule("emoji")
def emoji(article: Article) -> Hits:
    """No emoji."""
    return [
        (line.number, snippet(line.text))
        for line in article.lines
        if EMOJI.search(line.text)
    ]


@rule("markdown-in-code")
def markdown_in_code(article: Article) -> Hits:
    """No Markdown emphasis inside code blocks."""
    return [
        (line.number, snippet(line.text))
        for line in article.of_kind(CODE)
        if line.lang.lower() != "python" and BOLD.search(line.text)
    ]


@rule("c-star-on-type")
def c_star_on_type(article: Article) -> Hits:
    """Bind the asterisk to the variable name: int *p."""
    return [
        (line.number, snippet(line.text))
        for line in article.c_code()
        if STAR_ON_TYPE.search(line.text)
        and "sizeof" not in line.text
        and not line.text.strip().startswith(("/*", "*"))
    ]


@rule("c-line-comments")
def c_line_comments(article: Article) -> Hits:
    """C comments use /* */."""
    return [
        (line.number, snippet(line.text))
        for line in article.c_code()
        if LINE_COMMENT.search(line.text) and "http" not in line.text
    ]


@rule("c-status-codes")
def c_status_codes(article: Article) -> Hits:
    """Use EXIT_SUCCESS and EXIT_FAILURE, except in comparators."""
    hits: Hits = []
    function = ""
    for line in article.c_code():
        defined = FUNCTION_DEFINITION.match(line.text)
        if defined and not line.text.startswith((" ", "\t")):
            function = defined.group(1)
        if BARE_STATUS.search(line.text) and not COMPARATOR.match(function):
            hits.append((line.number, snippet(line.text)))
    return hits


def c_blocks(article: Article) -> list[list[Line]]:
    """Group the lines of C code into the blocks they were written in."""
    blocks: list[list[Line]] = []
    for line in article.c_code():
        if blocks and line.number == blocks[-1][-1].number + 1:
            blocks[-1].append(line)
        else:
            blocks.append([line])
    return blocks


@rule("c-main-first")
def c_main_first(article: Article) -> Hits:
    """In a demo program main() comes first and helpers follow it."""
    hits: Hits = []
    for block in c_blocks(article):
        main_at = next(
            (i for i, line in enumerate(block) if MAIN_DEFINITION.match(line.text)),
            None,
        )
        if main_at is None:
            continue
        hits.extend(
            (line.number, snippet(line.text))
            for line in block[:main_at]
            if FUNCTION_DEFINITION.match(line.text)
            and not line.text.startswith((" ", "\t", "#"))
        )
    return hits


@rule("c-uncast-null")
def c_uncast_null(article: Article) -> Hits:
    """NULL carries a cast: (int *)NULL."""
    return [
        (line.number, snippet(line.text))
        for line in article.c_code()
        if UNCAST_NULL.search(line.text) and "#define" not in line.text
    ]


@rule("c-typedef-name")
def c_typedef_name(article: Article) -> Hits:
    """Typedef names end in _t."""
    code = article.c_code()
    text = "\n".join(line.text for line in code)
    names = STRUCT_TYPEDEF.findall(text) + SIMPLE_TYPEDEF.findall(text)
    hits: Hits = []
    for name in names:
        if name.endswith("_t"):
            continue
        number = next(
            (line.number for line in code if re.search(rf"\b{name}\s*;", line.text)),
            0,
        )
        hits.append((number, f"typedef {name} does not end in _t"))
    return hits


@rule("c-uncast-allocator")
def c_uncast_allocator(article: Article) -> Hits:
    """Cast the result of malloc, calloc and realloc, unless it goes into a void *."""
    code = article.c_code()
    void_variables = set(VOID_VARIABLE.findall("\n".join(line.text for line in code)))
    hits: Hits = []
    for line in code:
        assigned = ASSIGNED_ALLOCATION.search(line.text)
        if UNCAST_ALLOCATOR.search(line.text) and not (
            assigned and assigned.group(1) in void_variables
        ):
            hits.append((line.number, snippet(line.text)))
    return hits


@rule("c-sizeof-type")
def c_sizeof_type(article: Article) -> Hits:
    """Size allocations with sizeof(*p), and print with an explicit stream."""
    return [
        (line.number, snippet(line.text))
        for line in article.c_code()
        if SIZEOF_TYPE.search(line.text) or PUTCHAR.search(line.text)
    ]


def run_rules(
    articles: list[Article],
    only: list[str] | None = None,
) -> list[Finding]:
    """Run the rules over the articles and return every finding."""
    unknown = sorted(set(only or []) - set(RULES))
    if unknown:
        message = f"unknown rule(s): {', '.join(unknown)}"
        raise KeyError(message)
    chosen = {name: RULES[name] for name in (only or RULES)}
    return [
        dataclasses.replace(
            article.finding(name, number, message),
            context=line_text(article, number),
        )
        for article in articles
        for name, function in chosen.items()
        for number, message in function(article)
    ]
