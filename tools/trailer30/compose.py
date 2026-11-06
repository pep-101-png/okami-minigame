"""Mix existing original audio with the native-60fps cinematic picture."""
from pathlib import Path
import argparse,subprocess,json,hashlib
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';bank=json.loads((D/'NativeAudio.json').read_text())['cues']
p=argparse.ArgumentParser();p.add_argument('--picture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
def cue(name):
 resource=next(x['resource'] for x in bank if x['cue']==name);base=D.parent/resource;return next(p for p in base.parent.glob(base.name+'.*') if p.suffix in ['.wav','.ogg'])
music=D/'NativeAudio/foodhouse-background-0.ogg';battle=cue('battle')
# Each effect is from the same existing original-source cue used by the project.
sequence=[('collect',8.62,.4),('collect',9.03,.4),('collect',9.48,.4),('weapon-wp2e',10.12,.55),('impact',10.55,.4),('enemy0',10.66,.25),('weapon-wp2e',11.08,.55),('impact',11.55,.4),('weapon-wp2e-heavy',12.0,.4),('heavy-impact',12.25,.4),('enemy0',12.35,.23),('collect',13.0,.3),('transformation-voice',17.0,.65),('weapon-wp2e-heavy',17.4,.24),('enemy5',18.95,.4),('weapon-wp29',20.02,.55),('heavy-impact',20.55,.35),('enemy5',21.5,.4),('weapon-wp29-heavy',22.5,.6),('heavy-impact',22.64,.5),('impact',22.70,.3),('enemy5',23.7,.35),('transformation-voice',25.9,.70)]
cmd=['ffmpeg','-v','warning','-y','-i',str(a.picture),'-i',str(music),'-i',str(battle)]
for name,_,_ in sequence:cmd+=['-i',str(cue(name))]
filters=["[0:v]fade=t=in:st=0:d=0.35,fade=t=out:st=29.55:d=0.45[v]", "[1:a]aresample=48000,atrim=start=8:duration=30,asetpts=PTS-STARTPTS,volume='if(between(t,10,24),.16,if(between(t,16,19)+between(t,25.5,28.5),.28,.72))':eval=frame,afade=t=in:d=0.6,afade=t=out:st=29:d=1[peace]", "[2:a]aresample=48000,atrim=start=8:duration=16,asetpts=PTS-STARTPTS,volume='if(between(t,6.7,9),.25,.60)':eval=frame,afade=t=in:d=1,afade=t=out:st=14:d=2,adelay=9000:all=1[battle]"]
labels=['[peace]','[battle]']
for i,(name,start,volume) in enumerate(sequence,3):
 label='s'+str(i);filters.append(f'[{i}:a]aresample=48000,asetpts=PTS-STARTPTS,volume={volume},adelay={round(start*1000)}:all=1[{label}]');labels.append('['+label+']')
filters.append(''.join(labels)+f'amix=inputs={len(labels)}:duration=first:normalize=0,loudnorm=I=-17:LRA=10:TP=-1.5,alimiter=limit=.89:level=false,afade=t=out:st=29.5:d=0.5,atrim=duration=30[a]')
cmd+=['-filter_complex_threads','2','-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-preset','fast','-crf','18','-maxrate','20M','-bufsize','40M','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','256k','-ar','48000','-ac','2','-t','30','-movflags','+faststart','-metadata','title=Sunward — Windflower Village | 30 Second Cinematic Trailer','-metadata','comment=Standalone offline cinematic rendered at 1920x1080 and 60fps from the saved Sunward scene, original Okami models, native animation banks and original audio. Directed camera/combat choreography, not recorded Unity gameplay. No trailer code or playback is added to the game.',str(a.output)]
subprocess.run(cmd,check=True)
receipt=dict(type='Standalone native-asset cinematic; not a Unity gameplay capture',music=[dict(path=str(x.relative_to(R)),sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in [music,battle]],effects=[dict(cue=n,path=str(cue(n).relative_to(R)),time=t,gain=v,sha256=hashlib.sha256(cue(n).read_bytes()).hexdigest()) for n,t,v in sequence]);a.output.with_suffix('.audio.json').write_text(json.dumps(receipt,indent=2));print('Composed',a.output)
