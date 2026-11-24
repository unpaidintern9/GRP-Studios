"""Gold Light V02 native Blender construction. Private, review-only.
Run Blender 4.5.17 headless. Do not publish these draft renders.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / "private"
WORK = PRIVATE / "gold-light-v02"
BLOBS = {
    "full": "84bba8beaba9ec557d05f5426e958233f00d3605",
    "mark": "8c8b9cad7ad96ffae49f778b78d09f7ce29b82cb",
}
EXPECTED = {
    "silver-monogram": (2, "silver"),
    "gold-r": (1, "gold"),
    "silver-wordmark": (6, "silver"),
    "gold-descriptor": (16, "gold"),
}
# Center in the full lockup's original pixel coordinate system.
CENTER = (744.0, 453.5)
UNITS_PER_PIXEL = 6.0 / 932.0
REVIEW_FRAMES = (18, 36, 76, 114)

def private_path(path):
    p = path.resolve()
    if PRIVATE.resolve() != ROOT / "private" or not p.is_relative_to(PRIVATE.resolve()):
        raise RuntimeError("Path must remain inside the private project directory")
    return p

def digest(data):
    return hashlib.sha256(data).hexdigest()

def git_blob(data):
    return hashlib.sha1(("blob " + str(len(data)) + "\0").encode() + data).hexdigest()

def load_geometry():
    raw = private_path(WORK / "geometry.json").read_bytes()
    if len(raw) > 2_000_000:
        raise RuntimeError("Geometry candidate unexpectedly large")
    report = json.loads(private_path(WORK / "geometry-report.json").read_text())
    if digest(raw) != report["geometrySha256"]:
        raise RuntimeError("Geometry report hash mismatch")
    g = json.loads(raw)
    if (g["version"], g["width"], g["height"]) != (1, 1536, 934):
        raise RuntimeError("Unexpected geometry format")
    if g["status"] != "candidate-not-human-approved" or g["monogramAgreement"] != 1:
        raise RuntimeError("Unverified geometry candidate")
    for key, blob in BLOBS.items():
        name = "grp-full-reverse.png" if key == "full" else "grp-mark-reverse.png"
        data = private_path(PRIVATE / "brand" / name).read_bytes()
        if git_blob(data) != blob or g["sources"][key]["blob"] != blob:
            raise RuntimeError("Original artwork identity mismatch")
        if digest(data) != g["sources"][key]["sha256"]:
            raise RuntimeError("Original artwork digest mismatch")
    if len(g["groups"]) != 4 or {x["name"] for x in g["groups"]} != set(EXPECTED):
        raise RuntimeError("Missing or duplicate geometry group")
    for group in g["groups"]:
        expected, _ = EXPECTED[group["name"]]
        if group["components"] != expected or group["outer"] != expected or not .985 <= group["iou"] <= 1:
            raise RuntimeError("Candidate does not meet contour acceptance")
        if not group["loops"] or sum(len(p) for p in group["loops"]) > 10000:
            raise RuntimeError("Invalid contour count")
        for polygon in group["loops"]:
            if len(polygon) < 3 or any(
                len(p) != 2 or not all(isinstance(v, int) for v in p)
                or not (0 <= p[0] <= 1536 and 0 <= p[1] <= 934)
                for p in polygon
            ):
                raise RuntimeError("Invalid contour coordinates")
    return g, digest(raw)

def world_point(px, py, z=0):
    return ((px - CENTER[0]) * UNITS_PER_PIXEL,
            (CENTER[1] - py) * UNITS_PER_PIXEL, z)

def aim(obj, target):
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = (Vector(target) - obj.location).to_track_quat("-Z", "Y")

def material(name, base, low, high, anisotropy):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    p = n.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*base, 1)
    p.inputs["Metallic"].default_value = 1.0
    p.inputs["Roughness"].default_value = (low + high) / 2
    if "Anisotropic IOR Level" in p.inputs:
        p.inputs["Anisotropic IOR Level"].default_value = anisotropy
    tex = n.new("ShaderNodeTexCoord")
    stretched = n.new("ShaderNodeVectorMath")
    stretched.operation = "MULTIPLY"
    stretched.inputs[1].default_value = (4.0, 180.0, 28.0)
    l.new(tex.outputs["Object"], stretched.inputs[0])
    noise = n.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 2.0
    l.new(stretched.outputs["Vector"], noise.inputs["Vector"])
    rough = n.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = low
    rough.inputs["To Max"].default_value = high
    l.new(noise.outputs["Fac"], rough.inputs["Value"])
    l.new(rough.outputs["Result"], p.inputs["Roughness"])
    return m

def make_group(group, mat):
    name = group["name"]
    curve = bpy.data.curves.new(name + "-contours", "CURVE")
    curve.dimensions = "2D"
    curve.fill_mode = "BOTH"
    curve.resolution_u = 1
    curve.render_resolution_u = 1
    is_mark = name in ("silver-monogram", "gold-r")
    # Native polygons, no retyping or rescaling by glyph. Relative positions
    # come directly from one shared full-lockup coordinate system.
    curve.extrude = .055 if is_mark else .018
    curve.bevel_depth = .0045 if is_mark else .0015
    curve.bevel_resolution = 3
    for polygon in group["loops"]:
        spline = curve.splines.new("POLY")
        spline.points.add(len(polygon) - 1)
        for p, (x, y) in zip(spline.points, polygon):
            p.co = (*world_point(x, y), 1)
        spline.use_cyclic_u = True
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    curve.materials.append(mat)
    return obj

def rectangle_light(name, location, target, width, height, energy, color):
    data = bpy.data.lights.new(name, "AREA")
    data.shape = "RECTANGLE"
    data.size = width
    data.size_y = height
    data.energy = energy
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj

def animate_energy(obj, keys):
    for frame, power in keys:
        obj.data.energy = power
        obj.data.keyframe_insert(data_path="energy", frame=frame)

def camera_key(camera, frame, target, distance, offset, lens, aperture):
    t = Vector(target)
    camera.location = t + Vector((offset[0], offset[1], distance))
    aim(camera, t)
    camera.data.lens = lens
    camera.data.dof.focus_distance = (camera.location - t).length
    camera.data.dof.aperture_fstop = aperture
    camera.keyframe_insert(data_path="location", frame=frame)
    camera.keyframe_insert(data_path="rotation_quaternion", frame=frame)
    camera.data.keyframe_insert(data_path="lens", frame=frame)
    camera.data.dof.keyframe_insert(data_path="focus_distance", frame=frame)
    camera.data.dof.keyframe_insert(data_path="aperture_fstop", frame=frame)

def optical_card(camera, name, depth, sx, sy, color, power, spread_x, spread_y):
    # An original optical streak, not a generated image or unrelated logo ribbon.
    # Camera-parented transparent emissive geometry lets Cycles render it without
    # introducing a second camera or rewriting the real monogram geometry.
    bpy.ops.mesh.primitive_plane_add(size=2)
    obj = bpy.context.object
    obj.name = name
    obj.parent = camera
    obj.location = (0, 0, -depth)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (sx, sy, 1)
    for attribute in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter"):
        if hasattr(obj, attribute):
            setattr(obj, attribute, False)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    output = n.new("ShaderNodeOutputMaterial")
    uv = n.new("ShaderNodeTexCoord")
    split = n.new("ShaderNodeSeparateXYZ")
    l.new(uv.outputs["UV"], split.inputs[0])
    def math_node(operation, a, b=None):
        node = n.new("ShaderNodeMath")
        node.operation = operation
        for i, value in enumerate([a] if b is None else [a,b]):
            if isinstance(value, (float,int)):
                node.inputs[i].default_value = value
            else:
                l.new(value, node.inputs[i])
        return node.outputs[0]
    def square_axis(axis, spread):
        centered = math_node("SUBTRACT", split.outputs[axis], .5)
        scaled = math_node("DIVIDE", centered, spread)
        return math_node("MULTIPLY", scaled, scaled)
    shape = math_node("EXPONENT", math_node("MULTIPLY",
                      math_node("ADD", square_axis("X",spread_x), square_axis("Y",spread_y)), -1))
    control = n.new("ShaderNodeValue")
    control.label = "Opening flare intensity"
    factor = math_node("MULTIPLY", shape, control.outputs[0])
    transparent = n.new("ShaderNodeBsdfTransparent")
    emission = n.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*color, 1)
    emission.inputs["Strength"].default_value = power
    mix = n.new("ShaderNodeMixShader")
    l.new(factor, mix.inputs[0])
    l.new(transparent.outputs[0], mix.inputs[1])
    l.new(emission.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], output.inputs["Surface"])
    obj.data.materials.append(m)
    # Screen stays dark first, develops the chosen gold core, and then
    # disappears as the physical gold R becomes illuminated.
    for frame, value in [(1,0),(6,.03),(14,.8),(18,1),(21,.35),(27,0),(120,0)]:
        control.outputs[0].default_value = value
        control.outputs[0].keyframe_insert(data_path="default_value", frame=frame)
    return obj

def create_scene(geometry, geometry_hash):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "GRP Gold Light V02 - private look development"
    scene["geometry_sha256"] = geometry_hash
    scene["creative_status"] = "candidate; V01 rejected; no publication"
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.cycles.transparent_max_bounces = 12
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.fps_base = 1
    scene.frame_start, scene.frame_end = 1, 120
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("Obsidian studio")
    world.use_nodes = True
    scene.world = world
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.008,.012,.023,1)
    for f,v in [(1,0),(18,0),(30,.10),(76,.15),(120,.15)]:
        background.inputs["Strength"].default_value = v
        background.inputs["Strength"].keyframe_insert(data_path="default_value", frame=f)
    gold = material("Brushed gold R", (.83,.43,.095), .23,.32,.42)
    silver = material("Satin silver G and P", (.70,.74,.79), .22,.30,.27)
    marks = [make_group(group, gold if EXPECTED[group["name"]][1]=="gold" else silver)
             for group in geometry["groups"]]
    # Inspect evaluated curves before rendering. This catches empty or
    # failed fill/extrusion, but not every possible contour/bevel artifact.
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    stats = []
    for obj in marks:
        evaluated = obj.evaluated_get(depsgraph)
        mesh = evaluated.to_mesh()
        try:
            if not mesh.vertices or not mesh.polygons:
                raise RuntimeError("Empty evaluated geometry: " + obj.name)
            stats.append({"object":obj.name,"vertices":len(mesh.vertices),
                          "faces":len(mesh.polygons),"dimensions":list(obj.dimensions)})
        finally:
            evaluated.to_mesh_clear()
    data = bpy.data.cameras.new("Hero 65mm")
    camera = bpy.data.objects.new("Hero camera",data)
    bpy.context.collection.objects.link(camera)
    scene.camera = camera
    data.sensor_width = 36
    data.clip_start = .02
    data.dof.use_dof = True
    # Frame 1 = 0 seconds; 120 frames total. The macro path follows the
    # original R bowl and descending leg, then pulls back toward the lockup.
    camera_key(camera,1,world_point(774,154,.05),1.35,(-.18,.10),65,2.8)
    camera_key(camera,18,world_point(774,154,.05),1.35,(-.18,.10),65,2.8)
    camera_key(camera,27,world_point(815,265,.05),1.55,(-.22,.12),65,3.2)
    camera_key(camera,36,world_point(818,370,.05),2.00,(-.25,.12),60,3.5)
    camera_key(camera,43,world_point(903,470,.05),2.8,(.24,.05),55,4.0)
    camera_key(camera,76,world_point(743,318,.05),10.5,(.12,.03),48,8)
    camera_key(camera,106,(0,0,.03),13.1,(0,0),48,11)
    camera_key(camera,120,(0,0,.03),13.1,(0,0),48,11)
    key = rectangle_light("Large soft silver key",(-3.3,3.5,4.6),(0,.8,0),5.0,2.2,0,(.83,.90,1))
    rim = rectangle_light("Warm grazing gold strip",(3.5,2.2,2.8),world_point(820,370),3.2,.35,0,(1,.72,.39))
    fill = rectangle_light("Low cool edge",(-2.4,-3.0,2.8),(0,0,0),4.1,.6,0,(.71,.82,1))
    front = rectangle_light("Broad clean wordmark fill",(0,1.0,6.0),(0,0,0),6,3,0,(1,.94,.84))
    animate_energy(key,[(1,0),(18,0),(26,65),(43,220),(76,550),(106,680),(120,680)])
    animate_energy(rim,[(1,0),(18,0),(25,220),(36,620),(43,700),(76,780),(106,450),(120,450)])
    animate_energy(fill,[(1,0),(18,0),(32,35),(76,260),(106,330),(120,330)])
    animate_energy(front,[(1,0),(43,0),(76,130),(106,520),(120,520)])
    # All three optical layers are original procedural elements. No stock
    # content, synthetic voice, data lines, globe, or generated lettering.
    optical_card(camera,"Amber halo",.45,.30,.10,(1,.26,.035),2.5,.19,.22)
    optical_card(camera,"Gold hairline",.44,.33,.020,(1,.55,.10),14,.45,.065)
    optical_card(camera,"White-gold core",.43,.09,.018,(1,.86,.48),32,.19,.12)
    for frame,label in [(18,"Gold light"),(36,"R macro"),(76,"Monogram"),(114,"Full alignment")]:
        scene.timeline_markers.new(label,frame=frame)
    return scene, stats

def main():
    args = argparse.ArgumentParser()
    args.add_argument("--review", action="store_true", help="Render only four private keyframes")
    opt = args.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    if tuple(bpy.app.version) != (4,5,17):
        raise RuntimeError("Expected Blender 4.5.17 LTS")
    geometry, sha = load_geometry()
    out = private_path(WORK / "lookdev")
    out.mkdir(exist_ok=False)
    scene, meshes = create_scene(geometry,sha)
    scene.frame_set(76)
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"gold-light-v02-lookdev.blend"))
    images = []
    if opt.review:
        for frame in REVIEW_FRAMES:
            scene.frame_set(frame)
            target = out / ("frame-%03d.png" % frame)
            scene.render.filepath = str(target)
            bpy.ops.render.render(write_still=True)
            if not target.is_file() or target.stat().st_size < 24:
                raise RuntimeError("Missing rendered keyframe")
            images.append({"frame":frame,"sha256":digest(target.read_bytes()),"file":target.name})
    receipt = {
        "status":"unapproved-lookdev", "version":bpy.app.version_string,
        "geometrySha256":sha, "engine":"Cycles CPU", "resolution":[1920,1080],
        "fps":24,"totalFrames":120,"samples":32,"meshes":meshes,
        "keyframes":images,
        "limits":["No complete animation yet", "Final exact PNG end-card compositing pending",
                  "Human review and contour/bevel quality checks pending"]
    }
    (out/"lookdev-receipt.json").write_text(json.dumps(receipt,indent=2)+"\n")
    print(json.dumps(receipt,indent=2))

if __name__ == "__main__":
    main()
