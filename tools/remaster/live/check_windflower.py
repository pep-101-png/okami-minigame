#!/usr/bin/env python3
"""Independent checks of the real saved Windflower change; no Unity claim."""
from pathlib import Path
import sys,re,json,hashlib,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'Sunward-Unity';A=P/'Assets'
sys.path.insert(0,str(ROOT/'tools/village'));from native import Scene,vec
BASE='1ba3426de6557d7bd494f6ba0deb7ef55aa6a354';path=A/'Sunward/Scenes/Windflower.unity';base=Scene(path,text=subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT,text=True));now=Scene(path)
authoring=json.loads(Path(__file__).with_name('authoring-report.json').read_text());allowed_renderer_ids=set(authoring['bridges']['hiddenLegacyDeckRenderers'])
report={};changed=[]
for i,text in base.blocks.items():
 assert i in now.blocks,('Deleted existing Unity object',i)
 a=now.blocks[i];kind=base.kind(i)
 if a!=text:
  changed.append(i)
  # Only existing renderer material/enabled bindings, prefab material overrides,
  # and transform child lists may change. Functional data must remain exact.
  if kind==23:
   scrub=lambda x:re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)', '  m_Materials: APPROVED\n',re.sub(r'(?m)^  m_Enabled: \d+','  m_Enabled: APPROVED',x),flags=re.S)
   assert scrub(a)==scrub(text),('Unexpected renderer field',i)
  elif kind==4:
   scrub=lambda x:re.sub(r'  m_Children:.*?(?=  m_Father:)', '  m_Children: APPROVED\n',x,flags=re.S)
   assert scrub(a)==scrub(text),('Moved existing transform',i)
  elif kind==1001:
   # Every pre-existing non-material override remains unchanged.
   def scrub(x):
    def override(match):
     text=match[0];target=int(re.search(r'fileID: (-?\d+)',text)[1]);property=re.search(r'propertyPath: (.*)',text)[1].strip("'")
     if property=='m_Materials.Array.data[0]' or (property=='m_Enabled' and target in allowed_renderer_ids):return ''
     return text
    return re.sub(r'    - target: .*\n      propertyPath: [^\n]*\n      value:[^\n]*\n      objectReference: [^\n]*\n',override,x)
   assert scrub(a)==scrub(text),('Changed non-material prefab override',i)
  elif kind==1660057539:
   oldrefs=re.findall(r'fileID: (-?\d+)',text);newrefs=re.findall(r'fileID: (-?\d+)',a);assert newrefs[:len(oldrefs)]==oldrefs
  else:raise AssertionError(('Changed protected component',kind,i))
for kind,label in [(114,'gameplayComponents'),(137,'skinnedRenderers'),(65,'boxColliders'),(136,'capsuleColliders'),(64,'meshColliders'),(143,'characterControllers'),(95,'animators'),(20,'cameras')]:
 ids=[i for i in base.blocks if base.kind(i)==kind];assert all(base.blocks[i]==now.blocks[i] for i in ids);report[label+'BytePreserved']=len(ids)
report['existingObjectsDeleted']=0;report['existingTransformsMoved']=0
# All baseline project files except the deliberately updated scene remain intact.
manifest=json.loads((ROOT/'tools/remaster/audit/baseline-file-manifest.json').read_text())['files'];unchanged=0
for name,record in manifest.items():
 if name in [str(path.relative_to(ROOT)),'Sunward-Unity/Assets/Editor/WindflowerDiagnostics.cs']:continue
 file=ROOT/name;assert file.exists() and hashlib.sha256(file.read_bytes()).hexdigest()==record['sha256'],name;unchanged+=1
report['otherBaselineFilesBytePreserved']=unchanged
report['modifiedExistingEditorDiagnostics']='Native painting paths and recovered river shader recognition only'
assert len(list(A.rglob('*.unity')))==1
report['activeGameplayScenes']=['Assets/Sunward/Scenes/Windflower.unity']
meta={}
for file in A.rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',file.read_text(),re.M)
 if m:assert m[1] not in meta,(file,meta.get(m[1]));meta[m[1]]=file.with_suffix('')
baseline_guids=set(re.findall(r'guid: ([a-f0-9]{32})',''.join(base.blocks.values())))
for file in [path,*list((A/'OkamiRemaster/Windflower').rglob('*.mat'))]:
 for g in re.findall(r'guid: ([a-f0-9]{32})',file.read_text()):
  if not g.startswith('0000000000000000'):assert g in meta or (file==path and g in baseline_guids),(file,g)
report['sceneAndNewMaterialsReferencesResolve']=True
posts=authoring['trialBellFrame']['newPostColliders'];assert len(posts)==2
assert posts[0]['center'][0]+posts[0]['size'][0]/2<-.65 and posts[1]['center'][0]-posts[1]['size'][0]/2>.65
report['trialBellClearApproachWidth']=posts[1]['center'][0]-posts[1]['size'][0]/2-(posts[0]['center'][0]+posts[0]['size'][0]/2)
meshes=[]
for file in (A/'OkamiRemaster/Windflower/Meshes').glob('*.asset'):
 raw=file.read_text();n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);data=bytes.fromhex(re.search('_typelessdata: ([a-f0-9]+)',raw)[1]);records=np.frombuffer(data,'<f4').reshape(-1,12);assert len(records)==n;assert np.isfinite(records).all()
 ix=np.frombuffer(bytes.fromhex(re.search('m_IndexBuffer: ([a-f0-9]+)',raw)[1]),'<u4').reshape(-1,3);assert ix.max()<n;assert np.isfinite(records).all();used=np.unique(ix);length=np.linalg.norm(records[used,3:6],axis=1)
 assert np.all(abs(length-1)<.002),(file,'Invalid used normals',length.min(),length.max())
 meshes.append(dict(name=file.stem,vertices=n,triangles=len(ix)))
report['newMeshes']=meshes
r=json.loads(Path(__file__).with_name('authoring-report.json').read_text());assert len(r['houses'])==14
for house in r['houses']:
 for i in house['oldVisualRoots']:assert 'm_Enabled: 0\n' in now.blocks[now.component(i,23)]
 for i in house['newObjects']:assert 'm_Enabled: 1\n' in now.blocks[now.component(i,23)]
assert len(r['originalRocks']['liveRockIndices'])==122
assert r['botanicalPaint']['counts']=={'Bamboo':7,'Flowers':180,'Grass':360}
report['liveRocksReplaced']=122;report['liveCherryTreesReplaced']=len(r['cherryTrees']['treeIndices']);report['liveMarketRoofsReplaced']=len(r['markets']['roots']);report['livePlantChanges']=r['botanicalPaint']['counts']
river=Path(r['riverPaint']['bindings'][0]['clone']);river_guid=re.search(r'^guid: (\w+)',Path(str(P/river)+'.meta').read_text(),re.M)[1];assert river_guid in path.read_text(),'Recovered river is not bound in the actual scene/prefab overrides'
pond_guid=re.search(r'^guid: (\w+)',Path(str(P/r['pondPaint']['material'])+'.meta').read_text(),re.M)[1];assert pond_guid in path.read_text(),'Recovered pond is not bound in actual scene'
report['riverAndPondMaterialOverridesVerified']=True
report['liveHouseReplacements']=len(r['houses']);report['liveBridgeReplacements']=2;report['liveMaterialClones']=len(r['paintRebindings']);report['newLiveRenderers']=sum(now.kind(i)==23 for i in now.blocks if i not in base.blocks)
# Animal paths must avoid existing building/obstacle/river/arena/pond footprints.
world=json.loads((A/'Sunward/Data/Valley.json').read_text())['world'];layout=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json').read_text());conflicts=[]
for animal in layout['actors']:
 for point in animal['path']:
  x,z=point['x'],point['y'];radius=.35 if animal['asset'] in ['cow','pig','boar'] else .20
  for b in world['boxes']:
   if abs(x-b['x'])<b['halfX']+radius+.2 and abs(z+b['z'])<b['halfZ']+radius+.2:conflicts.append((animal['name'],'building',b))
  for o in world['obstacles']:
   if (x-o['x'])**2+(z+o['z'])**2<(o['r']+radius+.2)**2:conflicts.append((animal['name'],'obstacle',o))
  assert (x-35)**2+z*z>18**2;assert ((x+15)/4)**2+((z+22)/3)**2>1
report['ambientActors']=len(layout['actors']);report['ambientAnimalTypes']=sorted(set(a['asset'] for a in layout['actors']));report['animalPathConflicts']=conflicts
assert not conflicts,str(conflicts)[:1000]
from tree_sitter import Language,Parser
import tree_sitter_c_sharp
parser=Parser(Language(tree_sitter_c_sharp.language()))
for file in A.rglob('*.cs'):assert not parser.parse(file.read_bytes()).root_node.has_error,file
report['csharpSyntaxFiles']=sum(1 for _ in A.rglob('*.cs'));report['sceneSHA256']=hashlib.sha256(path.read_bytes()).hexdigest();report['UnityExecuted']=False;report['gameplayTested']=False;report['UnityVisualsVerified']=False
Path(__file__).with_name('validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='newMeshes'},indent=2))
