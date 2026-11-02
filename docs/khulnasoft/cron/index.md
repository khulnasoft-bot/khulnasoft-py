# `khulnasoft.cron` — Cron schedule helpers

`khulnasoft.cron` provides cron schedule helpers for KhulnaSoft Python
applications — `CronTab`, `CronSchedule`, and a `cron` decorator.

## Quick start

```python
from khulnasoft.cron import CronTab, CronSchedule, cron

# Parse a cron expression
tab = CronTab("*/5 * * * *")

# Check if a cron expression matches a time
schedule = CronSchedule("0 9 * * 1-5")
if schedule.matches(some_datetime):
    ...
```

## Package layout

```
src/khulnasoft/cron/
├── __init__.py   # Public API: CronSchedule, CronTab, CronTabError, cron
├── crontab.py    # CronTab and CronSchedule implementations
├── README.md
└── py.typed
```

## Public API

| Symbol | Purpose |
|--------|---------|
| `CronTab` | Parse and evaluate cron expressions |
| `CronSchedule` | Cron schedule with matching logic |
| `CronTabError` | Cron tab error |
| `cron` | Cron decorator |

## Requirements

Python 3.10 or later. No dependencies.
