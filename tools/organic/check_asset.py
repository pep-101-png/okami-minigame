import json,struct,subprocess,pathlib,hashlib

def read(b):
 n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);return j,b[28+n:]
def accessor(j,b,i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];sz={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4}[a['componentType']]*{'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];off=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',sz);return bytes().join(b[off+k*stride:off+k*stride+sz]for k in range(a['count']))
def mesh_signature(j,b):
 out={}
 for m in j['meshes']:
  for i,p in enumerate(m['primitives']):
   for key,idx in p['attributes'].items():out[(m['name'],i,key)]=hashlib.sha256(accessor(j,b,idx)).hexdigest()
   if'indices'in p:out[(m['name'],i,'indices')]=hashlib.sha256(accessor(j,b,p['indices'])).hexdigest()
 return out
old,ob=read(subprocess.check_output(['git','show','e3b463d:public/models/amaterasu-original.glb']));new,nb=read(pathlib.Path('public/models/amaterasu-original.glb').read_bytes())
assert mesh_signature(old,ob)==mesh_signature(new,nb),'Original geometry, UVs or skin weights changed'
assert old['materials']==new['materials'],'Material changes'
for a,c in zip(old['images'],new['images']):
 v=old['bufferViews'][a['bufferView']];w=new['bufferViews'][c['bufferView']];assert ob[v['byteOffset']:v['byteOffset']+v['byteLength']]==nb[w['byteOffset']:w['byteOffset']+w['byteLength']],'Texture changes'
# Compare existing animation curves by target bone name/path, not buffer indices.
def clips(j,b):
 out={}
 for a in j['animations']:
  q={}
  for c in a['channels']:
   s=a['samplers'][c['sampler']];key=(j['nodes'][c['target']['node']]['name'],c['target']['path']);q[key]=(accessor(j,b,s['input']),accessor(j,b,s['output']))
  out[a['name']]=q
 return out
a=clips(old,ob);c=clips(new,nb);changed=[name for name in a if a[name]!=c.get(name)];assert not changed,changed
report={'original_mesh_uvs_indices_weights_unchanged':True,'original_materials_textures_unchanged':True,'original_41_animation_curves_unchanged':True,'actions':len(c),'added':sorted(set(c)-set(a))};assert len(c)==44;pathlib.Path('notes/organic/asset-preservation.json').write_text(json.dumps(report,indent=2));print(report)
