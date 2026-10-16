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
# The side-painted red ribbons must not bleed onto the rounded front brisket.
# Fade them toward the centre only in the lower front-neck region.
def smoothmask(value,low,high,invert=False):
    node=nodes.new('ShaderNodeMapRange');node.clamp=True;node.interpolation_type='SMOOTHSTEP';node.inputs['From Min'].default_value=low;node.inputs['From Max'].default_value=high
    node.inputs['To Min'].default_value=1 if invert else 0;node.inputs['To Max'].default_value=0 if invert else 1;links.new(value,node.inputs['Value']);return node.outputs[0]
chest_zone=mathnode('MULTIPLY',smoothmask(position.outputs['Y'],-2.12,-1.82,True),smoothmask(position.outputs['Z'],3.65,3.95,True))
normal_parts=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Normal'],normal_parts.inputs[0])
front_face=smoothmask(mathnode('MULTIPLY',normal_parts.outputs['Y'],-1),.65,.85)
allowed=mathnode('MULTIPLY',allowed,mathnode('SUBTRACT',1,mathnode('MULTIPLY',redflag,mathnode('MULTIPLY',chest_zone,front_face))))
links.new(mathnode('MULTIPLY',paint_tex.outputs['Alpha'],allowed),ink_mix.inputs[0])
links.new(ink_mix.outputs[0],bs.inputs['Base Color'])
# This single template is mirrored in surface tangent space, not projected across the entire face.
size=1024;image=Image.new('RGBA',(size,size),(0,0,0,0));draw=ImageDraw.Draw(image)
def eye_pixel(u,v):return ((u+.4)/.8*size,(.4-v)/.8*size)
def shape(points,color):draw.polygon([eye_pixel(u,v) for u,v in points],fill=color)
# Compact calligraphic eyes: expression comes from the silhouette, not an iris.
def bezier(a,b,c,d):
 return [tuple((1-t)**3*a[j]+3*(1-t)**2*t*b[j]+3*(1-t)*t*t*c[j]+t**3*d[j] for j in range(2)) for t in np.linspace(0,1,48)]
brow=Image.new('RGBA',(size,size),(0,0,0,0));bd=ImageDraw.Draw(brow)
bd.line([eye_pixel(u,v) for u,v in bezier((-.12,.10),(-.02,.14),(.08,.16),(.155,.16))],fill=(88,78,64,78),width=8,joint='curve')
image.alpha_composite(brow.filter(ImageFilter.GaussianBlur(5)));draw=ImageDraw.Draw(image)
# The lower stroke hugs the opening and ends in a rising, tapered brush flick.
shape(bezier((-.157,-.026),(-.075,-.112),(.055,-.078),(.225,.170))+bezier((.225,.170),(.065,-.012),(-.035,-.038),(-.157,-.026)),(185,22,10,255))
shape(bezier((-.150,.025),(-.065,.13),(.065,.12),(.235,.210))+bezier((.235,.210),(.080,.055),(-.025,.085),(-.150,.025)),(185,22,10,255))
shape([(.128,.117),(.235,.250),(.187,.127)],(185,22,10,240))
exec(compile((root/'authoring/watercolor_pigment.py').read_text(),'face-watercolor','exec'))
image=watercolor_pigment(image,531,black=False);draw=ImageDraw.Draw(image)
almond=bezier((-.150,-.012),(-.070,.048),(.070,.075),(.173,.061))+bezier((.173,.061),(.060,-.010),(-.055,-.039),(-.150,-.012))
shape(almond,(27,25,22,250))
shape(bezier((-.062,.022),(-.025,.043),(.018,.052),(.046,.048))+bezier((.046,.048),(.005,.039),(-.025,.027),(-.062,.022)),(142,125,95,105))
# A fine lower edge keeps the eye readable without a circular iris or catchlight.
draw.line([eye_pixel(u,v) for u,v in bezier((-.14,-.014),(-.055,-.036),(.060,-.009),(.16,.051))],fill=(91,80,62,135),width=3,joint='curve')
image=image.filter(ImageFilter.GaussianBlur(.7));image.save(root/'authoring'/'eye-template.png');eye_image=bpy.data.images.load(str(root/'authoring'/'eye-template.png'));eye_image.pack()
bvh=BVHTree.FromPolygons([v.co.copy() for v in coat.data.vertices],[list(f.vertices) for f in coat.data.polygons]);eye_locations=[]
position_socket=geo.outputs['Position']
def dot_position(vector,offset=0):
 node=nodes.new('ShaderNodeVectorMath');node.operation='DOT_PRODUCT';links.new(position_socket,node.inputs[0]);node.inputs[1].default_value=tuple(vector)
 return mathnode('SUBTRACT',node.outputs['Value'],offset)
def overlay(tex,mask):
 current=bs.inputs['Base Color'].links[0].from_socket;blend=nodes.new('ShaderNodeMixRGB');links.new(mask,blend.inputs[0]);links.new(current,blend.inputs[1]);links.new(tex.outputs['Color'],blend.inputs[2]);links.new(blend.outputs[0],bs.inputs['Base Color'])
for sign in [-1,1]:
 hit,normal,_,_=bvh.ray_cast(Vector((sign*1.6,-3.50,4.69)),Vector((-sign,0,0)),3)
 assert hit is not None,'Eye ray missed the face'
 horizontal=Vector((normal.x,normal.y,0)).normalized();tangent=Vector((0,0,1)).cross(horizontal)*sign
 uv=nodes.new('ShaderNodeCombineXYZ');u=dot_position(tangent,hit.dot(tangent));v=dot_position(Vector((0,0,1)),hit.z)
 links.new(mathnode('DIVIDE',mathnode('ADD',u,.4),.8),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('ADD',v,.4),.8),uv.inputs['Y'])
 tex=nodes.new('ShaderNodeTexImage');tex.image=eye_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0])
 depth=mathnode('ABSOLUTE',dot_position(horizontal,hit.dot(horizontal)));gate=mathnode('LESS_THAN',depth,.16);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],gate));eye_locations.append({'side':sign,'point':list(hit),'surface_normal':list(normal)})
# Central forehead seal follows the frontal face. It stays clear of the nose and ears.
front=Image.new('RGBA',(1024,1536),(0,0,0,0));fd=ImageDraw.Draw(front)
def fp(x,z):return ((x+.8)/1.6*1024,(5.6-z)/1.7*1536)
fd.ellipse([fp(-.095,5.09),fp(.095,4.84)],outline=(185,22,10,255),width=24)
fd.polygon([fp(x,z) for x,z in [(-.040,4.85),(.040,4.85),(.018,4.59),(0,4.43),(-.018,4.59)]],fill=(185,22,10,248))
fd.polygon([fp(x,z) for x,z in [(-.024,5.08),(.024,5.08),(0,5.29)]],fill=(185,22,10,248))
front=watercolor_pigment(front,712,black=False);front=front.filter(ImageFilter.GaussianBlur(.6));front.save(root/'authoring'/'forehead-template.png');front_image=bpy.data.images.load(str(root/'authoring'/'forehead-template.png'));front_image.pack()
uv=nodes.new('ShaderNodeCombineXYZ');links.new(mathnode('DIVIDE',mathnode('ADD',position.outputs['X'],.8),1.6),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('SUBTRACT',position.outputs['Z'],3.9),1.7),uv.inputs['Y'])
tex=nodes.new('ShaderNodeTexImage');tex.image=front_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0]);gate=mathnode('LESS_THAN',position.outputs['Y'],-2.50);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],gate))
# A small broad-topped nose, tapered chin and readable mouth replace the button.
nose=Image.new('RGBA',(768,768),(0,0,0,0));nd=ImageDraw.Draw(nose)
def npixel(x,z):return ((x+.24)/.48*768,(4.58-z)/.48*768)
nd.polygon([npixel(x,z) for x,z in [(-.090,4.405),(-.052,4.426),(.055,4.426),(.091,4.405),(.074,4.338),(0,4.298),(-.073,4.338)]],fill=(28,26,22,255))
nd.line([npixel(x,z) for x,z in [(-.055,4.402),(-.015,4.413),(.035,4.410)]],fill=(88,79,65,125),width=5,joint='curve')
nd.line([npixel(x,z) for x,z in [(0,4.303),(0,4.267)]],fill=(45,40,32,220),width=6)
nd.line([npixel(x,z) for x,z in [(-.070,4.250),(0,4.267),(.070,4.250)]],fill=(61,53,41,180),width=4,joint='curve')
nose=nose.filter(ImageFilter.GaussianBlur(1.1));nose.save(root/'authoring/nose-template.png')
nose_image=bpy.data.images.load(str(root/'authoring/nose-template.png'));nose_image.pack()
uv=nodes.new('ShaderNodeCombineXYZ');links.new(mathnode('DIVIDE',mathnode('ADD',position.outputs['X'],.24),.48),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('SUBTRACT',position.outputs['Z'],4.10),.48),uv.inputs['Y'])
tex=nodes.new('ShaderNodeTexImage');tex.image=nose_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0]);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],mathnode('LESS_THAN',position.outputs['Y'],-4.02)))
mouth=Image.new('RGBA',(2048,1024),(0,0,0,0));md=ImageDraw.Draw(mouth)
def mp(y,z):return ((y+4.50)/1.40*2048,(4.60-z)/.80*1024)
path=bezier((-4.245,4.267),(-4.06,4.222),(-3.86,4.238),(-3.68,4.260))
left=[];right=[]
for i,(y,z) in enumerate(path):
 w=.003+.008*math.sin(math.pi*i/(len(path)-1))**.8
 left.append(mp(y,z+w));right.append(mp(y,z-w))
md.polygon(left+right[::-1],fill=(61,53,41,205))
mouth=mouth.filter(ImageFilter.GaussianBlur(.9));mouth.save(root/'authoring/mouth-template.png');mouth_image=bpy.data.images.load(str(root/'authoring/mouth-template.png'));mouth_image.pack()
uv=nodes.new('ShaderNodeCombineXYZ');links.new(mathnode('DIVIDE',mathnode('ADD',position.outputs['Y'],4.50),1.40),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('SUBTRACT',position.outputs['Z'],3.80),.80),uv.inputs['Y'])
tex=nodes.new('ShaderNodeTexImage');tex.image=mouth_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0]);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],mathnode('GREATER_THAN',mathnode('ABSOLUTE',position.outputs['X']),.008)))
# Dilute tapered fur strokes describe the small chest tuft and rounded underside.
chest=Image.new('RGBA',(1024,1024),(0,0,0,0));cd=ImageDraw.Draw(chest)
def cp(x,z):return ((x+.8)/1.6*1024,(3.40-z)/1.10*1024)
for x,z,length,lean in [(-.34,2.88,.15,.075),(-.23,2.82,.17,.08),(-.10,2.77,.15,.045),(.04,2.74,.16,-.015),(.19,2.80,.15,-.06),(.32,2.88,.13,-.065)]:
    points=bezier((x,z),(x+lean*.2,z-length*.35),(x+lean*.8,z-length*.72),(x+lean,z-length))
    widths=np.sin(np.linspace(0,math.pi,len(points)))**.65*.008
    cd.polygon([cp(a-w,b) for (a,b),w in zip(points,widths)]+[cp(a+w,b) for (a,b),w in zip(points[::-1],widths[::-1])],fill=(70,65,51,145))
chest=chest.filter(ImageFilter.GaussianBlur(1.0));chest.save(root/'authoring/chest-template.png');chest_image=bpy.data.images.load(str(root/'authoring/chest-template.png'));chest_image.pack()
uv=nodes.new('ShaderNodeCombineXYZ');links.new(mathnode('DIVIDE',mathnode('ADD',position.outputs['X'],.8),1.6),uv.inputs['X']);links.new(mathnode('DIVIDE',mathnode('SUBTRACT',position.outputs['Z'],2.30),1.10),uv.inputs['Y'])
tex=nodes.new('ShaderNodeTexImage');tex.image=chest_image;tex.extension='CLIP';links.new(uv.outputs[0],tex.inputs[0]);gate=mathnode('LESS_THAN',position.outputs['Y'],-1.95);overlay(tex,mathnode('MULTIPLY',tex.outputs['Alpha'],gate))
face_metadata={'eyes':eye_locations,'red_excluded_ornament_faces':masked}
(root/'review'/'face-placement.json').write_text(json.dumps(face_metadata,indent=2))
(root/'public'/'face.json').write_text(json.dumps(face_metadata,indent=2))
