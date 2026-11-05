"""Offline native scene/placement geometry review. Does not run Unity shaders or collision."""
from pathlib import Path
import sys,os,json,numpy as np,math,re
ROOT=Path(__file__).resolve().parents[2];OUT=Path('/workspace/work/village-complete/previews');OUT.mkdir(exist_ok=True);os.environ['SUNWARD_PREVIEW_OUTPUT']=str(OUT);sys.path.insert(0,str(ROOT/'tools/spirit-charge-home/trailer'))
from paint_renderer import *
from PIL import Image
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
# The helper's two-sided branch must not retain Blender's .5 opacity default.
original=texture_material
def texture_material(path,two_sided=False):
 m=original(path,two_sided)
 if two_sided:m.node_tree.nodes['Math.001'].inputs[1].default_value=0
 return m
w=World();nativeGround=ground_material();D=A/'OkamiRemaster/Original/Resources/Okami'
rock=texture_material(D/'vt28/Texture-0.png',True)
# Diagnostic-only bake of the runtime analytic river mask using its original paint.
from PIL import Image
xx,zz=np.meshgrid(np.linspace(-60,70,1300),np.linspace(-48,48,960))
def rv(z):
 raw=lambda q:1.1*np.sin(q*.13)+.45*np.sin(q*.31)+2*np.exp(-((q+8)/4)**2)
 c=np.exp(-(26/4)**2);a=(raw(12)-raw(-14)*c)/(1-c*c);b=raw(-14)-a*c
 return -23+raw(z)-a*np.exp(-((z-12)/4)**2)-b*np.exp(-((z+14)/4)**2)
z=-zz;cx=rv(z);width=2.45+.4*np.sin(z*.17+.4)+.25*np.cos(z*.31);mask=(abs(xx-cx)<width*1.10)&(zz<=36.02)
raw=next((w.assets[g].read_text() for r in w.renderers() if r['name'].startswith('River-') for g in r['materials']),None)
guid=re.search(r'- _FlowMap:\n        m_Texture:.*guid: (\w+)',raw)[1];im=np.array(Image.open(w.assets[guid]).convert('RGBA'));u=((xx-cx)/(width*2)+.5)%1;v=(z*.052)%1;paint=im[((1-v)*(im.shape[0]-1)).astype(int),(u*(im.shape[1]-1)).astype(int)];paint[:,:,3]=mask*255
riverpaint=OUT/'river-mask-diagnostic.png';Image.fromarray(paint).save(riverpaint);riverMat=texture_material(riverpaint,True);nodes=riverMat.node_tree.nodes;links=riverMat.node_tree.links;texnode=next(n for n in nodes if n.type=='TEX_IMAGE');geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0]);comb=nodes.new('ShaderNodeCombineXYZ')
for axis,src,scale,offset in [(0,0,1/130,60/130),(1,1,-1/96,48/96)]:
 node=nodes.new('ShaderNodeMath');node.operation='MULTIPLY_ADD';links.new(sep.outputs[src],node.inputs[0]);node.inputs[1].default_value=scale;node.inputs[2].default_value=offset;links.new(node.outputs[0],comb.inputs[axis])
links.new(comb.outputs[0],texnode.inputs['Vector']);texnode.extension='EXTEND'
for row in w.renderers():
 if not row['lo'] is None and (row['hi'][1]<-12 or row['lo'][0]>25 or row['hi'][0]<-45):continue
 m=w.mesh(row['meshGUID'],row['meshID'])
 if m is None:continue
 raw=m['raw'];buf=bytes.fromhex(re.search('_typelessdata: ([a-f0-9]+)',raw)[1]);n=len(m['vertices']);uv=np.ndarray((n,2),'<f4',buffer=buf,offset=40,strides=(m['stride'],4)).copy() if m['stride']>=48 else np.zeros((n,2));col=np.ndarray((n,4),'<f4',buffer=buf,offset=24,strides=(m['stride'],4)).copy() if m['stride']>=48 else np.ones((n,4));v=m['vertices'];tri=m['triangles']
 # The real river shader truncates the flat water at the waterfall lip.
 if row['name'].startswith('River-'):tri=tri[v[tri].mean(1)[:,2]<=36.02]
 mat=riverMat if row['name'].startswith('River-') else nativeGround if 'ground · centre opening' in row['name'] else material(row['materials'][0],w) if row['materials'] else rock
 ob=mesh(row['name'],v,tri,uv,mat,row['matrix'],np.ones_like(col) if mat in [nativeGround,riverMat] else col)
 if mat==nativeGround:
  ob.data.materials.append(rock)
  for face in ob.data.polygons:
   # Blender transforms native Y-up to Z-up; rock only on the new gorge walls.
   if face.center.z>35.5 and abs(face.center.x+22)<10 and face.normal.y<.75:
    face.material_index=1
    for loopindex in face.loop_indices:
     point=ob.data.vertices[ob.data.loops[loopindex].vertex_index].co
     ob.data.uv_layers.active.data[loopindex].uv=((point.z*(1-abs(face.normal.z))+point.x*abs(face.normal.z))*.18,point.y*.18)

def put(resource,position,size,yaw=0):
 folder=D/resource;m=json.loads((folder/'Model.json').read_text());parts=[p for p in m['parts'] if not m.get('visibleGroups') or int(p['name'].split('-')[1]) in m['visibleGroups']];v=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in parts]);lo,hi=v.min(0),v.max(0);sc=np.array(size)/np.maximum(.001,hi-lo);offset=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*sc;angle=math.radians(yaw);root=np.eye(4);root[:3,:3]=np.array([[math.cos(angle),0,math.sin(angle)],[0,1,0],[-math.sin(angle),0,math.cos(angle)]]);root[:3,3]=position
 for p in parts:
  if resource=='et90' and p['name'].startswith('Native-0-'):continue
  t=next(t for t in m['textures'] if t['index']==p['texture']);paint=texture_material(folder/t['path'],resource!='et90');mesh(resource,np.array(p['positions']).reshape(-1,3)*sc+offset,np.array(p['indices']).reshape(-1,3),np.array(p['uv']).reshape(-1,2),paint,root,np.ones((len(p['positions'])//3,4)) if resource=='river-waterfall' else np.array(p['colors']).reshape(-1,4))
# Runtime waterfall: its source top-centre offsets exactly meet the river lip.
def river(z):
 def raw(q):return 1.1*math.sin(q*.13)+.45*math.sin(q*.31)+2*math.exp(-((q+8)/4)**2)
 cross=math.exp(-(26/4)**2);a=(raw(12)-raw(-14)*cross)/(1-cross*cross);b=raw(-14)-a*cross;return -23+raw(z)-a*math.exp(-((z-12)/4)**2)-b*math.exp(-((z+14)/4)**2)
x=river(-36);put('river-waterfall',(x-.036361,-6.54,36+.548696),(5,6.2,4.5),-37.445568)
# Original ET90 save model, separately framed for comparison with user reference.
put('et90',(-29.4,-249.88,-14),(2.3,2.15,3),180)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.cycles.max_bounces=1;scene.cycles.transparent_max_bounces=16;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.render.resolution_x=1600;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.world.color=(.5,.55,.6)
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.clip_end=400
for name,pos,target,lens in [('waterfall',(x+12,8,29),(x,-2.8,39),35),('waterfall-face',(x+10,4,34),(x,-3,38),35),('farm-house',(21,9,17),(14,1.5,29),38),('dojo-rear',(-15,10,27),(0,1,30),32),('save-mirror',(-25,-246,-19),(-29.4,-248.7,-14),45)]:
 cam.location=CONVERT@Vector(pos);cam.rotation_euler=(CONVERT@Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=lens;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
 if name=='waterfall':
  for px,py in [(350,130),(450,300),(100,200)]:
   direction=cam.rotation_euler.to_matrix()@Vector(((px/1600-.5)*36/lens,(.5-py/900)*36/lens*900/1600,-1));hit,loc,normal,idx,obj,_=scene.ray_cast(bpy.context.evaluated_depsgraph_get(),cam.location,direction.normalized());print('Waterfall diagnostic ray',px,py,hit,obj.name if obj else None,list(CONVERT.inverted()@loc) if hit else None,flush=True)
print('Rendered five offline native-geometry diagnostics; not Unity screenshots')
