"""Original-data, continuous deformation and head-clearance diagnostics; not Unity."""
from pathlib import Path
import json,sys,numpy as np,subprocess,re,hashlib
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/spirit-wisp-flow');checks=0
sys.path[:0]=[str(R/'tools/trailer30'),str(R/'tools/spirit-charge-home/trailer')];from native_renderer import pose_bank;from asset_geometry import skin,rotation

def check(b,s):
 global checks
 checks+=1;assert b,s

def sample(bank,clip,time,mirror=False):
 data,duration,_=bank[clip];f=(time%duration)/duration*(len(data)-1);i=int(f);j=min(i+1,len(data)-1);u=f-i;p=data[i]*(1-u)+data[j]*u;q=data[j,:,3:7].copy();a=data[i,:,3:7];q[np.sum(a*q,axis=1)<0]*=-1;p[:,3:7]=a*(1-u)+q*u;p[:,3:7]/=np.linalg.norm(p[:,3:7],axis=1,keepdims=True)
 if mirror:p[:,0]*=-1;p[:,4:6]*=-1
 return p

def matrices(model,p):
 out=[]
 for i,v in enumerate(p):
  m=np.eye(4);m[:3,:3]=rotation(v[3:7])@np.diag(v[7:]);m[:3,3]=v[:3];parent=model['bones'][i-1]['parent']+1 if i else -1;out.append(m if parent<0 else out[parent]@m)
 return out

for name in ['es4a','es4b']:
 original=json.loads((D/name/'Model.json').read_text());j=json.loads((D/(name+'-flow')/'Model.json').read_text());check(j['bones']==original['bones'],'Original native skeleton changed');check(j['sourceSHA256']==original['sourceSHA256'],'Original provenance lost')
 for p in j['parts']:
  v=np.array(p['positions']).reshape(-1,3);c=np.array(p['colors']).reshape(-1,4);weights=np.array(p['weights']).reshape(-1,3);ids=np.array(p['boneIndices']).reshape(-1,3);t=np.array(p['indices']).reshape(-1,3)
  check(np.isfinite(v).all() and np.isfinite(c).all(),'Nonfinite native streams');check(len(v)>1000 and max(t.ravel())<len(v),'Subdivided mesh incomplete');check(np.max(np.linalg.norm(v[t[:,0]]-v[t[:,1]],axis=1))<.086,'Long coarse edge remains');check(np.all(c[v[:,2]<.035,3]==0),'Opaque blunt roots remain');check(np.all(weights>=0) and np.allclose(weights.sum(1),1),'Invalid native skin weights');check(ids.min()>=0 and ids.max()<len(j['bones']),'Invalid native bone reference')
 for t in j['textures']:check((D/(name+'-flow')/t['path']).read_bytes()==(D/name/t['path']).read_bytes(),'Original texture changed')
 for path in (D/name).iterdir():
  if path.suffix in ['.json','.png','.bytes']:
   blob=subprocess.check_output(['git','show','HEAD:'+str(path.relative_to(R))],cwd=R);check(('oid sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()).encode() in blob if blob.startswith(b'version https://git-lfs') else blob==path.read_bytes(),'Raw native asset modified')

# Exercise dense visible native vertices around the actual native head through
# idle, locomotion, charge and howl poses, both original mirrored motion sides.
body=json.loads((D/'es3a/Model.json').read_text());bodybank=pose_bank(A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes');bank=pose_bank(D/'es4a/Poses.bytes');j=json.loads((D/'es4a-flow/Model.json').read_text());part=j['parts'][0];col=np.array(part['colors']).reshape(-1,4);visible=col[:,3]*np.sqrt(np.max(col[:,:3],axis=1))>.08
bindings=json.loads((A/'OkamiRemaster/Player/Resources/NativePlayer/Bindings.json').read_text())['bindings'];run=next(b['clip'] for b in bindings if b['state'].startswith('Sprint'));howl=next(b['clip'] for b in bindings if b['state']=='Bark');closest=999
source=(A/'OkamiRemaster/Original/Scripts/SpectralTendrils.cs').read_text()
def values(name):return [float(v.strip().rstrip('f')) for v in re.search(r'float\[\] '+name+r'=\{([^}]+)',source)[1].split(',')]
lengths,rates,phases,headings,breadth=[values(k) for k in ['lengths','rates','phases','headings','breadth']]
mounts=[np.array([float(v.strip().rstrip('f')) for v in row.split(',')]) for row in re.findall(r'new Vector3\(([^)]+)\)',re.search(r'Vector3\[\] mounts=\{([^}]+)',source)[1])]
def deform(i,time):
 point=np.zeros(3);control=[point.copy()];step=3.8271732/40
 for k in range(40):
  s=(k+.5)*step;seed=phases[i];phase=s*1.85-time*rates[i]+seed
  cross=breadth[i]*(.78*np.sin(phase)+.22*np.sin(s*3.1-time*.68+seed*1.37));rise=.1+.25*np.sin(s*1.35-time*.63+seed*1.7);d=np.array([cross,rise,1]);point=point+d/np.linalg.norm(d)*step;control.append(point.copy())
 control=np.array(control)
 def curve(u):
  f=np.clip(u,0,1)*40;k=np.minimum(39,np.floor(f).astype(int));t=(f-k)[:,None];a=control[np.maximum(0,k-1)];b=control[k];c=control[k+1];d=control[np.minimum(40,k+2)];return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t)
 v=np.array(part['positions']).reshape(-1,3);u=np.clip(v[:,2]/3.8271732,0,1);tangent=curve(np.minimum(1,u+.002))-curve(np.maximum(0,u-.002));tangent/=np.linalg.norm(tangent,axis=1,keepdims=True);right=np.cross([0,1,0],tangent);right/=np.linalg.norm(right,axis=1,keepdims=True);up=np.cross(tangent,right);width=.9+2.1*np.sin(u*np.pi)
 return curve(u)+(right*v[:,0,None]+up*v[:,1,None])*width[:,None]
maximumBend=0
for bodyclip in ['pl00_000',run,'pl00_523',howl]:
 for t in [.1,.4,.8]:
  mats=matrices(body,sample(bodybank,bodyclip,t));torso=mats[1][:3,3]*1.2;head=mats[8][:3,3]*1.2
  for i in range(6):
   origin=torso+mounts[i];angle=np.deg2rad(180+headings[i]);rot=np.array([[np.cos(angle),0,np.sin(angle)],[0,1,0],[-np.sin(angle),0,np.cos(angle)]])
   for time in [0,.7,1.8,3.4,5.9]:
    points=deform(i,time)[visible]@(rot*lengths[i]).T+origin;check(np.isfinite(points).all(),'Nonfinite shader deformation');distance=np.linalg.norm((points-head)/np.array([.32,.34,.36]),axis=1).min();closest=min(closest,float(distance));check(distance>1,'Visible wisp crosses head volume')
for name in ['lengths','rates','phases','headings','breadth']:check(len(set(values(name)))==6,'Paired profiles remain')

shader=(A/'OkamiRemaster/Original/Shaders/OriginalFlowingRibbon.shader').read_text();check('Blend SrcAlpha OneMinusSrcAlpha' in shader and 'saturate(paint.rgb' in shader,'Unbounded additive glare remains');check('sqrt(saturate(energy))' in shader,'Native additive fade becomes opaque black');check('native.Torso.position' in (A/'OkamiRemaster/Original/Scripts/SpectralTendrils.cs').read_text(),'Mount regressed to weapon/head socket')
sys.path.insert(0,'/workspace/work/csharp-syntax');import tree_sitter,tree_sitter_c_sharp
parser=tree_sitter.Parser(tree_sitter.Language(tree_sitter_c_sharp.language()))
for p in A.rglob('*.cs'):check(not parser.parse(p.read_bytes()).root_node.has_error,'C# syntax error '+str(p))
report=dict(checks=checks,headEllipsoidClosestNormalizedDistance=closest,shaderUnityCompiled=False,unityPlayed=False,scope='Actual native data/deformation and source checks; no Unity import/render/physics claim');(W/'geometry-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',checks,'continuous shader deformation, source preservation and head-clearance diagnostics; minimum head clearance ratio',closest)
