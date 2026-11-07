"""Compare actual effect mesh captures before/after the doubled ultimate burst."""
from pathlib import Path
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/double-sunburst-effects');C=Path('/workspace/work/solar-ultimate')
before=json.loads((W/'before-ultimate-runtime.json').read_text());after=json.loads((C/'ultimate-runtime.json').read_text())
receipt=json.loads((C/'runtime-receipt.json').read_text())
for path,sha in receipt['sourceHashes'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==sha,path
assert before['audio']==after['audio']
assert json.loads((W/'before-sword-runtime.json').read_text())==json.loads((C/'sword-runtime.json').read_text())
checks=0
for a,b in zip(before['frames'],after['frames']):
 for key in a:
  if key!='paint':assert a[key]==b[key],key
 if not a['detonated']:assert a['paint']==b['paint'];continue
 for old,new in zip(a['paint'],b['paint']):
  sprite=old['sprite'];ov=np.array(old['vertices']);nv=np.array(new['vertices']);assert old['position']==new['position']
  count=1 if sprite in ['SolarGlow','CannonCore'] else 2
  assert len(nv)==len(ov)*count
  # Every original quad grows to twice its width/height. Ring delays are
  # interleaved at half spacing to retain the existing blast timing envelope.
  for i in range(len(ov)//4):
   oi=i*4;ni=(i*2 if sprite=='OriginalWhiteRing' else i)*4
   assert np.allclose(nv[ni+1]-nv[ni],2*(ov[oi+1]-ov[oi]),atol=1e-4),sprite
   assert np.allclose(nv[ni+3]-nv[ni],2*(ov[oi+3]-ov[oi]),atol=1e-4),sprite
   if sprite!='OriginalWhiteRing':assert np.allclose(nv[ni:ni+4].mean(0),2*ov[oi:oi+4].mean(0),atol=1e-4),sprite
   checks+=1
result=dict(scope='Actual C# effect meshes using API doubles, not Unity Play Mode',quadComparisons=checks,blastSize=2,burstCopies=2,burstQuads=sum(len(p['vertices'])//4 for p in after['frames'][150]['paint']),chargeUnchanged=True,swordImpactUnchanged=True,bodyCameraAudioDamageTimingUnchanged=True)
(W/'verification.json').write_text(json.dumps(result,indent=2));print(result)
