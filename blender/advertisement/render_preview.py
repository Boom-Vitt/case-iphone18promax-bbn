import bpy
import json
scene=bpy.context.scene
print(json.dumps({'engine':scene.render.engine,'frame':scene.frame_current,'objects':len(scene.objects),'root':bpy.data.objects['CASE_TURNTABLE'].location[:]}))
scene.render.resolution_percentage=75
scene.cycles.samples=24
bpy.ops.render.render(write_still=True)
print('Preview render completed: '+scene.render.filepath)
