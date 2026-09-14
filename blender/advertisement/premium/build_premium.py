"""Run inside Blender with the existing cognac-turntable.blend open.
Creates a separate premium scene; the original scene and model stay intact.
"""
import bpy
import math
import json
from mathutils import Vector

SOURCE = bpy.data.scenes['BBN_Cognac_Advertisement']
OUT = bpy.path.abspath('//premium/')
assert not bpy.data.scenes.get('BBN_Premium_Film'), 'Premium scene already exists; open the original blend to rebuild.'
scene = bpy.data.scenes.new('BBN_Premium_Film')
bpy.context.window.scene = scene
scene['design_status'] = 'iPhone 18 Pro Max advertising concept; approximate geometry, not manufacturing CAD.'
scene['authoring'] = 'Created through official Blender MCP; existing BBN model reused and refined.'
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.taa_render_samples = 128
scene.eevee.shadow_ray_count = 3
scene.eevee.use_raytracing = True
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = 0.04
scene.cycles.max_bounces = 5
scene.render.use_persistent_data = True
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 384
scene.render.image_settings.file_format = 'PNG'
scene.render.image_settings.color_mode = 'RGB'
scene.render.film_transparent = False
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.world = bpy.data.worlds.new('Premium charcoal environment')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.06, 0.07, 0.085, 1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.18

root = bpy.data.objects.new('PREMIUM_CASE', None)
scene.collection.objects.link(root)
root.location = (0, 0, 0.125)
parts = {}
for original in SOURCE.objects['CASE_TURNTABLE'].children:
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = 'Premium ' + original.name
    scene.collection.objects.link(obj)
    obj.parent = root
    obj.animation_data_clear()
    parts[original.name] = obj

# Preserve the shell geometry and refine its procedural, millimetre-scale grain.
shell = parts['Leather case shell']
leather = shell.data.materials[0].copy()
leather.name = 'Premium tobacco cognac leather'
shell.data.materials[0] = leather
nodes, links = leather.node_tree.nodes, leather.node_tree.links
shader = nodes.get('Principled BSDF')
shader.inputs['Base Color'].default_value = (0.105, 0.029, 0.009, 1)
shader.inputs['Roughness'].default_value = 0.43
shader.inputs['Coat Weight'].default_value = 0.10
shader.inputs['Coat Roughness'].default_value = 0.4
noise = nodes.get('Noise Texture')
noise.inputs['Scale'].default_value = 2600
noise.inputs['Detail'].default_value = 3.4
bump = nodes.get('Bump')
bump.inputs['Strength'].default_value = 0.65
bump.inputs['Distance'].default_value = 0.00016
pores = nodes.new('ShaderNodeTexVoronoi')
pores.feature = 'DISTANCE_TO_EDGE'
pores.inputs['Scale'].default_value = 3600
links.new(nodes.get('Texture Coordinate').outputs['Object'], pores.inputs['Vector'])
fine = nodes.new('ShaderNodeBump')
fine.inputs['Strength'].default_value = 0.22
fine.inputs['Distance'].default_value = 0.000075
links.new(pores.outputs['Distance'], fine.inputs['Height'])
links.new(bump.outputs['Normal'], fine.inputs['Normal'])
links.new(fine.outputs['Normal'], shader.inputs['Normal'])
leather.diffuse_color = (0.105, 0.029, 0.009, 1)

island = parts['Wide camera plateau']
island_material = island.data.materials[0].copy()
island.data.materials[0] = island_material
island_shader = island_material.node_tree.nodes['Principled BSDF']
island_shader.inputs['Roughness'].default_value = 0.4
island_shader.inputs['Metallic'].default_value = 0.15
island_shader.inputs['Specular IOR Level'].default_value = 0.22

# Avoid coplanar lettering and preserve separate editable components.
for name in ['Embossed bbn wordmark', 'Atelier hallmark', 'Small batch hallmark']:
    parts[name].location.y -= 0.00012


def material(name, color, roughness, metallic=0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = roughness
    bsdf.inputs['Metallic'].default_value = metallic
    return mat


stone = material('Smoked basalt', (0.012, 0.014, 0.017), 0.30, 0.22)
gold = material('Satin champagne accent', (0.30, 0.17, 0.065), 0.28, 0.80)
for name in ['Warm stone plinth', 'Studio floor']:
    original = SOURCE.objects[name]
    obj = original.copy()
    obj.data = original.data.copy()
    obj.name = 'Premium ' + name
    scene.collection.objects.link(obj)
    obj.data.materials.clear()
    obj.data.materials.append(stone)
# Fine metal inlay catches a single highlight under the floating product.
bpy.ops.mesh.primitive_torus_add(major_segments=128, minor_segments=12, major_radius=0.0688, minor_radius=0.00032, location=(0, 0, 0.011))
bpy.context.object.name = 'Champagne plinth inlay'
bpy.context.object.data.materials.append(gold)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def area(name, location, energy, color, size, target, size_y=None):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy, data.color, data.size = energy, color, size
    data.shape = 'RECTANGLE' if size_y else 'DISK'
    if size_y:
        data.size_y = size_y
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = location
    point_at(obj, target)
    return obj


area('Premium warm key', (-0.18, -0.23, 0.30), 1.7, (1.0, 0.83, 0.64), 0.17, (0, 0, 0.13), 0.26)
area('Premium silver rim', (0.15, 0.055, 0.24), 3.0, (0.73, 0.84, 1.0), 0.065, (0, 0, 0.14), 0.26)
area('Premium front silk', (0.08, -0.21, 0.12), 0.38, (1.0, 0.94, 0.86), 0.12, (0, 0, 0.14))
area('Premium top strip', (-0.015, 0.02, 0.32), 1.3, (1.0, 0.70, 0.38), 0.13, (0, 0, 0.12), 0.025)
area('Premium ground halo', (0, 0.17, 0.20), 1.8, (0.70, 0.48, 0.27), 0.18, (0, 0, 0))

# Four camera cuts. All movement is keyed in the .blend, with no handlers/drivers.
shots = [
    ('01 / SILHOUETTE', 1, 96, (0, -0.52, 0.245), (-0.055, 0, 0.112), 0.45235, (-37, -10)),
    ('02 / CAMERA DETAIL', 97, 192, (-0.035, -0.32, 0.235), (0.010, -0.008, 0.174), 0.175, (-8, 13)),
    ('03 / EVERY ANGLE', 193, 288, (0, -0.50, 0.24), (0, 0, 0.112), 0.45235, (-18, 342)),
    ('04 / THE COGNAC EDIT', 289, 384, (0, -0.52, 0.23), (-0.050, 0, 0.112), 0.46325, (-32, -20)),
]
cameras = []
for name, start, end, location, target, scale, angles in shots:
    data = bpy.data.cameras.new(name)
    data.type, data.ortho_scale = 'ORTHO', scale
    data.clip_start, data.clip_end = 0.001, 20
    cam = bpy.data.objects.new(name, data)
    scene.collection.objects.link(cam)
    cam.location = location
    point_at(cam, target)
    marker = scene.timeline_markers.new(name, frame=start)
    marker.camera = cam
    cameras.append(cam)
    for frame in range(start, end + 1):
        t = (frame - start) / (end - start)
        eased = t * t * (3 - 2 * t)
        # Constant speed in the orbit; eased dolly/rotation on the detail shots.
        amount = t if start == 193 else eased
        root.rotation_euler = (math.radians(5), math.radians(-7), math.radians(angles[0] + (angles[1] - angles[0]) * amount))
        root.keyframe_insert(data_path='rotation_euler', frame=frame)
        data.ortho_scale = scale * (1 - 0.035 * eased)
        data.keyframe_insert(data_path='ortho_scale', frame=frame)

# Camera-local emission typography. Bfont is embedded by Blender, no font downloads.
ivory = bpy.data.materials.new('Premium ivory typography')
ivory.use_nodes = True
nt = ivory.node_tree
nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial')
emission = nt.nodes.new('ShaderNodeEmission')
emission.inputs['Color'].default_value = (0.71, 0.60, 0.44, 1)
emission.inputs['Strength'].default_value = 1
nt.links.new(emission.outputs[0], out.inputs['Surface'])


def title(cam, body, size, x, y, spacing=1.05):
    data = bpy.data.curves.new(body, 'FONT')
    data.body, data.size, data.space_character = body, size, spacing
    data.align_x = 'LEFT'
    obj = bpy.data.objects.new('Type ' + body, data)
    scene.collection.objects.link(obj)
    obj.parent, obj.location = cam, (x, y, -0.15)
    obj.data.materials.append(ivory)
    # Only show the typography belonging to the active shot.
    for name, start, end, *_ in shots:
        for frame in [start, end]:
            obj.hide_render = cam.name != name
            obj.keyframe_insert(data_path='hide_render', frame=frame)
    return obj


for cam, shot in zip(cameras, shots):
    scale = shot[5] / (1.09 if shot[1] != 97 else 1)
    title(cam, 'B B N   /   C A S E   A T E L I E R', scale * 0.009, -scale * 0.44, scale * 0.231)
    title(cam, 'iPhone 18 Pro Max  /  Design concept', scale * 0.0063, -scale * 0.44, -scale * 0.238)
title(cameras[0], 'COGNAC', 0.018, -0.181, 0.021, 1.1)
title(cameras[0], 'N O .  0 1', 0.0065, -0.179, 0.001)
title(cameras[0], 'A warmer kind of luxury.', 0.0044, -0.180, -0.025)
title(cameras[1], 'FORM.  FINISH.  DETAIL.', 0.0030, -0.076, -0.032)
title(cameras[2], 'EVERY ANGLE.', 0.007, -0.181, 0.073)
title(cameras[3], 'THE\nCOGNAC\nEDIT.', 0.020, -0.186, 0.039, 1.03)
title(cameras[3], 'Leather. Light. Character.', 0.0045, -0.184, -0.045)

# render_frames.py checks every camera cut and full-product frame before rendering.
scene.camera = cameras[0]
scene.frame_set(1)
scene.render.filepath = '//frames/'

# Open the deliverable directly in camera view, with the case assembly selected.
bpy.ops.object.select_all(action='DESELECT')
scene.objects['PREMIUM_CASE'].select_set(True)
bpy.context.view_layer.objects.active = scene.objects['PREMIUM_CASE']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_perspective = 'CAMERA'
            area.spaces.active.overlay.show_extras = False
scene.render.filepath = '//frames/'
bpy.ops.wm.save_as_mainfile(filepath=OUT + 'iphone18-pro-max-premium.blend')
print(json.dumps({'scene': scene.name, 'model_parts': len(parts), 'cameras': len(cameras), 'frames': [1, 384], 'resolution': [1920, 1080], 'blend': bpy.data.filepath}))
