# Give the welded closure its own UV island; the old tunnel crosses several
# atlas seams. Reusing its UVs would stretch unrelated pigment across the cheek.
import io
from PIL import Image,ImageDraw
baseinfo=asset.doc['materials'][0]['pbrMetallicRoughness']['baseColorTexture'];normalinfo=asset.doc['materials'][0]['normalTexture']
def load_image(info):
 image=asset.doc['images'][asset.doc['textures'][info['index']]['source']];v=asset.doc['bufferViews'][image['bufferView']];return image,Image.open(io.BytesIO(asset.binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])).convert('RGBA')
colordoc,color=load_image(baseinfo);normaldoc,normalimg=load_image(normalinfo);W,H=color.size
uv=asset.read(prim['attributes']['TEXCOORD_0']);occupied=Image.new('L',(W,H));draw=ImageDraw.Draw(occupied)
for t in indices[~rm]:draw.polygon([tuple(p) for p in uv[t]*[W,H]],fill=255)
occ=np.asarray(occupied);slot=None
for yy in range(8,H-88,8):
 for xx in range(8,W-152,8):
  if not occ[yy:yy+80,xx:xx+144].any():slot=(xx,yy);break
 if slot:break
assert slot is not None,'No empty texture island'
# A quiet ivory wash sampled from intact skin alongside each repaired cheek.
cp=np.asarray(color).copy();npix=np.asarray(normalimg).copy();newuv={};duplicates=[]
for side,loop in enumerate(loops):
 xx,yy=slot[0]+side*72,slot[1];coords=rest[loop][:,[1,2]];lo=coords.min(0);span=np.maximum(coords.max(0)-lo,1e-6)
 neighbors=np.where((np.sign(rest[ids,0])==np.sign(rest[loop,0].mean()))&(abs(rest[ids,1]+3.85)<.23)&(rest[ids,2]>4.24)&(rest[ids,2]<4.28))[0]
 samples=uv[neighbors];pixels=cp[np.clip((samples[:,1]*H).astype(int),0,H-1),np.clip((samples[:,0]*W).astype(int),0,W-1)]
 bright=pixels[(pixels[:,:3].min(1)>135)&(pixels[:,:3].max(1)-pixels[:,:3].min(1)<60)]
 shade=np.median(bright,axis=0) if len(bright) else np.array([232,231,220,255])
 rng=np.random.default_rng(812+side);noise=rng.normal(0,.65,(72,72,1));cp[yy:yy+72,xx:xx+72]=np.uint8(np.clip(shade+noise,0,255));npix[yy:yy+72,xx:xx+72]=[128,128,255,255]
 for i in loop:
  px=np.array([xx+8,yy+8])+(rest[i,[1,2]]-lo)/span*55
  newuv[i]=np.array([px[0]/W,px[1]/H],dtype=np.float32);duplicates.append(render_for[i])
# Duplicate only render seam vertices, with identical positions and all bindings.
# These vertices are welded in native topology, just as other GLTF UV seams are.
extra=np.array(duplicates);oldcount=len(ids);slotmap={int(ids[v]):oldcount+i for i,v in enumerate(extra)}
for key,accessor in list(prim['attributes'].items()):
 values=asset.read(accessor);full=np.concatenate([values,values[extra]])
 if key=='TEXCOORD_0':full[oldcount:]=np.array([newuv[int(ids[v])] for v in extra])
 a=dict(asset.doc['accessors'][accessor]);a.pop('sparse',None);a['bufferView']=asset.append_view(full);a['byteOffset']=0;a['count']=len(full)
 if 'min'in a:a['min']=full.min(0).tolist();a['max']=full.max(0).tolist()
 prim['attributes'][key]=len(asset.doc['accessors']);asset.doc['accessors'].append(a)
for target in prim['targets']:
 for key,accessor in list(target.items()):
  values=asset.read(accessor);full=np.concatenate([values,values[extra]]);a=dict(asset.doc['accessors'][accessor]);a.pop('sparse',None);a.pop('bufferView',None);a.pop('byteOffset',None);a.pop('min',None);a.pop('max',None);a['count']=len(full)
  nz=np.where(np.linalg.norm(full,axis=1)>1e-7)[0];a['sparse']={'count':len(nz),'indices':{'bufferView':asset.append_view(nz.astype('<u4')),'componentType':5125},'values':{'bufferView':asset.append_view(full[nz].astype('<f4'))}}
  target[key]=len(asset.doc['accessors']);asset.doc['accessors'].append(a)
idx[-len(caps)*3:]=np.array([[slotmap[i] for i in f] for f in caps],dtype='<u4').ravel();a=asset.doc['accessors'][prim['indices']];a['bufferView']=asset.append_view(idx);a['max']=[int(idx.max())]
for doc,array,label in [(colordoc,cp,'closure-diffuse.png'),(normaldoc,npix,'closure-normal.png')]:
 path=out/label;Image.fromarray(array).save(path);doc['bufferView']=asset.append_view(np.frombuffer(path.read_bytes(),dtype=np.uint8))
# Store the same clean island on the native welded cap for subsequent authoring.
for poly in mesh.polygons:
 if set(poly.vertices).issubset(newuv) and len(poly.vertices)==3:
  for li in poly.loop_indices:mesh.uv_layers.active.data[li].uv=(newuv[mesh.loops[li].vertex_index][0],1-newuv[mesh.loops[li].vertex_index][1])
bpy.ops.wm.save_as_mainfile(filepath=str(out/'jaw-repair.blend'),compress=True)
# Remove orphaned old accessors/buffer views after the UV seam update. This is
# binary compaction only: referenced data and animation samples remain exact.
used_accessors=set()
for m in asset.doc['meshes']:
 for p in m['primitives']:
  used_accessors.update(p['attributes'].values());used_accessors.add(p['indices'])
  for t in p.get('targets',[]):used_accessors.update(t.values())
for skin in asset.doc['skins']:used_accessors.add(skin['inverseBindMatrices'])
for animation in asset.doc['animations']:
 for sampler in animation['samplers']:used_accessors.update([sampler['input'],sampler['output']])
amap={old:i for i,old in enumerate(sorted(used_accessors))};asset.doc['accessors']=[asset.doc['accessors'][old] for old in sorted(used_accessors)]
for m in asset.doc['meshes']:
 for p in m['primitives']:
  p['attributes']={k:amap[v] for k,v in p['attributes'].items()};p['indices']=amap[p['indices']]
  for t in p.get('targets',[]):
   for k,v in list(t.items()):t[k]=amap[v]
for skin in asset.doc['skins']:skin['inverseBindMatrices']=amap[skin['inverseBindMatrices']]
for animation in asset.doc['animations']:
 for sampler in animation['samplers']:
  for k in ['input','output']:sampler[k]=amap[sampler[k]]
references=[]
for a in asset.doc['accessors']:
 if 'bufferView'in a:references.append(a)
 if 'sparse'in a:references.extend([a['sparse']['indices'],a['sparse']['values']])
references+=asset.doc['images'];used_views=sorted({a['bufferView'] for a in references});vmap={old:i for i,old in enumerate(used_views)};binary=bytearray();views=[]
for old in used_views:
 v=dict(asset.doc['bufferViews'][old]);start=v.get('byteOffset',0)
 while len(binary)%4:binary.append(0)
 payload=asset.binary[start:start+v['byteLength']];v['byteOffset']=len(binary);binary.extend(payload);views.append(v)
for a in references:a['bufferView']=vmap[a['bufferView']]
asset.binary=binary;asset.doc['bufferViews']=views
