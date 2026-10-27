#!/usr/bin/env python3
"""Convert decoded MD geometry for Unity review; preserve MOT bytes without claiming an animation port.
Usage: python tools/remaster/export_native_review.py --pl <pl-inspection> --wp <wp-inspection>
Requires Pillow only for converting the supplied original DDS textures to PNG.
"""
import argparse, hashlib, json, math, shutil, struct
from pathlib import Path
from PIL import Image

def sha(data): return hashlib.sha256(data).hexdigest()
def read_model(data, inventory, package, root, target):
    assert data[:4] == b'scr\0'
    version, count = struct.unpack_from('<II', data, 4); assert version == 0
    bones = None; parts = []; textures = {}
    for part, transform in enumerate(struct.unpack_from('<'+'I'*count, data, 16)):
        start = transform + struct.unpack_from('<i', data, transform)[0]
        assert data[start:start+4] == b'mdb\0'
        offset, nb, nd = struct.unpack_from('<IHH', data, start+4)
        current = []
        for i in range(nb):
            x,y,z,parent = struct.unpack_from('<fffi', data, start+offset+16*i)
            assert -1 <= parent < i and all(math.isfinite(v) for v in [x,y,z])
            current.append(dict(parent=parent, position=[x,y,z]))
        if bones is None: bones = current
        else: assert bones == current, 'Multiple skeletons need a separate adapter'
        for division, offset in enumerate(struct.unpack_from('<'+'I'*nd, data, start+32)):
            loc=start+offset
            vo,no,uo,co,wo,nv,tex=struct.unpack_from('<IIIIIHH',data,loc)
            assert no == 0, 'Unexpected normal stream; add its verified decoder first'
            positions=[]; indices=[]; uv=[]; colors=[]; bone_indices=[]; weights=[]
            for i in range(nv):
                x,y,z,winding=struct.unpack_from('<fffI',data,loc+vo+16*i)
                assert all(math.isfinite(v) for v in [x,y,z]) and winding in [0,1,32768]
                positions.extend([x,y,z])
                if i>=2 and winding in [0,1]: indices.extend([i-2+winding,i-1-winding,i])
                u,v=struct.unpack_from('<hh',data,loc+uo+4*i) if uo else (0,0)
                # DDS image origin is top-left; Unity UV origin is bottom-left.
                uv.extend([u/4096,1-v/4096])
                colors.extend([x/128 for x in data[loc+co+4*i:loc+co+4*i+4]] if co else [1,1,1,1])
                assert wo, 'This review converter expects native skinned MD'
                raw=data[loc+wo+8*i:loc+wo+8*i+8];bi=list(raw[1:4]);we=list(raw[4:7])
                assert max(bi)<nb and abs(sum(we)-255)<=1
                bone_indices.extend(bi);weights.extend([v/255 for v in we])
            if tex not in textures:
                e=next(e for e in inventory if e['package']==package and e['type']=='DDS' and e['index']==tex)
                image=Image.open(root/e['path']); image.load(); name='Texture-'+str(tex)+'.png';image.save(target/name)
                textures[tex]=dict(index=tex,path=name,sourceSHA256=e['sha256'])
            parts.append(dict(name=f'Native-{part}-{division}',texture=tex,positions=positions,indices=indices,uv=uv,colors=colors,boneIndices=bone_indices,weights=weights))
    return dict(version=1,name=package,sourceSHA256=sha(data),sourceUnits='Unscaled native coordinates; not gameplay calibrated',bones=bones,parts=parts,textures=list(textures.values()))

def export(pl,wp,output):
    output.mkdir(parents=True,exist_ok=True); banks={}; manifest=[]; motions={}
    for label,root in [('pl',pl),('wp',wp)]:
        inventory=json.loads((root/'inventory.json').read_text());banks[label]=inventory
        for e in inventory:
            is_ammy=e['type']=='MOT' and e['name'].startswith('pl00_') and (label=='wp' or e['package']=='pl00')
            if not is_ammy: continue
            data=(root/e['path']).read_bytes()
            if data[:4]!=b'mtb3':continue # _dummy entries are SEQ data, not animation.
            assert sha(data)==e['sha256']
            digest=sha(data);frames,properties,loop=struct.unpack_from('<HBB',data,4)
            alias=dict(archive=label,package=e['package'],name=e['name'],sourcePath=e['path'])
            if digest in motions:motions[digest]['aliases'].append(alias);continue
            relative='MotionSources/'+digest+'.bytes';(output/'MotionSources').mkdir(exist_ok=True);(output/relative).write_bytes(data)
            motions[digest]=dict(path=relative,sha256=digest,bytes=len(data),frames=frames,loop=bool(loop),propertyRecords=properties,aliases=[alias],unityPlayable=False)
    for label,package in [('pl','pl00'),('wp','wp24'),('wp','wp34')]:
        root=pl if label=='pl' else wp;inventory=banks[label];target=output/package;target.mkdir(exist_ok=True)
        e=next(e for e in inventory if e['package']==package and e['type']=='MD')
        data=(root/e['path']).read_bytes();assert sha(data)==e['sha256']
        model=read_model(data,inventory,package,root,target)
        (target/(package+'.okamimodel')).write_text(json.dumps(model,separators=(',',':'),allow_nan=False)+'\n')
        (target/(package+'.MD.bytes')).write_bytes(data)
        # Preserve Solar Flare's undecoded components for the later effects adapter.
        if label=='wp':
            raw=target/'OriginalComponents';raw.mkdir(exist_ok=True)
            for item in inventory:
                if item['package']!=package:continue
                original=(root/item['path']).read_bytes();assert sha(original)==item['sha256']
                relative=Path(package)/'OriginalComponents'/(str(item['index']).zfill(3)+'-'+item['name']+'.'+item['type']+'-'+item['sha256'][:12]+'.bytes')
                (output/relative).write_bytes(original)
                manifest.append(dict(path=str(relative),sha256=item['sha256'],bytes=len(original),type=item['type'],name=item['name']))
    (output/'motion-source-index.json').write_text(json.dumps(dict(status='Original bytes only; native interpolation, action names, FPS and Unity playback not approved',uniqueAmmyPayloads=len(motions),motions=list(motions.values())),indent=2)+'\n')
    (output/'original-component-index.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return dict(reviewModels=3,uniqueAmmyPayloads=len(motions),solarFlareComponentFiles=len(manifest))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--pl',type=Path,required=True);parser.add_argument('--wp',type=Path,required=True);parser.add_argument('--output',type=Path,default=Path(__file__).resolve().parents[2]/'Sunward-Unity/Assets/OkamiRemaster/NativeReview');args=parser.parse_args()
    print(json.dumps(export(args.pl,args.wp,args.output)))
