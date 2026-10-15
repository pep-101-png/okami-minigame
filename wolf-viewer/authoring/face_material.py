"""Fit paired ink eyes to real cheek surfaces, with soft brows and wrapping red ink."""
from PIL import Image,ImageDraw,ImageFilter
from mathutils.bvhtree import BVHTree
# A vertex mask prevents red ink from being projected onto the shoulder ornaments.
attr=coat.data.color_attributes.new(name='BodyInkOnly',type='FLOAT_COLOR',domain='CORNER')
masked=0
for face in coat.data.polygons:
 points=[coat.data.vertices[i] for i in face.vertices];center=face.center
 ornament=-1.95<center.y<-.42 and center.z>3.32 and max(abs(v.co.x) for v in points)>.76 and any(sum(g.weight for g in v.groups if coat.vertex_groups[g.group].name.startswith('shoulderFur'))>.025 for v in points)
 for index in face.loop_indices:attr.data[index].color=(0,0,0,1) if ornament else (1,1,1,1)
 masked+=int(ornament)
vertex_color=nodes.new('ShaderNodeVertexColor');vertex_color.layer_name=attr.name;parts=nodes.new('ShaderNodeSeparateColor');links.new(vertex_color.outputs['Color'],parts.inputs['Color'])
def mathnode(operation,left,right=None):
 node=nodes.new('ShaderNodeMath');node.operation=operation
 for i,value in enumerate([left,right]):
  if value is None:continue
  if isinstance(value,(float,int)):node.inputs[i].default_value=value
  else:links.new(value,node.inputs[i])
 return node.outputs[0]
colors=nodes.new('ShaderNodeSeparateColor');links.new(paint_tex.outputs['Color'],colors.inputs['Color'])
redflag=mathnode('MULTIPLY',mathnode('GREATER_THAN',colors.outputs['Red'],.18),mathnode('LESS_THAN',colors.outputs['Green'],.08))
allowed=mathnode('SUBTRACT',1,mathnode('MULTIPLY',redflag,mathnode('SUBTRACT',1,parts.outputs['Red'])))
links.new(mathnode('MULTIPLY',paint_tex.outputs['Alpha'],allowed),ink_mix.inputs[0])
# This single template is mirrored in surface tangent space, not projected across the entire face.
size=1024;image=Image.new('RGBA',(size,size),(0,0,0,0));draw=ImageDraw.Draw(image)
def eye_pixel(u,v):return ((u+.4)/.8*size,(.4-v)/.8*size)
def shape(points,color):draw.polygon([eye_pixel(u,v) for u,v in points],fill=color)
# Minor grey brows, softened separately so they read as shadow rather than black bars.
brow=Image.new('RGBA',(size,size),(0,0,0,0));bd=ImageDraw.Draw(brow);bd.line([eye_pixel(u,v) for u,v in [(-.16,.105),(-.07,.155),(.08,.180),(.18,.175)]],fill=(69,61,53,110),width=13,joint='curve');image.alpha_composite(brow.filter(ImageFilter.GaussianBlur(4)));draw=ImageDraw.Draw(image)
shape([(-.23,-.047),(-.09,-.11),(.09,-.03),(.255,.115),(.15,-.10),(-.045,-.165)],(185,22,10,247))
shape([(-.21,.023),(-.115,.105),(.045,.145),(.29,.175),(.18,.105),(.02,.095)],(185,22,10,246))
shape([(-.173,-.035),(-.095,.020),(.045,.068),(.180,.078),(.105,.010),(-.025,-.045)],(19,17,14,255))
image=image.filter(ImageFilter.GaussianBlur(.7));image.save(root/'authoring'/'eye-template.png');eye_image=bpy.data.images.load(str(root/'authoring'/'eye-template.png'));eye_image.pack()
bvh=BVHTree.FromPolygons([v.co.copy() for v in coat.data.vertices],[list(f.vertices) for f in coat.data.polygons]);eye_locations=[]
position_socket=geo.outputs['Position']
def dot_position(vector,offset=0):
 node=nodes.new('ShaderNodeVectorMath');node.operation='DOT_PRODUCT';links.new(position_socket,node.inputs[0]);node.inputs[1].default_value=tuple(vector)
 return mathnode('SUBTRACT',node.outputs['Value'],offset)
def overlay(tex,mask):
 current=bs.inputs['Base Color'].links[0].from_socket;blend=nodes.new('ShaderNodeMixRGB');links.new(mask,blend.inputs[0]);links.new(current,blend.inputs[1]);links.new(tex.outputs['Color'],blend.inputs[2]);links.new(blend.outputs[0],bs.inputs['Base Color'])
for sign in [-1,1]:
 hit,normal,_,_=bvh.ray_cast(Vector((sign*1.6,-3.36,4.70)),Vector((-sign,0,0)),3)
 assert hit is not None,'Eye ray missed the face'
 horizontal=Vector((normal.x,normal.y,0)).normalized();tangent=Vector((0,0,1)).cross(horizontal)*sign
 uv=nodes.new('ShaderNodeCombineXYZ');u=dot_position(tangent,hit.dot(tangent));v=dot_position(Vector((0,0,1)),hit.z)
 links.new(mathnode('DIVIDE',mathnode('ADD',u,.4),.8),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('ADD',v,.4),.8),uv.inputs['Y'])
 tex=nodes.new('ShaderNodeTexImage');tex.image=eye_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0])
 depth=mathnode('ABSOLUTE',dot_position(horizontal,hit.dot(horizontal)));gate=mathnode('LESS_THAN',depth,.16);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],gate));eye_locations.append({'side':sign,'point':list(hit),'surface_normal':list(normal)})
# Central forehead seal follows the frontal face. It stays clear of the nose and ears.
front=Image.new('RGBA',(1024,1536),(0,0,0,0));fd=ImageDraw.Draw(front)
def fp(x,z):return ((x+.8)/1.6*1024,(5.6-z)/1.7*1536)
fd.ellipse([fp(-.075,5.06),fp(.075,4.84)],outline=(185,22,10,248),width=14)
fd.polygon([fp(x,z) for x,z in [(-.055,4.84),(.055,4.84),(0,4.65)]],fill=(185,22,10,248))
fd.polygon([fp(x,z) for x,z in [(-.025,5.06),(.025,5.06),(0,5.18)]],fill=(185,22,10,248))
front=front.filter(ImageFilter.GaussianBlur(.8));front.save(root/'authoring'/'forehead-template.png');front_image=bpy.data.images.load(str(root/'authoring'/'forehead-template.png'));front_image.pack()
uv=nodes.new('ShaderNodeCombineXYZ');links.new(mathnode('DIVIDE',mathnode('ADD',position.outputs['X'],.8),1.6),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('SUBTRACT',position.outputs['Z'],3.9),1.7),uv.inputs['Y'])
tex=nodes.new('ShaderNodeTexImage');tex.image=front_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0]);gate=mathnode('LESS_THAN',position.outputs['Y'],-2.50);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],gate))
(root/'review'/'face-placement.json').write_text(json.dumps({'eyes':eye_locations,'red_excluded_ornament_faces':masked},indent=2))
