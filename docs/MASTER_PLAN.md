# GRP Studios — canonical execution plan

Owner-directed baseline: November 24, 2026. This file governs sequencing and progress. Update in the same change as meaningful milestones or explicit scope decisions. Keep completed work backed by links, commits, tests or reviewed output. Status vocabulary: DONE, ACTIVE, NEXT, PLANNED, BLOCKED, REJECTED.

## Objective
An MCP-first modular creative studio usable by the team through AI clients, with professional original GRP cinematic branding, reproducible Blender/FFmpeg production, controlled assets, optional AI providers and no required website. Establish quality on a real flagship logo ident before expanding the commercial system.

## Decision log
- D01: Independent GRP Studios repository; no Terminal dependency. Public initially, transfer later.
- D02: Premium realistic animation, real human voices only; use AI selectively; no synthetic narration.
- D03: Gold Light Emergence selected opening direction. Gold flare, macro brushed gold R, physical silver G/P, real camera pullback, exact final lockup. V01 rejected because flat reveal did not match cinematic reference.
- D04: Blender is free-first shared 3D production engine. Existing launcher and Docker runtime proven in M2; see runtime evidence below.
- D05: MCP-first modular system preferred to dedicated website. Team-shared authenticated service eventually; local development first. No deployment or purchases implied.
- D06: Agent skills and canonical plan before MCP implementation. Root AGENTS.md governs each session.
- D07: Initial spending target $100 or less, no spending without authorization; no paid generations submitted.
- D08: Cloudflare-first, not Cloudflare-only. Workers MCP, D1 metadata, private R2, Queues; local/on-demand render compute separate. No required website, Vercel or Supabase. Owner authorized starting source implementation; provisioning and paid use remain separately controlled.

## Milestones in order

| ID | Status | Deliverable | Exit evidence |
|---|---|---|---|
| M0 | DONE | Project charter, creative baseline, independent repo | README, campaign and architecture docs; commits 9d26f609 and dc404ffc |
| M1 | DONE | Agent operating contract, specialist skills, canonical roadmap | AGENTS.md, this file and 12 SKILL.md files; structural validation |
| M2 | DONE | Prove shared Blender runtime | Verify pinned official version/availability; run check and real metallic smoke render; inspect output; record OS/version and evidence. No production claims from smoke. |
| M3 | ACTIVE | Brand asset preparation and Gold Light V02 | Private official source artwork; vector/contour validation; representative 3D stills matching original selected reference; actual 5s 1080p preview with 120 frames at 24 fps; human review. V01 remains REJECTED. |
| M4 | ACTIVE | Minimal local MCP core plus Blender plugin | Versioned tool contract, local stdio server, list capabilities/templates, approved asset references, bounded render request/status/cancel, tests using fake worker and one real smoke job. |
| M5 | PLANNED | Finish cinematic identity | Approved 4K ident, 1s R sweep, alpha variant, clean close, optional original sound and silent masters; verified playback and rights. |
| M6 | PLANNED | Video and sound plugins | Reproducible compositing/export, audio mix, validated media outputs; actual integration tests. |
| M7 | PLANNED | Product/motion/design plugins | Real approved UI and data; 15s teaser then 30s launch proof; reusable scene templates, quality review. |
| M8 | ACTIVE | Shared authenticated MCP and render worker | Authorized team access, isolation, quotas, private assets, status/cancellation, no arbitrary code; explicit infrastructure approval before provisioning. |
| M9 | PLANNED | Campaign and optional AI cinema integrations | 60s platform film, 75–90s Beyond the Noise human-narrated flagship, targeted variants; only approved spending and publication. |
| M10 | PLANNED | Extend plugin ecosystem | Independently versioned adapters (design, data motion, QA, distribution, providers) as needed; optional multi-brand support. Website only if requested/justified. |

M2 is complete; M3 is the immediate critical path. M4 source implementation may proceed in parallel if it does not displace the cinematic deliverable. Do not wait on the whole MCP ecosystem before making V02; do not build a website instead of the ident.

## Current known blockers and evidence
- Blender 4.5.17 container runtime and MCP smoke verified on GitHub-hosted Ubuntu 24.04. Blender is not installed in this chat runtime; use the proven isolated worker or an authorized local machine.
- Source PNGs identified in docs/gold-light-ident.md; exact approved vector or validated contours still required. Private source copies are not committed here.
- Original selected reference should be kept privately and compared during V02 review.
- V01 2D preview explicitly rejected (commit ccdf0732); no final 3D master.
- MCP 0.1.0 source added: local stdio, bounded local Blender smoke adapter and read-only remote machine-token preview, Cloudflare config and D1 schema draft. 18 core assertions passed and real SDK, install, local SQLite and Worker dry-run verified. Actual Blender smoke PASS. Real D1 service, OAuth/team deployment, lockfile commitment and approved asset references remain outstanding. No shared worker, bucket, plugin install or production deployment. See cloudflare-mcp.md.

### M2/M4 execution checkpoint
- Corrected Agents 0.34.0 exact SDK peer mismatch from server 2.3.1 to 2.4.0 and added matching client for real stdio tests (upstream tagged package.json: https://github.com/cloudflare/agents/blob/agents@0.34.0/packages/agents/package.json). Confirmed official Blender 4.5.17 release listing.
- Exact prior core/test source rerun: 18 assertions passed. Local Node 22 preview-auth test passed; local SQLite 5/5 migration tests passed against the committed migration SHA. No live D1 access.
- Added manually dispatched studio-only validation workflow, SDK handshake/render verifier and fail-closed preview guard. Run it on main with render_smoke enabled; review lockfile and public-safe smoke artifact. No automatic workflow or deployment. Workflow dispatch, actual SDK install, bundle, native render, real D1 and Cloudflare access still pending.
- The standard GitHub-hosted runner is intended for this public repo only; if transferred/private, verify quota before running. No shared Terminal infrastructure.
- Next: execute validation, review actual metallic smoke, prepare official brand geometry and cinematic V02. Do not enable remote rendering or provision resources until authorized Cloudflare access, OAuth and isolated worker controls exist.

### First real runtime validation — November 24, 2026
- Run [45437812409](https://github.com/unpaidintern9/GRP-Studios/actions/runs/45437812409), exact SHA 83ace9c9cb917968c12250b8a0739feaad98ae51: dependency-free tests, npm install, actual SDK stdio handshake/tool inventory and Wrangler dry-run all PASS. Blender container FAIL: direct download.blender.org archive request returned HTTP 403 (curl exit 22), before checksum/extraction; real render SKIPPED. Lockfile-only artifact 14943080249 uploaded; review/commit pending. Corrected Dockerfile to use Blender's official mirror.blender.org download service (https://www.blender.org/download/release/Blender4.5/blender-4.5.17-linux-x64.tar.xz/), same exact release and publisher SHA-256 manifest, bounded download retries. Mirror delivery and actual render are not yet verified. New manual run on the corrected main required; re-running the original SHA will not exercise the fix. No cloud deployment or resource provisioning.

### Successful runtime validation — November 24, 2026
- [M2 acceptance evidence](evidence/m2-runtime-2026-11-24.md): exact-SHA [run 45438147120](https://github.com/unpaidintern9/GRP-Studios/actions/runs/45438147120) completed successfully. Official mirror checksum, container build, actual MCP render and artifact upload PASS. Downloaded artifact hash matched metadata; metallic image visually inspected. This supersedes the earlier download failure.
- M2 DONE, M3 ACTIVE. No need to repeat the generic validation just to advance the ident. M4 stays ACTIVE until its remaining exit criteria are met.
- Next: private official logo input and contour validation, then real cinematic keyframes and V02 preview. Review and commit the candidate lockfile before deploying; do not mistake dry-run for live Cloudflare deployment.

### M3 construction checkpoint
- [Contour evidence](evidence/m3-contour-study-2026-11-24.md): exact source blobs, actual native-resolution JS trace and cleaned-mask round-trip validation. 25 glyph components; monogram classified-mask agreement 100%; 651 isolated small pixels removed. Per-group IoU silver-monogram 99.88%; gold-r 99.91%; silver-wordmark 99.64%; gold-descriptor 99.67%. Candidate only; not vector master or human approval.
- Private asset preparation code added; no public artwork or output. Next: private local inputs, Blender scene construction and cinematic keyframe review. M3 remains ACTIVE.

### M3 look-development implementation
- Native Blender scene builder and [construction blueprint](gold-light-construction.md) added. Separate original contours, filled/extruded metal curves, brushed gold/silver, keyed studio lighting, physical macro camera, original procedural gold flare. Four fixed private 1080p review frames (18/36/76/114); no 120-frame render until visual review.
- 2/2 focused synthetic contour tests passed with the exact trace source in a JavaScript runtime; fixtures cover counters and whole-glyph material classification. Native Blender script and private asset preparation CLI NOT RUN in this chat. Source bytes and production media must stay outside public Git; next action is private execution on the verified container or authorized local machine, not generic smoke re-runs or public upload.
- M3 remains ACTIVE. Final exact artwork compositing, animation playback, and owner approval pending.

### Cloudflare provisioning checkpoint
- Owner authorized dedicated infrastructure under existing plan. [Provisioning evidence](evidence/cloudflare-provisioning-2026-11-24.md): private R2, D1, two inactive queues created and read back; initial live D1 migration PASS, four tables verified, no foreign key violations. Both official PNGs copied to private R2 and checksums verified.
- M8 ACTIVE in parallel with M3. Worker and render container NOT DEPLOYED; OAuth, private job execution and actual cinematic render outstanding. No recurring compute or plan upgrade. Billing scope unavailable.
- Next: package verified renderer as an isolated, bounded service and produce a deployable MCP bundle; execute four private keyframes after secure render path is operational.

### Private cloud renderer implementation checkpoint
- Fixed review runner, dedicated source-only image recipe, singleton DO admission and private R2 execution candidate, separate Wrangler config and manual packaging workflow added. Rendering disabled; no deployed Worker, container, queued messages or billing changes. 17 fixed-contract assertions passed against the exact shared contract source in a JS runtime. Native Worker bundle, Docker image and remote exec lifecycle NOT RUN.
- Next: run source-only package validation, establish authorized image publication and deploy with rendering disabled, verify private operator access and cleanup, then authorize and execute one bounded four-keyframe job. See [private render service](private-render-service.md). Do not rerun generic M2 smoke or publish proprietary render artifacts.

### Render package acceptance — November 24
- [Exact-source build acceptance](evidence/render-package-acceptance-2026-11-24.md): both manual packaging runs passed. Wrangler 4.168.0, actual service image build, malformed-template rejection, Blender 4.5.17 LTS and five source test cases passed. Artifact hash verified; contains lockfile and build receipt only, no executable bundle or registry image.
- Frozen deploy/grp-studios-render-v1 branch points to 9c2bfcaa59817cd94519333306e9c1b9e37f4303. Cloudflare native repo connection attempt rejected with 404/8000008; GitHub App authorization for GRP-Studios required. No need to repeat package validation. No auto-deploy on main, no build token created, no compute started.
- Next: authorize the Git integration, deploy only the frozen branch with rendering disabled, then verify actual protected runtime and cost-controlled one-shot execution.

### Protected deployment checkpoint
- [Live deployment evidence](evidence/cloudflare-render-deployment-2026-11-24.md): exact validated source deployed as grp-studios; Cloudflare image digest pinned, R2 and DO bindings verified, render admission false, public URLs off.
- Default scheduling unexpectedly requested one idle instance; immediately set dedicated application's max_instances=0. Verified zero desired/maximum/actual/starting/active instances. **Do not redeploy existing frozen config without correcting scheduling**; it can recreate idle compute. Transient startup billing unverified.
- M3/M8 remain ACTIVE. Next: correct and verify on-demand lifecycle, configure protected machine operator access, verify cancellation/deadline/teardown, then obtain explicit bounded first-render approval and produce four real private keyframes.

### On-demand correction candidate
- New SQLite DO class and replacement durable_object scheduling application use the previously published digest-pinned Blender image. Old app remains separate and zero capacity. No public routes or HTTP render tools. Fixed authenticated-account queue operation and R2 permit, one-use admission, deadline, independent PID 1 timeout; STUDIO_QUEUE_RENDER_ENABLED=false. Preflight does not start compute.
- Next: deploy corrected candidate only; verify zero instances, disabled render admission and private preflight receipt before enabling any render. Actual runtime not yet verified.

### First live render and corrective release
- [Private render evidence](evidence/private-render-attempt-2026-11-24.md): on-demand deployment/preflight passed, first authorized job failed before container start with compound state guard. Permit revoked and zero instances verified; no output. Settings PATCH created a different version; possible image metadata loss not yet proven.
- User confirmed final deliverable is real 5s/120-frame MP4 (not four keyframes). Keyframes internal only; generated concept images references only. M3 ACTIVE.
- Corrective candidate retains explicit private permit and one-use gate, adds predicate-specific diagnostics and fresh v3 receipt/state, uses Wrangler deployment rather than a settings PATCH to enable the permit-gated queue. No permit or automatic render at deployment. Next verify new preflight and actual bounded execution, then deliver full animation with measured compute budget.

### Five-second clip production source
- Owner clarified the deliverable is full video. [Fixed clip production candidate](gold-light-clip-production.md): actual native frames 1–105 at 1080p, original exact hold at frames 106–120, H.264 export, full decode/metadata/frame-count checks, private editable scene and four internal QC frames. Source added; remote clip admission not wired or executed. Active v3 review still uses pinned previous image.
- Use measured native render timing to select a bounded production budget; no 2D substitution, no claims of final output until clip rendered and reviewed.

### Bounded native clip execution candidate
- Full motion divided into 15 seven-frame native 1080p segments and one verified assembly. Each segment persists immutable private R2 archive, full assembly independently checks all 105 native frame digests and creates 120-frame H.264 MP4 with exact original hold. One singleton container at a time; 10-minute per-step cap, explicit expiring total-budget permit, no automatic retry. Reuses existing queue and DO application, adds named clip image and queue producer for this finite plan. No compute launched by committing.
- 9 focused plan/admission checks passed in JS runtime; new Docker image, remote queue sequencing, native clip output NOT RUN. Existing v3 native review must complete first. Do not submit clip-start until owner authorized full production budget and build/preflight verified.

### First genuine native render — PASS
- [Live evidence](evidence/native-review-success-2026-11-24.md): four real Cycles 1080p frames and editable .blend delivered privately, checksum verified; duration 242.197s, permit revoked, zero active/starting instances. Native render execution proven; M3 remains ACTIVE, no 5s clip yet.
- Visual defects (macro stair-step edges and excessive flare) corrected in production candidate. Actual private source comparison preserves 25 components, each group IoU >=99.24%; revised camera and light parameters still need native visual review.
- Full clip source/checkpoint controller prepared. Build it using the frozen release branch, keep v3 evidence intact, require explicit full production budget before launching the finite plan. No claim of cinematic acceptance.

## Workstream boundaries
Skills and brand policy are reusable source. Plugins expose narrow versioned interfaces and independent dependencies. Asset/media library private; local renders outside public Git. A future worker runs trusted templates only with bounded resources and no Terminal access. Team sharing requires explicit auth and access policy. External services optional, never default paid fallback.

## Change-control and evidence
Before each task identify milestone and relevant skill. If owner redirects priorities, update this file with reason and effect; do not silently rewrite accepted decisions. Mark milestone DONE only when its stated exit evidence exists. Keep a short handoff (commit, artifacts, tests actually run, blockers, next action). Avoid redundant approvals for ordinary scoped code changes; require owner creative approval, spending permission and relevant rights/financial marketing clearance for final outputs. No recurring CI or deployments by default.

## Canonical supporting documents
- Creative: creative-direction.md, gold-light-ident.md, campaign-plan.md.
- Technical: studio-architecture.md, blender-team-setup.md.
- Production: production-roadmap.md (background estimates and campaign specifications; this plan takes precedence for sequence/status).
- Agent behavior: ../AGENTS.md and ../.agents/skills/.


### V03 creative correction
- Owner rejected actual V02 MP4 despite successful technical rendering. M3 remains ACTIVE. [Reference reconstruction](gold-light-v03-reference.md) pins the recovered GIF and rejected output, observed timing, color targets and failure modes. New private V03 native motion study uses same official artwork and existing renderer/MCP queue; independent singleton and R2 keys. Source only: no deployment, compute or visual acceptance verified. GPU work remains separate.

- Owner subsequently confirmed the exact cinematic storyboard (SHA-256 2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26); the stationary V03 candidate was superseded without rendering. Revised V03 uses oblique macro camera travel, controlled upright pullback, thicker metallic lettering, physically reflective floor, and centered opening flare. Retains existing exclusion of Earth/tagline pending explicit change. Actual visual and runtime acceptance remains open.


### Runpod GPU backend candidate
- Owner requested GPU integration; prepaid Runpod account connected. Added opt-in OptiX native renderer, strict GPU receipts, private batch transport and quote-based GPU planner. CPU production stays isolated. See [GPU integration](runpod-gpu.md). M8 remains ACTIVE: image build, benchmark, Cloudflare lifecycle and private job publication still require runtime validation. No GPU rented or production deployment in this change.

- Worker secret `RUNPOD_API_KEY` presence verified; read-only v2 credential preflight source added. No secret value retrieved. Deploy and invoke only after active CPU rendering completes; live key scope, GPU image and lifecycle are still unverified.


### V04 creative correction
- Owner rejected V03 native motion preview after viewing it. See [V04 lookdev](gold-light-v04-lookdev.md). Added native 1080p five-checkpoint scene with geometry-derived macro camera, measured 3D depth, reflective stage, navy atmosphere, and restrained glow. Contact sheet generated from the actual Blender outputs for visual comparison. Keep M3 ACTIVE until real visual and full motion acceptance. No paid GPU allocation or final render authorized by code change.

- V04 v1 native attempt failed before any frame at optional Principled anisotropy socket. Container stopped. Corrected socket lookup and added real Blender scene-construction build smoke using synthetic geometry. V04 v2 has a separate one-use admission and output prefix, preserving failed v1 evidence. Visual acceptance remains open.


### V05 cinematic repair
- Owner rejected V04 rendered PNG package as visually inadequate. V04 verified native depth but is not an animation. Read the existing production skills and Blender guidance; added [cinematic title finishing](../.agents/skills/cinematic-title-finishing/SKILL.md). [V05 motion proof](gold-light-v05-motion.md) changes reflection lighting, contour construction, wordmark exposure and continuous camera cadence, then verifies 120 genuine frames at 24fps. Source only until native build and render pass; M3 ACTIVE. Retain previous creative exclusions pending explicit owner change.


### V06 reference reconstruction
- V05 real native L40S OptiX 120-frame proof completed, three private artifacts verified and GPU terminated. Owner rejected its camera motion, depth and background. Twelve timestamp comparison confirms hard blue room horizon, rippled edges, weak macro choreography, missing traveling lights and closing environment. [V06 candidate](gold-light-v06-reconstruction.md) adds scene-specific contour raster parity and new stage/camera/lighting construction. Source only; do not mark M3 complete or re-rent GPU without authorization. Earth/tagline conflict with active brief requires owner resolution.

- Owner affirmed the full-reference closing treatment after the proposed restoration; active ident creative brief now includes native night-Earth-style horizon and separate SEE BEYOND THE NOISE. line. V06 native closing implementation plus reusable explicit OptiX GPU runner and hard deadline checks added. Build smoke and actual brand render pending; no new rental authorized by this creative change.


### V07 timed motion correction — November 24
- V06 real RTX 4090 native proof completed; private MP4/scene/receipt verified, no remaining pod. Owner: much better, still not matching motion. Exact GIF and video hashes independently matched; 120 decoded frames at 24 FPS, 5 seconds, silent H.264. At 2.0s the wordmark is prematurely visible; at 0.8–1.2s the gold face is cropped/dark and adjacent silver dominates. At 3.6–4.4s the horizon remains too small. M3 ACTIVE.
- V07 source isolates camera framing and reveal timing: contour-scale-derived face shots, target upper R bowl before pulling back to full R, unchanged original geometry and V06 closing. Hold wordmark at zero through frame 53 and monogram position through frame 50; restore exact lockup at 59. Keep old renderer/output untouched. Three pure Python beat tests passed locally; private comparison utility decoded all 120 V06 frames and generated twelve matching storyboard checkpoints. Largest adjacent-frame mean absolute RGB change at frame 13 (diagnostic, not aesthetic score). No Blender available in local chat; V07 runtime/render and creative review pending. No paid resources or workflow dispatch. Next: test actual motion when authorized; separately refine broad horizon, reflections and atmosphere without changing brand geometry.

### V08 seven-second primary ident — November 24
- Owner explicitly accepted 7s/168 native frames at 24 FPS, 1080p, silent; 5s version remains optional later. V07 camera corrections preserved, scene-specific animation retiming, later wordmark and longer closing hold, broader dark night-planet and clearer tagline. Current user requested one GPU execution and private R2 delivery; use conservative $2 ceiling from prior run as upper bound, no recurring spending. Verify native OptiX and exact 168 frames; preserve prior candidates. M3 remains ACTIVE until actual playback reviewed.

### V09e delivery and seven-second review gate — November 24
- Owner rejected V08's professional look; V09 rebuilt stage, metal lighting and continuous camera, preserving the authorized seven-second cadence. The single L40S OptiX job completed 168 native 1920x1080 frames at 24fps, silent H.264; final receipt and full R2 video and final editable scene independently hash-matched. Zero job pods remain. V09d silver P fill regression rejected; V09e restored the prior silver contour and passed sampled evaluated-mesh interior/exterior coverage for all four original groups, not a claim of perfect contour fidelity. No creative approval or new spending authority.
- The original private comparison tool only accepted five seconds. Extended it to explicit 5s/7s review modes with fixed reference-beat mapping and three closing hold checkpoints, strict stream validation and full decode. Four focused local unit tests passed. Usage: `python tools/compare-ident.py REFERENCE_GIF VERIFIED_MP4 PRIVATE_OUTPUT --seconds 7`. Actual V09e reference-aligned comparison remains pending access to the original GIF and MP4 in an authorized decoding environment. Preserve verified V09e and earlier private candidates; do not perform additional GPU runs on this authorization. Next creative work must be based on real media review, not unsupported scores. M3 ACTIVE.
