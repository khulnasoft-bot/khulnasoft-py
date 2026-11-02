#!/usr/bin/env python3
from __future__ import annotations

import sys

from workspace import main

package = sys.argv[1] if len(sys.argv) > 1 else "khulnasoft"
raise SystemExit(main(["version", package]))
