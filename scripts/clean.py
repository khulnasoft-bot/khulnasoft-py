from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "node_modules"}
REMOVED_DIRS = {
    ".hypothesis",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}
REMOVED_SUFFIXES = {".egg-info", ".pyc", ".pyo"}
COVERAGE_FILE = ".coverage"
COVERAGE_XML = "coverage.xml"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Remove local build and test artifacts.")
    parser.add_argument("--dry-run", action="store_true", help="Report what would be removed.")
    parser.add_argument("--venv", action="store_true", help="Also remove .venv.")
    return parser.parse_args()


def collect_targets(*, include_venv: bool) -> list[Path]:
    targets: list[Path] = []
    venv = ROOT / ".venv"
    if include_venv and venv.exists():
        targets.append(venv)

    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True):
        current = Path(dirpath)
        kept: list[str] = []
        for name in sorted(dirnames):
            candidate = current / name
            if name in SKIP_DIRS:
                continue
            if name.endswith(".egg-info") or name in REMOVED_DIRS:
                targets.append(candidate)
                continue
            kept.append(name)
        dirnames[:] = kept

        for name in sorted(filenames):
            candidate = current / name
            if (
                candidate.suffix in REMOVED_SUFFIXES
                or name in {COVERAGE_FILE, COVERAGE_XML}
                or name.startswith(f"{COVERAGE_FILE}.")
            ):
                targets.append(candidate)

    return targets


def remove(target: Path) -> None:
    if target.is_dir() and not target.is_symlink():
        shutil.rmtree(target)
    else:
        target.unlink()


def main() -> int:
    args = parse_args()
    targets = collect_targets(include_venv=args.venv)
    if not targets:
        print("nothing to clean")
        return 0

    verb = "would remove" if args.dry_run else "removing"
    for target in targets:
        print(f"{verb} {target.relative_to(ROOT)}")
        if not args.dry_run:
            remove(target)

    action = "would remove" if args.dry_run else "removed"
    print(f"{action} {len(targets)} paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
