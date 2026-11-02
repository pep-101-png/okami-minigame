"""Source/geometry contracts; no Unity runtime, physics or visual approval."""
from pathlib import Path
import json,re,sys,subprocess
import numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets'
sys.path.insert(0,str(Path(__file__).parent));import scene_data as d
d.A=A;w=d.World();s=w.scene;rows=list(w.renderers());bygo={r['go']:r for r in rows if not r['instance']};checks=0

def check(ok,why):
 global checks;checks+=1
 assert ok,why
oldtext=subprocess.check_output(['git','show','62a8bb273964c495ccfa3f5ae155684980ee9d5c:Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'],cwd=R).decode();old={int(re.search(r'&(-?\d+)',b)[1]):b for b in re.split(r'(?=--- !u!)',oldtext) if b.startswith('--- !u!')}
for i in [8000000000000010614,8000000000000010615,8000000000000010618,8000000000000011274,8000000000000011982]:check(s.blocks[i]==old[i],'Working Susano setup changed')
for go in [8000000000000010362,8000000000000010367,8000000000000010372,8000000000000010377,8000000000000010382]:check('m_IsActive: 0' in s.blocks[go],'Dojo interior walls still duplicated outdoors')
for i in [8000000000000011275,8000000000000011276]:check('motion: hm2d_080' in s.blocks[i] and 'contactEnabled: 1' in s.blocks[i] and 'releasePhase: 0.225' in s.blocks[i],'Native archer draw/release/contact not connected')
check(s.blocks[8000000000000011983].split('  feet:\n')[1]==s.blocks[8000000000000011984].split('  feet:\n')[1],'Archer support indices do not match its recovered guard rig')
for i in [8000000000000010623,8000000000000010628]:check('resource: Okami/dojo-hm2d' in s.blocks[i],'Archer body differs from native shot skeleton')
dressing=(A/'OkamiRemaster/Original/Scripts/NativeInteriorDressing.cs').read_text();check('AddEntrance' not in dressing,'Freestanding exterior panels still generated');check('forceRenderingOff' in dressing and '.layer=' not in dressing,'Interior isolation changes physics layers')
rooms=[]
for i,b in s.blocks.items():
 if 'Assembly-CSharp::Sunward.Remaster.NativeHomeRoom\n' not in b:continue
 centre=w.matrix(0,s.transform(s.owner(i)))[:3,3];num=int(re.search('  number: (\\d+)',b)[1]);rooms.append(num);check('doorInward:' in b and 'roomStyle:' in b and 'wallResource:' in b,'Missing directional doorway or individual room style')
 content=list(map(int,re.findall('fileID: (\\d+)',b.split('  contents:\n')[1])));floor=next(go for go in content if 'Home-floor-' in s.name(go));r=bygo[floor];m=w.mesh(r['meshGUID'],r['meshID']);p=m['vertices'][np.unique(m['triangles'])]@r['matrix'][:3,:3].T+r['matrix'][:3,3]
 check(np.abs(p[:,1]-centre[1]).max()<.06,'Complete home floor has incorrect parent/world offset: '+str(num));check(np.ptp(p[:,0])>7.5 and np.ptp(p[:,2])>5.5,'Complete home floor no longer covers its room')
 for go in content:
  if 'recovered timber floor' not in s.name(go) and 'woven tatami sitting' not in s.name(go):continue
  r=bygo[go];m=w.mesh(r['meshGUID'],r['meshID']);v=m['vertices']@r['matrix'][:3,:3].T+r['matrix'][:3,3];f=m['triangles'];p=v[np.unique(f)];norm=np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]])
  check(np.abs(p[:,1]-centre[1]).max()<.04,'Decorative floor left its host interior');check(np.max(np.abs(p[:,0]-centre[0]))<4.02 and np.max(np.abs(p[:,2]-centre[2]))<3.02,'Decorative floor spills through room walls');check(np.all(norm[:,1]>0),'Native floor winding no longer faces up')
check(len(rooms)==12,'Expected all twelve existing NPC homes')
res=A/'OkamiRemaster/Original/Resources/Okami'
def bank(path):
 import struct
 data=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',data);assert magic==b'OPB1' and version==1;offset=16;clips={}
 for _ in range(count):
  length=struct.unpack_from('<I',data,offset)[0];offset+=4;name=data[offset:offset+length].decode();offset+=length;frames,duration,loop=struct.unpack_from('<IfI',data,offset);offset+=12;poses=np.frombuffer(data,'<f4',frames*bones*10,offset).reshape(frames,bones,10);offset+=poses.nbytes;clips[name]=(poses,duration,loop)
 return clips

for package,idle,gait in [('hm1c','hm1c_000','hm1c_011'),('hm1d','hm1c_000','hm1c_011'),('an05','an18_000','an18_011')]:
 m=json.loads((res/package/'Model.json').read_text());poses=bank(res/package/'Poses.bytes');check(idle in poses and gait in poses,'Missing original street gait');check(poses[gait][0].shape[1]==len(m['bones'])+1,'Street model/native motion skeleton mismatch');check(np.isfinite(poses[gait][0]).all(),'Nonfinite source street animation')
for package in ['et50','et03','et07','vt33','vt34','vt32','vt62','dr0c','dr0e','vt9b']:
 m=json.loads((res/package/'Model.json').read_text());check(bool(m.get('sourceSHA256')),'Missing original model provenance')
 for t in m['textures']:check((res/package/t['path']).is_file(),'Missing original paint texture')
festival=(A/'OkamiRemaster/Original/Scripts/VillageFestival.cs').read_text();check('for(int row=0;row<6;row++)' in festival and 'for(int i=0;i<5;i++)' in festival,'Overhead lantern strings incomplete');check('festival.SetActive(true)' in festival,'Festival decorations disappear by day')
print('PASS',checks,'doorway/room/source-asset contracts; not Unity compilation or gameplay verification')
