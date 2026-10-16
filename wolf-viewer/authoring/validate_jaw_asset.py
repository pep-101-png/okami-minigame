"""Verify the review asset against the preserved head, not the actual game."""
from pathlib import Path
import sys,json,hashlib,numpy as np
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'authoring'))
from glb_buffers import GLB,to_gltf
source=GLB(root/'public/models/head-study.glb');candidate=GLB(root/'public/models/jaw-repair.glb')
a=source.doc['meshes'][0]['primitives'][0];b=candidate.doc['meshes'][0]['primitives'][0];count=source.doc['accessors'][a['attributes']['POSITION']]['count']
assert source.doc['nodes']==candidate.doc['nodes']
for key in a['attributes']:
 if key not in ['POSITION','NORMAL','TEXCOORD_0']:
  assert np.array_equal(source.read(a['attributes'][key]),candidate.read(b['attributes'][key])[:count]),key
assert np.array_equal(source.read(a['attributes']['TEXCOORD_0']),candidate.read(b['attributes']['TEXCOORD_0'])[:count])
for old,new in zip(source.doc['animations'],candidate.doc['animations']):
 assert old['channels']==new['channels']
 for x,y in zip(old['samplers'],new['samplers']):
  for k in ['input','output']:assert np.array_equal(source.read(x[k]),candidate.read(y[k])),(old['name'],k)
for old,new in zip(source.doc['skins'],candidate.doc['skins']):
 assert old['joints']==new['joints'];assert np.array_equal(source.read(old['inverseBindMatrices']),candidate.read(new['inverseBindMatrices']))
q=np.load(root/'review/drafts/jaw-repair/jaw-surface.npz');p=q['rest'];tri=q['triangles'];old=np.load(root/'authoring/checkpoints/head-study/head-surface.npz');mask=q['facial_mask']
assert np.array_equal(p[~mask],old['rest'][~mask]);assert np.array_equal(q['delta'][:,~mask],old['delta'][:,~mask]);assert not mask[44506:].any()
# Closed edge counts alone missed the inherited tunnel. Shoot rays across a
# central rectangular region strictly inside the original side-visible hole.
Y=np.linspace(-3.895,-3.835,31);Z=np.linspace(4.145,4.175,21);yy,zz=np.meshgrid(Y,Z);hits=np.zeros(yy.shape,dtype=int)
for f in tri:
 t=p[f]
 if t[:,1].min()>Y.max() or t[:,1].max()<Y.min() or t[:,2].min()>Z.max() or t[:,2].max()<Z.min():continue
 A,B,C=t;den=(B[2]-C[2])*(A[1]-C[1])+(C[1]-B[1])*(A[2]-C[2])
 if abs(den)<1e-12:continue
 u=((B[2]-C[2])*(yy-C[1])+(C[1]-B[1])*(zz-C[2]))/den;v=((C[2]-A[2])*(yy-C[1])+(A[1]-C[1])*(zz-C[2]))/den
 hits+=((u>=0)&(v>=0)&(u+v<=1))
assert hits.min()>=2
assert candidate.doc['materials'][0].get('doubleSided') is False
out={'animationsPreserved':len(candidate.doc['animations']),'rigAndAllThreeBindingsUnchanged':True,'protectedGeometryChanges':0,'protectedCorrectiveChanges':0,'ornamentalFurChanges':0,'existingUVsUnchanged':True,'renderUVSeamVerticesAdded':candidate.doc['accessors'][b['attributes']['POSITION']]['count']-count,'newNativeVertices':0,'cheekTestRays':int(hits.size),'minimumSurfaceIntersections':int(hits.min()),'singleSidedSkin':True,'candidateSHA256':hashlib.sha256((root/'public/models/jaw-repair.glb').read_bytes()).hexdigest(),'approvedNeckSHA256':hashlib.sha256((root/'public/models/neck-approved.glb').read_bytes()).hexdigest()}
(root/'review/drafts/jaw-repair/asset-validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
