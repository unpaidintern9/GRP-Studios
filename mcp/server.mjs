import { McpServer } from "@modelcontextprotocol/server";
import { z } from "zod";
import { buildRegistry } from "./core.mjs";

export function createServer(options) {
  const registry = buildRegistry(options);
  const server = new McpServer({ name: "grp-studios", version: "0.1.0" });
  for (const tool of registry.definitions()) {
    const inputSchema = z.object(Object.fromEntries(Object.keys(tool.params).map(k=>[k,z.string().min(1).max(80)]))).strict();
    server.registerTool(tool.name, {description: tool.description, inputSchema, annotations:{readOnlyHint:tool.readOnly, destructiveHint:false, openWorldHint:false}}, async args=>{
      try {
        const result = await registry.invoke(tool.name,args);
        return {content:[{type:"text",text:JSON.stringify(result,null,2)}]};
      } catch(error) {
        return {isError:true,content:[{type:"text",text:error instanceof Error ? error.message : "Tool failed"}]};
      }
    });
  }
  return server;
}
