"""Source/scene/resource contracts only; never Unity rendering or playback proof."""
from pathlib import Path
import json,re,struct,subprocess,hashlib,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';base='f858f91c5abb8d79177ed45b18b9aff3aa3227a8';checks=0
def check(ok,why):
 global checks;checks+=1
 assert ok,why
def prior(p):return subprocess.check_output(['git','show',base+':'+str(p.relative_to(ROOT))],cwd=ROOT)
def blocks(text):return {int(re.search(r'&(-?\d+)',b)[1]):b for b in re.split(r'(?=--- !u!)',text) if b.startswith('--- !u!')}
def v(text,key):return np.array([float(x) for x in re.search(key+r': \{x: ([^,]+), y: ([^,]+), z: ([^}]+)',text).groups()])
scene=A/'Sunward/Scenes/Windflower.unity';s=blocks(scene.read_text());old=blocks(prior(scene).decode());check(set(s)==set(old),'Existing scene entities removed/added unexpectedly')
world=A/'Sunward/Data/Valley.json';j=json.loads(world.read_text());before=json.loads(prior(world));bounds=j['world'].pop('bounds');before['world'].pop('bounds');check(j==before,'World terrain/gameplay source changed beyond movement bounds')
for id,b in s.items():
 if 'Assembly-CSharp::Sunward.Remaster.FarmCrop\n' in b:
  go=int(re.search(r'm_GameObject: \{fileID: (\d+)',b)[1]);tr=int(re.search(r'component: \{fileID: (\d+)',s[go])[1]);x,y,z=v(s[tr],'m_LocalPosition');check(bounds['minX']+.5<x<bounds['maxX']-.5 and -bounds['maxZ']+.5<z<-bounds['minZ']-.5,'Harvestable crop remains outside player bounds')
for id in [8000000000000011274,8000000000000011275,8000000000000011276]:
 check('contactEnabled: 1' in s[id],'Disabled dojo contacts')
 archer=id!=8000000000000011274;check(('archer: 1' in s[id])==archer,'Incorrect practice role')
 if archer:
  actor=int(re.search(r'actor: \{fileID: (\d+)',s[id])[1]);dummy=int(re.search(r'dummy: \{fileID: (\d+)',s[id])[1])
  def position(component):
   go=int(re.search(r'm_GameObject: \{fileID: (\d+)',s[component])[1]);tr=int(re.search(r'component: \{fileID: (\d+)',s[go])[1]);return v(s[tr],'m_LocalPosition')
  check(np.linalg.norm(position(actor)-position(dummy))>8,'Archer placed at melee range')
# Names can use literal UTF-8 or escaped Unity serialization.
removed=[id for id in s if 'm_IsActive: 0' in s[id] and 'm_IsActive: 1' in old[id]];check(len(removed)==18,'Unexpected disabled objects beyond the repeated bridge rock parts')
# Validate all added/changed native models and corresponding pose-bank contracts.
res=A/'OkamiRemaster/Original/Resources/Okami'
for name in ['em65','dojo-hm2e','dojo-arrow']:
 folder=res/name;m=json.loads((folder/'Model.json').read_text());n=len(m['bones'])
 check(all(-1<=b['parent']<i for i,b in enumerate(m['bones'])),name+' hierarchy')
 for p in m['parts']:
  vertices=np.array(p['positions']).reshape(-1,3);indices=np.array(p['indices']);weights=np.array(p['weights']).reshape(-1,3);bones=np.array(p['boneIndices'])
  check(np.isfinite(vertices).all() and len(vertices)>0,name+' nonfinite mesh');check(indices.min()>=0 and indices.max()<len(vertices),name+' index range');check(bones.min()>=0 and bones.max()<n,name+' skin indices');check(np.allclose(weights.sum(1),1,atol=.001),name+' skin weights')
 for t in m['textures']:check((folder/t['path']).is_file(),name+' missing original texture')
 bank=folder/'Poses.bytes'
 if not bank.exists():continue
 data=bank.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',data);check(magic==b'OPB1' and bones==n+1,name+' motion skeleton');offset=16;names=[]
 for _ in range(count):
  size=struct.unpack_from('<I',data,offset)[0];offset+=4;clip=data[offset:offset+size].decode();offset+=size;frames,duration,loop=struct.unpack_from('<IfI',data,offset);offset+=12;pose=np.frombuffer(data,'<f4',frames*bones*10,offset).reshape(frames,bones,10);offset+=pose.nbytes;check(duration>0 and np.isfinite(pose).all(),clip+' nonfinite motion');names.append(clip)
 check(offset==len(data),name+' motion trailing/truncated bytes')
 if name=='em65':check({'em65_000','em65_020','em65_021','em65_022','em65_023','em65_030','em65_032'}<=set(names),'Missing armour combat/cinematic actions')
 if name=='dojo-hm2e':check('dojo_bow_080' in names,'Missing retargeted shared guard motion')
# Every introduced file must carry metadata and no newly introduced GUID may collide.
new=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','Sunward-Unity/Assets'],cwd=ROOT).decode().split('\0');new+=subprocess.check_output(['git','diff',base,'--name-only','--diff-filter=A','-z','--','Sunward-Unity/Assets'],cwd=ROOT).decode().split('\0');new=list(set(new));guids={}
for p in A.rglob('*.meta'):
 match=re.search(r'^guid: (\w+)',p.read_text(),re.M)
 if match:guids.setdefault(match[1],[]).append(p)
for name in filter(None,new):
 p=ROOT/name
 if p.suffix=='.meta':continue
 check(Path(str(p)+'.meta').exists(),'Missing metadata '+name);g=re.search(r'^guid: (\w+)',Path(str(p)+'.meta').read_text(),re.M)[1];check(len(guids[g])==1,'New GUID collision '+name)
ui=(A/'Sunward/Scripts/ScrollUI.cs').read_text();check('if (game.Panel=="")' in ui and 'game.Brush && game.Brush.Drawing' in ui,'Brush can still display a modal menu');check('case "bossVictory"' in ui,'Missing victory screen')
check(subprocess.check_output(['git','diff',base,'--','Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/OriginalAtmosphere.cs'],cwd=ROOT)==b'','Existing triple orbs changed')
print('PASS',checks,'scene/native-resource contracts. NOT Unity compilation, visual, sound or physics verification.')
