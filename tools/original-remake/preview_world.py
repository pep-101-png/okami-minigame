"""Blender diagnostics of the actual saved scene and exported native poses.

Never call these Unity screenshots, gameplay recordings or compilation evidence.
"""
from pathlib import Path
import bpy,json,math,re,struct,sys,os
import numpy as np
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';OUT=Path(os.environ.get('SUNWARD_PREVIEW_OUTPUT',str(Path(__file__).with_name('previews'))));OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref,vec
sys.path.insert(0,str(Path(__file__).parent));from export_assets import skin
CONVERT=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
MATERIALS={}
def texture_material(path):
    key=str(path)
    if key in MATERIALS:return MATERIALS[key]
    m=bpy.data.materials.new(path.stem);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.new('ShaderNodeEmission')
    # Native paint is intrinsically lit (minimum 82% in the Unity port). A PBR
    # shader makes inverted ink shells occlude every light ray and invents black
    # houses/people. Use flat paint for these explicitly non-Unity diagnostics.
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);vertex=n.new('ShaderNodeVertexColor');vertex.layer_name='Original pigment';mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(tex.outputs['Color'],mul.inputs[1]);l.new(vertex.outputs['Color'],mul.inputs[2]);l.new(mul.outputs[0],bs.inputs['Color']);trans=n.new('ShaderNodeBsdfTransparent');geo=n.new('ShaderNodeNewGeometry');alpha=n.new('ShaderNodeMath');alpha.operation='LESS_THAN';alpha.inputs[1].default_value=.3;l.new(tex.outputs['Alpha'],alpha.inputs[0]);hide=n.new('ShaderNodeMath');hide.operation='MAXIMUM';l.new(alpha.outputs[0],hide.inputs[0]);l.new(geo.outputs['Backfacing'],hide.inputs[1]);mix=n.new('ShaderNodeMixShader');l.new(hide.outputs[0],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);MATERIALS[key]=m;return m
def material(g,w):
    path=w.assets.get(g);raw=path.read_text() if path else '';tex=re.search(r'- (?:_MainTex|_FlowMap|_OriginalPaint):\n        m_Texture:.*guid: (\w+)',raw)
    if tex and tex[1] in w.assets:return texture_material(w.assets[tex[1]])
    m=bpy.data.materials.new('Native vertex colour');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;v=n.new('ShaderNodeVertexColor');v.layer_name='Original pigment';em=n.new('ShaderNodeEmission');l.new(v.outputs['Color'],em.inputs['Color']);trans=n.new('ShaderNodeBsdfTransparent');geo=n.new('ShaderNodeNewGeometry');mix=n.new('ShaderNodeMixShader');l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(em.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);return m
def mesh(name,v,faces,uv,mat,matrix=np.eye(4),colors=None):
    m=bpy.data.meshes.new(name);m.from_pydata(np.asarray(v).tolist(),[],np.asarray(faces).tolist());m.update();layer=m.uv_layers.new()
    for loop in m.loops:layer.data[loop.index].uv=uv[loop.vertex_index]
    if colors is None:colors=np.ones((len(v),4))
    attr=m.color_attributes.new(name='Original pigment',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.asarray(colors,dtype=np.float32).ravel())
    ob=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(ob);ob.matrix_world=CONVERT@Matrix(matrix);m.materials.append(mat);return ob
def ground_material():
    # Bake the same two original paintings through the existing layout mask.
    from PIL import Image
    tex=A/'OkamiRemaster/Original/Textures';mask=np.asarray(Image.open(A/'OkamiRemaster/Windflower/Textures/Existing-Road-Bank-Mask.png').convert('RGB')).astype(float)/255
    width,height=mask.shape[1],mask.shape[0];x,z=np.meshgrid(np.linspace(-60,70,width),np.linspace(-48,48,height))
    def sample(path,u,v):
        im=np.asarray(Image.open(path).convert('RGB')).astype(float)/255
        u=1-abs((u%2)-1);v=1-abs((v%2)-1);return im[((1-v)*(im.shape[0]-1)).astype(int), (u*(im.shape[1]-1)).astype(int)]
    a=sample(tex/'Kamiki-grass.png',x*.035,z*.035);b=sample(tex/'Kamiki-grass.png',(x*.9397-z*.342)*(.035*.73)+.31,(x*.342+z*.9397)*(.035*.73)+.57);grass=a*.65+b*.35;earth=sample(tex/'Kamiki-earth.png',x*.05,z*.05);blend=np.maximum(mask[:,:,0],mask[:,:,1])[:,:,None];color=grass*(1-blend)+earth*blend;target=OUT/'ground-diagnostic.png';Image.fromarray(np.uint8(np.clip(color,0,1)*255)).save(target)
    m=texture_material(target);n=m.node_tree.nodes;l=m.node_tree.links;texnode=next(x for x in n if x.type=='TEX_IMAGE');texnode.extension='EXTEND';geo=n.new('ShaderNodeNewGeometry');sep=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],sep.inputs[0]);comb=n.new('ShaderNodeCombineXYZ')
    for axis,src,scale,offset in [(0,0,1/130,60/130),(1,1,-1/96,48/96)]:
        node=n.new('ShaderNodeMath');node.operation='MULTIPLY_ADD';l.new(sep.outputs[src],node.inputs[0]);node.inputs[1].default_value=scale;node.inputs[2].default_value=offset;l.new(node.outputs[0],comb.inputs[axis])
    l.new(comb.outputs[0],texnode.inputs['Vector']);return m
def read_pose(path,name,end=False):
    data=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',data);off=16;assert magic==b'OPB1'
    for _ in range(count):
        n=struct.unpack_from('<I',data,off)[0];off+=4;label=data[off:off+n].decode();off+=n;samples,duration,loop=struct.unpack_from('<IfI',data,off);off+=12;values=np.frombuffer(data,'<f4',samples*bones*10,off).reshape(samples,bones,10);off+=values.nbytes
        if label==name:return values[-1] if end else values[0]
    raise ValueError(name)
def actor(record,matrix=None):
    resource=record['resource'];folder=next(p/resource for p in A.rglob('Resources') if (p/resource/'Model.json').exists());model=json.loads((folder/'Model.json').read_text());pose=read_pose(folder/'Poses.bytes',record['bindings']['idle'],record.get('holdIdlePose',False));verts=skin(model,pose);local=np.eye(4);local[:3,:3]*=record['modelScale'];local[:3,3]=record['modelOffset'];root=(np.asarray(record['matrix']) if matrix is None else matrix)@local
    for part,v in zip(model['parts'],verts):
        if model.get('visibleGroups') and int(part['name'].split('-')[1]) not in model['visibleGroups']:continue
        t=next(t for t in model['textures'] if t['index']==part['texture'])
        if t.get('vertexOnly'):continue
        mesh(resource,v,np.asarray(part['indices']).reshape(-1,3),np.asarray(part['uv']).reshape(-1,2),texture_material(folder/t['path']),root,colors=np.asarray(part['colors']).reshape(-1,4))
def animals():
    from farm_data import read
    from mathutils import Quaternion
    assets=read();placements=json.loads((A/'OkamiRemaster/Windflower/Resources/WindflowerNative/Animals.json').read_text())['actors']
    for p in placements:
        a=assets[p['asset']];clip=a['clips']['idle'];pose=clip['poses'][0];matrices=[];bind=[]
        for i,parent in enumerate(a['parents']):
            q=pose[i,3:7];m=np.eye(4);m[:3,:3]=np.asarray(Quaternion((float(q[3]),*map(float,q[:3]))).to_matrix())@np.diag(pose[i,7:]);m[:3,3]=pose[i,:3];matrices.append(m if parent<0 else matrices[parent]@m);bind.append(np.asarray(a['bind'][i])+(0 if parent<0 else bind[parent]))
        matrices=np.asarray(matrices);bind=np.asarray(bind);yaw=math.radians(p['yaw']);root=np.array([[math.cos(yaw),0,math.sin(yaw),p['position']['x']],[0,1,0,p['position']['y']],[ -math.sin(yaw),0,math.cos(yaw),p['position']['z']],[0,0,0,1.]])
        for part in a['parts']:
            v=part['vertices'];posed=np.zeros_like(v)
            for k in range(3):
                ix=part['bones'][:,k];posed+=part['weights'][:,k,None]*(np.einsum('nij,nj->ni',matrices[ix,:3,:3],v-bind[ix])+matrices[ix,:3,3])
            posed+=a['offset']+np.array([0,clip['ground'][0],0]);mesh(p['name'],posed,part['faces'],part['uv'],texture_material(A/'OkamiRemaster/Village/Resources/FarmTextures'/(part['texture']+'.png')),root)

bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);w=World();ground=ground_material();count=0;renderer_objects={}
billboards={w.scene.transform(w.scene.owner(i)) for i,b in w.scene.blocks.items() if 'Assembly-CSharp::Sunward.Remaster.OriginalBillboard\n' in b};billboard_objects=[]
for r in w.renderers():
    if r['kind']!=23:continue
    data=w.mesh(r['meshGUID'],r['meshID'])
    if data is None or not len(data['triangles']):continue
    n=len(data['vertices']);buf=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',data['raw'])[1]);streams=np.frombuffer(buf,'<f4').reshape(n,data['stride']//4);uv=streams[:,10:12] if data['stride']>=48 else np.zeros((n,2));colors=streams[:,6:10] if data['stride']>=48 else np.ones((n,4));g=r['materials'][0] if r['materials'] else None
    mat=ground if w.assets.get(g) and w.assets[g].name=='Original-Ground.mat' else material(g,w)
    ob=mesh(r['name'],data['vertices'],data['triangles'],uv,mat,r['matrix'],colors);count+=1
    renderer_objects[r['instance'],r['renderer']]=ob
    if not r['instance']:
        t=w.scene.transform(r['go'])
        while t:
            if t in billboards:
                anchor=w.matrix(0,t);billboard_objects.append((ob,anchor,np.linalg.inv(anchor)@r['matrix']));break
            t=ref(w.scene.blocks[t],'m_Father')[0]
report=json.loads(Path(__file__).with_name('world-install.json').read_text())
def saved_actor(source,id,instance=0):
    raw=source.blocks[id];resource=re.search(r'^  resource: (.+)',raw,re.M)[1];idle=re.search(r'^  idle: (.+)',raw,re.M)[1];go=source.owner(id)
    return dict(resource=resource,bindings=dict(idle=idle),modelScale=float(re.search(r'^  modelScale: (.+)',raw,re.M)[1]),modelOffset=vec(raw,'modelOffset').tolist(),matrix=w.matrix(instance,source.transform(go)).tolist(),holdIdlePose='  holdIdlePose: 1\n' in raw)
for instance,source in [(0,w.scene),*w.prefabs.items()]:
    for id,raw in source.blocks.items():
        if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' in raw and '  m_Enabled: 0\n' not in raw:actor(saved_actor(source,id,instance))
animals()
player=dict(resource='NativePlayer/pl00',bindings=dict(idle='pl00_000'),modelScale=1,modelOffset=[0,0,0],matrix=np.eye(4).tolist());player['matrix'][0][3]=-34;player['matrix'][1][3]=-.057714887;player['matrix'][2][3]=-22;actor(player)
for i,e in enumerate(report['enemyVisuals']):
    # Diagnostic arena lineup, not a claim of a recorded runtime wave.
    from native import Scene
    source=Scene(A/'Sunward/Generated'/('Enemy-'+e['role']+'.prefab'));id=next(id for id,raw in source.blocks.items() if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' in raw);raw=source.blocks[id];e=dict(e,modelScale=float(re.search(r'^  modelScale: (.+)',raw,re.M)[1]),modelOffset=vec(raw,'modelOffset').tolist())
    root=np.eye(4);definition=(A/'Sunward/Generated'/('Spirit-'+e['role']+'.asset')).read_text();scale=float(re.search(r'^  scale: ([^\n]+)',definition,re.M)[1]);root[:3,:3]*=scale;root[:3,3]=[28+(i%3)*5,0,-5+(i//3)*8];actor(e,root)
bpy.ops.object.light_add(type='SUN');sun=bpy.context.object;sun.rotation_euler=(.4,-.4,-.5);sun.data.energy=1.8;sun.data.angle=.18
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=8;s.cycles.use_denoising=False;s.cycles.max_bounces=4;s.cycles.transparent_max_bounces=12;s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.68,.67,.60,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.7;s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=-.3
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';s.camera=camera
shots=[('village',(-24,30,-28),(-4,0,1),73),('market',(-4,7,-15),(0,1,0),22),('houses',(-19,10,-23),(-8,2,-12),24),('arena',(31,22,24),(35,0,0),43),('farm',(-37,10,28),(-42,0,18),24),('home',(-43,10,-26),(-34,1,-16),22)]
if (ROOT/'tools/playtest-repair/scene-repairs.json').exists():shots += [('dojo',(0,13,13),(0,1,25),23),('food-house',(18,10,-7),(10,1,-15),16)]
receipts=[]
for name,position,target,width in shots:
    for ob in renderer_objects.values():ob.hide_render=False
    for raw in w.scene.blocks.values():
        if 'Assembly-CSharp::Sunward.Remaster.VenueVisibility\n' not in raw:continue
        venue=re.search(r'^  venue: (.+)',raw,re.M)[1]
        if (venue=='dojo' and name=='dojo') or (venue=='food' and name=='food-house'):
            roof=re.search(r'  roof:\n(.*?)(?=  interiorSurfaces:|  contents:)',raw,re.S)[1]
            for id in re.findall(r'fileID: (\d+)',roof):
                if (0,int(id)) in renderer_objects:renderer_objects[0,int(id)].hide_render=True
        elif '  interiorSurfaces:\n' in raw:
            surfaces=re.search(r'  interiorSurfaces:\n(.*?)(?=  contents:)',raw,re.S)[1]
            for id in re.findall(r'fileID: (\d+)',surfaces):
                if (0,int(id)) in renderer_objects:renderer_objects[0,int(id)].hide_render=True
    for ob,base,relative in billboard_objects:
        forward=np.asarray(position)-base[:3,3];forward[1]=0;forward/=max(.001,np.linalg.norm(forward));right=np.cross([0,1,0],forward);new=base.copy();new[:3,:3]=np.column_stack([right,[0,1,0],forward])@np.diag(np.linalg.norm(base[:3,:3],axis=0));ob.matrix_world=CONVERT@Matrix(new@relative)
    camera.location=CONVERT@Vector(position);look=CONVERT@Vector(target);camera.rotation_euler=(look-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=width;s.render.resolution_x=1200;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    receipts.append(dict(image=name+'.png',renderer='Blender Cycles',Unity=False,sceneSHA256=__import__('hashlib').sha256((A/'Sunward/Scenes/Windflower.unity').read_bytes()).hexdigest(),note='Actual saved static scene plus offline source pose previews; arena enemies are a diagnostic lineup.'))
(OUT/'preview-metadata.json').write_text(json.dumps(receipts,indent=2));print('Static saved-scene renderers:',count)
