"""Blender previews of current saved meshes and house transforms, not Unity."""
from pathlib import Path
import sys,re,bpy,numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from apply import read_mesh
sys.path.insert(0,str(ROOT/'tools/player-review'));from scene_tools import *
s=Scene(ASSETS/'Scenes/Windflower.unity');index=asset_index()
DEST=Path(__file__).parent/'previews';DEST.mkdir(exist_ok=True)
convert=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))

def reset():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def add(path,matrix=None):
 m=read_mesh(path);mesh=bpy.data.meshes.new(path.stem);mesh.from_pydata(m.v,[],m.tri);mesh.update();obj=bpy.data.objects.new(path.stem,mesh);bpy.context.collection.objects.link(obj);obj.matrix_world=convert@(Matrix(matrix.tolist()) if matrix is not None else Matrix.Identity(4))
 col=mesh.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='POINT');col.data.foreach_set('color',np.column_stack([np.array(m.c),np.ones(len(m.v))]).ravel())
 mat=bpy.data.materials.new(path.stem);mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Roughness'].default_value=.9;vc=mat.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Pigment';mat.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat)
 for f in mesh.polygons:f.use_smooth=True
 return obj

def render(name,target,camera,width):
 bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.06));mat=bpy.data.materials.new('Earth');mat.diffuse_color=(.24,.26,.16,1);bpy.context.object.data.materials.append(mat)
 for p,power in [((4,-5,10),1100),((-4,3,6),700)]:
  bpy.ops.object.light_add(type='AREA',location=p);bpy.context.object.data.energy=power;bpy.context.object.data.size=5
 bpy.ops.object.camera_add(location=camera);cam=bpy.context.object;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=width;scene=bpy.context.scene;scene.camera=cam
 scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.world.color=(.3,.3,.3);scene.render.resolution_x=1300;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG'
 text=bpy.data.curves.new('Limitation','FONT');text.body='BLENDER GEOMETRY PREVIEW — NOT UNITY';text.size=width*.014;label=bpy.data.objects.new('Limitation',text);bpy.context.collection.objects.link(label);label.parent=cam;label.location=(-width*.48,width*.33,-1)
 scene.render.filepath=str(DEST/(name+'.jpg'));bpy.ops.render.render(write_still=True)
reset();add(ASSETS/'Generated/PlayerReview3/Rooted-trunk-0.asset');render('integrated-root-closeup',(0,0,.6),(4,-6,2.8),4.8)
reset()
for j,n in enumerate([0,3,6]):
 t=np.eye(4);t[0,3]=(j-1)*3.2
 for part in ['culms','leaf-fans']:add(ASSETS/f'Generated/LivingWorld/Environment/Bamboo-{n}-{part}.asset',t)
render('three-unique-bamboo-clumps',(0,0,2.6),(9,-15,7),12.5)
reset()
for go in s.blocks:
 if s.kind(go)!=1 or not active(s,go):continue
 name=s.name(go)
 selected=name.startswith('Village house 0 ·') or name=='Review 3 · wall anchored doorway supports 0'
 if name=='Ink world · curved entrance fascia 0':selected=True
 if not selected:continue
 r=s.component(go,23);mf=s.component(go,33)
 if not r or not mf or '  m_Enabled: 0\n' in s.blocks[r]:continue
 g=re.search(r'guid: (\w+)',s.blocks[mf])[1]
 if g in index:add(index[g],world(s,s.transform(go),{}))
render('wall-attached-doorway',(-6,15,1.8),(-.2,9,5),8.5)
