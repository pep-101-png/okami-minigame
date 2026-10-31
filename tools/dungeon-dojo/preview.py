"""Offline Blender geometry/paint diagnostics, NOT Unity screenshots."""
from pathlib import Path
import os,sys
ROOT=Path(__file__).resolve().parents[2]
original=ROOT/'tools/original-remake/preview_world.py';os.environ['SUNWARD_PREVIEW_OUTPUT']=str(ROOT/'tools/dungeon-dojo/previews');scope={'__file__':str(original),'__name__':'preview_helpers'};exec(compile(original.read_text().split('bpy.ops.object.select_all(action=')[0],str(original),'exec'),scope);globals().update({k:v for k,v in scope.items() if not k.startswith('__')})
sys.path.insert(0,str(ROOT/'tools/playtest-followup'));from pose_audit import bank
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
w=World();plan=json.loads((ROOT/'tools/dungeon-dojo/world-changes.json').read_text());w.scene.set(plan['chamber'],'m_IsActive',1)
room=[];dojo=[];shaft=[];ground=[]
dummyroots={w.scene.transform(w.scene.owner(ref(b,'dummy')[0])) for b in w.scene.blocks.values() if 'Assembly-CSharp::Sunward.Remaster.NativeVenueActor\n' in b and '  role: training\n' in b}
def under_dummy(go):
 t=w.scene.transform(go)
 while t:
  if t in dummyroots:return True
  t=ref(w.scene.blocks[t],'m_Father')[0]
 return False
for r in w.renderers():
 name=r['name'];isroom=name.startswith('Original boss ');isshaft='textured earth shaft' in name;isdojo='training hall · dojo-' in name or (not r['instance'] and under_dummy(r['go']));isground=name=='Existing native-painted ground · centre opening'
 if not(isroom or isshaft or isdojo or isground):continue
 d=w.mesh(r['meshGUID'],r['meshID']);n=len(d['vertices']);raw=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',d['raw'])[1]),'<f4').reshape(n,d['stride']//4);ob=mesh(name,d['vertices'],d['triangles'],raw[:,10:12],ground_material() if isground else material(r['materials'][0],w),r['matrix'],raw[:,6:10]);(room if isroom else shaft if isshaft else ground if isground else dojo).append(ob)
# Use exact skin poses and the same support-vertex correction as runtime.
training=json.loads((ROOT/'tools/dungeon-dojo/training-sources.json').read_text())
for e,p in zip(training,plan['training']):
 folder=A/'OkamiRemaster/Original/Resources'/e['resource'];model=json.loads((folder/'Model.json').read_text());poses=bank(folder/'Poses.bytes')[e['motion']][0];parts=skin(model,poses[len(poses)//2]);feet=np.concatenate([parts[next(i for i,t in enumerate(model['parts']) if t['name']==f['part'])][f['indices']] for f in e['feet']]);off=-feet.mean(0);off[1]=-feet[:,1].min();matrix=np.diag([-e['scale'],e['scale'],-e['scale'],1]);matrix[:3,3]=p['position'];matrix[:3,3]+=matrix[:3,:3]@off
 for part,v in zip(model['parts'],parts):
  if int(part['name'].split('-')[1]) not in model['visibleGroups']:continue
  t=next(t for t in model['textures'] if t['index']==part['texture'])
  if t.get('vertexOnly'):continue
  dojo.append(mesh(part['name'],v,np.array(part['indices']).reshape(-1,3),np.array(part['uv']).reshape(-1,2),texture_material(folder/t['path']),matrix,np.array(part['colors']).reshape(-1,4)))
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=False;s.world.color=(.025,.018,.025);s.view_settings.view_transform='Standard';bpy.ops.object.camera_add();camera=bpy.context.object;s.camera=camera;camera.data.clip_end=1000
for name,position,target,width,objects in [('boss-cavern',(15,-79,30),(53,-101,-8),108,room+shaft),('earth-shaft',(37,10,4),(35,-8,0),17,shaft+ground),('dojo-practice',(0,6,22),(0,1,29),14,dojo)]:
 for ob in room+shaft+dojo+ground:ob.hide_render=ob not in objects
 camera.data.type='ORTHO';camera.data.ortho_scale=width;camera.location=CONVERT@Vector(position);look=CONVERT@Vector(target);camera.rotation_euler=(look-camera.location).to_track_quat('-Z','Y').to_euler();s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 from PIL import Image,ImageDraw
 im=Image.open(s.render.filepath);ImageDraw.Draw(im).text((15,15),'BLENDER GEOMETRY / ORIGINAL PAINT CHECK - NOT UNITY; lighting and particles not represented',fill='white',stroke_width=1,stroke_fill='black');im.save(s.render.filepath)
