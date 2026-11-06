"""Standalone native-asset cinematic renderer. No Unity game files are edited.
All geometry/paint/poses are read from the saved project. Camera/effect timing is
cinematic choreography, not a recording of Unity gameplay or game physics.
"""
from pathlib import Path
import os,sys,json,struct,math,re,time
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami'
sys.path[:0]=['/workspace/work/trailer30/deps',str(ROOT/'tools/spirit-charge-home/trailer')]
os.environ.setdefault('LP_NUM_THREADS','2')
os.environ.setdefault('MESA_SHADER_CACHE_DIR','/workspace/work/trailer30/mesa-cache')
import moderngl
from scene_data import World,ref,vec,rotation

def normalize(a):return np.asarray(a)/max(1e-9,np.linalg.norm(a))
def matrix(p=(0,0,0),yaw=0,scale=1):
 a=math.radians(yaw);m=np.eye(4);m[:3,:3]=np.array([[math.cos(a),0,math.sin(a)],[0,1,0],[-math.sin(a),0,math.cos(a)]])*scale;m[:3,3]=p;return m

def camera_matrix(eye,target,aspect,fov=50):
 f=normalize(np.asarray(target)-eye);r=normalize(np.cross(f,[0,1,0]));up=np.cross(r,f);v=np.eye(4);v[:3,:3]=[r,up,-f];v[:3,3]=-v[:3,:3]@eye;s=1/math.tan(math.radians(fov)/2);p=np.zeros((4,4));p[0,0]=s/aspect;p[1,1]=s;p[2,2]=-(500+.08)/(500-.08);p[2,3]=-2*500*.08/(500-.08);p[3,2]=-1;return p@v,r,up

def pose_bank(path):
 b=path.read_bytes();check=b[:4];assert check==b'OPB1',path;_,_,bones,n=struct.unpack_from('<4sIII',b);off=16;out={}
 for _ in range(n):
  ln=struct.unpack_from('<I',b,off)[0];off+=4;name=b[off:off+ln].decode();off+=ln;frames,duration,loop=struct.unpack_from('<IfI',b,off);off+=12;v=np.frombuffer(b,'<f4',frames*bones*10,off).reshape(frames,bones,10).copy();off+=v.nbytes;out[name]=(v,duration,loop)
 return out
VERT='''#version 330
in vec3 in_pos;in vec2 in_uv;in vec4 in_color;in vec3 in_ids;in vec3 in_weight;
uniform mat4 vp,root,bones[128];uniform bool skinned;
out vec2 uv;out vec4 pigment;out vec3 world;
void main(){vec4 p=vec4(in_pos,1);if(skinned){p=vec4(0);for(int k=0;k<3;k++)p+=bones[int(in_ids[k])]*vec4(in_pos,1)*in_weight[k];}p=root*p;world=p.xyz;uv=in_uv;pigment=in_color;gl_Position=vp*p;}
'''
FRAG='''#version 330
in vec2 uv;in vec4 pigment;in vec3 world;out vec4 out_color;
uniform sampler2D paint,grass,earth,layoutMask;uniform int mode;uniform float clock,night,realm,opacity;uniform vec3 cameraPos,tint;
float raw(float z){return 1.1*sin(z*.13)+.45*sin(z*.31)+2*exp(-pow((z+8)/4,2));}
float riverX(float z){float c=exp(-pow(26./4,2)),a=(raw(12)-raw(-14)*c)/(1-c*c),b=raw(-14)-a*c;return -23+raw(z)-a*exp(-pow((z-12)/4,2))-b*exp(-pow((z+14)/4,2));}
void main(){vec4 c=texture(paint,uv);if(mode==1){vec2 p=world.xz;vec2 q=vec2(p.x*.9397-p.y*.342,p.x*.342+p.y*.9397);vec3 g=mix(texture(grass,p*.035).rgb,texture(grass,q*(.035*.73)+vec2(.31,.57)).rgb,.35);vec2 m=texture(layoutMask,clamp((p+vec2(60,48))/vec2(130,96),0,1)).rg;c=vec4(mix(g,texture(earth,p*.05).rgb,max(m.r,m.g)),1);}
if(mode==2){float z=-world.z,cx=riverX(z),w=2.45+.4*sin(z*.17+.4)+.25*cos(z*.31);if(world.z>36.02||abs(world.x-cx)>w*1.1)discard;vec2 f=vec2((world.x-cx)/(2*w)+.5,z*.052-clock*.026);c=texture(paint,f);c.rgb=mix(c.rgb,vec3(.18,.45,.48),.35);c.a=.86;}
if(mode==3){c=texture(paint,vec2(world.x/180.+.5,.5-world.z/180.));}
if(mode==4){c=texture(paint,uv+vec2(0,clock*.17));c.a*=.7;}
if(c.a<.22)discard;
if(mode!=1&&mode!=2&&mode!=3&&mode!=4)c.rgb*=pigment.rgb;
if(mode==7){float q=dot(c.rgb,vec3(.333));c.rgb=mix(vec3(.94,.91,1),vec3(.72,.77,.89),clamp((1-q)*.8,0,1));c.a=.85;}if(mode==5){out_color=vec4(c.rgb*tint,c.a*opacity);return;}
vec3 light=vec3(.97);if(realm<.5){vec3 warm=vec3(0);for(int i=0;i<6;i++){float z=-11.+float(i)*4.2;float d=distance(world,vec3(0,3.7,z));warm+=vec3(.85,.42,.16)*pow(max(0,1-d/8.),2);};light=mix(light,vec3(.36,.43,.62)+warm,night);}else if(realm>1.5)light=vec3(.81,.62,.53);c.rgb*=light*tint;
float fog=clamp((distance(cameraPos,world)-60.)/160.,0,.7);vec3 fogColor=realm>.5?vec3(.88,.86,.91):mix(vec3(.73,.78,.76),vec3(.07,.10,.19),night);out_color=vec4(mix(c.rgb,fogColor,fog),c.a*opacity);}
'''
class Draw:
 def __init__(self,renderer,vertices,indices,uv,colors,texture,root=None,mode=0,ids=None,weights=None,realm='village',twosided=False):
  self.r=renderer;self.image_path=texture;self.vis_source=None;self.root=np.eye(4) if root is None else root;self.mode=mode;self.realm=realm;self.twosided=twosided;self.visible=True;self.tint=(1,1,1);self.opacity=1
  self.vertices=np.asarray(vertices);self.indices=np.asarray(indices);n=len(vertices);ids=np.zeros((n,3)) if ids is None else ids;weights=np.tile([1,0,0],(n,1)) if weights is None else weights
  self.vbo=renderer.ctx.buffer(np.column_stack([vertices,uv,colors,ids,weights]).astype('f4').tobytes());self.ibo=renderer.ctx.buffer(np.asarray(indices,dtype='u4').ravel().tobytes());self.vao=renderer.ctx.vertex_array(renderer.program,[(self.vbo,'3f 2f 4f 3f 3f','in_pos','in_uv','in_color','in_ids','in_weight')],self.ibo);self.texture=renderer.texture(texture)
 def render(self):
  if not self.visible or (self.vis_source is not None and not self.vis_source.visible):return
  r=self.r;p=r.program;p['root'].write(np.asarray(self.root.T,dtype='f4').tobytes());p['mode'].value=self.mode;p['tint'].value=self.tint;p['opacity'].value=self.opacity;self.texture.use(0)
  if self.twosided:r.ctx.disable(moderngl.CULL_FACE)
  else:r.ctx.enable(moderngl.CULL_FACE)
  self.vao.render()
class Native:
 def __init__(self,r,resource,scale=1,offset=(0,0,0),realm='village'):
  self.r=r;self.resource=resource;self.folder=next(p/resource for p in A.rglob('Resources') if (p/resource/'Model.json').exists());self.model=json.loads((self.folder/'Model.json').read_text());self.bank=pose_bank(self.folder/'Poses.bytes');self.scale=scale;self.offset=np.asarray(offset);self.parts=[];self.visible=False;self.root=np.eye(4);bind=[np.zeros(3)]
  for b in self.model['bones']:bind.append(bind[b['parent']+1]+np.asarray(b['position']))
  self.bind=np.asarray(bind);self.transforms=np.tile(np.eye(4),(128,1,1));self.skinmat=np.tile(np.eye(4),(128,1,1));self.pose_data=None
  for part in self.model['parts']:
   group=int(part['name'].split('-')[1]);tx=next(t for t in self.model['textures'] if t['index']==part['texture']);texture=None if tx.get('vertexOnly') else self.folder/tx['path'];v=np.array(part['positions']).reshape(-1,3);ids=np.array(part['boneIndices']).reshape(-1,3)+1;weights=np.array(part['weights']).reshape(-1,3);weights/=np.maximum(weights.sum(1,keepdims=True),1e-9);ob=Draw(r,v,np.array(part['indices']).reshape(-1,3),np.array(part['uv']).reshape(-1,2),np.array(part['colors']).reshape(-1,4),texture,realm=realm,ids=ids,weights=weights);self.parts.append((group,ob));r.dynamic.append(ob)
  self.groups=set(self.model.get('visibleGroups') or [g for g,_ in self.parts])
 def pose(self,clip,t,loop=True):
  if clip not in self.bank:raise ValueError(self.resource+' lacks '+clip)
  data,duration,_=self.bank[clip];x=((t%duration)/duration if loop else np.clip(t/duration,0,1))*(len(data)-1);i=int(x);j=min(i+1,len(data)-1);u=x-i;a=data[i];b=data[j];v=a*(1-u)+b*u;q1=a[:,3:7];q2=b[:,3:7].copy();q2[np.sum(q1*q2,axis=1)<0]*=-1;q=q1*(1-u)+q2*u;v[:,3:7]=q/np.maximum(np.linalg.norm(q,axis=1,keepdims=True),1e-9);return v
 def update(self,clip,t,root=None,loop=True,pose=None):
  if root is not None:self.root=root
  p=self.pose(clip,t,loop) if pose is None else pose;self.pose_data=p
  for i,v in enumerate(p):
   m=np.eye(4);m[:3,:3]=rotation(v[3:7])@np.diag(v[7:]);m[:3,3]=v[:3];parent=self.model['bones'][i-1]['parent']+1 if i else -1;self.transforms[i]=m if parent<0 else self.transforms[parent]@m;self.skinmat[i]=self.transforms[i];self.skinmat[i,:3,3]-=self.transforms[i,:3,:3]@self.bind[i]
  return p
 def draw(self):
  if not self.visible:return
  r=self.r;p=r.program;p['skinned'].value=True;p['bones'].write(self.skinmat.transpose(0,2,1).astype('f4').tobytes());off=matrix(self.offset);off[:3,:3]*=self.scale
  for group,ob in self.parts:
   if group not in self.groups:continue
   ob.root=self.root@off;ob.render()
 def anatomical_dorsal(self):
  m=self.transforms[1].copy();m[:3,3]+=m[:3,:3]@(self.bind[31]-self.bind[1]);u,_,v=np.linalg.svd(m[:3,:3]);m[:3,:3]=u@v;return self.root@m
 def dorsal(self):
  # The game's dorsal helper removes squash/scale from PL bone 30.
  m=self.transforms[31].copy();u,_,v=np.linalg.svd(m[:3,:3]);m[:3,:3]=u@v;return self.root@m
class Renderer:
 def __init__(self,width=1920,height=1080):
  self.width=width;self.height=height;self.ctx=moderngl.create_standalone_context(backend='egl');self.program=self.ctx.program(vertex_shader=VERT,fragment_shader=FRAG);self.textures={};self.static=[];self.dynamic=[];self.actors=[];self.models={};self.w=World();self.w.scene.set(8000000000000011862,'m_IsActive',1);self.framebuffer=self.ctx.framebuffer(color_attachments=[self.ctx.renderbuffer((width,height),components=4,samples=4)],depth_attachment=self.ctx.depth_renderbuffer((width,height),samples=4));self.output=self.ctx.simple_framebuffer((width,height),components=3);self.ctx.enable(moderngl.DEPTH_TEST|moderngl.CULL_FACE|moderngl.BLEND);self.ctx.blend_func=moderngl.SRC_ALPHA,moderngl.ONE_MINUS_SRC_ALPHA
  self.program['paint'].value=0;self.program['grass'].value=1;self.program['earth'].value=2;self.program['layoutMask'].value=3
  self.texture(A/'OkamiRemaster/Original/Textures/Kamiki-grass.png').use(1);self.texture(A/'OkamiRemaster/Original/Textures/Kamiki-earth.png').use(2);self.texture(A/'OkamiRemaster/Windflower/Textures/Existing-Road-Bank-Mask.png').use(3)
  self.identity=np.tile(np.eye(4),(128,1,1)).transpose(0,2,1).astype('f4').tobytes();self.load_scene();self.lanterns=[];self.billboards=[]
 def batch_static(self,lanterns,stand):
  groups={};lanterns={id(x) for x in lanterns};stand={id(x) for x in stand}
  for ob in self.static:
   tag='lantern' if id(ob) in lanterns else 'stand' if id(ob) in stand else 'ordinary';key=(id(ob.texture),ob.mode,ob.realm,ob.twosided,tag);groups.setdefault(key,[]).append(ob)
  batches=[]
  for key,members in groups.items():
   vertices=[];uv=[];colors=[];indices=[];count=0
   for ob in members:
    data=np.frombuffer(ob.vbo.read(),'f4').reshape(-1,15);v=data[:,:3]@ob.root[:3,:3].T+ob.root[:3,3];vertices.append(v);uv.append(data[:,3:5].copy());colors.append(data[:,5:9].copy());indices.append(ob.indices+count);count+=len(v)
   first=members[0];batch=Draw(self,np.concatenate(vertices),np.concatenate(indices),np.concatenate(uv),np.concatenate(colors),first.image_path,mode=first.mode,realm=first.realm,twosided=first.twosided);batch.vis_source=first if key[-1]!='ordinary' else None;batch.name=first.image_path;batches.append(batch)
  for ob in self.static:ob.vao.release();ob.vbo.release();ob.ibo.release()
  print('Batched',len(self.static),'static parts into',len(batches),'native material batches',flush=True);self.static=batches
 def overlay(self,ob,opacity=1):
  self.framebuffer.use();self.ctx.disable(moderngl.DEPTH_TEST);self.program['vp'].write(np.eye(4,dtype='f4').tobytes());self.program['skinned'].value=False;ob.opacity=opacity;ob.render();self.ctx.enable(moderngl.DEPTH_TEST)
 def texture(self,path):
  key=str(path)
  if key not in self.textures:
   im=Image.new('RGBA',(2,2),'white') if path is None else Image.open(path).convert('RGBA');im=im.transpose(Image.Transpose.FLIP_TOP_BOTTOM);tex=self.ctx.texture(im.size,4,im.tobytes());tex.build_mipmaps();tex.filter=(moderngl.LINEAR_MIPMAP_LINEAR,moderngl.LINEAR);tex.anisotropy=4;self.textures[key]=tex
  return self.textures[key]
 def load_scene(self):
  w=self.w
  for row in w.renderers():
   if row['lo'] is None:continue
   y=(row['lo'][1]+row['hi'][1])/2
   if y<-150 or y>20:continue
   realm='cave' if y<-35 else 'village';data=w.mesh(row['meshGUID'],row['meshID'])
   if data is None:continue
   n=len(data['vertices']);buf=bytes.fromhex(re.search('_typelessdata: ([a-f0-9]+)',data['raw'])[1]);a=np.frombuffer(buf,'<f4').reshape(n,data['stride']//4);uv=a[:,10:12] if data['stride']>=48 else np.zeros((n,2));col=a[:,6:10].copy() if data['stride']>=48 else np.ones((n,4));g=row['materials'][0] if row['materials'] else None;path=w.assets.get(g);raw=path.read_text() if path else '';m=re.search(r'- (?:_MainTex|_FlowMap|_OriginalPaint):\n        m_Texture:.*guid: (\w+)',raw);texture=w.assets.get(m[1]) if m else None;shader=w.assets.get(ref(raw,'m_Shader')[1]);two=bool(shader and 'Cull Off' in shader.read_text());mode=1 if path and path.name=='Original-Ground.mat' else 2 if row['name'].startswith('River-') else 0
   if mode in [1,2]:col[:]=1
   ob=Draw(self,data['vertices'],data['triangles'],uv,col,texture,row['matrix'],mode,realm=realm,twosided=two);ob.name=row['name'];self.static.append(ob)
  print('Saved scene:',len(self.static),'native mesh parts',flush=True)
 def place(self,resource,p,size,yaw=0,realm='village',mode=0,texture=None):
  folder=D/resource.removeprefix('Okami/');j=self.models.get(resource)
  if j is None:j=json.loads((folder/'Model.json').read_text());self.models[resource]=j
  parts=[q for q in j['parts'] if not j.get('visibleGroups') or int(q['name'].split('-')[1]) in j['visibleGroups']];v=np.concatenate([np.array(q['positions']).reshape(-1,3) for q in parts]);lo,hi=v.min(0),v.max(0);scale=np.asarray(size)/np.maximum(hi-lo,.001);offset=-np.array([(lo[0]+hi[0])/2,lo[1],(lo[2]+hi[2])/2])*scale;root=matrix(p,yaw);out=[]
  for q in parts:
   tx=next(t for t in j['textures'] if t['index']==q['texture']);v=np.array(q['positions']).reshape(-1,3)*scale+offset;col=np.array(q['colors']).reshape(-1,4);col=np.ones_like(col) if mode in [1,2,3,4] else col;ob=Draw(self,v,np.array(q['indices']).reshape(-1,3),np.array(q['uv']).reshape(-1,2),col,texture or (None if tx.get('vertexOnly') else folder/tx['path']),root,mode,realm=realm,twosided=mode==4);ob.name=resource;self.static.append(ob);out.append(ob)
  return out
 def sprite(self,name,p,width,height,right,up,tint=(1,1,1),alpha=1,tile=None):
  # Billboard sprite geometry is render plumbing; the image is original game art.
  right=np.asarray(right);up=np.asarray(up);c=np.asarray(p);v=np.array([c-right*width/2-up*height/2,c+right*width/2-up*height/2,c+right*width/2+up*height/2,c-right*width/2+up*height/2]);uv=np.array([[0,0],[1,0],[1,1],[0,1]],float)
  if tile is not None:uv[:,0]=(uv[:,0]+tile)/4
  ob=Draw(self,v,[[0,1,2],[0,2,3]],uv,np.ones((4,4)),D/'Effects'/(name+'.png'),mode=5,twosided=True);ob.tint=tint;ob.opacity=alpha;ob.render();ob.vao.release();ob.vbo.release();ob.ibo.release()
 def begin(self,eye,target,t,night=0,realm='village',fov=50):
  self.eye=np.asarray(eye,float);self.realm=realm;self.time=t;vp,self.right,self.up=camera_matrix(self.eye,np.asarray(target,float),self.width/self.height,fov);self.vp=vp;self.forward=normalize(np.asarray(target)-self.eye);p=self.program;p['vp'].write(vp.T.astype('f4').tobytes());p['cameraPos'].value=tuple(self.eye);p['clock'].value=t;p['night'].value=night;p['realm'].value=0 if realm=='village' else 1 if realm=='garden' else 2;p['skinned'].value=False;p['bones'].write(self.identity)
  sky=(.65,.74,.81) if realm=='village' else (.85,.87,.94) if realm=='garden' else (.10,.065,.075)
  sky=tuple(np.array(sky)*(1-night)+np.array([.045,.065,.13])*night) if realm=='village' else sky;self.framebuffer.use();self.ctx.viewport=(0,0,self.width,self.height);self.framebuffer.clear(*sky,1,depth=1)
 def geometry(self,night=0):
  self.program['skinned'].value=False
  for ob in self.static:
   if ob.realm==self.realm and ob.visible:ob.render()
  for actor in self.actors:
   if actor.visible:actor.draw()
  self.program['skinned'].value=False
 def end(self):
  self.ctx.copy_framebuffer(self.output,self.framebuffer);return self.output.read(components=3,alignment=1)
