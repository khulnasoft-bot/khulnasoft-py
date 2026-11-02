# Retry Handling Queue app

Deploy this directory as a Khulnasoft app:

```bash
cd src/khulnasoft-queue/examples/retry_handling
vc link
vc deploy
```

Send a message from an environment that has Khulnasoft Queue credentials. Use
`--region iad1` for local sends outside Khulnasoft:

```bash
uv run --project ../.. python -m khulnasoft.queue send --region iad1 --topic jobs --json '{"job_id":"job_123","simulate_failure":true}'
```

Check the function logs:

```bash
vc logs <deployment-url>
```

Expected output includes:

```text
Retrying job job_123 attempt 1
Retrying job job_123 attempt 2
Processed job job_123 attempt 3
```

The subscriber reads `Message.metadata.delivery_count`, raises `RetryAfter(30)`
for transient failures, and uses `max_attempts=3` to cap retries.
