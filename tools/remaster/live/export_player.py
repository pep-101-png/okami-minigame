#!/usr/bin/env python3
"""Bake original mtb3 channels onto the original MD rig, never the unrelated FBX.

30 native frames/second follows the public MD Studio importer. Curves use its
normalized-segment Hermite tangents; samples are baked at 60 Hz. This is a Unity
port, not proof of byte-identical execution of the original game's renderer.
"""
from pathlib import Path
import hashlib, json, math, shutil, struct
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT/'tools/remaster/reference/NativeSources'
OUT = ROOT/'Sunward-Unity/Assets/OkamiRemaster/Player/Resources/NativePlayer'
UNIT = .075

def half(x):
    return (-1 if x & 32768 else 1)*2**(((x >> 9) & 63)-47)*(1+(x & 511)/512)

def parse(data, bones):
    assert data[:4] == b'mtb3'
    frames, count, loop = struct.unpack_from('<HBB', data, 4)
    channels = {}
    for k in range(count-1):
        bone, prop, n, offset = struct.unpack_from('<bBHI', data, 8+k*8)
        assert -1 <= bone < bones
        if prop < 9:
            values = [(0., struct.unpack_from('<f', data, 12+k*8)[0], 0., 0.)]
        elif 16 <= prop <= 24:
            c = [half(x) for x in struct.unpack_from('<6H', data, offset)]
            values = []; time = 0
            for j in range(n):
                dt, a, b, c1 = struct.unpack_from('<4B', data, offset+12+j*4)
                time += dt; values.append((time, c[0]+c[1]*a, c[2]+c[3]*b, c[4]+c[5]*c1))
            prop -= 16
        elif 50 <= prop <= 58:
            c = struct.unpack_from('<6f', data, offset); values = []
            for j in range(n):
                t, a, b, c1 = struct.unpack_from('<4H', data, offset+24+j*8)
                values.append((t, c[0]+c[1]*a, c[2]+c[3]*b, c[4]+c[5]*c1))
            prop -= 50
        elif 80 <= prop <= 88:
            values = [struct.unpack_from('<HHfff', data, offset+j*16) for j in range(n)]
            values = [(t, a, b, c) for t, pad, a, b, c in values]; prop -= 80
        else:
            raise ValueError(('Unsupported MOT channel', prop))
        assert values and all(values[i][0] < values[i+1][0] for i in range(len(values)-1))
        assert (bone+1, prop) not in channels
        channels[bone+1, prop] = np.asarray(values, dtype=float)
    return frames, bool(loop), channels

def evaluate(keys, time):
    if time <= keys[0,0]: return keys[0,1]
    if time >= keys[-1,0]: return keys[-1,1]
    k = np.searchsorted(keys[:,0], time, side='right')-1
    s = (time-keys[k,0])/(keys[k+1,0]-keys[k,0])
    return (2*s**3-3*s*s+1)*keys[k,1]+(s**3-2*s*s+s)*keys[k,3]+(-2*s**3+3*s*s)*keys[k+1,1]+(s**3-s*s)*keys[k+1,2]

def sample(model, channels, time):
    n = len(model['bones'])+1
    pos = np.array([[0.,0.,0.]]+[b['position'] for b in model['bones']])
    angles = np.zeros((n,3)); scales = np.ones((n,3))
    for (b,p), keys in channels.items():
        target = pos if p < 3 else angles if p < 6 else scales
        target[b,p%3] = evaluate(keys, time)
    # The motor already owns translation, gravity, jumps and attack lunges.
    # Remove only the virtual scene root's translation. Preserve pelvis motion,
    # every deform-bone scale and all rotations (including rolls and flips).
    pos[0] = 0
    # Native Amaterasu's muzzle points along +Z. Reflect X to change
    # handedness without turning her away from the controller's +Z heading.
    pos *= [-UNIT,UNIT,UNIT]
    x,y,z = angles.T/2
    sx,cx = np.sin(x),np.cos(x); sy,cy = np.sin(y),np.cos(y); sz,cz = np.sin(z),np.cos(z)
    # Rz * Ry * Rx, then reflect X into Unity's coordinate basis.
    quat = np.array([sx*cy*cz-cx*sy*sz, -(cx*sy*cz+sx*cy*sz), -(cx*cy*sz-sx*sy*cz), cx*cy*cz+sx*sy*sz]).T
    return np.concatenate([pos,quat,scales],axis=1).astype('<f4')

def export():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest = {'version':1,'unitMetres':UNIT,'nativeFPS':30,'sampleFPS':60,'rootTranslation':'virtual scene root removed; bone translations, scales and rotations retained','motions':[],'models':[],'UnityVerified':False}
    for name in ['pl00','wp24','wp34']:
        model = json.loads((SOURCE/name/(name+'.okamimodel')).read_text())
        target = OUT/name; target.mkdir(exist_ok=True)
        converted = json.loads(json.dumps(model))
        converted['sourceUnits'] = 'Metres; reflect native X at 0.075 m/unit, preserve +Z facing'
        for b in converted['bones']: b['position'] = (np.asarray(b['position'])*[-UNIT,UNIT,UNIT]).tolist()
        for part in converted['parts']:
            part['positions'] = (np.asarray(part['positions']).reshape(-1,3)*[-UNIT,UNIT,UNIT]).ravel().tolist()
            # Reflection reverses geometric winding.
            part['indices'] = np.asarray(part['indices']).reshape(-1,3)[:,[0,2,1]].ravel().tolist()
        for texture in converted['textures']: shutil.copyfile(SOURCE/name/texture['path'],target/texture['path'])
        (target/'Model.json').write_text(json.dumps(converted,separators=(',',':'))+'\n')
        manifest['models'].append(dict(name=name,sourceSHA256=model['sourceSHA256'],bones=len(model['bones']),vertices=sum(len(p['positions'])//3 for p in model['parts'])))
        candidates = []
        if name == 'pl00':
            for record in json.loads((SOURCE/'motion-source-index.json').read_text())['motions']:
                candidates.append((record['aliases'][0]['name'],SOURCE/record['path'],record['sha256']))
        else:
            for record in json.loads((SOURCE/'original-component-index.json').read_text()):
                if record['type']=='MOT' and record['path'].startswith(name+'/') and record['name'].startswith(name+'_'):
                    candidates.append((record['name'],SOURCE/record['path'],record['sha256']))
        with (target/'Poses.bytes').open('wb') as f:
            f.write(struct.pack('<4sIII',b'OPB1',1,len(model['bones'])+1,len(candidates)))
            for clipname, path, digest in candidates:
                data = path.read_bytes(); assert hashlib.sha256(data).hexdigest()==digest
                frames,loop,channels = parse(data,len(model['bones']))
                samples = max(2,(frames-1)*2+1); duration = max(1,frames-1)/30
                namebytes = clipname.encode('ascii')
                f.write(struct.pack('<I',len(namebytes)));f.write(namebytes)
                f.write(struct.pack('<IfI',samples,duration,int(loop)))
                bank = np.array([sample(model,channels,t) for t in np.linspace(0,frames-1,samples)])
                # Quaternion sign continuity makes linear/spherical playback
                # stable across full turns without changing any native pose.
                for t in range(1,samples):
                    flip = np.sum(bank[t-1,:,3:7]*bank[t,:,3:7],axis=1)<0
                    bank[t,flip,3:7] *= -1
                assert np.isfinite(bank).all()
                assert np.max(abs(np.linalg.norm(bank[:,:,3:7],axis=2)-1))<1e-5
                f.write(bank.astype('<f4').tobytes())
                manifest['motions'].append(dict(model=name,name=clipname,sourceSHA256=digest,nativeFrames=frames,loop=loop,samples=samples,duration=duration,poseSHA256=hashlib.sha256(bank.astype('<f4').tobytes()).hexdigest()))
    (Path(__file__).with_name('player-export.json')).write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({'models':manifest['models'],'motionCount':len(manifest['motions']),'bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file())}))

if __name__ == '__main__': export()
