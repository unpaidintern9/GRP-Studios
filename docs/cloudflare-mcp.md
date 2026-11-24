# Cloudflare-first MCP foundation (0.1.0)

The owner approved Cloudflare-first infrastructure with external/local heavy rendering, not Cloudflare-only. No site is required. No cloud resource was provisioned by this change. This is a first slice, not a deployed team service.

## What exists
- Shared versioned registry; four read-only tools on a remote preview, seven local tools including one bounded Blender smoke job, status and cancel.
- Local stdio and Cloudflare Streamable HTTP adapters based on MCP SDK v2 / Cloudflare Agents SDK documentation.
- Only the fixed generic metallic smoke template is executable, locally. Gold Light V02 is explicitly blocked until actual geometry/render verification. No arbitrary input files, script execution, external generation, queue consumption or paid call tools.
- Remote preview requires a strong machine token, denies browser Origin requests, and exposes no mutation/render methods. It is not an OAuth endpoint or ChatGPT-connectable team service yet.
- D1 schema draft for workspace membership, private asset metadata, idempotent jobs and scoped outputs; no migrations applied. Cloudflare R2 and Queues are planned, not bound. No production resource is reused.

## Local verification
Requires Node 22+ and a package registry connection. From repo root:
```sh
npm test
npm install
npm run mcp:local
npm run cf:check
```
Core tests use only Node built-ins and need no npm install. Generate and commit a reviewed package-lock before any deployment. The local job needs Blender 4.5.17 in PATH or BLENDER_BIN. It runs the trusted checked-in smoke script, one job at a time with 180-second render timeout; job status is process-local and not durable. Generic smoke output is not GRP footage. Verify official Blender version and image visually.
A local Codex MCP configuration can use node with an absolute path to mcp/stdio.mjs after installation. Use MCP Inspector to test discovery and invocations. No fake cloud or production claims.

## Cloudflare deployment preparation (manual, not executed)
Use authorized Wrangler login or a narrowly scoped deployment token in an approved secret store; never send credentials in chat or commit them. Confirm account and spending policy first. Do not reuse the Terminal's tokens, DBs, buckets, or runners. Current wrangler config intentionally has workers_dev and preview_urls disabled and no route. First verify the dry-run bundle, then configure an explicit approved hostname/route and set STUDIO_PREVIEW_TOKEN using Wrangler secrets (strong unique random value, at least 32 characters). Preview is machine-only; verify negative auth tests and confirm tools/list contains exactly four read-only tools before enabling any access. For real shared access implement user OAuth and authorization per MCP spec; never pass the machine token to team clients. Refer to https://developers.cloudflare.com/agents/model-context-protocol/guides/remote-mcp-server/ and https://developers.cloudflare.com/agents/model-context-protocol/apis/handler-api/.

## Proposed dedicated resource names (not created)
grp-studios-mcp; grp-studios-db (D1); grp-studios-media (private R2); grp-studios-render-queue; grp-studios-render-dlq. After approval use Wrangler resource commands in a dedicated scope, add actual binding IDs and queue configuration, then test local migrations and access boundaries. Do not enable producers/consumers or accept remote render jobs before isolated worker, limits, claim/lease and cancellation semantics, private media security, per-user authorization, idempotency and budget enforcement are tested. Container CPU previews are optional; heavy Blender rendering on approved dedicated GPU/local hardware. No always-on GPU.

## Verification limits
Dependency install, SDK transports, Wrangler dry-run, SQLite migration execution, real Blender render and remote deployment must be tested in the target environment. This change validates the same registry and job manager source in a JavaScript runtime with a fake worker; no real Blender execution is claimed.
