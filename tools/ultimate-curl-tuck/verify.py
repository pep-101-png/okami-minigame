from pathlib import Path
import sys,json,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/solar-ultimate');OUT=Path('/workspace/work/ultimate-curl-tuck');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
receipt=json.load(open(W/'runtime-receipt.json'))
for p,h in receipt['sourceHashes'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==h,'Stale capture: '+p
frames=json.load(open(W/'ultimate-runtime.json'))['frames'];bank=nr.pose_bank(R/'Sunward-Unity/Assets/OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes')
def sample(name,phase):
 a,d,_=bank[name];x=np.clip(phase,0,1)*(len(a)-1);i=int(x);j=min(i+1,len(a)-1);u=x-i;out=a[i]*(1-u)+a[j]*u;q1=a[i,:,3:7];q2=a[j,:,3:7].copy();q2[np.sum(q1*q2,axis=1)<0]*=-1;q=q1*(1-u)+q2*u;out[:,3:7]=q/np.maximum(np.linalg.norm(q,axis=1,keepdims=True),1e-9);return out
# Compare the actual driver's chosen postures to the two original samples the user saw.
for target,name,phase in [(2.75,'pl00_018',.25),(4.5,'pl00_021',None)]:
 f=min(frames,key=lambda f:abs(f['t']-target));elapsed=f['t']+1/30
 if phase is None:phase=.65+.008*np.sin((elapsed-3.05)*2.8)
 actual=np.array(f['pose']);expected=sample(name,phase)
 assert np.max(abs(actual[:,:3]-expected[:,:3]))<.0002 and np.max(abs(actual[:,7:]-expected[:,7:]))<.0002
 assert np.min(abs(np.sum(actual[:,3:7]*expected[:,3:7],axis=1)))>.99999,'Chosen source posture differs: '+name
relative=[nr.rotation(f['rotation']).T@nr.rotation(f['bodyRotation']) for f in frames]
angle=np.unwrap([np.arctan2(-m[1,2],m[2,2]) for m in relative]);times=np.array([f['t']+1/30 for f in frames]);charge=(times>=2.1)&(times<=4.65);motion=angle[charge];assert np.all(np.diff(motion)>-.0001),'Backward roll/reversal';assert 12.55<motion[-1]<12.58,'Expected two complete forward turns';assert np.max(np.diff(motion))<.30,'Forward roll jumps between frames';assert np.max(abs(angle[times<=2.1]))<.0001,'Approved ascent orientation changed'
assert not frames[-1]['playing'] and np.linalg.norm(np.array(frames[-1]['hero'])-[35,0,0])<1e-5
report=dict(scope='Actual C# capture with API doubles; not Unity Play Mode',foldedCurlOriginal='pl00_018 at 25%',airborneTuckOriginal='pl00_021 near 65%',forwardTurns=float(motion[-1]/(2*np.pi)),maxRollDegreesPer30fpsFrame=float(np.max(np.diff(motion))*180/np.pi),ascentOrientationUnchanged=True,playerRestored=True)
(OUT/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
