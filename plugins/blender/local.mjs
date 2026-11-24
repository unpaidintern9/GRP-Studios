// Local machine only. No arbitrary commands, scripts, paths or paid services.
import { spawn } from "node:child_process";
import { readFile, mkdir, mkdtemp, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { createJobs } from "../../mcp/core.mjs";

const root = fileURLToPath(new URL("../../",import.meta.url));
const blender = process.env.BLENDER_BIN || "blender";
const script = path.join(root,"engine","motion","smoke_scene.py");

function execute(args, {signal, timeout}) {
  return new Promise((resolve,reject)=>{
    if(signal.aborted){reject(Error("Cancelled"));return;}
    const child=spawn(blender,args,{cwd:root,shell:false,stdio:["ignore","pipe","pipe"],windowsHide:true});
    let log="",reason=null;
    const collect=buf=>{log=(log+buf.toString()).slice(-8192);};
    child.stdout.on("data",collect);child.stderr.on("data",collect);
    const stop=why=>{if(!reason)reason=why;child.kill("SIGKILL");};
    const abort=()=>stop("cancelled");
    const timer=setTimeout(()=>stop("timeout"),timeout);
    signal.addEventListener("abort",abort,{once:true});
    if(signal.aborted)abort();
    const clean=()=>{clearTimeout(timer);signal.removeEventListener("abort",abort);};
    child.once("error",err=>{clean();reject(err);});
    child.once("close",(code)=>{clean();if(reason||code!==0){console.error("Blender smoke:",reason||code,log);reject(Error(reason||"Blender returned nonzero"));}else resolve(log);});
  });
}
export async function runSmoke({signal}) {
  const version=await execute(["--version"],{signal,timeout:10000});
  if(!/^Blender 4\.5\.17(?:\s|$)/m.test(version))throw Error("Expected Blender 4.5.17");
  const base=path.join(root,"renders","mcp-smoke");await mkdir(base,{recursive:true});
  const dir=await mkdtemp(path.join(base,"run-")), target=path.join(dir,"metallic.png");
  await execute(["--background","--factory-startup","--disable-autoexec","--python-exit-code","1","--python",script,"--",target],{signal,timeout:180000});
  const st=await stat(target);
  if(st.size<24||st.size>10*1024*1024)throw Error("Invalid PNG size");
  const png=await readFile(target);
  if(!png.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10]))||png.readUInt32BE(16)!==640||png.readUInt32BE(20)!==360)throw Error("Invalid smoke PNG");
  return {artifact:path.relative(root,target)};
}
export function createLocalJobs(){
  return createJobs(runSmoke,{id:randomUUID,now:()=>new Date().toISOString(),controller:()=>new AbortController()});
}
