"""15s OFFLINE cinematic of the saved Sunward scene; never label as gameplay capture.
Run with Blender -b -t 8 -P this_file -- --out /path --preview (four stills).
"""
from pathlib import Path
import sys,os,argparse,json,struct,math,time,hashlib
sys.path.insert(0,str(Path(__file__).resolve().parent))
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--preview',action='store_true');p.add_argument('--start',type=int,default=0);p.add_argument('--end',type=int,default=360);args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(args.out);OUT.mkdir(parents=True,exist_ok=True);os.environ['SUNWARD_PREVIEW_OUTPUT']=str(OUT)
from paint_renderer import *
from asset_geometry import rotation
from mathutils import Quaternion
from scene_data import Terrain
FPS=24
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
w=World();s=w.scene;ground=ground_material();statics=[];billboards=[]
anchors={s.transform(s.owner(i)) for i,b in s.blocks.items() if 'Assembly-CSharp::Sunward.Remaster.OriginalBillboard\n' in b}
for r in w.renderers():
 if r['kind']!=23:continue
 data=w.mesh(r['meshGUID'],r['meshID'])
 if data is None or not len(data['triangles']):continue
 n=len(data['vertices']);buf=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',data['raw'])[1]);a=np.frombuffer(buf,'<f4').reshape(n,data['stride']//4);uv=a[:,10:12] if data['stride']>=48 else np.zeros((n,2));colors=a[:,6:10] if data['stride']>=48 else np.ones((n,4));g=r['materials'][0] if r['materials'] else None;mat=ground if w.assets.get(g) and w.assets[g].name=='Original-Ground.mat' else material(g,w)
 ob=mesh(r['name'],data['vertices'],data['triangles'],uv,mat,r['matrix'],colors);statics.append(ob)
 if not r['instance']:
  tr=s.transform(r['go'])
  while tr:
   if tr in anchors:
    anchor=w.matrix(0,tr);billboards.append((ob,anchor,np.linalg.inv(anchor)@r['matrix']));break
   tr=ref(s.blocks[tr],'m_Father')[0]
print('Loaded',len(statics),'saved scene meshes',flush=True)
terrain=Terrain(w)
terrain_points=np.array([[x,y,z] for (x,z),y in terrain.heights.items()])
def height(x,z):
 try:return terrain.height(x,z)
 except KeyError:
  # The saved upper floor has a separate closed lid over the cut terrain.
  d=(terrain_points[:,0]-x)**2+(terrain_points[:,2]-z)**2
  return float(terrain_points[np.argmin(d),1])
def bank(path):
 d=path.read_bytes();_,_,bones,count=struct.unpack_from('<4sIII',d);off=16;out={}
 for _ in range(count):
  n=struct.unpack_from('<I',d,off)[0];off+=4;name=d[off:off+n].decode();off+=n;frames,duration,loop=struct.unpack_from('<IfI',d,off);off+=12;v=np.frombuffer(d,'<f4',frames*bones*10,off).reshape(frames,bones,10).copy();off+=v.nbytes;out[name]=(v,duration,loop)
 return out
def matrix(position,yaw=0,scale=1):
 a=math.radians(yaw);m=np.array([[math.cos(a),0,math.sin(a),position[0]],[0,1,0,position[1]],[-math.sin(a),0,math.cos(a),position[2]],[0,0,0,1.]])
 m[:3,:3]*=scale;return m
class Native:
 def __init__(self,resource,root=np.eye(4),scale=1,offset=(0,0,0)):
  self.folder=next(p/resource for p in A.rglob('Resources') if (p/resource/'Model.json').exists());self.model=json.loads((self.folder/'Model.json').read_text());self.bank=bank(self.folder/'Poses.bytes');self.root=root;self.scale=scale;self.offset=np.array(offset);self.parts=[]
  pose=next(iter(self.bank.values()))[0][0];verts=skin(self.model,pose)
  for i,(part,v) in enumerate(zip(self.model['parts'],verts)):
   if self.model.get('visibleGroups') and int(part['name'].split('-')[1]) not in self.model['visibleGroups']:continue
   tex=next(t for t in self.model['textures'] if t['index']==part['texture'])
   if tex.get('vertexOnly'):continue
   ob=mesh(resource,v,np.array(part['indices']).reshape(-1,3),np.array(part['uv']).reshape(-1,2),texture_material(self.folder/tex['path']),root,np.array(part['colors']).reshape(-1,4));self.parts.append((i,ob))
 def pose(self,clip,t,loop=True):
  data,duration,_=self.bank[clip];frame=((t%duration)/duration if loop else np.clip(t/duration,0,1))*(len(data)-1);i=int(frame);j=min(i+1,len(data)-1);u=frame-i;a=data[i];b=data[j];v=a*(1-u)+b*u;q1=a[:,3:7];q2=b[:,3:7].copy();q2[np.sum(q1*q2,axis=1)<0]*=-1;qs=q1*(1-u)+q2*u;v[:,3:7]=qs/np.maximum(np.linalg.norm(qs,axis=1,keepdims=True),1e-8);return v
 def update(self,clip,t,root=None,loop=True):
  if root is not None:self.root=root
  pose=self.pose(clip,t,loop);verts=skin(self.model,pose)
  for i,ob in self.parts:
   ob.data.vertices.foreach_set('co',np.asarray(verts[i]*self.scale+self.offset,dtype=np.float32).ravel());ob.data.update();ob.matrix_world=CONVERT@Matrix(self.root)
  return pose
 def show(self,yes):
  for _,ob in self.parts:ob.hide_render=not yes
npcs=[]
for instance,source in [(0,s),*w.prefabs.items()]:
 for cid,b in source.blocks.items():
  if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b or '  m_Enabled: 0\n' in b:continue
  go=source.owner(cid)
  if not w.active(instance,go):continue
  root=w.matrix(instance,source.transform(go));resource=re.search(r'  resource: (.+)',b)[1]
  if root[1,3]<-5:continue
  idle=re.search(r'  idle: (.+)',b)[1]
  actor=Native(resource,root,float(re.search(r'  modelScale: (.+)',b)[1]),vec(b,'modelOffset'));npcs.append((actor,idle))
player=Native('NativePlayer/pl00');spirit=Native('Okami/pl0d');weapon=Native('Okami/wp2e');enemies=[]
raw=(A/'Sunward/Generated/Enemy-wisp.prefab').read_text();offset=vec(raw,'modelOffset');scale=float(re.search(r'  modelScale: (.+)',raw)[1]);spec=(A/'Sunward/Generated/Spirit-wisp.asset').read_text();scale*=float(re.search(r'^  scale: (.+)',spec,re.M)[1])
for z,x in [(4.2,35),(5,38.5)]:enemies.append(Native('Okami/em00',matrix([x,height(x,z),z],180),scale,offset))
def soft_material(sprite,tint=(.65,.82,1),strength=2,opacity=.7):
 m=bpy.data.materials.new('Original sprite '+sprite+' soft alpha');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(A/'OkamiRemaster/Original/Resources/Okami/Effects'/(sprite+'.png')),check_existing=True);mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(tex.outputs['Color'],mul.inputs[1]);mul.inputs[2].default_value=(*tint,1);em=n.new('ShaderNodeEmission');em.inputs['Strength'].default_value=strength;l.new(mul.outputs[0],em.inputs['Color']);trans=n.new('ShaderNodeBsdfTransparent');alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';l.new(tex.outputs['Alpha'],alpha.inputs[0]);alpha.inputs[1].default_value=opacity;mix=n.new('ShaderNodeMixShader');l.new(alpha.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);return m
particle_materials={kind:soft_material(kind,strength=1 if kind=='Wind' else 2.7,opacity=.45 if kind=='Wind' else .7) for kind in ['Wind','SpiritGlow','Spark','Spirit']}
shadow=mesh('Painted contact shadow',[[-1,0,-.45],[1,0,-.45],[1,0,.45],[-1,0,.45]],[[0,1,2],[0,2,3]],[[0,0],[1,0],[1,1],[0,1]],soft_material('SpiritGlow',(0,0,0),1,.26))
# Billboard particles adapt original core sprites, as the game does. No replacement artwork.
particle_objects=[]
for kind,count in [('Wind',24),('SpiritGlow',24),('Spark',18),('Spirit',5)]:
 for i in range(count):
  ob=mesh(kind,[[-.5,-.5,0],[.5,-.5,0],[.5,.5,0],[-.5,.5,0]],[[0,1,2],[0,2,3]],[[0,0],[1,0],[1,1],[0,1]],particle_materials[kind]);particle_objects.append((kind,i,ob))
  if kind=='Spark':
   for uv in ob.data.uv_layers[0].data:uv.uv.x*=.25
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=4;scene.cycles.use_denoising=False;scene.cycles.max_bounces=2;scene.cycles.transparent_max_bounces=16;scene.render.use_persistent_data=True;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.15;scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.67,.75,.82,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.8
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera;camera.data.type='PERSP';camera.data.lens=36;camera.data.clip_end=500;scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.film_transparent=False
scene.use_nodes=True;nodes=scene.node_tree.nodes;nodes.clear();layers=nodes.new('CompositorNodeRLayers');glare=nodes.new('CompositorNodeGlare');glare.glare_type='FOG_GLOW';glare.quality='MEDIUM';glare.threshold=1.5;glare.size=6;composite=nodes.new('CompositorNodeComposite');scene.node_tree.links.new(layers.outputs['Image'],glare.inputs['Image']);scene.node_tree.links.new(glare.outputs['Image'],composite.inputs['Image'])
# Attach a separately skinned instrument to PL bone 30 without squash/stretch scale.
def dorsal(model,pose):
 mats=[];qs=[]
 for i,r in enumerate(pose):
  parent=model['bones'][i-1]['parent']+1 if i else -1;q=Quaternion((float(r[6]),*map(float,r[3:6])));local=Matrix.Translation(Vector(r[:3]))@q.to_matrix().to_4x4()@Matrix.Diagonal((*map(float,r[7:]),1));mats.append(local if parent<0 else mats[parent]@local);qs.append(q if parent<0 else qs[parent]@q)
 out=qs[31].to_matrix().to_4x4();out.translation=mats[31].translation;return np.array(out)
def set_frame(t):
 for i,(actor,idle) in enumerate(npcs):actor.update(idle,t+i*.37)
 for e in enemies:e.show(7<=t<11)
 spirit.show(False);player.show(True);weapon.show(False)
 if t<3.5:
  u=t/3.5;pos=np.array([-23+u*5,17-u*2,-29+u*3]);target=np.array([-1,1,4+u*2]);root=matrix([0,height(0,-8),-8]);player.update('pl00_000',t,root);camera.data.lens=30
 elif t<7:
  u=(t-3.5)/3.5;z=-8+6*u;root=matrix([0,height(0,z),z]);player.update('pl00_010',(t-3.5)*.8,root);pos=np.array([-6.5,3.3,z-5]);target=np.array([0,1,z+1]);camera.data.lens=36
 elif t<11:
  local=t-7;root=matrix([35,height(35,0),0]);clip='pl00_000';wp='wp2e_000';ct=local
  for start,pn,wn in [(.3,'pl00_544','wp2e_001'),(1.45,'pl00_545','wp2e_002'),(2.55,'pl00_54b','wp2e_008')]:
   if start<=local<start+.9666667:clip=pn;wp=wn;ct=local-start
  pose=player.update(clip,ct,root,clip=='pl00_000');weapon.show(True);weapon.update(wp,ct,root@dorsal(player.model,pose),wp=='wp2e_000');pos=np.array([44,4.5,-6.8]);target=np.array([35,1.2,3.4]);camera.data.lens=35
  for k,e in enumerate(enemies):
   death=local-(1.1 if k==0 else 3.15)
   if death>=0:e.update('em00_040',death,loop=False);e.show(death<1.4)
   else:e.update('em00_082',max(0,local-.15) if k==0 else max(0,local-1.4),loop=False)
 elif t<13.5:
  local=t-11;root=matrix([35,height(35,0),0],175);pose=player.update('pl00_04e',local,root,False);spirit.update('pl00_000',0,root) if 'pl00_000' in spirit.bank else None
  # PL0d shares PL00's original motion skeleton; use the same native pose.
  if local>=1.1:
   player.show(False);spirit.show(True)
   verts=skin(spirit.model,pose)
   for i,ob in spirit.parts:ob.data.vertices.foreach_set('co',np.asarray(verts[i],dtype=np.float32).ravel());ob.data.update();ob.matrix_world=CONVERT@Matrix(root)
  a=math.radians(-75+local*20);pos=np.array([35+math.sin(a)*7.3,3,-math.cos(a)*7.3]);target=np.array([35,1.1,0]);camera.data.lens=38
 else:
  u=(t-13.5)/1.5;pos=np.array([-20+u*2,15+u,-27]);target=np.array([0,2,6]);root=matrix([0,height(0,-3),-3]);player.update('pl00_000',t,root);camera.data.lens=29
 shadow.matrix_world=CONVERT@Matrix(root@matrix([0,.025,0]));shadow.hide_render=False
 camera.location=CONVERT@Vector(pos);look=CONVERT@Vector(target);camera.rotation_euler=(look-camera.location).to_track_quat('-Z','Y').to_euler()
 for ob,base,relative in billboards:
  forward=pos-base[:3,3];forward[1]=0;forward/=max(.001,np.linalg.norm(forward));right=np.cross([0,1,0],forward);new=base.copy();new[:3,:3]=np.column_stack([right,[0,1,0],forward])@np.diag(np.linalg.norm(base[:3,:3],axis=0));ob.matrix_world=CONVERT@Matrix(new@relative)
 for kind,i,ob in particle_objects:
  visible=7<=t<11 if kind=='Wind' else 11<=t<13.5;ob.hide_render=not visible
  if not visible:continue
  if kind=='Wind':a=i*2*math.pi/24+t*.1;point=[35+17.6*math.cos(a),1.3+.25*math.sin(t+i),17.6*math.sin(a)];size=1.25
  else:
   local=t-11;u=(local+i*.097)%1.1/1.1;a=i*2.399+local*2.8;r=(1-u)*2.3 if local<1.1 else .5+(local-1.1)*3.3
   point=[35+math.cos(a)*r,.45+u*2.1,math.sin(a)*r];size=.15+.22*(1-u)
   if kind=='Spark':
    if local<1.1:ob.hide_render=True;continue
    size=.14
  if kind=='Spirit':size=.7+.3*math.sin(t*4+i);point=[35+math.cos(i*1.7+t)*1.4,1.2+.4*math.sin(t*2+i),math.sin(i*1.7+t)*1.4]
  ob.location=CONVERT@Vector(point);ob.rotation_euler=camera.rotation_euler;ob.scale=(size,size,size)
frames=[48,126,205,294] if args.preview else range(args.start,args.end)
for frame in frames:
 set_frame(frame/FPS);scene.render.filepath=str(OUT/(f'preview-{frame:04d}.png' if args.preview else f'frame-{frame:04d}.png'));bpy.ops.render.render(write_still=True)
 print('TRAILER_FRAME',frame,flush=True)
(OUT/'render-receipt.json').write_text(json.dumps(dict(type='Offline cinematic preview, NOT recorded Unity gameplay',scene=str(A/'Sunward/Scenes/Windflower.unity'),sceneSHA256=hashlib.sha256((A/'Sunward/Scenes/Windflower.unity').read_bytes()).hexdigest(),renderBatchFrames=len(frames),previewOnly=args.preview,expectedFinalFrames=360,fps=FPS,duration=15,width=1280,height=720,staticMeshes=len(statics),nativeActors=len(npcs),motions=['pl00_010','pl00_544','pl00_545','pl00_54b','pl00_04e','em00_082','em00_040'],media='Original project models/paintings/motion banks and core sprites; cinematic camera/choreography adapted offline'),indent=2))
