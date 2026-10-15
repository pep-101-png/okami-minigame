"""Bake run-only surface corrections into a portable GLB (no runtime solver)."""
import bpy,numpy as np,json,struct,os
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'))
coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig'];scene=bpy.context.scene
archive=np.load(root/'review/drafts/surface.npz');delta=archive['delta'];rest=archive['rest']
if os.environ.get('WOLF_RAW_PREVIEW'):delta=np.zeros_like(delta)
coat.shape_key_add(name='Basis')
for i,change in enumerate(delta):
 key=coat.shape_key_add(name=f'RunSurface{i+1:02}');key.data.foreach_set('co',(rest+change).astype(np.float32).ravel())
 for frame in range(1,50):key.value=1.0 if (frame-1)%48==i else 0.0;key.keyframe_insert('value',frame=frame)
 key.value=0
keys=coat.data.shape_keys;keys.animation_data.action.name='Run surface correctives';keys.animation_data.action.use_fake_user=True
for f in keys.animation_data.action.fcurves:
 for k in f.keyframe_points:k.interpolation='LINEAR'
keys.animation_data.action=None
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');coat.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
asset=root/'public/models/wolf.glb'
bpy.ops.export_scene.gltf(filepath=str(asset),use_selection=True,export_animations=True,export_nla_strips=True,export_anim_slide_to_zero=True,export_morph=False)
exec((root/'authoring/idle_binding.py').read_text());embed_idle_binding(asset,root.parent/'wolf-animation-viewer/public/models/wolf.glb')
exec((root/'authoring/idle_binding.py').read_text().replace('embed_idle_binding','embed_walk_binding').replace('_IDLE_SKIN_','_WALK_SKIN_'));embed_walk_binding(asset,root.parent/'wolf-motion-refinement/public/models/wolf.glb')
doc,binary=read_glb(asset);primitive=doc['meshes'][0]['primitives'][0];positions=accessor(doc,binary,primitive['attributes']['POSITION']);kd=KDTree(len(rest))
def convert(v):return np.stack([v[...,0],v[...,2],-v[...,1]],axis=-1)
for i,p in enumerate(convert(rest)):kd.insert(Vector(p),i)
kd.balance();mapping=[]
for p in positions:
 _,index,d=kd.find(Vector(p));assert d<1e-4,d;mapping.append(index)
def append(array,kind='VEC3'):
 array=np.asarray(array,dtype='<f4');array=array.reshape(-1,{'VEC3':3,'SCALAR':1}[kind])
 while len(binary)%4:binary.append(0)
 view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':array.nbytes});binary.extend(array.tobytes());index=len(doc['accessors']);doc['accessors'].append({'bufferView':view,'componentType':5126,'count':len(array),'type':kind,'min':array.min(axis=0).tolist(),'max':array.max(axis=0).tolist()});return index
def patch_tail_binding(index_name,weight_name):
 indices=accessor(doc,binary,primitive['attributes'][index_name]);weights=accessor(doc,binary,primitive['attributes'][weight_name]);normal_i=accessor(doc,binary,primitive['attributes']['JOINTS_0']);normal_w=accessor(doc,binary,primitive['attributes']['WEIGHTS_0']);names=[doc['nodes'][n]['name'] for n in doc['skins'][0]['joints']]
 for v in range(len(indices)):
  retained={};amount=0
  for n,w in zip(indices[v],weights[v]):
   if names[int(n)].startswith('tail'):amount+=w
   else:retained[int(n)]=retained.get(int(n),0)+w
  if amount<1e-8:continue
  plume=[(int(n),w) for n,w in zip(normal_i[v],normal_w[v]) if names[int(n)].startswith('plume') and w>1e-8];total=sum(w for n,w in plume)
  if not plume:plume=[(names.index('plume00'),1)];total=1
  for n,w in plume:retained[n]=retained.get(n,0)+amount*w/total
  top=sorted(retained.items(),key=lambda p:-p[1])[:4];total=sum(w for n,w in top);indices[v]=0;weights[v]=0
  for j,(n,w) in enumerate(top):indices[v,j]=n;weights[v,j]=w/total
 for attr,arr in [(index_name,indices),(weight_name,weights)]:
  a=doc['accessors'][primitive['attributes'][attr]];view=doc['bufferViews'][a['bufferView']];offset=view.get('byteOffset',0)+a.get('byteOffset',0);raw=np.asarray(arr,dtype='<u2' if attr.endswith('INDEX') else '<f4').tobytes();binary[offset:offset+len(raw)]=raw
patch_tail_binding('_IDLE_SKIN_INDEX','_IDLE_SKIN_WEIGHT');patch_tail_binding('_WALK_SKIN_INDEX','_WALK_SKIN_WEIGHT')
def patch_fur_binding(index_name,weight_name):
 indices=accessor(doc,binary,primitive['attributes'][index_name]);weights=accessor(doc,binary,primitive['attributes'][weight_name]);normal_i=accessor(doc,binary,primitive['attributes']['JOINTS_0']);normal_w=accessor(doc,binary,primitive['attributes']['WEIGHTS_0']);names=[doc['nodes'][n]['name'] for n in doc['skins'][0]['joints']]
 for v in range(len(indices)):
  bases=('ruffL','ruffR','shoulderFurL','shoulderFurR');fur=[(int(n),float(w)) for n,w in zip(normal_i[v],normal_w[v]) if names[int(n)].startswith(bases) and w>1e-8];amount=sum(w for n,w in fur)
  if amount<1e-8:continue
  body={int(n):float(w) for n,w in zip(indices[v],weights[v]) if not names[int(n)].startswith(bases) and w>1e-8};total=sum(body.values())
  retained={n:w*(1-amount)/total for n,w in body.items()} if total>1e-8 else {}
  for n,w in fur:retained[n]=retained.get(n,0)+w
  top=sorted(retained.items(),key=lambda p:-p[1])[:4];total=sum(w for n,w in top);indices[v]=0;weights[v]=0
  for j,(n,w) in enumerate(top):indices[v,j]=n;weights[v,j]=w/total
 for attr,arr in [(index_name,indices),(weight_name,weights)]:
  a=doc['accessors'][primitive['attributes'][attr]];view=doc['bufferViews'][a['bufferView']];offset=view.get('byteOffset',0)+a.get('byteOffset',0);raw=np.asarray(arr,dtype='<u2' if attr.endswith('INDEX') else '<f4').tobytes();binary[offset:offset+len(raw)]=raw
patch_fur_binding('_IDLE_SKIN_INDEX','_IDLE_SKIN_WEIGHT');patch_fur_binding('_WALK_SKIN_INDEX','_WALK_SKIN_WEIGHT')
primitive['targets']=[{'POSITION':append(convert(d)[mapping])} for d in delta];doc['meshes'][0]['weights']=[0]*48;doc['meshes'][0].setdefault('extras',{})['targetNames']=[f'RunSurface{i+1:02}' for i in range(48)]
node=next(i for i,n in enumerate(doc['nodes']) if n.get('mesh')==0 and 'skin' in n)
for animation in doc['animations']:
 if animation['name']=='Run':
  times=np.arange(49)/48;values=np.vstack([np.eye(48),np.eye(48)[0]])
 else:
  duration=max(float(accessor(doc,binary,s['input'])[-1,0]) for s in animation['samplers']);times=[0,duration];values=np.zeros((2,48))
 sampler=len(animation['samplers']);animation['samplers'].append({'input':append(times,'SCALAR'),'output':append(values.ravel(),'SCALAR'),'interpolation':'LINEAR'});animation['channels'].append({'sampler':sampler,'target':{'node':node,'path':'weights'}})
occlusion=root/'authoring/fur-occlusion.png'
# Legacy occlusion records rest-pose creases; the repaired coat uses live light.
if occlusion.exists() and not coat.get('surface_polished'):
 while len(binary)%4:binary.append(0)
 payload=occlusion.read_bytes();view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':len(payload)});binary.extend(payload);image_index=len(doc['images']);doc['images'].append({'bufferView':view,'mimeType':'image/png','name':'Soft fur occlusion'});texture_index=len(doc['textures']);doc['textures'].append({'source':image_index});doc['materials'][0]['occlusionTexture']={'index':texture_index,'texCoord':0,'strength':.35}
while len(binary)%4:binary.append(0)
doc['buffers'][0]['byteLength']=len(binary);text=json.dumps(doc,separators=(',',':')).encode()
while len(text)%4:text+=b' '
asset.write_bytes(struct.pack('<III',0x46546c67,2,28+len(text)+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'authoring/wolf.blend'),compress=True)
print('CORRECTIVE_EXPORT',len(delta),len(positions),asset.stat().st_size,flush=True)
