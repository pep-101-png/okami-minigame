"""Inspect raw FBX unit/container curves without Blender's compensating import transform."""
import bpy,json,hashlib
from pathlib import Path
from io_scene_fbx import parse_fbx
R=Path(__file__).resolve().parents[1];p=R/'Assets/Sunward/Models/Amaterasu.fbx';root,_=parse_fbx.parse(str(p));objects=next(e for e in root.elems if e.id==b'Objects');connections=next(e for e in root.elems if e.id==b'Connections');byid={e.props[0]:e for e in objects.elems};rigids={i for i,e in byid.items()if e.id==b'Model'and e.props[1].split(b'\x00')[0]==b'WOLF_RIG'};scale_nodes={e.props[1] for e in connections.elems if e.props[0]==b'OP' and e.props[2]in rigids and e.props[3]==b'Lcl Scaling'};curves=[]
for e in connections.elems:
 if e.props[0]!=b'OP' or e.props[2]not in scale_nodes:continue
 curve=byid[e.props[1]];values=list(next(x for x in curve.elems if x.id==b'KeyValueFloat').props[0]);curves.append({'axis':e.props[3].decode(),'minimum':min(values),'maximum':max(values),'keys':len(values)})
report={'fbx_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'animation_stacks':sum(e.id==b'AnimationStack'for e in objects.elems),'rig_container_scale_curves':len(curves),'container_scale_values':sorted({c['minimum']for c in curves}|{c['maximum']for c in curves}),'all_container_curves_constant_100':bool(curves)and all(c['minimum']==100 and c['maximum']==100 for c in curves),'blender_import_caveat':'Blender compensates these object curves to scale 1 during FBX import; bone-only validation missed the raw 100 values. Unity user reported rest scale 1 and animated scale 100.','repair':'Keep source FBX untouched. Generate native .anim copies without container-only local-scale channels, preserving all bone channels and original imported clips.'}
assert report['animation_stacks']==47 and report['all_container_curves_constant_100'];(R/'Review/raw-fbx-scale-audit.json').write_text(json.dumps(report,indent=2));print('RAW_FBX_SCALE_AUDIT',json.dumps(report),flush=True)
