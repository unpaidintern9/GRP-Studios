# Cloudflare-first MCP foundation (0.1.0)

The owner approved Cloudflare-first infrastructure with external/local heavy rendering, not Cloudflare-only. No site is required. No cloud resource was provisioned by this change. This is a first slice, not a deployed team service.

## What exists
- Shared versioned registry; four read-only tools on a remote preview, seven local tools including one bounded Blender smoke job, status and cancel.
- Local stdio and Cloudflare Streamable HTTP adapters. Agents 0.34.0 declares exact MCP SDK 2.4.0 peer versions: server and test client now match. Zod is pinned to the release's development baseline 4.6.7. Installation remains unverified until the manual run.
- Only the fixed generic metallic smoke template is executable, locally. Gold Light V02 is explicitly blocked until actual geometry/render verification. No arbitrary input files, script execution, external generation, queue consumption or paid call tools.
- Remote preview requires a strong machine token, denies browser Origin requests, and exposes no mutation/render methods. It is not an OAuth endpoint or ChatGPT-connectable team service yet.
- D1 schema draft for workspace membership, private asset metadata, idempotent jobs and scoped outputs; no migrations applied. Cloudflare R2 and Queues are planned, not bound. No production resource is reused.

## Local verification
Requires Node 22+ and a package registry connection. From repo root:
```sh
npm test
npm install
npm run verify:stdio
npm run test:schema
npm run cf:check
```
Core tests use only Node built-ins and need no npm install. Generate and commit a reviewed package-lock before any deployment. The local job needs Blender 4.5.17 in PATH or BLENDER_BIN. It runs the trusted checked-in smoke script, one job at a time with 180-second render timeout; job status is process-local and not durable. Generic smoke output is not GRP footage. Verify official Blender version and image visually.
A local Codex MCP configuration can use node with an absolute path to mcp/stdio.mjs after installation. Use MCP Inspector to test discovery and invocations. No fake cloud or production claims.

## Execute the manual validation now
Open https://github.com/unpaidintern9/GRP-Studios/actions/workflows/studio-validate.yml, select Run workflow on main and leave render_smoke true. It runs only when manually requested, on a standard GitHub-hosted public-repository runner; no Terminal runner, cloud credentials, paid GPU, or deployments. It tests the core, preview auth, schema, real SDK handshake, Wrangler dry-run, then the checksum-verified Blender container via the MCP local adapter. The public-safe generic smoke PNG and package-lock candidate are downloadable from that run; inspect the render visually, then review and commit the lockfile. A successful smoke does not certify Gold Light V02. If workflow dispatch is unavailable, run the documented commands in an authorized developer environment.
 
## Cloudflare deployment preparation (manual, not executed)
Use authorized Wrangler login or a narrowly scoped deployment token in an approved secret store; never send credentials in chat or commit them. Confirm account and spending policy first. Do not reuse the Terminal's tokens, DBs, buckets, or runners. Current wrangler config intentionally has workers_dev and preview_urls disabled and no route. First verify the dry-run bundle, then configure an explicit approved hostname/route and set STUDIO_PREVIEW_TOKEN using Wrangler secrets (strong unique random value, at least 32 characters). Preview is machine-only; verify negative auth tests and confirm tools/list contains exactly four read-only tools before enabling any access. For real shared access implement user OAuth and authorization per MCP spec; never pass the machine token to team clients. Refer to https://developers.cloudflare.com/agents/model-context-protocol/guides/remote-mcp-server/ and https://developers.cloudflare.com/agents/model-context-protocol/apis/handler-api/.

## Proposed dedicated resource names (not created)
grp-studios-mcp; grp-studios-db (D1); grp-studios-media (private R2); grp-studios-render-queue; grp-studios-render-dlq. After approval use Wrangler resource commands in a dedicated scope, add actual binding IDs and queue configuration, then test local migrations and access boundaries. Do not enable producers/consumers or accept remote render jobs before isolated worker, limits, claim/lease and cancellation semantics, private media security, per-user authorization, idempotency and budget enforcement are tested. Container CPU previews are optional; heavy Blender rendering on approved dedicated GPU/local hardware. No always-on GPU.

## Verification limits
The previous 18 registry/job assertions were re-executed from the exact committed core/test sources. New preview authorization tests passed in Node 22; five migration tests passed against the exact migration bytes in local SQLite. Actual dependency install, SDK transport, Wrangler dry-run, D1 runtime, Docker/Blender, OAuth and live deployment are still NOT RUN. Local npm lookup fails with DNS EAI_AGAIN; Blender and Docker absent. The manual workflow is the next execution step, not a completed run.

## First real validation result — November 24, 2026
Run [45437812409](https://github.com/unpaidintern9/GRP-Studios/actions/runs/45437812409), exact SHA 83ace9c9cb917968c12250b8a0739feaad98ae51: dependency-free tests, npm install, actual SDK stdio handshake/tool inventory and Wrangler dry-run all PASS. Blender container FAIL: direct download.blender.org archive request returned HTTP 403 (curl exit 22), before checksum/extraction; real render SKIPPED. Lockfile-only artifact 14943080249 uploaded; review/commit pending. Corrected Dockerfile to use Blender's official mirror.blender.org download service (https://www.blender.org/download/release/Blender4.5/blender-4.5.17-linux-x64.tar.xz/), same exact release and publisher SHA-256 manifest, bounded download retries. Mirror delivery and actual render are not yet verified. New manual run on the corrected main required; re-running the original SHA will not exercise the fix. No cloud deployment or resource provisioning.

## Successful runtime validation — November 24, 2026
See [M2 acceptance evidence](evidence/m2-runtime-2026-11-24.md). Run 45438147120 passed dependency installation, SDK stdio handshake, Worker dry-run, Docker build and real Blender smoke. Downloaded artifact hash and visual inspection confirmed. Real D1, OAuth, live deployment and lockfile commitment remain pending. This result supersedes the earlier failed download.

## Authorized provisioning checkpoint
See [live resource evidence](evidence/cloudflare-provisioning-2026-11-24.md). R2, D1 and both queues now exist; live migration passed and original logos are verified in private R2. Earlier proposed/not-created labels are historical. Worker, container, authenticated team access and queue bindings are still pending. No public route or active consumer.

## Private render service candidate
See [private render service](private-render-service.md). A separate Wrangler config binds only the dedicated R2 and singleton container. Render admission disabled, routes disabled, no queues attached. Manual source-only packaging workflow must pass before deployment. Team OAuth remains outstanding.

## Render package validation passed
Both exact-source GitHub builds passed. See [acceptance evidence](evidence/render-package-acceptance-2026-11-24.md). Cloudflare Git integration authorization is the remaining image publication/deployment prerequisite; resource API access alone does not grant that connection. No running container.
