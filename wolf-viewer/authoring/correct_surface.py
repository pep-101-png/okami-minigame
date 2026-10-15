import bpy,numpy as np,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'))
coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig'];scene=bpy.context.scene;coat.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in coat.data.loop_triangles]);rest=np.array([v.co[:] for v in coat.data.vertices]);rn=np.cross(rest[tri[:,1]]-rest[tri[:,0]],rest[tri[:,2]]-rest[tri[:,0]]);ra=np.linalg.norm(rn,axis=1);names=[b.name for b in rig.pose.bones];weights=np.zeros((len(rest),len(names)))
for v in coat.data.vertices:
 for g in v.groups:
  n=coat.vertex_groups[g.group].name
  if n in names:weights[v.index,names.index(n)]=g.weight
rig.animation_data.action=bpy.data.actions['Run'];results=[];deltas=[]
for frame in range(1,49):
 scene.frame_set(frame);m=coat.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;p=np.array([v.co[:] for v in m.vertices]);mat=np.array([b.matrix@b.bone.matrix_local.inverted() for b in rig.pose.bones]);expect=np.einsum('tb,bij,tj->ti',weights[tri].mean(axis=1),mat[:,:3,:3],rn);normal=expect/(np.linalg.norm(expect,axis=1)[:,None]+1e-10);q=p.copy();valid=ra>.001
 def measure(q):
  actual=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);dot=np.einsum('ti,ti->t',actual,normal);cos=dot/(np.linalg.norm(actual,axis=1)+1e-12);return float(ra[(cos<-.1)&valid].sum()/2)
 before=measure(q)
 for iteration in range(2400):
  a,b,c=q[tri[:,0]],q[tri[:,1]],q[tri[:,2]];actual=np.cross(b-a,c-a);signed=np.einsum('ti,ti->t',actual,normal);bad=(signed<ra*.16)&valid
  if not bad.any():break
  t=tri[bad];n=normal[bad];aa,bb,cc=a[bad],b[bad],c[bad];grads=np.stack([np.cross(bb-cc,n),np.cross(cc-aa,n),np.cross(aa-bb,n)],axis=1);denom=(grads*grads).sum(axis=(1,2));lam=(ra[bad]*.16-signed[bad])/(denom+1e-9);corrections=grads*lam[:,None,None];delta=np.zeros_like(q);count=np.zeros(len(q))
  for j in range(3):np.add.at(delta,t[:,j],corrections[:,j]);np.add.at(count,t[:,j],1)
  q+=delta/np.maximum(1,count)[:,None]*.75
 after=measure(q);maxmove=float(np.linalg.norm(q-p,axis=1).max());results.append({'frame':frame,'before_area':before,'after_area':after,'max_move_m':maxmove*.34});print('UNFOLD',results[-1],flush=True)
 blend=np.einsum('vb,bij->vij',weights,mat);unskinned=np.einsum('vij,vj->vi',np.linalg.inv(blend[:,:3,:3]),q-blend[:,:3,3]);deltas.append(unskinned-rest)
np.savez_compressed(root/'review/drafts/surface.npz',delta=np.array(deltas),rest=rest,tri=tri);open(root/'review/surface-corrections.json','w').write(json.dumps(results,indent=2))
