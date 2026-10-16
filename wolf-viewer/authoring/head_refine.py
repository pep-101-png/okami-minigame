"""A restrained head-length and ear-size pass, preserving the approved body.

Run after anchor_fur and before fur_finish. Repeating the pass reloads its
saved input, so revisions never accumulate stretch or change body topology.
"""
from pathlib import Path
import bpy, json, numpy as np

root = Path(__file__).resolve().parents[1]
draft = root / 'review/drafts'
bpy.ops.wm.open_mainfile(filepath=str(draft / 'run-candidate.blend'))
coat = bpy.data.objects['Wolf ivory coat']
if coat.get('head_refined'):
    bpy.ops.wm.open_mainfile(filepath=str(draft / 'head-paint-source.blend'))
    coat = bpy.data.objects['Wolf ivory coat']
    archive = np.load(draft / 'head-paint-source.npz')
else:
    archive = np.load(draft / 'surface.npz')
    bpy.ops.wm.save_as_mainfile(filepath=str(draft / 'head-paint-source.blend'))
    np.savez_compressed(draft / 'head-paint-source.npz', rest=archive['rest'], delta=archive['delta'])

def smooth(x):
    x = np.clip(x, 0, 1)
    return x*x*(3-2*x)

def refine(points):
    p = np.asarray(points).copy()
    x, y, z = points.T
    head = smooth((-y-2.42)/.60) * smooth((z-3.60)/.50)
    p[:, 1] -= .105 * np.maximum(0, -y-2.70) * head
    p[:, 0] *= 1 - .035*smooth((-y-3.15)/.75)*head
    ears = smooth((z-4.90)/.28)*smooth((np.abs(x)-.16)/.12)*smooth((-y-2.55)/.30)
    p[:, 2] += .12*ears
    p[:, 0] += np.sign(x)*.024*ears
    return p

rest, delta = archive['rest'], archive['delta']
next_rest = refine(rest)
next_delta = np.asarray([refine(rest+d)-next_rest for d in delta])
coat.data.vertices.foreach_set('co', next_rest.astype(np.float32).ravel())
coat.data.update()
coat['head_refined'] = True
body = rest[:, 1] > -2.42
assert np.max(np.abs(next_rest[body]-rest[body])) == 0
np.savez_compressed(draft / 'surface.npz', rest=next_rest, delta=next_delta)
(root/'review/head-refinement.json').write_text(json.dumps({
    'headLengthScale': 1.105, 'muzzleWidthScale': .965,
    'earTipAddedHeight': .12, 'earTipAddedLateralWidth': .024,
    'bodyMaxCoordinateChange': 0,
    'topologyChanged': False, 'correctiveShapes': len(delta),
    'previousHeadFront': float(rest[:,1].min()),
    'newHeadFront': float(next_rest[:,1].min()),
    'previousEarTop': float(rest[rest[:,1]<-2.5,2].max()),
    'newEarTop': float(next_rest[rest[:,1]<-2.5,2].max())
}, indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(draft / 'run-candidate.blend'))
print('HEAD_REFINED', len(next_rest), flush=True)
