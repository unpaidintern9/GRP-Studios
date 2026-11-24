import { serveStdio } from "@modelcontextprotocol/server/stdio";
import { createServer } from "./server.mjs";
import { createLocalJobs } from "../plugins/blender/local.mjs";

const handle=serveStdio(()=>createServer({mode:"local",jobs:createLocalJobs()}));
process.on("SIGINT",()=>void handle.close());
process.on("SIGTERM",()=>void handle.close());
