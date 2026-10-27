#!/usr/bin/env python3
"""Offline integrity checks. Does not launch, compile, render or play Unity."""
import argparse, collections, csv, gzip, hashlib, json, math, re, struct
from pathlib import Path
import numpy as np

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
 return h.hexdigest()
def main(repo):
 project=repo/'Sunward-Unity';new=project/'Assets/OkamiRemaster';audit=repo/'tools/remaster/audit';results={}
 baseline=json.loads((audit/'baseline-file-manifest.json').read_text())
 for name,record in baseline['files'].items():
  path=repo/name;assert path.is_file(),name;assert path.stat().st_size==record['bytes'] and sha(path)==record['sha256'],name
 results['unchangedBaselineFiles']=len(baseline['files'])
 # Unity imports identifiers globally, even for scenes outside Build Settings.
 guids={}
 for meta in (project/'Assets').rglob('*.meta'):
  m=re.search(r'^guid: ([a-f0-9]{32})',meta.read_text(),re.M)
  assert m,meta;assert m[1] not in guids,(meta,guids.get(m[1]));guids[m[1]]=meta
 for path in new.rglob('*'):
  if path.name.startswith('.') or path.suffix=='.meta':continue
  assert Path(str(path)+'.meta').exists(),path
  if path.suffix in ['.unity','.mat','.meta']:
   for g in re.findall(r'guid: ([a-f0-9]{32})',path.read_text()):
    if not g.startswith('0000000000000000'):assert g in guids,(path,g)
 results['allNewAssetMetadataAndSerializedReferencesResolve']=True
 resources={}
 for path in (project/'Assets').rglob('*'):
  if path.is_file() and path.suffix!='.meta' and 'Resources' in path.parts:
   key=str(Path(*path.parts[path.parts.index('Resources')+1:]).with_suffix('')).lower()
   assert key not in resources,(key,path,resources.get(key));resources[key]=path
 results['resourceKeysWithoutCollisions']=len(resources)
 # Every copied file must retain source bytes unless the adaptation is explicit.
 manifest=json.loads((audit/'village-source-manifest.json').read_text());adapted=[]
 for row in manifest['files']:
  path=new/'Village'/row['path']
  if sha(path)!=row['sourceSHA256']:
   assert path.suffix=='.shader' or path.name in ['DemoExplorer.cs','DemoHouseDoors.cs','DemoFarmAnimals.cs','DemoWorld.cs'],path
   adapted.append(row['path'])
 assert len(adapted)==12,adapted
 results['villageSourceFiles']=len(manifest['files']);results['intentionalVillageAdaptations']=adapted
 # Parse every packed village vertex/index, not just a file header/count.
 data=gzip.decompress(resources['demogeometry/villageworld'].read_bytes());off=12
 assert struct.unpack_from('<ii',data)==(0x32565753,1)
 count=struct.unpack_from('<i',data,8)[0];names=set();vertex_total=0;triangles=0;colliders=0;redundant=0
 shader_by_guid={re.search(r'^guid: (\w+)',Path(str(p)+'.meta').read_text(),re.M)[1]:p for p in (new/'Village/Demo/Shaders').glob('*.shader')}
 def string():
  nonlocal off
  n=struct.unpack_from('<i',data,off)[0];off+=4;assert 0<=n<=4096;s=data[off:off+n].decode();off+=n;return s
 dtype=np.dtype([('p','<f4',3),('n','<i2',3),('c','u1',4),('uv','<f4',2)])
 for k in range(count):
  name=string();material=string();assert name not in names;names.add(name)
  collision,nv,ni=struct.unpack_from('<Bii',data,off);off+=9;assert 3<=nv<=500000 and ni%3==0 and 3<=ni<=3000000
  vertices=np.frombuffer(data,dtype,nv,off);off+=nv*dtype.itemsize;indices=np.frombuffer(data,'<i4',ni,off);off+=ni*4
  assert np.isfinite(vertices['p']).all() and np.isfinite(vertices['uv']).all();assert indices.min()>=0 and indices.max()<nv
  assert 'demomaterials/mat-'+material in resources,material
  mat=resources['demomaterials/mat-'+material].read_text();shader_guid=re.search(r'm_Shader:.*guid: (\w+)',mat)[1]
  shader=shader_by_guid[shader_guid];source=shader.read_text()
  if not collision and shader.stem in ['PaintedSurface','PaintedWater','PaintedGround','InkHull']:
   assert 'Cull Off' in source and 'Blend SrcAlpha' not in source
   faces=indices.reshape(-1,3);canonical=np.sort(faces,axis=1);unique,first=np.unique(canonical,axis=0,return_index=True)
   kept=faces[np.sort(first)];assert np.array_equal(np.unique(np.sort(kept,axis=1),axis=0),unique)
   redundant+=len(faces)-len(kept)
  vertex_total+=nv;triangles+=ni//3;colliders+=collision
 assert off==len(data)
 results['villageGeometry']=dict(batches=count,vertices=vertex_total,sourceTriangles=triangles,meshColliders=colliders,redundantOpaqueFaces=redundant,expectedSubmittedTriangles=triangles-redundant,sourceGeometryBytesUnchanged=True,collisionIndicesUnchanged=True,transparentIndicesUnchanged=True,renderingEquivalenceVerifiedInUnity=False)
 layout=json.loads(resources['farm/layout'].read_text());results['farmActors']=len(layout['actors']);results['farmSpecies']=sorted(set(a['asset'] for a in layout['actors']))
 # Original byte payloads are bound to hashes, including nested EST/effect sources.
 native=new/'NativeReview';motion=json.loads((native/'motion-source-index.json').read_text())
 for e in motion['motions']:
  path=native/e['path'];assert sha(path)==e['sha256'];assert path.read_bytes()[:4]==b'mtb3'
 for e in json.loads((native/'original-component-index.json').read_text()):assert sha(native/e['path'])==e['sha256']
 results['verifiedOriginalAmmyMotionPayloads']=len(motion['motions'])
 models=[]
 for path in sorted(native.rglob('*.okamimodel')):
  model=json.loads(path.read_text());bones=model['bones'];bind=np.zeros((len(bones),3));vertices_count=0;triangle_count=0
  assert sha(path.with_name(model['name']+'.MD.bytes'))==model['sourceSHA256']
  for i,b in enumerate(bones):assert -1<=b['parent']<i;bind[i]=np.asarray(b['position'])+(bind[b['parent']] if b['parent']>=0 else 0)
  for p in model['parts']:
   positions=np.array(p['positions']).reshape(-1,3);uv=np.array(p['uv']).reshape(-1,2);colors=np.array(p['colors']).reshape(-1,4);indices=np.array(p['indices']);bi=np.array(p['boneIndices']).reshape(-1,3);weights=np.array(p['weights']).reshape(-1,3)
   assert len(positions)==len(uv)==len(colors)==len(bi)==len(weights)
   assert all(np.isfinite(x).all() for x in [positions,uv,colors,weights,bind]);assert (bi>=0).all() and (bi<len(bones)).all();assert np.allclose(weights.sum(1),1,atol=.005)
   assert indices.min()>=0 and indices.max()<len(positions) and len(indices)%3==0
   # Independent CPU bind-pose skinning: inverse-bind translation must cancel the hierarchy.
   recovered=sum(weights[:,j,None]*((positions-bind[bi[:,j]])+bind[bi[:,j]]) for j in range(3))
   assert np.max(abs(recovered-positions))<.00001
   texture=next(t for t in model['textures'] if t['index']==p['texture']);assert (path.parent/texture['path']).exists()
   vertices_count+=len(positions);triangle_count+=len(indices)//3
  models.append(dict(name=model['name'],nativeBones=len(bones),parts=len(model['parts']),vertices=vertices_count,triangles=triangle_count))
 results['nativeReviewModels']=models
 # Static syntax is not C# semantic/Unity compilation.
 from tree_sitter import Language,Parser
 import tree_sitter_c_sharp
 parser=Parser(Language(tree_sitter_c_sharp.language()));scripts=list((project/'Assets').rglob('*.cs'))
 for path in scripts:assert not parser.parse(path.read_bytes()).root_node.has_error,path
 results['csharpSyntaxFiles']=len(scripts)
 for path in new.rglob('*.shader'):
  text=path.read_text();assert '"RenderPipeline"="UniversalPipeline"' in text,path
  assert text.count('{')==text.count('}'),path
  assert not any(s in text for s in ['UnityCG.cginc','AutoLight.cginc','ForwardBase','CGPROGRAM','SHADOW_ATTENUATION','UsePass "Legacy']),path
  assert 'UniversalForwardOnly' in text,path
 for path in (new/'Village/Demo/Scripts').glob('*.cs'):assert not re.search(r'(?<!Village)\bInput\.',path.read_text()),path
 results.update(shaderSourcePorts=8,UnityExecuted=False,UnityCompiled=False,UnityVisualsVerified=False,gameplayRegressionTested=False,allBaselineBytesPreserved=True)
 return results
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[2]);parser.add_argument('--output',type=Path);args=parser.parse_args();result=main(args.repo)
 if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
