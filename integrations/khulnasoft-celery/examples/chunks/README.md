# Celery chunks app

Deploy this directory as a Khulnasoft app:

```bash
cd integrations/khulnasoft-celery/examples/chunks
vc link
vc deploy
```

Queue the chunks by requesting the sender endpoint on the deployed app:

```bash
vc curl /enqueue
```

Check the worker logs:

```bash
vc logs <deployment-url>
```

Expected output includes:

```text
queued chunk group <group-id>
0 + 0 = 0
99 + 99 = 198
```

`pyproject.toml` declares `worker.py` as a queue subscriber:

```toml
[[tool.khulnasoft.subscribers]]
entrypoint = "worker:celery_app"
```

The Khulnasoft build introspects the Celery app's queues and compiles the
subscriber into a queue-triggered function; no `khulnasoft.json` trigger
configuration is needed. The FastAPI sender in `main.py` uses Celery canvas
chunks:

```python
add.chunks(zip(range(100), range(100), strict=False), 10).apply_async()
```

Tasks publish through the `khulnasoft://` broker and store results with the
`khulnasoft-runtime-cache://` backend.
