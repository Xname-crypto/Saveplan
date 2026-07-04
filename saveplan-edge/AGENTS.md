# saveplan-edge

Fullstack EdgeSpark project using npm workspaces.

## Structure

- `server/` — Hono API on Cloudflare Workers (see server/AGENTS.md)
- `web/` — React SPA via Vite (see web/AGENTS.md)
- `edgespark.toml` — Project configuration
- `package.json` — Root workspace (no deps, just wires server + web)

## Commands

Always run from the project root:

```bash
npm install          # install all dependencies
edgespark deploy        # build + deploy to platform
```

Do not run `npm install` from inside `server/` or `web/` — use the root.
