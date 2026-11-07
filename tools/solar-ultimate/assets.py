"""Original-only paint exports and mastered layers of identified original SFX."""
from pathlib import Path
import json,hashlib,re,numpy as np,wave
from PIL import Image
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/solar-ultimate');W.mkdir(exist_ok=True);records=[]
rows=json.load(open('/workspace/work/playtest-repair/extra-inventory.json'))
for name,original in [('SolarBlast','bafooon'),('ImpactDust','sand_01'),('ImpactRocks','rcok_gray'),('SolarPuff','kemuri_01'),('SolarFlare','fire_02'),('SolarGlow','circleLight')]:
 x=next(x for x in rows if x['name']==original);raw=Path(x['cache']);assert hashlib.sha256(raw.read_bytes()).hexdigest()==x['sha256'];p=D/'Effects'/(name+'.png');Image.open(raw).save(p);m=(D/'Effects/CannonFire.png.meta').read_text();m=re.sub('guid: [0-9a-f]+','guid: '+hashlib.sha256(('OriginalOnly/'+str(p.relative_to(R))).encode()).hexdigest()[:32],m,count=1);Path(str(p)+'.meta').write_text(m);records.append(dict(output=str(p.relative_to(R)),original=original,sourceSHA256=x['sha256'],pixelSHA256=hashlib.sha256(Image.open(p).convert('RGBA').tobytes()).hexdigest()))
bank=json.load(open(D/'NativeAudio.json'));cues={x['cue']:x['resource'] for x in bank['cues']}
def source(cue,pitch):
 p=D.parent/(cues[cue]+'.wav')
 with wave.open(str(p),'rb') as f:rate=f.getframerate();assert f.getsampwidth()==2;v=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(float)/32768;channels=f.getnchannels();v=v.reshape(-1,channels).mean(1)
 idx=np.arange(round(len(v)*48000/(rate*pitch)))*rate*pitch/48000;return np.interp(idx,np.arange(len(v)),v),dict(cue=cue,path=str(p.relative_to(R)),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),pitch=pitch)
for cue,name,layers in [('solar-detonation','SolarDetonation',[('imp-em02-203',.64,.85,0),('heavy-impact',.8,.55,0),('weapon-wp24-heavy',.93,.55,.035)]),('divine-sword-impact','DivineSwordImpact',[('imp-em02-203',.92,.85,0),('heavy-impact',1,.65,0)])]:
 mix=np.zeros(4*48000);identity=[]
 for key,pitch,gain,delay in layers:
  v,m=source(key,pitch);offset=round(delay*48000);n=min(len(v),len(mix)-offset);mix[offset:offset+n]+=v[:n]*gain;m.update(gain=gain,delay=delay);identity.append(m)
 active=np.where(abs(mix)>1e-5)[0];mix=mix[:min(len(mix),active[-1]+1200)];peak=float(max(abs(mix)));gain=.90/max(peak,1e-8);mix*=gain;mix[-480:]*=np.linspace(1,0,480);p=D/'SelectedAudio'/(name+'.wav')
 with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes(np.rint(mix*32767).astype('<i2').tobytes())
 m=(D/'ImpAudio/imp-em02-203.wav.meta').read_text();m=re.sub('guid: [0-9a-f]+','guid: '+hashlib.sha256(('OriginalOnly/'+str(p.relative_to(R))).encode()).hexdigest()[:32],m,count=1);Path(str(p)+'.meta').write_text(m);records.append(dict(output=str(p.relative_to(R)),layers=identity,masterGain=gain,peak=float(max(abs(mix))),sha256=hashlib.sha256(p.read_bytes()).hexdigest()));bank['cues']=[x for x in bank['cues'] if x['cue']!=cue]+[dict(cue=cue,resource='Okami/SelectedAudio/'+name)]
(D/'NativeAudio.json').write_text(json.dumps(bank,indent=2)+'\n');(R/'tools/solar-ultimate/provenance.json').write_text(json.dumps(records,indent=2)+'\n')
