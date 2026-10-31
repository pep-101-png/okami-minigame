"""Patch the existing tested scene; native poses and physics must agree at startup."""
from pathlib import Path
import sys,json,re,math,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/playtest-repair'));import install_repairs as previous
from export_assets import A,OUT,RES,guid
from install_world import add_component,patch
from scene_data import World,ref,Terrain
from native import Scene,vec,fmt
BASE='045e48e7f07054b81876c58fe5975cb4616c3139'
def run():

 for name in ['NPC-0.prefab','NPC-1.prefab']:
  target=A/'Sunward/Generated'/name;target.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(target.relative_to(ROOT))],cwd=ROOT))
 p=A/'Sunward/Scenes/Windflower.unity';p.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(ROOT))],cwd=ROOT));w=World();s=w.scene;terrain=Terrain(w);report={}
 # Make furniture roots obey cutaway state, including dynamically generated children.
 for i,b in list(s.blocks.items()):
  if 'Assembly-CSharp::Sunward.HomeCutaway\n' in b:
   ids=[int(x) for x in re.findall(r'fileID: (\d+)',b.split('  interior:\n')[1])];roots=list(dict.fromkeys(s.owner(x) for x in ids));s.blocks[i]+='  contents:\n'+''.join('  - {fileID: '+str(x)+'}\n' for x in roots)
 # Real door geometry is already in the exterior. Remove the freestanding marker.
 marker=set()
 for go,b in list(s.blocks.items()):
  if s.kind(go)==1 and 'training hall south door' in s.name(go):
   rid=s.component(go,23);s.set(rid,'m_Enabled',0);marker.add(rid)
 # Native room floor flush to local ground, matching NPC roots/entry/collision.
 floor=[]
 for go,b in list(s.blocks.items()):
  if s.kind(go)!=1:continue
  name=s.name(go)
  if 'food house floor' in name or name=='Food house corrected collision':
   t=s.transform(go);v=vec(s.blocks[t],'m_LocalPosition');v[1]-=.25;s.set(t,'m_LocalPosition',fmt(v))
   if 'floor' in name:floor.append(s.component(go,23))
 pub_roots=[]
 for i,b in list(s.blocks.items()):
  if 'Assembly-CSharp::Sunward.Remaster.VenueVisibility\n' not in b:continue
  for rid in marker:b=b.replace('  - {fileID: '+str(rid)+'}\n','')
  if '  venue: food\n' in b:
   b=b.replace('  interiorSurfaces: []\n','  interiorSurfaces:\n'+''.join('  - {fileID: '+str(r)+'}\n' for r in floor));pub_roots=[int(x) for x in re.findall(r'fileID: (\d+)',b.split('  contents:\n')[1])]
  s.blocks[i]=b
 for go in pub_roots:
  t=s.transform(go);v=vec(s.blocks[t],'m_LocalPosition');v[1]-=.25;s.set(t,'m_LocalPosition',fmt(v))
 # Discard cross-rig seated poses. Every actor uses its own native seated action.
 sources={'hm00':('hm00_003','hm00_020'),'hm01':('hm01_003','hm01_020'),'hm09':('hm05_003','hm05_028'),'hm05':('hm05_003','hm05_028')}
 def seat(actor,package,base,arms):
  raw=s.blocks[actor];standing=re.search(r'  idle: (\S+)',raw)[1];scale,offset=previous.calibration(package,standing,1.8);model=json.loads((RES/package/'Model.json').read_text());posed=previous.skin(model,previous.pose(package,base));mask=model.get('visibleGroups');v=np.concatenate([v for part,v in zip(model['parts'],posed) if not mask or int(part['name'].split('-')[1]) in mask]);center=(v.min(0)+v.max(0))/2;offset=np.array([-center[0],-v[:,1].min(),-center[2]])*scale
  for key in ['idle','walk','run','windup','strike','recover','death']:s.set(actor,key,base)
  s.set(actor,'modelScale',scale);s.set(actor,'modelOffset',fmt(offset));s.blocks[actor]+='  seatedArmMotion: '+arms+'\n'
 for i,b in list(s.blocks.items()):
  if 'Assembly-CSharp::Sunward.Remaster.NativeVenueActor\n' not in b or '  role: training' in b:continue
  actor=ref(b,'actor')[0];raw=s.blocks[actor];package=re.search(r'  resource: Okami/(\S+)',raw)[1];base,arms=sources[package];seat(actor,package,base,arms);s.blocks[i]+='  seatedMotion: '+base+'\n  handMotion: '+arms+'\n'
  if '  role: diner' in b:s.set(s.transform(s.owner(actor)),'m_LocalRotation','{x: 0, y: 1, z: 0, w: 0}')
 # Remove the preserved outdoor offering shrine from inside the new dojo.
 old=json.loads((ROOT/'tools/original-remake/world-install.json').read_text());shrine=next(r for r in old['nativePlacements'] if r['category']=='offering shrine');delta=np.array([0,terrain.height(0,10)-shrine['position'][1],-10])
 for go in shrine['objects']:
  t=s.transform(go);s.set(t,'m_LocalPosition',fmt(vec(s.blocks[t],'m_LocalPosition')+delta))
 # Original NPC2 remains a working NPC, now outside the enlarged dojo wall.
 oldman=812487608;src=w.prefabs[oldman];root=next(i for i in src.blocks if src.kind(i)==4 and ref(src.blocks[i],'m_Father')[0]==0)
 for axis,val in zip('xyz',[-4.2,terrain.height(-4.2,12.1),12.1]):patch(s,oldman,root,'m_LocalPosition.'+axis,val)
 # Complete waterwheel model and its actual native full-turn animation.
 for i,b in list(s.blocks.items()):
  if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' in b and 'resource: Okami/vt6a' in b:
   for key in ['idle','walk','run','windup','strike','recover','death']:s.set(i,key,'vt6a_001')
   scale,offset=previous.calibration('vt6a','vt6a_001',3.6);s.set(i,'modelScale',scale);s.set(i,'modelOffset',fmt(offset))
 # Larger stalls: both face the approach, merchant centred behind the goods.
 current=json.loads((ROOT/'tools/playtest-repair/scene-repairs.json').read_text());records=next(v for v in current.values() if isinstance(v,list) and v and isinstance(v[0],dict) and 'package' in v[0] and 'objects' in v[0])
 for r in records:
  if r.get('label')=='enlarged working market':
   for go in r['objects']:s.set(s.component(go,23),'m_Enabled',0)
 for package,x in [('vtb5',-7),('vtab',7)]:
  e=previous.MODELS[package];lo=np.array(e['boundsMin']);hi=np.array(e['boundsMax']);scale=np.array([6.4,4.4,5.2])/(hi-lo);rot=np.diag([-1,1,-1]);offset=np.array([x,terrain.height(x,0),0])-rot@(np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*scale)
  for part in e['meshes']:
   go=s.add('Original larger centred '+package,part['mesh'],part['material'],p=offset,scale=scale);s.set(s.transform(go),'m_LocalRotation','{x: 0, y: 1, z: 0, w: 0}')
 # The two existing shop NPCs already have gameplay/interactions. Anchor them;
 # their startup navigation must not push them off their own stall platform.
 for inst,x,package,base,arms in [(2027807467,-7,'hm01','hm01_003','hm01_020'),(1439298636,7,'hm29','hm92_003','hm29_020')]:
  src=w.prefabs[inst];t=next(i for i in src.blocks if src.kind(i)==4 and ref(src.blocks[i],'m_Father')[0]==0);position=[x,terrain.height(x,1.1)+.1,1.1]
  for axis,val in zip('xyz',position):patch(s,inst,t,'m_LocalPosition.'+axis,val)
  patch(s,inst,t,'m_LocalRotation.y',1);patch(s,inst,t,'m_LocalRotation.w',0)
  go=next(s.owner(i) for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.VillageResident\n' in b and re.search(r'  index: (\d+)',b)[1]==('0' if x<0 else '1'))
  resident=next(i for i,b in s.blocks.items() if s.owner(i)==go and 'Assembly-CSharp::Sunward.VillageResident\n' in b);s.blocks[resident]+='  hasStation: 1\n  station: '+fmt(position)+'\n'
  actor=next(i for i,b in src.blocks.items() if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' in b);raw=src.blocks[actor];standing=re.search(r'  idle: (\S+)',raw)[1];scale,offset=previous.calibration(package,standing,1.8);m=json.loads((RES/package/'Model.json').read_text());mask=m.get('visibleGroups');vv=np.concatenate([v for part,v in zip(m['parts'],previous.skin(m,previous.pose(package,base))) if not mask or int(part['name'].split('-')[1]) in mask]);center=(vv.max(0)+vv.min(0))/2;offset=np.array([-center[0],-vv[:,1].min(),-center[2]])*scale
  for key in ['idle','walk','run','windup','strike','recover','death']:src.set(actor,key,base)
  src.set(actor,'modelScale',scale);src.set(actor,'modelOffset',fmt(offset));src.blocks[actor]+='  seatedArmMotion: '+arms+'\n';add_component(src,src.owner(actor),'NativeVenueActor','  actor: {fileID: '+str(actor)+'}\n  role: merchant\n  seatedMotion: '+base+'\n  handMotion: '+arms+'\n');src.path.write_text(src.header+''.join(src.blocks.values()))
 s.save();report.update(base=BASE,pubFloor=.4,doorMarkerRemoved=True,shrine=[0,terrain.height(0,10),10],oldman=[-4.2,0,12.1],markets=[[-7,0,0],[7,0,0]],wheel='vt6a_001 / complete group 1',nativeSeatedActions=sources);Path(__file__).with_name('scene-changes.json').write_text(json.dumps(report,indent=2)+'\n');print('Third-playtest scene corrections applied')
if __name__=='__main__':run()
