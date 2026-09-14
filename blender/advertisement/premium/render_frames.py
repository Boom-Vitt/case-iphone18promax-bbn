"""Blender CLI render with resumable PNG output and framing assertions."""
from pathlib import Path
import json
import struct
import bpy
from mathutils import Vector

out = Path(bpy.data.filepath).parent
scene = bpy.data.scenes['BBN_Premium_Film']
bpy.context.window.scene = scene
assert (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage) == (1920, 1080, 100)
assert (scene.frame_start, scene.frame_end, scene.render.fps) == (1, 384, 24)
frames = out / 'frames'
frames.mkdir(exist_ok=True)
report = []
for frame in range(1, 385):
    scene.frame_set(frame)
    camera = scene.camera
    expected = min((frame - 1) // 96 + 1, 4)
    assert camera.name.startswith(f'{expected:02d} /'), (frame, camera.name)
    if expected != 2:
        points = []
        for obj in scene.objects['PREMIUM_CASE'].children:
            for corner in obj.bound_box:
                v = camera.matrix_world.inverted() @ obj.matrix_world @ Vector(corner)
                points.append((0.5 + v.x / camera.data.ortho_scale, 0.5 + v.y / (camera.data.ortho_scale * 1080 / 1920)))
        bounds = [min(p[0] for p in points), min(p[1] for p in points), max(p[0] for p in points), max(p[1] for p in points)]
        assert all(0.01 < x < 0.99 for x in bounds), (frame, bounds)
    dest = frames / f'{frame:04d}.png'
    if dest.exists():
        header = dest.read_bytes()[:24]
        assert header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1920, 1080), dest
    else:
        scene.render.filepath = str(dest)
        bpy.ops.render.render(write_still=True)
    if frame % 24 == 0 or frame in [1, 97, 193, 289]:
        report.append({'frame': frame, 'camera': camera.name})
        print(f'PREMIUM_RENDER {frame}/384', flush=True)
(out / 'render-validation.json').write_text(json.dumps({'status': 'PASS', 'frames': 384, 'fps': 24, 'resolution': [1920, 1080], 'camera_cuts_checked': 384, 'full_product_bounds_checked': 288, 'samples': report}, indent=2) + '\n')
scene.frame_set(1)

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
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
print('PREMIUM_RENDER COMPLETE', flush=True)
