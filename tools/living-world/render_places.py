"""Blender preview of the authored native meshes. NOT Unity visual validation."""
from pathlib import Path
import sys,re,math,struct
import bpy,numpy as np
from mathutils import Matrix,Quaternion,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/village'))
from native import Scene,ASSETS,vec
s=Scene(ASSETS/'Scenes/Windflower.unity');paths={re.search(r'guid: (\w+)',p.read_text())[1]:p.with_suffix('') for p in (ASSETS/'Generated/LivingPlaces').glob('*.asset.meta')}
convert=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)));cache={}
def world(t):
 if t in cache:return cache[t]
 b=s.blocks[t];x,y,z,w=map(float,re.search(r'm_LocalRotation: \{x: ([^,]+), y: ([^,]+), z: ([^,]+), w: ([^}]+)',b).groups());m=Matrix.Translation(vec(b,'m_LocalPosition'))@Quaternion((w,x,y,z)).to_matrix().to_4x4()@Matrix.Diagonal((*vec(b,'m_LocalScale'),1));p=int(re.search(r'm_Father: \{fileID: (-?\d+)',b)[1]);cache[t]=(world(p)@m if p else m);return cache[t]
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
mat=bpy.data.materials.new('Vertex painted native surfaces');mat.use_nodes=True;nodes=mat.node_tree.nodes;v=nodes.new('ShaderNodeVertexColor');v.layer_name='Pigment';mat.node_tree.links.new(v.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color']);nodes['Principled BSDF'].inputs['Roughness'].default_value=.85
ink=bpy.data.materials.new('Native ink');ink.use_nodes=True;nodes=ink.node_tree.nodes;nodes.clear();out=nodes.new('ShaderNodeOutputMaterial');em=nodes.new('ShaderNodeEmission');em.inputs['Color'].default_value=(.015,.01,.005,1);geo=nodes.new('ShaderNodeNewGeometry');tr=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');ink.node_tree.links.new(geo.outputs['Backfacing'],mix.inputs[0]);ink.node_tree.links.new(tr.outputs[0],mix.inputs[1]);ink.node_tree.links.new(em.outputs[0],mix.inputs[2]);ink.node_tree.links.new(mix.outputs[0],out.inputs[0])
objects=[]
for i in s.blocks:
 if s.kind(i)!=1 or not s.name(i).startswith(('Living places ·','Living ink ·')):continue
 r=s.component(i,23);mf=s.component(i,33)
 if not r or not mf or 'm_Enabled: 0\n' in s.blocks[r]:continue
 g=re.search(r'm_Mesh: .*guid: (\w+)',s.blocks[mf])[1]
 if g not in paths:continue
 raw=paths[g].read_text();n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);buf=bytes.fromhex(re.search(r'_typelessdata: (\w+)',raw)[1]);stride=len(buf)//n;pos=np.ndarray((n,3),dtype='<f4',buffer=buf,strides=(stride,4)).copy();normal=np.ndarray((n,3),dtype='<f4',buffer=buf,offset=12,strides=(stride,4)).copy();outline=s.name(i).startswith('Living ink')
 if outline:pos+=normal*.022
 ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: (\w+)',raw)[1]),dtype='<u4').reshape(-1,3)
 mesh=bpy.data.meshes.new(s.name(i));mesh.from_pydata(pos,[],ix);mesh.update()
 if not outline:
  colors=np.ndarray((n,4),dtype='<f4',buffer=buf,offset=24,strides=(stride,4)).copy();attr=mesh.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',colors.ravel())
 obj=bpy.data.objects.new(s.name(i),mesh);bpy.context.collection.objects.link(obj);obj.matrix_world=convert@world(s.transform(i));mesh.materials.append(ink if outline else mat);objects.append(obj)
 if outline:obj.visible_shadow=False;obj.visible_diffuse=False;obj.visible_glossy=False
bpy.ops.object.light_add(type='SUN',location=(0,-10,20));bpy.context.object.rotation_euler=(.3,-.4,-.7);bpy.context.object.data.energy=2
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.62,.56,.42,1);scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=88
outdir=ROOT/'tools/player-review/previews';outdir.mkdir(exist_ok=True)
for name,p,target,width,interior in [('market-stalls',(-8,9,-12),(0,1,0),18,False),('shrine-interior',(-10,13,19),(-.5,.7,29.2),17,True),('foodhall-interior',(-1,15,1),(10.5,.6,10),20,True)]:
 for obj in objects:obj.hide_render=interior and any(k in obj.name for k in ['roof','shoji walls','door jamb panels'])
 bpy.ops.object.camera_add(location=(convert@Vector((*p,1))).xyz);camera=bpy.context.object;t=(convert@Vector((*target,1))).xyz;camera.rotation_euler=(t-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=width;scene.camera=camera
 text=bpy.data.curves.new('Limitation','FONT');text.body='BLENDER MODEL PREVIEW — NOT UNITY';text.size=width*.014;label=bpy.data.objects.new('Preview limitation label',text);bpy.context.collection.objects.link(label);label.parent=camera;label.location=(-width*.48,width*.32,-1);text.materials.append(mat)
 scene.render.resolution_x=960;scene.render.resolution_y=660;scene.render.resolution_percentage=100;scene.render.filepath=str(outdir/(name+'.jpg'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(label,do_unlink=True);bpy.data.objects.remove(camera,do_unlink=True)

import hashlib,json
(outdir/'places-preview-metadata.json').write_text(json.dumps({'renderer':'Blender Cycles native asset model review','unityRendered':False,'scene':'actual saved Windflower scene, place geometry subset','sceneSha256':hashlib.sha256((ASSETS/'Scenes/Windflower.unity').read_bytes()).hexdigest(),'limitations':['No Unity lighting, shader, interaction, collision or motion validation','Residents are inspected separately; not included in these place-only previews'],'images':['market-stalls.jpg','shrine-interior.jpg','foodhall-interior.jpg']},indent=2)+'\n')
