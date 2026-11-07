"""Original-bank music routing derivatives; crossfade waveform seams, no new media."""
from pathlib import Path
import sys,json,hashlib,subprocess,wave,numpy as np,re
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/awakening-playtest');W.mkdir(exist_ok=True)
sys.path[:0]=['/workspace/sunward-remaster/tools/playtest-followup'];from repair_audio import render
rows=json.loads(Path('/workspace/work/interior-repair/bgm-streams.json').read_text());source=Path('/workspace/work/playtest-repair/source-native/data_pc/bgm/bgm00.afs2');out=D/'SelectedAudio';records=[]
def meta(p):
 text=(D/'NativeAudio/house-melody-67.ogg.meta').read_text();text=re.sub(r'^guid: \w+','guid: '+hashlib.sha256(('OriginalOnly/'+str(p.relative_to(R))).encode()).hexdigest()[:32],text,flags=re.M);Path(str(p)+'.meta').write_text(text)
def seamless(src,dest,seconds):
 raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(src),'-ac','2','-ar','32000','-f','f32le','-']);x=np.frombuffer(raw,'<f4').reshape(-1,2).copy();rate=32000
 energy=np.max(np.abs(x),axis=1);active=np.where(energy>max(1e-6,energy.max()*.004))[0]
 if len(active):x=x[max(0,active[0]-160):min(len(x),active[-1]+161)]
 n=min(int(seconds*rate),len(x)//4);u=np.linspace(0,1,n)[:,None];seam=x[-n:]*(1-u)+x[:n]*u;y=np.r_[x[n:-n],seam];peak=float(np.max(abs(y)));assert peak<.8
 p=W/'seam.wav'
 with wave.open(str(p),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(np.rint(y*32767).astype('<i2').tobytes())
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(p),'-c:a','libvorbis','-q:a','5',str(dest)],check=True)
 return dict(seconds=len(y)/rate,crossfadeSeconds=n/rate,boundaryStep=float(abs(y[0]-y[-1]).max()),peak=peak)
for index,cue,loop in [(196,'gardenmusic',True),(6,'trial-victory',False),(17,'boss-victory',False)]:
 row=rows[index]
 with source.open('rb') as f:f.seek(row['offset']);raw=f.read(row['end']-row['offset'])
 target=out/('bgm00-index-'+str(index)+('.ogg' if loop else '.wav'));info=render(raw,target,cue,loop)
 if loop:info['seam']=seamless(target,target,1.5)
 meta(target);records.append(dict(cue=cue,source=str(source),zeroBasedIndex=index,sourceSHA256=hashlib.sha256(raw).hexdigest(),outputSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),conversion=info,resource='Okami/SelectedAudio/'+target.stem,identity='Original bank entry; no unverified soundtrack title assigned'))
target=out/'palace-continuous.ogg';info=seamless(out/'core-core-subsong-16.ogg',target,.7);meta(target);pmeta=Path(str(target)+'.meta');pmeta.write_text(pmeta.read_text().replace('loadType: 1','loadType: 0'));records.append(dict(cue='palacemusic',source='Okami/SelectedAudio/core-core-subsong-16',conversion=info,outputSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),resource='Okami/SelectedAudio/'+target.stem))
p=D/'NativeAudio.json';j=json.loads(p.read_text());cues={r['cue'] for r in records};j['cues']=[r for r in j['cues'] if r['cue'] not in cues]+[dict(cue=r['cue'],resource=r['resource']) for r in records];p.write_text(json.dumps(j,indent=2)+'\n');(R/'tools/awakening-playtest/audio-provenance.json').write_text(json.dumps(records,indent=2)+'\n');print([(r['cue'],r['conversion'].get('seconds')) for r in records])
