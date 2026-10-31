"""Patch the existing Windflower scene; no demo scene or source archive changes."""
from pathlib import Path
import sys,json,re,subprocess,math,importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/repair'),str(ROOT/'tools/original-remake'),str(ROOT/'tools/village')]
from scene_data import World,ref,Terrain
from native import Mesh,vec,fmt
from export_assets import A,OUT,RES,guid
spec=importlib.util.spec_from_file_location('helpers',ROOT/'tools/original-remake/install_world.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
BASE='472f7be2fbaa29ed7d1827eca563ee4033e65c35';path=A/'Sunward/Scenes/Windflower.unity';path.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT));w=World();s=w.scene;terrain=Terrain(w);ledger=[]
models={}
for p in [ROOT/'tools/original-remake/original-assets.json',ROOT/'tools/playtest-repair/scene-repairs.json',ROOT/'tools/combat-depths/furniture-sources.json',ROOT/'tools/world-life/asset-sources.json']:
 j=json.loads(p.read_text());rows=j.get('models',[]) if isinstance(j,dict) else j
 for e in rows:
  if 'package' in e and 'meshes' in e:models[e['package']]=e
# Existing native furniture dependencies are also listed by the earlier repair exporter.
for p in (ROOT/'tools/playtest-repair').glob('*sources.json'):
 j=json.loads(p.read_text())
 if isinstance(j,list):
  for e in j:
   if 'package' in e and 'meshes' in e:models[e['package']]=e

def empty(name,p=(0,0,0),parent=0):
 part=models['vt64']['meshes'][0];go=s.add(name,part['mesh'],part['material'],p=p,parent=parent);s.set(s.component(go,23),'m_Enabled',0);return go

def place(package,pos,size=None,height=None,yaw=0,parent=0,label=''):
 e=models[package];lo=np.array(e['boundsMin']);hi=np.array(e['boundsMax']);ext=np.maximum(hi-lo,.001);scale=np.array(size)/ext if size else np.repeat(height/ext[1] if height else 1,3);a=math.radians(yaw);rot=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]);off=np.array(pos)-rot@((lo+np.array([hi[0],lo[1],hi[2]]))/2*scale);objects=[]
 for part in e['meshes']:
  go=s.add('Original village life · '+label,part['mesh'],part['material'],p=off,scale=scale,parent=parent);s.set(s.transform(go),'m_LocalRotation','{x: 0, y: %.9g, z: 0, w: %.9g}'%(math.sin(a/2),math.cos(a/2)));objects.append(go)
 ledger.append(dict(label=label,package=package,objects=objects,position=pos));return objects

def collider(go,mesh):
 sample=next(b for i,b in s.blocks.items() if s.kind(i)==64 and 'stripped' not in b);cid=s.alloc();sample=re.sub(r'^--- !u!64 &-?\d+.*',f'--- !u!64 &{cid}',sample);sample=re.sub(r'  m_GameObject: .*',f'  m_GameObject: {{fileID: {go}}}',sample);sample=re.sub(r'  m_Mesh: .*',f'  m_Mesh: {{fileID: 4300000, guid: {mesh}, type: 2}}',sample);s.blocks[cid]=sample;s.blocks[go]=s.blocks[go].replace('  m_Layer:',f'  - component: {{fileID: {cid}}}\n  m_Layer:',1);s.set(go,'m_Layer',6)

def native_quad(name,x,z,y,texture,size=(8,6),parent=0):
 m=Mesh();ww,dd=size;m.v=[[-ww/2,0,-dd/2],[-ww/2,0,dd/2],[ww/2,0,dd/2],[ww/2,0,-dd/2]];m.tri=[[0,1,2],[0,2,3]];m.uv=[[0,0],[0,1],[1,1],[1,0]];m.c=([[.45,.35,.25]] if name.startswith('Farm-soil') else [[1,1,1]])*4;m.bones=[0]*4;path=OUT/'Meshes'/(name+'.asset');m.write(path);mat=OUT/'Materials'/(name+'.mat');mat.write_text((OUT/'Materials/vta0-0.mat').read_text().replace(guid(RES/'vta0/Texture-0.png'),guid(texture)));go=s.add('Original village life · '+name,guid(path),guid(mat),p=[x,y,z],parent=parent);collider(go,guid(path));return go

game=next(i for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.GameFlow\n' in b);gamego=s.owner(game)
# Existing upper seal remains; the shaft gets chipped layers and staggered UVs,
# with a much longer horizontal paint period instead of square tiles.
plan=json.loads((ROOT/'tools/dungeon-dojo/world-changes.json').read_text());shaft=[]
for section,go in enumerate(plan['shaft']):
 mf=s.component(go,33);mg=ref(s.blocks[mf],'m_Mesh')[1];d=w.mesh(mg,4300000);v=np.array(d['vertices']);raw=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',d['raw'])[1]),'<f4').reshape(len(v),d['stride']//4);uv=raw[:,10:12].copy();uv[:,0]=uv[:,0]*.23+section*.173;uv[:,1]=uv[:,1]*.55+section*.137
 # Subdivide vertical facets before carving; profile boundaries stay welded.
 faces=np.array(d['triangles']);colors=raw[:,6:9].copy()
 for _ in range(2):
  nv=[];nu=[];nc=[];nf=[]
  for face in faces:
   a,b,c=v[face];ta,tb,tc=uv[face];ca,cb,cc=colors[face];offset=len(nv)
   nv.extend([a,b,c,(a+b)/2,(b+c)/2,(c+a)/2]);nu.extend([ta,tb,tc,(ta+tb)/2,(tb+tc)/2,(tc+ta)/2]);nc.extend([ca,cb,cc,(ca+cb)/2,(cb+cc)/2,(cc+ca)/2]);nf.extend([[offset+i for i in f] for f in [[0,3,5],[3,1,4],[5,4,2],[3,4,5]]])
  v=np.array(nv);uv=np.array(nu);colors=np.array(nc);faces=np.array(nf)
 depth=np.maximum(0,-v[:,1]);rad=v[:,[0,2]]-[35,0];a=np.arctan2(rad[:,1],rad[:,0]);amount=.15*np.sin(a*7+depth*.31)+.1*np.sin(a*13-depth*.19);amount*=np.minimum(depth/.5,1);rad*=1+amount[:,None]/np.maximum(np.linalg.norm(rad,axis=1)[:,None],.01);v[:,[0,2]]=rad+[35,0]
 m=Mesh();m.v=v.tolist();m.uv=uv.tolist();m.c=colors.tolist();m.tri=faces.tolist();m.bones=[0]*len(v);p=OUT/'Meshes'/('Chipped-earth-shaft-'+str(section)+'.asset');m.write(p);s.set(mf,'m_Mesh',f'{{fileID: 4300000, guid: {guid(p)}, type: 2}}');s.set(s.component(go,64),'m_Mesh',f'{{fileID: 4300000, guid: {guid(p)}, type: 2}}');shaft.append(go)
# Clip only protruding entry walkway triangles outside the dojo enclosure.
clipped=[]
for r in list(w.renderers()):
 if 'training hall · dojo-floor' not in r['name']:continue
 d=w.mesh(r['meshGUID'],r['meshID']);v=np.array(d['vertices']);world=v@r['matrix'][:3,:3].T+r['matrix'][:3,3];tri=np.array(d['triangles']);raw=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',d['raw'])[1]),'<f4').reshape(len(v),d['stride']//4)
 if np.all((world[:,2]>=16.6)&(world[:,2]<=33.6)&(abs(world[:,0])<=6.4)):continue
 m=Mesh();inverse=np.linalg.inv(r['matrix'])
 for face in tri:
  polygon=[np.r_[world[k],raw[k,10:12],raw[k,6:9]] for k in face]
  for axis,limit,sign in [(0,-6.4,1),(0,6.4,-1),(2,16.6,1),(2,33.6,-1)]:
   result=[]
   for j,current in enumerate(polygon):
    previous=polygon[j-1];dc=(current[axis]-limit)*sign;dp=(previous[axis]-limit)*sign
    if (dc>=0)!=(dp>=0):result.append(previous+(current-previous)*(dp/(dp-dc)))
    if dc>=0:result.append(current)
   polygon=result
   if not polygon:break
  if len(polygon)<3:continue
  ids=[]
  for q in polygon:
   local=(inverse@np.r_[q[:3],1])[:3];ids.append(m.vertex(local,q[5:8],q[3:5]))
  for j in range(1,len(ids)-1):m.tri.append([ids[0],ids[j],ids[j+1]])
 if not m.tri:
  s.set(s.component(r['go'],23),'m_Enabled',0);s.set(s.component(r['go'],64),'m_Enabled',0);continue
 p=OUT/'Meshes'/('Dojo-contained-floor-'+str(len(clipped))+'.asset');m.write(p);s.set(s.component(r['go'],33),'m_Mesh',f'{{fileID: 4300000, guid: {guid(p)}, type: 2}}');s.set(s.component(r['go'],64),'m_Mesh',f'{{fileID: 4300000, guid: {guid(p)}, type: 2}}');clipped.append(r['go'])
# Native slim saplings replace the oversized cherry stage assemblies.
cherry=[]
for go,b in list(s.blocks.items()):
 if s.kind(go)!=1 or 'stripped' in b:continue
 if 'village cherry' in s.name(go) or 'pond cherry blossom tree' in s.name(go):s.set(go,'m_IsActive',0);cherry.append(go)
for i,(x,z) in enumerate([(-18,-21),(-13,-25),(-16,-18)]):
 place('vt59',[x,terrain.height(x,z),z],height=4.6+(i%2)*.4,label='slender pond flowering sapling '+str(i))
# Spacious market plaza south of the main street; preserve each complete stall.
market=[]
for side,centre,inst,index in [(-1,np.array([-6,0,-30]),2027807467,0),(1,np.array([5,0,-30]),1439298636,1)]:
 old=np.array([side*7.5,0,0]);angle=math.radians(-side*90);rot=np.array([[math.cos(angle),0,math.sin(angle)],[0,1,0],[-math.sin(angle),0,math.cos(angle)]])
 for go,b in list(s.blocks.items()):
  if s.kind(go)!=1 or not s.name(go).startswith('Original larger centred'):continue
  tr=s.transform(go);p=vec(s.blocks[tr],'m_LocalPosition')
  if np.sign(p[0])!=side:continue
  s.set(tr,'m_LocalPosition',fmt(centre+rot@(p-old)));s.set(tr,'m_LocalRotation','{x: 0, y: 1, z: 0, w: 0}');market.append(go)
 station=centre+[0,.03,-1.1];src=w.prefabs[inst];root=next(i for i in src.blocks if src.kind(i)==4 and ref(src.blocks[i],'m_Father')[0]==0)
 for axis,value in zip('xyz',station):h.patch(s,inst,root,'m_LocalPosition.'+axis,value)
 for axis,value in [('y',0),('w',1)]:h.patch(s,inst,root,'m_LocalRotation.'+axis,value)
 for i,b in list(s.blocks.items()):
  if 'Assembly-CSharp::Sunward.VillageResident\n' in b and '  index: '+str(index)+'\n' in b:s.set(i,'station',fmt(station))
 for cid in ([249600521,1530535325] if side<0 else [204672430,688100575]):
  go=s.owner(cid);s.set(s.transform(go),'m_LocalPosition',fmt(centre));size=vec(s.blocks[cid],'m_Size');s.set(cid,'m_Size',fmt(size[[2,1,0]]))
# Crop beds west of the animal pens, with original vegetable models.
crops=[]
for row in range(6):
 for col in range(3):
  x=-54+col*1.3;z=22.5+row*1.35;y=terrain.height(x,z);root=empty('Harvestable original vegetable '+str(len(crops)),[x,y,z]);package=['it25','it26','it27'][col];place(package,[0,-.08,0],height=.65,parent=s.transform(root),label='crop '+package);e=models[package];lo=np.array(e['boundsMin']);hi=np.array(e['boundsMax']);carry=.28/max(.001,hi[1]-lo[1]);offset=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*carry;h.add_component(s,root,'FarmCrop','  index: '+str(len(crops))+'\n  resource: Okami/'+package+'\n  carryScale: '+str(carry)+'\n  carryOffset: '+fmt(offset)+'\n');crops.append(root)
for row in range(6):native_quad('Farm-soil-bed-'+str(row),-52.7,22.5+row*1.35,terrain.height(-52.7,22.5+row*1.35)+.012,OUT/'Textures/Kamiki-earth.png',size=(4.1,.95))
# Farm produce counter, baskets and native well complement the existing stable/pens.
place('vt90',[-50.8,terrain.height(-50.8,20),20],size=[2.1,.8,.8],label='farm shop counter')
for i,package in enumerate(['it24','it25','it26','it27']):place(package,[-51.6+i*.5,terrain.height(-50.8,20)+.81,20],height=.35,label='farm shop produce')
# Native hearths/futons/cabinets in every remaining residential house.
old=json.loads((ROOT/'tools/original-remake/world-install.json').read_text());rooms=[];homeinfo=[]
for house in old['houses']:
 root=house['root']
 if not w.active(0,root) or not any(r['go'] in house['objects'] for r in w.renderers()):continue
 centre=w.matrix(0,s.transform(root))[:3,3];x,z=float(centre[0]),float(centre[2]);y=-55.;room=empty('Village home interior '+str(house['number']),[x,y,z]);parent=s.transform(room);contents=[]
 contents.append(native_quad('Home-floor-'+str(house['number']),0,0,.0,OUT/'Textures/Kamiki-floorboards.png',parent=parent))
 contents+=place('vt64',[-2.3,.02,1.2],size=[2.2,.22,1.4],yaw=90,parent=parent,label='home futon')
 contents+=place('vt0b',[2.2,.02,1.3],size=[1.1,.35,1.1],parent=parent,label='home stone hearth')
 contents+=place('vt90',[2.9,.02,-1],size=[1.3,1.0,.7],yaw=90,parent=parent,label='home storage cabinet')
 contents+=place('vt65',[-.5,.02,-.2],height=.32,parent=parent,label='home tea tray')
 contents+=place('vt13',[2.8,.02,2.2],height=.55,parent=parent,label='home food storage')
 for pos,yaw,size in [([0,0,2.95],0,[7.8,2.8,.12]),([-3.95,0,0],90,[5.8,2.8,.12]),([3.95,0,0],90,[5.8,2.8,.12]),([-2.5,0,-2.95],0,[2.6,2.8,.12]),([2.5,0,-2.95],0,[2.6,2.8,.12])]:contents+=place('vt61',pos,size=size,yaw=yaw,parent=parent,label='home painted paper wall')
 # Door is outside the facade; interior exit always available, never radius-stranded.
 render=[r for r in w.renderers() if not r['instance'] and r['go'] in house['objects']];bounds=[]
 for r in render:
  d=w.mesh(r['meshGUID'],r['meshID']);bounds.append(np.array(d['vertices'])@r['matrix'][:3,:3].T+r['matrix'][:3,3])
 front=z-4.5
 if bounds:front=float(np.concatenate(bounds)[:,2].min())-.8
 door=[x,terrain.height(x,front),front];entrance=[x,y+.03,z-2.2];bed=[x-2.3,y+.25,z+1.2];fields='  number: '+str(house['number'])+'\n  game: {fileID: '+str(game)+'}\n  door: '+fmt(door)+'\n  exitPoint: '+fmt(door)+'\n  entrance: '+fmt(entrance)+'\n  bed: '+fmt(bed)+'\n  hearth: '+fmt([x+2.2,y+.4,z+1.3])+'\n  contents:\n'+''.join('  - {fileID: '+str(go)+'}\n' for go in contents);h.add_component(s,room,'NativeHomeRoom',fields);rooms.append(room);homeinfo.append(dict(number=house['number'],root=room,door=door,entrance=entrance))
# Original residents keep identity and dialogue, with scheduled destinations.
for i,b in list(s.blocks.items()):
 if 'Assembly-CSharp::Sunward.VillageResident\n' not in b or '  stallkeeper: 1\n' in b:continue
 go=s.owner(i)
 if 'stripped' in s.blocks[go]:continue
 actor=next((c for c in s.refs(go) if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' in s.blocks[c]),None)
 if not actor:continue
 p=vec(s.blocks[s.transform(go)],'m_LocalPosition');seed=int(re.search(r'  index: (\d+)',b)[1]);h.add_component(s,go,'NativeDailyRoutine','  game: {fileID: '+str(game)+'}\n  seed: '+str(seed)+'\n  workplace: '+fmt(p)+'\n')
farmer=next(go for go in s.blocks if s.kind(go)==1 and s.name(go)=='Original Okami · farmer');s.set(s.transform(farmer),'m_LocalPosition',fmt([-52,terrain.height(-52,20),20]));h.add_component(s,farmer,'NativeDailyRoutine','  game: {fileID: '+str(game)+'}\n  farmer: 1\n  seed: 0\n  workplace: '+fmt([-52,0,20])+'\n')
# Musician and native koto face each other with hands over the strings.
performer=next(i for i,b in s.blocks.items() if '  role: musician\n' in b);pg=s.owner(performer);s.set(s.transform(pg),'m_LocalPosition',fmt([7,.4,-17.8]));s.set(s.transform(pg),'m_LocalRotation','{x: 0, y: 0, z: 0, w: 1}')
# Use the original woman without the former basket headgear, with her own bank.
actor=ref(s.blocks[performer],'actor')[0];s.set(actor,'resource','Okami/hm05')
for k in ['idle','walk','run','windup','strike','recover','death']:s.set(actor,k,'hm05_003')
s.set(performer,'seatedMotion','hm05_003');s.set(performer,'handMotion','hm05_028')
s.set(actor,'modelScale',.9184123273)
from export_assets import skin
sys.path.insert(0,str(ROOT/'tools/playtest-followup'));from pose_audit import bank
folder=RES/'hm05';model=json.loads((folder/'Model.json').read_text());parts=skin(model,bank(folder/'Poses.bytes')['hm05_003'][0][0]);v=np.concatenate(parts);lo=v.min(0);hi=v.max(0);s.set(actor,'modelOffset',fmt(-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*.9184123273));s.blocks[actor]+='  seatedArmWeight: 0.18\n'
# Keep current venue visibility lists; move original instrument within that group.
for go,b in list(s.blocks.items()):
 if s.kind(go)==1 and 'original koto' in s.name(go):
  tr=s.transform(go);p=vec(s.blocks[tr],'m_LocalPosition');p+=[0,.12,.35];s.set(tr,'m_LocalPosition',fmt(p))
restoration=[]
for i,(x,z) in enumerate([(-5,-25),(3,-24),(-49,18)]):
 root=empty('Restored village flower bed '+str(i));place('vt46',[x,terrain.height(x,z),z],height=.65,parent=s.transform(root),label='request restored flowers');restoration.append(s.transform(root));s.set(root,'m_IsActive',0)
h.add_component(s,gamego,'VillageLife','  game: {fileID: '+str(game)+'}\n  restorationBeds:\n'+''.join('  - {fileID: '+str(t)+'}\n' for t in restoration))
# Clear stale unused aliases left by earlier seated-pose replacements.
for cid,b in list(s.blocks.items()):
 if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b:continue
 resource=re.search(r'^  resource: (.+)',b,re.M)[1];folder=RES.parent/resource;posefile=folder/'Poses.bytes'
 if not posefile.exists():continue
 clips=bank(posefile);idle=re.search(r'^  idle: (\S+)',b,re.M)[1]
 for key in ['walk','run','windup','strike','recover','death']:
  found=re.search(r'^  '+key+r': (\S+)',b,re.M)
  if found and found[1] not in clips:s.set(cid,key,next((n for n in clips if n.endswith('_010')),idle) if key=='walk' else idle)
s.save()
# Navigation follows moved market footprints, old entrances become clear.
p=A/'Sunward/Data/Valley.json';data=json.loads(subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT))
for b in data['world']['boxes']:
 if abs(b['z'])<.1 and abs(abs(b['x'])-4.8)<.1:b['x']=-6 if b['x']>0 else 5;b['z']=30;b['halfX']=3.2;b['halfZ']=1.7
p.write_text(json.dumps(data,separators=(',',':'))+'\n')
for f in [OUT,*OUT.rglob('*')]:
 if not f.name.endswith('.meta'):guid(f)
Path(__file__).with_name('world-changes.json').write_text(json.dumps(dict(base=BASE,placements=ledger,rooms=homeinfo,crops=crops,clippedDojoFloors=clipped,retiredCherryParts=cherry,marketParts=market,shaft=shaft),indent=2)+'\n');print('Installed',len(rooms),'homes,',len(crops),'crops, moved markets, farm shop, routines and shaft relief')
