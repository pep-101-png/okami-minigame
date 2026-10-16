"""Compare facial and approved neck deformation on the existing native rig."""
from pathlib import Path
import bpy,numpy as np,json,math
from mathutils.bvhtree import BVHTree
from mathutils import Vector
root=Path(__file__).resolve().parents[1];draft=root/'review/drafts/head-reconstruction'
selection=np.load(draft/'head-surface.npz')['facial_mask'];neck=np.load(root/'authoring/checkpoints/neck-approved-bindings.npz')['mask']
results={}
for label,blendfile,shapefile in [('approved',root/'authoring/checkpoints/neck-approved.blend',root/'authoring/checkpoints/neck-approved-surface.npz'),('head',draft/'head-candidate.blend',draft/'head-surface.npz')]:
 bpy.ops.wm.open_mainfile(filepath=str(blendfile));o=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig'];scene=bpy.context.scene;data=np.load(shapefile);rest=data['rest'];delta=data['delta']
 o.data.calc_loop_triangles();alltri=np.array([t.vertices[:] for t in o.data.loop_triangles]);regions={'face':alltri[np.any(selection[alltri],axis=1)],'neck':alltri[np.all(neck[alltri]>.5,axis=1)]}
 references={key:np.cross(rest[t[:,1]]-rest[t[:,0]],rest[t[:,2]]-rest[t[:,0]]) for key,t in regions.items()}
 bones=list(rig.pose.bones);names=[b.name for b in bones];joint=np.zeros((len(rest),4),int);weight=np.zeros((len(rest),4))
 for v in o.data.vertices:
  for k,g in enumerate(v.groups):
   if k<4:joint[v.index,k]=names.index(o.vertex_groups[g.group].name);weight[v.index,k]=g.weight
 clips={}
 for clip,samples in [('Idle',96),('Walk',96),('Run',96),('Bark',32),('Howl',32)]:
  action=bpy.data.actions[clip];rig.animation_data.action=action;first,last=action.frame_range;worst={key:0 for key in regions};max_overlap=0
  for sample in range(samples):
   frame=first+(last-first)*sample/samples;scene.frame_set(int(frame),subframe=frame-int(frame));m=np.array([b.matrix@b.bone.matrix_local.inverted() for b in bones]);blend=np.sum(m[joint]*weight[:,:,None,None],axis=1)
   p=rest
   if clip=='Run':
    phase=((frame-first)/(last-first)*48)%48;i=int(phase);t=phase-i;p=rest+delta[i]*(1-t)+delta[(i+1)%48]*t
   q=np.einsum('vij,vj->vi',blend[:,:3,:3],p)+blend[:,:3,3];assert np.isfinite(q).all()
   for key,tri in regions.items():
    n=references[key];area=np.linalg.norm(n,axis=1);expected=np.einsum('tij,tj->ti',blend[tri,:3,:3].mean(axis=1),n);expected/=np.linalg.norm(expected,axis=1)[:,None]+1e-12
    actual=np.cross(q[tri[:,1]]-q[tri[:,0]],q[tri[:,2]]-q[tri[:,0]]);cos=np.einsum('ti,ti->t',actual,expected)/(np.linalg.norm(actual,axis=1)+1e-12)
    worst[key]=max(worst[key],int(((cos<-.1)&(area>1e-5)).sum()))
   if sample in [0,samples//4,samples//2,3*samples//4]:
    tri=regions['face'];tree=BVHTree.FromPolygons([Vector(p) for p in q],tri.tolist(),all_triangles=True,epsilon=0)
    pairs=tree.overlap(tree);overlap=sum(1 for a,b in pairs if a<b and not set(tri[a]).intersection(tri[b]));max_overlap=max(max_overlap,overlap)
  clips[clip]={'poses':samples,'worstLocalInvertedTriangles':worst,'maxNonadjacentFaceOverlapPairs':max_overlap};print(label,clip,clips[clip],flush=True)
 results[label]=clips
for clip in results['head']:
 for key in ['neck','face']:
  assert results['head'][clip]['worstLocalInvertedTriangles'][key]<=results['approved'][clip]['worstLocalInvertedTriangles'][key],(clip,key)
 assert results['head'][clip]['maxNonadjacentFaceOverlapPairs']<=results['approved'][clip]['maxNonadjacentFaceOverlapPairs'],clip
(draft/'native-pose-validation.json').write_text(json.dumps(results,indent=2)+'\n');print('HEAD_POSE_VALIDATION_PASSED',flush=True)
