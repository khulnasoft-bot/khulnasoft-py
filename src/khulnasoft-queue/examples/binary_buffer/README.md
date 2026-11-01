# Binary Buffer Queue app

Deploy this directory as a Khulnasoft app:

```bash
cd src/khulnasoft-queue/examples/binary_buffer
vc link
vc deploy
```

Send a message from an environment that has Khulnasoft Queue credentials. Use
`--region iad1` for local sends outside Khulnasoft:

```bash
uv run --project ../.. python -m khulnasoft.queue send --region iad1 --topic images --binary iVBORw0K
```

Check the function logs:

```bash
vc logs <deployment-url>
```

Expected output includes:

```text
Received image bytes 89504e470d0a
```

The push subscriber receives a small `bytes` payload and logs its hexadecimal
representation.
