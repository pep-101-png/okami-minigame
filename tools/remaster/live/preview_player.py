"""Blender-only diagnostic of the exact exported Unity pose banks. NOT UNITY."""
import bpy,json,struct,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[3];RES=ROOT/'Sunward-Unity/Assets/OkamiRemaster/Player/Resources/NativePlayer';OUT=Path(__file__).with_name('previews');OUT.mkdir(exist_ok=True)
scene=bpy.context.scene;bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=False;scene.render.resolution_x=1100;scene.render.resolution_y=420;scene.render.resolution_percentage=100;scene.world.color=(.5,.5,.5);scene.view_settings.view_transform='Standard'
bpy.ops.object.camera_add();camera=bpy.context.object;camera.data.type='ORTHO';scene.camera=camera
materials={}
def read_bank(path):
    data=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',data);off=16;clips={}
    assert magic==b'OPB1' and version==1
    for i in range(count):
        n=struct.unpack_from('<I',data,off)[0];off+=4;name=data[off:off+n].decode();off+=n
        frames,duration,loop=struct.unpack_from('<IfI',data,off);off+=12
        a=np.frombuffer(data,'<f4',frames*bones*10,off).reshape(frames,bones,10).copy();off+=a.nbytes;clips[name]=a
    assert off==len(data);return clips
def skin(model,pose):
    n=len(model['bones'])+1;matrices=[];bind=np.zeros((n,3))
    for i in range(n):
        p,q,s=pose[i,:3],pose[i,3:7],pose[i,7:]
        matrix=np.eye(4);matrix[:3,:3]=np.array(Quaternion((float(q[3]),*map(float,q[:3]))).to_matrix())@np.diag(s);matrix[:3,3]=p
        if i:
            parent=model['bones'][i-1]['parent']+1;matrix=matrices[parent]@matrix
            bind[i]=bind[parent]+np.array(model['bones'][i-1]['position'])
        matrices.append(matrix)
    matrices=np.array(matrices);result=[]
    for part in model['parts']:
        vertex=np.array(part['positions']).reshape(-1,3);indices=np.array(part['boneIndices']).reshape(-1,3)+1;weights=np.array(part['weights']).reshape(-1,3);weights/=weights.sum(axis=1,keepdims=True);posed=np.zeros_like(vertex)
        for j in range(3):posed+=weights[:,j,None]*(np.einsum('nij,nj->ni',matrices[indices[:,j],:3,:3],vertex-bind[indices[:,j]])+matrices[indices[:,j],:3,3])
        result.append(posed)
    return result
def material(name,texture):
    key=(name,texture)
    if key in materials:return materials[key]
    mat=bpy.data.materials.new(name+str(texture));mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
    tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(RES/name/('Texture-'+str(texture)+'.png')),check_existing=True)
    em=nodes.new('ShaderNodeEmission');links.new(tex.outputs['Color'],em.inputs['Color']);transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
    # Match Unity's alpha clipping and backface culling, including original
    # inward-wound, expanded ink shells. Never turn them into solid black bodies.
    geo=nodes.new('ShaderNodeNewGeometry');alpha=nodes.new('ShaderNodeMath');alpha.operation='LESS_THAN';alpha.inputs[1].default_value=.3;links.new(tex.outputs['Alpha'],alpha.inputs[0]);maximum=nodes.new('ShaderNodeMath');maximum.operation='MAXIMUM';links.new(alpha.outputs[0],maximum.inputs[0]);links.new(geo.outputs['Backfacing'],maximum.inputs[1]);links.new(maximum.outputs[0],mix.inputs[0]);links.new(em.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);out=nodes.new('ShaderNodeOutputMaterial');links.new(mix.outputs[0],out.inputs['Surface']);materials[key]=mat;return mat
selections=[('pl00','pl00_000','idle'),('pl00','pl00_010','walk'),('pl00','pl00_011','run'),('pl00','pl00_012','sprint'),('pl00','pl00_021','jump'),('pl00','pl00_02d','landing'),('pl00','pl00_019','dodge'),('pl00','pl00_501','reflector-combat'),('wp24','wp24_000','solar-native-flames')]
models={name:json.loads((RES/name/'Model.json').read_text()) for name in ['pl00','wp24']};banks={name:read_bank(RES/name/'Poses.bytes') for name in models};receipts=[]
for name,clip,label in selections:
    model=models[name];poses=banks[name][clip];objects=[];points=[]
    direction=Vector((7,-2.3,2.0)) if name=='pl00' else Vector((-7,-2.3,2.0))
    right=Vector((-direction.y,direction.x,0)).normalized()
    for k,phase in enumerate([.05,.38,.75]):
        verts=skin(model,poses[round(phase*(len(poses)-1))])
        for i,(part,v) in enumerate(zip(model['parts'],verts)):
            xyz=np.c_[v[:,0],-v[:,2],v[:,1]]+np.asarray(right)*(k-1)*3.1;mesh=bpy.data.meshes.new(part['name']);mesh.from_pydata(xyz.tolist(),[],np.array(part['indices']).reshape(-1,3).tolist());mesh.update();ob=bpy.data.objects.new(part['name'],mesh);bpy.context.collection.objects.link(ob);objects.append(ob);uv=mesh.uv_layers.new();source=np.array(part['uv']).reshape(-1,2)
            for loop in mesh.loops:uv.data[loop.index].uv=source[loop.vertex_index]
            mesh.materials.append(material(name,part['texture']));points.extend(xyz.tolist())
    lo=np.min(points,axis=0);hi=np.max(points,axis=0);center=Vector((lo+hi)/2);camera.location=center+direction;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler()
    rotation=camera.rotation_euler.to_matrix();right=np.asarray(rotation@Vector((1,0,0)));up=np.asarray(rotation@Vector((0,1,0)));projected=np.c_[np.asarray(points)@right,np.asarray(points)@up];a=projected.min(axis=0);b=projected.max(axis=0);mid=(a+b)/2
    center+=Vector(right*(mid[0]-np.dot(center,right))+up*(mid[1]-np.dot(center,up)));camera.location=center+direction
    camera.data.ortho_scale=max(b[0]-a[0],(b[1]-a[1])*scene.render.resolution_x/scene.render.resolution_y)*1.12
    scene.render.filepath=str(OUT/('native-'+label+'.png'));bpy.ops.render.render(write_still=True)
    receipts.append(dict(label=label,source=clip,preview='native-'+label+'.png',bounds=[lo.tolist(),hi.tolist()],Unity=False))
    for ob in objects:bpy.data.objects.remove(ob,do_unlink=True)
(OUT/'native-preview-metadata.json').write_text(json.dumps(receipts,indent=2)+'\n')
