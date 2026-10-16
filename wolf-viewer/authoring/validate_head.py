"""Preservation and topology checks for the approved-neck to head-only sculpt."""
from pathlib import Path
import sys,json,hashlib,io
import numpy as np
from PIL import Image
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'authoring'))
from glb_buffers import GLB
out=root/'review/drafts/head-reconstruction';before=GLB(root/'public/models/neck-approved.glb');after=GLB(out/'head-candidate.glb')
a=before.doc['meshes'][0]['primitives'][0];b=after.doc['meshes'][0]['primitives'][0]
p0=before.read(a['attributes']['POSITION']);p1=after.read(b['attributes']['POSITION']);mask=np.any(p0!=p1,axis=1)
assert len(p0)==len(p1)==78730
for key in ['TEXCOORD_0','JOINTS_0','WEIGHTS_0','_IDLE_SKIN_INDEX','_IDLE_SKIN_WEIGHT','_WALK_SKIN_INDEX','_WALK_SKIN_WEIGHT','_FUR_DETAIL']:
 assert np.array_equal(before.read(a['attributes'][key]),after.read(b['attributes'][key])),key
assert np.array_equal(before.read(a['indices']),after.read(b['indices']))
assert np.array_equal(before.read(a['attributes']['NORMAL'])[~mask],after.read(b['attributes']['NORMAL'])[~mask])
for old,new in zip(a['targets'],b['targets']):
 for key in ['POSITION','NORMAL']:
  v0=before.read(old[key]);v1=after.read(new[key]);assert np.array_equal(v0[~mask],v1[~mask]),key
  assert np.isfinite(v1).all()
for key in ['animations','nodes','skins','materials','textures','samplers']:
 assert before.doc.get(key)==after.doc.get(key),key
for animation in before.doc['animations']:
 for sampler in animation['samplers']:
  for k in ['input','output']:assert np.array_equal(before.read(sampler[k]),after.read(sampler[k]))
normal_source=before.doc['textures'][before.doc['materials'][0]['normalTexture']['index']]['source']
def payload(g,im):
 v=g.doc['bufferViews'][im['bufferView']];return bytes(g.binary[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']])
for i,(old,new) in enumerate(zip(before.doc['images'],after.doc['images'])):
 if i!=normal_source:assert payload(before,old)==payload(after,new)
old=np.asarray(Image.open(io.BytesIO(payload(before,before.doc['images'][normal_source]))).convert('RGBA'))
new=np.asarray(Image.open(io.BytesIO(payload(after,after.doc['images'][normal_source]))).convert('RGBA'))
allowed=np.asarray(Image.open(out/'jaw-normal-mask.png'))>0
assert np.array_equal(old[~allowed],new[~allowed])
n=after.read(b['attributes']['NORMAL']);assert np.isfinite(n).all();assert abs(np.linalg.norm(n,axis=1)-1).max()<1e-4
native=np.load(out/'head-surface.npz');base=np.load(root/'authoring/checkpoints/neck-approved-surface.npz');selected=native['facial_mask']
assert np.array_equal(native['rest'][~selected],base['rest'][~selected]);assert np.array_equal(native['delta'][:,~selected],base['delta'][:,~selected])
assert not selected[44506:].any()
report={'sourceSHA256':hashlib.sha256((root/'public/models/neck-approved.glb').read_bytes()).hexdigest(),'headSHA256':hashlib.sha256((out/'head-candidate.glb').read_bytes()).hexdigest(),'renderVertices':len(p0),'triangles':len(before.read(a['indices']))//3,'changedFacialRenderVertices':int(mask.sum()),'protectedVerticesExact':int((~mask).sum()),'topologyIdentical':True,'allThreeSkinBindingsIdentical':True,'skeletonAndRigIdentical':True,'all22AnimationTracksAndSamplesIdentical':True,'UVsIdentical':True,'colourAndEyePaintBytesIdentical':True,'normalMapChangesRestrictedToJawTexels':int(np.any(old!=new,axis=2).sum()),'protectedNormalTexelChanges':0,'protectedPositionAndNormalCorrectivesIdentical':True,'ornamentalFurVerticesChanged':0}
(out/'preservation-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
