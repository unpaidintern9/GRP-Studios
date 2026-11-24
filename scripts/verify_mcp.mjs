// Real SDK transport verification. Optional real Blender smoke, never a brand render.
import assert from "node:assert/strict";
import { stat } from "node:fs/promises";
import { setTimeout as sleep } from "node:timers/promises";
import { Client } from "@modelcontextprotocol/client";
import { StdioClientTransport } from "@modelcontextprotocol/client/stdio";

const client = new Client({ name: "grp-studios-validation", version: "0.1.0" });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: ["mcp/stdio.mjs"],
  env: process.env.BLENDER_BIN ? { BLENDER_BIN: process.env.BLENDER_BIN } : {},
  stderr: "inherit",
});
let active = null;
async function call(name, args = {}) {
  const result = await client.callTool({ name, arguments: args });
  assert.ok(!result.isError, name + ": " + JSON.stringify(result.content));
  const item = result.content.find(x => x.type === "text");
  assert.ok(item, "expected text result");
  return JSON.parse(item.text);
}
try {
  await client.connect(transport);
  const { tools } = await client.listTools();
  const expected = ["studio_status","list_plugins","get_brand_policy","list_templates","render_smoke","render_status","cancel_render"];
  assert.deepEqual(tools.map(t => t.name).sort(), expected.sort());
  assert.equal((await call("studio_status")).remoteRendering, false);
  assert.equal((await call("list_templates")).find(t => t.id === "gold-light-v02").status, "blocked");
  assert.match((await call("get_brand_policy")).prototypeV01, /rejected/);
  console.log("PASS SDK stdio handshake, seven tools, policy and blocked brand template");
  if (process.argv.includes("--render")) {
    const job = await call("render_smoke");
    active = job.id;
    const deadline = Date.now() + 210000;
    let status;
    do {
      status = await call("render_status", {job_id: active});
      if (["succeeded","failed","cancelled"].includes(status.state)) break;
      await sleep(500);
    } while (Date.now() < deadline);
    assert.equal(status.state, "succeeded", JSON.stringify(status));
    assert.match(status.artifact.replaceAll("\\","/"), /^renders\/mcp-smoke\/run-[^/]+\/metallic\.png$/);
    assert.ok((await stat(status.artifact)).size > 24);
    active = null;
    console.log("PASS actual Blender MCP smoke:", status.artifact);
  }
} finally {
  if (active) { try { await call("cancel_render", {job_id:active}); } catch {} }
  await client.close();
}
