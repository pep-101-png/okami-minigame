"""Rig the untouched uploaded glTF. Run with Blender 4.3+, from any directory.

No mesh editing, normal recalculation, UV/material replacement, or animation baking.
The existing inward ink hull receives barycentrically transferred skin weights.
"""
import bpy, math, json, hashlib, os
from pathlib import Path
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'uploaded-wolf-review/source'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SOURCE / 'scene.gltf'))
scene = bpy.context.scene
meshes = sorted([o for o in scene.objects if o.type == 'MESH'], key=lambda o: o.name)

def fingerprint(o):
    data = {'v':[list(v.co) for v in o.data.vertices],
            'faces':[list(p.vertices) for p in o.data.polygons],
            'uv':[[list(l.uv) for l in u.data] for u in o.data.uv_layers],
            'smooth':[p.use_smooth for p in o.data.polygons],
            'normals':[list(n.vector) for n in o.data.corner_normals]}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

fingerprints = {o.name: fingerprint(o) for o in meshes}
rest = {o.name:[o.matrix_world @ v.co for v in o.data.vertices] for o in meshes}
texture_proof = {str(p.relative_to(SOURCE)):hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in SOURCE.rglob('*') if p.is_file()}

def collection(name):
    c=bpy.data.collections.new(name); scene.collection.children.link(c); return c
skin_col=collection('01 · Original painted surfaces and ink hull')
rig_col=collection('02 · WOLF RIG — select and enter Pose Mode')
shapes_col=collection('03 · Control shapes (hidden)')
studio_col=collection('04 · Preview studio (not part of wolf)')
for o in meshes:
    world=o.matrix_world.copy()
    o.parent=None; o.matrix_world=world
    for c in list(o.users_collection): c.objects.unlink(o)
    skin_col.objects.link(o)
    o['original_mesh_sha256']=fingerprints[o.name]
    o['source_component']=o.name
    # Same front-face-only preview used by the approved browser viewer.
    # Shader nodes, images, UV sampling, values and material slots are unchanged.
    for mat in o.data.materials: mat.use_backface_culling=True
for o in list(scene.objects):
    if o.type=='EMPTY': bpy.data.objects.remove(o,do_unlink=True)

arm=bpy.data.armatures.new('Original wolf · quadruped skeleton')
rig=bpy.data.objects.new('WOLF_RIG',arm);rig_col.objects.link(rig)
rig.show_in_front=True;arm.display_type='OCTAHEDRAL'
rig['Rig notes']='Read START HERE text. Original rest mesh/UVs/normals unchanged. No animation actions.'
rig['Coordinate system']='Blender Z up, wolf faces -Y; .L = positive X.'
rig['Controls']='Gold = root/body; green = planted IK paws; blue = body FK; purple = head/jaw; teal = tail.'
bpy.context.view_layer.objects.active=rig;rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')
spec={};controls={};deform={};mechanism=[]
def bone(name,h,t,parent=None,deform=False,connected=False):
    b=arm.edit_bones.new(name);b.head=h;b.tail=t;b.use_deform=deform
    if parent:b.parent=arm.edit_bones[parent];b.use_connect=connected
    spec[name]=(Vector(h),Vector(t))
    return b
def ctrl(name,h,t,parent=None,category='Body FK'):
    bone(name,h,t,parent);controls[name]=category;return name
def pair(name,h,t,parent_ctrl,parent_def,category='Body FK'):
    c=ctrl('CTRL_'+name,h,t,parent_ctrl,category)
    d='DEF_'+name;bone(d,h,t,parent_def,True);deform[d]=c
    return c,d

ctrl('CTRL_root',(0,0,0),(0,0,.6),category='Root and body')
ctrl('CTRL_body',(0,0,3.05),(0,-.6,3.05),'CTRL_root','Root and body')
hips,pelvis=pair('hips',(0,1.65,3.03),(0,.8,3.22),'CTRL_body',None)
spine1,dsp1=pair('spine_mid',(0,.8,3.22),(0,-.3,3.33),hips,pelvis)
chest,dchest=pair('chest',(0,-.3,3.33),(0,-1.55,3.35),spine1,dsp1)
neck1,dn1=pair('neck_base',(0,-1.55,3.35),(0,-2.2,3.95),chest,dchest)
neck2,dn2=pair('neck_upper',(0,-2.2,3.95),(0,-2.9,4.48),neck1,dn1)
head,dhead=pair('head',(0,-2.9,4.48),(0,-3.85,4.35),neck2,dn2,'Head and face')
jaw,djaw=pair('jaw',(0,-3.31,4.14),(0,-4.02,4.035),head,dhead,'Head and face')
for side,sgn in [('L',1),('R',-1)]:
    pair('ear.'+side,(sgn*.32,-2.84,4.84),(sgn*.36,-2.92,5.27),head,dhead,'Head and face')

tail_pts=[(0,1.93,3.34),(0,2.44,3.01),(0,2.98,2.76),(0,3.48,2.38),(0,3.93,1.66),(0,4.4,1.02)]
pc,pd=hips,pelvis
for i in range(5):
    pc,pd=pair('tail_%02d'%(i+1),tail_pts[i],tail_pts[i+1],pc,pd,'Tail FK')

leg_specs={}
for side,sgn in [('L',1),('R',-1)]:
    for kind in ['front','rear']:
        tag=kind+'.'+side;x=sgn*.61
        if kind=='front':
            shoulder=(x,-1.42,2.95); elbow=(x,-1.18,1.82); wrist=(x,-1.39,.43)
            toe=(x,-1.78,.13); tip=(x,-2.08,.105)
            scap_h=(sgn*.48,-.95,3.5)
            sc,ds=pair('shoulder.'+side,scap_h,shoulder,chest,dchest)
            joints=[shoulder,elbow,wrist,toe,tip]
            names=['upper','lower','paw','toes']
            attach=ds
        else:
            hip=(x,1.42,3.04);knee=(x,1.25,2.05);hock=(x,2.09,.87)
            ankle=(x,1.98,.25);toe=(x,1.67,.115);tip=(x,1.36,.09)
            hc,ds=pair('hip_socket.'+side,(sgn*.4,1.5,3.14),hip,hips,pelvis)
            joints=[hip,knee,hock,ankle,toe,tip]
            names=['upper','lower','hock','paw','toes'];attach=ds
        parent=attach
        for i,n in enumerate(names):
            dn='DEF_'+kind+'_'+n+'.'+side
            bone(dn,joints[i],joints[i+1],parent,True, i>0);parent=dn
        paw_idx=2 if kind=='front' else 3
        paw=ctrl('CTRL_paw_'+tag,joints[paw_idx],joints[paw_idx+1],'CTRL_root','Paw IK')
        ctrl('CTRL_toes_'+tag,joints[-2],joints[-1],paw,'Paw IK')
        pole_y=1.2 if kind=='front' else -1.4
        pole=ctrl('CTRL_pole_'+tag,(x,pole_y,1.9),(x,pole_y,2.2),'CTRL_root','IK poles')
        target='MCH_target_'+tag
        bone(target,joints[2],Vector(joints[2])+Vector((0,0,.2)),paw);mechanism.append(target)
        if kind=='rear':
            follow='MCH_hock_'+tag
            bone(follow,joints[2],joints[3],paw);mechanism.append(follow)
        leg_specs[tag]={'kind':kind,'side':side,'joints':[list(v) for v in joints],'paw':paw,'pole':pole,'target':target}

bpy.ops.object.mode_set(mode='OBJECT')
for d,c in deform.items():
    co=rig.pose.bones[d].constraints.new('COPY_TRANSFORMS');co.name='Follow animator control'
    co.target=rig;co.subtarget=c;co.target_space='WORLD';co.owner_space='WORLD'

calibration={}
for tag,item in leg_specs.items():
    k,s=item['kind'],item['side'];lower=rig.pose.bones['DEF_'+k+'_lower.'+s]
    ik=lower.constraints.new('IK');ik.name='Planted paw · non-stretch two-bone IK'
    ik.target=rig;ik.subtarget=item['target'];ik.chain_count=2;ik.use_stretch=False
    ik.pole_target=rig;ik.pole_subtarget=item['pole'];ik.iterations=128
    for n in ['upper','lower']:rig.pose.bones['DEF_'+k+'_'+n+'.'+s].ik_stretch=0
    # Pole-angle solve against ORIGINAL elbow/knee, never change the rest mesh.
    best=(1e9,0)
    for i in range(73):
        angle=-math.pi+i*math.tau/72;ik.pole_angle=angle;bpy.context.view_layer.update()
        err=(lower.head-Vector(item['joints'][1])).length
        if err<best[0]:best=err,angle
    center=best[1]
    for i in range(41):
        angle=center+(i-20)*math.tau/72/20;ik.pole_angle=angle;bpy.context.view_layer.update()
        err=(lower.head-Vector(item['joints'][1])).length
        if err<best[0]:best=err,angle
    ik.pole_angle=best[1];calibration[tag]={'joint_error':best[0],'pole_angle':best[1]}
    if k=='rear':
        c=rig.pose.bones['DEF_rear_hock.'+s].constraints.new('COPY_ROTATION')
        c.target=rig;c.subtarget='MCH_hock_'+tag;c.target_space='WORLD';c.owner_space='WORLD'
    for part,ct in [('paw',item['paw']),('toes','CTRL_toes_'+tag)]:
        c=rig.pose.bones['DEF_'+k+'_'+part+'.'+s].constraints.new('COPY_ROTATION')
        c.name='Paw orientation / toe curl';c.target=rig;c.subtarget=ct;c.target_space='WORLD';c.owner_space='WORLD'

def smooth(v):
    t=max(0.,min(1.,v));return t*t*(3-2*t)
def blend(a,b,t):
    out={k:w*(1-t) for k,w in a.items()}
    for k,w in b.items():out[k]=out.get(k,0)+w*t
    return out
def sequence(t,centers,names,width):
    # Piecewise smooth joint blends, rigid shaft centers.
    out={names[0]:1.}
    for i,c in enumerate(centers):
        w=width[i] if isinstance(width,(tuple,list)) else width
        out=blend(out,{names[i+1]:1.},smooth((t-c+w)/(2*w)))
    return out
def trunk(p):
    x,y,z=p
    w=sequence(-y,[-.55,.55],['DEF_hips','DEF_spine_mid','DEF_chest'],.55)
    neck=smooth((-y-1.5)/.85)*smooth((z-2.4)/.9)
    nw=blend({'DEF_neck_base':1.},{'DEF_neck_upper':1.},smooth((-y-2.05)/.75))
    w=blend(w,nw,neck)
    headblend=smooth((-y-2.6)/.5)*smooth((z-3.45)/.5)
    w=blend(w,{'DEF_head':1.},headblend)
    if y<-2.5 and z>4.85:
        e=smooth((z-4.85)/.38)*smooth((abs(x)-.1)/.15)
        w=blend(w,{'DEF_ear.'+('L' if x>=0 else 'R'):1.},e)
    return w

tail_segments=[(Vector(a),Vector(b)) for a,b in zip(tail_pts[:-1],tail_pts[1:])]
def tail_weights(p):
    distances=[]
    for i,(a,b) in enumerate(tail_segments):
        t=max(0,min(1,(p-a).dot(b-a)/(b-a).length_squared));distances.append(((p-a-(b-a)*t).length,i,t))
    _,i,t=min(distances)
    # Blend at each joint, not just at the tip. Length coordinate follows curved tail.
    q=i+t
    return sequence(q,[1,2,3,4],['DEF_tail_%02d'%(j+1) for j in range(5)],.38)

def skin_weights(p,objname):
    x,y,z=p;side='L' if x>=0 else 'R'
    if objname=='Object_7':return tail_weights(p)
    if objname=='Object_9':return {'DEF_shoulder.'+side:.68,'DEF_chest':.32}
    if objname=='Object_8':
        kind='front' if y<0 else 'rear'
        return {'DEF_'+kind+'_lower.'+side:1.}
    w=trunk(p)
    # Lower jaw, including its original lower lip. No new jaw geometry.
    jaw=smooth((-y-3.29)/.28)*(1-smooth((z-3.99)/.12))
    if y<-3.28 and z<4.18:w=blend(w,{'DEF_jaw':1.},jaw)
    # The upper tooth strip follows the cranium; lower outlines use surface transfer.
    if objname=='Object_5':return {'DEF_head':1.}
    if objname not in ['Object_6','Object_11']:return w
    if y>1.9 and abs(x)<.29 and z>2.7:
        w=blend(w,tail_weights(p),smooth((y-1.9)/.5))
    fore=smooth((-y-.65)/.4)*(1-smooth((-y-2.0)/.4))
    rear=smooth((y-.72)/.45)
    side_gate=smooth((abs(x)-.18)/.18)
    if fore>rear:
        attach=(1-smooth((z-2.25)/.85))*side_gate*fore
        leg=sequence(-z,[-1.82,-.43,-.13],['DEF_front_upper.'+side,'DEF_front_lower.'+side,'DEF_front_paw.'+side,'DEF_front_toes.'+side],[.34,.20,.08])
        w=blend(w,leg,attach)
        sc=smooth((z-2.25)/.45)*(1-smooth((z-3.05)/.55))*side_gate*fore*.5
        w=blend(w,{'DEF_shoulder.'+side:1.},sc)
    else:
        attach=(1-smooth((z-2.25)/.85))*side_gate*rear
        leg=sequence(-z,[-2.05,-.87,-.25,-.115],['DEF_rear_upper.'+side,'DEF_rear_lower.'+side,'DEF_rear_hock.'+side,'DEF_rear_paw.'+side,'DEF_rear_toes.'+side],[.34,.22,.12,.06])
        w=blend(w,leg,attach)
    return {k:v for k,v in w.items() if v>1e-6}

# Painted shell weights first; transfer onto coincident seams and the outline hull.
painted=[o for o in meshes if o.name not in ['Object_2','Object_3','Object_4']]
weights={o.name:[skin_weights(p,o.name) for p in rest[o.name]] for o in painted}

def components(obj):
    parent=list(range(len(obj.data.vertices)))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(a,b):parent[find(a)]=find(b)
    bins={}
    for v in obj.data.vertices:
        key=tuple(round(c,4) for c in v.co)
        if key in bins:union(v.index,bins[key])
        bins[key]=v.index
    for edge in obj.data.edges:union(*edge.vertices)
    out={}
    for v in obj.data.vertices:out.setdefault(find(v.index),[]).append(v.index)
    return list(out.values())

# Original teeth/tongue are separate islands within Object_11. Never blend
# vertically through a tooth: upper teeth follow skull, lower teeth follow jaw.
rigid_face_ids=set()
obj=bpy.data.objects['Object_11']
for ids in components(obj):
    ps=[rest[obj.name][i] for i in ids]
    if max(p.y for p in ps)<-3.3 and min(p.z for p in ps)>3.8:
        upper=max(p.z for p in ps)>4.22
        for i in ids:weights[obj.name][i]={'DEF_head' if upper else 'DEF_jaw':1.};rigid_face_ids.add(i)

points=[];triangles=[];w_flat=[]
for o in painted:
    start=len(points);points.extend(rest[o.name]);w_flat.extend(weights[o.name]);o.data.calc_loop_triangles()
    triangles.extend([tuple(start+i for i in t.vertices) for t in o.data.loop_triangles])
bvh=BVHTree.FromPolygons(points,triangles,all_triangles=True)

def surface_weight(p):
    q,n,index,distance=bvh.find_nearest(p)
    ids=triangles[index];a,b,c=[points[i] for i in ids]
    bary=barycentric_transform(q,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    bary=[max(0,min(1,v)) for v in bary];total=sum(bary)
    out={}
    for i,amount in zip(ids,bary):
        for name,w in w_flat[i].items():out[name]=out.get(name,0)+w*amount/total
    return out,distance

transfer_max={}
# Smooth the outline's weights across its own connected surface before
# resampling to painted skin. This removes nearest-surface discontinuities at
# curl/body contacts. This is weight-only graph smoothing: no vertex is moved.
hull=bpy.data.objects['Object_2']
transferred=[surface_weight(p) for p in rest[hull.name]]
weights[hull.name]=[w for w,d in transferred]
transfer_max[hull.name]=max(d for w,d in transferred)
neighbors=[{} for _ in hull.data.vertices]
for edge in hull.data.edges:
    i,j=edge.vertices;distance=(rest[hull.name][i]-rest[hull.name][j]).length
    influence=1/max(.025,distance)
    neighbors[i][j]=influence;neighbors[j][i]=influence
for _ in range(6):
    previous=weights[hull.name];new=[]
    for i,adj in enumerate(neighbors):
        if not adj:new.append(previous[i]);continue
        amount=sum(adj.values());mean={}
        for j,a in adj.items():
            for n,w in previous[j].items():mean[n]=mean.get(n,0)+w*a/amount
        new.append(blend(previous[i],mean,.38))
    weights[hull.name]=new

# Resample this common continuous weight field at original painted vertices.
# Keep the separate rigid teeth and tongue away from the outer skin projector.
hull.data.calc_loop_triangles()
hull_tri=[tuple(t.vertices) for t in hull.data.loop_triangles]
hull_bvh=BVHTree.FromPolygons(rest[hull.name],hull_tri,all_triangles=True)
for o in painted:
    if o.name=='Object_5':continue
    for i,p in enumerate(rest[o.name]):
        if o.name=='Object_11' and i in rigid_face_ids:continue
        q,n,index,distance=hull_bvh.find_nearest(p)
        if distance>.16:continue
        ids=hull_tri[index];a,b,c=[rest[hull.name][j] for j in ids]
        bary=barycentric_transform(q,a,b,c,Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
        bary=[max(0,min(1,v)) for v in bary];amount=sum(bary);out={}
        for j,v in zip(ids,bary):
            for name,w in weights[hull.name][j].items():out[name]=out.get(name,0)+w*v/amount
        weights[o.name][i]=out

# Lower-mouth outline pieces are separate original components; follow the jaw.
for name in ['Object_3','Object_4']:
    weights[name]=[{'DEF_jaw':1.} for p in rest[name]]
for o in meshes:
    if o.name not in weights:
        transferred=[surface_weight(p) for p in rest[o.name]]
        weights[o.name]=[w for w,d in transferred];transfer_max[o.name]=max(d for w,d in transferred)
    groups={b.name:o.vertex_groups.new(name=b.name) for b in arm.bones if b.use_deform}
    for i,w in enumerate(weights[o.name]):
        total=sum(w.values());assert total>0
        for n,v in w.items():
            if v>1e-7:groups[n].add([i],v/total,'REPLACE')
    world=o.matrix_world.copy();o.parent=rig;o.matrix_world=world
    mod=o.modifiers.new('Original mesh · quadruped skin (dual quaternion)','ARMATURE')
    mod.object=rig;mod.use_deform_preserve_volume=True
    # Do not apply modifier; no destructive change to rest coordinates.

# Bone collections and useful control shapes.
collections={n:arm.collections.new(n) for n in ['Root and body','Paw IK','Body FK','Head and face','Tail FK','IK poles','Deform (hidden)','Mechanism (hidden)']}
for b in arm.bones:
    cat=controls.get(b.name,'Deform (hidden)' if b.use_deform else 'Mechanism (hidden)')
    collections[cat].assign(b)
for n in ['Deform (hidden)','Mechanism (hidden)']:collections[n].is_visible=False

def shape(name,kind):
    if kind=='ring':
        verts=[(math.cos(i*math.tau/40),0,math.sin(i*math.tau/40)) for i in range(40)];edges=[(i,(i+1)%40) for i in range(40)]
    elif kind=='paw':
        verts=[(-.5,-.2,0),(.5,-.2,0),(.62,.9,0),(.35,1.3,0),(-.35,1.3,0),(-.62,.9,0)];edges=[(i,(i+1)%6) for i in range(6)]
    else:
        verts=[(0,0,-1),(-1,0,0),(0,0,1),(1,0,0),(0,-.4,0),(0,.4,0)];edges=[(0,1),(1,2),(2,3),(3,0),(0,4),(4,2),(0,5),(5,2)]
    me=bpy.data.meshes.new(name);me.from_pydata(verts,edges,[]);ob=bpy.data.objects.new(name,me);shapes_col.objects.link(ob);ob.hide_render=True;ob.hide_set(True);return ob
ring=shape('Shape · ring','ring');pawshape=shape('Shape · paw','paw');diamond=shape('Shape · diamond','diamond')
colors={'Root and body':(1,.65,.15),'Paw IK':(.2,1,.42),'Body FK':(.3,.65,1),'Head and face':(.85,.4,1),'Tail FK':(.15,.85,.8),'IK poles':(1,.4,.2)}
for name,category in controls.items():
    pb=rig.pose.bones[name];pb.rotation_mode='XYZ';pb.custom_shape=ring if category in ['Root and body','Body FK','Tail FK'] else pawshape if name.startswith('CTRL_paw_') else diamond
    size=1.9 if name=='CTRL_root' else 1.1 if name=='CTRL_body' else .43 if category=='Body FK' else .40 if name.startswith('CTRL_paw_') else .17 if 'toes' in name or 'ear' in name else .28
    pb.use_custom_shape_bone_size=False;pb.custom_shape_scale_xyz=(size,size,size)
    pb.color.palette='CUSTOM';pb.color.custom.normal=colors[category];pb.color.custom.select=(1,.85,.35);pb.color.custom.active=(1,1,.6)
    pb.lock_scale=(True,True,True)
    if category in ['Body FK','Tail FK','Head and face'] or name.startswith('CTRL_toes_'):pb.lock_location=(True,True,True)
    pb['Help']='Rotate this control' if all(pb.lock_location) else 'G move / R rotate. Alt+G and Alt+R restore neutral.'
rig.pose.bones['CTRL_jaw']['Help']='Small LOCAL X rotation opens/closes original jaw. Original mouth is slightly open at rest. No mouth interior was added.'

# Pack every original image. Use the original node graphs and original UVs.
for image in bpy.data.images:
    if image.source=='FILE':image.pack()

def reset():
    for pb in rig.pose.bones:
        pb.location=(0,0,0);pb.rotation_mode='XYZ';pb.rotation_euler=(0,0,0);pb.scale=(1,1,1)
    bpy.context.view_layer.update()

def local_move(name,world_delta):
    pb=rig.pose.bones[name];m=pb.matrix.copy();m.translation+=Vector(world_delta);pb.matrix=m;bpy.context.view_layer.update()
def rotate(name,angles):
    rig.pose.bones[name].rotation_euler=[math.radians(v) for v in angles];bpy.context.view_layer.update()

reset()
deps=bpy.context.evaluated_depsgraph_get()
neutral_error={}
for o in meshes:
    ev=o.evaluated_get(deps);em=ev.to_mesh()
    neutral_error[o.name]=max((ev.matrix_world@v.co-p).length for v,p in zip(em.vertices,rest[o.name]));ev.to_mesh_clear()
    assert fingerprint(o)==fingerprints[o.name],o.name
assert max(neutral_error.values())<.001,neutral_error
assert not bpy.data.actions[:]

# Studio is separate and hidden from ordinary viewport; source materials intact.
world=bpy.data.worlds.new('Neutral warm studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.65,.65,.65,1);world.node_tree.nodes['Background'].inputs[1].default_value=.6;scene.world=world
def link_studio(o):
    for c in list(o.users_collection):c.objects.unlink(o)
    studio_col.objects.link(o)
def area(name,loc,power,size):
    data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size
    ob=bpy.data.objects.new(name,data);studio_col.objects.link(ob);ob.location=loc;ob.rotation_euler=(Vector((0,0,2.5))-ob.location).to_track_quat('-Z','Y').to_euler();return ob
area('Key softbox',(5,-6,9),1250,7);area('Fill softbox',(-5,-1,5),900,6);area('Rim softbox',(1,6,7),1200,5)
camdata=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',camdata);studio_col.objects.link(cam);scene.camera=cam
def camera(position,target,scale=10):
    cam.location=position;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();camdata.type='ORTHO';camdata.ortho_scale=scale
camera((11,-10,7),(0,0,2.6),10)
scene.render.engine='CYCLES'
# Cycles ignores material backface-culling; use Eevee to match approved outline rendering.
scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=1280;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast';scene.view_settings.exposure=0;scene.view_settings.gamma=1

notes='''ORIGINAL SKETCHFAB WOLF — RIG REVIEW (no animation cycles)

Original uploaded geometry, UVs, split normals, textures and shader graphs preserved.
An inward black outline shell is intentional. Front-face culling matches the
approved browser viewer; do not recalculate its normals or remove original parts.

OPEN / POSE
Select WOLF_RIG in the Outliner, then Ctrl+Tab > Pose Mode.
Gold CTRL_root moves everything. CTRL_body moves torso with paws planted.
Green CTRL_paw_front/rear.L/R: G places paw, R sets orientation.
Orange CTRL_pole controls elbow/knee bend direction.
Blue hips/spine/chest/shoulder/neck: rotate for body posing.
Purple head/jaw/ears: rotate; jaw uses LOCAL X, small angles.
Teal tail_01..05: FK rotations along the whole curved original tail.
CTRL_toes: toe flex. Scale is locked to prevent accidental mesh distortion.
Clear a pose: select all controls in Pose Mode, Alt+G, Alt+R, Alt+S.

TEXTURES
All original images are packed. Z > Material Preview displays original paint.
If you see only grey use Material Preview, not Solid viewport shading.
The Preview studio collection is independent of the wolf and is optional.

The original is low-poly and has thin ornamental curls/overlapping parts.
This rig preserves that topology; extreme joint compression or large jaw poses
need additional review. No retopology, subdivision, new mouth interior or fur
geometry has been added. Original mouth is slightly open at rest.
No Idle/Walk/Run or other animation actions were authored.

Source: Amaterasu the Japanese Fox God by theamazingdonovan207, CC BY 4.0.
https://sketchfab.com/3d-models/amaterasu-the-japanese-fox-god-6d64c6b79c0942a086cad6d988e35712
'''
text=bpy.data.texts.new('START HERE — posing and preservation');text.write(notes)
(ROOT/'OPEN-IN-BLENDER.txt').write_text(notes)

report={'source_files_sha256':texture_proof,'mesh_fingerprints':fingerprints,'mesh_count':len(meshes),'deform_bones':sum(b.use_deform for b in arm.bones),'control_bones':len(controls),'neutral_max_displacement':neutral_error,'ik_rest_calibration':calibration,'ink_weight_transfer_max_distance':transfer_max,'packed_images':[i.name for i in bpy.data.images if i.packed_file],'animations':len(bpy.data.actions),'limitations':['Original low-poly topology retained, no added bend loops or mouth interior.','Temporary test poses are not animation cycles.','Large jaw openings are outside this initial rig review.']}

def render(name,view='three'):
    if os.environ.get('RIG_TEST_FAST')=='1':return
    if view=='side':camera((14,0,3.8),(0,0,2.65),10)
    elif view=='front':camera((0,-15,4),(0,-.5,2.65),8.4)
    elif view=='other':camera((-11,-10,7),(0,0,2.6),10)
    else:camera((11,-10,7),(0,0,2.6),10)
    scene.render.filepath=str(ROOT/'review'/f'{name}.png');bpy.ops.render.render(write_still=True)

def pose_metrics(name):
    deps=bpy.context.evaluated_depsgraph_get();maximum=0;min_ratio=1;max_ratio=1;flipped=0
    for o in meshes:
        ev=o.evaluated_get(deps);em=ev.to_mesh();vs=[ev.matrix_world@v.co for v in em.vertices]
        assert len(vs)==len(rest[o.name]);assert all(math.isfinite(c) for v in vs for c in v)
        for edge in o.data.edges:
            a,b=edge.vertices;l0=(rest[o.name][a]-rest[o.name][b]).length;l1=(vs[a]-vs[b]).length
            if l0>.04:min_ratio=min(min_ratio,l1/l0);max_ratio=max(max_ratio,l1/l0)
        maximum=max(maximum,max((v-p).length for v,p in zip(vs,rest[o.name])));ev.to_mesh_clear()
    paw_error={}
    for tag,item in leg_specs.items():
        p=rig.pose.bones['DEF_'+item['kind']+'_lower.'+item['side']].tail
        target=rig.pose.bones[item['target']].head;paw_error[tag]=(p-target).length
    return {'pose':name,'max_displacement':maximum,'edge_ratio_range':[min_ratio,max_ratio],'ik_target_errors':paw_error}

tests=[]
render('neutral-three');render('neutral-side','side');render('neutral-front','front')
tests.append(pose_metrics('Neutral'))
local_move('CTRL_body',(0,0,-.30));rotate('CTRL_neck_base',(8,0,0));rotate('CTRL_head',(-8,0,0));tests.append(pose_metrics('Body lowered with planted paws'));render('crouch-three');render('crouch-other','other');reset()
local_move('CTRL_paw_front.L',(0,-.5,.52));rotate('CTRL_shoulder.L',(0,0,-6));local_move('CTRL_paw_rear.R',(0,.3,.22));tests.append(pose_metrics('Opposing paw lift'));render('paw-lift-three');render('paw-lift-side','side');reset()
rotate('CTRL_head',(7,-12,15));rotate('CTRL_neck_upper',(-4,0,-8));rotate('CTRL_jaw',(9,0,0));tests.append(pose_metrics('Head turn and small jaw opening'));render('head-jaw-three');render('head-jaw-other','other');reset()
for i in range(5):rotate('CTRL_tail_%02d'%(i+1),(0,4 if i%2==0 else -3,9))
rotate('CTRL_chest',(0,0,5));rotate('CTRL_spine_mid',(0,0,-5));tests.append(pose_metrics('Tail and spine articulation'));render('tail-spine-three');reset()

report['temporary_pose_tests']=tests
assert all(max(t['ik_target_errors'].values())<.001 for t in tests),tests
# Compression along the inside of a bent joint is expected. Flag severe
# collapsed/stretched edges, including outline-shell discontinuities.
assert all(t['edge_ratio_range'][0]>.35 and t['edge_ratio_range'][1]<1.8 for t in tests),tests
report['source_unchanged']=all(hashlib.sha256((SOURCE/p).read_bytes()).hexdigest()==h for p,h in texture_proof.items())
assert report['source_unchanged']
for o in meshes:assert fingerprint(o)==fingerprints[o.name]
assert len(bpy.data.actions)==0
camera((11,-10,7),(0,0,2.6),10)
for o in scene.objects:o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
# Open straight into a useful textured, framed model/rig view on Windows.
from mathutils import Quaternion
for screen in bpy.data.screens:
    for a in screen.areas:
        if a.type=='VIEW_3D':
            space=a.spaces.active;space.shading.type='MATERIAL';space.clip_end=1000
            space.overlay.show_floor=False;space.overlay.show_axis_x=False;space.overlay.show_axis_y=False
            space.region_3d.view_distance=11;space.region_3d.view_location=(0,0,2.7)
            space.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
        elif a.type=='PROPERTIES':a.spaces.active.context='DATA'
for o in studio_col.objects:o.hide_set(True)
bpy.ops.object.mode_set(mode='POSE')
for b in arm.bones:b.select=False
arm.bones.active=arm.bones['CTRL_body'];arm.bones['CTRL_body'].select=True
scene.frame_start=1;scene.frame_end=120;scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Original-Sketchfab-Wolf-Rig.blend'))
(ROOT/'review'/'rig-validation.json').write_text(json.dumps(report,indent=2))
print('RIG_COMPLETE',json.dumps({'neutral_max':max(neutral_error.values()),'pose_tests':len(tests),'file':str(ROOT/'Original-Sketchfab-Wolf-Rig.blend')}))
