"""Convert inspected original payloads; never generate replacement artwork.

Input is the isolated full-asset-inspection inventory/cache from the supplied
archives. Source hashes are checked before conversion. Runtime code owns gameplay;
native models, UVs, paintings, weights and motion curves own the visual content.
"""
from pathlib import Path
import argparse,collections,hashlib,importlib.util,json,math,re,struct,sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets'
OUT=A/'OkamiRemaster/Original';RES=OUT/'Resources/Okami'
sys.path.insert(0,str(ROOT/'tools/village'));from native import Mesh
sys.path.insert(0,str(ROOT/'tools/remaster/live'));import export_player as motion
spec=importlib.util.spec_from_file_location('source_converter',ROOT/'tools/remaster/export_native_review.py');converter=importlib.util.module_from_spec(spec);spec.loader.exec_module(converter)
UNIT=.075

STATIC={
 'VT': 'vta0 vta1 vta2 vta3 vta8 vta9 vtaa vtae vtb0 vtb1 vtb2 vtb4 vtab vtb5 vt04 vt05 vt08 vt0b vt0c vt0d vt11 vt12 vt13 vt15 vt17 vt18 vt19 vt1a vt1d vt1e vt1f vt24 vt25 vt26 vt27 vt28 vt29 vt2a vt31 vt32 vt33 vt34 vt35 vt36 vt37 vt3a vt3c vt3e vt3f vt40 vt46 vt47 vt48 vt49 vt4a vt60 vt61 vt62 vt64 vt65 vt66 vt67 vt68 vt69 vt6a vt6b vt6c vt6d vt74 vt75 vt7c vte0 vte1 vte3 vte4 vte5 vte6',
 'ET': 'et00 et01 et08 et09 et0c et0d et16 et19 et24 et25 et47 et4a et4b et4c et4d et4e et4f et51',
 'IT': 'it20 it21 it22 it23 it24 it25 it26 it27 it28 it29 it2b it2c it2d it2e it2f it30 it31 it34',
 'GT': 'gt02 gt12 gt18 gt22',
 'WP': 'wp24 wp25',
 'DR': 'dr01 dr05 dr06',
}
ACTORS={'HM':'hm00 hm01 hm05 hm09 hm0f hm29 hm2d hm44 hm68','EM':'em00 em01 em02 em03 em04 em11','VT':'vt6a','WP':'wp25'}
suffixes=['000','010','011','012','020','021','030','032','040','050','130']

def digest(data):return hashlib.sha256(data).hexdigest()
def guid(path):
    path=Path(path);m=Path(str(path)+'.meta')
    if m.exists():return re.search(r'^guid: (\w+)',m.read_text(),re.M)[1]
    g=digest(('OriginalOnly/'+str(path.relative_to(A))).encode())[:32]
    if path.is_dir():kind='folderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n'
    elif path.suffix=='.png':
        template=(A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Texture-0.png.meta').read_text()
        m.write_text(re.sub(r'^guid: \w+','guid: '+g,template,flags=re.M));return g
    elif path.suffix=='.mat':kind='NativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 2100000\n'
    elif path.suffix=='.asset':kind='NativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 4300000\n'
    elif path.suffix=='.cs':kind='MonoImporter:\n  externalObjects: {}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n'
    elif path.suffix=='.shader':kind='ShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n'
    else:kind='TextScriptImporter:\n  externalObjects: {}\n'
    m.write_text('fileFormatVersion: 2\nguid: '+g+'\n'+kind+'  userData:\n  assetBundleName:\n  assetBundleVariant:\n');return g

def rotation(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])

def skin(model,pose):
    matrices=[];bind=[]
    for i,record in enumerate(pose):
        p,q,s=record[:3],record[3:7],record[7:];m=np.eye(4);m[:3,:3]=rotation(q)@np.diag(s);m[:3,3]=p
        parent=model['bones'][i-1]['parent']+1 if i else -1
        matrices.append(m if parent<0 else matrices[parent]@m)
        bind.append(np.zeros(3) if not i else bind[parent]+np.asarray(model['bones'][i-1]['position']))
    matrices=np.asarray(matrices);bind=np.asarray(bind);out=[]
    for part in model['parts']:
        v=np.asarray(part['positions']).reshape(-1,3);indices=np.asarray(part['boneIndices']).reshape(-1,3)+1;weights=np.asarray(part['weights']).reshape(-1,3);weights/=weights.sum(1,keepdims=True);posed=np.zeros_like(v)
        for k in range(3):posed+=weights[:,k,None]*(np.einsum('nij,nj->ni',matrices[indices[:,k],:3,:3],v-bind[indices[:,k]])+matrices[indices[:,k],:3,3])
        out.append(posed)
    return out

def export(source):
    rows=[json.loads(l) for l in (source/'inventory.jsonl').read_text().splitlines()]
    for path in [OUT,RES,OUT/'Meshes',OUT/'Materials',OUT/'Scripts',OUT/'Shaders']:path.mkdir(parents=True,exist_ok=True)
    original_shader=A/'OkamiRemaster/Village/Demo/Shaders/FarmAnimals.shader'
    shader=OUT/'Shaders/OriginalPaint.shader'
    text=original_shader.read_text().replace('VillageDemo/Original Farm Animals','Sunward/Original Okami Paint').replace('#include "VillageLighting.hlsl"','#include "../../Village/Demo/Shaders/VillageLighting.hlsl"')
    shader.write_text(text);shader_guid=guid(shader)
    index=[]
    for group,listing in {**STATIC,**{g:STATIC.get(g,'')+' '+s for g,s in ACTORS.items()}}.items():
        for package in dict.fromkeys(listing.split()):
            target=RES/package;target.mkdir(exist_ok=True)
            es=[e for e in rows if e['group']==group and e['package']==package]
            md=next(e for e in es if e['type']=='MD');data=(source/md['cache']).read_bytes();assert digest(data)==md['sha256']
            adapted=[dict(e,path=e.get('cache','')) for e in es]
            native=converter.read_model(data,adapted,package,source,target,allow_vertex_only=True)
            converted=json.loads(json.dumps(native));converted['sourceUnits']='Metres; native X reflected, +Z preserved'
            for bone in converted['bones']:bone['position']=(np.asarray(bone['position'])*[-UNIT,UNIT,UNIT]).tolist()
            for part in converted['parts']:
                part['positions']=(np.asarray(part['positions']).reshape(-1,3)*[-UNIT,UNIT,UNIT]).ravel().tolist()
                part['indices']=np.asarray(part['indices']).reshape(-1,3)[:,[0,2,1]].ravel().tolist()
            (target/'Model.json').write_text(json.dumps(converted,separators=(',',':'),allow_nan=False))
            nb=len(native['bones']);candidates=[e for e in es if e['type']=='MOT' and e.get('frames') and e.get('maxBone',999)<nb]
            idle=next((e for e in candidates if e['name']==package+'_000'),None) or next((e for e in candidates if e['name'].endswith('_000')),None)
            if idle:
                raw=(source/idle['cache']).read_bytes();assert digest(raw)==idle['sha256'];frames,loop,ch=motion.parse(raw,nb,allow_duplicate_channels=True);pose=motion.sample(native,ch,0)
            else:pose=motion.sample(native,{},0)
            verts=skin(converted,pose);points=np.concatenate(verts);lo=points.min(0);hi=points.max(0)
            entry=dict(group=group,package=package,sourceSHA256=md['sha256'],sourcePath=md['path'],boundsMin=lo.tolist(),boundsMax=hi.tolist(),idle=idle['name'] if idle else '',meshes=[],textures=converted['textures'],motions=[],UnityVerified=False)
            for i,(part,v) in enumerate(zip(converted['parts'],verts)):
                if not part['indices']:continue
                m=Mesh();m.v=v.tolist();m.c=np.asarray(part['colors']).reshape(-1,4)[:,:3].tolist();m.uv=np.asarray(part['uv']).reshape(-1,2).tolist();m.bones=[0]*len(v);m.tri=np.asarray(part['indices']).reshape(-1,3).tolist();path=OUT/'Meshes'/(package+'-'+str(i)+'.asset');m.write(path)
                material=OUT/'Materials'/(package+'-'+str(part['texture'])+'.mat')
                material.write_text('''%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_Name: Original '''+package+''' paint
  m_Shader: {fileID: 4800000, guid: '''+shader_guid+''', type: 3}
  m_EnableInstancingVariants: 1
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs:
    - _MainTex:
        m_Texture: {fileID: 2800000, guid: '''+(guid(target/('Texture-'+str(part['texture'])+'.png')) if part['texture']!=255 else '00000000000000000000000000000000')+''', type: 3}
        m_Scale: {x: 1, y: 1}
        m_Offset: {x: 0, y: 0}
    m_Ints: []
    m_Floats:
    - _Cutoff: 0.3
    m_Colors:
    - _Color: {r: 1, g: 1, b: 1, a: 1}
''')
                if part['texture']==255:
                    material.write_text(re.sub(r'    m_TexEnvs:\n.*?(?=    m_Ints:)', '    m_TexEnvs: []\n', material.read_text(),flags=re.S))
                entry['meshes'].append(dict(mesh=guid(path),material=guid(material),vertices=len(v),triangles=len(m.tri)))
            if group in ACTORS and package in ACTORS[group].split():
                selected=[]
                for suffix in suffixes:
                    e=next((e for e in candidates if e['name'].endswith('_'+suffix)),None)
                    if e:selected.append(e)
                with (target/'Poses.bytes').open('wb') as f:
                    f.write(struct.pack('<4sIII',b'OPB1',1,nb+1,len(selected)))
                    for e in selected:
                        raw=(source/e['cache']).read_bytes();assert digest(raw)==e['sha256'];frames,loop,ch=motion.parse(raw,nb,allow_duplicate_channels=True);n=max(2,(frames-1)*2+1);duration=max(1,frames-1)/30;clipname=e['name'].encode();bank=np.asarray([motion.sample(native,ch,t) for t in np.linspace(0,frames-1,n)])
                        for t in range(1,n):
                            flip=np.sum(bank[t-1,:,3:7]*bank[t,:,3:7],1)<0;bank[t,flip,3:7]*=-1
                        assert np.isfinite(bank).all();f.write(struct.pack('<I',len(clipname)));f.write(clipname);f.write(struct.pack('<IfI',n,duration,int(loop)));f.write(bank.astype('<f4').tobytes())
                        entry['motions'].append(dict(name=e['name'],sourceSHA256=e['sha256'],samples=n,duration=duration,loop=loop))
            index.append(entry);print('EXPORTED',group,package,len(entry['meshes']),len(entry['motions']),flush=True)
    index.extend(export_stage_objects(source,rows,shader_guid))
    for file in [OUT,*sorted(OUT.rglob('*'))]:
        if not file.name.endswith('.meta'):guid(file)
    report=dict(sourceInspection='All supplied original groups; source SHA256 checked at conversion',sourceUnitMetres=UNIT,originalModels=len(index),models=index,UnityVerified=False)
    (Path(__file__).parent/'original-assets.json').write_text(json.dumps(report,indent=2))
    return report

def export_stage_objects(source,rows,shader_guid):
    # Reuse the already-inspected static SCR decoder; preserve original UVs and
    # native per-object transforms, rather than the authored demo's geometry.
    sys.path.insert(0,str(source));import visual_catalog
    result=[]
    for package,name,key in [('r200','Torii_LY01','stage-torii'),('r102','torii_ly1b','kamiki-torii')]:
        row=next(e for e in rows if e['package']==package and e['type']=='SCR' and e['name']==name)
        assert digest((source/row['cache']).read_bytes())==row['sha256']
        parts,_=visual_catalog.model(row);target=RES/key;target.mkdir(exist_ok=True);points=[];meshes=[];textures={}
        for i,part in enumerate(parts):
            v=part['points']*[-UNIT,UNIT,UNIT];points.append(v);faces=part['faces'][:,[0,2,1]];uv=part['uv'].copy();uv[:,1]=1-uv[:,1]
            m=Mesh();m.v=v.tolist();m.c=(part['colors'][:,:3]/128).tolist();m.uv=uv.tolist();m.tri=faces.tolist();m.bones=[0]*len(v);path=OUT/'Meshes'/(key+'-'+str(i)+'.asset');m.write(path)
            tex=part['texture'];assert tex is not None,'Unresolved stage paint binding'
            data=(source/tex['cache']).read_bytes();assert digest(data)==tex['sha256'];texpath=target/(tex['sha256']+'.png');Image.open(source/tex['cache']).save(texpath);textures[tex['sha256']]=dict(path=str(texpath.relative_to(A)),sourceSHA256=tex['sha256'])
            mat=OUT/'Materials'/(key+'-'+str(i)+'.mat');mat.write_text((OUT/'Materials/vta0-0.mat').read_text().replace('Original vta0 paint','Original '+key+' paint').replace(guid(RES/'vta0/Texture-0.png'),guid(texpath)))
            meshes.append(dict(mesh=guid(path),material=guid(mat),vertices=len(v),triangles=len(faces)))
        p=np.concatenate(points);result.append(dict(group='ST2' if package=='r200' else 'ST1',package=key,sourcePackage=package,sourceSHA256=row['sha256'],sourcePath=row['path'],boundsMin=p.min(0).tolist(),boundsMax=p.max(0).tolist(),meshes=meshes,textures=list(textures.values()),motions=[],UnityVerified=False))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--inspection',type=Path,required=True);args=p.parse_args();report=export(args.inspection);print('TOTAL ORIGINAL MODELS',len(report['models']))
