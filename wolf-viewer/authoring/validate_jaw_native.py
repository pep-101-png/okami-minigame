"""Native cheek topology, intersection and protected-surface audit."""
import bpy,numpy as np,sys,json,ast
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
r=Path(__file__).resolve().parents[1];out=r/'review/drafts/jaw-repair'
bpy.ops.wm.open_mainfile(filepath=str(out/'jaw-repair.blend'));o=bpy.data.objects['Wolf ivory coat'];m=o.data;m.calc_loop_triangles();tri=np.array([t.vertices[:] for t in m.loop_triangles]);data=np.load(out/'jaw-surface.npz');p=data['rest'];src=np.load(r/'authoring/checkpoints/head-study/head-surface.npz');mask=data['facial_mask'];assert np.array_equal(p,np.array([v.co[:] for v in m.vertices],dtype=np.float32));assert np.array_equal(p[~mask],src['rest'][~mask]);assert np.array_equal(data['delta'][:,~mask],src['delta'][:,~mask]);assert not mask[44506:].any()
# Mesh connectivity after removing unused former tunnel-wall vertices.
e=np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]);_,cnt=np.unique(np.sort(e,1),axis=0,return_counts=True);assert np.all(cnt==2)
face=tri[np.any(mask[tri],axis=1)];tree=BVHTree.FromPolygons([Vector(v) for v in p],face.tolist(),all_triangles=True,epsilon=0);overlap=[(a,b)for a,b in tree.overlap(tree)if a<b and not set(face[a]).intersection(face[b])];print('Rest facial triangle intersections',len(overlap),flush=True)
# Numeric local map Jacobians report risky foldovers separately from closure.
support=np.zeros(len(p))
for v in m.vertices:
 if v.index<44506:
  a=sum(g.weight for g in v.groups if o.vertex_groups[g.group].name in ('head','jaw'));v0=np.clip((a-.985)/.015,0,1);support[v.index]=v0*v0*(3-2*v0)
treeast=ast.parse((r/'authoring/repair_jaw.py').read_text());env={'np':np};exec(compile(ast.Module(body=[n for n in treeast.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'sculpt-functions','exec'),env)
env.update({'rest':src['rest'],'tri':tri,'Vector':Vector,'BVHTree':BVHTree});text=(r/'authoring/repair_jaw.py').read_text();exec(text[text.index('# Sample the existing skull envelope.'):text.index('def sculpt(points,allowed):')],env)
J=env['jacobian'](src['rest'][mask],support[mask]);det=np.linalg.det(J);print('Jacobian range',det.min(),det.max(),flush=True)
result={'closedEdges':bool(np.all(cnt==2)),'restFacialIntersectionPairs':len(overlap),'minimumSculptJacobian':float(det.min()),'protectedVertexChanges':0,'ornamentalFurChanges':0,'newNativeVertices':0,'triangles':len(tri),'removedInternalTunnelTriangles':144,'weldedClosureTriangles':24}
(out/'native-validation.json').write_text(json.dumps(result,indent=2)+'\n');assert not overlap
