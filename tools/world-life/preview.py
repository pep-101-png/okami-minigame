"""Saved scene / original paint diagnostics. Not Unity screenshots."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[2];original=ROOT/'tools/original-remake/preview_world.py';os.environ['SUNWARD_PREVIEW_OUTPUT']=str(ROOT/'tools/world-life/previews');scope={'__file__':str(original),'__name__':'helpers'};code=original.read_text().split("bpy.ops.object.select_all(action=")[0].replace('q=base*.3+q*.7','q=base*(1-record.get("armWeight",.7))+q*record.get("armWeight",.7)');exec(compile(code,str(original),'exec'),scope);globals().update({k:v for k,v in scope.items() if not k.startswith('__')})
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);w=World();s=w.scene;plan=json.loads((ROOT/'tools/world-life/world-changes.json').read_text());home=plan['rooms'][0];root=s.transform(home['root']);groups={n:[] for n in ['farm','home','shaft','market','music']}
for i,b in s.blocks.items():
 if 'Assembly-CSharp::Sunward.Remaster.VenueVisibility\n' in b and '  venue: food\n' in b:
  for field,kind,value in [('roof',23,0),('interiorSurfaces',23,1),('contents',1,1)]:
   chunk=b.split('  '+field+':\n')[-1].split('\n  ',1)[0] if '  '+field+':\n' in b else ''
   # Unity array entries have two-space indent, parse until next named field.
   if '  '+field+':\n' in b:chunk=re.split(r'\n  [A-Za-z]',b.split('  '+field+':\n')[1],maxsplit=1)[0]
   for valueid in re.findall(r'fileID: (\d+)',chunk):
    valueid=int(valueid)
    if valueid in s.blocks:s.set(valueid,'m_Enabled' if kind==23 else 'm_IsActive',value)
def under(go,tr):
 t=s.transform(go)
 while t:
  if t==tr:return True
  t=ref(s.blocks[t],'m_Father')[0]
 return False
for r in w.renderers():
 name=r['name'];group=None
 if not r['instance'] and under(r['go'],root):group='home'
 elif 'textured earth shaft' in name:group='shaft'
 elif 'Original larger centred' in name:group='market'
 elif 'original koto' in name or 'food house table' in name or 'food house floor' in name:group='music'
 elif 'Original village life' in name and ('crop ' in name or 'farm shop' in name or 'Farm-soil' in name) or 'farm pen fence' in name or 'farm native' in name or 'farm shelter' in name:group='farm'
 elif name=='Existing native-painted ground · centre opening':group='ground'
 if not group:continue
 d=w.mesh(r['meshGUID'],r['meshID']);n=len(d['vertices']);raw=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',d['raw'])[1]),'<f4').reshape(n,d['stride']//4);mat=ground_material() if group=='ground' else material(r['materials'][0],w);ob=mesh(name,d['vertices'],d['triangles'],raw[:,10:12],mat,r['matrix'],raw[:,6:10]);
 if group=='ground':
  for key in ['farm','market','shaft']:groups[key].append(ob)
 else:groups[group].append(ob)
# Exact serialized native performer and farmer appearances.
for cid,b in s.blocks.items():
 if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b:continue
 go=s.owner(cid);name=s.name(go);group='music' if name=='Original music house performer' else 'farm' if name=='Original Okami · farmer' else None
 if not group:continue
 before=set(bpy.data.objects);resource=re.search(r'  resource: (.+)',b)[1];idle=re.search(r'  idle: (.+)',b)[1];actor(dict(resource=resource,bindings=dict(idle=idle),modelScale=float(re.search(r'  modelScale: (.+)',b)[1]),modelOffset=vec(b,'modelOffset').tolist(),matrix=w.matrix(0,s.transform(go)).tolist(),armMotion='hm05_028' if group=='music' else None,armWeight=.18,posePhase=.5));groups[group]+=[o for o in bpy.data.objects if o not in before]
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.world.color=(.05,.05,.05);scene.view_settings.view_transform='Standard';bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='ORTHO';camera.data.clip_end=1000
x,y,z=vec(s.blocks[root],'m_LocalPosition');shots=[('farm',(-58,10,32),(-49,0,24),23),('home',(x+7,y+7,z-8),(x,y+.6,z),12),('shaft',(37,9,3),(35,-5,0),16),('market',(0,10,-42),(0,1,-30),23),('music',(4,4,-12),(7,.9,-17.2),8)]
for name,position,target,width in shots:
 shown=set(groups[name])
 for ob in {o for v in groups.values() for o in v}:ob.hide_render=ob not in shown
 camera.location=CONVERT@Vector(position);look=CONVERT@Vector(target);camera.rotation_euler=(look-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=width;scene.render.resolution_x=1100;scene.render.resolution_y=750;scene.render.resolution_percentage=100;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 from PIL import Image,ImageDraw
 im=Image.open(scene.render.filepath);ImageDraw.Draw(im).text((12,12),'OFFLINE BLENDER / ORIGINAL PAINT - NOT UNITY PLAYBACK; runtime lighting and effects not shown',fill='white',stroke_fill='black',stroke_width=1);im.save(scene.render.filepath)
