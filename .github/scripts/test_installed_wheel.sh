#!/bin/sh
# Install a built bundle wheel and run the package tests against it.
#
# Usage: test_installed_wheel.sh <package> <wheel>
#
# Bundle wheels vendor their dependencies under a private namespace, so the
# tests must run against the installed wheel rather than the source tree. respx
# patches the unvendored httpx2 and therefore cannot intercept the vendored
# copy; every test that touches respx is deselected by scanning its AST.

set -eu

if [ "$#" -ne 2 ]; then
    echo "usage: $0 <package> <wheel>" >&2
    exit 2
fi

PACKAGE=$1
WHEEL=$2
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)

if [ ! -f "$WHEEL" ]; then
    echo "wheel not found: $WHEEL" >&2
    exit 1
fi

PACKAGE_ROOT=
for candidate in "$ROOT/src/$PACKAGE" "$ROOT/integrations/$PACKAGE"; do
    if [ -d "$candidate" ]; then
        PACKAGE_ROOT=$candidate
        break
    fi
done

if [ -z "$PACKAGE_ROOT" ]; then
    echo "package source not found for $PACKAGE" >&2
    exit 1
fi

WORKDIR=$(mktemp -d "${TMPDIR:-/tmp}/test-installed-wheel.XXXXXX")
trap 'rm -rf "$WORKDIR"' EXIT INT TERM

echo "creating environment for $PACKAGE"
uv venv --no-config "$WORKDIR/venv"
VENV_PYTHON=$WORKDIR/venv/bin/python

echo "installing test tooling"
uv pip install --project "$ROOT" --python "$VENV_PYTHON" --group dev

echo "installing $WHEEL"
uv pip install --python "$VENV_PYTHON" "$WHEEL"

if [ ! -d "$PACKAGE_ROOT/tests" ]; then
    echo "no tests for $PACKAGE; verifying import"
    "$VENV_PYTHON" - "$PACKAGE" <<'PY'
import importlib
import sys

package = sys.argv[1].replace("-", "_")
importlib.import_module(package)
PY
    exit 0
fi

cp -R "$PACKAGE_ROOT/tests" "$WORKDIR/tests"

# Only the repo-local vendored test helpers (for example vendor.respx.plugin)
# may come from the source tree. The package itself must resolve from the wheel.
cd "$WORKDIR"
PYTHONPATH="$ROOT" "$VENV_PYTHON" - "$WORKDIR" <<'PY'
import ast
import sys
from pathlib import Path


def node_source(source: str, node: ast.AST) -> str:
    """Return a node's source, including decorators."""
    parts = []
    for decorator in getattr(node, "decorator_list", ()) or ():
        segment = ast.get_source_segment(source, decorator)
        if segment:
            parts.append(segment)
    segment = ast.get_source_segment(source, node)
    if segment:
        parts.append(segment)
    return "\n".join(parts)


def _walk(node: ast.AST):
    yield node
    for child in ast.iter_child_nodes(node):
        yield from _walk(child)


def respx_helper_names(source: str, module: ast.Module) -> set[str]:
    """Return module-level helpers that use respx, directly or indirectly."""
    helpers: set[str] = set()
    changed = True
    while changed:
        changed = False
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    continue
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    continue
            else:
                continue
            if node.name in helpers:
                continue
            if "respx" in node_source(source, node):
                helpers.add(node.name)
                changed = True
                continue
            for child in _walk(node):
                if isinstance(child, ast.Name) and child.id in helpers:
                    helpers.add(node.name)
                    changed = True
                    break
    return helpers


def uses_respx(source: str, node: ast.AST, helpers: set[str]) -> bool:
    """Return whether a test reaches respx directly or through a helper."""
    if "respx" in node_source(source, node):
        return True
    for child in _walk(node):
        if isinstance(child, ast.Name) and child.id in helpers:
            return True
        if isinstance(child, ast.Attribute) and isinstance(child.value, ast.Name):
            if child.value.id in helpers:
                return True
        if isinstance(child, ast.arg) and child.arg in helpers:
            return True
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            if child.value in helpers:
                return True
    return False


def pytest_filter_for_tests(root: Path) -> list[str]:
    """Build pytest arguments that deselect every respx test under root/tests."""
    args: list[str] = []
    tests = root / "tests"
    if not tests.is_dir():
        return args
    for path in sorted(tests.rglob("test_*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            module = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        helpers = respx_helper_names(source, module)
        names: list[str] = []
        for node in module.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_") and uses_respx(source, node, helpers):
                    names.append(node.name)
            elif isinstance(node, ast.ClassDef) and uses_respx(source, node, helpers):
                names.append(node.name)
        relative = path.relative_to(root).as_posix()
        args.extend(f"--deselect={relative}::{name}" for name in names)
    return args


def main() -> int:
    import pytest

    root = Path(sys.argv[1])
    args = [
        "-q",
        "-p",
        "no:cacheprovider",
        "-m",
        "not live",
        "--asyncio-mode=auto",
        *pytest_filter_for_tests(root),
    ]
    return pytest.main([str(root / "tests"), *args])


if __name__ == "__main__":
    raise SystemExit(main())
PY
