#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COVERAGE_FILE = ROOT / ".coverage"
COVERAGE_XML = ROOT / "coverage.xml"
DEFAULT_FAIL_UNDER = 80.0


def _clean() -> None:
    for path in ROOT.glob(".coverage*"):
        path.unlink(missing_ok=True)
    COVERAGE_XML.unlink(missing_ok=True)


def _run(command: list[str], *, env: dict[str, str]) -> int:
    return subprocess.run(command, cwd=ROOT, env=env, check=False).returncode


def _scopes(env: dict[str, str]) -> list[str]:
    output = subprocess.check_output(
        [sys.executable, str(ROOT / "scripts" / "poe" / "workspace_poe_resolve.py")],
        cwd=ROOT,
        env={**env, "WORKSPACE_POE_SCOPE_TASK": "test"},
        text=True,
    )
    return [line.split("\t", 1)[0] for line in output.splitlines() if line]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the workspace tests with coverage.")
    parser.add_argument(
        "--fail-under",
        type=float,
        default=DEFAULT_FAIL_UNDER,
        help="Exit nonzero when total coverage is below this percentage.",
    )
    args = parser.parse_args(argv)

    _clean()
    env = {
        **os.environ,
        "COVERAGE_FILE": str(COVERAGE_FILE),
        "WORKSPACE_POE_TEST_RUNNER": "pytest",
        "FORCE_PYTEST": "1",
        "WORKSPACE_POE_PARALLEL": "0",
        "WORKSPACE_POE_PYTEST_XDIST": "1",
    }
    test_status = 0
    for scope in _scopes(env):
        status = _run(
            [
                sys.executable,
                str(ROOT / "scripts" / "poe" / "workspace_poe.py"),
                "workspace",
                "test",
                scope,
                "--",
                "--cov=khulnasoft",
                "--cov-branch",
                "--cov-append",
                "--cov-report=",
            ],
            env=env,
        )
        test_status = test_status or status
    if test_status:
        return test_status
    report_status = _run(
        [
            sys.executable,
            "-m",
            "coverage",
            "report",
            f"--fail-under={args.fail_under}",
        ],
        env=env,
    )
    xml_status = _run(
        [sys.executable, "-m", "coverage", "xml", "-o", str(COVERAGE_XML)],
        env=env,
    )
    return report_status or xml_status


if __name__ == "__main__":
    raise SystemExit(main())
