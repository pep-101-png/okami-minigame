"""Focused patch of tested Windflower; original boss layout, earth shaft, dojo."""
from pathlib import Path
import sys,json,re,subprocess,math,collections,shutil,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/repair'),str(ROOT/'tools/original-remake'),str(ROOT/'tools/village')]
from scene_data import World,ref
from native import Mesh,vec,fmt
from export_assets import A,OUT,RES,guid
spec=importlib.util.spec_from_file_location('worldhelpers',ROOT/'tools/original-remake/install_world.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
BASE='9646fda1fd46017f6627c8f815cdb32382b2d73e'
path=A/'Sunward/Scenes/Windflower.unity';path.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT));w=World();s=w.scene
old=json.loads((ROOT/'tools/combat-depths/world-changes.json').read_text());sources=json.loads(Path(__file__).with_name('source-conversions.json').read_text());records=[]
def collider(go,mesh):
 sample=next(b for i,b in s.blocks.items() if s.kind(i)==64 and 'stripped' not in b);cid=s.alloc();sample=re.sub(r'^--- !u!64 &-?\d+.*',f'--- !u!64 &{cid}',sample);sample=re.sub(r'  m_GameObject: .*',f'  m_GameObject: {{fileID: {go}}}',sample);sample=re.sub(r'  m_Mesh: .*',f'  m_Mesh: {{fileID: 4300000, guid: {mesh}, type: 2}}',sample);sample=re.sub(r'  m_Enabled: .*','  m_Enabled: 1',sample);s.blocks[cid]=sample;s.blocks[go]=s.blocks[go].replace('  m_Layer:',f'  - component: {{fileID: {cid}}}\n  m_Layer:',1);s.set(go,'m_Layer',6)
def empty(name):
 p=sources[0]['meshes'][0];go=s.add(name,p['mesh'],p['material']);s.set(s.component(go,23),'m_Enabled',0);return go
s.set(old['chamber'],'m_IsActive',0)
chamber=empty('Original r10d boss cavern');parent=s.transform(chamber)
for e in sources:
 if not e['package'].startswith('dungeon-'):continue
 for part in e['meshes']:
  name='Original boss floor' if e['package']=='dungeon-floor' else 'Original boss architecture '+e['package'];p=[35,-110+(.025 if e['package']=='dungeon-seal' else 0),0];go=s.add(name+' '+str(part['part']),part['mesh'],part['material'],p=p,scale=[1.1]*3,parent=parent)
  if e['package']=='dungeon-floor':collider(go,part['mesh'])
  records.append(dict(go=go,package=e['package'],part=part['part']))
# Relocate the existing functional mirror, preserving its authentic model.
mirrortr=s.transform(old['mirror']);mirrorpos=vec(s.blocks[mirrortr],'m_LocalPosition');delta=np.array([15,-109.7,-18])-mirrorpos
# Mirror is a root grouping; its original children retain native scale/artwork.
oldparent=ref(s.blocks[mirrortr],'m_Father')[0]
if oldparent:s.blocks[oldparent]=s.blocks[oldparent].replace('  - {fileID: '+str(mirrortr)+'}\n','')
s.set(mirrortr,'m_Father',f'{{fileID: {parent}}}');s.set(mirrortr,'m_LocalPosition',fmt(mirrorpos+delta));s.blocks[parent]=s.blocks[parent].replace('  m_Children: []',f'  m_Children:\n  - {{fileID: {mirrortr}}}') if '  m_Children: []' in s.blocks[parent] else s.blocks[parent].replace('  m_Children:\n','  m_Children:\n  - {fileID: '+str(mirrortr)+'}\n')
# Cut boundary comes from the exact existing terrain triangles, welded by position.
d=w.mesh(old['oldGroundSource'],-1844107791034710560);v=np.asarray(d['vertices']);tri=np.asarray(d['triangles']);q=v[tri][:,:,[0,2]]-[35,0];cut=np.any(np.linalg.norm(q,axis=2)<4.8,axis=1)|(np.linalg.norm(q.mean(1),axis=1)<4.8)
edges=collections.Counter()
for t in tri[cut]:
 for a,b in zip(t,np.roll(t,-1)):
  pa=tuple(np.round(v[a],5));pb=tuple(np.round(v[b],5));edges[tuple(sorted([pa,pb]))]+=1
boundary=[e for e,n in edges.items() if n==1];adj=collections.defaultdict(list)
for a,b in boundary:adj[a].append(b);adj[b].append(a)
assert all(len(x)==2 for x in adj.values()),'Non-manifold shaft boundary'
loop=[next(iter(adj))];prev=None
while True:
 choices=[p for p in adj[loop[-1]] if p!=prev];n=choices[0]
 if n==loop[0]:break
 prev=loop[-1];loop.append(n)
assert len(loop)==len(adj);rim=np.array(loop);centre=np.array([35,0,0]);rad= rim[:,[0,2]]-[35,0];angle=np.unwrap(np.arctan2(rad[:,1],rad[:,0]));
if angle[-1]<angle[0]:rim=rim[::-1]
texdir=RES/'dungeon-shaft';texdir.mkdir(exist_ok=True)
for key,source in [('Soil',OUT/'Textures/Kamiki-earth.png'),('Rock',A/'OkamiRemaster/Windflower/Textures/Recovered-Cliff.png')]:
 target=texdir/(key+'.png');shutil.copyfile(source,target);guid(target);meta=Path(str(target)+'.meta');raw=meta.read_text();raw=re.sub(r'wrap([UVW]): \d',r'wrap\1: 0',raw);meta.write_text(raw)
# Open-ended throat with a bevel and changing cross-section; no disk/cap.
profiles=[(0,1),(-.35,.99),(-1.25,.92),(-4,1.02),(-12,1.12),(-24,1.35),(-34,1.8)]
shaft=[]
for section in range(len(profiles)-1):
 m=Mesh();y0,r0=profiles[section];y1,r1=profiles[section+1];distance=0
 for j in range(len(rim)):
  k=(j+1)%len(rim);length=np.linalg.norm(rim[k]-rim[j]);pts=[]
  for idx,y,r in [(j,y0,r0),(k,y0,r0),(j,y1,r1),(k,y1,r1)]:
   p=centre+(rim[idx]-centre)*[r,0,r];p[1]=rim[idx,1]+y;pts.append(p)
  ids=[m.vertex(p,(1,1,1),uv) for p,uv in zip(pts,[(distance/3,-y0/3),((distance+length)/3,-y0/3),(distance/3,-y1/3),((distance+length)/3,-y1/3)])];distance+=length
  for face in [(ids[0],ids[2],ids[1]),(ids[1],ids[2],ids[3])]:
   a,b,c=np.array(m.v)[list(face)];normal=np.cross(b-a,c-a);out=(a+b+c)/3-centre;out[1]=0;m.tri.append(face if normal@out<0 else tuple(reversed(face)))
 p=OUT/'Meshes'/('Dungeon-earth-shaft-'+str(section)+'.asset');m.write(p);mat=OUT/'Materials'/('Dungeon-earth-shaft-'+str(section)+'.mat');template=(OUT/'Materials/vta0-0.mat').read_text().replace(guid(RES/'vta0/Texture-0.png'),guid(texdir/('Soil.png' if section<2 else 'Rock.png')))
 if section>=2:template=template.replace(guid(OUT/'Shaders/OriginalPaint.shader'),guid(OUT/'Shaders/OriginalDepthsPaint.shader'))
 mat.write_text(template);go=s.add('Original textured earth shaft '+str(section),guid(p),guid(mat),parent=parent);collider(go,guid(p));shaft.append(go)
lower=next(i for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.Remaster.LowerArena\n' in b);s.set(lower,'chamber',f'{{fileID: {chamber}}}');s.set(chamber,'m_IsActive',0)
# Keep all other village roots intact; adjust only the three practice pairs.
floors=[]
for r in w.renderers():
 if 'training hall · dojo-floor' in r['name']:
  d=w.mesh(r['meshGUID'],r['meshID']);fv=np.asarray(d['vertices'])@r['matrix'][:3,:3].T+r['matrix'][:3,3];floors.append((fv,np.asarray(d['triangles'])))
def floor(x,z):
 values=[]
 for v,t in floors:
  a,b,c=v[t[:,0]],v[t[:,1]],v[t[:,2]];u=b[:,[0,2]]-a[:,[0,2]];q=c[:,[0,2]]-a[:,[0,2]];p=np.array([x,z])-a[:,[0,2]];den=u[:,0]*q[:,1]-u[:,1]*q[:,0];valid=abs(den)>1e-9;f=np.zeros_like(den);g=f.copy();f[valid]=(p[valid,0]*q[valid,1]-p[valid,1]*q[valid,0])/den[valid];g[valid]=(u[valid,0]*p[valid,1]-u[valid,1]*p[valid,0])/den[valid];hit=valid&(f>=-1e-5)&(g>=-1e-5)&(f+g<=1.00001);values.extend((a[:,1]+f*(b[:,1]-a[:,1])+g*(c[:,1]-a[:,1]))[hit].tolist())
 assert values,(x,z);return max(values)
training=json.loads(Path(__file__).with_name('training-sources.json').read_text());actors=[i for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.Remaster.NativeVenueActor\n' in b and '  role: training\n' in b];assert len(actors)==3
placements=[]
for index,(venue,e,pos) in enumerate(zip(actors,training,[[-4.2,28.5],[4.2,28.5],[0,31.5]])):
 go=s.owner(venue);actor=ref(s.blocks[venue],'actor')[0];dummy=ref(s.blocks[venue],'dummy')[0];dummygo=s.owner(dummy);x,z=pos;y=floor(x,z)+.015;dz=z-1.85;dy=floor(x,dz)+.015
 s.set(s.transform(go),'m_LocalPosition',fmt([x,y,z]));s.set(s.transform(dummygo),'m_LocalPosition',fmt([x,dy,dz]));s.set(s.transform(go),'m_LocalRotation','{x: 0, y: 1, z: 0, w: 0}')
 for k,val in [('resource',e['resource']),('idle',e['idle']),('walk',e['idle']),('modelScale',e['scale']),('modelOffset',fmt([0,0,0]))]:s.set(actor,k,val)
 s.set(venue,'motion',e['motion']);s.blocks[venue]+='  contactEnabled: 0\n'
 fields=f'  actor: {{fileID: {actor}}}\n  feet:\n'
 for f in e['feet']:fields+='  - part: '+f['part']+'\n    indices: '+''.join(int(i).to_bytes(4,'little').hex() for i in f['indices'])+'\n'
 h.add_component(s,go,'NativePracticeAnchor',fields);placements.append(dict(go=go,package=e['package'],position=[x,y,z],dummy=[x,dy,dz],motion=e['motion']))
s.save();Path(__file__).with_name('world-changes.json').write_text(json.dumps(dict(base=BASE,chamber=chamber,architecture=records,shaft=shaft,shaftBoundary=rim.tolist(),shaftProfiles=profiles,training=placements,mirror=[15,-109.7,-18],floor=-110,scale=1.1),indent=2)+'\n');print('Installed boss cavern,',len(rim),'edge 3D shaft, three isolated native practice rigs')
