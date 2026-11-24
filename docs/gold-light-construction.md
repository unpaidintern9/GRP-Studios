# Gold Light V02 — precise construction blueprint

**Scope:** M3 look development, not final campaign or MCP expansion. The owner selected the black/gold flare concept. V01 flat reveal was rejected. Native source contours are candidates; do not call them original vectors or approve the look until inspected.

## Inputs and outputs
Read-only provenance: official GRP PNGs with exact Git blob IDs recorded in gold-light-ident.md. No Terminal runtime, repository dependency, production secrets, or asset publication. Copy the two original files into ignored private/brand/ using an authorized one-time export; the renderer has no network access. The preparation CLI verifies exact Git blob IDs, measures native-resolution masks, assigns materials to whole connected letter components, produces geometry.json, silhouette-review.svg and geometry-report.json privately. Stop on any hash, component count or round-trip mismatch.

## Physical construction
The shared full-lockup canvas is 1536x934. Map x/y pixel coordinates to the XY plane, camera on +Z; one common scale (6 scene units / 932 pixels) and center (744,453.5). All glyph placement is inherited from the source. Create separate filled curve objects: silver-monogram (G and P), gold-r, silver-wordmark, gold-descriptor. Maintain outer/hole winding; do not type text or invent a new mark. The mark extrudes .055 units and bevels .0045 units; text extrudes .018, bevel .0015. These are provisional review settings to protect thin serifs; inspect true 3D silhouettes before increasing depth. Two physical Principled metal materials, metallic 1, subtle stretched roughness, no emission on logo surfaces. Gold roughness .23-.32; silver .22-.30. Controlled soft key, warm rectangular strip, cool edge, broad fill. World almost black. AgX color management. No stock music or voice in this pass.

## Camera/lighting plan (1-based Blender frames, 24 fps)
| Review beat | Frame | Composition and action |
|---|---:|---|
| Gold-light opening | 18 | Near-black frame; original procedural narrow amber streak and white-gold core, no visible unrelated ribbons. |
| Macro R | 36 | 60mm physical camera, shallow focus, grazing warm strip light on the actual curved gold R. Inspect surface and bevel fidelity. |
| Monogram pullback | 76 | 48mm camera, G/P and R revealed, controlled reflections; no letter morphing. |
| Full-lockup alignment | 114 | 48mm centered camera and clean light, check all 25 glyphs and legibility. This is 3D alignment only, not the exact composited final hold. |

The full scene spans frames 1-120 (5s). Frame 106-120 remains still. Macro path and light energy are keyed; review actual movement and fix camera easing before rendering a complete draft. The 4th frame is a supplemental alignment check to the 3 primary creative review beats.

## Private execution on a trusted local or dedicated render machine
Prerequisites: existing GRP Studios checkout, Node 22, Blender 4.5.17 (or the M2 container), and authorized access to the exact source artwork. Do not use public GitHub Actions artifacts for unreleased GRP media.

From GRP Studios root, copy the two original PNG files from an authorized export, preserving bytes. For example, if the authenticated GitHub CLI is available (no secrets in commands):
 
    mkdir -p private/brand
    gh api repos/Gilmer-Research-Partners/Gilmer-Research-Terminal-/git/blobs/8c8b9cad7ad96ffae49f778b78d09f7ce29b82cb --jq .content | tr -d '\n' | base64 -d > private/brand/grp-mark-reverse.png
    gh api repos/Gilmer-Research-Partners/Gilmer-Research-Terminal-/git/blobs/84bba8beaba9ec557d05f5426e958233f00d3605 --jq .content | tr -d '\n' | base64 -d > private/brand/grp-full-reverse.png

The example uses GNU base64 syntax; on macOS replace base64 -d with base64 -D if needed. This is an explicit one-time copy, not an automatic link or dependency. Alternatively copy from an existing authorized checkout. Keep originals private and never commit them.

    node engine/brand/prepare_gold_light.mjs

Inspect private/gold-light-v02/silhouette-review.svg and geometry-report.json. Preparation uses exclusive writes to prevent accidental overwrite of a candidate. Review original art at matching scale and compare contours. To rerun, move the existing private candidate directory to a versioned private archive first.

    blender --background --factory-startup --disable-autoexec --python-exit-code 1 --python engine/motion/gold_light_v02.py -- --review

Or use the already proven M2 Docker recipe. From checkout root:

    docker build --platform linux/amd64 -f infrastructure/blender/Dockerfile -t grp-studios-blender:4.5.17 .
    docker run --rm --network none --cpus 4 --memory 8g --user "$(id -u):$(id -g)" \
      -v "$(pwd):/work:ro" -v "$(pwd)/private:/work/private:rw" -w /work \
      --entrypoint /opt/blender/blender grp-studios-blender:4.5.17 \
      --background --factory-startup --disable-autoexec --python-exit-code 1 \
      --python engine/motion/gold_light_v02.py -- --review

Outputs: private/gold-light-v02/lookdev/gold-light-v02-lookdev.blend, frame-018.png, frame-036.png, frame-076.png, frame-114.png and lookdev-receipt.json. Without --review, saves scene only. The lookdev directory must be new. Never upload these to a public artifact or repo. No full animation, GPU purchase, MCP remote tool, or Cloudflare provisioning in this pass.

## Review gate
Inspect frame 18 against the owner's chosen flare. Frame 36 must show visible real dimensional gold with correct R contour and believable brushed finish. Frame 76 must have legible silver G/P, exact shape and natural pullback composition; frame 114 must preserve all original wordmark proportions. Check evaluated geometry count and bounds; inspect narrow serif bevels, holes, edge jaggies, lighting and depth of field. Reject flat reveals and generic effects. Only after approval: tune curves/lights, composite the exact official full PNG for the final hold, render all 120 frames, review playback, and export the five-second 1080p H.264 draft. No synthetic narration. 4K master and R transition follow creative acceptance.

## Current evidence
Native-resolution contour analysis passed on both original repository PNGs (see evidence/m3-contour-study-2026-11-24.md). M2 proves Blender runtime on an isolated GitHub runner, not this new scene. This new Blender script has not been executed; scene, keyframes and visual quality remain NOT RUN until private render. The contour CLI's filesystem entry point still requires execution with original files.

## Private cloud asset staging
Both exact original PNGs are now present in dedicated private R2 at brand/originals/<git-blob>/<filename>. Source Git blob and readback SHA-256 verified. The upcoming render service should stage these into the existing private input layout without contacting the Terminal. No render has yet run from R2.
