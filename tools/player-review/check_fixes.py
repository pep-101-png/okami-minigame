"""Check saved layout and assets from the player's issue list, without Unity claims."""
from pathlib import Path
import sys,re,json,hashlib,wave,itertools
import numpy as np
sys.path.insert(0,str(Path(__file__).parent))
from scene_tools import *
from build import Sources
s=Scene(ASSETS/'Scenes/Windflower.unity');src=Sources(s);ix=asset_index();cache={}
assert all(not src.visible(n) for n in [371,408,409,*range(841,876)]),'Legacy river/bridge/bamboo source still visible'
rooms=[]
for go in s.blocks:
 if s.kind(go)!=1 or not active(s,go):continue
 if s.name(go) in ['Living places · Windflower training shrine roof','Living places · Street food hall roof']:
  rooms.append((s.name(go),bounds(s,go,src,ix,cache)))
assert len(rooms)==2
for label,(lo,hi) in rooms:
 for go in s.blocks:
  if s.kind(go)!=1 or not active(s,go) or not s.name(go).startswith('Village house ') or 'closed' not in s.name(go):continue
  a,b=bounds(s,go,src,ix,cache)
  overlap=np.minimum(hi[[0,2]],b[[0,2]])-np.maximum(lo[[0,2]],a[[0,2]])
  assert not (overlap>0).all(),('Room roof intersects neighbouring roof',label,s.name(go),overlap)
# Verify no surviving grounded rock occupies the actual bridge walking footprint.
for go in s.blocks:
 if s.kind(go)!=1 or not active(s,go) or not s.name(go).startswith('Grounded stone '):continue
 lo,hi=bounds(s,go,src,ix,cache)
 for z in [-8,14]:assert not (hi[0]>-27.6 and lo[0]<-18.4 and hi[2]>z-1.27 and lo[2]<z+1.27 and hi[1]>.08),('Bridge obstruction',s.name(go))
# Four inventories must have different actual vertex geometry, not recolours.
paths=[ASSETS/'Generated/LivingPlaces'/('stall '+str(k)+' hand arranged produce.asset') for k in range(4)]
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})==4
pillow=ASSETS/'Generated/LivingPlaces/food hall listening mat woven wicker.asset';raw=pillow.read_text();ext=vec(raw,'m_Extent')
assert ext[0]*2<1.1 and ext[2]*2<1.3,'Listening pillow still sleep-bed sized'
training=eating=0
for i,b in s.blocks.items():
 if s.kind(i)!=114 or 'Assembly-CSharp::Sunward.ResidentPerformance\n' not in b:continue
 if '  activity: 1\n' in b:
  assert re.search(r'practiceSword: \{fileID: [1-9]\d*\}',b);training+=1
 if '  activity: 2\n' in b:
  assert re.search(r'mealBowl: \{fileID: [1-9]\d*\}',b) and re.search(r'teaCup: \{fileID: [1-9]\d*\}',b);eating+=1
assert (training,eating)==(2,2)
with wave.open(str(ASSETS/'Generated/LivingVillagers/Foodhall-bowed-pentatonic.wav')) as audio:
 samples=np.frombuffer(audio.readframes(audio.getnframes()),dtype='<i2')/32768.
 assert np.max(np.abs(samples))<.92 and np.sqrt(np.mean(samples*samples))>.01
 assert max(abs(samples[0]),abs(samples[-1]))<.0001,'Audible loop endpoint discontinuity'
combat=(ASSETS/'Scripts/WolfCombat.cs').read_text();assert combat.count('ShieldPresentationRules.Visible(')==5
assert 'discAnchor.position = backSocket' not in combat
prefab=Scene(ASSETS/'Generated/Sundial.prefab');assert not any(prefab.kind(i) in [54,64,65,82,136] for i in prefab.blocks),'Weapon unexpectedly contains collision/audio'
report={'scope':'Static/asset tests only; Unity rendering and runtime remain unverified','nonoverlappingRoomRoofs':2,'uniqueStallInventories':4,'heldPracticeSwords':training,'dinerBowlAndCupBindings':eating,'legacyBambooPartsHidden':35,'shieldCollidersAndAudioSources':0,'musicPCMAndLoop':'passed','bridgeObstructions':'none'}
Path(__file__).with_name('checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
