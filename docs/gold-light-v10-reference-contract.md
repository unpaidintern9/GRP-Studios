# V10 reference-locked native production contract

Status: V09E technically delivered, creatively REJECTED by owner. V10 source work only; no new GPU allocation or creative acceptance.

## Immutable inputs

- Exact owner motion reference SHA-256 `2c407f2474f0173f75ce19689b7741f4ab397012571799132da79ac839c16d26`, 357 x 357, 12 GIF frames at 400 ms each. The original GIF is private; use the owner-uploaded asset, not the separately labeled storyboard or another GIF. Do not commit reference pixels, proprietary artwork, or media to Git.
- V09E verified MP4 SHA-256 `d4f18f9111c8c3ba23a184678de863f155577cd79519a440fa96422a1df0e5e0`. Rejected creative baseline, not a visual target.
- Verified V09E editable source blend SHA-256 `86ff34d0a65c2bac53317b0539537dc9dfea0163504d207fadc1ea3801e8ee00`. Safe geometry baseline only. Preserve restored silver geometry and verified original-art parity. Do not reuse rejected V09d fill.
- Retain last owner-authorized output format, 1920 x 1080, 24 FPS, exactly 168 native frames, seven seconds, silent H.264. The square GIF is a 4.8-second discrete look reference, not continuous 24fps motion. Uniformly retime its 12 beats to seven seconds; preserve proportions and extend the scene laterally rather than stretching the logo. Exact in-between motion is a creative reconstruction, not recoverable from the GIF.

## Reference-led shot contract

Frame numbering is one-based. The proposed 16:9 framing preserves vertical placement and the square reference composition in a centered 1080 x 1080 safe region; side extensions should continue environment and stage naturally. Macro shots may exceed this region. Tune camera through actual rendered reference pairs, not a fixed guessed zoom.

| Panel | GIF time | Target frame | Native shot requirement |
|---|---:|---:|---|
| 1 | 0.0s | 1 | Concentrated white-gold ignition, wide soft optical halo and narrow streak in black. |
| 2 | 0.4s | 15 | Diagonal silver bevel macro; camera grazes the silver surface, a hot specular highlight travels along the edge. Not a gold R close-up. |
| 3 | 0.8s | 29 | Gold R bowl and flowing leg visibly sculptural; realistic gold highlight and restrained shallow depth of field. |
| 4 | 1.2s | 43 | R reads as a complete flowing shape; silver neighboring strokes in frame; stable curve edges. |
| 5 | 1.6s | 57 | Full three-quarter GRP monogram and reflective stage already visible. No cropping. |
| 6 | 2.0s | 71 | Smaller full monogram, moving warm floor reflections, dark navy depth; wordmark still absent. |
| 7 | 2.4s | 85 | Complete original lockup legible, reflective stage beneath. |
| 8 | 2.8s | 99 | Upper diagonal traveling highlight and stable full lockup. |
| 9 | 3.2s | 113 | Reflective stage and deep atmosphere remain; prepare the foreground transition. |
| 10 | 3.6s | 127 | Broad, textured Earth-from-space horizon already spans the frame below the lockup; coordinated stage-to-horizon transition, not a small globe rising. |
| 11 | 4.0s | 141 | Gold-white sunrise peaks along the fixed shallow curved horizon; no logo movement or clipping. |
| 12 | 4.4s | 155 | Sunrise settles, campaign line SEE BEYOND THE NOISE is legible above the horizon. Continue the hold through frame 168. |

## Native production method

1. Start clean shot rigs using original geometry. Do not continue modifying rejected V09 framing or hide the stage to disguise seam problems. Work from the official logo geometry; use true vector curves if available, otherwise use verified V09E geometry and inspect large macro edges, including holes, stroke thickness, and topology. Do not replace the logo or use reference pixels as rendered content.
2. Build a camera shot plan from the reference anchors. Use Blender camera projection to match annotated landmark coverage and center in a square-safe composition, not merely interpolating one long camera pullback. Explicitly solve macro silver, macro R, three-quarter monogram, and final lockup. Use graph-editor-equivalent F-curves with controlled tangents, continuous velocity, and focus distance appropriate to the object. Bake final camera and check frame-to-frame motion. Prefer matched focal transitions and purposeful movement over an arbitrary roll/zoom.
3. Restore a physically reflective dark stage with controlled falloff, no visible flat seam, and real warm specular pools. Build broad softbox reflections, narrow traveling contour lights, and depth-producing atmosphere. Separate silver, gold, stage, environment and sunrise lighting via Cycles light groups and object/material Cryptomatte or view layers. Do not obscure logo edges with excessive bloom or isolated blown-out P highlights.
4. Build a separate, native, physically shaded Earth environment or rendered layer. Use a cleared, provenance-recorded true night-light texture, proper atmospheric limb, realistic city-light emission and an independently animated sun flare. NASA Black Marble flat maps are a candidate for rights review; do not assume commercial promotional clearance, use no NASA identifiers and imply no endorsement. A procedural fallback must not be called geographic imagery. Match the wide shallow horizon to the reference and hold its framing. Blend out stage reflections and blend in the Earth horizon together between panels 9 and 10; preserve logo position. The sun intensifies toward panel 11 and settles as the tagline appears in panel 12. Avoid a camera-parented small sphere that mechanically rises into text.
5. Use a scene-linear multilayer OpenEXR intermediate (Combined, light groups, Cryptomatte, emission, mist/depth, normals and denoising data as needed). Composite independently adjustable reflection, atmosphere, Earth and glare contributions. AgX finishing; test highlight clipping, black levels, color and glare with comparison frames. Keep render passes separate so a grade or transition change does not require the whole sequence to be ray-traced again.
6. Use native Blender 4.5.17 / Cycles OptiX when available and authorized. Draft all 12 anchor stills before a full motion run. Compare at the exact frames in the contract and review an inexpensive native motion pass at 24 FPS. Verify no malformed fills, aliasing, cropping, abrupt jumps, missing stage, mistimed Earth, or unreadable words. Only after visual review, render full resolution and encode with FFmpeg. Test denoiser settings with albedo/normal passes for detail retention rather than assuming more samples fixes geometry. Keep editable blend and render manifests in existing private R2, with hashes. No publishing private assets or modifying unrelated systems.

## Deterministic comparison

`engine/motion/v10/reference_match.py PRIVATE_REFERENCE.gif CANDIDATE.mp4 PRIVATE_OUTPUT_DIR` checks the exact reference digest, all frame durations, video dimensions/codec/duration/frame count/audio and generates a 12-pair contact sheet and JSON manifest. Run it on every full candidate; for keyframe drafts, compare the same anchor frame numbers directly. The tool never claims creative approval.

Local execution against the actual V09E video succeeded with exact GIF SHA and all 168 decoded frames verified by ffprobe. The contact sheet is private. Observed mismatch: frame 15 is a gold macro instead of silver bevel; frames 57 and 71 are still cropped instead of full monogram; frame 85 crops the wordmark; reflective floor is missing; the closing Earth is a small flat-looking rising shape rather than the reference's broad luminous horizon, and the tagline is obscured by the planet. Technical delivery is not creative success.

## Primary technical references

- Blender 4.5 light groups, render passes, Cryptomatte: https://docs.blender.org/manual/en/4.5/render/layers/passes.html
- Blender 4.5 F-curve control: https://docs.blender.org/manual/en/4.5/editors/graph_editor/fcurves/properties.html
- Blender 4.5 camera and optics: https://docs.blender.org/manual/en/4.5/render/cameras.html
- Blender 4.5 glare: https://docs.blender.org/manual/en/4.5/compositing/types/filter/glare.html
- Blender 4.5 color management and OpenEXR: https://docs.blender.org/manual/en/4.5/render/color_management.html
- Blender 4.5 adaptive sampling and denoising: https://docs.blender.org/manual/en/4.5/render/cycles/render_settings/sampling.html
- NASA Black Marble candidate asset source: https://science.nasa.gov/earth/earth-observatory/earth-at-night/maps/
- NASA commercial media guidance: https://www.nasa.gov/nasa-brand-center/images-and-media/

Do not rent a new GPU under the completed V09-specific authorization. Source work and local nonbillable checks may continue. Further paid native previews require explicit new authorization and bounded budget, verified cleanup, and private delivery. Final creative acceptance requires the owner.
