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
for i,(position,color) in enumerate([(0,(.75,.79,.81,1)),(.28,(.86,.89,.88,1)),(.58,(.97,.96,.91,1)),(1,(1,.99,.95,1))]):
    element=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(position);element.position=position;element.color=color
tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3.5;tex.inputs['Detail'].default_value=3;links.new(geo.outputs['Position'],tex.inputs['Vector'])
variation=nodes.new('ShaderNodeValToRGB');variation.color_ramp.elements[0].color=(.91,.93,.95,1);variation.color_ramp.elements[1].color=(1,1,.98,1);links.new(tex.outputs['Fac'],variation.inputs[0])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.18;links.new(ramp.outputs[0],mix.inputs[1]);links.new(variation.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(28,4,70);links.new(geo.outputs['Position'],scale.inputs[0])
grain=nodes.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=1;grain.inputs['Detail'].default_value=2;links.new(scale.outputs[0],grain.inputs[0])
bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.1;bump.inputs['Distance'].default_value=.008;links.new(grain.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
for obj in meshes:
    obj.data.materials.clear();obj.data.materials.append(fur)
    for face in obj.data.polygons:face.use_smooth=True
