from __future__ import annotations

import dramatiq
from dramatiq.results import Results

from khulnasoft.integrations.dramatiq import KhulnasoftQueueBroker, KhulnasoftRuntimeCacheBackend

# Construct the broker explicitly: dramatiq.set_broker() always takes effect,
# and the broker options are visible right here.
broker = KhulnasoftQueueBroker(queue_name_prefix="dramatiq-khulnasoft-dramatiq-example-chunks-")
broker.add_middleware(Results(backend=KhulnasoftRuntimeCacheBackend()))
dramatiq.set_broker(broker)


@dramatiq.actor(store_results=True)
def add(left: int, right: int) -> int:
    result = left + right
    print(f"{left} + {right} = {result}")
    return result
