"""Bury fur roots in the coat and blend their skin into the attachment surface.

Run after fur_details. UVs and topology are retained, so this can also refine an
already painted sculpt. Tips retain their free flow controls.
"""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
root=Path(__file__).resolve().parents[1];draft=root/'review/drafts'
bpy.ops.wm.open_mainfile(filepath=str(draft/'run-candidate.blend'));coat=bpy.data.objects['Wolf ivory coat']
if coat.get('fur_anchored'):raise RuntimeError('Fur already anchored; regenerate details before repeating.')
manifest=json.loads((root/'review/fur-details.json').read_text());count=manifest['originalVertices'];archive=np.load(draft/'surface.npz');rest=archive['rest'].copy();delta=archive['delta']
coat.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in coat.data.loop_triangles if all(i<count for i in t.vertices)])
tree=BVHTree.FromPolygons([v.co.copy() for v in coat.data.vertices[:count]],tri.tolist(),all_triangles=True)
original=[{coat.vertex_groups[g.group].name:g.weight for g in v.groups} for v in coat.data.vertices]
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
for strand in manifest['ranges']:
    start,rings,ring=strand['start'],strand['segments'],strand['ring'];center=Vector(np.mean(rest[start:start+ring],axis=0))
    hit,normal,face,distance=tree.find_nearest(center);indices=tri[face]
    bary=barycentric_transform(hit,*[Vector(rest[i]) for i in indices],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    bary=np.maximum(np.array(bary),0);bary/=bary.sum();anchor={}
    for vertex,amount in zip(indices,bary):
        for name,weight in original[vertex].items():anchor[name]=anchor.get(name,0)+weight*amount
    offset=np.array(hit-normal*.06-center)
    for j in range(rings):
        amount=1-smooth(j/(rings-1)/.28)
        if amount<=0:continue
        for k in range(ring):
            i=start+j*ring+k;rest[i]+=offset*amount;coat.data.vertices[i].co=rest[i]
            merged={n:w*(1-amount) for n,w in original[i].items()}
            for name,weight in anchor.items():merged[name]=merged.get(name,0)+weight*amount
            top=sorted(((n,w) for n,w in merged.items() if w>1e-8),key=lambda p:-p[1])[:4];total=sum(w for _,w in top)
            for group_index in [g.group for g in coat.data.vertices[i].groups]:coat.vertex_groups[group_index].remove([i])
            for name,weight in top:coat.vertex_groups[name].add([i],float(weight/total),'REPLACE')
coat['fur_anchored']=True;np.savez_compressed(draft/'surface.npz',rest=rest,delta=delta);bpy.ops.wm.save_as_mainfile(filepath=str(draft/'run-candidate.blend'));print('ANCHORED_STRANDS',len(manifest['ranges']))
