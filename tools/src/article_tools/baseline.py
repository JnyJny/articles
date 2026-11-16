"""Findings that have been looked at and accepted, kept in one TOML file."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from .model import Finding

DEFAULT_NAME = "accepted.toml"
REQUIRED = ("article", "rule", "message", "context")
HEADER = """\
# Findings from `article-tools audit` that have been looked at and accepted.
#
# An entry matches on article, rule, message and the text of the line, so
# editing the line brings the finding back. Say why in `reason`.
"""

Key = tuple[str, str, str, str]


@dataclass(frozen=True)
class Accepted:
    """One finding someone decided to live with."""

    article: str
    rule: str
    message: str
    context: str
    reason: str = ""

    @property
    def key(self) -> Key:
        """Return what an entry matches on."""
        return (self.article, self.rule, self.message, self.context)


@dataclass(frozen=True)
class Applied:
    """What a baseline does to a list of findings."""

    new: list[Finding]
    skipped: list[Finding]
    stale: list[Accepted]


def key_of(finding: Finding) -> Key:
    """Return what a finding is matched on."""
    return (finding.article, finding.rule, finding.message, finding.context)


def read(path: Path) -> list[Accepted]:
    """Read the accepted findings. A missing file means there are none."""
    if not path.is_file():
        return []
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        message = f"{path}: {error}"
        raise ValueError(message) from error
    entries: list[Accepted] = []
    for number, table in enumerate(data.get("accepted", []), 1):
        missing = [name for name in REQUIRED if not isinstance(table.get(name), str)]
        if missing:
            message = f"{path}: entry {number} lacks {', '.join(missing)}"
            raise ValueError(message)
        entries.append(
            Accepted(
                article=table["article"],
                rule=table["rule"],
                message=table["message"],
                context=table["context"],
                reason=str(table.get("reason", "")),
            ),
        )
    return entries


def quote(text: str) -> str:
    """Write text as a TOML basic string."""
    return json.dumps(text, ensure_ascii=False).replace("\x7f", "\\u007f")


def write(path: Path, entries: list[Accepted]) -> None:
    """Write the accepted findings, sorted so the file diffs cleanly."""
    ordered = sorted(
        entries,
        key=lambda entry: (entry.article, entry.rule, entry.context, entry.message),
    )
    chunks = [HEADER]
    for entry in ordered:
        fields = "".join(
            f"{name} = {quote(getattr(entry, name))}\n"
            for name in (*REQUIRED, "reason")
        )
        chunks.append(f"\n[[accepted]]\n{fields}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(chunks), encoding="utf-8")


def apply(
    findings: list[Finding],
    accepted: list[Accepted],
    *,
    rules: set[str],
    articles: set[str],
) -> Applied:
    """Split findings into new and accepted, and find entries gone stale.

    An entry is stale when its rule and article were checked and nothing
    matched it. Entries for rules or articles that were not checked this
    time are left alone.
    """
    accepted_keys = {entry.key for entry in accepted}
    seen = {key_of(finding) for finding in findings}
    return Applied(
        new=[finding for finding in findings if key_of(finding) not in accepted_keys],
        skipped=[finding for finding in findings if key_of(finding) in accepted_keys],
        stale=[
            entry
            for entry in accepted
            if entry.rule in rules
            and entry.article in articles
            and entry.key not in seen
        ],
    )


def accept(findings: list[Finding], accepted: list[Accepted]) -> list[Accepted]:
    """Add findings to the accepted list, keeping the reasons already there."""
    entries = {entry.key: entry for entry in accepted}
    for finding in findings:
        entries.setdefault(
            key_of(finding),
            Accepted(finding.article, finding.rule, finding.message, finding.context),
        )
    return list(entries.values())
