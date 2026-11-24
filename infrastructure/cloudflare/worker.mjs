// Read-only machine-authenticated preview. Not the final team OAuth endpoint.
import { createMcpHandler } from "agents/mcp/server";
import { createServer } from "../../mcp/server.mjs";
import { previewGuard } from "./preview-auth.mjs";

const handler = createMcpHandler(() => createServer({ mode: "remote" }));
export default {
  async fetch(request, env, ctx) {
    const rejection = await previewGuard(request, env);
    if (rejection) return rejection;
    const response = await handler(request, env, ctx);
    const headers = new Headers(response.headers);
    headers.set("Cache-Control", "no-store");
    return new Response(response.body, { status: response.status, statusText: response.statusText, headers });
  }
};
