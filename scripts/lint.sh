#!/usr/bin/env bash

set -e
set -x

mypy src/khulnasoft
ruff check src/khulnasoft examples tests scripts
ruff format src/khulnasoft examples tests scripts --check
