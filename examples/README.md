# Examples

This directory holds cross-package examples that combine several Khulnasoft
packages, such as Blob with Projects, runtime cache, and OIDC with FastAPI.

Package-specific examples live in the owning package:

- `src/khulnasoft-sandbox/examples/`
- `src/khulnasoft-queue/examples/`
- `integrations/*/examples/`

Run the root examples, plus every package that opts in, with:

```sh
uv run poe test-examples
```

The root examples require `BLOB_READ_WRITE_TOKEN`, plus `KHULNASOFT_TOKEN` or
`KHULNASOFT_OIDC_TOKEN`, `KHULNASOFT_PROJECT_ID`, and `KHULNASOFT_TEAM_ID`.
They skip safely when those credentials are unavailable.

Pushes to `main` and the nightly schedule run this aggregate in CI. Pull
requests do not, because forked pull requests cannot read the credentials.
