"""Check the actual saved revision, with explicit separation from Unity testing."""
from pathlib import Path
import sys,re,json,hashlib,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/player-review'))
from scene_tools import *
from build import Sources
s=Scene(ASSETS/'Scenes/Windflower.unity');src=Sources(s);ix=asset_index();cache={}
objects=[go for go in s.blocks if s.kind(go)==1 and active(s,go)]
roots=[go for go in objects if s.name(go).startswith('Living tree ') and 'bark and branching' in s.name(go)]
assert len(roots)==21
for go in roots:
 assert 'Generated/PlayerReview3/Rooted-trunk-' in str(ix[re.search(r'guid: (\w+)',s.blocks[s.component(go,33)])[1]])
assert not any(s.name(go).startswith('Review 2 · rooted tree transition') for go in objects)
lanterns=[go for go in objects if s.name(go).startswith('Review 3 · coloured festival lantern')]
assert len(lanterns)==24
# Supports are on clear street lanes, not inside any stall's actual geometry.
for go in objects:
 if not s.name(go).startswith('Review 3 · festival posts'):continue
 lo,hi=bounds(s,go,src,ix,cache)
 for side in [-1,1]:
  x=3.06*side;z=(lo[2]+hi[2])/2
  for stall in objects:
   if not s.name(stall).startswith('Living places · stall ') or 'cedar frame' not in s.name(stall):continue
   a,b=bounds(s,stall,src,ix,cache)
   assert not(a[0]-.08<x<b[0]+.08 and a[2]-.08<z<b[2]+.08),('Festival support intersects stall',s.name(stall),x,z)
# Active door arches are wall-attached and have matching authored brackets.
arches=[go for go in objects if s.name(go).startswith('Ink world · curved entrance fascia')]
for go in arches:
 t=s.transform(go);roof=parent(s,t);n=re.search(r'Village house (\d+)',s.name(s.owner(roof)))[1]
 assert any(s.name(o)=='Review 3 · wall anchored doorway supports '+n for o in objects)
 assert vec(s.blocks[t],'m_LocalScale')[1]==.55
bamboo=[ASSETS/f'Generated/LivingWorld/Environment/Bamboo-{n}-culms.asset' for n in range(7)]
assert len({hashlib.sha256(p.read_bytes()).hexdigest() for p in bamboo})==7
for name in ['Foodhall-bowed-pentatonic','Market-wordless-conversation','Village-soft-sole','Dojo-wood-contact']:
 with wave.open(str(ASSETS/f'Generated/LivingVillagers/{name}.wav')) as w:
  a=np.frombuffer(w.readframes(w.getnframes()),dtype='<i2')/32768.;assert np.max(np.abs(a))<.92
  assert a[0]==0 and abs(a[-1])<.0001
steps=(ASSETS/'Scripts/ResidentLocomotion.cs').read_text();assert steps.count('PlayOneShot(')==1 and 'soundBudget.Allow(Time.time)' in steps and 'stepClock.Advance(' in steps
assert 'stepSource.PlayOneShot' not in steps[steps.index('if (contact && !stance[i]'):]
assert 'ShiranuiTest = Button("ShiranuiTest", "<Keyboard>/p", null)' in (ASSETS/'Scripts/WolfInput.cs').read_text()
assert 'shiranuiMane:' in next(b for i,b in s.blocks.items() if s.kind(i)==114 and 'Assembly-CSharp::Sunward.DivineGrowth\n' in b)
trimmed=ASSETS/'Generated/PlayerReview3/Legacy-ink-cleared-market-mill-349.asset'
assert trimmed.exists() and guid(trimmed) in s.path.read_text()
raw=trimmed.read_text();import struct
n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);buf=bytes.fromhex(re.search(r'_typelessdata: ([a-fA-F0-9]+)',raw)[1]);stride=len(buf)//n
v=np.array([struct.unpack_from('<3f',buf,i*stride) for i in range(n)]);tri=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([a-fA-F0-9]+)',raw)[1]),dtype='<u4' if 'm_IndexFormat: 1' in raw else '<u2').reshape(-1,3);vv=v[tri]
market=(abs(vv[:,:,0])<6.3)&(vv[:,:,2]>-8)&(vv[:,:,2]<7)&(vv[:,:,1]>-.3)&(vv[:,:,1]<3.4)
mill=(vv[:,:,0]>-31)&(vv[:,:,0]<-17)&(vv[:,:,2]>3)&(vv[:,:,2]<12)&(vv[:,:,1]>-2)&(vv[:,:,1]<4)
assert not (market|mill).all(1).any(),'Legacy ink faces remain in cleared regions'
report={'legacyInkRegions':'cleared and bound','scope':'Static/source/asset checks, not a Unity runtime or rendered result','integratedRootedTrunks':21,'distinctBambooCulms':7,'colouredMarketLanterns':24,'activeWallAttachedFasciaParts':len(arches),'supportStallClearance':'passed','fourAudioPCMChecks':'passed','distanceAndBudgetFootsteps':'bound','temporaryPKeyShiranui':'bound','unityRuntimeVerified':False}
Path(__file__).with_name('checks.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
