"""Ivory pigment with a gentle height wash; lighting supplies the form shadows.

Do not bake face-normal shading into the paint. That records polygon edges and
rest-pose shadows which become conspicuous when the fur bends.
"""
fur=bpy.data.materials.new('Ivory pigment - soft warm and cool wash');fur.use_nodes=True
nodes=fur.node_tree.nodes;links=fur.node_tree.links;bs=nodes.get('Principled BSDF')
bs.inputs['Roughness'].default_value=.88;bs.inputs['Specular IOR Level'].default_value=.22
geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],sep.inputs[0])
height=nodes.new('ShaderNodeMath');height.operation='MULTIPLY';height.inputs[1].default_value=1/5.6;links.new(sep.outputs['Z'],height.inputs[0])
ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE';links.new(height.outputs[0],ramp.inputs[0]);ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for i,(position,color) in enumerate([(0,(.60,.67,.71,1)),(.28,(.78,.83,.84,1)),(.58,(.92,.93,.89,1)),(1,(1,.97,.87,1))]):
    element=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(position);element.position=position;element.color=color
tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3.5;tex.inputs['Detail'].default_value=3;links.new(geo.outputs['Position'],tex.inputs['Vector'])
variation=nodes.new('ShaderNodeValToRGB');variation.color_ramp.elements[0].color=(.91,.93,.95,1);variation.color_ramp.elements[1].color=(1,1,.98,1);links.new(tex.outputs['Fac'],variation.inputs[0])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.18;links.new(ramp.outputs[0],mix.inputs[1]);links.new(variation.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(28,4,70);links.new(geo.outputs['Position'],scale.inputs[0])
grain=nodes.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=1;grain.inputs['Detail'].default_value=2;links.new(scale.outputs[0],grain.inputs[0])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.22;bump.inputs['Distance'].default_value=.016;links.new(grain.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
# Fine directional fibres and pigment breaks remain visible in the colour map.
fibre=nodes.new('ShaderNodeValToRGB');fibre.color_ramp.elements[0].color=(.72,.77,.80,1);fibre.color_ramp.elements[1].color=(1,.99,.95,1);links.new(grain.outputs['Fac'],fibre.inputs[0])
body_mix=mix;mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.30;links.new(body_mix.outputs[0],mix.inputs[1]);links.new(fibre.outputs[0],mix.inputs[2])
if coat.data.color_attributes.get('FurWash'):
    strand_wash=nodes.new('ShaderNodeVertexColor');strand_wash.layer_name='FurWash';base_mix=mix;mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.8;links.new(base_mix.outputs[0],mix.inputs[1]);links.new(strand_wash.outputs['Color'],mix.inputs[2])
links.new(mix.outputs[0],bs.inputs['Base Color'])
for obj in meshes:
    obj.data.materials.clear();obj.data.materials.append(fur)
    for face in obj.data.polygons:face.use_smooth=True
