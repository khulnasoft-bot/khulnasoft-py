from __future__ import annotations

import os

from celery import Celery

# On Khulnasoft, the runtime installs the khulnasoft-celery integration before this
# module is imported, registering the "khulnasoft://" broker transport and the
# "khulnasoft-runtime-cache://" result backend.
celery_app = Celery(
    "khulnasoft_celery_example_chunks",
    broker=os.getenv("CELERY_BROKER_URL", "khulnasoft://"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "khulnasoft-runtime-cache://"),
)


@celery_app.task(name="chunks.add")
def add(left: int, right: int) -> int:
    result = left + right
    print(f"{left} + {right} = {result}")
    return result
