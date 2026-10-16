"""Reference-guided tapered face and pointed ears, preserving the approved body.

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
    # A wedge-shaped face, rather than stretching the broad original muzzle.
    p[:, 1] -= .045 * np.maximum(0, -y-2.70) * head
    taper = smooth((-y-2.70)/.65)*smooth((z-3.85)/.35)
    p[:, 0] *= 1-.15*taper-.055*smooth((-y-3.55)/.5)*head
    lip = smooth((-y-3.40)/.45)*(1-smooth((z-4.02)/.18))*head
    p[:, 2] += .045*lip
    ears = smooth((z-4.90)/.28)*smooth((np.abs(x)-.16)/.12)*smooth((-y-2.55)/.30)
    p[:, 2] += .17*ears
    p[:, 0] += (np.sign(x)*.024-(x-np.sign(x)*.40)*.32)*ears
    p[:, 1] -= .025*ears
    return p

rest, delta = archive['rest'], archive['delta']
# Relax the inherited lip bumps locally, with the same linear operator for
# every corrective. Neither the body nor the sculpted fur enters this mask.
edges=np.asarray([e.vertices[:] for e in coat.data.edges]);a,b=edges.T
degree=np.bincount(edges.ravel(),minlength=len(rest)).clip(1)
x,y,z=rest.T
lip_weight=.38*smooth((-y-3.30)/.28)*smooth((y+4.25)/.15)*smooth((z-3.98)/.10)*(1-smooth((z-4.22)/.13))
def smooth_lip(points):
    p=points.copy()
    for _ in range(5):
        total=np.zeros_like(p);np.add.at(total,a,p[b]);np.add.at(total,b,p[a])
        p+=(total/degree[:,None]-p)*lip_weight[:,None]
    return p
next_rest = smooth_lip(refine(rest))
next_delta = np.asarray([smooth_lip(refine(rest+d))-next_rest for d in delta])
coat.data.vertices.foreach_set('co', next_rest.astype(np.float32).ravel())
coat.data.update()
coat['head_refined'] = True
body = rest[:, 1] > -2.42
assert np.max(np.abs(next_rest[body]-rest[body])) == 0
np.savez_compressed(draft / 'surface.npz', rest=next_rest, delta=next_delta)
(root/'review/head-refinement.json').write_text(json.dumps({
    'headLengthScale': 1.045, 'faceWidthScale': .85, 'muzzleWidthScale': .795,
    'earTipAddedHeight': .17, 'earTipTaper': .32,
    'design': 'Tapered face, slimmer muzzle and jaw, pointed ears; small painted nose and compact ink eyes.',
    'bodyMaxCoordinateChange': 0,
    'topologyChanged': False, 'correctiveShapes': len(delta),
    'previousHeadFront': float(rest[:,1].min()),
    'newHeadFront': float(next_rest[:,1].min()),
    'previousEarTop': float(rest[rest[:,1]<-2.5,2].max()),
    'newEarTop': float(next_rest[rest[:,1]<-2.5,2].max())
}, indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(draft / 'run-candidate.blend'))
print('HEAD_REFINED', len(next_rest), flush=True)
