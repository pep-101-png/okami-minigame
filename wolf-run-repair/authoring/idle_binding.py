"""Embed approved idle skin bindings, remapped to the expanded joint palette."""
import json,struct,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

def read_glb(path):
 data=path.read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);offset=20+length;length=struct.unpack_from('<I',data,offset)[0];return doc,bytearray(data[offset+8:offset+8+length])
def accessor(doc,binary,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];types={5126:np.float32,5123:np.uint16,5125:np.uint32,5121:np.uint8};components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dtype=np.dtype(types[a['componentType']]);offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',components*dtype.itemsize);arr=np.ndarray((a['count'],components),dtype=dtype,buffer=binary,offset=offset,strides=(stride,dtype.itemsize)).copy()
 if a.get('normalized'):arr=arr.astype(float)/np.iinfo(dtype).max
 return arr

def embed_idle_binding(asset,approved):
 old,oldbin=read_glb(approved);doc,binary=read_glb(asset);p_old=old['meshes'][0]['primitives'][0];p_new=doc['meshes'][0]['primitives'][0]
 oldpos=accessor(old,oldbin,p_old['attributes']['POSITION']);newpos=accessor(doc,binary,p_new['attributes']['POSITION']);oldindices=accessor(old,oldbin,p_old['attributes']['JOINTS_0']);oldweights=accessor(old,oldbin,p_old['attributes']['WEIGHTS_0']);tri=accessor(old,oldbin,p_old['indices']).ravel().reshape(-1,3)
 names_old=[old['nodes'][n]['name'] for n in old['skins'][0]['joints']];names_new=[doc['nodes'][n]['name'] for n in doc['skins'][0]['joints']];remap=np.array([names_new.index(n) for n in names_old],dtype=np.uint16)
 kd=KDTree(len(oldpos))
 for i,p in enumerate(oldpos):kd.insert(Vector(p),i)
 kd.balance();bvh=BVHTree.FromPolygons([Vector(p) for p in oldpos],[list(t) for t in tri],all_triangles=True)
 indices=np.zeros((len(newpos),4),dtype=np.uint16);weights=np.zeros((len(newpos),4),dtype=np.float32)
 for i,p in enumerate(newpos):
  _,nearest,distance=kd.find(Vector(p))
  if distance<1e-5:indices[i]=remap[oldindices[nearest].astype(int)];weights[i]=oldweights[nearest];continue
  hit,normal,face,distance=bvh.find_nearest(Vector(p));a,b,c=tri[face];bary=barycentric_transform(hit,Vector(oldpos[a]),Vector(oldpos[b]),Vector(oldpos[c]),Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
  merged={}
  for vertex,amount in zip([a,b,c],bary):
   for n,w in zip(oldindices[vertex],oldweights[vertex]):merged[int(remap[int(n)])]=merged.get(int(remap[int(n)]),0)+max(0,amount)*float(w)
  top=sorted(merged.items(),key=lambda q:q[1],reverse=True)[:4];total=sum(w for _,w in top)
  for j,(n,w) in enumerate(top):indices[i,j]=n;weights[i,j]=w/total
 for name,array,component in [('_IDLE_SKIN_INDEX',indices,5123),('_IDLE_SKIN_WEIGHT',weights,5126)]:
  while len(binary)%4:binary.append(0)
  view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':array.nbytes,'target':34962});binary.extend(array.tobytes());index=len(doc['accessors']);doc['accessors'].append({'bufferView':view,'componentType':component,'count':len(array),'type':'VEC4'});p_new['attributes'][name]=index
 while len(binary)%4:binary.append(0)
 doc['buffers'][0]['byteLength']=len(binary);text=json.dumps(doc,separators=(',',':')).encode()
 while len(text)%4:text+=b' '
 result=struct.pack('<III',0x46546c67,2,12+8+len(text)+8+len(binary))+struct.pack('<II',len(text),0x4e4f534a)+text+struct.pack('<II',len(binary),0x004e4942)+binary;asset.write_bytes(result)
