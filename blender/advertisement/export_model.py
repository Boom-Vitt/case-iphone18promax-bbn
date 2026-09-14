import bpy
import json
from mathutils import Vector
scene=bpy.context.scene
source=bpy.data.objects['CASE_TURNTABLE']
scene.frame_set(1)
# Export copies keep the advertising scene and its animation intact.
export_root=bpy.data.objects.new('BBN_Cognac_3D',None);scene.collection.objects.link(export_root)
exported=[export_root]
for original in list(source.children):
    obj=original.copy()
    obj.data=original.data.copy()
    obj.name='GLB '+original.name
    scene.collection.objects.link(obj)
    obj.parent=export_root
    exported.append(obj)
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
    if obj.type in ['CURVE','FONT']:bpy.ops.object.convert(target='MESH')
    if obj.type=='MESH':
        for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
# Bake procedural leather grain into a portable tangent-space normal texture.
shell=bpy.data.objects.get('GLB Leather case shell')
bpy.ops.object.select_all(action='DESELECT');shell.select_set(True);bpy.context.view_layer.objects.active=shell
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(island_margin=0.025);bpy.ops.object.mode_set(mode='OBJECT')
mat=shell.data.materials[0].copy();mat.name='Cognac leather - portable PBR';shell.data.materials[0]=mat
image=bpy.data.images.new('Leather grain normal',width=1024,height=1024,alpha=False)
image.colorspace_settings.name='Non-Color'
image_node=mat.node_tree.nodes.new('ShaderNodeTexImage');image_node.image=image
mat.node_tree.nodes.active=image_node
scene.render.bake.use_selected_to_active=False
scene.cycles.samples=8
bpy.ops.object.bake(type='NORMAL')
normal=mat.node_tree.nodes.new('ShaderNodeNormalMap')
mat.node_tree.links.new(image_node.outputs['Color'],normal.inputs['Color'])
mat.node_tree.links.new(normal.outputs['Normal'],mat.node_tree.nodes.get('Principled BSDF').inputs['Normal'])
image.pack()
bpy.ops.object.select_all(action='DESELECT')
for obj in exported:obj.select_set(True)
bpy.context.view_layer.objects.active=export_root
bpy.ops.export_scene.gltf(filepath='/Users/boombignose/Desktop/chatgpt101-iphone18/public/models/cognac-case.glb',export_format='GLB',use_selection=True,use_active_scene=True,export_apply=True,export_animations=False,export_cameras=False,export_lights=False,export_materials='EXPORT',export_extras=True)
print(json.dumps({'exported_objects':len(exported),'normal_texture':[image.size[0],image.size[1]],'glb':'public/models/cognac-case.glb'}))
for obj in exported:bpy.data.objects.remove(obj,do_unlink=True)
scene.cycles.samples=32
scene.render.resolution_percentage=100
scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath='/Users/boombignose/Desktop/chatgpt101-iphone18/blender/advertisement/cognac-turntable.blend')
