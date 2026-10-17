import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;scene=bpy.data.scenes['02 · Movement showcase'];bpy.context.window.scene=scene;scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.taa_render_samples=8;scene.render.resolution_x=900;scene.render.resolution_y=620;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';segments=json.loads((R/'review/demo.json').read_text())['segments'];rows=[]
for i,seg in enumerate(segments):rows.append((int((seg['start']+seg['end'])/2),seg['action']))
for i in [3,7,11,15,16,17]:
 seg=segments[i];rows.append((int(seg['start']+seg['blend']/2),'transition '+seg['action']))
for f,label in rows:
 p=R/f'review/renders/ShowcaseFinal/{f:04}.png';p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists()and p.read_bytes()[-8:]==b'IEND\xaeB\x60\x82':continue
 scene.frame_set(f);scene.render.filepath=str(p);bpy.ops.render.render(write_still=True)
(R/'review/showcase-frames.json').write_text(json.dumps([{'frame':f,'label':label}for f,label in rows],indent=2));print('SHOWCASE_FINAL_REVIEW_RENDERED')
