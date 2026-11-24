import bpy,json,pathlib
root=pathlib.Path('/tmp/grp-v09')
s=bpy.context.scene
# The original V09b silver curves have correct Blender tessellation and fill.
# Import ONLY the independently checked refined gold R curve from the rejected
# V09d scene; never import its malformed silver P mesh.
old=bpy.data.objects['gold-r'];old_data=old.data
with bpy.data.libraries.load(str(root/'preview/gold-light-v09d.blend'),link=False) as (src,dst):
    dst.objects=['gold-r']
gold=dst.objects[0]
if gold is None or gold.type!='CURVE':
    raise RuntimeError("Expected original refined gold curve")
old.data=gold.data
bpy.data.objects.remove(gold,do_unlink=True)
# Silver contour fidelity takes priority over a visually invalid fitted face.
for name in ('silver-monogram','gold-r'):
    c=bpy.data.objects[name].data;c.resolution_u=48;c.render_resolution_u=48;c.bevel_resolution=12
# Maintain metal shading while keeping the small typography readable.
for name,color,strength in [('silver-wordmark',(.60,.65,.70,1),.020),('gold-descriptor',(.62,.27,.035,1),.035)]:
    mat=bpy.data.objects[name].data.materials[0];p=mat.node_tree.nodes.get('Principled BSDF')
    p.inputs['Emission Color'].default_value=color;p.inputs['Emission Strength'].default_value=strength
s['creative_status']='V09e corrected silver face fill; review candidate, unapproved'
p=bpy.context.preferences.addons["cycles"].preferences;p.compute_device_type="OPTIX";p.get_devices()
if not any(d.type=="OPTIX" for d in p.devices):raise RuntimeError("No OptiX")
for d in p.devices:d.use=d.type=="OPTIX"
s.cycles.device="GPU";s.cycles.denoiser="OPTIX";s.cycles.samples=64;s.cycles.adaptive_threshold=.018
s.render.resolution_percentage=100
s.frame_set(120);bpy.ops.wm.save_as_mainfile(filepath=str(root/'preview/gold-light-v09e.blend'))
for f in (65,92,120,145):
    s.frame_set(f);s.render.filepath=str(root/f'preview/corrected-{f:03}.png');bpy.ops.render.render(write_still=True)
print('V09E_PREVIEW_PASS',flush=True)
