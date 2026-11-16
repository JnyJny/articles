"""Check that article directories are laid out the way the style guide says."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .model import Finding
from .stubs import CATEGORIES

if TYPE_CHECKING:
    from pathlib import Path

RULE = "layout"


def directory_findings(name: str, directory: Path) -> list[Finding]:
    """Check one article directory."""
    findings: list[Finding] = []
    readme = directory / "README.md"
    if readme.is_symlink() and not readme.exists():
        target = readme.readlink()
        message = f"README.md is a symlink to {target}, which does not exist"
        findings.append(Finding(name, RULE, 0, message))
    if not (directory / "article.md").exists():
        strays = sorted(
            path.name for path in directory.glob("*.md") if path.name != "README.md"
        )
        if strays:
            message = f"no article.md, but {', '.join(strays)} is here; rename it?"
            findings.append(Finding(name, RULE, 0, message))
    return findings


def check_layout(root: Path) -> list[Finding]:
    """Check every directory under the category directories."""
    findings: list[Finding] = []
    for category in CATEGORIES:
        base = root / category
        if not base.is_dir():
            continue
        for directory in sorted(base.iterdir()):
            if directory.is_dir():
                findings += directory_findings(
                    f"{category}/{directory.name}", directory
                )
    return findings
