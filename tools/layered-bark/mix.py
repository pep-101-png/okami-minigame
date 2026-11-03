"""User-requested mix of the exact audition WAVs, at original speed and pitch."""
from pathlib import Path
import wave,json,hashlib,numpy as np,argparse,re
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/celestial-polish/bark-candidates')
def read(p):
 with wave.open(str(p)) as f:
  assert (f.getnchannels(),f.getsampwidth(),f.getframerate())==(1,2,32000)
  return np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(float)/32768
sources=[('Player Archive A',W/'pl00-afs2-0.wav',1.0),('Shiranui 16',W/'pl0d-16.wav',2.0)];waves=[read(p) for _,p,_ in sources];mix=np.zeros(max(map(len,waves)))
for a,(_,p,gain) in zip(waves,sources):mix[:len(a)]+=a*gain
peak=float(abs(mix).max());headroom=min(1,.85/max(peak,1e-12));mix*=headroom;pcm=np.rint(mix*32767).astype('<i2');p=D/'NativeAudio/player-shiranui-layered-bark.wav'
with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(32000);f.writeframes(pcm.tobytes())
meta=Path(str(p)+'.meta');template=(D/'NativeAudio/player-pl00-41-bark.wav.meta').read_text();meta.write_text(re.sub(r'^guid: \w+','guid: '+hashlib.md5(b'SunwardUserRequestedPlayerShiranuiBark20261103').hexdigest(),template,flags=re.M))
j=json.loads((D/'NativeAudio.json').read_text());j['cues']=[x for x in j['cues'] if x['cue']!='bark']+[dict(cue='bark',resource='Okami/NativeAudio/player-shiranui-layered-bark')];(D/'NativeAudio.json').write_text(json.dumps(j,indent=2)+'\n')
report=dict(userInstruction='Mix Player Archive A with Shiranui 16 and turn Shiranui up',sources=[dict(name=n,filename=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest(),gain=gain,gainDB=round(20*np.log10(gain),4),startSeconds=0) for n,p,gain in sources],sampleRate=32000,channels=1,seconds=len(pcm)/32000,commonHeadroomGain=headroom,peak=float(abs(pcm.astype(float)/32768).max()),clippedSamples=int((abs(pcm.astype(float))>=32767).sum()),outputSHA256=hashlib.sha256(p.read_bytes()).hexdigest(),derivation='Aligned at time zero; full clips; linear gain and summing only; no pitch shift, time stretch, reverb or synthesized audio')
Path(__file__).with_name('mix-provenance.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
