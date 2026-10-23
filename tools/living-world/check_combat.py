"""Offline structural checks for the actual authored arena prefabs, not playtest approval."""
from pathlib import Path
import sys,re,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/village'))
from native import Scene,ASSETS
report=json.loads((ROOT/'tools/living-world/combat-report.json').read_text())
checks=0
for kind,spec in report.items():
 p=ASSETS/f'Generated/Enemy-{kind}.prefab';s=Scene(p)
 root=spec['prefabRootPreserved'];assert s.name(root)=='Enemy-'+kind
 # Definitions still resolve to exactly the original prefab root/GUID.
 guid=re.search(r'guid: (\w+)',Path(str(p)+'.meta').read_text())[1]
 definition=(ASSETS/f'Generated/Spirit-{kind}.asset').read_text()
 assert f'visual: {{fileID: {root}, guid: {guid}, type: 3}}' in definition;checks+=1
 for part in ['torso','mask','left arm','right arm','left leg','right leg']:
  objects=[i for i in s.blocks if s.kind(i)==1 and s.name(i)=='Spirit '+part];assert len(objects)==1
  go=objects[0];t=s.transform(go);assert f'm_Father: {{fileID: {s.transform(root)}}}' in s.blocks[t]
  assert 'm_Enabled: 1' in s.blocks[s.component(go,23)]
  outline=next(i for i in s.blocks if s.kind(i)==1 and s.name(i)=='Spirit '+part+' ink')
  assert f'm_Father: {{fileID: {t}}}' in s.blocks[s.transform(outline)];checks+=1
for p in (ASSETS/'Generated/LivingCombat').glob('*.asset'):
 raw=p.read_text();n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);buf=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',raw)[1]);stride=len(buf)//n
 values=np.frombuffer(buf,dtype='<f4').reshape(n,stride//4);assert np.isfinite(values).all()
 assert np.allclose(np.linalg.norm(values[:,3:6],axis=1),1,atol=.0001)
 ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',raw)[1]),dtype='<u4');assert ix.max()<n;checks+=1
 # The prescribed 24-byte outline layout must match its shader inputs.
 if p.name.startswith('Contour-'):assert stride==24
wolf=(ASSETS/'Scripts/WolfCombat.cs').read_text()
assert 'Instantiate(sundial.visual, discAnchor)' in wolf and 'discAnchor.localPosition = new Vector3(0, ShieldPresentationRules.MountHeight' in wolf
assert 'heavy ? 1080 : 720' in wolf and 'ShieldPresentationRules.Visible' in wolf
assert 'if (motor.Swimming)' in wolf
brain=(ASSETS/'Scripts/EnemyBrain.cs').read_text();assert brain.index('fallVelocity = motor.isGrounded')<brain.index('if (stun > 0)')
print(f'PASS: {checks} prefab/artifact integrity checks; stable six spirit identities; weapon back anchor/swim guard. Unity rendering/combat playtest NOT performed.')
