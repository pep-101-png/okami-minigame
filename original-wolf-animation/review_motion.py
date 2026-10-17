"""Inspect actual evaluated Actions and render motion for human review.
Read-only with respect to the delivered Blender project and source rig.
"""
import bpy,math,json,hashlib,os
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'review'
scene=bpy.context.scene;rig=bpy.data.objects['WOLF_RIG']
if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
proof=json.loads((OUT/'authoring-validation.json').read_text())
meshes=[o for o in scene.objects if o.type=='MESH' and o.parent==rig]
footmesh=bpy.data.objects['Object_11'];feet={}
for kind in ['front','rear']:
 for side,sgn in [('L',1),('R',-1)]:
  ids=[v.index for v in footmesh.data.vertices if (footmesh.matrix_world@v.co).z<.17 and sgn*(footmesh.matrix_world@v.co).x>.25 and ((footmesh.matrix_world@v.co).y<-.9 if kind=='front' else (footmesh.matrix_world@v.co).y>1)]
  feet[kind+'.'+side]=ids

def evaluate():
 deps=bpy.context.evaluated_depsgraph_get();data={}
 for o in meshes:
  ev=o.evaluated_get(deps);me=ev.to_mesh();data[o.name]=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
 return data

saved_action=rig.animation_data.action
rig.animation_data.action=None
for p in rig.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update()
# Static pre-skin subdivision can be baked on this throwaway review copy.
# It renders identically; the delivered .blend retains editable modifiers.
for o in meshes:
 for mod in list(o.modifiers):
  if mod.type=='SUBSURF':
   bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name)
rest_geometry={};rest_edges={}
deps=bpy.context.evaluated_depsgraph_get()
for o in meshes:
 ev=o.evaluated_get(deps);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices]
 rest_geometry[o.name]=ps
 rest_edges[o.name]=[tuple(e.vertices)for e in me.edges if (ps[e.vertices[0]]-ps[e.vertices[1]]).length>.06]
 ev.to_mesh_clear()
rig.animation_data.action=saved_action
metrics={}
for name,item in proof['actions'].items():
 a=bpy.data.actions[name];rig.animation_data.action=a;n=item['frames'];edges=rest_edges
 lengths={o.name:[(rest_geometry[o.name][i]-rest_geometry[o.name][j]).length for i,j in edges[o.name]]for o in meshes}
 scene.frame_set(1);first=evaluate();scene.frame_set(n+1);last=evaluate()
 seam=max((p-q).length for obj in first for p,q in zip(first[obj],last[obj]))
 worst=[];min_floor=100;max_floor_error=0;flight=[]
 for f in range(1,n+1):
  scene.frame_set(f);data=evaluate();phase=(f-1)/n
  samples=item['samples'][f-1]['feet'];above=[]
  for key,ids in feet.items():
   z=min(data['Object_11'][i].z for i in ids);min_floor=min(min_floor,z);above.append(z>.06)
   if samples[key]['contact']:max_floor_error=max(max_floor_error,abs(z-.035))
  if all(above):flight.append(f)
  for o in meshes:
   ps=data[o.name]
   for (i,j),length in zip(edges[o.name],lengths[o.name]):
    ratio=(ps[i]-ps[j]).length/length
    if ratio<.25 or ratio>2.1:worst.append({'frame':f,'object':o.name,'edge':[i,j],'ratio':ratio})
 # Virtual ground velocity removes in-place locomotion from planted paws.
 slipping=0
 for prev,nxt in zip(item['samples'],item['samples'][1:]):
  for key in feet:
   p,q=prev['feet'][key],nxt['feet'][key]
   if p['contact'] and q['contact']:
    displacement=q['center'][1]-p['center'][1]-item['ground_speed']/60
    # Skip the phase wrap where a stance interval changes identity.
    if abs(q['idealY']-p['idealY'])<.3:slipping=max(slipping,abs(displacement))
 metrics[name]={'loop_seam_vertex_error':seam,'minimum_paw_z':min_floor,'max_contact_floor_error':max_floor_error,
                'max_stance_slip_per_frame':slipping,'flight_frames':flight,'severe_edge_samples':len(worst),
                'worst_edges':sorted(worst,key=lambda v:max(v['ratio'],1/max(.001,v['ratio'])),reverse=True)[:18]}
 print('CHECKED',name,json.dumps({k:v for k,v in metrics[name].items() if k!='worst_edges'}),flush=True)
(OUT/'motion-validation.json').write_text(json.dumps(metrics,indent=2))
if os.environ.get('ANIM_RENDER_MODE','keys')=='none':raise SystemExit

# Temporary review floor only; never save it into the delivered project.
for o in bpy.data.collections['04 · Preview studio (not part of wolf)'].objects:o.hide_set(False)
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,-.012));floor=bpy.context.object;floor.name='TEMP · moving ground for in-place contact review'
mat=bpy.data.materials.new('TEMP · neutral ground');mat.use_nodes=True;floor.data.materials.append(mat)
nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=1
geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
sub=nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';links.new(sep.outputs['Y'],sub.inputs[0])
mult=nodes.new('ShaderNodeMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=math.tau;links.new(sub.outputs[0],mult.inputs[0])
sine=nodes.new('ShaderNodeMath');sine.operation='SINE';links.new(mult.outputs[0],sine.inputs[0])
threshold=nodes.new('ShaderNodeMath');threshold.operation='GREATER_THAN';threshold.inputs[1].default_value=.987;links.new(sine.outputs[0],threshold.inputs[0])
mix=nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=(.16,.15,.14,1);mix.inputs[2].default_value=(.09,.085,.08,1);links.new(threshold.outputs[0],mix.inputs[0]);links.new(mix.outputs[0],bs.inputs['Base Color'])
scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=8
scene.render.resolution_x=768;scene.render.resolution_y=512;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';cam=scene.camera;cam.data.type='ORTHO';cam.data.ortho_scale=11.5
def camera(view):
 cam.location=(14,0,4.4)if view=='side'else(11,-10,6.4)if view=='three'else(-11,-10,6.4)
 cam.rotation_euler=(Vector((0,0,2.45))-cam.location).to_track_quat('-Z','Y').to_euler()
def render(name,f,view,path):
 scene.frame_set(int(f),subframe=f-int(f));sub.inputs[1].default_value=(f-1)/60*proof['actions'][name]['ground_speed'];camera(view);scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)

mode=os.environ.get('ANIM_RENDER_MODE','keys')
for name,item in proof['actions'].items():
 rig.animation_data.action=bpy.data.actions[name];n=item['frames'];directory=OUT/name.lower();directory.mkdir(exist_ok=True)
 if mode=='full':
  count=24 if name=='IDLE'else n//2 if name=='WALK'else n
  for i in range(count):render(name,1+n*i/count,'side',directory/f'{i:03d}.png')
 else:
  count=4 if name=='IDLE'else 12
  for i in range(count):render(name,1+n*i/count,'side',directory/f'key-{i:02d}.png')
 for i,phase in enumerate([.15,.43,.68,.92]):
  render(name,1+n*phase,'three',directory/f'three-{i}.png')
  if name=='RUN':render(name,1+n*phase,'other',directory/f'other-{i}.png')
print('MOTION_REVIEW_RENDER_COMPLETE',flush=True)
