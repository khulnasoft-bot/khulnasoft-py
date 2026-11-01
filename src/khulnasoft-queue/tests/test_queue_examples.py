from __future__ import annotations

import re
from pathlib import Path

import pytest

EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
EXAMPLE_SOURCES = sorted(EXAMPLES_DIR.rglob("*.py"))
DEPLOYABLE_EXAMPLES = sorted(
    path
    for path in EXAMPLES_DIR.iterdir()
    if path.is_dir() and (path / "main.py").is_file() and (path / "pyproject.toml").is_file()
)


@pytest.mark.parametrize(
    "source",
    EXAMPLE_SOURCES,
    ids=lambda path: str(path.relative_to(EXAMPLES_DIR)),
)
def test_example_sources_compile(source: Path) -> None:
    compile(source.read_text(encoding="utf-8"), str(source), "exec")


@pytest.mark.parametrize("directory", DEPLOYABLE_EXAMPLES, ids=lambda path: path.name)
def test_deployable_example_metadata(directory: Path) -> None:
    pyproject = (directory / "pyproject.toml").read_text(encoding="utf-8")

    assert re.search(r'(?m)^name = "[^"]+"$', pyproject)
    assert "[[tool.khulnasoft.subscribers]]" in pyproject
    assert (directory / "README.md").is_file()


def test_examples_are_discoverable() -> None:
    assert EXAMPLE_SOURCES
    assert DEPLOYABLE_EXAMPLES
