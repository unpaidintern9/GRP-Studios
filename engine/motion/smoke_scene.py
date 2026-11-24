"""Generic Blender Cycles test. Not an approved GRP ident."""
import sys
from pathlib import Path
import bpy
from mathutils import Vector

target = Path(sys.argv[sys.argv.index("--") + 1])
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 16
scene.render.resolution_x = 640
scene.render.resolution_y = 360
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = str(target)
scene.world = bpy.data.worlds.new("Studio world")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.015, 0.019, 0.027, 1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.25

def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()

bpy.ops.mesh.primitive_torus_add(major_radius=1.0, minor_radius=0.22)
metal = bpy.data.materials.new("Generic gold")
metal.use_nodes = True
bsdf = metal.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.83, 0.46, 0.13, 1)
bsdf.inputs["Metallic"].default_value = 1.0
bsdf.inputs["Roughness"].default_value = 0.23
bpy.context.object.data.materials.append(metal)
bpy.ops.object.shade_smooth()

for loc, energy, size in [((2, -3, 4), 900, 3), ((-3, 1, 2), 750, 2)]:
    bpy.ops.object.light_add(type="AREA", location=loc)
    lamp = bpy.context.object
    lamp.data.energy = energy
    lamp.data.shape = "DISK"
    lamp.data.size = size
    aim(lamp, (0, 0, 0))

bpy.ops.object.camera_add(location=(3, -4, 3))
scene.camera = bpy.context.object
scene.camera.data.lens = 52
aim(scene.camera, (0, 0, 0))
bpy.ops.render.render(write_still=True)
