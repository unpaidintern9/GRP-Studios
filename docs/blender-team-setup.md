# Shared Blender production environment

## Goal
Blender is the GRP Studios rendering engine, not an individual employee's workstation dependency. Share the source, scene-building scripts, version and rendering commands through this repository. Do not vendor Blender binaries into Git. Blender is free software; obtain its executable directly from the Blender Foundation.

Pinned baseline: Blender 4.5.17 LTS (official release archive https://download.blender.org/release/Blender4.5/). The version is a shared reproducibility baseline, not a guarantee of identical GPU output. Keep upgrades deliberate.

## Desktop use (Mac, Windows, Linux)
Install the matching official Blender 4.5.17 build. Clone this repository; Python 3.10+ is needed for the launcher. Run from the checkout root:

    python scripts/studio_render.py --check
    python scripts/studio_render.py --smoke
    python scripts/studio_render.py --scene private/scenes/gold-light-v02.blend --output renders/gold-light-v02/frame_

If Blender is not on PATH, set BLENDER_BIN to its full executable path or pass --blender explicitly. The launcher also checks the usual macOS and Windows install locations. On Windows, use py -3 instead of python if needed. Install Python from its official source.

The smoke test renders a generic metallic gold torus with physical lighting and a camera, not the GRP logo. Its only purpose is proving the shared rendering environment. It does not qualify as Gold Light V02 or any approved brand asset.

## Headless worker (no desktop installation needed)
A Linux x86-64 Docker build is provided. Docker or an equivalent container runtime is required only on the machine doing the rendering. Build and run from checkout root:

    docker build --platform linux/amd64 -f infrastructure/blender/Dockerfile -t grp-studios-blender:4.5.17 .
    docker run --rm --platform linux/amd64 -v "$(pwd):/work" grp-studios-blender:4.5.17 --check
    docker run --rm --platform linux/amd64 -v "$(pwd):/work" grp-studios-blender:4.5.17 --smoke
    docker run --rm --platform linux/amd64 -v "$(pwd):/work" grp-studios-blender:4.5.17 --scene private/scenes/gold-light-v02.blend --output renders/gold-light-v02/frame_

These commands use POSIX shells; PowerShell users can substitute ${PWD} for the absolute host path in the bind mount. The supplied container is CPU-first, not GPU-enabled. Apple Silicon should prefer native Blender rather than emulating an x86 CPU renderer. On Linux, add --user "$(id -u):$(id -g)" to docker run if host file ownership matters. Only render trusted scenes and scripts; do not expose this unrestricted local launcher as an unauthenticated remote API.

The Dockerfile fetches the versioned Blender archive and its published SHA-256 list and verifies the archive before extraction. No scheduled jobs, runner, cloud service, or Docker image registry is provisioned by this commit.

## Team-wide browser access (next milestone, not deployed)
A GitHub repository is not a hosted rendering service. To let every team member work from a browser without installing Blender, deploy one independent GRP Studios web interface and a dedicated Blender render worker. Keep the worker entirely separate from the Research Terminal.

- Studio UI: authenticated project library, versioned scene templates, preview, render requests, progress, review, export.
- Queue: explicit manual render jobs with bounded concurrency, time, disk and sample limits; cancel/retry; enforce per-user permissions.
- Blender worker: isolated CPU/GPU execution, read-only inputs, per-job scratch space, approved templates only, no arbitrary user Python, no Terminal access.
- Storage: private asset store (local initially; dedicated private R2 later if approved) with signed download links, versioning and retention.
- Review: approved versions and immutable output hashes. Do not expose private scenes or source assets in public Git.

Start on one dedicated machine the team can use; add cloud GPU only if justified and approved. A hosted service still requires compute and possibly storage costs; Blender itself is free. No auto-deploy or paid resources without approval.

## Quality and collaboration
Maintain the selected Gold Light Emergence visual direction, exact official geometry and original wordmark, real 3D lighting and camera motion. V01 flat animation remains rejected. Keep proprietary logos, reference clips, .blend working projects and rendered media under ignored private/ or renders/ directories until cleared. Use scene-building scripts and public-safe placeholder fixtures in Git. Native Blender scene files for final GRP ident have not yet been built.

## Verification
Run the check and smoke commands on the target machine before using the worker for a production job. Verify Blender reports 4.5.17, the smoke PNG is non-empty and visually shows metallic highlights, and a complete render sequence has expected frame count. This setup is scaffolding, not an acceptance receipt for the final GRP animation. Keep a record of runtime/OS, version and job outcome.
