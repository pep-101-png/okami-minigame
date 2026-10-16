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
if coat.data.color_attributes.get('FurGeometry'):
 detail=nodes.new('ShaderNodeVertexColor');detail.layer_name='FurGeometry';channel=nodes.new('ShaderNodeSeparateColor');links.new(detail.outputs['Color'],channel.inputs['Color'])
 allowed=mathnode('MULTIPLY',allowed,mathnode('SUBTRACT',1,channel.outputs['Red']))
links.new(mathnode('MULTIPLY',paint_tex.outputs['Alpha'],allowed),ink_mix.inputs[0])
# This single template is mirrored in surface tangent space, not projected across the entire face.
size=1024;image=Image.new('RGBA',(size,size),(0,0,0,0));draw=ImageDraw.Draw(image)
def eye_pixel(u,v):return ((u+.4)/.8*size,(.4-v)/.8*size)
def shape(points,color):draw.polygon([eye_pixel(u,v) for u,v in points],fill=color)
# Fine shadow brows and curved vermilion sweeps frame a real almond opening.
def bezier(a,b,c,d):
 return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in range(2)) for t in np.linspace(0,1,48)]
brow=Image.new('RGBA',(size,size),(0,0,0,0));bd=ImageDraw.Draw(brow)
bd.line([eye_pixel(u,v) for u,v in bezier((-.17,.12),(-.07,.19),(.09,.19),(.20,.18))],fill=(78,68,57,100),width=10,joint='curve')
image.alpha_composite(brow.filter(ImageFilter.GaussianBlur(5)));draw=ImageDraw.Draw(image)
shape(bezier((-.215,-.040),(-.11,-.16),(.07,-.13),(.265,.12))+bezier((.265,.12),(.09,-.005),(-.04,-.04),(-.215,-.040)),(185,22,10,248))
shape(bezier((-.22,.025),(-.12,.19),(.09,.14),(.29,.19))+bezier((.29,.19),(.14,.11),(-.04,.12),(-.22,.025)),(185,22,10,246))
exec(compile((root/'authoring/watercolor_pigment.py').read_text(),'face-watercolor','exec'))
image=watercolor_pigment(image,531,black=False);draw=ImageDraw.Draw(image)
almond=bezier((-.174,-.030),(-.070,.103),(.060,.116),(.190,.080))+bezier((.190,.080),(.055,-.058),(-.080,-.102),(-.174,-.030))
almond=[(u,.25*u+.018+(v-.25*u-.018)*.82) for u,v in almond]
shape(almond,(35,31,26,255))
# Warm iris, a focused pupil and two restrained pigment highlights give direction.
iris=Image.new('RGBA',(size,size),(0,0,0,0));idraw=ImageDraw.Draw(iris)
def ellipse(drawer,u,v,rx,ry,color):
 drawer.ellipse([eye_pixel(u-rx,v+ry),eye_pixel(u+rx,v-ry)],fill=color)
ellipse(idraw,-.024,.014,.054,.055,(100,77,44,255))
ellipse(idraw,-.030,.015,.042,.044,(142,111,65,255))
ellipse(idraw,-.040,.018,.027,.029,(24,24,22,255))
ellipse(idraw,-.047,.040,.009,.010,(240,230,199,225))
ellipse(idraw,-.002,-.015,.005,.006,(197,166,107,160))
eye_mask=Image.new('L',(size,size),0);ImageDraw.Draw(eye_mask).polygon([eye_pixel(u,v) for u,v in almond],fill=255)
iris.putalpha(Image.fromarray(np.minimum(np.array(iris.getchannel('A')),np.array(eye_mask))))
image.alpha_composite(iris);draw=ImageDraw.Draw(image)
draw.line([eye_pixel(u,v) for u,v in bezier((-.16,-.030),(-.06,-.087),(.06,-.04),(.16,.055))],fill=(111,98,78,165),width=4,joint='curve')
image=image.filter(ImageFilter.GaussianBlur(.7));image.save(root/'authoring'/'eye-template.png');eye_image=bpy.data.images.load(str(root/'authoring'/'eye-template.png'));eye_image.pack()
bvh=BVHTree.FromPolygons([v.co.copy() for v in coat.data.vertices],[list(f.vertices) for f in coat.data.polygons]);eye_locations=[]
position_socket=geo.outputs['Position']
def dot_position(vector,offset=0):
 node=nodes.new('ShaderNodeVectorMath');node.operation='DOT_PRODUCT';links.new(position_socket,node.inputs[0]);node.inputs[1].default_value=tuple(vector)
 return mathnode('SUBTRACT',node.outputs['Value'],offset)
def overlay(tex,mask):
 current=bs.inputs['Base Color'].links[0].from_socket;blend=nodes.new('ShaderNodeMixRGB');links.new(mask,blend.inputs[0]);links.new(current,blend.inputs[1]);links.new(tex.outputs['Color'],blend.inputs[2]);links.new(blend.outputs[0],bs.inputs['Base Color'])
for sign in [-1,1]:
 hit,normal,_,_=bvh.ray_cast(Vector((sign*1.6,-3.46,4.74)),Vector((-sign,0,0)),3)
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
front=watercolor_pigment(front,712,black=False);front=front.filter(ImageFilter.GaussianBlur(.6));front.save(root/'authoring'/'forehead-template.png');front_image=bpy.data.images.load(str(root/'authoring'/'forehead-template.png'));front_image.pack()
uv=nodes.new('ShaderNodeCombineXYZ');links.new(mathnode('DIVIDE',mathnode('ADD',position.outputs['X'],.8),1.6),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('SUBTRACT',position.outputs['Z'],3.9),1.7),uv.inputs['Y'])
tex=nodes.new('ShaderNodeTexImage');tex.image=front_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0]);gate=mathnode('LESS_THAN',position.outputs['Y'],-2.50);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],gate))
face_metadata={'eyes':eye_locations,'red_excluded_ornament_faces':masked}
(root/'review'/'face-placement.json').write_text(json.dumps(face_metadata,indent=2))
(root/'public'/'face.json').write_text(json.dumps(face_metadata,indent=2))
