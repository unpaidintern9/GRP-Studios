# Private Gold Light review service — deployment candidate

M3 remains the critical path. This candidate provides a single fixed operator job, not a general creative execution API or team OAuth service. Uses the existing verified Blender 4.5.17 distribution. The separate default-scheduling container configuration caps instances at one and starts only on explicit MCP invocation; no cron or Queue producer/consumer. A render is not authorized by resource provisioning alone. STUDIO_RENDER_ENABLED is false and public routes/previews are disabled by default.

## Flow
1. Authenticated machine-only MCP (existing preview guard) exposes status; start/cancel tools only when explicitly enabled.
2. Singleton Durable Object persists one-use admission and a 10-minute safety alarm. No automatic retries or arbitrary commands. Fetch exactly two versioned private R2 inputs, verify sizes and SHA-256, pass bounded JSON through container stdin. No credentials or internet inside container.
3. Fixed runner verifies Git blob and SHA-256 again, creates private ephemeral directory, invokes the committed trace and actual Blender lookdev scripts with bounded subprocesses. Accepts exactly frames 18,36,76,114, 1920x1080, correct receipt and per-image digests. Packages only four PNGs, the private editable scene and receipt.
4. Durable Object verifies bounded ZIP delivery and R2 readback, writes to an immutable review key, destroys container and reports outcome. Cancel and alarm destroy the container. Actual cancellation/cleanup behavior still requires real integration tests.
5. A human with R2 permission retrieves the private archive through authenticated Cloudflare API. No signed public URL or public GitHub artifact of brand inputs/results. D1 and queues remain provisioned but unused for this single operator job; team auth, role-based jobs and queue processing are later milestones.

## Validation and deployment
Manual workflow .github/workflows/studio-render-package.yml compiles the Worker without deployment and builds the source-only service image on GitHub-hosted infrastructure; no cloud secrets or brand assets. It is not a render job. The candidate must be tested before live deployment. Verify Wrangler supports the documented default container scheduling configuration and native Durable Object exec API (https://developers.cloudflare.com/containers/api/durable-object-container/). Docker build context is allowlisted and excludes private/ and media. Existing CLI Dockerfile stays unchanged.

After build validation, deploy via an authorized, dedicated Wrangler environment with:

    npx wrangler deploy --config infrastructure/cloudflare/wrangler.render.jsonc

Wrangler must be able to build and publish the image to Cloudflare Registry. Do not put token in Git or chat. The existing Cloudflare MCP can manage resources but does not itself build/push Docker images. Use a dedicated Cloudflare Workers Builds connection or a manual GitHub deployment with authorized secret if needed. Do not connect auto-deploy on main; avoid broad tokens. Confirm existing name, account, binding and application state before deploying. No route or secret is configured by this commit. Preserve fail-closed mode until auth, private invocation, cost bounds and cleanup are verified. Only then obtain explicit permission for a one-shot CPU render; no GPU, no recurring compute. No production quality claim until actual frames reviewed.

## Known limitations
Candidate source only: Worker bundle, SDK registration, native Cloudflare container exec lifecycle, timeout/cancel and R2 output path are not yet exercised. Local contract tests check input shape, allowlist, receipt and single-use state. Actual brand render remains outstanding. Team OAuth, D1 job integration, and queue integration remain deferred; do not treat this machine-token endpoint as a team service.

## Build acceptance and exact release branch
See [verified build evidence](evidence/render-package-acceptance-2026-11-24.md). Both package workflows passed; actual deployable image and Worker bundle were not exported. Native Cloudflare Git connection requires separate GitHub App authorization. Use the frozen deploy/grp-studios-render-v1 branch and the recorded deploy command, not main. Runtime and rendering remain unverified.

## Live deployment and safety hold
[Live evidence](evidence/cloudflare-render-deployment-2026-11-24.md). Worker and image deployed successfully under the actual dashboard name grp-studios. The earlier assumption that default scheduling would start only on invocation was false: deployment requested one idle instance. Live app was reduced to zero capacity and independently verified stopped. Render admission remains false; no operator secret or public route. Before redeploying, fix and verify the lifecycle configuration, since the frozen release still requests max_instances=1. No private render has executed.
