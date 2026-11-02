"""Saved scene and source-resource checks. These do not run Unity."""
from pathlib import Path
import re,json,struct,subprocess
import numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';B='4c51e08ab9caf23684e89337df96646b263ce02b';checks=0

def check(ok,msg):
 global checks;checks+=1
 assert ok,msg

def blocks(text):return {int(re.search(r'&(-?\d+)',b)[1]):b for b in re.split(r'(?=--- !u!)',text) if b.startswith('--- !u!')}
def ref(b,key):return int(re.search(re.escape(key)+r': \{fileID: (\d+)',b)[1])
def vec(b,key):return np.array([float(x) for x in re.search(re.escape(key)+r': \{x: ([^,]+), y: ([^,]+), z: ([^}]+)',b).groups()])
p=A/'Sunward/Scenes/Windflower.unity';s=blocks(p.read_text());old=blocks(subprocess.check_output(['git','show',B+':'+str(p.relative_to(R))],cwd=R).decode());check(set(old)<=set(s),'Existing scene entities removed')
for id,b in s.items():
 if 'Assembly-CSharp::Sunward.HomeCutaway\n' in b or 'Assembly-CSharp::Sunward.Remaster.VenueVisibility\n' in b:
  m=re.search(r'  contents:\n((?:  - .*\n)*)',b)
  for target in map(int,re.findall(r'fileID: (\d+)',m[1])):check(target in s and s[target].startswith('--- !u!1 '),'Invalid interior content reference')
root=next(b for b in s.values() if b.startswith('--- !u!1660057539 '));roots=set(map(int,re.findall(r'fileID: (\d+)',root)))
for id,b in s.items():
 if b.startswith('--- !u!4 ') and 'm_LocalPosition:' in b and ref(b,'m_Father')==0:check(id in roots,'Detached object missing from SceneRoots')
for id in [1439298638,2027807469]:check(abs(vec(s[id],'station')[2]+31)<.001,'Vendor runtime station still in front of merchandise')
flow=(A/'Sunward/Scripts/GameFlow.cs').read_text();check('Consider("weapons", new Vector3(-6, 0, -27.6f)' in flow and 'Consider("shop", new Vector3(5, 0, -27.6f)' in flow,'Market interaction hotspots remain behind the moved vendors/rear wall')
repeated=[b for b in s.values() if 'bridge approach stone' in b and b.startswith('--- !u!1 ')]
check(len(repeated)>=10 and all('m_IsActive: 0' in b for b in repeated),'Actual repeating approach stones remain visible')
for b in s.values():
 if 'Assembly-CSharp::Sunward.Remaster.NativeArcheryPose\n' in b:check('m_Enabled: 0' in b,'User-rejected procedural archer alignment remains enabled')
for id in [8000000000000011275,8000000000000011276]:check('contactEnabled: 0' in s[id],'Archer fires while no native shooting clip is bound')
susano=vec(s[8000000000000010615],'m_LocalPosition');check(susano[0]<-5 and abs(susano[1]+249.5)<.05,'Susano is still under the raised central platform')
check('motion: hm08_087' in s[8000000000000011274],'Missing original continuous sword-practice motion')
check('walk: hm00_010' in s[8000000000000011215],'Farmer still walks in an idle pose')
res=A/'OkamiRemaster/Original/Resources/Okami'
for name in ['dr06','vt00','em11']:
 folder=res/name;m=json.loads((folder/'Model.json').read_text());check(m['version']==1,'Native model version')
 check(all(-1<=b['parent']<i for i,b in enumerate(m['bones'])),'Invalid bone hierarchy '+name)
 for part in m['parts']:
  v=np.array(part['positions']).reshape(-1,3);ix=np.array(part['indices']);weights=np.array(part['weights']).reshape(-1,3);bones=np.array(part['boneIndices']);check(np.isfinite(v).all() and ix.min()>=0 and ix.max()<len(v),'Native mesh/index corruption '+name);check(np.allclose(weights.sum(1),1,atol=.001) and bones.min()>=0 and bones.max()<len(m['bones']),'Native weights '+name)
 for tex in m['textures']:check((folder/tex['path']).is_file(),'Missing native texture '+name)
m=json.loads((res/'em11/Model.json').read_text());head=next(x for x in m['parts'] if x['name']=='Native-3-0');source=json.loads((res/'crimson-armour/Model.json').read_text())['parts'][0];original=set(map(tuple,np.array(source['positions']).reshape(-1,3)));check(len(head['indices'])>600 and all(tuple(x) in original for x in np.array(head['positions']).reshape(-1,3)),'Crimson face is not original WP19 face geometry')
bindings=json.loads((A/'OkamiRemaster/Player/Resources/NativePlayer/Bindings.json').read_text())['bindings'];check(next(b for b in bindings if b['state']=='Tundra_Cast')['clip']=='pl00_54c','Charged release still uses near-static ready pose')
audio=json.loads((res/'NativeAudio.json').read_text())['cues'];steps={x['resource'] for x in audio if x['cue']=='step'};water={x['resource'] for x in audio if x['cue']=='water'};check(steps and water and not steps&water and all('dry-ground' in x for x in steps),'Walking still routes wet surface sounds')
for x in audio:
 if x['cue'] in ['step','water','swim-exit','housemusic']:check(any((A1/(x['resource']+ext)).is_file() for A1 in A.rglob('Resources') for ext in ['.wav','.ogg']),'Missing cue resource '+x['resource'])
guids={}
for p in A.rglob('*.meta'):
 m=re.search(r'^guid: (\w+)',p.read_text(),re.M)
 if m:guids.setdefault(m[1],[]).append(p)
new=subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','Sunward-Unity/Assets'],cwd=R).decode().split('\0')+subprocess.check_output(['git','diff',B,'--name-only','--diff-filter=A','-z','--','Sunward-Unity/Assets'],cwd=R).decode().split('\0')
for name in set(filter(None,new)):
 p=R/name
 if p.suffix=='.meta':continue
 meta=Path(str(p)+'.meta');check(meta.is_file(),'Missing metadata '+name);guid=re.search(r'^guid: (\w+)',meta.read_text(),re.M)[1];check(len(guids[guid])==1,'New GUID collision '+name)
check((A/'OkamiRemaster/Original/Scripts/OriginalAtmosphere.cs').read_bytes()==subprocess.check_output(['git','show',B+':Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/OriginalAtmosphere.cs'],cwd=R),'Existing Shiranui atmospheric effects changed')
print('PASS',checks,'scene/resource/metadata contracts; not Unity compilation, playback, audio listening or physics validation.')
