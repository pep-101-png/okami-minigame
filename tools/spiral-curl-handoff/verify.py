from pathlib import Path
import sys,json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/solar-ultimate');OUT=Path('/workspace/work/spiral-curl-handoff');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
receipt=json.load(open(W/'runtime-receipt.json'))
for p,h in receipt['sourceHashes'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'Stale capture '+p
before=json.load(open(OUT/'before-runtime.json'));after=json.load(open(W/'ultimate-runtime.json'));frames=after['frames'];model=json.load(open(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/es3a/Model.json'))
for a,b in zip(frames,before['frames']):
 if a['t']<1.55 or a['t']>4.95:
  for k in ['hero','rotation','pose','bodyPosition','bodyRotation','bodyScale']:assert np.allclose(a[k],b[k],atol=1e-5,rtol=0),'Preserved segment changed '+k
 assert a['detonated']==b['detonated']
assert after['audio']==before['audio'],'Existing sound scheduling changed'
def projected_turn(data):
 angles=[];torso=[]
 for f in data['frames']:
  matrices=[]
  for i,v in enumerate(f['pose'][:9]):
   m=np.eye(4);m[:3,:3]=nr.rotation(v[3:7])@np.diag(v[7:]);m[:3,3]=v[:3];parent=model['bones'][i-1]['parent']+1 if i else -1;matrices.append(m if parent<0 else matrices[parent]@m)
  rot=nr.rotation(f['bodyRotation']);direction=nr.rotation(f['cameraRotation']).T@rot@np.diag(f['bodyScale'])@(matrices[8][:3,3]-matrices[1][:3,3]);angles.append(np.arctan2(direction[1],direction[0]));torso.append(rot@nr.rotation(f['pose'][0][3:7])@nr.rotation(f['pose'][1][3:7]))
 a=np.unwrap(angles)*180/np.pi;window=[i for i,f in enumerate(data['frames'][:-1]) if 1.65<f['t']<2.65];velocity=np.array([(a[i+1]-a[i])*30 for i in window]);speed=[]
 for i in window:
  d=torso[i+1]@torso[i].T;speed.append(np.arccos(np.clip((np.trace(d)-1)/2,-1,1))*30*180/np.pi)
 return velocity,np.array(speed)
old_v,old_speed=projected_turn(before);new_v,new_speed=projected_turn(after)
assert max(new_v)<-1,'Visible direction reverses in the handoff'
assert min(new_speed)>30,'The torso pauses during the handoff'
assert min(old_v)<0 and max(old_v)>0,'Negative control did not detect the old reversal'
assert min(new_speed)>min(old_speed)*2,'Handoff did not improve the old slow-down'
report=dict(scope='Actual C# native pose/camera capture with API doubles; offline, not Unity Play Mode',window='1.65–2.65 seconds',oldVisibleDegreesPerSecond=[float(min(old_v)),float(max(old_v))],newVisibleDegreesPerSecond=[float(min(new_v)),float(max(new_v))],oldMinimumTorsoDegreesPerSecond=float(min(old_speed)),newMinimumTorsoDegreesPerSecond=float(min(new_speed)),ascentBeforeHandoffPreserved=True,releaseLandingPreserved=True,damageAndAudioTimingPreserved=True)
(OUT/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
