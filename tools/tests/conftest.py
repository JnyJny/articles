"""Article Tools pytest configuration file."""

import tomllib
from collections.abc import Callable
from pathlib import Path

import pytest

META = (
    "<!--\nAuthor: Erik\nDate: May 2025\nStatus: draft\nSeries: C Programming\n"
    "Prerequisites: none\nNext: none\n-->\n\n"
)

MakeRepo = Callable[[dict[str, str]], Path]


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root path of the project."""
    return Path.cwd()


@pytest.fixture(scope="session")
def pyproject_path(project_root: Path) -> Path:
    """Return the path to the pyproject.toml file."""
    return project_root / "pyproject.toml"


@pytest.fixture(scope="session")
def pyproject_toml(pyproject_path: Path) -> dict:
    """Return the contents of the pyproject.toml file."""
    return tomllib.load(pyproject_path.open("rb"))


@pytest.fixture(scope="session")
def project_version(pyproject_toml: dict) -> str:
    """Return the project version from pyproject.toml."""
    return pyproject_toml["project"]["version"]


@pytest.fixture
def repo(tmp_path: Path) -> MakeRepo:
    """Return a function that builds a small articles repo in a temp dir."""

    def build(files: dict[str, str]) -> Path:
        (tmp_path / "STYLE.md").write_text("# style\n", encoding="utf-8")
        for name, text in files.items():
            path = tmp_path / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        return tmp_path

    return build
