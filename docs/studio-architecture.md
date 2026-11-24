# Standalone GRP Studios architecture

## Boundary (non-negotiable)

GRP Studios is its own repository and production environment, not a submodule or feature branch of the Gilmer Research Terminal. No Terminal source dependency, database access, production API access, shared secrets, production runners, scheduled CI, automated application deployment or ingestion coupling.

The studio receives only separately approved exports supplied by a human: official logo vectors, brand guidelines, approved screenshots, approved screen recordings, and scrubbed sample data if needed. Copy assets into a private working area; no live integration. Product footage may be captured manually or with a separate, authorized screen-recording workflow; use a local/static capture set by default.

Initially public under the owner's personal account, transferable later. Public repository contains safe source code, documentation, and cleared placeholder assets only. No proprietary vectors, unreleased ads, confidential business data, raw footage, customer data, credentials or restricted license materials. Public visibility does not confer an open-source license. Changing visibility later cannot undo prior public copies.

## Proposed components

| Component | Responsibility | Candidate implementation |
|---|---|---|
| GRP Motion Engine | Brand geometry, cinematic logo reveal, materials, lighting, camera paths, transparent transitions | Blender + Python; optional Cinema 4D if licensed |
| Product Showcase Engine | Real approved interface captures, animated device scenes, exact financial chart motion, kinetic typography | Three.js, React, Remotion where licensing permits |
| GRP Studio | Standalone scene assembly, preview, customize, manage licensed footage and audio, export | Local-first interface later; no hosted app needed for MVP |
| Cinematic Asset Library | Brand tokens, scene presets, lower thirds, templates, audio, camera and grading references | Local/private manifest-driven asset store |
| Render Engine | Deterministic render settings, compositing, multi-format exports, validation | Blender, FFmpeg, Remotion if appropriate, DaVinci Resolve/Fusion |
| Review workflow | Visual review, provenance, permissions, data verification, deliverable approval | Local review sheets, versioned manifests, manual approval |

Start with a reusable rendering toolkit and a finished teaser, not a large application. Add a local UI once a real production demonstrates the workflow. Do not provision a database or Vercel project for the initial phases.

## Production technology

- Actual people / speaking scenes: filmed or commercially licensed live action; real human voice only.
- Difficult environmental or atmospheric shots: selective AI footage, e.g. Higgsfield Cinema Studio, subject to rights, continuity and frame-by-frame quality review.
- Cities / industrial locations: licensed stock or original footage. Pexels/Pixabay are candidates; verify each clip's usage rights, model/property releases and editorial restrictions.
- Motion and logo: Blender/Python first; precise geometry, controlled animation and physically plausible lighting.
- Product and financial graphics: exact, approved screenshots or screen recordings and data; Playwright only for authorized capture workflows, no production credentials in studio; Remotion/Three.js for repeatable scenes, subject to commercial licensing.
- Editing and finishing: DaVinci Resolve, Fusion, optionally After Effects if licensed; color management, controlled grading, professional mix.
- Audio: original/licensed music and sound effects, real narration, documented rights.
- AI may assist with ideation, non-human environmental imagery, atmospheric elements, difficult camera work, rotoscoping, compositing and cleanup. Never generate the official logo, fabricate product UI or synthesize the narration.

## Infrastructure

| Area | Initial plan | Later option |
|---|---|---|
| Git | Separate repository, manual changes | Transfer ownership when requested |
| Media | Local private work directory outside Git | Dedicated private object store, proposed R2 bucket grp-studios-media |
| Rendering | Local Mac or dedicated standalone machine, manual runs | Dedicated cloud/GPU compute only if justified and approved |
| CI | No GitHub Actions initially | Manual/on-demand studio-only checks; no shared runners |
| Deployments | None | Separate preview app only if needed |
| Database | None | Local file metadata first; consider a studio-specific store only if needed |
| Credentials | None committed, local environment or secret store if needed | Studio-specific least-privilege tokens |

No paid plan, bucket, compute or account is being provisioned by this document. Avoid unnecessary storage of large media in Git. Ignore local renders and raw media; use external backups, manifests, hashes and versioning for deliverables.

## Suggested future directory structure

    docs/
    brand/                   # public-safe placeholders and instructions only
    engine/motion/           # Blender scripts, materials, camera and lighting
    engine/product/          # approved capture-based scenes and graphics
    engine/render/           # FFmpeg and reproducible export tooling
    templates/               # reusable scene, title and transition definitions
    campaigns/               # approved public-safe project definitions
    studio/                  # optional local-first visual editor, later phase
    tests/                   # local validation and deterministic smoke tests

Private raw media, approved original brand files, paid stock, generated footage, voice tracks, working renders and masters live outside the public repository. Use portable asset IDs or relative paths; never hardcode ownership, private paths or credentials. Preserve source/version information, rights, hashes and review status in appropriate private manifests.
