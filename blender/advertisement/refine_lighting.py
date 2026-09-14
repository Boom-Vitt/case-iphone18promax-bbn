import bpy
scene=bpy.context.scene
scene.view_settings.look='AgX - Medium High Contrast'
for obj in scene.objects:
    if obj.type=='LIGHT': obj.data.energy *= 0.14
leather=bpy.data.objects['Leather case shell'].data.materials[0]
leather.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.16,0.041,0.011,1)
leather.diffuse_color=(0.16,0.041,0.011,1)
# Stronger grain catches grazing light without altering the silhouette.
leather.node_tree.nodes.get('Bump').inputs['Strength'].default_value=0.5
bpy.data.objects['Advertising portrait camera'].data.ortho_scale=0.32
# Keep offer copy below the plinth and legible against the light studio floor.
ink=bpy.data.materials.new('Offer dark ink');ink.use_nodes=True
shader=ink.node_tree.nodes.get('Principled BSDF');shader.inputs['Base Color'].default_value=(0.009,0.005,0.003,1);shader.inputs['Roughness'].default_value=1
for name,y in [('Offer',-0.133),('Footer',-0.145),('Concept note',-0.154)]:
    obj=bpy.data.objects[name];obj.location.y=y;obj.data.materials.clear();obj.data.materials.append(ink)
scene.render.resolution_percentage=75
scene.cycles.samples=32
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath='/Users/boombignose/Desktop/chatgpt101-iphone18/blender/advertisement/cognac-turntable.blend')
print('Refined exposure, leather, and typography; preview saved.')
