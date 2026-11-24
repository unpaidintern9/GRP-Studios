# GRP Studios — permanent agent operating contract

Read this file at the beginning of every task. Read [docs/MASTER_PLAN.md](docs/MASTER_PLAN.md) before implementation and the relevant skill in [.agents/skills](.agents/skills/). The master plan is the single source of truth for priorities, status, and approved decisions. Detailed creative briefs remain the source of truth for their particular deliverables. If they conflict, flag the conflict and reconcile it with the owner rather than silently changing direction.

## Immutable project constraints unless owner explicitly changes them
- Premium, professional cinematic production. Real human voices only. AI may assist imagery and effects but cannot fabricate brand identity, product data, testimonials or narration.
- Gold Light Emergence is selected for the first ident; the original cinematic concept is the benchmark. V01 flat 2D animation is rejected. Never lower the standard just to return a file.
- Official GRP source artwork and authentic approved product captures only. No redesign by default.
- MCP-first, modular plugins, shared reusable skills. A standalone website is optional and deferred; no unnecessary platform build.
- Completely separate from the Research Terminal. No shared repo, secrets, production APIs, database, ingestion, runners or deployments. Read-only provenance or approved exported assets is allowed.
- Public repository: no proprietary media, credentials, confidential data, private references or unreleased production files. Do not publish marketing assets automatically.
- Free-first, no paid generation, hosting, GPU rental or new cloud resources without explicit approval. Initial $100 planning target is not spending authorization.
- No fake completion, no fabricated test output, no generic quality gates unrelated to the change. Prefer focused tests, actual media review and evidence.

## Work protocol
1. Identify the active milestone and requested outcome. Read the relevant skill(s) and brief. Preserve prior owner decisions.
2. Make the smallest useful deliverable aligned with that milestone. If owner explicitly redirects, document the decision and update priority/status in MASTER_PLAN.md. Otherwise do not expand scope or start a new platform.
3. Implement and validate using focused checks. A plan, tool scaffold, render smoke test or generated storyboard is not an approved final production. Report actual results and blockers.
4. Update the master plan status/evidence and next step when meaningful progress occurs; do not mark complete until the milestone's exit criteria are satisfied. Keep historical rejections and approved decisions.
5. Commit scoped source/docs to this repository using normal safe Git practices; do not overwrite unrelated work. Keep sensitive artifacts outside public Git. Do not add automatic CI or deployment without approval.

## Skill routing
Use studio-director for orchestration; brand-asset-integrity for source fidelity; cinematic-art-direction for look/shot design; blender-production for 3D; motion-graphics for stings and transitions; video-post-production for editing/export; sonic-branding for sound; product-showcase for authentic product/data motion; campaign-production for commercials; ai-cinema for optional reference-guided studies; quality-and-compliance for acceptance; mcp-plugin-engineering for tooling and shared access.

All skills are repository-owned instructions, not proof that an engine or plugin is installed. Agents that do not discover .agents/skills automatically must read the corresponding SKILL.md explicitly. Keep the root contract and master plan up to date with approved changes.
