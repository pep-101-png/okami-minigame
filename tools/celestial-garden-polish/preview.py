"""Offline diagnostic using exactly the runtime CelestialGarden placement JSON.
This does not run Unity or verify shader compilation/collision/playback.
"""
from pathlib import Path
import sys,os,json,math,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/spirit-charge-home/trailer'))
p=argparse.ArgumentParser();p.add_argument('--out',required=True);args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(args.out);OUT.mkdir(parents=True,exist_ok=True);os.environ['SUNWARD_PREVIEW_OUTPUT']=str(OUT)
from paint_renderer import *
from asset_geometry import rotation
from PIL import Image
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
D=A/'OkamiRemaster/Original/Resources/Okami';layout=json.loads((D/'CelestialGarden.json').read_text());surfaces=[];trees=[]

def matrix(p,yaw):
 m=np.eye(4);a=math.radians(yaw);m[:3,:3]=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]);m[:3,3]=p;return m

def height(x,z):
 top=-.2
 for tri in surfaces:
  a,b,c=tri;u=b-a;v=c-a;det=u[0]*v[2]-u[2]*v[0]
  if abs(det)<1e-8:continue
  q=np.array([x-a[0],z-a[2]]);s=(q[0]*v[2]-q[1]*v[0])/det;t=(u[0]*q[1]-u[2]*q[0])/det
  if s>=0 and t>=0 and s+t<=1:top=max(top,float(a[1]+s*u[1]+t*v[1]))
 return top

def place(item):
 folder=D/item['resource'].split('/')[-1];m=json.loads((folder/'Model.json').read_text());parts=[p for p in m['parts'] if not m.get('visibleGroups') or int(p['name'].split('-')[1]) in m['visibleGroups']];v=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in parts]);lo=v.min(0);hi=v.max(0);size=np.array(list(item['size'].values()));sc=size/np.maximum(.001,hi-lo);offset=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*sc;p=np.array(list(item['position'].values()),dtype=float)
 if item['kind'] not in ['ground','cloud']:p[1]=height(p[0],p[2])+.025
 if item['kind']=='ground' and item['resource'] not in ['Okami/celestial-meadow','Okami/celestial-terrace']:p[1]+=height(p[0],p[2])
 root=matrix(p,item['yaw'])
 for part in parts:
  tx=next(t for t in m['textures'] if t['index']==part['texture'])
  if tx.get('vertexOnly'):continue
  mat=texture_material(folder/tx['path'],item['kind']=='cloud')
  if item['kind']=='ground':
   for n in mat.node_tree.nodes:
    if n.type=='EMISSION' and not mat.get('celestial_ground'):
     old=n.inputs['Color'].links[0].from_socket;mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.06;mat.node_tree.links.new(old,mix.inputs[1]);mix.inputs[2].default_value=(.9,.94,.84,1);mat.node_tree.links.new(mix.outputs[0],n.inputs['Color']);mat['celestial_ground']=True
  if item['kind']=='pond' and part['name']=='Native-1-0':
   mat=mat.copy();nodes=mat.node_tree.nodes;links=mat.node_tree.links;geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0]);squares=[]
   for axis,centre,rad in [(0,p[0],size[0]*.32),(1,-p[2],size[2]*.32)]:
    sub=nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';links.new(sep.outputs[axis],sub.inputs[0]);sub.inputs[1].default_value=centre;div=nodes.new('ShaderNodeMath');div.operation='DIVIDE';links.new(sub.outputs[0],div.inputs[0]);div.inputs[1].default_value=rad;sq=nodes.new('ShaderNodeMath');sq.operation='MULTIPLY';links.new(div.outputs[0],sq.inputs[0]);links.new(div.outputs[0],sq.inputs[1]);squares.append(sq)
   add=nodes.new('ShaderNodeMath');add.operation='ADD';links.new(squares[0].outputs[0],add.inputs[0]);links.new(squares[1].outputs[0],add.inputs[1]);outside=nodes.new('ShaderNodeMath');outside.operation='GREATER_THAN';links.new(add.outputs[0],outside.inputs[0]);outside.inputs[1].default_value=1;out=nodes.get('Material Output');old=out.inputs['Surface'].links[0].from_socket;mix=nodes.new('ShaderNodeMixShader');links.new(old,mix.inputs[1]);links.new(nodes.new('ShaderNodeBsdfTransparent').outputs[0],mix.inputs[2]);links.new(outside.outputs[0],mix.inputs[0]);links.new(mix.outputs[0],out.inputs['Surface'])
  vv=np.array(part['positions']).reshape(-1,3)*sc+offset;faces=np.array(part['indices']).reshape(-1,3);ob=mesh(item['resource'],vv,faces,np.array(part['uv']).reshape(-1,2),mat,root,np.array(part['colors']).reshape(-1,4))
  if item['kind']=='cloud':
   for n in mat.node_tree.nodes:
    if n.type=='EMISSION':
     # Match the game's lighter source-cloud palette (native texture, no new painting).
     old=n.inputs['Color'].links[0].from_socket;mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.inputs[0].default_value=.55;mix.inputs[1].default_value=(.93,.93,1,1);mat.node_tree.links.new(old,mix.inputs[2]);mat.node_tree.links.new(mix.outputs[0],n.inputs['Color'])
  if item['kind']=='tree':trees.append((ob,root.copy()))
  if item['kind']=='ground':surfaces.extend((vv@root[:3,:3].T+root[:3,3])[faces])
for item in layout['items']:
 if item['kind']=='ground':place(item)
for item in layout['items']:
 if item['kind']!='ground':place(item)
# Native spirit shafts use the same original sprite as the production LineRenderers.
beams=[]
for x,z in [(0,23),(-20,-8),(21,9)]:
 mat=bpy.data.materials.new('Original spectral shaft');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(D/'Effects/SpiritGlow.png'),check_existing=True);em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=(1.5,1.6,2,1);em.inputs['Strength'].default_value=2;trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';alpha.inputs[1].default_value=.25;l.new(tex.outputs['Color'],alpha.inputs[0]);l.new(alpha.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);h=height(x,z)+1;ob=mesh('Original altar radiance',[[-1.75,0,0],[1.75,0,0],[.325,20,0],[-.325,20,0]],[[0,1,2],[0,2,3]],[[0,0],[1,0],[1,1],[0,1]],mat,matrix([x,h,z],0));beams.append((ob,np.array([x,h,z])))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.cycles.max_bounces=1;scene.cycles.transparent_max_bounces=16;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';# Bake the actual celestial sky colour/UV formula using the original Cloud painting.
cloud=np.asarray(Image.open(D/'Effects/Cloud.png').convert('RGB'))/255;yy,xx=np.mgrid[0:512,0:1024];u=xx/1024;v=1-yy/512;dy=np.sin((v-.5)*np.pi);f=np.clip(dy*.8+.2,0,1)[:,:,None];horizon=np.array([.98,.92,.86])*(1-f)+np.array([.64,.79,.95])*f;sample=cloud[((1-(v*2)%1)*(cloud.shape[0]-1)).astype(int),((u*3)%1*(cloud.shape[1]-1)).astype(int)];curl=np.clip((.83-sample.mean(2))*3,0,1)[:,:,None]*.45;sky=horizon*(1-curl)+np.array([.85,.77,.91])*curl;sky_path=OUT/'sky-diagnostic.png';Image.fromarray(np.uint8(np.clip(sky,0,1)*255)).save(sky_path);scene.world.use_nodes=True;nodes=scene.world.node_tree.nodes;tex=nodes.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(sky_path));scene.world.node_tree.links.new(tex.outputs['Color'],nodes['Background'].inputs['Color']);scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=400
for i,(pos,target,lens) in enumerate([([0,3,-23],[0,3,10],28),([30,17,-34],[0,1,1],28),([-30,4,-12],[-12,2,3],30),([0,4,16],[0,2,25],29)]):
 cam.location=CONVERT@Vector(pos);look=CONVERT@Vector(target);cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 for ob,root in trees:
  delta=np.array(pos)-root[:3,3];a=math.atan2(delta[0],delta[2]);new=matrix(root[:3,3],math.degrees(a));ob.matrix_world=CONVERT@Matrix(new)
 for ob,origin in beams:
  d=np.array(pos)-origin;ob.matrix_world=CONVERT@Matrix(matrix(origin,math.degrees(math.atan2(d[0],d[2]))))
 scene.render.filepath=str(OUT/f'garden-{i}.png');bpy.ops.render.render(write_still=True)
print('Rendered four offline views of the actual runtime layout; not Unity gameplay.',flush=True)
