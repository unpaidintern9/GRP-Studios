# GRP Studios GPU backend — source candidate
Owner requested Runpod integration after funding the account. CPU production remains independent and unchanged in the deployed Worker. No GPU purchase or production deployment is implied.

## Runtime
Build the existing pinned service Dockerfile from this revision; publish an immutable image to a registry accessible by Runpod. Launch only on approved NVIDIA hardware with driver capability `compute,utility,graphics` available; no SSH or public service needed. GPU execution is explicit via `GRP_RENDER_DEVICE=OPTIX`; Blender must enumerate a named OptiX device or fail, never silently use CPU. CPU remains default. The same 105 native moving frames, original closing hold and verified five-second export are retained. CPU and GPU receipts cannot be mixed. Separate R2 job prefix required; never use the in-flight CPU singleton's keys.

## Private batch transfer
`python3 /opt/studio/scripts/gpu_batch_transfer.py` reads a pre-signed HTTPS input URL (GRP_INPUT_URL), exact input SHA-256 (GRP_INPUT_SHA256) and a single short-lived signed upload URL (GRP_OUTPUT_URL). Input is the existing four-byte big-endian length plus fixed JSON header, followed by archives for assembly. Output is the existing ZIP contract. URLs must expire shortly after the authorized job deadline; only job-specific object permissions. No account tokens in pod env, Git or logs. The operator/controller must verify uploaded ZIP bytes, hash and receipt independently before accepting. Use a distinct GPU prefix and immutable publication; presigned writes alone do not enforce immutability.

## Control plane
The quote planner accepts current per-GPU hourly prices and matching count availability. Secure Cloud by default, community only explicit. Pro=1, Ultra=4, Ultra Max=8; a smaller available count can be selected. It estimates a ceiling including a storage reserve; it does not enforce provider billing or provision hardware. Prices must be freshly verified. Cloudflare lifecycle wiring is a separate next step: use a dedicated durable job record and independent deadline alarm before allocation, store returned pod IDs, terminate on success/failure/deadline, reconcile ambiguous create/delete and orphan pods, verify actual billing. Store Runpod API credential as a Worker secret; OAuth ChatGPT connection does not automatically grant the Worker credentials. No automatic CPU-to-GPU fallback or duplicate production jobs.

## Acceptance
1. Build and pin image; generic GPU smoke and actual OptiX enumeration.
2. Authorized single-GPU benchmark, same scene and settings, compare elapsed time, original geometry, device receipt, visual frames and real billing.
3. Validate private transfer, immutable R2 output, termination and independent deadline; test orphan recovery.
4. Only then enable production scheduling and multi-GPU frame distribution. No GPU runtime, image publication or deployment has been verified by this source change.

## Credential preflight
The fixed authenticated queue operation `{ "operation": "gpu-preflight" }` performs only Runpod REST v2 GETs for billing balance and pod listing (scopes `billing:read`, `pods:read`). It stores a sanitized private receipt at `gpu/control/runpod-preflight.json`. No GPU is rented. Worker secret presence was verified on November 24; actual authentication is pending deployment and private preflight. Do not deploy over the active CPU job. API documentation: https://docs.runpod.io/api-reference-v2/overview.
