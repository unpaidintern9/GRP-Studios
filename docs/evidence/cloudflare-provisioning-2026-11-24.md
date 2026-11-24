# Cloudflare provisioning — 2026-11-24

Owner authorized dedicated GRP Studios resources under the existing plan. All writes used the authenticated Cloudflare MCP, scoped to new Studio resources only.

| Resource | Result |
|---|---|
| grp-studios-media | Created Standard R2, ENAM; managed public domain disabled, no custom domains |
| grp-studios-db | Created D1, ENAM, replication disabled; initial migration all six statements passed; four expected tables verified; foreign_key_check empty |
| grp-studios-render-queue | Created; zero producers and consumers |
| grp-studios-render-dlq | Created; zero producers and consumers |

Both original reverse PNGs were copied directly from authorized GitHub read-only access into private R2, under versioned keys brand/originals/<git-blob>/<filename>. Git blob SHA-1 verified before write; R2 GET SHA-256 matched source bytes. Monogram 304742 bytes; full lockup 562827 bytes. No artwork bytes or proprietary output committed publicly. No Terminal runtime dependency.

Worker grp-studios-mcp and Container grp-studios-render-worker remain NOT DEPLOYED. The prior successful Wrangler dry run did not retain a deployable Worker bundle; the proven Blender CLI container was not published as a Cloudflare-ready HTTP service. Next implement a bounded private render service, publish and verify its image, deploy the authenticated MCP without public asset exposure, and connect the isolated worker. Do not create a placeholder application or start recurring compute merely to mark a milestone done.

No billing changes, GPU rentals, public routes, queue messages or running containers initiated. Billing scope was unavailable, so actual account usage/charges are not independently verified. Resource identifiers and credentials are omitted from public Git. M3 and M8 remain incomplete.
