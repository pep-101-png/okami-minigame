"""Offline diagnostic using exactly the runtime CelestialGarden placement JSON.
This does not run Unity or verify shader compilation/collision/playback.
"""
from pathlib import Path
import sys,os,json,math,argparse
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/spirit-charge-home/trailer'))
p=argparse.ArgumentParser();p.add_argument('--out',required=True);p.add_argument('--views',default='0,1,2,3,4');args=p.parse_args(sys.argv[sys.argv.index('--')+1:]);OUT=Path(args.out);OUT.mkdir(parents=True,exist_ok=True);os.environ['SUNWARD_PREVIEW_OUTPUT']=str(OUT)
from paint_renderer import *
from asset_geometry import rotation
from PIL import Image
# The shared offline helper leaves MAXIMUM's second input at Blender's .5
# default for two-sided paint. Explicit zero matches the opaque Unity shaders.
native_material=texture_material
def texture_material(path,two_sided=False):
 mat=native_material(path,two_sided)
 if two_sided:mat.node_tree.nodes['Math.001'].inputs[1].default_value=0
 return mat
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
D=A/'OkamiRemaster/Original/Resources/Okami';layout=json.loads((D/'CelestialGarden.json').read_text());surfaces=[];trees=[]

def matrix(p,yaw):
 m=np.eye(4);a=math.radians(yaw);m[:3,:3]=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]]);m[:3,3]=p;return m

def height(x,z):
 if not surfaces:return -.2
 tri=np.asarray(surfaces);a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a;det=b[:,0]*c[:,2]-b[:,2]*c[:,0];valid=abs(det)>1e-8;d0=x-a[:,0];d1=z-a[:,2];u=np.divide(d0*c[:,2]-d1*c[:,0],det,out=np.full(len(a),-1.),where=valid);v=np.divide(b[:,0]*d1-b[:,2]*d0,det,out=np.full(len(a),-1.),where=valid);hit=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001);return float(np.max((a[:,1]+u*b[:,1]+v*c[:,1])[hit])) if hit.any() else -.2

def sample(path,u,v):
 im=np.asarray(Image.open(path).convert('RGB'))/255;im=np.where(im<=.04045,im/12.92,((im+.055)/1.055)**2.4)
 return im[((1-v%1)*(im.shape[0]-1)).astype(int),((u%1)*(im.shape[1]-1)).astype(int)]
def floor_material(mode,extent,res):
 yy,xx=np.mgrid[0:res,0:res];x=-extent+xx/(res-1)*extent*2;z=extent-yy/(res-1)*extent*2;u=x*.866-z*.5;v=x*.5+z*.866
 paint=sample(D/'farm-earth/Grass.png',x*.065,z*.065)*.55+sample(D/'farm-earth/Grass.png',u*.047+.31,v*.047+.31)*.45
 shade=np.clip(np.einsum('ijk,k->ij',paint,[.3,.5,.2])*.8+.18,0,1)[:,:,None]
 col=paint*np.array([.98,1.12,1.05])*.9+np.array([.50,.64,.58])*.1
 cloud=sample(D/'Effects/Cloud.png',x*.014,z*.014);curl=np.clip((.8-cloud.mean(2))*4,0,1)[:,:,None]
 col=col*(1-curl*.035)+np.array([.72,.64,.87])*curl*.035
 if mode==1:
  nearest=np.full(x.shape,1000.)
  for w in layout['walks']:
   ax,az=w['a']['x'],w['a']['z'];bx,bz=w['b']['x'],w['b']['z'];dx,dz=bx-ax,bz-az;den=max(.000001,dx*dx+dz*dz);t=np.clip(((x-ax)*dx+(z-az)*dz)/den,0,1);distance=np.sqrt((x-ax-t*dx)**2+(z-az-t*dz)**2)-w['width'];nearest=np.minimum(nearest,distance)
  t=np.clip((nearest+.12)/.28,0,1);mask=(1-t*t*(3-2*t))[:,:,None];stone=sample(D/'celestial-stair/Texture-0.png',x*.18,z*.42)*1.16;col=col*(1-mask)+stone*mask
 if mode==2:col=np.array([.94,.95,1])*(1-curl*.4)+np.array([.86,.84,.95])*curl*.4
 target=OUT/('cloud-floor-diagnostic.png' if mode==2 else 'ground-diagnostic.png');encoded=np.where(col<=.0031308,col*12.92,1.055*np.maximum(col,0)**(1/2.4)-.055);Image.fromarray(np.uint8(np.clip(encoded,0,1)*255)).save(target)
 mat=texture_material(target,True);nodes=mat.node_tree.nodes;links=mat.node_tree.links;geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0]);combine=nodes.new('ShaderNodeCombineXYZ')
 for axis,src,scale in [(0,0,1/(2*extent)),(1,1,-1/(2*extent))]:
  node=nodes.new('ShaderNodeMath');node.operation='MULTIPLY_ADD';links.new(sep.outputs[src],node.inputs[0]);node.inputs[1].default_value=scale;node.inputs[2].default_value=.5;links.new(node.outputs[0],combine.inputs[axis])
 tex=next(n for n in nodes if n.type=='TEX_IMAGE');links.new(combine.outputs[0],tex.inputs['Vector']);return mat
terrain_material=floor_material(1,90,2048);cloud_material=floor_material(2,250,1024)

def place(item):
 folder=D/item['resource'].split('/')[-1];m=json.loads((folder/'Model.json').read_text());parts=[p for p in m['parts'] if not m.get('visibleGroups') or int(p['name'].split('-')[1]) in m['visibleGroups']];v=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in parts]);lo=v.min(0);hi=v.max(0);size=np.array(list(item['size'].values()));sc=size/np.maximum(.001,hi-lo);offset=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*sc;p=np.array(list(item['position'].values()),dtype=float)
 if item['kind'] not in ['ground','cloud','cloudsea']:p[1]=height(p[0],p[2])+.005
 if item['kind']=='pond':p[1]=min([p[1]]+[height(p[0]+x,p[2]+z)+.005 for x,z in [(-.4*size[0],-.4*size[2]),(.4*size[0],-.4*size[2]),(-.4*size[0],.4*size[2]),(.4*size[0],.4*size[2])]])
 if item['kind']=='ground' and not item.get('absoluteHeight') and item['resource'] not in ['Okami/celestial-meadow','Okami/celestial-terrace','Okami/celestial-grounded']:
  base=height(p[0],p[2])
  if item['resource']=='Okami/vt0a' and size[1]>.5:base=min([base]+[height(p[0]+x,p[2]+z) for x,z in [(-4,-4),(4,-4),(-4,4),(4,4)]])
  p[1]+=base
 root=matrix(p,item['yaw'])
 for part in parts:
  tx=next(t for t in m['textures'] if t['index']==part['texture'])
  if tx.get('vertexOnly'):continue
  isTerrain=item['resource'] in ['Okami/celestial-meadow','Okami/celestial-terrace','Okami/celestial-grounded']
  mat=cloud_material if item['kind']=='cloudsea' else terrain_material if item['kind']=='ground' and isTerrain else texture_material(folder/tx['path'],item['kind']=='cloud')
  if item['kind']=='pond' and part['name']=='Native-1-0':
   mat=mat.copy();nodes=mat.node_tree.nodes;links=mat.node_tree.links;geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0]);squares=[]
   for axis,centre,rad in [(0,p[0],size[0]*.32),(1,-p[2],size[2]*.32)]:
    sub=nodes.new('ShaderNodeMath');sub.operation='SUBTRACT';links.new(sep.outputs[axis],sub.inputs[0]);sub.inputs[1].default_value=centre;div=nodes.new('ShaderNodeMath');div.operation='DIVIDE';links.new(sub.outputs[0],div.inputs[0]);div.inputs[1].default_value=rad;sq=nodes.new('ShaderNodeMath');sq.operation='MULTIPLY';links.new(div.outputs[0],sq.inputs[0]);links.new(div.outputs[0],sq.inputs[1]);squares.append(sq)
   add=nodes.new('ShaderNodeMath');add.operation='ADD';links.new(squares[0].outputs[0],add.inputs[0]);links.new(squares[1].outputs[0],add.inputs[1]);outside=nodes.new('ShaderNodeMath');outside.operation='GREATER_THAN';links.new(add.outputs[0],outside.inputs[0]);outside.inputs[1].default_value=1;out=nodes.get('Material Output');old=out.inputs['Surface'].links[0].from_socket;mix=nodes.new('ShaderNodeMixShader');links.new(old,mix.inputs[1]);links.new(nodes.new('ShaderNodeBsdfTransparent').outputs[0],mix.inputs[2]);links.new(outside.outputs[0],mix.inputs[0]);links.new(mix.outputs[0],out.inputs['Surface'])
  vv=np.array(part['positions']).reshape(-1,3)*sc+offset;faces=np.array(part['indices']).reshape(-1,3);ob=mesh(item['resource'],vv,faces,np.array(part['uv']).reshape(-1,2),mat,root,np.ones((len(vv),4)) if item['kind']=='cloudsea' or (item['kind']=='ground' and (isTerrain or (item['resource']=='Okami/vt0a' and size[1]>1))) else np.array(part['colors']).reshape(-1,4))
  if item['kind']=='ground' and item['resource']=='Okami/vt0a' and size[1]>1:
   wall=texture_material(D/'celestial-stair/Texture-0.png').copy();nodes=wall.node_tree.nodes;links=wall.node_tree.links
   tex=next(n for n in nodes if n.type=='TEX_IMAGE');geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0]);combine=nodes.new('ShaderNodeCombineXYZ')
   # The original retaining sides are axis aligned; X-facing and Z-facing faces get their matching projection.
   cap=terrain_material.copy();cap.node_tree.links.new(cap.node_tree.nodes['Geometry'].outputs['Backfacing'],cap.node_tree.nodes['Math.001'].inputs[1]);ob.data.materials.append(wall);ob.data.materials.append(cap)
   for poly in ob.data.polygons:
    if abs(poly.normal.y)<.65:
     poly.material_index=1
    else:
     poly.material_index=2
   horizontal=nodes.new('ShaderNodeMath');horizontal.operation='ADD';links.new(sep.outputs['X'],horizontal.inputs[0]);links.new(sep.outputs['Y'],horizontal.inputs[1]);sx=nodes.new('ShaderNodeMath');sx.operation='MULTIPLY';sx.inputs[1].default_value=.15;links.new(horizontal.outputs[0],sx.inputs[0]);sy=nodes.new('ShaderNodeMath');sy.operation='MULTIPLY';sy.inputs[1].default_value=.8;links.new(sep.outputs['Z'],sy.inputs[0]);links.new(sx.outputs[0],combine.inputs['X']);links.new(sy.outputs[0],combine.inputs['Y']);links.new(combine.outputs[0],tex.inputs['Vector'])
  if item['kind']=='cloud':
   mat=mat.copy();ob.data.materials[0]=mat
   nodes=mat.node_tree.nodes;links=mat.node_tree.links;alpha=nodes.new('ShaderNodeMath');alpha.operation='MULTIPLY';alpha.inputs[1].default_value=3;alpha.use_clamp=True;links.new(nodes['Color Attribute'].outputs['Alpha'],alpha.inputs[0]);fade=nodes.new('ShaderNodeMath');fade.operation='SUBTRACT';fade.inputs[0].default_value=1;opacity=nodes.new('ShaderNodeMath');opacity.operation='MULTIPLY';opacity.inputs[1].default_value=.72;links.new(alpha.outputs[0],opacity.inputs[0]);links.new(opacity.outputs[0],fade.inputs[1]);links.new(fade.outputs[0],nodes['Math.001'].inputs[1])
   for n in mat.node_tree.nodes:
    if n.type=='EMISSION':
     # Match the game's lighter source-cloud palette (native texture, no new painting).
     old=next(node for node in mat.node_tree.nodes if node.type=='TEX_IMAGE').outputs['Color'];mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=(.96,.91,.84,1);mix.inputs[2].default_value=(.59,.63,.79,1);invert=mat.node_tree.nodes.new('ShaderNodeInvert');mat.node_tree.links.new(old,invert.inputs['Color']);mat.node_tree.links.new(invert.outputs['Color'],mix.inputs[0]);mat.node_tree.links.new(mix.outputs[0],n.inputs['Color'])
  if item['kind']=='tree':trees.append((ob,root.copy()))
  if item['kind']=='ground':surfaces.extend((vv@root[:3,:3].T+root[:3,3])[faces])
for item in layout['items']:
 if item['kind']=='ground':place(item)
for item in layout['items']:
 if item['kind']!='ground':place(item)
# Original keeper skin/idle pose, at the same grounded position as the runtime actor.
import struct
from asset_geometry import skin
folder=D/'garden-hm50';model=json.loads((folder/'Model.json').read_text());raw=(folder/'Poses.bytes').read_bytes();_,_,nb,count=struct.unpack_from('<4sIII',raw);off=16;pose=None
for _ in range(count):
 n=struct.unpack_from('<I',raw,off)[0];off+=4;name=raw[off:off+n].decode();off+=n;frames,duration,loop=struct.unpack_from('<IfI',raw,off);off+=12;a=np.frombuffer(raw,'<f4',frames*nb*10,off).reshape(frames,nb,10);off+=a.nbytes
 if name=='hm05_000':pose=a[0]
if pose is not None:
 root=matrix([0,height(0,17)+.025,17],180)
 for part,vv in zip(model['parts'],skin(model,pose)):
  tx=next(t for t in model['textures'] if t['index']==part['texture'])
  if not tx.get('vertexOnly'):mesh('Original keeper',vv*1.25,np.array(part['indices']).reshape(-1,3),np.array(part['uv']).reshape(-1,2),texture_material(folder/tx['path']),root,np.array(part['colors']).reshape(-1,4))
# Native spirit shafts use the same original sprite as the production LineRenderers.
beams=[]
for x,z in [(0,23),(22,-18),(23,19)]:
 mat=bpy.data.materials.new('Original spectral shaft');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(D/'Effects/SpiritGlow.png'),check_existing=True);em=n.new('ShaderNodeEmission');em.inputs['Color'].default_value=(1.5,1.6,2,1);em.inputs['Strength'].default_value=2;trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';alpha.inputs[1].default_value=.10;l.new(tex.outputs['Color'],alpha.inputs[0]);l.new(alpha.outputs[0],mix.inputs[0]);l.new(trans.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);h=height(x,z)+1;ob=mesh('Original altar radiance',[[-.9,0,0],[.9,0,0],[.175,20,0],[-.175,20,0]],[[0,1,2],[0,2,3]],[[0,0],[1,0],[1,1],[0,1]],mat,matrix([x,h,z],0));beams.append((ob,np.array([x,h,z])))

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.cycles.max_bounces=1;scene.cycles.transparent_max_bounces=16;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';# Bake the actual celestial sky colour/UV formula using the original Cloud painting.
cloud=np.asarray(Image.open(D/'Effects/Cloud.png').convert('RGB'))/255;yy,xx=np.mgrid[0:512,0:1024];u=xx/1024;v=1-yy/512;dy=np.sin((v-.5)*np.pi);f=np.clip(dy*.8+.2,0,1)[:,:,None];horizon=np.array([.98,.92,.86])*(1-f)+np.array([.64,.79,.95])*f;sample=cloud[((1-(v*2)%1)*(cloud.shape[0]-1)).astype(int),((u*3)%1*(cloud.shape[1]-1)).astype(int)];curl=np.clip((.83-sample.mean(2))*3,0,1)[:,:,None]*.45;sky=horizon*(1-curl)+np.array([.85,.77,.91])*curl;sky_path=OUT/'sky-diagnostic.png';Image.fromarray(np.uint8(np.clip(sky,0,1)*255)).save(sky_path);scene.world.use_nodes=True;nodes=scene.world.node_tree.nodes;tex=nodes.new('ShaderNodeTexEnvironment');tex.image=bpy.data.images.load(str(sky_path));scene.world.node_tree.links.new(tex.outputs['Color'],nodes['Background'].inputs['Color']);scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=400
for i,(pos,target,lens) in enumerate([([0,height(0,-23)+2.3,-23],[0,height(0,15)+2,15],28),([38,27,-40],[-3,2,3],28),([-31,5,-13],[-19,2,-2],28),([5,height(5,10)+3.4,10],[0,height(0,17)+1.4,17],32),([31,6,0],[19,2,4],28)]):
 if str(i) not in args.views.split(','):continue
 cam.location=CONVERT@Vector(pos);look=CONVERT@Vector(target);cam.rotation_euler=(look-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens
 for ob,root in trees:
  delta=np.array(pos)-root[:3,3];a=math.atan2(delta[0],delta[2]);new=matrix(root[:3,3],math.degrees(a));ob.matrix_world=CONVERT@Matrix(new)
 for ob,origin in beams:
  d=np.array(pos)-origin;ob.matrix_world=CONVERT@Matrix(matrix(origin,math.degrees(math.atan2(d[0],d[2]))))
 scene.render.filepath=str(OUT/f'garden-{i}.png');bpy.ops.render.render(write_still=True)
print('Rendered selected offline views of the actual runtime layout; not Unity gameplay.',flush=True)
