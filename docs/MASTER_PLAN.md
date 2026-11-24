# GRP Studios — canonical execution plan

Owner-directed baseline: November 24, 2026. This file governs sequencing and progress. Update in the same change as meaningful milestones or explicit scope decisions. Keep completed work backed by links, commits, tests or reviewed output. Status vocabulary: DONE, ACTIVE, NEXT, PLANNED, BLOCKED, REJECTED.

## Objective
An MCP-first modular creative studio usable by the team through AI clients, with professional original GRP cinematic branding, reproducible Blender/FFmpeg production, controlled assets, optional AI providers and no required website. Establish quality on a real flagship logo ident before expanding the commercial system.

## Decision log
- D01: Independent GRP Studios repository; no Terminal dependency. Public initially, transfer later.
- D02: Premium realistic animation, real human voices only; use AI selectively; no synthetic narration.
- D03: Gold Light Emergence selected opening direction. Gold flare, macro brushed gold R, physical silver G/P, real camera pullback, exact final lockup. V01 rejected because flat reveal did not match cinematic reference.
- D04: Blender is free-first shared 3D production engine. Existing launcher and Docker scaffolding committed; execution not yet proven.
- D05: MCP-first modular system preferred to dedicated website. Team-shared authenticated service eventually; local development first. No deployment or purchases implied.
- D06: Agent skills and canonical plan before MCP implementation. Root AGENTS.md governs each session.
- D07: Initial spending target $100 or less, no spending without authorization; no paid generations submitted.
- D08: Cloudflare-first, not Cloudflare-only. Workers MCP, D1 metadata, private R2, Queues; local/on-demand render compute separate. No required website, Vercel or Supabase. Owner authorized starting source implementation; provisioning and paid use remain separately controlled.

## Milestones in order

| ID | Status | Deliverable | Exit evidence |
|---|---|---|---|
| M0 | DONE | Project charter, creative baseline, independent repo | README, campaign and architecture docs; commits 9d26f609 and dc404ffc |
| M1 | DONE | Agent operating contract, specialist skills, canonical roadmap | AGENTS.md, this file and 12 SKILL.md files; structural validation |
| M2 | ACTIVE | Prove shared Blender runtime | Verify pinned official version/availability; run check and real metallic smoke render; inspect output; record OS/version and evidence. No production claims from smoke. |
| M3 | NEXT | Brand asset preparation and Gold Light V02 | Private official source artwork; vector/contour validation; representative 3D stills matching original selected reference; actual 5s 1080p preview with 120 frames at 24 fps; human review. V01 remains REJECTED. |
| M4 | ACTIVE | Minimal local MCP core plus Blender plugin | Versioned tool contract, local stdio server, list capabilities/templates, approved asset references, bounded render request/status/cancel, tests using fake worker and one real smoke job. |
| M5 | PLANNED | Finish cinematic identity | Approved 4K ident, 1s R sweep, alpha variant, clean close, optional original sound and silent masters; verified playback and rights. |
| M6 | PLANNED | Video and sound plugins | Reproducible compositing/export, audio mix, validated media outputs; actual integration tests. |
| M7 | PLANNED | Product/motion/design plugins | Real approved UI and data; 15s teaser then 30s launch proof; reusable scene templates, quality review. |
| M8 | PLANNED | Shared authenticated MCP and render worker | Authorized team access, isolation, quotas, private assets, status/cancellation, no arbitrary code; explicit infrastructure approval before provisioning. |
| M9 | PLANNED | Campaign and optional AI cinema integrations | 60s platform film, 75–90s Beyond the Noise human-narrated flagship, targeted variants; only approved spending and publication. |
| M10 | PLANNED | Extend plugin ecosystem | Independently versioned adapters (design, data motion, QA, distribution, providers) as needed; optional multi-brand support. Website only if requested/justified. |

M2 and M3 are the immediate critical path. M4 source implementation may proceed in parallel if it does not displace the cinematic deliverable. Do not wait on the whole MCP ecosystem before making V02; do not build a website instead of the ident.

## Current known blockers and evidence
- Blender launcher and container files exist, but runtime/build verification is not recorded. Blender 4.5.17 is listed in the official release archive https://download.blender.org/release/Blender4.5/; executable absent in this chat runtime.
- Source PNGs identified in docs/gold-light-ident.md; exact approved vector or validated contours still required. Private source copies are not committed here.
- Original selected reference should be kept privately and compared during V02 review.
- V01 2D preview explicitly rejected (commit ccdf0732); no final 3D master.
- MCP 0.1.0 source added: local stdio, bounded local Blender smoke adapter and read-only remote machine-token preview, Cloudflare config and D1 schema draft. 18 core assertions passed in a JavaScript runtime with fake adapter. Dependency install, actual SDK transport, migration, worker bundle, actual Blender runtime and OAuth/team deployment NOT RUN (no network/package registry or Blender access here). No shared worker, bucket, plugin install or production deployment. See cloudflare-mcp.md.

### M2/M4 execution checkpoint
- Corrected Agents 0.34.0 exact SDK peer mismatch from server 2.3.1 to 2.4.0 and added matching client for real stdio tests (upstream tagged package.json: https://github.com/cloudflare/agents/blob/agents@0.34.0/packages/agents/package.json). Confirmed official Blender 4.5.17 release listing.
- Exact prior core/test source rerun: 18 assertions passed. Local Node 22 preview-auth test passed; local SQLite 5/5 migration tests passed against the committed migration SHA. No live D1 access.
- Added manually dispatched studio-only validation workflow, SDK handshake/render verifier and fail-closed preview guard. Run it on main with render_smoke enabled; review lockfile and public-safe smoke artifact. No automatic workflow or deployment. Workflow dispatch, actual SDK install, bundle, native render, real D1 and Cloudflare access still pending.
- The standard GitHub-hosted runner is intended for this public repo only; if transferred/private, verify quota before running. No shared Terminal infrastructure.
- Next: execute validation, review actual metallic smoke, prepare official brand geometry and cinematic V02. Do not enable remote rendering or provision resources until authorized Cloudflare access, OAuth and isolated worker controls exist.

### First real runtime validation — November 24, 2026
- Run [45437812409](https://github.com/unpaidintern9/GRP-Studios/actions/runs/45437812409), exact SHA 83ace9c9cb917968c12250b8a0739feaad98ae51: dependency-free tests, npm install, actual SDK stdio handshake/tool inventory and Wrangler dry-run all PASS. Blender container FAIL: direct download.blender.org archive request returned HTTP 403 (curl exit 22), before checksum/extraction; real render SKIPPED. Lockfile-only artifact 14943080249 uploaded; review/commit pending. Corrected Dockerfile to use Blender's official mirror.blender.org download service (https://www.blender.org/download/release/Blender4.5/blender-4.5.17-linux-x64.tar.xz/), same exact release and publisher SHA-256 manifest, bounded download retries. Mirror delivery and actual render are not yet verified. New manual run on the corrected main required; re-running the original SHA will not exercise the fix. No cloud deployment or resource provisioning.

## Workstream boundaries
Skills and brand policy are reusable source. Plugins expose narrow versioned interfaces and independent dependencies. Asset/media library private; local renders outside public Git. A future worker runs trusted templates only with bounded resources and no Terminal access. Team sharing requires explicit auth and access policy. External services optional, never default paid fallback.

## Change-control and evidence
Before each task identify milestone and relevant skill. If owner redirects priorities, update this file with reason and effect; do not silently rewrite accepted decisions. Mark milestone DONE only when its stated exit evidence exists. Keep a short handoff (commit, artifacts, tests actually run, blockers, next action). Avoid redundant approvals for ordinary scoped code changes; require owner creative approval, spending permission and relevant rights/financial marketing clearance for final outputs. No recurring CI or deployments by default.

## Canonical supporting documents
- Creative: creative-direction.md, gold-light-ident.md, campaign-plan.md.
- Technical: studio-architecture.md, blender-team-setup.md.
- Production: production-roadmap.md (background estimates and campaign specifications; this plan takes precedence for sequence/status).
- Agent behavior: ../AGENTS.md and ../.agents/skills/.
