// Shared, side-effect-free plugin registry and local job manager.
const POLICY = {
  "version": "1.0.0",
  "brand": "Gilmer Research Partners",
  "approvedDirection": "Gold Light Emergence",
  "prototypeV01": "rejected: flat 2D reveal",
  "rules": [
    "Real human narration only; no cloned or synthetic voices.",
    "Use official artwork and approved product/data captures; no fabricated claims.",
    "No flat 2D substitute for cinematic 3D; no globe, random particles or unrelated ribbons in the ident.",
    "No Terminal runtime, credentials, database, runners or deployments.",
    "Keep proprietary media private; no automatic publication.",
    "No paid generation, GPU rental or new cloud resources without explicit authorization."
  ],
  "plan": "docs/MASTER_PLAN.md",
  "brief": "docs/gold-light-ident.md"
};
const PLUGINS = [
  {
    "id": "blender",
    "version": "0.1.0",
    "state": "local-smoke-adapter",
    "description": "Local, generic metallic test render; real Blender runtime not yet verified."
  },
  {
    "id": "video",
    "state": "planned"
  },
  {
    "id": "sound",
    "state": "planned"
  },
  {
    "id": "motion",
    "state": "planned"
  },
  {
    "id": "design",
    "state": "planned"
  },
  {
    "id": "product-showcase",
    "state": "planned"
  },
  {
    "id": "ai-cinema",
    "state": "planned"
  },
  {
    "id": "quality",
    "state": "planned"
  }
];
const TEMPLATES = [
  {
    "id": "metallic-smoke-v1",
    "engine": "blender",
    "status": "local-test-only",
    "description": "640x360 generic metallic torus. Not GRP brand footage.",
    "cost": "local compute only"
  },
  {
    "id": "gold-light-v02",
    "engine": "blender",
    "status": "blocked",
    "description": "Selected cinematic 5-second 120-frame ident; needs verified geometry and renderer.",
    "brief": "docs/gold-light-ident.md"
  }
];
export function createJobs(run, options) {
  const jobs=new Map(); let active=null; const max=options.maxHistory??32;
  function status(id){const j=jobs.get(id);if(!j)throw Error("Unknown job");return {...j}}
  function start(){
    if(active)throw Error("A local render is already running");
    while(jobs.size>=max){const old=[...jobs.keys()].find(k=>!["running","cancelling"].includes(jobs.get(k).state));if(!old)throw Error("Job capacity reached");jobs.delete(old)}
    const id=options.id(), controller=options.controller();
    if(jobs.has(id))throw Error("Duplicate job ID");
    const j={id,template:"metallic-smoke-v1",state:"running",createdAt:options.now(),artifact:null,detail:null};jobs.set(id,j);active={id,controller};
    Promise.resolve().then(()=>run({id,signal:controller.signal})).then(result=>{
      if(controller.signal.aborted){j.state="cancelled";j.detail="Cancelled";}
      else if(!result||typeof result.artifact!=="string"||!result.artifact){j.state="failed";j.detail="Adapter returned no artifact";}
      else {j.state="succeeded";j.artifact=result.artifact;}
    },()=>{j.state=controller.signal.aborted?"cancelled":"failed";j.detail=controller.signal.aborted?"Cancelled":"Render failed; inspect private worker logs.";}).finally(()=>{j.finishedAt=options.now();if(active?.id===id)active=null;});
    return {...j};
  }
  function cancel(id){const j=jobs.get(id);if(!j)throw Error("Unknown job");if(active?.id===id&&j.state==="running"){j.state="cancelling";active.controller.abort();}return {...j}}
  return {start,status,cancel};
}
export function buildRegistry({mode,jobs=null}){
  if(!["local","remote"].includes(mode))throw Error("Invalid mode");
  const list=new Map();
  function add(name,description,params,readOnly,handler){if(list.has(name))throw Error("Duplicate tool");list.set(name,{name,description,params,readOnly,handler});}
  add("studio_status","Report implemented tools and deployment/render limitations.",{},true,()=>({mode,version:"0.1.0",remoteRendering:false,paidProviders:false,localSmoke:mode==="local"&&!!jobs,finalIdent:"not rendered",authentication:mode==="remote"?"machine-token preview only":"local process"}));
  add("list_plugins","List production plugins and their actual implementation status.",{},true,()=>PLUGINS.map(p=>({...p})));
  add("get_brand_policy","Return the approved production rules and rejection benchmark.",{},true,()=>({...POLICY,rules:[...POLICY.rules]}));
  add("list_templates","List render templates, including blocked work.",{},true,()=>TEMPLATES.map(t=>({...t})));
  if(mode==="local"&&jobs){
    add("render_smoke","Start a single bounded local Blender test render (not a GRP ident). No cloud or paid calls.",{},false,()=>jobs.start());
    add("render_status","Get local smoke job status.",{job_id:"string"},true,a=>jobs.status(a.job_id));
    add("cancel_render","Request cancellation of a running local smoke job.",{job_id:"string"},false,a=>jobs.cancel(a.job_id));
  }
  return {
    definitions:()=>[...list.values()].map(({handler,...x})=>x),
    invoke:async(name,args={})=>{
      const t=list.get(name);if(!t)throw Error("Unknown or disabled tool");
      if(!args||typeof args!=="object"||Array.isArray(args))throw Error("Invalid arguments");
      for(const k of Object.keys(args))if(!Object.hasOwn(t.params,k))throw Error("Unexpected argument");
      for(const k of Object.keys(t.params))if(typeof args[k]!=="string"||args[k].length<1||args[k].length>80)throw Error("Invalid "+k);
      return t.handler(args);
    }
  };
}
