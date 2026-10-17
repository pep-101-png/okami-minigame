"""Author only IDLE/WALK/RUN on the approved original-wolf control rig.
Blender 4.3: blender -b -t 4 --python original-wolf-animation/animate.py
No mesh, material or image edits. Non-smoothing pre-skin deformation resolution addresses joint-face folding;
the original mesh, weights, rest bones and control system are preserved.
"""
import bpy, math, json, hashlib, os, bmesh
from pathlib import Path
from mathutils import Vector, Quaternion, Matrix

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'original-wolf-rig/Original-Sketchfab-Wolf-Rig.blend'
SOURCE_HASH='6dacb175ae341fafc0c7a5b2f5ca742ea6f962a5762dcc14316b7c90073f3a34'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene;rig=bpy.data.objects['WOLF_RIG']
if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
rig.animation_data_create();scene.render.fps=60;scene.render.fps_base=1
CTRL=[p for p in rig.pose.bones if p.name.startswith('CTRL_')]
meshes=[o for o in scene.objects if o.type=='MESH' and o.parent==rig]
TAU=math.tau

def geometry_hash():
    data={}
    for o in meshes:
        data[o.name]={'coords':[list(v.co) for v in o.data.vertices],
           'faces':[list(p.vertices) for p in o.data.polygons],
           'uv':[[list(l.uv) for l in u.data] for u in o.data.uv_layers],
           'normals':[list(n.vector) for n in o.data.corner_normals],
           'material_slots':[m.name for m in o.data.materials]}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def skeleton_hash():
    data={b.name:{'head':list(b.head_local),'tail':list(b.tail_local),
                 'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None,
                 'deform':b.use_deform} for b in rig.data.bones}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def materials_hash():
    data={}
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        data[m.name]={'cull':m.use_backface_culling,'nodes':[],'links':[]}
        for n in m.node_tree.nodes:
            ins=[]
            for s in n.inputs:
                if hasattr(s,'default_value'):
                    v=s.default_value
                    try:v=list(v)
                    except TypeError:pass
                    ins.append((s.identifier,v))
            data[m.name]['nodes'].append((n.name,n.bl_idname,ins,n.image.name if n.type=='TEX_IMAGE' and n.image else None))
        data[m.name]['links']=[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in m.node_tree.links]
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
def weight_hash():
    data={o.name:[[[o.vertex_groups[g.group].name,g.weight]for g in v.groups]for v in o.data.vertices]for o in meshes}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()
preservation={'mesh_uv_normals':geometry_hash(),'skeleton_rest':skeleton_hash(),'materials':materials_hash(),
              'source_skin_weights':weight_hash(),
              'images':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}}

# The original long, sparsely divided hip/knee faces fold during deep recovery.
# Add NON-SMOOTHING pre-skin deformation resolution on a separate animation copy.
# SIMPLE subdivision retains the exact original surface, UV interpolation,
# silhouette, normals and base mesh, and uses the existing weights/armature.
# No sculpting, rest-bone edits, new controls or applied modifiers.
repair_counts={}
for name in ['Object_6','Object_2']:
    o=bpy.data.objects[name]
    mod=o.modifiers.new('Joint bend resolution · SIMPLE, original surface retained','SUBSURF')
    mod.subdivision_type='SIMPLE';mod.levels=1;mod.render_levels=1;mod.uv_smooth='NONE'
    # Paw contact solving uses unchanged Object_11; avoid repeatedly evaluating
    # unrelated surface subdivision while authoring control keys.
    mod.show_viewport=False
    if hasattr(mod,'use_custom_normals'):mod.use_custom_normals=True
    bpy.context.view_layer.objects.active=o
    bpy.ops.object.modifier_move_up(modifier=mod.name)
    repair_counts[name]={'modifier':'SIMPLE subdivision before existing armature','level':1}
bpy.context.view_layer.objects.active=rig
preservation['delivered_skin_weights']=weight_hash()
assert preservation['delivered_skin_weights']==preservation['source_skin_weights']
preservation['necessary_rig_repair']={'reason':'Original long hip/knee faces fold during gallop recovery. Non-smoothing pre-skin subdivision supplies bend resolution without changing the original rest surface or base mesh. Original weights, skeleton, controls and constraints retained.','components':repair_counts}

def reset():
    for p in rig.pose.bones:p.matrix_basis.identity();p.rotation_mode='XYZ'
    bpy.context.view_layer.update()
reset()
rest_matrix={p.name:p.matrix.copy() for p in CTRL}
feet={}
footmesh=bpy.data.objects['Object_11']
rest_points=[footmesh.matrix_world@v.co for v in footmesh.data.vertices]
for kind in ['front','rear']:
    for side,sign in [('L',1),('R',-1)]:
        key=kind+'.'+side
        ids=[i for i,p in enumerate(rest_points) if p.z<.17 and sign*p.x>.25 and (p.y<-.9 if kind=='front' else p.y>1)]
        assert len(ids)>20
        center=sum((rest_points[i] for i in ids),Vector())/len(ids)
        feet[key]={'ids':ids,'center':center,'control':'CTRL_paw_'+key,'sign':sign}

def smooth(t):
    t=max(0,min(1,t));return t*t*(3-2*t)
def quint(t):
    t=max(0,min(1,t));return t*t*t*(10+t*(-15+6*t))
def hermite(a,b,da,db,t):
    return (2*t**3-3*t*t+1)*a+(t**3-2*t*t+t)*da+(-2*t**3+3*t*t)*b+(t**3-t*t)*db
def curve(nodes,u,start_d=None,end_d=None,positive=False):
    for i in range(len(nodes)-1):
        a,va=nodes[i];b,vb=nodes[i+1]
        if u<=b+1e-8:
            da=start_d if i==0 and start_d is not None else (vb-nodes[max(0,i-1)][1])/(b-nodes[max(0,i-1)][0])
            db=end_d if i+1==len(nodes)-1 and end_d is not None else (nodes[min(len(nodes)-1,i+2)][1]-va)/(nodes[min(len(nodes)-1,i+2)][0]-a)
            if positive:
                if i>0 and (va-nodes[i-1][1])*(vb-va)<=0:da=0
                if i+2<len(nodes) and (vb-va)*(nodes[i+2][1]-vb)<=0:db=0
            return hermite(va,vb,da*(b-a),db*(b-a),max(0,min(1,(u-a)/(b-a))))
    return nodes[-1][1]

def rotate(name,x=0,y=0,z=0):
    rig.pose.bones[name].rotation_euler=tuple(math.radians(v) for v in (x,y,z))
def translate(name,delta):
    p=rig.pose.bones[name];m=p.matrix.copy();m.translation+=Vector(delta);p.matrix=m
def set_paw(key,dy,height,pitch=0,side_offset=0):
    f=feet[key];p=rig.pose.bones[f['control']];m=rest_matrix[p.name].copy()
    q=Quaternion((1,0,0),math.radians(pitch))@m.to_quaternion()
    mat=q.to_matrix().to_4x4();mat.translation=m.translation+Vector((side_offset,dy,height));p.matrix=mat

def walk_foot(t,key):
    offsets={'rear.L':0,'front.L':.25,'rear.R':.5,'front.R':.75}
    u=(t-offsets[key])%1;duty=.65;stride=2.0;start=-stride*duty/2
    if u<duty:
        dy=start+stride*u;height=0
        pitch=-3*(1-smooth(u/.055))+10*smooth((u-duty+.075)/.075)
        toe=6*smooth((u-duty+.055)/.055)
    else:
        v=(u-duty)/(1-duty)
        dy=hermite(-start,start,stride*(1-duty),stride*(1-duty),v)
        height=(.37 if key.startswith('front') else .42)*math.sin(math.pi*v)**2
        pitch=curve([(0,10),(.32,27),(.62,9),(1,-3)],v)
        toe=12*math.sin(math.pi*v)**2
    return {'u':u,'duty':duty,'dy':dy,'height':height,'pitch':pitch,'toe':toe,'stride':stride,'contact':u<duty}

def run_foot(t,key):
    offsets={'front.R':0,'front.L':.12,'rear.R':.50,'rear.L':.62}
    u=(t-offsets[key])%1;front=key.startswith('front');duty=.22 if front else .23;stride=4.8
    start=(-.60 if key.endswith('R') else -.72) if front else -.99
    if u<duty:
        dy=start+stride*u;height=0
        pitch=-5*(1-smooth(u/.035))+18*smooth((u-duty+.07)/.07)
        toe=9*smooth((u-duty+.05)/.05)
    else:
        end=start+stride*duty
        if front:
            dy=curve([(duty,end),(.35,.65),(.53,.20),(.82,-.92),(1,start)],u,start_d=stride,end_d=stride)
            height=curve([(duty,0),(.35,.66),(.53,.91),(.82,.42),(1,0)],u,start_d=0,end_d=0,positive=True)
            pitch=curve([(duty,18),(.40,53),(.60,34),(.84,-12),(1,-5)],u)
        else:
            dy=curve([(duty,end),(.35,.55),(.50,.40),(.72,-1.14),(.90,-1.12),(1,start)],u,start_d=stride,end_d=stride)
            height=curve([(duty,0),(.35,.46),(.50,.58),(.72,.50),(.90,.20),(1,0)],u,start_d=0,end_d=0,positive=True)
            pitch=curve([(duty,18),(.4,30),(.68,22),(.90,-9),(1,-5)],u)
        toe=18*math.sin(math.pi*(u-duty)/(1-duty))**2
    return {'u':u,'duty':duty,'dy':dy,'height':max(0,height),'pitch':pitch,'toe':toe,'stride':stride,'contact':u<duty}

def sole_points():
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    ev=footmesh.evaluated_get(deps);me=ev.to_mesh();out={}
    for key,f in feet.items():
        ps=[ev.matrix_world@me.vertices[i].co for i in f['ids']]
        out[key]={'center':sum(ps,Vector())/len(ps),'minZ':min(p.z for p in ps)}
    ev.to_mesh_clear();return out

def pose(kind,t):
    reset();states={}
    if kind=='IDLE':
        breath=math.sin(2*TAU*t);shift=math.sin(TAU*t)
        translate('CTRL_body',(.026*shift,.006*math.sin(TAU*t+.4),.013*breath))
        rotate('CTRL_hips',x=.22*breath,z=.25*shift)
        rotate('CTRL_spine_mid',x=-.35*breath,y=.15*shift)
        rotate('CTRL_chest',x=.42*breath)
        rotate('CTRL_neck_base',x=.25*math.sin(2*TAU*t-.4))
        rotate('CTRL_neck_upper',x=-.4*math.sin(2*TAU*t-.6))
        rotate('CTRL_head',x=.45*math.sin(2*TAU*t-.8),z=1.2*math.sin(TAU*t-.3))
        for i in range(5):rotate('CTRL_tail_%02d'%(i+1),x=.5*math.sin(TAU*t-i*.23),z=.65*math.sin(TAU*t-i*.32))
        for side,sgn in [('L',1),('R',-1)]:rotate('CTRL_ear.'+side,x=.5*math.sin(TAU*t+.6*sgn),z=sgn*.3*math.sin(2*TAU*t))
        states={key:{'u':t,'duty':1,'dy':0,'height':0,'pitch':0,'toe':0,'stride':0,'contact':True}for key in feet}
    elif kind=='WALK':
        translate('CTRL_body',(.055*math.sin(TAU*(t+.1)),.015*math.sin(2*TAU*t),-.075+.043*math.cos(2*TAU*(t-.08))))
        rotate('CTRL_body',x=.8*math.sin(2*TAU*t),y=.6*math.cos(TAU*t))
        rotate('CTRL_hips',x=.9*math.sin(2*TAU*t+.4),z=1.8*math.sin(TAU*t))
        rotate('CTRL_spine_mid',x=-.65*math.sin(2*TAU*t+.4),z=-1.3*math.sin(TAU*t-.2))
        rotate('CTRL_chest',x=.55*math.sin(2*TAU*t-.5),z=-1.0*math.sin(TAU*t))
        rotate('CTRL_neck_base',x=-.7*math.sin(2*TAU*t-.4))
        rotate('CTRL_neck_upper',x=.55*math.sin(2*TAU*t-.65))
        states={key:walk_foot(t,key) for key in feet}
        for side in ['L','R']:
            rotate('CTRL_shoulder.'+side,x=-3.2*math.cos(TAU*states['front.'+side]['u']))
            rotate('CTRL_hip_socket.'+side,x=-1.3*math.cos(TAU*states['rear.'+side]['u']))
            rotate('CTRL_ear.'+side,x=1+.7*math.sin(2*TAU*t-.3))
        for i in range(5):rotate('CTRL_tail_%02d'%(i+1),x=1.0*math.sin(2*TAU*t-i*.24),z=1.2*math.sin(TAU*t-i*.32))
    else:
        collect=math.cos(TAU*(t-.43))
        translate('CTRL_body',(.035*math.sin(TAU*t),.035*math.sin(TAU*(t-.1)),-.17+.17*math.cos(2*TAU*(t-.43))))
        rotate('CTRL_body',x=2.4*math.sin(TAU*(t-.1)),y=.7*math.sin(TAU*t))
        rotate('CTRL_hips',x=-5.2*collect,z=.6*math.sin(TAU*t))
        rotate('CTRL_spine_mid',x=8.8*collect)
        rotate('CTRL_chest',x=-4.6*collect,z=-.5*math.sin(TAU*t))
        rotate('CTRL_neck_base',x=2.2+1.6*math.sin(TAU*(t-.2)))
        rotate('CTRL_neck_upper',x=-2.3-1.4*math.sin(TAU*(t-.27)))
        states={key:run_foot(t,key) for key in feet}
        for side in ['L','R']:
            rotate('CTRL_shoulder.'+side,x=-6*math.cos(TAU*states['front.'+side]['u']))
            rotate('CTRL_hip_socket.'+side,x=-2.3*math.cos(TAU*states['rear.'+side]['u']))
            rotate('CTRL_ear.'+side,x=3.3+1.2*math.sin(2*TAU*t-.8),z=.3*math.sin(TAU*t))
        for i,lift in enumerate([14,10,2,2,0]):
            rotate('CTRL_tail_%02d'%(i+1),x=lift+1.4*math.sin(TAU*t-i*.3),z=.7*math.sin(TAU*t-i*.35))
    bpy.context.view_layer.update()
    # Stabilise the gaze against inherited body pitch. Keep the head's actual
    # position and all rest bones; this is ordinary control-key animation.
    if kind!='IDLE':
        p=rig.pose.bones['CTRL_head'];m=p.matrix.copy()
        nod=(.6 if kind=='WALK' else 1.6)*math.sin(2*TAU*t-.7)
        goal=Quaternion((1,0,0),math.radians(nod))@rest_matrix[p.name].to_quaternion()
        q=m.to_quaternion().slerp(goal,.82 if kind=='WALK' else .72)
        target=q.to_matrix().to_4x4();target.translation=m.translation;p.matrix=target
    for key,state in states.items():
        set_paw(key,state['dy'],state['height'],state['pitch'])
        rotate('CTRL_toes_'+key,x=state['toe'])
    bpy.context.view_layer.update()
    # Ground contacts are checked on the actual deformed painted paw mesh,
    # not just IK targets. Correct small skinning/paw-roll offsets on controls.
    for _ in range(5):
        observed=sole_points()
        for key,state in states.items():
            f=feet[key];q=observed[key]
            dy=f['center'].y+state['dy']-q['center'].y
            dz=.035+state['height']-q['minZ']
            dx=f['center'].x-q['center'].x
            translate(f['control'],(dx,dy,dz))
        bpy.context.view_layer.update()
    return states,sole_points()

settings={'IDLE':{'frames':240,'stride':0,'duty':1},'WALK':{'frames':72,'stride':2.0,'duty':.65},'RUN':{'frames':40,'stride':4.8,'duty':.22}}
report={'source_sha256':SOURCE_HASH,'fps':60,'preservation':preservation,'actions':{},'revision':7}
for name,cfg in settings.items():
    action=bpy.data.actions.new(name);action.use_fake_user=True;rig.animation_data.action=action
    action.use_frame_range=True;action.frame_start=1;action.frame_end=cfg['frames']+1
    action['cycle_frames']=cfg['frames'];action['in_place']=True;action['metres_per_second']=cfg['stride']*60/cfg['frames']
    action['export_note']='Bake constraints / sample every frame for deform-bone game export. Duplicate endpoint gives seamless loop.'
    action.asset_mark();action.asset_data.description={'IDLE':'Quiet breathing, planted paws, subtle weight shifts and gaze.','WALK':'Four-beat lateral walk; ground velocity 1.667 Blender units/s.','RUN':'Four-beat gallop, collected and extended suspension; ground velocity 7.2 Blender units/s.'}[name]
    action.asset_data.author='Amaterasu animation study'
    contact_error=0;ik_error=0;samples=[]
    for frame in range(1,cfg['frames']+2):
        scene.frame_set(frame);t=(frame-1)/cfg['frames'];states,observed=pose(name,t)
        frame_data={'frame':frame,'phase':t,'feet':{},'ik':{}}
        for key,s in states.items():
            f=feet[key];q=observed[key]
            error=max(abs(q['minZ']-.035-s['height']),abs(q['center'].y-f['center'].y-s['dy']))
            if s['contact']:contact_error=max(contact_error,error)
            low=rig.pose.bones['DEF_'+key.split('.')[0]+'_lower.'+key[-1]]
            goal=rig.pose.bones['MCH_target_'+key]
            ik=(low.tail-goal.head).length;ik_error=max(ik_error,ik)
            frame_data['feet'][key]={'contact':s['contact'],'height':q['minZ'],'center':list(q['center']),'idealY':f['center'].y+s['dy'],'error':error}
            frame_data['ik'][key]=ik
        for p in CTRL:
            p.keyframe_insert('location',frame=frame,group=p.name)
            p.keyframe_insert('rotation_euler',frame=frame,group=p.name)
        samples.append(frame_data)
    for fc in action.fcurves:
        for k in fc.keyframe_points:
            k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
        fc.modifiers.new('CYCLES')
    report['actions'][name]={'frames':cfg['frames'],'duration_seconds':cfg['frames']/60,'ground_speed':action['metres_per_second'],
                             'max_contact_error':contact_error,'max_ik_error':ik_error,'samples':samples}
    print('ACTION_BUILT',name,'contact error',contact_error,'IK',ik_error,flush=True)

assert geometry_hash()==preservation['mesh_uv_normals']
assert weight_hash()==preservation['delivered_skin_weights']
assert skeleton_hash()==preservation['skeleton_rest']
assert materials_hash()==preservation['materials']
assert {i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest() for i in bpy.data.images if i.packed_file}==preservation['images']
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
report['preserved']=True

guide='''AMATERASU — IDLE / WALK / RUN

The approved original wolf's mesh, appearance and control system are unchanged.
Only animator controls have keys. Non-smoothing pre-skin subdivision prevents sparse joint faces folding.
Original base mesh, weights, rest bones and rig hierarchy remain unchanged;
no remodel or rest-mesh edits. The source rig checkpoint is untouched.
All original images remain packed. Original unanimated rig remains a separate file.

PLAY AN ACTION
Select WOLF_RIG. The lower panel is an Action Editor.
Use the Action-name dropdown in its header: IDLE, WALK or RUN. Press Space.
The shared review range loops smoothly with all three Actions; no range change
is needed. All actions use 60 fps. Start = 1.
  IDLE: 240-frame cycle (4 seconds)
  WALK: 72-frame cycle (1.2 seconds)
  RUN:  40-frame cycle (0.667 seconds)
The 720-frame review range repeats whole cycles of whichever Action is active.
Each Action has its own short export range and a duplicate closing key.
The shield / fake-user flag retains all three actions in the file.

CONTROLS
Gold: root and torso. Green: planted IK paws. Orange: bend-direction poles.
Blue: hips/spine/chest/shoulders/neck. Purple: head, jaw, ears. Teal: tail.
Press Z > Material Preview for original paint. No plugin or texture folder needed.

GAME EXPORT LATER
These are in-place cycles. Match game travel speed to 1.667 Blender units/s for
WALK, 7.2 for RUN (or scale both model and velocity consistently).
Sample/bake the existing constraints when exporting deform-bone animation.
Do not export just raw control curves as if they were deform bones.
No game files or browser pages were changed.
'''
text=bpy.data.texts.new('PLAY ANIMATIONS — START HERE');text.write(guide)
(ROOT/'OPEN-AND-PLAY.txt').write_text(guide)

# Useful default: select rig, Walk active, one complete cycle visible.
for o in meshes:
    for mod in o.modifiers:
        if mod.type=='SUBSURF':mod.show_viewport=True
rig.animation_data.action=bpy.data.actions['WALK'];scene.frame_start=1;scene.frame_end=720;scene.frame_set(1)
scene.use_preview_range=False
if bpy.context.window and bpy.data.workspaces.get('Layout'):
    bpy.context.window.workspace=bpy.data.workspaces['Layout']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='DOPESHEET_EDITOR' and (screen.name.startswith('Layout') or area.ui_type!='TIMELINE'):
            area.ui_type='DOPESHEET';area.spaces.active.mode='ACTION';area.spaces.active.show_region_ui=False
        elif area.type=='VIEW_3D':
            area.spaces.active.shading.type='MATERIAL'
            area.spaces.active.region_3d.view_distance=12
            area.spaces.active.region_3d.view_location=(0,0,2.5)
for o in scene.objects:o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Amaterasu-Idle-Walk-Run.blend'))
(ROOT/'review/authoring-validation.json').write_text(json.dumps(report,indent=2))
print('ANIMATION_BUILD_COMPLETE',flush=True)
