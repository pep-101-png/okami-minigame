"""Content/provenance checks, not Unity rendering, sound listening or gameplay approval."""
from pathlib import Path
import json,hashlib,re,numpy as np,sys
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';res=A/'OkamiRemaster/Original/Resources/Okami';S=A/'OkamiRemaster/Original/Scripts';count=0
def check(v,msg):
 global count
 count+=1;assert v,msg
ledger=json.loads(Path(__file__).with_name('source-provenance.json').read_text());b=next(x for x in ledger if x.get('id')=='PL00-41');clip=res/'NativeAudio/player-pl00-41-bark.wav'
check(hashlib.sha256(clip.read_bytes()).hexdigest()==b['outputSHA256'],'Bark differs from selected audition recording');check(b['streamIndex']==41 and b['source']=='data_pc/se/pl/pl00.ses' and b['userConfirmation'],'Wrong sound/event or no listening confirmation')
entries=json.loads((res/'NativeAudio.json').read_text())['cues'];check([e['resource'] for e in entries if e['cue']=='bark']==['Okami/NativeAudio/player-pl00-41-bark'],'Bark cue rotates or points to puppy bank')
check('if(id=="bark")return' not in (A/'Sunward/Scripts/ValleyAudio.cs').read_text(),'Approved bark remains muted')
for resource in ['farm-rail','river-waterfall','river-spirit-portal','garden-gate','garden-altar','heaven-island','heaven-cloud','heaven-pond','trailer-moon','garden-hm40','garden-hm50','garden-hm06']:
 folder=res/resource;m=json.loads((folder/'Model.json').read_text());check(bool(m['parts']),'Empty original model '+resource)
 for p in m['parts']:
  v=np.array(p['positions']);check(np.isfinite(v).all(),'Nonfinite geometry');check(len(v)%3==0 and max(p['indices'])<len(v)//3,'Invalid original triangle index');t=next(t for t in m['textures'] if t['index']==p['texture']);check(t.get('vertexOnly') or (folder/t['path']).exists(),'Unresolved original paint')
 for p in folder.iterdir():
  if p.suffix!='.meta':check(Path(str(p)+'.meta').exists(),'Missing asset metadata '+str(p))
for resource in set(re.findall(r'"(Okami/[a-z0-9-]+)"',(S/'HeavenlyGarden.cs').read_text())):
 check((res/resource.split('/')[-1]/'Model.json').exists(),'Missing runtime garden model '+resource)
rail=json.loads((res/'farm-rail/Model.json').read_text());check(rail['sourceName']=='r102/saku_ly16' and rail['sourceParts']==[10],'Weapon rack or unrelated object used as farm fence')
farm=(S/'VillageFarm.cs').read_text();check('Okami/vt4e' not in farm,'Weapon racks are still pen rails');check(farm.count('Earth(new Vector3')==1,'Repeated circular crop beds restored');check('54.2f,0,38.2f' in farm and '54.2f,0,38.2f' in (S/'NativeDailyRoutine.cs').read_text(),'Camp and bedtime route disagree')
spa=json.loads((res/'spa-hm16/Model.json').read_text());check(spa['visibleGroups']==[0,2],'Separate spa ornament still displayed');check('seatedArmMotion="hm05_027"' in farm and len(spa.get('omittedHeldProps',[]))==8,'Spa source gesture or held-prop cleanup missing')
flow=(A/'Sunward/Scripts/GameFlow.cs').read_text();waves=flow[flow.index('static readonly string[][] waves'):flow.index('void Awake()')];check(waves.count('new[]')==5,'Upper trial is not five normal waves');check('"boss"' not in waves,'Boss placed in upper waves')
ui=(A/'Sunward/Scripts/ScrollUI.cs').read_text();check('Times New Roman' not in ui and 'CreateDynamicFontFromOSFont' not in ui,'OS font is still the visible menu lettering');check('GUILayout.Label(' not in ui and 'GUILayout.Button(' not in ui,'Default rectangular text/button rendering remains');check('MenuScrollBody' in ui and 'MenuScrollRoll' in ui,'Scroll atlas is stretched as one broken sheet')
from PIL import Image
source=Image.open(res/'UI/SystemScroll.png').convert('RGBA')
for n,box in [('MenuScrollBody',(256,68,512,452)),('MenuScrollRoll',(16,10,116,502))]:check(np.array_equal(np.array(Image.open(res/'UI'/(n+'.png')).convert('RGBA')),np.array(source.crop(box))),'Menu art is not the original atlas crop')
for i in range(0x20,0x2f):
 p=res/'WeaponPortraits'/f'wp{i:02x}.png';check(p.exists() and Image.open(p).size==(1024,1024),'Missing catalogue portrait '+str(i))
for name in ['FarmEarthBlend','FallingWater']:
 p=res/'Effects'/(name+'.mat');check(p.exists() and 'NativeFormatImporter:' in Path(str(p)+'.meta').read_text(),'Runtime shader not included through a valid material')
for name in ['OriginalFarmEarth','OriginalFallingWater']:
 p=A/'OkamiRemaster/Original/Shaders'/(name+'.shader.meta');check('ShaderImporter:' in p.read_text(),'Invalid shader importer')
# New actor skeletons must agree with their own original pose banks.
sys.path.insert(0,str(R/'tools/real-door-street-repairs'));from verify import bank
for resource in ['garden-hm40','garden-hm50','garden-hm06']:
 m=json.loads((res/resource/'Model.json').read_text());poses=bank(res/resource/'Poses.bytes')
 for motion,(a,d,l) in poses.items():check(a.shape[1]==len(m['bones'])+1 and np.isfinite(a).all(),'Garden actor pose belongs to a different rig');check(d>0,'Invalid native motion duration')
# Probe the source island itself, including the complete guarded perimeter.
island=json.loads((res/'heaven-island/Model.json').read_text());v=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in island['parts']]);lo=v.min(0);hi=v.max(0);scale=np.array([94,2.5,88])/(hi-lo);offset=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*scale
triangles=[]
for part in island['parts']:
 vv=np.array(part['positions']).reshape(-1,3)*scale+offset;triangles.extend(vv[np.array(part['indices']).reshape(-1,3)])
def covered(x,z):
 for a,b,c in triangles:
  mat=np.array([[b[0]-a[0],c[0]-a[0]],[b[2]-a[2],c[2]-a[2]]])
  if abs(np.linalg.det(mat))<1e-7:continue
  u,v=np.linalg.solve(mat,[x-a[0],z-a[2]])
  if u>=0 and v>=0 and u+v<=1:return True
 return False
for i in range(72):
 theta=i*np.pi/36;check(covered(35*np.cos(theta),32*np.sin(theta)),'Garden guard allows walking off original ground')
for x,z in [(0,-20),(0,-25),(0,22),(0,17),(18,-12),(-23,7),(-19,-8),(21,8),(-17,23)]:check(covered(x,z),'Arrival or landmark has no original ground beneath it')
print('PASS',count,'selected-bark/source-fence/native-art/rig/river/garden/catalogue contracts; no Unity or audio approval')
