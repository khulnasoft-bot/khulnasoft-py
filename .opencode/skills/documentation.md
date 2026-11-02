# Documentation Skill

This skill provides guidance for creating and maintaining documentation for the KhulnaSoft Python SDK monorepo.

## When to use

Use this skill when creating or updating documentation for any package under `src/`.

## Documentation structure

```
docs/
├── index.md              # SDK overview and package index
├── ai/                   # khulnasoft.ai documentation
│   ├── index.md          # Overview + quick start + API reference
│   ├── concepts.md       # Deep dives (agents, tools, events, hooks, telemetry)
│   └── modules.md        # Per-module responsibility breakdown
├── blob/                 # khulnasoft-blob documentation
│   ├── index.md
│   ├── concepts.md
│   └── modules.md
├── cache/index.md
├── connect/index.md
├── headers/index.md
├── internal-core/index.md
├── internal-telemetry/index.md
├── oidc/index.md
├── queue/index.md
├── sandbox/index.md
├── workflow/index.md
└── khulnasoft/           # Meta package (src/khulnasoft/)
    ├── index.md
    ├── blob/index.md
    ├── cron/index.md
    ├── deployments/index.md
    ├── functions/index.md
    ├── project_routes/index.md
    └── projects/index.md
```

## Documentation guidelines

### Each package docs directory should contain:
- `index.md` — Overview, quick start, package layout, public API reference, requirements, related links
- `concepts.md` (optional) — Deep dives on key concepts (credentials, access levels, hooks, telemetry, etc.)
- `modules.md` (optional) — Detailed per-module responsibility breakdown for larger packages

### Writing style
- Use clear, concise language
- Include code examples for common operations
- List public API symbols in tables with purpose descriptions
- Include requirements (Python version, dependencies)
- Link to related packages
- Reference source files with relative paths (e.g., `src/khulnasoft/ai/agents/agent.py`)

### News fragments
- Before opening a PR, run `uv run poe check-news-fragments`
- Add news fragments with `uv run poe changelog` or create files in `changes/<package>/`
- Format: `<timestamp>.<type>.md` where type is `internal`, `feature`, `fix`, `docs`, etc.

## Common documentation commands
- `uv run poe check-news-fragments` — verify news fragments are present
- `uv run poe changelog` — generate changelog from news fragments
