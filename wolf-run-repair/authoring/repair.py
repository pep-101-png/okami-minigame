"""Targeted run repair from the last shipped native scene. No gait keys changed."""
import bpy,bmesh,json,math,os,numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'wolf-motion-refinement/authoring/wolf.blend'))
coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0)
# Exact detached rear plate, identified by connected-component inspection.
bm=bmesh.new();bm.from_mesh(coat.data)
remove=[v for v in bm.verts if 2.2640<v.co.y<2.2949 and 2.5863<v.co.z<2.7603 and abs(v.co.x)<.31]
assert len(remove)==10,len(remove)
bmesh.ops.delete(bm,geom=remove,context='VERTS')
# The hip surface had very long triangles crossing a bending joint.
edges=[e for e in bm.edges if all(.6<v.co.y<2.65 and 1.45<v.co.z<3.38 for v in e.verts)]
bmesh.ops.subdivide_edges(bm,edges=edges,cuts=2,use_grid_fill=True);bm.to_mesh(coat.data);bm.free();coat.data.update()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def read(v):return {coat.vertex_groups[g.group].name:g.weight for g in v.groups}
def write(v,weights):
 top=sorted(((n,w) for n,w in weights.items() if w>1e-7),key=lambda e:-e[1])[:4];total=sum(w for _,w in top)
 for i in [g.group for g in v.groups]:coat.vertex_groups[i].remove([v.index])
 for n,w in top:coat.vertex_groups[n].add([v.index],w/total,'REPLACE')
original=[read(v) for v in coat.data.vertices]
coat.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in coat.data.loop_triangles]);rest=np.array([v.co[:] for v in coat.data.vertices]);rn=np.cross(rest[tri[:,1]]-rest[tri[:,0]],rest[tri[:,2]]-rest[tri[:,0]]);ra=np.linalg.norm(rn,axis=1);names=[b.name for b in rig.pose.bones]
def folds():
 weights=np.zeros((len(rest),len(names)))
 for v in coat.data.vertices:
  for n,w in read(v).items():
   if n in names:weights[v.index,names.index(n)]=w
 avg=weights[tri].mean(axis=1);records=[]
 rig.animation_data.action=bpy.data.actions['Run']
 for f in range(1,25):
  scene.frame_set(f);m=coat.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=np.array([v.co[:] for v in m.vertices]);mat=np.array([(b.matrix@b.bone.matrix_local.inverted()).to_3x3() for b in rig.pose.bones]);expected=np.einsum('tb,bij,tj->ti',avg,mat,rn);actual=np.cross(p[tri[:,1]]-p[tri[:,0]],p[tri[:,2]]-p[tri[:,0]]);cos=np.einsum('ti,ti->t',actual,expected)/(np.linalg.norm(actual,axis=1)*np.linalg.norm(expected,axis=1)+1e-12);bad=(cos<-.1)&(ra>.001);records.append({'frame':f,'folded_area':float(ra[bad].sum()/2),'folded_triangles':int(bad.sum())})
 return {'peak_area':max(r['folded_area'] for r in records),'total_area':sum(r['folded_area'] for r in records),'frames':records}
variants=[]
for trial,top,bottom in [(0,2.95,2.23),(1,3.20,2.0),(2,3.40,1.85),(3,3.5,1.6),(4,3.25,1.65)]:
 for v,old in zip(coat.data.vertices,original):
  x,y,z=v.co;new=old.copy()
  if .65<y<2.8 and z>1.35 and z<3.6 and not any(n.startswith('tail') and w>.01 for n,w in old.items()):
   side='L' if x>=0 else 'R'
   # Central belly remains on the torso; lateral haunch bends as a whole.
   lateral=smooth((abs(x)-.13)/.50);upper=smooth((top-z)/(top-bottom))*lateral*smooth((y-.55)/.65)
   below=smooth((2.12-z)/.8);upper=max(upper,below*sum(w for n,w in old.items() if n.startswith('hind')))
   lower=smooth((2.10-z)/.65);paw=smooth((.65-z)/.36)
   fur={n:w for n,w in old.items() if n.startswith('hindFur')};f=sum(fur.values());scale=1-f
   body={n:w for n,w in old.items() if n in ['hips','chest','body','hipsBackA','hipsBackB','chestBackA','chestBackB']};total=sum(body.values())
   if total<1e-7:body={'hips':1};total=1
   new={n:w/total*(1-upper)*scale for n,w in body.items()};new['hind'+side]=upper*(1-lower)*scale;new['hindShin'+side]=upper*lower*(1-paw)*scale;new['hindPaw'+side]=upper*lower*paw*scale;new.update(fur)
  write(v,new)
 result=folds();result.update({'trial':trial,'top':top,'bottom':bottom});variants.append(result);print('TRIAL',json.dumps({k:v for k,v in result.items() if k!='frames'}),flush=True)
 if trial==int(os.environ.get('WOLF_TRIAL','2')):
  selected=[read(v) for v in coat.data.vertices]
for v,w in zip(coat.data.vertices,selected):write(v,w)
(root/'review').mkdir(exist_ok=True);(root/'review/weight-trials.json').write_text(json.dumps(variants,indent=2))
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');coat.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/wolf.glb'),use_selection=True,export_animations=True,export_nla_strips=True,export_anim_slide_to_zero=True)
exec((root/'authoring/idle_binding.py').read_text());embed_idle_binding(root/'public/models/wolf.glb',root.parent/'wolf-animation-viewer/public/models/wolf.glb')
# Second retained binding for the approved walking display.
source=(root/'authoring/idle_binding.py').read_text().replace('embed_idle_binding','embed_walk_binding').replace('_IDLE_SKIN_','_WALK_SKIN_')
exec(source);embed_walk_binding(root/'public/models/wolf.glb',root.parent/'wolf-motion-refinement/public/models/wolf.glb')
bpy.ops.wm.save_as_mainfile(filepath=str(root/'authoring/wolf.blend'))
