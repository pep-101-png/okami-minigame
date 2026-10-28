"""Resolved Windflower + actual native spawn-pose diagnostics. BLENDER, not Unity."""
from pathlib import Path
import bpy,numpy as np,ast,struct,json,importlib.util,math,sys
from mathutils import Matrix,Quaternion,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from scene_data import World,A
from farm_data import read as farm
spec=importlib.util.spec_from_file_location('layout',ROOT/'tools/remaster/live/preview_windflower.py');layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
OUT=ROOT/'tools/repair/previews';OUT.mkdir(exist_ok=True);layout.OUT=OUT
RES=A/'OkamiRemaster/Player/Resources/NativePlayer';scope={'np':np,'struct':struct,'bpy':bpy,'Path':Path,'Quaternion':Quaternion,'RES':RES,'materials':{}}
p=ROOT/'tools/remaster/live/preview_player.py'
for node in ast.parse(p.read_text()).body:
    if isinstance(node,ast.FunctionDef) and node.name in ['read_bank','skin','material']:exec(compile(ast.Module([node],[]),str(p),'exec'),scope)
def ground_material():
    material=bpy.data.materials.new('Continuous native paint — Blender approximation');material.use_nodes=True;n=material.node_tree.nodes;l=material.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.9
    image=n.new('ShaderNodeTexImage');image.image=bpy.data.images.load('/workspace/work/repair/ground-colour-reference.png');image.extension='EXTEND';geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0]);combine=n.new('ShaderNodeCombineXYZ')
    for axis,source,scale,offset in [(0,0,1/130,60/130),(1,1,-1/96,48/96)]:
        calc=n.new('ShaderNodeMath');calc.operation='MULTIPLY_ADD';l.new(sep.outputs[source],calc.inputs[0]);calc.inputs[1].default_value=scale;calc.inputs[2].default_value=offset;l.new(calc.outputs[0],combine.inputs[axis])
    l.new(combine.outputs[0],image.inputs['Vector']);l.new(image.outputs['Color'],bs.inputs['Base Color']);return material
def mesh(name,v,faces,uv,material,matrix=np.eye(4)):
    m=bpy.data.meshes.new(name);m.from_pydata(np.asarray(v).tolist(),[],np.asarray(faces).tolist());m.update();layer=m.uv_layers.new()
    for loop in m.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
    ob=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(ob);ob.matrix_world=layout.CONVERT@Matrix(matrix);m.materials.append(material);return ob
def painted_texture(path):
    mat=bpy.data.materials.new(path.stem);mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links;em=n.new('ShaderNodeEmission');tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);l.new(tex.outputs['Color'],em.inputs['Color']);tr=n.new('ShaderNodeBsdfTransparent');geo=n.new('ShaderNodeNewGeometry');alpha=n.new('ShaderNodeMath');alpha.operation='LESS_THAN';alpha.inputs[1].default_value=.3;l.new(tex.outputs['Alpha'],alpha.inputs[0]);maximum=n.new('ShaderNodeMath');maximum.operation='MAXIMUM';l.new(alpha.outputs[0],maximum.inputs[0]);l.new(geo.outputs['Backfacing'],maximum.inputs[1]);mix=n.new('ShaderNodeMixShader');l.new(maximum.outputs[0],mix.inputs[0]);l.new(em.outputs[0],mix.inputs[1]);l.new(tr.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);return mat
def add_animals():
    assets=farm();placements=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json').read_text())['actors']
    for a in placements:
        asset=assets[a['asset']];clip=asset['clips']['idle'];time=a['seed']*2.3;frame=time%clip['duration']/clip['duration']*(len(clip['poses'])-1);f=int(frame);j=min(f+1,len(clip['poses'])-1);u=frame-f;poses=clip['poses'];matrices=[];bind=[];lift=clip['ground'][f]*(1-u)+clip['ground'][j]*u
        for i,parent in enumerate(asset['parents']):
            pos=poses[f,i,:3]*(1-u)+poses[j,i,:3]*u;s=poses[f,i,7:]*(1-u)+poses[j,i,7:]*u;qa=poses[f,i,3:7];qb=poses[j,i,3:7];q=Quaternion((float(qa[3]),*map(float,qa[:3]))).slerp(Quaternion((float(qb[3]),*map(float,qb[:3]))),float(u));local=np.eye(4);local[:3,:3]=np.array(q.to_matrix())@np.diag(s);local[:3,3]=pos
            matrices.append(local if parent<0 else matrices[parent]@local);bind.append(np.asarray(asset['bind'][i])+(0 if parent<0 else bind[parent]))
        matrices=np.asarray(matrices);bind=np.asarray(bind);yaw=Matrix.Rotation(math.radians(a['yaw']),4,'Y');root=np.asarray(yaw);root[:3,3]=[a['position']['x'],a['position']['y'],a['position']['z']]
        for part in asset['parts']:
            v=part['vertices'];p=np.zeros_like(v)
            for k in range(3):
                indices=part['bones'][:,k];p+=part['weights'][:,k,None]*(np.einsum('nij,nj->ni',matrices[indices,:3,:3],v-bind[indices])+matrices[indices,:3,3])
            p+=asset['offset']+np.array([0,lift,0]);mesh(a['name'],p,part['faces'],part['uv'],painted_texture(A/'OkamiRemaster/Village/Resources/FarmTextures'/(part['texture']+'.png')),root)
def add_player_and_weapon():
    body=json.loads((RES/'pl00/Model.json').read_text());bank=scope['read_bank'](RES/'pl00/Poses.bytes');pose=bank['pl00_000'][0];p=scope['skin'](body,pose);root=np.eye(4);root[:3,3]=[-34,-.057714887,-22]
    for part,v in zip(body['parts'],p):mesh('Native Amaterasu pose',v,np.asarray(part['indices']).reshape(-1,3),np.asarray(part['uv']).reshape(-1,2),scope['material']('pl00',part['texture']),root)
    mats=[];rotations=[]
    for i,record in enumerate(pose):
        q=Quaternion((float(record[6]),*map(float,record[3:6])));m=Matrix.Translation(Vector(record[:3]))@q.to_matrix().to_4x4()@Matrix.Diagonal((*record[7:],1));parent=body['bones'][i-1]['parent']+1 if i else -1;mats.append(m if parent<0 else mats[parent]@m);rotations.append(q if parent<0 else rotations[parent]@q)
    mount=rotations[31].to_matrix().to_4x4();mount.translation=mats[31].translation
    weapon=json.loads((RES/'wp24/Model.json').read_text());wp=scope['read_bank'](RES/'wp24/Poses.bytes')['wp24_000'][0]
    for part,v in zip(weapon['parts'],scope['skin'](weapon,wp)):mesh('Native Solar Flare dorsal pose',v,np.asarray(part['indices']).reshape(-1,3),np.asarray(part['uv']).reshape(-1,2),scope['material']('wp24',part['texture']),root@np.asarray(mount))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);w=World();ground=ground_material();count=0
for row in w.renderers():
    if row['kind']!=23:continue
    source=w.mesh(row['meshGUID'],row['meshID'])
    if source is None or len(source['triangles'])==0:continue
    g=row['materials'][0] if row['materials'] else None;materialfile=w.assets.get(g)
    shaderfile=w.assets.get(__import__('scene_data').ref(materialfile.read_text(),'m_Shader')[1]) if materialfile else None
    outline=bool(shaderfile and shaderfile.name=='InkContour.shader')
    material=ground if materialfile and materialfile.name=='Continuous-Ground.mat' else layout.mat(row['name'],g,outline=outline)
    layout.add_object(row['name'],(row['meshGUID'],row['meshID']),source['raw'],material,Matrix(row['matrix']),outline=outline);count+=1
add_animals();add_player_and_weapon()
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.rotation_euler=(.4,-.4,-.5);sun.data.energy=2.0;sun.data.angle=.2
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=False;s.cycles.max_bounces=4;s.cycles.transparent_max_bounces=8;s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.65,.64,.58,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=-.3
for name,position,target,width in [('street',(-5,9,-22),(3,1.6,-8),27),('village',(-25,34,-20),(-4,0,0),75),('arena',(35,27,28),(35,0,0),46),('animals',(-39,10,26),(-42,0,18),25),('solar',(-38,2.8,-25),(-34,1,-22),4.6)]:layout.render('repair-'+name,position,target,width,(1100,720))
print('Blender-only resolved static renderers:',count)
