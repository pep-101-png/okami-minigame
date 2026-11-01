"""Edit the offline native-asset cinematic into a 15-second shareable MP4."""
import argparse,json,subprocess,hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--frames',required=True,type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args();root=Path(__file__).resolve().parents[3];audio=root/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/NativeAudio'
for frame in range(360):assert (args.frames/f'frame-{frame:04d}.png').exists(),frame
music=audio/'foodhouse-background-0.ogg'
cues=[('npc0-0.wav',4.6,.12),('weapon-wp2e-0.wav',7.38,.30),('weapon-wp2e-heavy-1.wav',7.7,.16),('enemy0-0.wav',7.8,.14),('weapon-wp2e-0.wav',8.53,.30),('weapon-wp2e-0.wav',9.63,.34),('weapon-wp2e-heavy-1.wav',9.9,.18),('transformation-voice-pl00-13.wav',11.3,.38),('weapon-wp2e-heavy-1.wav',12.1,.28)]
cmd=['ffmpeg','-hide_banner','-loglevel','warning','-y','-framerate','24','-start_number','0','-i',str(args.frames/'frame-%04d.png'),'-ss','8','-i',str(music)]
for name,_,_ in cues:cmd+=['-i',str(audio/name)]
font='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf';sans='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
video="[0:v]hqdn3d=1:1:2:2,drawbox=x=0:y=0:w=iw:h=38:color=black@.9:t=fill,drawbox=x=0:y=ih-38:w=iw:h=38:color=black@.9:t=fill"
def title(text,size,y,enable):
 return f",drawtext=fontfile={font}:text='{text}':fontcolor=white:fontsize={size}:x=(w-tw)/2:y={y}:shadowcolor=black@.65:shadowx=2:shadowy=2:enable='{enable}'"
video+=title('WINDFLOWER VILLAGE',34,86,'between(t,0.5,2.8)')
video+=title('TUNDRA BEADS',23,620,'between(t,7.25,10.7)')
video+=title('SHIRANUI',29,610,'between(t,11.5,13.3)')
video+=title('SUNWARD',66,280,'gte(t,13.5)')+title('Windflower Village',24,370,'gte(t,13.5)')
video+=f",drawtext=fontfile={sans}:text='CINEMATIC PREVIEW · ŌKAMI FAN PROJECT':fontcolor=white@.8:fontsize=16:x=(w-tw)/2:y=h-29,fade=t=in:st=0:d=.3,fade=t=out:st=14.6:d=.4,format=yuv420p[v]"
filters=[video,"[1:a]atrim=duration=15,asetpts=PTS-STARTPTS,volume='if(between(t,11,13.6),.32,.62)':eval=frame,afade=t=in:d=.4[music]"]
labels=['[music]']
for i,(_,start,volume) in enumerate(cues,2):
 label=f's{i}';delay=round(start*1000);filters.append(f'[{i}:a]aresample=48000,asetpts=PTS-STARTPTS,volume={volume},adelay={delay}:all=1[{label}]');labels.append('['+label+']')
filters.append(''.join(labels)+f'amix=inputs={len(labels)}:duration=first:normalize=0,alimiter=limit=.9:level=false,afade=t=out:st=14.5:d=.5,atrim=duration=15[a]')
cmd+=['-filter_complex',';'.join(filters),'-map','[v]','-map','[a]','-c:v','libx264','-preset','medium','-crf','19','-pix_fmt','yuv420p','-r','24','-c:a','aac','-b:a','192k','-ar','48000','-ac','2','-t','15','-movflags','+faststart','-metadata','title=Sunward — Windflower Village | Cinematic Preview','-metadata','comment=Offline cinematic rendered from the actual saved Sunward scene and original Okami assets/animations. Not recorded Unity gameplay.',str(args.output)]
subprocess.run(cmd,check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(args.output)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');a=next(s for s in probe['streams'] if s['codec_type']=='audio');assert v['nb_frames']=='360' and abs(float(probe['format']['duration'])-15)<.05 and v['width']==1280 and v['height']==720 and a['channels']==2
subprocess.run(['ffmpeg','-v','error','-i',str(args.output),'-f','null','-'],check=True)
report=dict(type='Cinematic preview — not recorded Unity gameplay',path=str(args.output),bytes=args.output.stat().st_size,sha256=hashlib.sha256(args.output.read_bytes()).hexdigest(),duration=15,frames=360,fps=24,width=1280,height=720,fullDecode='passed',music=str(music.relative_to(root)),audio=[dict(file=n,seconds=t,gain=g) for n,t,g in cues]);args.output.with_suffix('.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
