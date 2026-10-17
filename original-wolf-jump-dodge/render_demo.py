import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;s=bpy.data.scenes['03 · Jump and dodge showcase'];bpy.context.window.scene=s
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=4;s.render.resolution_x=800;s.render.resolution_y=560;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
rows=json.load(open(R/'review/demo.json'));frames=[]
for case in rows['cases']:
 segs=[x for x in rows['segments']if x['case']==case['name']and x['action']not in ['Idle','Walk_Natural','Jog_Natural','Sprint_Fluid']]
 for seg in segs:
  if seg['action']=='Air_Fall':t=seg['duration']*.5
  elif seg['action'].startswith('Land'):t=20
  elif seg['action'].startswith('Dodge'):t=20
  else:t=seg['duration']*.5
  frames.append({'frame':int(seg['start']+t),'label':case['name']+' / '+seg['action']})
 for seg in segs[:1]:frames.append({'frame':int(seg['end']+3),'label':case['name']+' / recovery blend'})
for row in frames:
 f=row['frame'];path=R/f'review/final-renders/Showcase/{f:04}.png';path.parent.mkdir(parents=True,exist_ok=True);s.frame_set(f);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
(R/'review/showcase-frames.json').write_text(json.dumps(frames,indent=2));print('M2_SHOWCASE_RENDERED',len(frames),flush=True)
