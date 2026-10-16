"""Continue the saved neck repair on the accepted mesh; write review files only.

No sculpt, bake, animation regeneration or promotion to public/models is done.
The unfinished head study stays untouched in the original draft and assets.
"""
from pathlib import Path
import bpy, json, struct, hashlib, numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
root=Path(__file__).resolve().parents[1];draft=root/'review/drafts';out=draft/'neck-repair';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(draft/'run-candidate.blend'))
o=bpy.data.objects['Wolf ivory coat'];bindings=np.load(out/'neck-bindings.npz');mask=bindings['mask'];target=bindings['target'];selected=mask>1e-7
saved_weights={v.index:{o.vertex_groups[g.group].name:g.weight for g in v.groups} for v in o.data.vertices if selected[v.index]}
unfinished=np.load(out/'unfinished.npz');base=np.load(out/'accepted.npz');rest=base['rest'];delta=base['delta'].copy();delta[:,selected]=unfinished['delta'][:,selected]
bpy.ops.wm.open_mainfile(filepath=str(out/'accepted.blend'))
o=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig'];o.data.update();native=np.array([v.co[:] for v in o.data.vertices],dtype=np.float32)
assert np.array_equal(native,rest),'Native accepted snapshot differs from the accepted coordinates'
for i,row in saved_weights.items():
 v=o.data.vertices[i]
 for g in list(v.groups):o.vertex_groups[g.group].remove([i])
 for name,w in row.items():o.vertex_groups[name].add([i],w,'REPLACE')
assert np.array_equal(delta[:,~selected],base['delta'][:,~selected])
np.savez_compressed(out/'surface.npz',rest=rest,delta=delta)
# Normal targets accompany the existing repaired position targets. The
# accepted base normals/UVs/textures are retained verbatim in the GLB.
normal_base=np.empty_like(rest);o.data.vertices.foreach_get('normal',normal_base.ravel());normal_deltas=[]
# Recompute the normal on the actual skinned surface, then take it back
# through the same linear skin transform used by Three.js. Rest-space-only
# normal deltas miss the spatial gradient of the repaired skin weights.
normal_mesh=o.data.copy();bone_names=[b.name for b in rig.pose.bones];skin_joint=np.zeros((len(rest),4),dtype=int);skin_weight=np.zeros((len(rest),4))
for v in o.data.vertices:
 for j,g in enumerate(v.groups):
  if j<4:skin_joint[v.index,j]=bone_names.index(o.vertex_groups[g.group].name);skin_weight[v.index,j]=g.weight
rig.animation_data.action=bpy.data.actions['Run']
for i,change in enumerate(delta):
 bpy.context.scene.frame_set(i+1);mat=np.array([b.matrix@b.bone.matrix_local.inverted() for b in rig.pose.bones]);blend=np.sum(mat[skin_joint]*skin_weight[:,:,None,None],axis=1)
 posed=np.einsum('vij,vj->vi',blend[:,:3,:3],rest+change)+blend[:,:3,3]
 normal_mesh.vertices.foreach_set('co',posed.astype(np.float32).ravel());normal_mesh.update();normals=np.empty_like(rest);normal_mesh.vertices.foreach_get('normal',normals.ravel())
 unskinned_normals=np.einsum('vij,vj->vi',np.linalg.inv(blend[:,:3,:3]),normals)
 normal_deltas.append((unskinned_normals-normal_base)*mask[:,None])
bpy.data.meshes.remove(normal_mesh)
o.data.vertices.foreach_set('co',rest.ravel());o.data.update();rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'candidate.blend'),compress=True)

def load_glb(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return json.loads(raw[20:20+n]),bytearray(raw[28+n:])
doc,binary=load_glb(out/'baseline.glb');pr=doc['meshes'][0]['primitives'][0]
def read(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]);c={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 return np.ndarray((a['count'],c),dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',c*dt.itemsize),dt.itemsize)).copy()
def overwrite(index,array):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];dt=np.dtype({5126:'<f4',5123:'<u2',5125:'<u4',5121:'u1'}[a['componentType']]);c=array.shape[1];view=np.ndarray(array.shape,dtype=dt,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',c*dt.itemsize),dt.itemsize));view[:]=array
 if 'min' in a:a['min']=array.min(axis=0).tolist();a['max']=array.max(axis=0).tolist()
def convert(p):return np.stack([p[...,0],p[...,2],-p[...,1]],axis=-1)
kd=KDTree(len(rest))
for i,p in enumerate(convert(rest)):kd.insert(Vector(p),i)
kd.balance();mapping=[];max_distance=0
for p in read(pr['attributes']['POSITION']):
 _,i,d=kd.find(Vector(p));mapping.append(i);max_distance=max(d,max_distance)
assert max_distance<1e-6,('Accepted GLB/rest mismatch',max_distance)
mapping=np.array(mapping);region=selected[mapping];names=[doc['nodes'][n]['name'] for n in doc['skins'][0]['joints']]
for index_key,weight_key in [('JOINTS_0','WEIGHTS_0'),('_IDLE_SKIN_INDEX','_IDLE_SKIN_WEIGHT'),('_WALK_SKIN_INDEX','_WALK_SKIN_WEIGHT')]:
 ii=read(pr['attributes'][index_key]);ww=read(pr['attributes'][weight_key]);old_ii=ii.copy();old_ww=ww.copy()
 for v in np.where(region)[0]:
  native=int(mapping[v])
  if index_key=='JOINTS_0':row={names.index(n):w for n,w in saved_weights[native].items()}
  else:
   a=float(mask[native]);row={int(n):float(w)*(1-a) for n,w in zip(ii[v],ww[v]) if w>1e-8}
   for n,w in zip(['chest','neck','head'],target[native]):j=names.index(n);row[j]=row.get(j,0)+float(w)*a
  top=sorted(row.items(),key=lambda x:-x[1])[:4];total=sum(w for _,w in top);ii[v]=0;ww[v]=0
  for j,(n,w) in enumerate(top):ii[v,j]=n;ww[v,j]=w/total
 assert np.array_equal(ii[~region],old_ii[~region]) and np.array_equal(ww[~region],old_ww[~region])
 assert np.isfinite(ww).all() and abs(ww.sum(axis=1)-1).max()<1e-5
 overwrite(pr['attributes'][index_key],ii);overwrite(pr['attributes'][weight_key],ww)
def add_view(array):
 while len(binary)%4:binary.append(0)
 view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':array.nbytes});binary.extend(array.tobytes());return view
for key,change,normal_change in zip(pr['targets'],delta,normal_deltas):
 previous=read(key['POSITION']);values=previous.copy();values[region]=convert(change)[mapping[region]];overwrite(key['POSITION'],values)
 normals=convert(normal_change)[mapping];ids=np.where(region & (np.linalg.norm(normals,axis=1)>1e-6))[0]
 if not len(ids):ids=np.array([0])
 iv=add_view(np.asarray(ids,dtype='<u4'));vv=add_view(np.asarray(normals[ids],dtype='<f4'));idx=len(doc['accessors']);doc['accessors'].append({'componentType':5126,'count':len(mapping),'type':'VEC3','sparse':{'count':len(ids),'indices':{'bufferView':iv,'componentType':5125},'values':{'bufferView':vv}}});key['NORMAL']=idx
while len(binary)%4:binary.append(0)
doc['buffers'][0]['byteLength']=len(binary);encoded=json.dumps(doc,separators=(',',':')).encode()
while len(encoded)%4:encoded+=b' '
(out/'wolf.glb').write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)
report={'baselineCommit':'2ba1f2b7f829145334a261f7a0fc36d80f39b29e','baselineSHA256':hashlib.sha256((out/'baseline.glb').read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256((out/'wolf.glb').read_bytes()).hexdigest(),'nativeRestVertices':len(rest),'renderVertices':len(mapping),'changedNativeBindingVertices':int(selected.sum()),'acceptedRestMaxChange':0,'acceptedPositionNormalsUVTexturesAndClips':'Retained from baseline binary; only neck skin bindings and neck corrective targets changed.','protectedBindingsAndMorphsUnchanged':True,'normalTargets':len(normal_deltas),'normalCorrectionSpace':'Actual skinned Run surface, inverse skin transformed for portable GLB normal morphs','unfinishedHeadStudyPreserved':True}
(root/'review/neck-repair').mkdir(parents=True,exist_ok=True);(root/'review/neck-repair/preservation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
