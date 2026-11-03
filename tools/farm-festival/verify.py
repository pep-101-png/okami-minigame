"""Source/scene/native provenance contracts, not Unity execution or audio listening."""
from pathlib import Path
import sys,json,re,struct,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';sys.path.insert(0,str(ROOT/'tools/real-door-street-repairs'));import scene_data as d
w=d.World();s=w.scene;res=A/'OkamiRemaster/Original/Resources/Okami';checks=0
def check(v,why):
 global checks
 checks+=1;assert v,why
for name in ['farm-roof','farm-walls','spa-hm16','vt08','vt0d','et2b','vt77','vt55','vt99']:
 folder=res/name;m=json.loads((folder/'Model.json').read_text());check(bool(m.get('sourceSHA256')),'No source provenance '+name)
 for part in m['parts']:
  nv=len(part['positions'])//3;check(len(part['colors'])==nv*4 and len(part['uv'])==nv*2,'Attribute shape '+name);check(max(part['indices'])<nv,'Invalid source index '+name)
 for tex in m['textures']:
  if tex.get('path'):check((folder/tex['path']).exists(),'Missing original texture '+name)
 for p in [folder,*[f for f in folder.iterdir() if f.suffix!='.meta']]:check(Path(str(p)+'.meta').exists(),'Missing .meta '+str(p))
# Roof/wall parts are exact copies of original model divisions.
for target,source,part in [('farm-roof','vtb0','Native-1-2'),('farm-walls','vta3','Native-1-0')]:
 actual=json.loads((res/target/'Model.json').read_text())['parts'];native=next(p for p in json.loads((res/source/'Model.json').read_text())['parts'] if p['name']==part);check(actual==[native],'Shelter geometry no longer original '+target)
for i in range(2):
 p=res/'Farm'/f'Rail{i}.asset';source=A/'OkamiRemaster/Original/Meshes'/f'farm-fence-{i}.asset';check(p.read_bytes()==source.read_bytes(),'Railing geometry modified')
# Scene crops retain every original FarmCrop identity and mouth attachment.
crops=[]
for i,b in s.blocks.items():
 if 'Assembly-CSharp::Sunward.Remaster.FarmCrop\n' in b:
  p=d.vec(s.blocks[s.transform(s.owner(i))],'m_LocalPosition');check(41<p[0]<52 and 21<p[2]<26,'Crop not in new rows');crops.append(i)
check(len(crops)==18,'Harvestable crops lost')
for i,b in s.blocks.items():
 if s.kind(i)==1 and any(n in s.name(i) for n in ['farm native water basin','farm stable shelter','farm pen fence','Farm pen collision']):check('m_IsActive: 0' in b,'Old farm dressing still visible')
animals=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json').read_text())['actors'];check(len(animals)==13,'Farm population lost')
for actor in animals:
 p=actor['position'];check(20<=p['x']<=55 and 22<=p['z']<=35,'Animal left farm');check(len(actor['path'])==4,'Lost native walking route')
# The native archery lane has a body-width margin from Susano.
sus=d.vec(s.blocks[s.transform(8000000000000010614)],'m_LocalPosition');start=d.vec(s.blocks[s.transform(8000000000000010624)],'m_LocalPosition');dummy=s.owner(8000000000000010613);end=d.vec(s.blocks[s.transform(dummy)],'m_LocalPosition');v=end[[0,2]]-start[[0,2]];p=sus[[0,2]]-start[[0,2]];u=np.clip(np.dot(p,v)/np.dot(v,v),0,1);distance=np.linalg.norm(p-v*u);check(distance>1.25,'Susano still occupies archer lane')
check('motion: hm08_087' in s.blocks[8000000000000011274],'Working Susano animation changed')
audio=json.loads((res/'NativeAudio.json').read_text())['cues'];bark=[r for r in audio if r['cue']=='bark'];check(len(bark)==1 and bark[0]['resource']=='Okami/NativeAudio/player-pl00-41-bark','Selected original bark not assigned')
for r in audio:check(any((p/Path(r['resource'])).with_suffix(suffix).exists() for p in A.rglob('Resources') for suffix in ['.wav','.ogg']),'Missing sound '+r['cue'])
for package in range(0x20,0x2f):
 for suffix in ['', '-heavy']:check(any(r['cue']=='weapon-wp'+format(package,'02x')+suffix for r in audio),'Weapon attack sound mapping missing')
for r in json.loads(Path(__file__).with_name('audio-provenance.json').read_text()):
 p=res/'NativeAudio'/r['output'];check(hashlib.sha256(p.read_bytes()).hexdigest()==r['outputSHA256'],'Audio payload/provenance mismatch');check(r['conversion']['output']['clippedFraction']==0,'Output clipping')
print('PASS',checks,'farm/native-resource/audio-mapping/archer-lane contracts; no Unity play or listening claimed')
