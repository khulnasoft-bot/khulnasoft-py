#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = Path(__file__).with_name("type-ignore-baseline.json")
SEARCH_DIRS = ("src", "integrations", "tests", "examples", "scripts")
SKIP_DIRS = {".git", ".venv", "build", "dist", "node_modules", "vendor", "__pycache__"}
PATTERN = re.compile(r"#\s*type:\s*ignore\b")


def _iter_python_files() -> list[Path]:
    files: list[Path] = []
    for name in SEARCH_DIRS:
        base = ROOT / name
        if not base.is_dir():
            continue
        for path in base.rglob("*.py"):
            if path.is_symlink():
                continue
            if any(part in SKIP_DIRS for part in path.relative_to(ROOT).parts):
                continue
            files.append(path)
    return sorted(files)


def count_ignores() -> dict[str, int]:
    counts: dict[str, int] = {}
    for path in _iter_python_files():
        lines = path.read_text(encoding="utf-8").splitlines()
        count = sum(1 for line in lines if PATTERN.search(line))
        if count:
            counts[path.relative_to(ROOT).as_posix()] = count
    return dict(sorted(counts.items()))


def _load_baseline() -> dict[str, int]:
    if not BASELINE.exists():
        return {}
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    return {str(path): int(count) for path, count in payload.get("files", {}).items()}


def _write_baseline(counts: dict[str, int]) -> None:
    payload = {"total": sum(counts.values()), "files": counts}
    BASELINE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Track type-ignore comments against a baseline.")
    parser.add_argument("--update", action="store_true", help="Rewrite the baseline from the tree.")
    args = parser.parse_args(argv)

    current = count_ignores()
    if args.update:
        _write_baseline(current)
        print(f"recorded {sum(current.values())} type-ignore comments")
        return 0

    baseline = _load_baseline()
    regressions: list[str] = []
    for path, count in current.items():
        allowed = baseline.get(path, 0)
        if count > allowed:
            regressions.append(f"{path}: {count} > {allowed}")
    for path, allowed in baseline.items():
        if current.get(path, 0) > allowed:
            regressions.append(f"{path}: {current[path]} > {allowed}")

    current_total = sum(current.values())
    baseline_total = sum(baseline.values())
    if current_total > baseline_total:
        regressions.append(f"total: {current_total} > {baseline_total}")

    if regressions:
        print("type-ignore count grew beyond the baseline:", file=sys.stderr)
        for line in sorted(set(regressions)):
            print(f"  {line}", file=sys.stderr)
        print("Remove the ignore, or update the baseline with --update.", file=sys.stderr)
        return 1

    if current_total < baseline_total:
        print(
            f"type-ignore count dropped to {current_total} from {baseline_total}; "
            "run with --update to ratchet the baseline"
        )
    else:
        print(f"type-ignore count is at the baseline of {baseline_total}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
