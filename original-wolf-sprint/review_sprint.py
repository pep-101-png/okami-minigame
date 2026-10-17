"""Read-only evaluated-mesh and frame-by-frame render review of the refined Run."""
import bpy,math,json,os
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'review'/os.environ.get('REVIEW_DIR','final');OUT.mkdir(exist_ok=True);s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];r.animation_data.action=None
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for p in r.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update()
meshes=[o for o in s.objects if o.type=='MESH'and o.parent==r]
for o in meshes:
 for m in list(o.modifiers):
  if m.type=='SUBSURF':bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
def evaluate():
 dep=bpy.context.evaluated_depsgraph_get();out={}
 for o in meshes:
  ev=o.evaluated_get(dep);me=ev.to_mesh();out[o.name]=[ev.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear()
 return out
rest=evaluate();edges={o.name:[tuple(e.vertices)for e in o.data.edges if(rest[o.name][e.vertices[0]]-rest[o.name][e.vertices[1]]).length>.06]for o in meshes}
metrics={}
for name in ['Jog','Sprint']:
 n=40 if name=='Jog' else 32
 r.animation_data.action=bpy.data.actions[name];s.frame_set(1);first=evaluate();s.frame_set(n+1);last=evaluate();loop=max((p-q).length for n in first for p,q in zip(first[n],last[n]));rows=[];folds=[]
 for f in range(1,4*n+2):
  fr=1+(f-1)/4;s.frame_set(int(fr),subframe=fr-int(fr));row={'frame':fr,'bones':{}}
  for key in ['rear.L','rear.R','front.L','front.R']:
   u=r.pose.bones['DEF_'+key.split('.')[0]+'_upper.'+key[-1]];l=r.pose.bones['DEF_'+key.split('.')[0]+'_lower.'+key[-1]]
   row['bones'][key]={'q':list(u.matrix.to_quaternion()),'bend':math.degrees((u.tail-u.head).angle(l.tail-l.head)),'ik':(l.tail-r.pose.bones['MCH_target_'+key].head).length,'knee_above_hip':u.tail.z-u.head.z}
  row['spine']={n:list(r.pose.bones['DEF_'+n].head)for n in ['hips','spine_mid','chest','neck_base','head']};rows.append(row)
  if f%4==1:
   data=evaluate()
   for n in ['Object_6','Object_2']:
    for i,j in edges[n]:
     ratio=(data[n][i]-data[n][j]).length/(rest[n][i]-rest[n][j]).length
     if ratio<.25:folds.append({'object':n,'frame':fr,'edge':[i,j],'ratio':ratio})
 jump={}
 for key in ['rear.L','rear.R']:
  values=[math.degrees(2*math.acos(min(1,abs(sum(a*b for a,b in zip(x['bones'][key]['q'],y['bones'][key]['q']))))))for x,y in zip(rows,rows[1:])];jump[key]=max(values)
 metrics[name]={'loop_vertex_error':loop,'max_ik_error':max(d['ik']for row in rows for d in row['bones'].values()),'max_rear_bend':max(row['bones'][k]['bend']for row in rows for k in ['rear.L','rear.R']),'max_knee_above_hip':max(row['bones'][k]['knee_above_hip']for row in rows for k in ['rear.L','rear.R']),'max_quarterframe_joint_rotation':jump,'collapsed_edges':len(folds),'worst_edges':sorted(folds,key=lambda x:x['ratio'])[:15],'frames':rows}
 print('REVIEW_METRICS',name,{k:v for k,v in metrics[name].items()if k not in ['frames','worst_edges']},flush=True)
(OUT/'evaluated.json').write_text(json.dumps(metrics,indent=2))
if os.environ.get('RENDER_MODE')=='none':raise SystemExit
for o in bpy.data.collections['04 · Preview studio (not part of wolf)'].objects:o.hide_set(False)
bpy.ops.mesh.primitive_plane_add(size=20,location=(0,0,-.012));floor=bpy.context.object
mat=bpy.data.materials.new('TEMP neutral ground');mat.diffuse_color=(.17,.16,.15,1);floor.data.materials.append(mat)
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=12;s.render.resolution_x=840;s.render.resolution_y=600;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';c=s.camera;c.data.type='ORTHO'
full=os.environ.get('RENDER_MODE')=='full';r.animation_data.action=bpy.data.actions['Sprint']
for view,loc,target,scale in [('side',(14,0,4.4),(0,0,2.45),11.5),('front',(0,-14,4.5),(0,-.5,2.65),9.6),('rear',(0,14,4.5),(0,.5,2.65),9.6),('hip',(9,4.5,3.8),(0,1.2,2),5.4)]:
 c.location=loc;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();c.data.ortho_scale=scale
 directory=OUT/view;directory.mkdir(exist_ok=True)
 keys=[1,5,9,13,17,21,25,29]
 frames=(keys+[i for i in range(1,33)if i not in keys])if full and view!='hip'else keys
 for f in frames:
  s.frame_set(f);s.render.filepath=str(directory/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
print('REVIEW_RENDER_COMPLETE',flush=True)
