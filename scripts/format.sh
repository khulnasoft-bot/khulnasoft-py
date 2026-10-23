#!/usr/bin/env bash
set -x

ruff check src/khulnasoft examples tests scripts --fix
ruff format src/khulnasoft examples tests scripts
