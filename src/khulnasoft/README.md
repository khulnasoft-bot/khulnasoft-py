# khulnasoft Package Map

This package exposes small public modules for Khulnasoft APIs and Khulnasoft Function
helpers.

## Public Modules

- `khulnasoft.blob` - Khulnasoft Blob uploads, downloads, metadata, listing, copy, and delete
- `khulnasoft.cache` - Runtime Cache clients and invalidation helpers
- `khulnasoft.cron` - cron decorators and schedule helpers
- `khulnasoft.deployments` - deployment creation and deployment file upload helpers
- `khulnasoft.functions` - convenience exports for function code
- `khulnasoft.oidc` - OIDC token lookup, refresh, credentials, and payload decoding
- `khulnasoft.project_routes` - project-level routing rule staging, publishing, and history
- `khulnasoft.projects` - project list, create, update, and delete helpers
- `khulnasoft.sandbox` - Sandbox creation, commands, files, and snapshots, delivered by the
  separately owned `khulnasoft-sandbox` dependency
- `khulnasoft.workflow` - Workflows, steps, sleeps, hooks, and run startup, delivered by the
  separately owned `khulnasoft-workflow` dependency
- `khulnasoft.client` - `AsyncKhulnasoft` and `Khulnasoft` grouped clients
- `khulnasoft.env` - Khulnasoft system environment variable parsing
- `khulnasoft.headers` - request header context, IP, and geolocation helpers

## Internals

`khulnasoft._internal` contains implementation details shared by the public modules.
Do not import from it in application code or generated examples; it may change
without public API guarantees.

`khulnasoft.internal` is reserved for separately distributed internal packages
such as `khulnasoft-internal-telemetry`. It is also not public API. Feature
packages own one `khulnasoft/<feature>` path, and integrations own
`khulnasoft/integrations/<name>`; no two packages may claim the same path.
