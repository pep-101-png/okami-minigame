"""Layered sculpted fur curls on the repaired coat; no boolean fusion.

Closed tapered strands keep the clean underlying skin and give the shoulder,
ankles, ruff, haunch and tail readable depth. Root weights stay anchored while
loose tips blend progressively through the existing flow controls.
"""
from pathlib import Path
import bpy, math, json
import numpy as np
from mathutils import Vector
root=Path(__file__).resolve().parents[1];draft=root/'review/drafts'
bpy.ops.wm.open_mainfile(filepath=str(draft/'run-candidate.blend'))
coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig']
if coat.get('fur_details'):
    bpy.ops.wm.open_mainfile(filepath=str(draft/'fur-detail-source.blend'))
    coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig']
    archive=np.load(draft/'fur-detail-source.npz')
else:
    archive=np.load(draft/'surface.npz')
    bpy.ops.wm.save_as_mainfile(filepath=str(draft/'fur-detail-source.blend'))
    np.savez_compressed(draft/'fur-detail-source.npz',rest=archive['rest'],delta=archive['delta'])
rig.animation_data.action=None
for bone in rig.pose.bones:bone.location=(0,0,0);bone.rotation_euler=(0,0,0)
bpy.context.view_layer.update()
old_count=len(coat.data.vertices);old_delta=archive['delta']
verts=[tuple(v.co) for v in coat.data.vertices];faces=[tuple(f.vertices) for f in coat.data.polygons]
weights=[{coat.vertex_groups[g.group].name:g.weight for g in v.groups} for v in coat.data.vertices]
wash=[(1,1,1,1)]*old_count
# Additional hip fur controls use the same anchored spring response as the ruff.
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for side,sign in [('L',1),('R',-1)]:
    start=Vector((sign*.65,2.12,3.22));end=Vector((sign*.85,2.80,3.38))
    parent='hips'
    for suffix,a,b in [('',0,.45),('Flow',.45,.76),('Tip',.76,1.12)]:
        name='haunchFur'+side+suffix
        bone=rig.data.edit_bones.new(name);bone.head=start.lerp(end,a);bone.tail=start.lerp(end,b);bone.parent=rig.data.edit_bones[parent];parent=name
bpy.ops.object.mode_set(mode='OBJECT')
for side in ['L','R']:
    for suffix in ['', 'Flow', 'Tip']:rig.pose.bones['haunchFur'+side+suffix].rotation_mode='XYZ'

def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def flow_weights(name,t):
    q=min(1.999,max(0,t)*2);i=int(q);u=smooth(q-i);names=[name,name+'Flow',name+'Tip'];return {names[i]:1-u,names[i+1]:u}
metadata=json.loads((root/'public/tail.json').read_text());tailpoints=np.array(metadata['points']);lengths=np.linalg.norm(np.diff(tailpoints,axis=0),axis=1);arc=np.r_[0,np.cumsum(lengths)]
def tail_weights(point):
    best=(1e9,0)
    for j,d in enumerate(np.diff(tailpoints,axis=0)):
        u=np.clip(np.dot(np.array(point)-tailpoints[j],d)/np.dot(d,d),0,1);distance=np.linalg.norm(np.array(point)-(tailpoints[j]+u*d))
        if distance<best[0]:best=(distance,arc[j]+u*lengths[j])
    s=best[1];q=np.clip(s/arc[-1]*16-.35,0,14.999);i=int(q);u=smooth(q-i);amount=smooth(s/.24)
    return {'hips':1-amount,f'plume{i:02}':amount*(1-u),f'plume{i+1:02}':amount*u}
# Let the whole visible tail leave the hip smoothly, including its proximal skin.
for i,point in enumerate(verts):
    if sum(w for n,w in weights[i].items() if n.startswith('plume'))>.005 or (point[1]>2.68 and abs(point[0])<.48 and point[2]>2.7):
        weights[i]=tail_weights(point)

def bezier(points,t):
    p=[Vector(v) for v in points]
    while len(p)>1:p=[a.lerp(b,t) for a,b in zip(p,p[1:])]
    return p[0]
strands=[];strand_ranges=[]
def strand(name,path,width,depth,side,bone,kind='blade',segments=56):
    start=len(verts);ring=12
    for j in range(segments):
        t=j/(segments-1);p=Vector(path(t));a=Vector(path(max(0,t-.002)));b=Vector(path(min(1,t+.002)));direction=(b-a).normalized()
        across=Vector((0,-direction.z,direction.y)).normalized()
        if across.length<.01:across=Vector((0,1,0))
        taper=max(.018,math.sin(math.pi*(.12+.88*t))**.65*(1-t)**.18)
        if kind=='curl':taper=max(.025,(1-t)**.55)
        for k in range(ring):
            angle=math.tau*k/ring;point=p+across*(width*taper*math.cos(angle))+Vector((side*depth*taper*math.sin(angle),0,0));verts.append(tuple(point))
            if bone=='tail':w=tail_weights(point)
            elif kind=='curl':w={bone:.9,bone+'Flow':.1}
            else:w=flow_weights(bone,t*.92)
            weights.append(w)
            # Quiet blue-grey underlayers and warm ivory ridges, smoothly painted
            # around the strand rather than a black spiral drawn across it.
            light=.5+.5*math.sin(angle);tip=smooth(t)
            wash.append((.72+.25*light+.03*tip,.77+.21*light+.02*tip,.79+.18*light+.01*tip,1))
    for j in range(segments-1):
        for k in range(ring):
            a=start+j*ring+k;b=start+j*ring+(k+1)%ring;faces.append((a,b,b+ring,a+ring))
    faces.append(tuple(start+k for k in reversed(range(ring))));faces.append(tuple(start+(segments-1)*ring+k for k in range(ring)))
    strands.append(name);strand_ranges.append({'name':name,'start':start,'segments':segments,'ring':ring})

for side,sign in [('L',1),('R',-1)]:
    bone='shoulderFur'+side
    # The shoulder's relief is a physical tapered curl, with open negative space
    # between its turns, accompanied by two overlapping swept fur blades.
    def curl(t,sign=sign):
        angle=-math.pi*.5+t*math.tau*1.12;r=.34*(1-t)**.72+.015
        return (sign*(.95+.49*smooth(t/.30)), -1.12+r*math.cos(angle),3.58+r*math.sin(angle))
    strand('Shoulder curl '+side,curl,.090,.052,sign,bone,'curl',72)
    for layer,(offset,length,width) in enumerate([(0,1,.13),(-.14,.79,.095)]):
        control=[(sign*(.80-.05*layer),-1.67,3.39+offset),(sign*(1.42-.09*layer),-1.51,3.97+offset),(sign*(1.40-.09*layer),-.57,3.86+offset),(sign*(1.25-.09*layer),-.19+(1-length)*.65,4.28+offset)]
        strand('Shoulder flowing layer '+side+str(layer),lambda t,c=control:bezier(c,t),width,.040,sign,bone)
    # Small, asymmetrical underlayers blend into the neck, rather than fins.
    for j in range(3):
        control=[(sign*(.57+.07*j),-2.67+.23*j,4.39-.24*j),(sign*(.76+.06*j),-2.40+.22*j,4.34-.23*j),(sign*(.84+.04*j),-2.15+.18*j,4.04-.22*j),(sign*(.76+.05*j),-1.94+.17*j,4.16-.24*j)]
        strand('Ruff layer '+side+str(j),lambda t,c=control:bezier(c,t),.095-j*.013,.035,sign,'ruff'+side,segments=40)
    for leg,cy in [('fore',-1.18),('hind',2.15)]:
        bone=leg+'Fur'+side
        def ankle_curl(t,sign=sign,cy=cy):
            angle=-math.pi*.6+t*math.tau*1.05;r=.16*(1-t)**.72+.009
            return (sign*(.69+.48*smooth(t/.25)),cy+r*math.cos(angle),.91+r*math.sin(angle))
        strand(leg+' ankle curl '+side,ankle_curl,.046,.030,sign,bone,'curl',60)
        for layer,(dy,dz,width) in enumerate([(0,0,.092),(-.12,-.17,.068)]):
            control=[(sign*(.70-.09*layer),cy-.08+dy,.78+dz),(sign*(1.12-.09*layer),cy+.14+dy,1.13+dz),(sign*(1.14-.09*layer),cy+.65+dy,1.48+dz),(sign*(1.03-.09*layer),cy+.43+dy,1.88+dz)]
            strand(leg+' ankle plume '+side+str(layer),lambda t,c=control:bezier(c,t),width,.035,sign,bone,segments=48)
    for j in range(2):
        control=[(sign*(.62+.03*j),2.11,3.27-.15*j),(sign*(.82+.03*j),2.36,3.28-.14*j),(sign*(.88+.03*j),2.62,3.00-.14*j),(sign*(.78+.02*j),2.82,3.14-.14*j)]
        strand('Haunch wisp '+side+str(j),lambda t,c=control:bezier(c,t),.085-j*.02,.035,sign,'haunchFur'+side,segments=40)
    for j in range(2):
        control=[(sign*(.15+.05*j),3.44,3.43),(sign*(.28+.05*j),3.71,3.67),(sign*(.30+.04*j),4.02,3.98),(sign*(.10+.06*j),4.35,4.44-j*.15)]
        strand('Tail soft layer '+side+str(j),lambda t,c=control:bezier(c,t),.092-j*.024,.035,sign,'tail',segments=48)
# Rebuild the combined mesh, preserving all original body bindings and poses.
mesh=bpy.data.meshes.new('Defined layered divine fur');mesh.from_pydata(verts,[],faces);mesh.update();coat.data=mesh
for group in list(coat.vertex_groups):coat.vertex_groups.remove(group)
groups={n:coat.vertex_groups.new(name=n) for n in {n for row in weights for n in row}}
for i,row in enumerate(weights):
    top=sorted(((n,w) for n,w in row.items() if w>1e-7),key=lambda p:-p[1])[:4];total=sum(w for _,w in top)
    for name,w in top:groups[name].add([i],w/total,'REPLACE')
attr=mesh.color_attributes.new(name='FurWash',type='FLOAT_COLOR',domain='POINT');attr.data.foreach_set('color',np.asarray(wash,dtype=np.float32).ravel())
mask=mesh.color_attributes.new(name='FurGeometry',type='FLOAT_COLOR',domain='POINT');mask.data.foreach_set('color',np.array([(0,0,0,1)]*old_count+[(1,1,1,1)]*(len(verts)-old_count),dtype=np.float32).ravel())
for face in mesh.polygons:face.use_smooth=True
# Consistent outward winding for the new closed strands.
import bmesh
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
rest=np.array([v.co[:] for v in mesh.vertices],dtype=np.float32);assert np.max(np.abs(rest[:old_count]-archive['rest']))<1e-6,'Detail pass changed the approved body';delta=np.zeros((48,len(rest),3),dtype=np.float32);delta[:,:old_count]=old_delta
np.savez_compressed(draft/'surface.npz',rest=rest,delta=delta)
coat['fur_details']=True;rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(draft/'run-candidate.blend'))
(root/'review/fur-details.json').write_text(json.dumps({'strands':strands,'ranges':strand_ranges,'originalVertices':old_count,'vertices':len(verts),'newVertices':len(verts)-old_count},indent=2)+'\n')
print('SCULPTED_FUR',len(strands),len(verts),flush=True)
