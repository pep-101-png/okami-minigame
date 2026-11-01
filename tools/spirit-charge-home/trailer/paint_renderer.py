"""Blender diagnostics of the actual saved scene and exported native poses.

Never call these Unity screenshots, gameplay recordings or compilation evidence.
"""
from pathlib import Path
import bpy,json,math,re,struct,sys,os
import numpy as np
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[3];A=ROOT/'Sunward-Unity/Assets';OUT=Path(os.environ.get('SUNWARD_PREVIEW_OUTPUT',str(Path(__file__).with_name('previews'))));OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref,vec
sys.path.insert(0,str(Path(__file__).parent));from asset_geometry import skin
CONVERT=Matrix(((1,0,0,0),(0,0,-1,0),(0,1,0,0),(0,0,0,1)))
MATERIALS={}
def texture_material(path,two_sided=False):
    key=str(path)+str(two_sided)
    if key in MATERIALS:return MATERIALS[key]
    m=bpy.data.materials.new(path.stem);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.new('ShaderNodeEmission')
    # Native paint is intrinsically lit (minimum 82% in the Unity port). A PBR
    # shader makes inverted ink shells occlude every light ray and invents black
    # houses/people. Use flat paint for these explicitly non-Unity diagnostics.
    tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(path),check_existing=True);vertex=n.new('ShaderNodeVertexColor');vertex.layer_name='Original pigment';mul=n.new('ShaderNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;l.new(tex.outputs['Color'],mul.inputs[1]);l.new(vertex.outputs['Color'],mul.inputs[2]);l.new(mul.outputs[0],bs.inputs['Color']);trans=n.new('ShaderNodeBsdfTransparent');geo=n.new('ShaderNodeNewGeometry');alpha=n.new('ShaderNodeMath');alpha.operation='LESS_THAN';alpha.inputs[1].default_value=.3;l.new(tex.outputs['Alpha'],alpha.inputs[0]);hide=n.new('ShaderNodeMath');hide.operation='MAXIMUM';l.new(alpha.outputs[0],hide.inputs[0]);
    if not two_sided:l.new(geo.outputs['Backfacing'],hide.inputs[1])
    mix=n.new('ShaderNodeMixShader');l.new(hide.outputs[0],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);MATERIALS[key]=m;return m
def material(g,w):
    path=w.assets.get(g);raw=path.read_text() if path else '';tex=re.search(r'- (?:_MainTex|_FlowMap|_OriginalPaint):\n        m_Texture:.*guid: (\w+)',raw)
    if tex and tex[1] in w.assets:
        shader=w.assets.get(ref(raw,'m_Shader')[1]);two_sided=shader and 'Cull Off' in shader.read_text()
        return texture_material(w.assets[tex[1]],bool(two_sided))
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
