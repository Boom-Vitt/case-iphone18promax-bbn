# Executed inside Blender by the official Blender MCP execute_blender_code tool.
import bpy
import math
import json
from mathutils import Vector

ROOT = '/Users/boombignose/Desktop/chatgpt101-iphone18'
previous = bpy.data.scenes.get('BBN_Cognac_Advertisement')
if previous:
    for obj in list(previous.objects): bpy.data.objects.remove(obj,do_unlink=True)
    bpy.data.scenes.remove(previous)
scene = bpy.data.scenes.new('BBN_Cognac_Advertisement')
bpy.context.window.scene = scene
scene['bbn_project_root'] = ROOT
scene['creation_method'] = 'Official Blender MCP execute_blender_code; safe mode enabled'
scene['design_status'] = 'Advertising concept. Approximate dimensions, not manufacturing CAD.'
scene.unit_settings.system = 'METRIC'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 720
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = 'PNG'
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 192
scene.world = bpy.data.worlds.new('Warm studio world')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (0.18,0.15,0.12,1)
scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.25
scene.view_settings.view_transform = 'AgX'

root = bpy.data.objects.new('CASE_TURNTABLE', None)
scene.collection.objects.link(root)
root.location = (0,0,0.125)
root['rotation_axis'] = 'Z up; full 360 degrees in 8 seconds'

# All shape arguments below are in millimetres, converted to metre geometry.
def material(name, color, rough=0.4, metal=0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color,1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color,1)
    shader.inputs['Roughness'].default_value = rough
    shader.inputs['Metallic'].default_value = metal
    return mat

leather = material('Cognac full-grain leather', (0.24,0.078,0.028),0.48)
nodes = leather.node_tree.nodes
noise = nodes.new('ShaderNodeTexNoise')
noise.inputs['Scale'].default_value=1800
noise.inputs['Detail'].default_value=2.6
noise.inputs['Roughness'].default_value=0.75
coord=nodes.new('ShaderNodeTexCoord')
leather.node_tree.links.new(coord.outputs['Object'],noise.inputs['Vector'])
bump=nodes.new('ShaderNodeBump')
bump.inputs['Strength'].default_value=0.32
bump.inputs['Distance'].default_value=0.00022
leather.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
leather.node_tree.links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
edge = material('Burnished leather edges',(0.105,0.029,0.013),0.38)
stitch = material('Warm linen saddle stitch',(0.60,0.38,0.18),0.75)
metal = material('Brushed champagne metal',(0.34,0.24,0.13),0.25,0.85)
phone = material('Graphite titanium',(0.038,0.043,0.045),0.30,0.78)
plate = material('Graphite camera island',(0.022,0.027,0.030),0.24,0.35)
glass = material('Sapphire lens glass',(0.006,0.018,0.032),0.095,0.45)
black = material('Optical black',(0.002,0.003,0.004),0.22)
flash = material('Flash diffuser',(0.75,0.70,0.53),0.3)
screen = material('Front obsidian glass',(0.004,0.007,0.010),0.17,0.35)

# Rounded rectangle in X/Z with 12 segments per quarter.
def outline(w,h,r):
    points=[]
    for cx,cz,start in [(w/2-r,h/2-r,0),(-w/2+r,h/2-r,90),(-w/2+r,-h/2+r,180),(w/2-r,-h/2+r,270)]:
        for i in range(13):
            a=math.radians(start+i*90/12)
            points.append(((cx+r*math.cos(a))/1000,(cz+r*math.sin(a))/1000))
    return points

def extrude(name,w,h,r,depth,location,mat,bevel=0.25,parent=True):
    path=outline(w,h,r)
    n=len(path)
    vertices=[(x,-depth/2000,z) for x,z in path]+[(x,depth/2000,z) for x,z in path]
    faces=[tuple(range(n)),tuple(reversed(range(n,2*n)))]
    for i in range(n):
        j=(i+1)%n
        faces.append((i,n+i,n+j,j))
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj=bpy.data.objects.new(name,mesh)
    scene.collection.objects.link(obj)
    obj.location=tuple(v/1000 for v in location)
    if parent: obj.parent=root
    if mat: obj.data.materials.append(mat)
    if bevel:
        mod=obj.modifiers.new('Soft edge highlights','BEVEL');mod.width=bevel/1000;mod.segments=3
        mod=obj.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return obj

def difference(target,cutter):
    bpy.context.view_layer.objects.active=target
    modifier=target.modifiers.new('True opening','BOOLEAN')
    modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
    while target.modifiers[0] != modifier: bpy.ops.object.modifier_move_up(modifier=modifier.name)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(cutter,do_unlink=True)

shell=extrude('Leather case shell',82,171,10,13,(0,0,0),leather,0)
inner=extrude('Temporary interior cavity',78,167,8.5,18,(0,4,0),None,0)
difference(shell,inner)
cutout=extrude('Temporary camera cutout',72.5,42,8,14,(0,-7,59),None,0)
difference(shell,cutout)
bevel=shell.modifiers.new('Hand finished edge','BEVEL');bevel.width=0.0004;bevel.segments=3
shell.modifiers.new('Soft normals','WEIGHTED_NORMAL')
# The rounded raised rim is an actual hollow ring.
rim=extrude('Raised leather camera surround',76,46,10,3.6,(0,-7.0,59),edge,0)
cutout=extrude('Temporary rim hole',72,42,8,10,(0,-7,59),None,0)
difference(rim,cutout)
bevel=rim.modifiers.new('Rounded camera rim','BEVEL');bevel.width=0.00055;bevel.segments=4
rim.modifiers.new('Camera rim normals','WEIGHTED_NORMAL')
body=extrude('Reference handset',77.7,166.7,8.3,9.5,(0,0.5,0),phone,0.35)
front=extrude('Front glass',75.4,164.4,8.0,0.6,(0,5.5,0),screen,0.25)
island=extrude('Wide camera plateau',71.5,41.5,8,2.5,(0,-6.6,59),plate,0.5)

def cylinder(name,radius,depth,location,mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=radius/1000,depth=depth/1000,location=(0,0,0))
    obj=bpy.context.object;obj.name=name;obj.parent=root
    obj.location=tuple(v/1000 for v in location)
    obj.rotation_euler=(math.pi/2,0,0)
    obj.data.materials.append(mat)
    bevel=obj.modifiers.new('Polished edge','BEVEL');bevel.width=0.00018;bevel.segments=3
    obj.modifiers.new('Optical normals','WEIGHTED_NORMAL')
    return obj

for index,(x,z) in enumerate([(-23,69),(-23,49),(-4,59)]):
    cylinder('Lens %d metal ring'%(index+1),8.6,2.5,(x,-9,z),phone)
    cylinder('Lens %d black gasket'%(index+1),7.5,0.5,(x,-10.4,z),black)
    cylinder('Lens %d sapphire'%(index+1),6.5,0.35,(x,-10.7,z),glass)
    cylinder('Lens %d inner optic'%(index+1),3.0,0.1,(x,-10.9,z),black)
    cylinder('Lens %d blue coating'%(index+1),1.55,0.08,(x-0.6,-11,z+0.5),glass)
cylinder('True Tone flash',3.1,0.5,(23,-8.2,69),flash)
cylinder('LiDAR sensor',3.3,0.5,(23,-8.2,49),black)
cylinder('Camera microphone',0.65,0.5,(23,-8.2,59),black)

# Button caps, camera-control recess and USB-C aperture.
for name,x,z,h in [('Power key',40.8,22,17),('Volume up',-40.8,26,12),('Volume down',-40.8,9,12),('Action key',-40.8,48,7)]:
    obj=extrude(name,2.0,h,0.8,3.5,(x,1,z),metal,0.3)
button=extrude('Camera control inset',2,20,0.8,4,(40.8,1,-43),black,0.2)
usb=extrude('Temporary USB-C opening',13,5,2,8,(0,1,-84),None,0)
# Rotate cutter so the opening exits through the bottom wall along Z.
usb.rotation_euler=(math.pi/2,0,0)
difference(shell,usb)
for x in [-26,-22,-18,18,22,26]:
    bpy.ops.mesh.primitive_cylinder_add(vertices=16,radius=0.0008,depth=0.006,location=(0,0,0))
    vent=bpy.context.object;vent.name='Temporary speaker port';vent.parent=root;vent.location=(x/1000,0.001,-0.085)
    difference(shell,vent)

# One curve object contains all individual stitches: lightweight actual geometry.
curve=bpy.data.curves.new('Saddle stitch paths','CURVE');curve.dimensions='3D';curve.resolution_u=1;curve.bevel_depth=0.00019;curve.bevel_resolution=2
path=outline(75,112,7)
# Stitch path runs below the camera housing.
shift=-24
lengths=[0]
for i in range(len(path)):
    a=path[i];b=path[(i+1)%len(path)];lengths.append(lengths[-1]+math.hypot(b[0]-a[0],b[1]-a[1]))
perimeter=lengths[-1]
for distance in [i*0.0032 for i in range(int(perimeter/0.0032))]:
    points=[]
    for d in [distance,distance+0.00165]:
        k=0
        while k<len(path)-1 and lengths[k+1]<d:k+=1
        t=(d-lengths[k])/(lengths[k+1]-lengths[k]);a=path[k];b=path[(k+1)%len(path)]
        points.append((a[0]+(b[0]-a[0])*t,-0.0067,a[1]+(b[1]-a[1])*t+shift/1000,1))
    spline=curve.splines.new('POLY');spline.points.add(1)
    for index,point in enumerate(points):spline.points[index].co=point
seams=bpy.data.objects.new('Hand sewn linen stitching',curve);scene.collection.objects.link(seams);seams.parent=root;seams.data.materials.append(stitch)

def label(name,body,size,location,mat):
    data=bpy.data.curves.new(name,'FONT');data.body=body;data.align_x='CENTER';data.size=size/1000;data.extrude=0.000035;data.bevel_depth=0.000015
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.parent=root;obj.location=tuple(v/1000 for v in location);obj.rotation_euler=(math.pi/2,0,0);obj.data.materials.append(mat)
    return obj
label('Embossed bbn wordmark','bbn',8.0,(0,-6.9,-47),metal)
label('Atelier hallmark','LEATHER ATELIER',1.8,(0,-6.85,-54),stitch)
label('Small batch hallmark','01 / COGNAC',1.7,(0,-6.85,-69),stitch)

# A constant-speed loop with a duplicated endpoint at frame 193.
root.rotation_euler=(math.radians(7),math.radians(-9),math.radians(-22))
root.keyframe_insert(data_path='rotation_euler',frame=1)
root.rotation_euler.z=math.radians(338)
root.keyframe_insert(data_path='rotation_euler',frame=193)
action=root.animation_data.action
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for fcurve in bag.fcurves:
                for key in fcurve.keyframe_points:key.interpolation='LINEAR'
scene.frame_set(1)

# Studio pedestal and seamless background.
stage=material('Ivory travertine',(0.44,0.36,0.27),0.68)
bpy.ops.mesh.primitive_cylinder_add(vertices=128,radius=0.070,depth=0.014,location=(0,0,0.007))
pedestal=bpy.context.object;pedestal.name='Warm stone plinth';pedestal.data.materials.append(stage)
bevel=pedestal.modifiers.new('Plinth edge','BEVEL');bevel.width=0.002;bevel.segments=4
pedestal.modifiers.new('Plinth normals','WEIGHTED_NORMAL')
floor=material('Warm seamless',(0.055,0.040,0.030),0.72)
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-0.001))
bpy.context.object.name='Studio floor';bpy.context.object.data.materials.append(floor)

def point_at(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
def area(name,location,energy,color,size,target):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.color=color;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=location;point_at(obj,target)
area('Key softbox',(-0.15,-0.22,0.30),16,(1.0,0.83,0.67),0.22,(0,0,0.12))
area('Cool contour',(0.18,0.07,0.22),24,(0.75,0.85,1.0),0.18,(0,0,0.13))
area('Front fill',(0.1,-0.22,0.10),4,(1.0,0.94,0.85),0.15,(0,0,0.12))
area('Top ribbon',(-0.02,0.02,0.38),12,(1.0,0.75,0.45),0.12,(0,0,0.12))
cam_data=bpy.data.cameras.new('Advertising portrait camera');cam=bpy.data.objects.new('Advertising portrait camera',cam_data);scene.collection.objects.link(cam)
cam.location=(0,-0.46,0.23);point_at(cam,(0,0,0.128));cam_data.type='ORTHO';cam_data.ortho_scale=0.30;scene.camera=cam
# Camera-parented typography remains readable through the turntable.
white=material('Title ivory',(0.82,0.73,0.59),0.5)
shader=white.node_tree.nodes.get('Principled BSDF');shader.inputs['Emission Color'].default_value=(0.82,0.73,0.59,1);shader.inputs['Emission Strength'].default_value=1
for name,body,size,x,y in [('Brand title','bbn / CASE ATELIER',0.006,0,0.124),('Collection title','THE COGNAC EDIT',0.009,0,0.108),('Offer','1,090 THB  /  FREE DELIVERY',0.006,0,-0.111),('Footer','PRE-ORDER   •   iPHONE 18 PRO MAX',0.0035,0,-0.122),('Concept note','3D DESIGN CONCEPT',0.0025,0,-0.133)]:
    data=bpy.data.curves.new(name,'FONT');data.body=body;data.align_x='CENTER';data.size=size
    obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.parent=cam;obj.location=(x,y,-0.4);obj.data.materials.append(white)
scene.render.filepath=ROOT+'/blender/advertisement/hero.png'
bpy.ops.wm.save_as_mainfile(filepath=ROOT+'/blender/advertisement/cognac-turntable.blend')
print(json.dumps({'scene':scene.name,'objects':len(scene.objects),'case_mesh':shell.name,'frames':[scene.frame_start,scene.frame_end],'fps':scene.render.fps,'saved':bpy.data.filepath}))
