"""Prompt 2B: remove the inherited cheek tunnel and refine only facial skin.

Starts from the recoverable, unapproved head study. No rig, clip, neck, body,
ornamental fur or runtime shader changes. Closure uses existing boundary verts.
"""
from pathlib import Path
import sys,json,hashlib
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.geometry import tessellate_polygon
from mathutils.bvhtree import BVHTree
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/'authoring'))
from glb_buffers import GLB,to_native,to_gltf
out=root/'review/drafts/jaw-repair';out.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root/'authoring/checkpoints/head-study/wolf.blend'))
o=bpy.data.objects['Wolf ivory coat'];mesh=o.data
archive=np.load(root/'authoring/checkpoints/head-study/head-surface.npz');rest=archive['rest'];delta=archive['delta']
assert np.array_equal(rest,np.array([v.co[:] for v in mesh.vertices],dtype=np.float32))
mesh.calc_loop_triangles();tri=np.array([t.vertices[:] for t in mesh.loop_triangles]);centers=rest[tri].mean(1)
remove=(abs(centers[:,0])<.115)&(centers[:,1]>-3.96)&(centers[:,1]<-3.76)&(centers[:,2]>4.115)&(centers[:,2]<4.215)
assert remove.sum()==144
# Find the two open borders after removing the tube's internal wall.
kept=tri[~remove];edges=np.concatenate([kept[:,[0,1]],kept[:,[1,2]],kept[:,[2,0]]]);u,c=np.unique(np.sort(edges,1),axis=0,return_counts=True);border=u[c==1]
adj={}
for a,b in border:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
assert all(len(n)==2 for n in adj.values())
loops=[]
while adj:
 first=next(iter(adj));loop=[first];last=-1;v=first
 while True:
  nxt=next(n for n in adj[v] if n!=last)
  if nxt==first:break
  loop.append(nxt);last,v=v,nxt
 for v in loop:adj.pop(v)
 loops.append(loop)
assert len(loops)==2 and all(len(l)==14 for l in loops)

def smooth(t):
 t=np.clip(t,0,1);return t*t*(3-2*t)
support=np.zeros(len(rest))
for v in mesh.vertices:
 if v.index<44506:
  amount=sum(g.weight for g in v.groups if o.vertex_groups[g.group].name in ('head','jaw'))
  support[v.index]=smooth((amount-.985)/.015)

# Sample the existing skull envelope. Tangential eye relocation must follow
# this envelope, rather than carrying the wider rear cheek into the muzzle.
bvh=BVHTree.FromPolygons([Vector(p) for p in rest],tri.tolist(),all_triangles=True)
grid_y=np.linspace(-4.35,-3.08,160);grid_z=np.linspace(4.25,5.20,150);width_grids=[]
for side in [-1,1]:
 grid=np.zeros((len(grid_z),len(grid_y)))
 for iz,z in enumerate(grid_z):
  for iy,y in enumerate(grid_y):
   hit,normal,index,distance=bvh.ray_cast(Vector((side*2,float(y),float(z))),Vector((-side,0,0)),4)
   if hit is not None:grid[iz,iy]=abs(hit.x)
 width_grids.append(grid)
def envelope(y,z,side):
 yy=np.clip((y-grid_y[0])/(grid_y[-1]-grid_y[0])*(len(grid_y)-1),0,len(grid_y)-1.001);zz=np.clip((z-grid_z[0])/(grid_z[-1]-grid_z[0])*(len(grid_z)-1),0,len(grid_z)-1.001)
 iy=yy.astype(int);iz=zz.astype(int);fy=yy-iy;fz=zz-iz;result=np.zeros_like(y)
 for sign,grid in zip([-1,1],width_grids):
  value=(1-fy)*(1-fz)*grid[iz,iy]+fy*(1-fz)*grid[iz,iy+1]+(1-fy)*fz*grid[iz+1,iy]+fy*fz*grid[iz+1,iy+1]
  result=np.where(side==sign,value,result)
 return result

def sculpt(points,allowed):
 p=np.asarray(points,dtype=float);x,y,z=p.T;a=np.asarray(allowed);d=np.zeros_like(p)
 # Lower and flatten the large supraorbital dome; leave ears and neck alone.
 forehead=np.exp(-((y+3.47)/.32)**2)*smooth((z-4.70)/.40)*(1-smooth((z-5.05)/.12))
 d[:,2]-=.080*forehead
 # Move the complete orbital bed and its existing pigment together, toward the
 # muzzle and slightly lower. A broad smooth field avoids a sliding eye decal.
 orbit=np.exp(-((y+3.51)/.40)**8-((z-4.70)/.34)**8)*smooth((abs(x)-.06)/.12)
 d[:,1]-=.090*orbit;d[:,2]-=.045*orbit
 follow=envelope(y+d[:,1],z+d[:,2],np.sign(x))-envelope(y,z,np.sign(x))
 d[:,0]+=np.sign(x)*.20*follow*orbit*smooth((abs(x)-.055)/.10)
 bed=np.exp(-((y+3.51)/.16)**2-((z-4.69)/.065)**2)*smooth((abs(x)-.08)/.13)
 rim=np.exp(-((y+3.49)/.20)**2-((z-4.79)/.065)**2)*smooth((abs(x)-.1)/.12)
 d[:,0]+=np.sign(x)*(-.006*bed+.008*rim)
 # Shorten the very end of the upper muzzle, rather than scaling the head.
 nose=smooth((-y-3.92)/.30)*smooth((z-4.235)/.08)
 d[:,1]+=.035*nose
 # Retain the extended mandible but flatten the round chin underneath it.
 chin=np.exp(-((y+4.10)/.19)**4)*smooth((4.20-z)/.09)*smooth((z-4.03)/.06)
 d[:,2]+=.028*chin;d[:,1]+=.010*chin
 # Fair the entire aperture collar into the cheek. This edits the real skin;
 # the new faces below are part of that same connected surface.
 collar=np.exp(-((y+3.855)/.18)**4-((z-4.16)/.095)**4)
 desired=(.190+.16*(y+3.855))*np.sqrt(np.maximum(.1,1-((z-4.235)/.18)**2))
 collar*=smooth((abs(x)-.025)/.04)*smooth((z-4.075)/.04)
 d[:,0]+=np.sign(x)*np.maximum(0,desired-abs(x))*collar
 boundary=smooth((-y-3.12)/.20)*smooth((z-3.96)/.12)*(1-smooth((z-5.12)/.12))
 return p+d*(a*boundary)[:,None]

def jacobian(p,a):
 cols=[]
 for axis in range(3):
  h=np.zeros(3);h[axis]=1e-4;cols.append((sculpt(p+h,a)-sculpt(p-h,a))/2e-4)
 return np.stack(cols,-1)
new=sculpt(rest,support).astype(np.float32);changed=np.linalg.norm(new-rest,axis=1)>1e-7
new[~changed]=rest[~changed];new_delta=delta.copy()
for i in range(len(delta)):new_delta[i,changed]=sculpt((rest+delta[i])[changed],support[changed])-new[changed]
# Triangulate each welded border in its cheek plane; orient outward.
caps=[]
for loop in loops:
 pts=[Vector((0,float(new[i,1]),float(new[i,2]))) for i in loop]
 for triangle in tessellate_polygon([pts]):
  ids=[loop[v] for v in triangle];q=new[ids]
  if np.cross(q[1]-q[0],q[2]-q[0])[0]*np.sign(q[:,0].mean())<0:ids.reverse()
  caps.append(ids)
new_tri=np.concatenate([kept,np.array(caps)])
# True closure, consistent orientation and no extra detached surfaces.
e=np.concatenate([new_tri[:,[0,1]],new_tri[:,[1,2]],new_tri[:,[2,0]]]);ue,counts=np.unique(np.sort(e,1),axis=0,return_counts=True)
assert np.all(counts==2)
signs=np.where(e[:,0]<e[:,1],1,-1);order=np.lexsort((e.max(1),e.min(1)));assert np.all(signs[order].reshape(-1,2).sum(1)==0)
# Native bmesh edit retains UVs, custom layers, bone groups and vertex ordering.
bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
# Triangulate just polygons belonging to the removed tube.
polys={mesh.loop_triangles[i].polygon_index for i in np.where(remove)[0]}
bm.faces.ensure_lookup_table();bmesh.ops.triangulate(bm,faces=[bm.faces[i] for i in polys],quad_method='FIXED',ngon_method='EAR_CLIP')
kill=[]
for face in bm.faces:
 c=np.array(face.calc_center_median())
 if abs(c[0])<.115 and -3.96<c[1]<-3.76 and 4.115<c[2]<4.215:kill.append(face)
bmesh.ops.delete(bm,geom=kill,context='FACES_ONLY');bm.verts.ensure_lookup_table()
for ids in caps:
 face=bm.faces.new([bm.verts[int(i)] for i in ids])
 # Continuous skin UVs: reuse each collar vertex's neighboring loop UV.
 for layer in bm.loops.layers.uv.values():
  for loop in face.loops:
   neighbor=next((l for l in loop.vert.link_loops if l.face!=face),None)
   if neighbor:loop[layer].uv=neighbor[layer].uv
for i,v in enumerate(bm.verts):v.co=new[i]
bm.to_mesh(mesh);bm.free();mesh.update()
assert len(mesh.vertices)==len(rest)
mesh.calc_loop_triangles();assert len(mesh.loop_triangles)==len(new_tri),(len(mesh.loop_triangles),len(new_tri))
bpy.data.objects['DivineWolfRig'].animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(out/'jaw-repair.blend'),compress=True)
np.savez_compressed(out/'jaw-surface.npz',rest=new,delta=new_delta,facial_mask=changed,triangles=new_tri)
asset=GLB(root/'public/models/head-study.glb');prim=asset.doc['meshes'][0]['primitives'][0]
k=KDTree(len(rest))
for i,p in enumerate(to_gltf(rest)):k.insert(Vector(p),i)
k.balance();mapping=np.array([k.find(Vector(p))[1] for p in asset.read(prim['attributes']['POSITION'])]);ids=mapping;region=changed[ids]
positions=asset.read(prim['attributes']['POSITION']);positions[region]=to_gltf(new)[ids[region]];asset.write(prim['attributes']['POSITION'],positions)
indices=asset.read(prim['indices']).ravel().reshape(-1,3);native=ids[indices];c=rest[native].mean(1)
rm=(abs(c[:,0])<.115)&(c[:,1]>-3.96)&(c[:,1]<-3.76)&(c[:,2]>4.115)&(c[:,2]<4.215);assert rm.sum()==144
render_for={}
for t in indices[~rm]:
 for v in t:render_for.setdefault(int(ids[v]),int(v))
caprender=np.array([[render_for[i] for i in face] for face in caps],dtype='<u4')
idx=np.concatenate([indices[~rm],caprender]).astype('<u4').ravel();acc=asset.doc['accessors'][prim['indices']];acc.update(bufferView=asset.append_view(idx),byteOffset=0,componentType=5125,count=len(idx),min=[int(idx.min())],max=[int(idx.max())])
# Differential normals outside the repaired collar, area-weighted normals on it.
J=jacobian(rest[ids[region]],support[ids[region]]);assert np.linalg.det(J).min()>0,'Facial map foldover';N=np.linalg.inv(J).transpose(0,2,1)
old=asset.read(prim['attributes']['NORMAL']);norm=old.copy();n=np.einsum('vij,vj->vi',N,to_native(old[region]));n/=np.linalg.norm(n,axis=1)[:,None];norm[region]=to_gltf(n)
def geomnormal(p):
 g=np.zeros_like(p);v=np.cross(p[new_tri[:,1]]-p[new_tri[:,0]],p[new_tri[:,2]]-p[new_tri[:,0]])
 for j in range(3):np.add.at(g,new_tri[:,j],v)
 return g/(np.linalg.norm(g,axis=1)[:,None]+1e-12)
x,y,z=rest.T;repair=(np.arange(len(rest))<44506)&(abs(y+3.855)<.20)&(abs(z-4.16)<.12);r=repair[ids];gn=geomnormal(new);norm[r]=to_gltf(gn[ids[r]]);asset.write(prim['attributes']['NORMAL'],norm)
for i,target in enumerate(prim['targets']):
 values=asset.read(target['POSITION']);values[region]=to_gltf(new_delta[i])[ids[region]];asset.write(target['POSITION'],values)
 dn=asset.read(target['NORMAL']);base=to_native(old[region]);loc=np.linalg.inv(jacobian((rest+delta[i])[ids[region]],support[ids[region]])).transpose(0,2,1)
 posed=np.einsum('vij,vj->vi',loc,base+to_native(dn[region]));posed/=np.linalg.norm(posed,axis=1)[:,None];dn[region]=to_gltf(posed)-norm[region]
 dgn=geomnormal(new+new_delta[i]);dn[r]=to_gltf(dgn[ids[r]]-gn[ids[r]])
 target['NORMAL']=asset.write_sparse(target['NORMAL'],dn)
# Cull back faces so a folded or missing cheek cannot be hidden by rendering.
for material in asset.doc['materials']: material['doubleSided']=False
exec(compile((root/'authoring/repair_jaw_uv.py').read_text(),'repair-jaw-uv','exec'))
asset.save(root/'public/models/jaw-repair.glb')
metadata=json.loads((root/'public/face-head-study.json').read_text())
for eye in metadata['eyes']:
 p=np.array(eye['point'])[None,:];eye['point']=sculpt(p,np.ones(1))[0].tolist();n=np.linalg.inv(jacobian(p,np.ones(1))[0]).T@np.array(eye['surface_normal']);eye['surface_normal']=(n/np.linalg.norm(n)).tolist()
(root/'public/face-jaw-repair.json').write_text(json.dumps(metadata,indent=2)+'\n')
metrics={'sourceSHA256':hashlib.sha256((root/'public/models/head-study.glb').read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256((root/'public/models/jaw-repair.glb').read_bytes()).hexdigest(),'internalTunnelTrianglesRemoved':int(rm.sum()),'weldedClosureTriangles':len(caps),'newVertices':0,'changedFacialVertices':int(changed.sum()),'closedSurfaceEdges':bool(np.all(counts==2)),'reviewStatus':'NOT APPROVED'}
(out/'repair.json').write_text(json.dumps(metrics,indent=2)+'\n');print('JAW_REPAIR',metrics,flush=True)
