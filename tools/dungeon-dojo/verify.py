"""Source, mesh and complete native-cycle checks; does not compile Unity."""
from pathlib import Path
import sys,json,re,hashlib,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/repair'),str(ROOT/'tools/original-remake'),str(ROOT/'tools/playtest-followup'),'/workspace/work/csharp-syntax']
from scene_data import World,ref
from export_assets import RES,skin
from pose_audit import bank
from tree_sitter import Language,Parser
import tree_sitter_c_sharp
w=World();s=w.scene;plan=json.loads(Path(__file__).with_name('world-changes.json').read_text());s.set(plan['chamber'],'m_IsActive',1);bounds=[];floors=[];shaft=[]
for r in w.renderers():
 if not(r['name'].startswith('Original boss ') or 'textured earth shaft' in r['name']):continue
 d=w.mesh(r['meshGUID'],r['meshID']);assert d is not None;v=np.array(d['vertices'])@r['matrix'][:3,:3].T+r['matrix'][:3,3];t=np.array(d['triangles']);assert np.isfinite(v).all()
 if r['name'].startswith('Original boss '):bounds.append(v)
 if r['name'].startswith('Original boss floor'):floors.append((v,t))
 if 'textured earth shaft' in r['name']:
  a,b,c=v[t[:,0]],v[t[:,1]],v[t[:,2]];norm=np.cross(b-a,c-a);rad=(a+b+c)/3-[35,0,0];rad[:,1]=0;assert np.all(np.sum(norm*rad,axis=1)<0);shaft.append(v)
points=np.concatenate(bounds);assert points[:,1].max()<-20
# Downward floor support throughout playable circle, including mirror landing.
heights=[]
for x,z in [(35+float(r)*np.cos(a),float(r)*np.sin(a)) for r in np.linspace(0,30.2,9) for a in np.linspace(0,2*np.pi,33)]+[(15,-18)]:
 hits=[]
 for v,t in floors:
  a,b,c=v[t[:,0]],v[t[:,1]],v[t[:,2]];u=b[:,[0,2]]-a[:,[0,2]];q=c[:,[0,2]]-a[:,[0,2]];p=np.array([x,z])-a[:,[0,2]];den=u[:,0]*q[:,1]-u[:,1]*q[:,0];valid=abs(den)>1e-9;f=np.zeros_like(den);g=f.copy();f[valid]=(p[valid,0]*q[valid,1]-p[valid,1]*q[valid,0])/den[valid];g[valid]=(u[valid,0]*p[valid,1]-u[valid,1]*p[valid,0])/den[valid];hit=valid&(f>=-1e-5)&(g>=-1e-5)&(f+g<=1.00001);hits.extend((a[:,1]+f*(b[:,1]-a[:,1])+g*(c[:,1]-a[:,1]))[hit].tolist())
 assert hits,(x,z);heights.append(max(hits))
training=[]
for e,p in zip(json.loads(Path(__file__).with_name('training-sources.json').read_text()),plan['training']):
 folder=RES/('dojo-'+e['package']);model=json.loads((folder/'Model.json').read_text());clips=bank(folder/'Poses.bytes');count=0;maxwidth=0;maxdepth=0
 for motion in [e['idle'],e['motion']]:
  for pose in clips[motion][0]:
   parts=skin(model,pose);feet=np.concatenate([parts[next(i for i,t in enumerate(model['parts']) if t['name']==f['part'])][f['indices']] for f in e['feet']]);offset=-feet.mean(0);offset[1]=-feet[:,1].min();ground=(feet+offset)*e['scale'];assert abs(ground[:,1].min())<1e-6
   visible=np.concatenate([v for t,v in zip(model['parts'],parts) if int(t['name'].split('-')[1]) in e['mask']]);v=(visible+offset)*e['scale'];assert np.isfinite(v).all();maxwidth=max(maxwidth,np.ptp(v[:,0]));maxdepth=max(maxdepth,np.ptp(v[:,2]));count+=1
 training.append(dict(package=e['package'],frames=count,footErrorBelow1e6=True,maxWidth=maxwidth,maxDepth=maxdepth,mask=e['mask']))
parser=Parser(Language(tree_sitter_c_sharp.language()));scripts=list((ROOT/'Sunward-Unity/Assets').rglob('*.cs'));errors=[str(p) for p in scripts if parser.parse(p.read_bytes()).root_node.has_error];assert not errors,errors
# Every scene GUID resolves; no duplicate serialized components/roots.
scene=(ROOT/'Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity').read_text();baseline=subprocess.check_output(['git','show',plan['base']+':Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'],cwd=ROOT,text=True);missing=sorted(set(re.findall(r'guid: ([a-f0-9]{32})',scene))-set(w.assets)-set(re.findall(r'guid: ([a-f0-9]{32})',baseline)));assert not missing,missing
assert sum('Assembly-CSharp::Sunward.Remaster.LowerArena\n' in b for b in s.blocks.values())==1
for go,b in s.blocks.items():
 if s.kind(go)==1 and 'stripped' not in b:
  components=re.findall(r'  - component: \{fileID: (\d+)\}',b)
  if components:assert s.kind(int(components[0]))==4,(go,components)
result=dict(nativeArchitectureBounds=[points.min(0).tolist(),points.max(0).tolist()],highestArchitectureBelowVillage=float(-points[:,1].max()),floorSamples=len(heights),floorHeightRange=[min(heights),max(heights)],shaftSections=len(shaft),shaftBoundary=len(plan['shaftBoundary']),shaftOpenBottom=-34,training=training,csharpSyntaxFiles=len(scripts),unityCompilation='UNVERIFIED: no Unity editor',unityPlayback='UNVERIFIED',lightingParticles='UNVERIFIED in Unity')
Path(__file__).with_name('verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
