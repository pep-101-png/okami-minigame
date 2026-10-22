"""Offline layout review of the ACTUAL saved Windflower scene in Blender.

  blender -b -t 4 -P tools/ink-world/preview_scene.py

Reads active saved MeshFilter/renderer objects, their complete transform ancestry,
visible TownV3 prefab source meshes, and prefab mesh/material overrides. No game
files are written. Pigment material sampling is an approximation; Unity lighting,
animation, water shading, fog, postprocessing and screen-space stroke widths are
NOT reproduced. Images carry a permanent non-Unity label.
"""
from pathlib import Path
import sys,re,json,math,hashlib
import bpy
import numpy as np
from mathutils import Matrix,Quaternion,Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
from native import Scene,ASSETS,vec
from build import Sources
OUT=ROOT/'tools/ink-world/previews'
OUT.mkdir(parents=True,exist_ok=True)
SCENE_TEXT=(ASSETS/'Scenes/Windflower.unity').read_text()
SCENE_SHA256=hashlib.sha256(SCENE_TEXT.encode()).hexdigest()
SCENE=Scene(ASSETS/'Scenes/Windflower.unity',text=SCENE_TEXT)
SOURCES=Sources(SCENE)
GUIDS={}
for meta in ASSETS.rglob('*.meta'):
    m=re.search(r'^guid: (\w+)',meta.read_text(),re.M)
    if m:GUIDS[m[1]]=meta.with_suffix('')

CONVERT=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
MESHES={};MATERIALS={};WORLD={};ACTIVE={}
OVERRIDES={}
for m in re.finditer(r'    - target: \{fileID: (-?\d+),[^\n]+\}\n      propertyPath: ([^\n]+)\n      value: ([^\n]*)\n      objectReference: ([^\n]+)',SCENE.blocks[SOURCES.instance]):
    OVERRIDES[(int(m[1]),m[2].strip("'"))]=(m[3],m[4])


def reference(raw,key):
    m=re.search(re.escape(key)+r': \{fileID: (-?\d+)(?:, guid: (\w+))?',raw)
    return (int(m[1]),m[2]) if m else (0,None)


def world(scene,t):
    key=(id(scene),t)
    if key in WORLD:return WORLD[key]
    if not t or t not in scene.blocks:return Matrix.Identity(4)
    b=scene.blocks[t]
    if 'm_LocalPosition:' not in b:
        source=reference(b,'m_CorrespondingSourceObject')[0]
        result=world(SOURCES.prefab,source) if scene is SCENE and source in SOURCES.prefab.blocks else Matrix.Identity(4)
        WORLD[key]=result;return result
    p=vec(b,'m_LocalPosition');s=vec(b,'m_LocalScale')
    q=re.search(r'm_LocalRotation: \{x: ([^,]+), y: ([^,]+), z: ([^,]+), w: ([^}]+)',b)
    x,y,z,w=map(float,q.groups());rot=Quaternion((w,x,y,z)).to_matrix().to_4x4()
    mat=Matrix.Translation(p)@rot@Matrix.Diagonal((*s,1))
    parent=reference(b,'m_Father')[0]
    WORLD[key]=world(scene,parent)@mat if parent else mat
    return WORLD[key]


def active(scene,go):
    key=(id(scene),go)
    if key in ACTIVE:return ACTIVE[key]
    if '  m_IsActive: 0\n' in scene.blocks[go]:ACTIVE[key]=False;return False
    t=scene.transform(go)
    if not t:return False
    parent=reference(scene.blocks[t],'m_Father')[0]
    parent_go=scene.owner(parent) if parent in scene.blocks else None
    ACTIVE[key]=active(scene,parent_go) if parent_go and scene.kind(parent_go)==1 else True
    return ACTIVE[key]


def mesh_data(raw):
    n=int(re.search(r'm_VertexCount: (\d+)',raw)[1])
    buf=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',raw)[1]);stride=len(buf)//n
    channels=re.search(r'    m_Channels:\n(.*?)(?=    m_DataSize:)',raw,re.S)[1]
    channels=[tuple(map(int,m)) for m in re.findall(r'- stream: (\d+)\n      offset: (\d+)\n      format: (\d+)\n      dimension: (\d+)',channels)]
    def get(i,default):
        if i>=len(channels) or not channels[i][3]:return np.tile(default,(n,1))
        stream,offset,fmt,dim=channels[i]
        if stream!=0:return np.tile(default,(n,1))
        dtype={0:'<f4',2:'u1'}.get(fmt)
        if not dtype:return np.tile(default,(n,1))
        a=np.ndarray((n,dim),dtype=dtype,buffer=buf,offset=offset,strides=(stride,np.dtype(dtype).itemsize)).copy()
        if fmt==2:a=a/255
        return a
    positions=get(0,(0,0,0));normals=get(1,(0,1,0));colors=get(3,(1,1,1,1));uv=get(4,(0,0))
    dtype='<u4' if 'm_IndexFormat: 1' in raw else '<u2'
    ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]*)',raw)[1]),dtype=dtype).reshape(-1,3)
    return positions,normals,colors,uv,ix


def load_mesh(key,raw,outline=False):
    cachekey=(key,outline)
    if cachekey in MESHES:return MESHES[cachekey]
    v,n,c,uv,ix=mesh_data(raw)
    if outline:v=v+n*.026
    mesh=bpy.data.meshes.new(str(key));mesh.from_pydata(v,[],ix);mesh.update()
    attr=mesh.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='POINT')
    values=np.column_stack([c[:,:3],np.ones(len(v))]).astype(np.float32)
    attr.data.foreach_set('color',values.ravel())
    layer=mesh.uv_layers.new(name='Authored UV')
    loops=np.empty(len(mesh.loops),dtype=np.int32);mesh.loops.foreach_get('vertex_index',loops)
    layer.data.foreach_set('uv',uv[loops,:2].astype(np.float32).ravel())
    for poly in mesh.polygons:poly.use_smooth=True
    MESHES[cachekey]=mesh
    return mesh


def prop(raw,key,default):
    m=re.search(r'^    - '+re.escape(key)+r': ([^\n]+)',raw,re.M)
    try:return float(m[1]) if m else default
    except ValueError:return default


def mat(name,guid=None,default=(.45,.44,.30),outline=False):
    key=(guid or name,outline)
    if key in MATERIALS:return MATERIALS[key]
    material=bpy.data.materials.new(name);material.use_nodes=True
    nodes=material.node_tree.nodes;links=material.node_tree.links
    out=nodes.get('Material Output');bs=nodes.get('Principled BSDF')
    if outline:
        nodes.remove(bs);back=nodes.new('ShaderNodeNewGeometry');trans=nodes.new('ShaderNodeBsdfTransparent');black=nodes.new('ShaderNodeEmission');black.inputs['Color'].default_value=(.012,.010,.008,1)
        mix=nodes.new('ShaderNodeMixShader');links.new(back.outputs['Backfacing'],mix.inputs[0]);links.new(trans.outputs[0],mix.inputs[1]);links.new(black.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
        MATERIALS[key]=material;return material
    raw=GUIDS[guid].read_text() if guid in GUIDS and GUIDS[guid].suffix=='.mat' else ''
    color=re.search(r'- _BaseColor: \{r: ([^,]+), g: ([^,]+), b: ([^,]+)',raw)
    base=tuple(map(float,color.groups())) if color else default
    vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='Pigment'
    mult=nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;mult.inputs[2].default_value=(*base,1)
    if prop(raw,'_VertexTint',1)>.5:links.new(vc.outputs['Color'],mult.inputs[1])
    else:mult.inputs[1].default_value=(1,1,1,1)
    col=mult.outputs[0]
    alpha=None
    base_texture=re.search(r'- _BaseMap:\n        m_Texture: .*guid: (\w+)',raw)
    if base_texture and base_texture[1] in GUIDS:
        path=GUIDS[base_texture[1]]
        if path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n':
            image=nodes.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(path),check_existing=True)
            texmult=nodes.new('ShaderNodeMixRGB');texmult.blend_type='MULTIPLY';texmult.inputs[0].default_value=1;links.new(col,texmult.inputs[1]);links.new(image.outputs['Color'],texmult.inputs[2]);col=texmult.outputs[0]
            alpha=image.outputs['Alpha']
    texture=re.search(r'- _DetailMap:\n        m_Texture: .*guid: (\w+)',raw)
    strength=prop(raw,'_ArtStrength',0)
    if texture and strength>.01 and texture[1] in GUIDS:
        path=GUIDS[texture[1]]
        if path.read_bytes()[:8]==b'\x89PNG\r\n\x1a\n':
            image=nodes.new('ShaderNodeTexImage');image.image=bpy.data.images.load(str(path),check_existing=True);image.projection='BOX';image.projection_blend=.18
            coords=nodes.new('ShaderNodeTexCoord');mapping=nodes.new('ShaderNodeVectorMath');mapping.operation='SCALE';mapping.inputs[3].default_value=prop(raw,'_ArtTiling',.6);links.new(coords.outputs['Object'],mapping.inputs[0]);links.new(mapping.outputs[0],image.inputs['Vector'])
            pale=nodes.new('ShaderNodeMixRGB');pale.blend_type='MIX';pale.inputs[0].default_value=.65;links.new(col,pale.inputs[1]);pale.inputs[2].default_value=(*base,1)
            paint=nodes.new('ShaderNodeMixRGB');paint.blend_type='MULTIPLY';paint.inputs[0].default_value=1;links.new(pale.outputs[0],paint.inputs[1]);links.new(image.outputs['Color'],paint.inputs[2])
            gain=nodes.new('ShaderNodeMixRGB');gain.blend_type='MULTIPLY';gain.inputs[0].default_value=1;gain.inputs[2].default_value=(1.35,1.35,1.35,1);links.new(paint.outputs[0],gain.inputs[1])
            mix=nodes.new('ShaderNodeMixRGB');mix.inputs[0].default_value=strength;links.new(col,mix.inputs[1]);links.new(gain.outputs[0],mix.inputs[2]);col=mix.outputs[0]
    links.new(col,bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.88
    if 'Water' in name or 'River' in name or 'Pond' in name:
        bs.inputs['Base Color'].default_value=(.10,.30,.29,1)
        for link in list(bs.inputs['Base Color'].links):links.remove(link)
        bs.inputs['Roughness'].default_value=.25
    # Legacy leaf/grass cards and inverted ink hulls need the saved material's
    # alpha/cull rules; otherwise this preview invents white cards/black spikes.
    a=re.search(r'- _BaseColor: \{[^}]+a: ([^}]+)',raw)
    opacity=float(a[1]) if a else 1.0
    cutoff=prop(raw,'_Cutoff',0)
    if alpha:
        scale=nodes.new('ShaderNodeMath');scale.operation='MULTIPLY';links.new(alpha,scale.inputs[0]);scale.inputs[1].default_value=opacity;alpha=scale.outputs[0]
        if cutoff>0:
            cut=nodes.new('ShaderNodeMath');cut.operation='GREATER_THAN';links.new(alpha,cut.inputs[0]);cut.inputs[1].default_value=cutoff;alpha=cut.outputs[0]
    elif opacity<.999:
        value=nodes.new('ShaderNodeValue');value.outputs[0].default_value=opacity;alpha=value.outputs[0]
    cull=prop(raw,'_Cull',0)
    if cull in (1,2):
        geometry=nodes.new('ShaderNodeNewGeometry');facing=geometry.outputs['Backfacing']
        if cull==2:
            invert=nodes.new('ShaderNodeMath');invert.operation='SUBTRACT';invert.inputs[0].default_value=1;links.new(facing,invert.inputs[1]);facing=invert.outputs[0]
        if alpha:
            multiply=nodes.new('ShaderNodeMath');multiply.operation='MULTIPLY';links.new(alpha,multiply.inputs[0]);links.new(facing,multiply.inputs[1]);alpha=multiply.outputs[0]
        else:alpha=facing
    if alpha:
        mix=nodes.new('ShaderNodeMixShader');trans=nodes.new('ShaderNodeBsdfTransparent');links.new(alpha,mix.inputs[0]);links.new(trans.outputs[0],mix.inputs[1]);links.new(bs.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs['Surface'])
    MATERIALS[key]=material;return material


def add_object(name,key,raw,material,matrix,outline=False):
    mesh=load_mesh(key,raw,outline)
    # A mesh can be instanced by different material slots in Unity, so a cheap
    # object data copy preserves material identity without mutating its sibling.
    if not mesh.materials:mesh.materials.append(material)
    o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.matrix_world=CONVERT@matrix
    o.material_slots[0].link='OBJECT';o.material_slots[0].material=material
    if outline:
        # Unity's unlit contour does not absorb baked/probe ambient lighting.
        # In Cycles its enclosing black backfaces would incorrectly block every
        # diffuse environment bounce, turning the real rock/cliff nearly black.
        o.visible_shadow=False;o.visible_diffuse=False;o.visible_glossy=False
        o.visible_transmission=False;o.visible_volume_scatter=False
    return o


def saved_objects():
    count=0;skipped=0
    selected={}
    def environment_hierarchy(go):
        if go in selected:return selected[go]
        name=SCENE.name(go).lower()
        keywords=['ink world','ink contour','village house','living tree','grounded stone',
                  'grass','flower','bamboo','bridge','plant','home','market','forest',
                  'groundcover','house','garden','waterside','windflower']
        if any(word in name for word in keywords):selected[go]=True;return True
        t=SCENE.transform(go)
        parent=reference(SCENE.blocks[t],'m_Father')[0] if t else 0
        parent_go=SCENE.owner(parent) if parent in SCENE.blocks else None
        selected[go]=environment_hierarchy(parent_go) if parent_go and SCENE.kind(parent_go)==1 else False
        return selected[go]
    for go in SCENE.blocks:
        if SCENE.kind(go)!=1 or not active(SCENE,go):continue
        mf=SCENE.component(go,33);r=SCENE.component(go,23)
        if not mf or not r or '  m_Enabled: 0\n' in SCENE.blocks[r]:continue
        fid,g=reference(SCENE.blocks[mf],'m_Mesh')
        if g not in GUIDS or GUIDS[g].suffix!='.asset':continue
        p=GUIDS[g]
        if p.name=='ValleyMeshes.asset':continue # resolved once through Sources below
        name=SCENE.name(go);matrix=world(SCENE,SCENE.transform(go))
        # Keep relevant active saved environment meshes; exclude imported wolf,
        # diagnostic effects and interior clutter from this layout-only review.
        # Select WHOLE environment hierarchies. Looking only at the child's name
        # used to import lantern ribs while omitting their paper bodies/strings,
        # inventing floating wire circles that are absent from the actual game.
        if not environment_hierarchy(go):continue
        match=re.search(r'  m_Materials:\n  - \{fileID: \d+, guid: (\w+)',SCENE.blocks[r])
        materialguid=match[1] if match else None
        outline=name.startswith('Ink contour')
        # scene roots may include huge old inactive preserved visuals. Limit by
        # saved object position only where meshes use local rather than world data.
        raw=p.read_text()
        if 'm_VertexCount:' not in raw:skipped+=1;continue
        add_object(name,g,raw,mat(name,materialguid,outline=outline),matrix,outline)
        count+=1
    return count,skipped


def source_objects():
    count=0
    # Active prefab source records include terrain, water, paths, remaining house
    # details and bridge walking decks. Overrides are applied to their actual mesh.
    for n,raw in SOURCES.native.items():
        if not SOURCES.visible(n):continue
        if n not in SOURCES.objects:continue
        go=SOURCES.objects[n];mf=SOURCES.prefab.component(go,33);r=SOURCES.prefab.component(go,23)
        override=OVERRIDES.get((mf,'m_Mesh'))
        key='Valley-'+str(n)
        if override:
            mm=re.search(r'guid: (\w+)',override[1])
            if mm and mm[1] in GUIDS:
                raw=GUIDS[mm[1]].read_text();key=mm[1]
        material=SOURCES.data['materials'][SOURCES.records[n]['material']]
        color=tuple(int(material['color'][i:i+2],16)/255 for i in [0,2,4])
        name='Prefab '+str(n)+' '+material.get('kind','')
        materialguid=None
        override=OVERRIDES.get((r,'m_Materials.Array.data[0]'))
        if override:
            mm=re.search(r'guid: (\w+)',override[1]);materialguid=mm[1] if mm else None
        if not materialguid:
            mm=re.search(r'  m_Materials:\n  - \{fileID: \d+, guid: (\w+)',SOURCES.prefab.blocks[r]);materialguid=mm[1] if mm else None
        add_object(name,key,raw,mat(name,materialguid,default=color),world(SOURCES.prefab,SOURCES.prefab.transform(go)))
        count+=1
    return count


def render(name,position,look,width,res=(1600,1000)):
    p=CONVERT@Vector((*position,1));target=CONVERT@Vector((*look,1))
    bpy.ops.object.camera_add(location=p.xyz);cam=bpy.context.object;cam.rotation_euler=(target.xyz-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=width;bpy.context.scene.camera=cam
    # Orthographic framing is unchanged by moving along its viewing axis. Put
    # its near plane outside the wide foreground instead of clipping into roofs.
    cam.location-=(target.xyz-cam.location).normalized()*80
    # Permanent camera-facing text is in the rendered image, not just metadata.
    text=bpy.data.curves.new('Preview limitation','FONT');text.body='BLENDER SCENE LAYOUT PREVIEW — NOT UNITY';text.size=width*.012
    obj=bpy.data.objects.new('Permanent non-Unity label',text);bpy.context.collection.objects.link(obj);obj.parent=cam
    obj.location=(-width*.48,width*res[1]/res[0]*.455,-1)
    label=mat('Preview label',outline=True);nodes=label.node_tree.nodes
    # Simple emission keeps the camera label readable independent of world light.
    label=bpy.data.materials.new('Preview label ink');label.use_nodes=True;n=label.node_tree.nodes;n.clear();e=n.new('ShaderNodeEmission');e.inputs['Color'].default_value=(.96,.88,.65,1);o=n.new('ShaderNodeOutputMaterial');label.node_tree.links.new(e.outputs[0],o.inputs[0]);text.materials.append(label)
    s=bpy.context.scene;s.render.resolution_x=res[0];s.render.resolution_y=res[1];s.render.resolution_percentage=100;s.render.image_settings.file_format='JPEG';s.render.image_settings.quality=88;s.render.filepath=str(OUT/(name+'.jpg'));bpy.ops.render.render(write_still=True)
    capture_path=OUT/'preview-metadata.json'
    captures=json.loads(capture_path.read_text()) if capture_path.exists() else {}
    captures[name+'.jpg']={'sourceSceneSha256':SCENE_SHA256,'renderer':'Blender Cycles layout approximation','unityRendered':False,'cameraUnity':list(position),'lookAtUnity':list(look),'orthographicWidthMetres':width,'resolution':list(res),'samples':s.cycles.samples,'ambient':'Explicit Blender world fill; not Unity lighting'}
    capture_path.write_text(json.dumps(captures,indent=2)+'\n')
    bpy.data.objects.remove(obj,do_unlink=True);bpy.data.objects.remove(cam,do_unlink=True)


def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    n,skipped=saved_objects();legacy=source_objects()
    bpy.ops.object.light_add(type='SUN',location=(0,-10,20));sun=bpy.context.object;sun.rotation_euler=(math.radians(24),math.radians(-25),math.radians(-30));sun.data.energy=2.0;sun.data.angle=.20
    scene=bpy.context.scene;scene.world.color=(.52,.48,.39);scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.cycles.max_bounces=5;scene.cycles.transparent_max_bounces=8
    scene.world.use_nodes=True
    background=scene.world.node_tree.nodes.get('Background')
    background.inputs['Color'].default_value=(.68,.65,.54,1)
    background.inputs['Strength'].default_value=.65
    scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=-.3
    if '--diagnose-street' in sys.argv:
        from collections import Counter
        p=CONVERT@Vector((-5,9,-22,1));target=CONVERT@Vector((3,1.6,-8,1))
        bpy.ops.object.camera_add(location=p.xyz);cam=bpy.context.object;cam.rotation_euler=(target.xyz-cam.location).to_track_quat('-Z','Y').to_euler();cam.location-=(target.xyz-cam.location).normalized()*80;bpy.context.view_layer.update()
        direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1));dg=bpy.context.evaluated_depsgraph_get();counts=Counter();examples={}
        for px in range(590,741,2):
            for py in range(380,521,2):
                origin=cam.matrix_world@Vector(((px/1280-.5)*27,(.5-py/840)*27*840/1280,-.1))
                hit,loc,normal,index,obj,matrix=scene.ray_cast(dg,origin,direction)
                if hit:
                    counts[obj.name]+=1
                    examples.setdefault(obj.name,{'pixel':[px,py],'unityPosition':[loc.x,loc.z,-loc.y]})
        (OUT/'street-ray-diagnostics.json').write_text(json.dumps({'counts':dict(counts),'examples':examples},indent=2)+'\n');return
    if '--diagnose' in sys.argv:
        p=CONVERT@Vector((-12,11,-17,1));target=CONVERT@Vector((-27,1.9,2.5,1))
        bpy.ops.object.camera_add(location=p.xyz);cam=bpy.context.object;cam.rotation_euler=(target.xyz-cam.location).to_track_quat('-Z','Y').to_euler();cam.location-=(target.xyz-cam.location).normalized()*80;bpy.context.view_layer.update()
        hits=[];direction=cam.matrix_world.to_quaternion()@Vector((0,0,-1));dg=bpy.context.evaluated_depsgraph_get()
        for px,py in [(660,955),(690,965),(715,957),(735,925),(1415,187),(970,100)]:
            origin=cam.matrix_world@Vector(((px/1600-.5)*33,(.5-py/1050)*33*1050/1600,-.1));rows=[]
            for _ in range(10):
                hit,loc,normal,index,obj,matrix=scene.ray_cast(dg,origin,direction)
                if not hit:break
                rows.append({'name':obj.name,'location':list(loc),'normal':list(normal),'frontFacing':normal.dot(direction)<0})
                origin=loc+direction*.002
            hits.append({'pixel':[px,py],'hits':rows})
        (OUT/'ray-diagnostics.json').write_text(json.dumps(hits,indent=2)+'\n');return
    if '--rock-only' in sys.argv or '--rock-no-contours' in sys.argv:
        no_contours='--rock-no-contours' in sys.argv
        if no_contours:
            for obj in bpy.context.scene.objects:
                if obj.name.startswith('Ink contour'):obj.hide_render=True
        render('rock-without-contours' if no_contours else 'rock-lighting-check',(-42,7,5),(-51,2,13),11,(800,600))
        return
    if '--street-only' not in sys.argv and '--final-roofs' not in sys.argv:
        render('west-bank-bridge-mill',(-12,11,-17),(-27,1.9,2.5),33,(1280,840))
    if '--mill-only' not in sys.argv:
        render('village-street-gables',(-5,9,-22),(3,1.6,-8),27,(1280,840))
    if '--final-roofs' in sys.argv or not any(flag in sys.argv for flag in ['--mill-only','--street-only']):
        render('village-hall-and-gables',(-18,15,4),(0,2.8,19),30,(1280,840))
    report={'source':'Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity','sourceSceneSha256':SCENE_SHA256,'unityRendered':False,'savedActiveObjects':n,'visiblePrefabMeshes':legacy,'unsupportedMeshesSkipped':skipped,'limitations':['Blender layout render, not Unity; no wolf motion, gameplay or performance verification','Pigment texture mixing approximated in Blender; Unity shaders/water/fog not reproduced','Explicit outline shells approximated with fixed .026m expansion instead of Unity pixel-space width']}
    (OUT/'layout-preview-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))


if __name__=='__main__':main()
