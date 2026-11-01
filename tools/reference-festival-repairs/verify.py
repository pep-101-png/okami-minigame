"""Asset/scene contracts only. Not a Unity build or rendered gameplay test."""
from pathlib import Path
import subprocess,json,re,struct
import numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';BASE='76aebc1f850c2cc631ccea482d3b7cd16f6bf4d5';checks=0

def check(ok,msg):
 global checks;checks+=1
 assert ok,msg

def old(p):return subprocess.check_output(['git','show',BASE+':'+str(p.relative_to(R))],cwd=R)
def blocks(s):return {int(re.search(r'&(-?\d+)',b)[1]):b for b in re.split(r'(?=--- !u!)',s) if b.startswith('--- !u!')}
def fieldref(b,name):return int(re.search(name+r': \{fileID: (\d+)',b)[1])
def transform(s,go):return fieldref(s[go],'component')
def vector(b,name):return np.array([float(x) for x in re.search(name+r': \{x: ([^,]+), y: ([^,]+), z: ([^}]+)',b).groups()])
p=A/'Sunward/Scenes/Windflower.unity';s=blocks(p.read_text());before=blocks(old(p).decode());check(set(before)<=set(s),'Existing scene IDs lost')
ledger=json.loads(Path(__file__).with_name('scene-changes.json').read_text())
for go in ledger['removedFloorInstrument']+ledger['disabledOldPondPieces']:check('m_IsActive: 0' in s[go],'Old floor instrument/pond tree still active')
for b in s.values():
 if 'Assembly-CSharp::Sunward.Remaster.VenueVisibility\n' in b:
  for go in ledger['removedFloorInstrument']:check('{fileID: '+str(go)+'}' not in b,'Venue reactivates removed floor instrument')
for go in ledger['newSlimCherries']:check('m_IsActive: 1' in s[go] and 'Pond cherry' in s[go],'Missing new slim cherry part')
for instance in [2027807467,1439298636]:
 b=s[instance];check('propertyPath: m_LocalRotation.y\n      value: 0' in b and 'propertyPath: m_LocalRotation.w\n      value: 1' in b,'Vendor not turned')
 for axis in 'xyz':
  pat=r'propertyPath: m_LocalPosition\.'+axis+r'\n      value: ([^\n]+)';check(re.findall(pat,b)==re.findall(pat,before[instance]),'Market moved unexpectedly')
for id in [8000000000000011275,8000000000000011276]:check('releasePhase: 0.55' in s[id] and 'archer: 1' in s[id],'Archer release/role')
for go in [8000000000000010119,8000000000000010123]:
 pos=vector(s[transform(s,go)],'m_LocalPosition');check(not np.allclose(pos,vector(before[transform(before,go)],'m_LocalPosition')) and 'grounded clear of practice lanes' in s[go],'Dojo lantern not moved from old placement')
check(sum('Assembly-CSharp::Sunward.Remaster.NativeArcheryPose\n' in b for b in s.values())==2,'Archery adapters missing')
check(sum('Assembly-CSharp::Sunward.Remaster.NativeHeldInstrument\n' in b for b in s.values())==1,'Held flute missing')
res=A/'OkamiRemaster/Original/Resources/Okami';armour=json.loads((res/'crimson-armour/Model.json').read_text());body=json.loads((res/'em11/Model.json').read_text())
check(len(armour['bones'])==36,'Wrong armour skeleton')
for i in range(32):check(armour['bones'][i]==body['bones'][i],'Armour/body core bind mismatch '+str(i))
check(sum(len(p['positions'])//3 for p in armour['parts'])==2739,'Wrong original armour mesh')
for name in ['crimson-armour','native-flute']:
 folder=res/name;m=json.loads((folder/'Model.json').read_text());check(len(m['sourceSHA256'])==64,name+' missing source provenance')
 for p in m['parts']:
  v=np.array(p['positions']).reshape(-1,3);idx=np.array(p['indices']);w=np.array(p['weights']).reshape(-1,3);bi=np.array(p['boneIndices']);check(np.isfinite(v).all() and idx.min()>=0 and idx.max()<len(v),name+' mesh');check(bi.min()>=0 and bi.max()<len(m['bones']) and np.allclose(w.sum(1),1,atol=.001),name+' skin')
 for t in m['textures']:check((folder/t['path']).is_file(),name+' missing texture')
def bank(path):
 data=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',data);check(magic==b'OPB1' and version==1,'Pose bank header');offset=16;clips={}
 for _ in range(count):
  n=struct.unpack_from('<I',data,offset)[0];offset+=4;name=data[offset:offset+n].decode();offset+=n;frames,duration,loop=struct.unpack_from('<IfI',data,offset);offset+=12;pose=np.frombuffer(data,'<f4',frames*bones*10,offset).reshape(frames,bones,10);offset+=pose.nbytes;check(duration>0 and np.isfinite(pose).all(),'Nonfinite motion '+name);clips[name]=pose
 check(offset==len(data),'Pose bank truncated');return bones,clips
n,clips=bank(res/'crimson-armour/Poses.bytes');check(n==37 and 'wp19_000' in clips,'Armour motion source')
n,clips=bank(res/'hm05/Poses.bytes');check('venue_flute' in clips,'Missing flute arm motion');base=clips['hm05_003'][0] if 'hm05_003' in clips else clips['venue_seated'][0];pose=clips['venue_flute'];mask=np.ones(pose.shape[1:],dtype=bool);mask[6:12,3:7]=False;check(np.allclose(pose[:,mask],base[mask]),'Flute retarget modifies seated body/legs')
actor=(A/'OkamiRemaster/Original/Scripts/OriginalActor.cs').read_text();check('Okami/crimson-armour' in actor and 'Okami/em65' not in actor,'Wrong Crimson first-phase resource')
for rel in ['Sunward/Scripts/OrbitCamera.cs','OkamiRemaster/Original/Scripts/OriginalAtmosphere.cs','OkamiRemaster/Original/Scripts/LowerArena.cs']:
 p=A/rel;check(p.read_bytes()==old(p),'Existing camera/orbs/boss exit changed '+rel)
guids={}
for p in A.rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',p.read_text(),re.M)
 if m:guids.setdefault(m[1],[]).append(p)
changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A','-z','--','Sunward-Unity/Assets'],cwd=R).decode().split('\0')+subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','Sunward-Unity/Assets'],cwd=R).decode().split('\0')
for name in set(filter(None,changed)):
 p=R/name
 if p.suffix=='.meta':continue
 meta=Path(str(p)+'.meta');check(meta.is_file(),'Missing meta '+name);g=re.search(r'^guid: (\w+)',meta.read_text(),re.M)[1];check(len(guids[g])==1,'New GUID collision '+name)
print('PASS',checks,'scene/resource contracts; NOT Unity rendering, playback, sound or physics verification.')
