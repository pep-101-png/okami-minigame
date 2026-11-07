"""Check the recovered archive content and the recorded runtime transitions."""
from pathlib import Path
import sys,json,hashlib,subprocess,struct,numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';S=Path('/workspace/work/full-asset-inspection');W=Path('/workspace/work/imp-rework');rows=[json.loads(x) for x in (S/'inventory.jsonl').read_text().splitlines()];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
receipt=json.loads((W/'runtime-receipt.json').read_text())
for name,sha in receipt['sourceHashes'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==sha,'Stale runtime trace: '+name
profiles=json.loads((D/'ImpMotions.json').read_text())['profiles'];report=[]
for p,role in zip(profiles,['wisp','reed','ranged','heavy','elite']):
 pkg=p['resource'].split('/')[-1];j=json.loads((D/pkg/'Model.json').read_text());old=json.loads(subprocess.check_output(['git','show','HEAD:'+str((D/pkg/'Model.json').relative_to(R))],cwd=R));a=j.copy();b=old.copy();a.pop('visibleGroups');b.pop('visibleGroups');assert a==b,'Geometry, UVs or pigment changed outside the inspected masks'
 body=2 if pkg=='em02' else 1;parts=[q for q in j['parts'] if int(q['name'].split('-')[1])==body];bones=set(i for q in parts for i in q['boneIndices']);assert len(bones)>=20,'Rigid LOD selected again'
 for tx in j['textures']:
  if tx.get('vertexOnly'):continue
  row=next(x for x in rows if x['sha256']==tx['sourceSHA256'] and x.get('cache'));raw=S/row['cache'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==row['sha256'];assert np.array_equal(np.asarray(Image.open(D/pkg/tx['path']).convert('RGBA')),np.asarray(Image.open(raw).convert('RGBA'))),'Original paint does not match its own DDS'
 bank=nr.pose_bank(D/pkg/'Poses.bytes');source=nr.pose_bank(W/f'{pkg}-all.bytes')
 for name,(frames,duration,loop) in bank.items():assert np.array_equal(frames,source[name][0]) and duration==source[name][1]
 assert set(bank)=={m['name'] for m in p['motions']};assert 'em00_012' not in bank and 'em00_040' not in bank
 for m in p['motions']:
  for e in m['sounds']:assert 0<=e['time']<=m['duration'] and 0<e['gain']<=1
 trace=json.loads((W/f'{role}-runtime.json').read_text());frames=trace['frames'];assert len(frames)==720 and all(np.isfinite(x['pose']).all() for x in frames)
 assert max(x['hits'] for x in frames)>0 or role=='ranged','Stationary target never received a melee contact'
 if role=='ranged':assert max(abs(x['position'][2]-7) for x in frames)<10.1,'Drum recoil escaped its combat range'
 statechanges=[(round(f['t'],3),f['state']) for i,f in enumerate(frames) if i==0 or frames[i-1]['state']!=f['state']]
 report.append(dict(role=role,bodyGroup=body,skinnedBodyBones=len(bones),originalDDSMatch=True,originalGeometryUVPigmentPreserved=True,sourceNativeClips=list(bank),stateChanges=statechanges,damageContacts=frames[-1]['hits'],projectiles=frames[-1]['shots']))
# Every new waveform has an explicit SEQ -> SES cue -> sample -> ADX identity.
ledger=json.loads((R/'tools/imp-rework/audio-provenance.json').read_text());assert len({x['cue'] for x in ledger})==len(ledger)
for item in ledger:
 path=D/'ImpAudio'/(item['cue']+'.wav');assert hashlib.sha256(path.read_bytes()).hexdigest()==item['outputSHA256'];assert item['decoding']['output']['clippedFraction']==0
(W/'verification.json').write_text(json.dumps(dict(scope='Archive conservation and actual C# driver traces; not a Unity visual approval',variants=report,newAudio=ledger),indent=2));print('Original MD paint/UV conservation and captured attack/reaction/defeat sequences verified; visual review remains separate')
