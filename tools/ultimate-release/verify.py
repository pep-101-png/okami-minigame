from pathlib import Path
import sys,json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/solar-ultimate');OUT=Path('/workspace/work/ultimate-release');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
receipt=json.load(open(W/'runtime-receipt.json'))
for p,h in receipt['sourceHashes'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'Stale capture '+p
new=json.load(open(W/'ultimate-runtime.json'));old=json.load(open(OUT/'approved-charge.json'));frames=new['frames'];preserved=0
for a,b in zip(frames,old['frames']):
 if b['detonated']:break
 for k in ['hero','rotation','pose','bodyPosition','bodyRotation','bodyScale','centre']:assert np.allclose(a[k],b[k],atol=1e-6,rtol=0),'Approved charge changed: '+k
 preserved+=1
assert next(f['t'] for f in frames if f['detonated'])==next(f['t'] for f in old['frames'] if f['detonated'])
land=next(e['resource'] for e in json.load(open(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/NativeAudio.json'))['cues'] if e['cue']=='land');assert sum(e['cue']==land for e in new['audio'])==1
assert not frames[-1]['playing'] and np.linalg.norm(np.array(frames[-1]['hero'])-[35,0,0])<1e-5
landing=min(frames,key=lambda f:abs(f['t']-5.95));assert abs(landing['hero'][1])<.05,'Player never lands'
chargeEnd=np.array(frames[138]['pose']);release=np.array(frames[150]['pose']);assert np.linalg.norm(chargeEnd-release)>1,'No release unfurl'
# Unwrap actual player heading. Finish forward by 60 degrees, rather than
# unwinding 300 degrees backwards during descent.
angles=np.unwrap([np.arctan2(nr.rotation(f['rotation'])[0,2],nr.rotation(f['rotation'])[2,2]) for f in frames]);phase=[i for i,f in enumerate(frames) if 4.65<f['t']<5.95];travel=angles[phase[-1]]-angles[phase[0]];assert .9<travel<1.1 and np.min(np.diff(angles[phase]))>=-.0001
# Actual source joint/rig transforms; compare landing root to the restored motor.
model=json.load(open(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/es3a/Model.json'));heights=[]
for f in frames:
 if not 6.1<=f['t']<=6.75:continue
 base=np.eye(4);base[:3,:3]=nr.rotation(f['bodyRotation'])@np.diag(f['bodyScale']);base[:3,3]=f['bodyPosition'];mat=[]
 for i,v in enumerate(f['pose']):
  m=np.eye(4);m[:3,:3]=nr.rotation(v[3:7])@np.diag(v[7:]);m[:3,3]=v[:3];parent=model['bones'][i-1]['parent']+1 if i else -1;mat.append(m if parent<0 else mat[parent]@m)
 heights.extend((base@mat[i])[1,3] for i in [13,18,22,26])
assert min(heights)>-.18,'Landing paws penetrate floor'
last=frames[201];assert np.linalg.norm(np.array(last['bodyPosition'])-last['hero'])<.001,'Landing offset not settled before restoring control'
report=dict(scope='Actual C# output with API doubles; not Unity Play Mode',approvedChargeFramesPreserved=preserved,flashDamageTimingPreserved=True,releaseUnfurls=True,forwardHeadingDegrees=float(travel*180/np.pi),oneLandingCue=True,groundedRig=True,minLandingFootJointY=float(min(heights)),playerRestored=True)
(OUT/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
