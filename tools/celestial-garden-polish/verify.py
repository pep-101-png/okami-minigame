"""Actual original art / new layout / farm clearance audit. Not a Unity run."""
from pathlib import Path
import json,math,re,numpy as np,sys,hashlib,subprocess
from PIL import Image
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';checks=0

def check(ok,msg):
 global checks;checks+=1;assert ok,msg
layout=json.loads((D/'CelestialGarden.json').read_text())['items'];check(len(layout)>350,'Garden lost its extensive original planting/dressing');check(sum(i['kind']=='pond' for i in layout)==3,'Original complete ponds missing');check(sum(i['kind']=='tree' for i in layout)==16,'Native pine groupings missing');check(not any(i['resource'] in ['Okami/heaven-island','Okami/garden-gate','Okami/heaven-pond','Okami/garden-altar'] for i in layout),'Misidentified old dressing restored')
models={}
for item in layout:
 n=item['resource'].split('/')[-1];folder=D/n
 if n not in models:
  m=json.loads((folder/'Model.json').read_text());models[n]=m;check(bool(m.get('sourceSHA256')),'Untraceable model '+n)
  for p in m['parts']:
   v=np.array(p['positions']).reshape(-1,3);check(np.isfinite(v).all() and max(p['indices'])<len(v),'Corrupt native mesh '+n)
  for t in m['textures']:check(t.get('vertexOnly') or (folder/t['path']).exists(),'Missing source paint '+n)
 for value in item['size'].values():check(value>0,'Invalid prop dimensions')
# Reconstruct the same source triangles and normalisation used by VillageFestival.Place.
surfaces=[]
def height(x,z):
 if not surfaces:return None
 tri=np.concatenate(surfaces);a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a;det=b[:,0]*c[:,2]-b[:,2]*c[:,0];valid=abs(det)>1e-8;d0=x-a[:,0];d1=z-a[:,2];u=np.divide(d0*c[:,2]-d1*c[:,0],det,out=np.full(len(a),-1.),where=valid);v=np.divide(b[:,0]*d1-b[:,2]*d0,det,out=np.full(len(a),-1.),where=valid);hit=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001);return float(np.max((a[:,1]+u*b[:,1]+v*c[:,1])[hit])) if hit.any() else None
for item in layout:
 if item['kind']!='ground':continue
 m=models[item['resource'].split('/')[-1]];vv=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in m['parts']]);lo=vv.min(0);hi=vv.max(0);sc=np.array(list(item['size'].values()))/np.maximum(.001,hi-lo);off=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*sc;p=np.array(list(item['position'].values()),dtype=float)
 if item['resource'] not in ['Okami/celestial-meadow','Okami/celestial-terrace']:p[1]+=height(p[0],p[2]) or 0
 a=math.radians(item['yaw']);rot=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])
 for part in m['parts']:
  v=(np.array(part['positions']).reshape(-1,3)*sc+off)@rot.T+p;surfaces.append(v[np.array(part['indices']).reshape(-1,3)])
for i in range(96):
 a=i*math.tau/96;check(height(35*math.cos(a),32*math.sin(a)) is not None,'Gap in guarded garden perimeter')
for x,z in [(0,-25),(0,-20),(0,17),(0,22),(18,-12),(-23,7)]:
 h=height(x,z);check(h is not None and -.5<h<7,'Missing/unsafe arrival, keeper or visitor floor')
# Every illustration is the original 1024px alpha artwork, not an offline mesh diagnostic.
for i in range(15):
 p=D/'WeaponPortraits'/f'wp{0x20+i:02x}.png';im=Image.open(p);check(im.size==(1024,1024) and im.mode=='RGBA','Catalogue lacks original equipment illustration');check(im.getextrema()[3][0]==0 and im.getextrema()[3][1]==255,'Lost native artwork alpha')
ledger=json.loads(Path(__file__).with_name('farm-cleanup.json').read_text());scene=(A/'Sunward/Scenes/Windflower.unity').read_text()
for go in ledger['disabledSceneObjects']:
 b=re.search(r'--- !u!1 &'+str(go)+r'\n.*?(?=--- !u!)',scene,re.S)[0];check('m_IsActive: 0' in b,'Old pen rock/bamboo remains visible')
for cid in ledger.get('disabledObsoleteColliders',[]):
 b=re.search(r'--- !u!136 &'+str(cid)+r'\n.*?(?=--- !u!)',scene,re.S)[0];check('m_Enabled: 0' in b,'Obsolete pen collision remains active')
animals=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json').read_text())['actors'];check(len(animals)==13 and sum(a['asset']=='rooster' for a in animals)==2,'Original farm population lost');check('if (!FindSpawn(p,asset.radius))' in (A/'OkamiRemaster/Windflower/Scripts/WindflowerAnimals.cs').read_text(),'Blocked bird coordinates are still silently skipped without trying their yard')
f=(A/'OkamiRemaster/Original/Scripts/FestivalChallenges.cs').read_text();check('kind==1?50:90' in f,'Race duration is not 50 seconds');check('RUN · 50 seconds' in (A/'Sunward/Scripts/ScrollUI.cs').read_text(),'Race caption mismatch')
for n in ['CelestialGround','CelestialWater','HeavenCloud']:check((D/'Effects'/(n+'.mat')).exists(),'Garden shader is not reachable through a bundled material')
print('PASS',checks,'native art, floor coverage, garden layout, race and farm clearance checks; NOT Unity playback or rendering')
