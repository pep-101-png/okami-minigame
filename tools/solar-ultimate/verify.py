from pathlib import Path
import json,hashlib,numpy as np,subprocess,wave
from PIL import Image
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/solar-ultimate');D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';receipt=json.load(open(W/'runtime-receipt.json'));report={}
for p,h in receipt['sourceHashes'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'Stale capture '+p
rows=json.load(open('/workspace/work/playtest-repair/extra-inventory.json'));paint=[]
for p in json.load(open(R/'tools/solar-ultimate/provenance.json')):
 dest=R/p['output']
 if 'original' in p:
  row=next(x for x in rows if x['sha256']==p['sourceSHA256']);raw=Path(row['cache']);assert hashlib.sha256(raw.read_bytes()).hexdigest()==p['sourceSHA256'];assert np.array_equal(np.asarray(Image.open(raw).convert('RGBA')),np.asarray(Image.open(dest).convert('RGBA')));paint.append(p['original'])
 else:
  assert hashlib.sha256(dest.read_bytes()).hexdigest()==p['sha256']
  for layer in p['layers']:assert hashlib.sha256((R/layer['path']).read_bytes()).hexdigest()==layer['sha256']
  with wave.open(str(dest),'rb') as f:v=np.frombuffer(f.readframes(f.getnframes()),'<i2')/32768
  assert max(abs(v))<.94 and np.isfinite(v).all()
old=json.loads(subprocess.check_output(['git','show','349b2f63a62d92910ae67be17effa121a5f05d88:'+str((D/'NativeAudio.json').relative_to(R))],cwd=R));new=json.load(open(D/'NativeAudio.json'));assert [x for x in new['cues'] if x['cue'] not in ['solar-detonation','divine-sword-impact']]==old['cues'],'Existing sound bindings changed'
u=json.load(open(W/'ultimate-runtime.json'));s=json.load(open(W/'sword-runtime.json'));f=u['frames'];assert len(f)==222 and len(s['frames'])==54
blast=next(i for i,x in enumerate(f) if x['detonated']);assert 4.60<f[blast]['t']<4.70;assert all(e['dead'] for e in f[blast]['enemies']);assert all(not e['dead'] for e in f[blast-1]['enemies']);assert not f[-1]['playing'];assert np.linalg.norm(np.array(f[-1]['hero'])-[35,0,0])<1e-5
for x in f:
 assert np.isfinite(x['pose']).all() and np.isfinite(x['eye']).all()
 for p in x['paint']:assert np.isfinite(p['vertices']).all() and np.isfinite(p['colors']).all() and np.min(p['colors'])>=0 and np.max(p['colors'])<=1
assert max(np.linalg.norm(np.array(x['eye'])-np.array(f[0]['eye'])) for x in f)>10
assert np.linalg.norm(np.array(f[145]['enemies'][0]['pose'])-np.array(f[160]['enemies'][0]['pose']))>.1,'Victims never fall during the cinematic'
assert sum(x['cue'].endswith('/SolarDetonation') for x in u['audio'])==1
assert sum(x['cue'].endswith('/DivineSwordImpact') for x in s['audio'])==1
impact=next(x for x in s['frames'] if x['paint']);assert impact['t']<.4
report.update(scope='Source conservation and actual C# driver capture with API doubles, not Unity Play Mode',originalPaint=paint,existingAudioBindingsPreserved=True,flashDamageTime=f[blast]['t'],swordImpactTime=impact['t'],ultimateFrames=len(f),swordFrames=len(s['frames']),maxPaintedQuads=max(sum(len(p['vertices'])//4 for p in x['paint']) for x in f),oneDetonation=True)
(W/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
