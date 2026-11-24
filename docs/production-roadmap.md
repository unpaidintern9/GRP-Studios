# Production roadmap, budget and acceptance standards

## Build sequence

| Phase | Deliverable | Exit evidence |
|---|---|---|
| 1 — Cinematic identity | Three distinct original five-second ident concepts, lighting/material studies, candidate sonic signature | Owner selects direction; exact approved logo, no shape/text distortion, reference renders and rights review |
| 2 — Proof of concept | 15-second no-narration teaser using real product imagery and cinematic footage | Reviewed 16:9 video with strong pacing, sound, believable imagery and legible real UI; no sensitive or unsupported claims |
| 3 — Reusable toolkit | Motion, product, render and asset library templates; local tooling | Repeatable renders, documented setup, predictable outputs and no Terminal integration |
| 4 — Product launch | 30-second initial film, then optional 60-second Introducing Gilmer master | Approved picture, licensed audio, correct UI and claims, versioned master and cutdowns |
| 5 — Flagship | 75–90-second Beyond the Noise, real narrator, edited product and real-world scenes | Approved storyboard, human audio and rights, polished sound/color, compliance review and final renders |
| 6 — Campaign rollout | Investor, advisor, research, options, global variants; social and web cuts | Per-channel delivery, brand consistency, claim and rights checks |

The original planning conversation proposed building the reusable engine before the flagship. The revised lean approach deliberately starts with the ident and teaser, validating visual quality before building a full studio. The initial teaser is 15 seconds; a subsequent 30-second product launch is a separate milestone. Do not build everything at once or purchase services before a specific need is established.

## Budget

Original outsourced/hybrid planning estimate (not vendor quotes):

| Item | Estimated cost |
|---|---:|
| AI video generation / experiments | $100–$400 |
| Premium licensed footage | $150–$600 |
| Professional human voiceover | $250–$1,000 |
| Music and sound licensing | $100–$500 |
| Editing and motion software | $0–$150 |
| Specialist motion design | $500–$2,500 |
| Total | $1,100–$5,150 |

This is not the approved spending plan. The owner questioned the cost and the project shifted to a lean, predominantly self-produced approach.

| Lean item | Proposed approach | Estimated cash |
|---|---|---:|
| Logo and VFX | Blender/Python, Fusion | $0 |
| Product motion | Three.js / Remotion if licensing allows | $0 assumption |
| Editing | DaVinci Resolve free version | $0 |
| Actual UI | Approved capture/screen recording | $0 incremental |
| Real-world footage | Original or cleared free stock | $0 assumption |
| AI footage | Optional limited experiments | $30–$100 |
| Sound and music | Original or cleared free commercial licenses | $0 assumption |
| Narration | Real self-recorded voice or hired human | $0–$100 |
| Initial total | If optional AI used | $30–$200 |

**Target initial cash budget: $100 or less**, a planning target rather than authorization to spend. The first logo/teaser can be attempted with zero incremental cash using existing equipment, local rendering and cleared assets. Free plans and commercial licenses must be verified; paid compute, storage, music rights, voice rights, team labor, and revisions may increase costs. No purchase is implied.

## Non-negotiable quality standards

1. No synthetic voice, voice cloning, AI avatar, fake human speaking scene, fabricated testimonial or implied endorsement.
2. No hallucinated charts, financial values, UI, branding, or generated lettering. Use approved official vector artwork and authentic product captures. Maintain approved color, proportions, clear space and typography.
3. No generic blue holograms, floating dollar signs, cheesy Wall Street imagery, obvious AI artifacts or gratuitous effects.
4. Realistic light, materials, shadows, optics, motion, continuity, color and sound; inspect generated shots frame by frame for warping, temporal flicker, impossible movement, artifacts and discontinuities.
5. Actual products and financial data only; no invented coverage, performance claims, misleading availability or guarantee of returns. Verify current product functionality and required disclosures for each campaign.
6. Original or properly licensed visuals, fonts, voices, sound, music, software and third-party assets. Confirm commercial and advertising rights, releases, attribution and license scope. Maintain rights and provenance in private records.
7. No secrets, personal data, internal datasets, confidential captures, unreleased proprietary media or production access in public Git. No automatic deployment, no production runner or ingestion workload.
8. Review legibility, timing, crops, transitions, audio peaks, caption accuracy and output integrity. Do not call an animation, film or launch complete until actual render and human review exist.

## Deliverable specifications (proposed defaults)

- Primary 4K 16:9 master (3840×2160), with 1080p review and distribution renders; choose a consistent 24 or 30 fps after tests.
- Preserve high-quality mezzanine master and web/social H.264 MP4; transparent transitions using an appropriate alpha-capable format; audio stems where useful.
- 9:16, 1:1 and optional 4:5 reframes, captioned versions for speech, silent web loops. Export no fabricated UI or financial claims.
- Keep manifests for source files, asset rights, render version and hash, final review and approval, outside public Git if sensitive.
- Human approval before publication; do not deploy to the Terminal or publish externally from this repository automatically.

## Immediate next tasks

- Obtain the official GRP logo vector and approved brand palette/typeface as private inputs, plus sanitized real product captures.
- Review the reference videos and select a distinctive motion direction.
- Prototype three Blender ident concepts, compare frame-accurate preview renders and score sound, realism, distinctiveness and logo fidelity.
- Select one and render the standalone ident, one-second sweep and a silent 15-second teaser.
- Approve the visual language before committing to the larger studio or external expenditure.
