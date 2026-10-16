"""Local anatomical sculpt, starting from the immutable approved neck checkpoint.

Reuse the current native mesh, 48 companion correctives and portable GLB.
No remesh, subdivision, rebake, animation regeneration or neck-weight editing.
"""
from pathlib import Path
import sys
import json
import hashlib
import os
import io
import bpy
import numpy as np
from PIL import Image, ImageDraw
from mathutils import Vector
from mathutils.kdtree import KDTree

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / 'authoring'))
from glb_buffers import GLB, to_gltf, to_native

draft = root / 'review/drafts/head-reconstruction'
draft.mkdir(parents=True, exist_ok=True)
checkpoint = root / 'authoring/checkpoints'
source = root / 'public/models/neck-approved.glb'
assert hashlib.sha256(source.read_bytes()).hexdigest() == '34927db7ab06488414889a8c2eb74e112b13bc10bfbde13e3333f6c9f77a001c'
bpy.ops.wm.open_mainfile(filepath=str(checkpoint / 'neck-approved.blend'))
coat = bpy.data.objects['Wolf ivory coat']
rig = bpy.data.objects['DivineWolfRig']
archive = np.load(checkpoint / 'neck-approved-surface.npz')
rest, delta = archive['rest'], archive['delta']
native = np.array([v.co[:] for v in coat.data.vertices], dtype=np.float32)
assert np.array_equal(native, rest)

# Only the actual facial coat is sculpted. The neck, ears and every ornamental
# fur layer retain their accepted coordinates and all three skin bindings.
support = np.zeros(len(rest))
for v in coat.data.vertices:
    if v.index < 44506:
        amount = sum(g.weight for g in v.groups if coat.vertex_groups[g.group].name in ('head', 'jaw'))
        support[v.index] = np.clip((amount - .985) / .015, 0, 1)

strength = float(os.environ.get('HEAD_SCULPT_STRENGTH', '1'))


def smooth(value):
    v = np.clip(value, 0, 1)
    return v * v * (3 - 2 * v)


def sculpt(points, allowed):
    p = np.asarray(points, dtype=np.float64)
    x, y, z = p.T
    a = np.asarray(allowed)
    movement = np.zeros_like(p)
    # A full mandible, tapering beneath the upper lip instead of a recessed
    # triangular chin. The forward displacement is bounded behind the nose.
    t = np.linspace(0, 1, 128)
    curve_y = (1-t)**3*(-4.245) + 3*(1-t)**2*t*(-4.06) + 3*(1-t)*t*t*(-3.86) + t**3*(-3.68)
    curve_z = (1-t)**3*4.267 + 3*(1-t)**2*t*4.222 + 3*(1-t)*t*t*4.238 + t**3*4.260
    line = np.interp(y, curve_y, curve_z)
    jaw = smooth((line - .008 - z) / .065) * smooth((-y - 3.44) / .30)
    jaw *= smooth((z - 3.92) / .10)
    front = smooth((-y - 3.56) / .44)
    desired = .190 * jaw * front
    available = np.maximum(0, y + 4.230)
    extension = available * (1 - np.exp(-desired / np.maximum(available, 1e-6)))
    movement[:, 1] -= extension
    movement[:, 2] -= .060 * jaw * front * smooth((z - 4.05) / .10)
    movement[:, 0] += x * .08 * jaw * front
    # Fair the inherited mandibular-angle dimple and small underside nub.
    angle = np.exp(-((y+3.87)/.18)**2 - ((z-4.14)/.075)**2)
    movement[:, 0] += np.sign(x) * .025 * angle * smooth((abs(x)-.035)/.065)
    jaw_movement = movement.copy()

    # A subtle stop, a flatter muzzle bridge and a rounded frontal dome.
    # These are surface changes, not uniform head scaling.
    upper = smooth((z - 4.43) / .25)
    bridge = np.exp(-((y + 3.69) / .19) ** 2) * upper
    movement[:, 2] -= .075 * bridge
    dome = np.exp(-((y + 3.35) / .25) ** 2) * smooth((z - 4.76) / .18)
    dome *= 1 - smooth((z - 5.03) / .10)
    movement[:, 2] += .040 * dome
    muzzle = np.exp(-((y + 3.91) / .25) ** 2) * smooth((z - 4.20) / .12)
    muzzle *= (1 - smooth((z - 4.57) / .14)) * smooth((y + 4.23) / .13)
    movement[:, 0] += x * .075 * muzzle

    # Actual orbital relief: shallow recessed eye beds, a supported upper
    # orbital rim and restrained cheekbone volume beneath the painted eyes.
    eye = np.exp(-((abs(x) - .28) / .13) ** 2 - ((y + 3.50) / .19) ** 2 - ((z - 4.69) / .070) ** 2)
    brow = np.exp(-((abs(x) - .29) / .16) ** 2 - ((y + 3.47) / .22) ** 2 - ((z - 4.80) / .095) ** 2)
    cheek = np.exp(-((y + 3.39) / .22) ** 2 - ((z - 4.52) / .16) ** 2) * smooth((abs(x) - .14) / .13)
    movement[:, 0] += np.sign(x) * (-.019 * eye + .037 * brow + .038 * cheek)
    movement[:, 2] += .018 * brow + .008 * cheek

    eye_patch = np.exp(-((abs(x)-.28)/.25)**4 - ((y+3.50)/.30)**4 - ((z-4.77)/.22)**4)
    seal = np.exp(-(x/.16)**4) * smooth((z-4.68)/.11)
    anatomy = movement - jaw_movement
    anatomy[:, 2] *= (1 - .92*eye_patch) * (1 - .85*seal)
    anatomy[:, 2] += .012*seal
    movement = jaw_movement + anatomy

    boundary = smooth((-y - 3.09) / .20) * smooth((z - 3.92) / .12)
    boundary *= 1 - smooth((z - 5.05) / .10)
    return p + movement * (a * boundary * strength)[:, None]


def jacobian(points, allowed):
    h = 1e-4
    columns = []
    for axis in range(3):
        offset = np.zeros(3); offset[axis] = h
        columns.append((sculpt(points + offset, allowed) - sculpt(points - offset, allowed)) / (2 * h))
    return np.stack(columns, axis=-1)


next_rest = sculpt(rest, support).astype(np.float32)
changed = np.linalg.norm(next_rest - rest, axis=1) > 1e-7
next_rest[~changed] = rest[~changed]
next_delta = delta.copy()
for i, change in enumerate(delta):
    next_delta[i, changed] = (sculpt((rest + change)[changed], support[changed]) - next_rest[changed]).astype(np.float32)
assert np.array_equal(next_rest[~changed], rest[~changed])
assert not changed[44506:].any()
assert not changed[(rest[:, 1] > -3.09) | (rest[:, 2] < 3.92)].any()
assert np.array_equal(next_delta[:, ~changed], delta[:, ~changed])
assert np.isfinite(next_delta).all()

coat.data.vertices.foreach_set('co', next_rest.ravel())
coat.data.update()
coat['head_reconstructed'] = True
rig.animation_data.action = bpy.data.actions['Idle']
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(draft / 'head-candidate.blend'), compress=True)
np.savez_compressed(draft / 'head-surface.npz', rest=next_rest, delta=next_delta, facial_mask=changed)

asset = GLB(source)
primitive = asset.doc['meshes'][0]['primitives'][0]
positions = asset.read(primitive['attributes']['POSITION'])
kd = KDTree(len(rest))
for i, p in enumerate(to_gltf(rest)):
    kd.insert(Vector(p), i)
kd.balance()
mapping = []
for p in positions:
    _, index, distance = kd.find(Vector(p))
    assert distance < 1e-6
    mapping.append(index)
mapping = np.asarray(mapping)
region = changed[mapping]
ids = mapping[region]
positions[region] = to_gltf(next_rest)[ids]
asset.write(primitive['attributes']['POSITION'], positions)

J = jacobian(rest[ids], support[ids])
determinants = np.linalg.det(J)
assert determinants.min() > .04, ('Sculpt field inversion', float(determinants.min()))
normal_matrices = np.linalg.inv(J).transpose(0, 2, 1)
old_normals = asset.read(primitive['attributes']['NORMAL'])
base_native_normals = to_native(old_normals[region])
new_native_normals = np.einsum('vij,vj->vi', normal_matrices, base_native_normals)
new_native_normals /= np.linalg.norm(new_native_normals, axis=1)[:, None]
normals = old_normals.copy(); normals[region] = to_gltf(new_native_normals)
asset.write(primitive['attributes']['NORMAL'], normals)

for i, target in enumerate(primitive['targets']):
    before = asset.read(target['POSITION'])
    values = before.copy(); values[region] = to_gltf(next_delta[i])[ids]
    asset.write(target['POSITION'], values)
    old_delta_normal = asset.read(target['NORMAL'])
    local_J = jacobian(rest[ids] + delta[i, ids], support[ids])
    local_N = np.linalg.inv(local_J).transpose(0, 2, 1)
    posed_normal = np.einsum('vij,vj->vi', local_N, base_native_normals + to_native(old_delta_normal[region]))
    posed_normal /= np.linalg.norm(posed_normal, axis=1)[:, None]
    new_delta_normal = old_delta_normal.copy()
    new_delta_normal[region] = to_gltf(posed_normal - new_native_normals)
    target['NORMAL'] = asset.write_sparse(target['NORMAL'], new_delta_normal)

# The old bake contains a dark mandibular dimple. Attenuate only that patch's
# tangent-space normal deviations; keep colour/eye paint and protected body
# texels exact. This is a local bake correction after the geometric sculpt.
normal_image = asset.doc['images'][asset.doc['textures'][asset.doc['materials'][0]['normalTexture']['index']]['source']]
view = asset.doc['bufferViews'][normal_image['bufferView']]
payload = bytes(asset.binary[view.get('byteOffset', 0):view.get('byteOffset', 0)+view['byteLength']])
image = Image.open(io.BytesIO(payload)).convert('RGBA')
pixels = np.asarray(image).copy(); height, width = pixels.shape[:2]
uv = asset.read(primitive['attributes']['TEXCOORD_0'])
triangles = asset.read(primitive['indices']).ravel().reshape(-1, 3)
q = rest[mapping]; x,y,z = q.T
normal_amount = np.exp(-((y+3.87)/.25)**2 - ((z-4.13)/.11)**2)
normal_amount *= smooth((-y-3.45)/.20) * support[mapping] * (mapping<44506)
normal_amount *= smooth((4.225-z)/.07)
normal_amount[normal_amount<.025] = 0
uv_pixels = uv * np.array([width, -height]) + np.array([0, height])
protected = Image.new('L', (width, height), 0); draw = ImageDraw.Draw(protected)
for triangle in triangles[np.max(normal_amount[triangles], axis=1)==0]:
    draw.polygon([tuple(v) for v in uv_pixels[triangle]], fill=255)
normal_mask = np.zeros((height, width), dtype=np.float32)
for triangle in triangles[np.max(normal_amount[triangles], axis=1)>0]:
    pts = uv_pixels[triangle]; lo = np.maximum(np.floor(pts.min(axis=0)).astype(int), 0)
    hi = np.minimum(np.ceil(pts.max(axis=0)).astype(int), [width-1, height-1])
    if np.any(hi<lo): continue
    xx,yy = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
    denom = (pts[1,1]-pts[2,1])*(pts[0,0]-pts[2,0])+(pts[2,0]-pts[1,0])*(pts[0,1]-pts[2,1])
    if abs(denom)<1e-8: continue
    a = ((pts[1,1]-pts[2,1])*(xx-pts[2,0])+(pts[2,0]-pts[1,0])*(yy-pts[2,1]))/denom
    b = ((pts[2,1]-pts[0,1])*(xx-pts[2,0])+(pts[0,0]-pts[2,0])*(yy-pts[2,1]))/denom
    c = 1-a-b; inside = (a>=0)&(b>=0)&(c>=0)
    value = (a*normal_amount[triangle[0]]+b*normal_amount[triangle[1]]+c*normal_amount[triangle[2]])*inside
    area = normal_mask[lo[1]:hi[1]+1,lo[0]:hi[0]+1]; np.maximum(area,value,out=area)
normal_mask[np.asarray(protected)>0] = 0
mask = normal_mask>.025
vectors = pixels[mask,:3].astype(np.float32)/127.5-1
vectors[:,:2] *= (1-.82*normal_mask[mask])[:,None]
vectors /= np.linalg.norm(vectors,axis=1)[:,None]
pixels[mask,:3] = np.clip(np.round((vectors+1)*127.5),0,255).astype(np.uint8)
assert np.array_equal(pixels[~mask], np.asarray(image)[~mask])
new_image = Image.fromarray(pixels); normal_path = draft/'head-normal.png';new_image.save(normal_path)
normal_image['bufferView'] = asset.append_view(np.frombuffer(normal_path.read_bytes(),dtype=np.uint8))
Image.fromarray(np.round(normal_mask*255).astype(np.uint8)).save(draft/'jaw-normal-mask.png')
for material in coat.data.materials:
    if not material or not material.use_nodes: continue
    for node in material.node_tree.nodes:
        if node.type=='TEX_IMAGE' and node.image and 'fur-normals' in node.image.filepath:
            node.image=bpy.data.images.load(str(normal_path),check_existing=True);node.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(draft/'head-candidate.blend'),compress=True)
output = draft / 'head-candidate.glb'
asset.save(output)
assert output.stat().st_size<100*1024*1024
# Preserve painted eye shapes; only move the existing blink-fit landmarks with
# the real surface, so their runtime compression follows the reconstructed eye.
metadata = json.loads((root / 'public/face-neck-approved.json').read_text())
for eye in metadata['eyes']:
    p = np.asarray(eye['point'])[None, :]
    eye['point'] = sculpt(p, np.ones(1))[0].tolist()
    n = np.linalg.inv(jacobian(p, np.ones(1))[0]).T @ np.asarray(eye['surface_normal'])
    eye['surface_normal'] = (n / np.linalg.norm(n)).tolist()
(draft / 'face.json').write_text(json.dumps(metadata, indent=2) + '\n')
metrics = {'approvedNeckSHA256': hashlib.sha256(source.read_bytes()).hexdigest(),
           'candidateSHA256': hashlib.sha256(output.read_bytes()).hexdigest(),
           'nativeVertices': len(rest), 'renderVertices': len(positions),
           'changedNativeFacialVertices': int(changed.sum()),
           'maxNativeDisplacement': float(np.linalg.norm(next_rest-rest, axis=1).max()),
           'minimumSculptJacobianDeterminant': float(determinants.min()),
           'protectedNativeVerticesChanged': 0, 'ornamentalFurVerticesChanged': 0,
           'topologyChanged': False, 'skinBindingsChanged': False, 'animationTracksChanged': False,
           'colourAndEyePaintChanged': False,
           'normalBakeRepairTexels': int(mask.sum()), 'protectedNormalTexelsChanged': 0,
           'strength': strength}
(draft / 'sculpt-metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
print('HEAD_SCULPT', json.dumps(metrics), flush=True)
