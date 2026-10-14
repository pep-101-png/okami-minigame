"""Check the exported model, not just the Blender authoring scene."""
import bpy,bmesh,json,struct,math
from pathlib import Path
root=Path(__file__).resolve().parent
blob=(root/'wolf.glb').read_bytes();magic,version,size=struct.unpack_from('<III',blob);assert magic==0x46546C67 and version==2 and size==len(blob)
length=struct.unpack_from('<I',blob,12)[0];document=json.loads(blob[20:20+length]);assert {'Idle','Walk'}=={a['name'] for a in document['animations']};assert all('bufferView' in image for image in document['images'])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False);bpy.ops.import_scene.gltf(filepath=str(root/'wolf.glb'))
rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');mesh=next(o for o in bpy.context.scene.objects if o.type=='MESH');bm=bmesh.new();bm.from_mesh(mesh.data)
for v in bm.verts:v.co=mesh.matrix_world@v.co
volume=abs(bm.calc_volume());assert volume>9,('Body lost in export',volume);assert min(v.co.z for v in bm.verts)<.1;assert max(v.co.z for v in bm.verts)>5;bm.free()
assert {'hips','chest','neck','head','tail','tailTip'}<=set(rig.pose.bones.keys())
action=next(a for a in bpy.data.actions if 'Walk' in a.name);rig.animation_data.action=action;start,end=action.frame_range;period=end-start;assert abs(period-48)<.01
phases={('fore','L'):0,('hind','R'):.25,('fore','R'):.5,('hind','L'):.75};max_contact_error=0;max_bend=0
for i in range(49):
 frame=start+i;bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update()
 for (leg,side),offset in phases.items():
  phase=(i/48+offset)%1;paw=rig.pose.bones[leg+'Paw'+side];ankle=rig.matrix_world@paw.head
  if phase<.62:max_contact_error=max(max_contact_error,abs(ankle.z-(.46 if leg=='fore' else .68)))
  max_bend=max(max_bend,rig.pose.bones[leg+'Shin'+side].matrix_basis.to_quaternion().angle)
assert max_contact_error<.035,('Ground contact drift',max_contact_error);assert max_bend>.6,('Insufficient joint articulation',max_bend)
poses=[]
for frame in [start,end]:
 bpy.context.scene.frame_set(int(frame),subframe=frame-int(frame));bpy.context.view_layer.update();poses.append({b.name:b.matrix.copy() for b in rig.pose.bones})
loop_error=max(abs(poses[0][name][i][j]-poses[1][name][i][j]) for name in poses[0] for i in range(4) for j in range(4));assert loop_error<.002,('Loop discontinuity',loop_error)
print(json.dumps({'body_volume':round(volume,4),'skin_joints':len(document['skins'][0]['joints']),'clips':['Idle','Walk'],'contact_error':round(max_contact_error,6),'max_joint_bend_degrees':round(math.degrees(max_bend),2),'loop_error':round(loop_error,6),'embedded_images':len(document['images'])},indent=2))
