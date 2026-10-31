"""Convert inspected native content for the twenty-item playtest repair.

Source inputs remain byte-identical. Effects use actual core DDS sprite art;
Unity emission/lifetime adapters are recorded separately from native EST playback.
"""
from pathlib import Path
import hashlib, json, struct, sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/original-remake'))
from export_assets import A,OUT,RES,guid,converter,motion,skin,UNIT
from native import Mesh
SOURCE=Path('/workspace/work/full-asset-inspection')
WORK=Path('/workspace/work/playtest-repair')
ROWS=[json.loads(s) for s in (SOURCE/'inventory.jsonl').read_text().splitlines()]
LEDGER=[]

def trim_human_banks():
    """Keep bound human motions; leave every original MOT input untouched."""
    common={'000','010','011','012','020','021','030','032','040','050','130'}
    retained={}
    for package,allowed in [('hm09',common|{'037'}),('hm2d',common|{'080'}),('hm44',common),('hm0c',{'000','081'})]:
        path=RES/package/'Poses.bytes'
        if not path.exists():continue
        raw=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',raw);offset=16;records=[];names=[]
        for _ in range(count):
            start=offset;n=struct.unpack_from('<I',raw,offset)[0];offset+=4;name=raw[offset:offset+n].decode();offset+=n;samples=struct.unpack_from('<I',raw,offset)[0];offset+=12+samples*bones*40
            if name.split('_')[-1] in allowed:records.append(raw[start:offset]);names.append(name)
        assert offset==len(raw) and records
        path.write_bytes(struct.pack('<4sIII',magic,version,bones,len(records))+b''.join(records));retained[package]=names
    return retained

def native(group,package,selected=None,all_motions=False):
    rows=[r for r in ROWS if r['group']==group and r['package']==package]
    target=RES/package;target.mkdir(exist_ok=True)
    md=next(r for r in rows if r['type']=='MD');raw=(SOURCE/md['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==md['sha256']
    model=converter.read_model(raw,[dict(r,path=r.get('cache','')) for r in rows],package,SOURCE,target,allow_vertex_only=True)
    native_model=json.loads(json.dumps(model))
    for b in model['bones']:b['position']=(np.asarray(b['position'])*[-UNIT,UNIT,UNIT]).tolist()
    for p in model['parts']:
        p['positions']=(np.asarray(p['positions']).reshape(-1,3)*[-UNIT,UNIT,UNIT]).ravel().tolist()
        p['indices']=np.asarray(p['indices']).reshape(-1,3)[:,[0,2,1]].ravel().tolist()
    if selected is not None:model['visibleGroups']=selected
    model['sourceUnits']='Metres; native X reflected, +Z preserved'
    (target/'Model.json').write_text(json.dumps(model,separators=(',',':')))
    nb=len(model['bones']);clips=[];names=set()
    for row in rows:
        if row['type']!='MOT' or not row.get('frames') or row.get('maxBone',999)>=nb or row['name'] in names:continue
        if not all_motions and not row['name'].endswith(('_000','_010','_020','_030','_040','_050')):continue
        names.add(row['name']);clips.append(row)
    idle=next((r for r in clips if r['name'].endswith('_000')),None)
    if idle:
        _,_,channels=motion.parse((SOURCE/idle['cache']).read_bytes(),nb,allow_duplicate_channels=True);pose=motion.sample(native_model,channels,0)
    else:pose=motion.sample(native_model,{},0)
    parts=skin(model,pose);points=np.concatenate([v for p,v in zip(model['parts'],parts) if selected is None or int(p['name'].split('-')[1]) in selected]);lo=points.min(0);hi=points.max(0)
    if clips:
        with (target/'Poses.bytes').open('wb') as f:
            f.write(struct.pack('<4sIII',b'OPB1',1,nb+1,len(clips)))
            for row in clips:
                raw=(SOURCE/row['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
                frames,loop,ch=motion.parse(raw,nb,allow_duplicate_channels=True);n=max(2,(frames-1)*2+1);bank=np.asarray([motion.sample(native_model,ch,t) for t in np.linspace(0,frames-1,n)])
                for t in range(1,n):
                    flip=np.sum(bank[t-1,:,3:7]*bank[t,:,3:7],1)<0;bank[t,flip,3:7]*=-1
                assert np.isfinite(bank).all();name=row['name'].encode();f.write(struct.pack('<I',len(name)));f.write(name);f.write(struct.pack('<IfI',n,max(1,frames-1)/30,int(loop)));f.write(bank.astype('<f4').tobytes())
    meshes=[]
    for i,(p,v) in enumerate(zip(model['parts'],parts)):
        if selected is not None and int(p['name'].split('-')[1]) not in selected:continue
        if not p['indices']:continue
        m=Mesh();m.v=v.tolist();m.c=np.asarray(p['colors']).reshape(-1,4)[:,:3].tolist();m.uv=np.asarray(p['uv']).reshape(-1,2).tolist();m.bones=[0]*len(v);m.tri=np.asarray(p['indices']).reshape(-1,3).tolist();path=OUT/'Meshes'/(package+'-selected-'+str(i)+'.asset');m.write(path)
        mat=OUT/'Materials'/(package+'-'+str(p['texture'])+'.mat')
        if not mat.exists():
            template=(OUT/'Materials/vta0-0.mat').read_text();template=template.replace(guid(RES/'vta0/Texture-0.png'),guid(target/('Texture-'+str(p['texture'])+'.png')));mat.write_text(template.replace('Original vta0 paint','Original '+package+' paint'))
        meshes.append(dict(mesh=guid(path),material=guid(mat)))
    entry=dict(package=package,group=group,sourceSHA256=md['sha256'],visibleGroups=selected,boundsMin=lo.tolist(),boundsMax=hi.tolist(),meshes=meshes,motions=[dict(name=r['name'],sha256=r['sha256']) for r in clips]);LEDGER.append(entry);print('CONVERTED',package,len(meshes),len(clips),flush=True);return entry

def run():
    # Alternate bodies, skeleton form and detached umbrella were visibly
    # inspected individually before choosing these masks. Player groups are
    # separate body/head/tail/markings and must all remain present.
    for p,groups in [('em00',[0,3]),('em01',[0,3]),('em02',[0,3]),('em03',[0,3]),('em04',[0,3]),('em11',[0,2]),('hm29',[0]),('vt6a',[0])]:
        path=RES/p/'Model.json';d=json.loads(path.read_text());d['visibleGroups']=groups;path.write_text(json.dumps(d,separators=(',',':')));LEDGER.append(dict(package=p,visibleGroups=groups,reason='Source group diagnostics; mutually exclusive body/form/prop selection'))
    # Human groups are not uniformly LODs: hm05's visible body is group 1,
    # and hm68's head/hands are separate from its clothing. Preserve those
    # pieces and their inspected ink shells while omitting detached props.
    human_masks={'hm00':[0,1],'hm01':[0,1],'hm05':[1,2],'hm09':[0,1],'hm0f':[0],'hm29':[0,1],'hm44':[0],'hm68':[0,1,2,3]}
    for p,mask in human_masks.items():
        path=RES/p/'Model.json';d=json.loads(path.read_text());available={int(r['name'].split('-')[1]) for r in d['parts']};d['visibleGroups']=[i for i in mask if i in available];path.write_text(json.dumps(d,separators=(',',':')))
    native('HM','hm09',[0,1],all_motions=True)
    native('HM','hm44',[0],all_motions=True)
    native('HM','hm2d',[0,1,2,3],all_motions=True)
    native('HM','hm0c',[0,2],all_motions=True)
    native('PL','pl0d',all_motions=False)
    for i in range(0x20,0x2f):
        groups=[0,1] if i==0x24 else [0] if i<0x25 or i>=0x2a else [3]
        native('WP','wp'+format(i,'02x'),groups,all_motions=True)
    player_solar=A/'OkamiRemaster/Player/Resources/NativePlayer/wp24/Model.json';d=json.loads(player_solar.read_text());d['visibleGroups']=[0,1];player_solar.write_text(json.dumps(d,separators=(',',':')))
    for p in ['vta7','vtb1','vta9','vt9e','vt9f','vt3c']:native('VT',p)
    # A clean portion of original book paper, not the earlier bark-like crop.
    row=next(r for r in ROWS if r['package']=='EmFileRoll' and r['name']=='EmFileRoll-255' and r['type']=='DDS');im=Image.open(SOURCE/row['cache']);w,h=im.size;crop=(int(w*.15),int(h*.12),int(w*.85),int(h*.88));im.crop(crop).save(RES/'UI/Paper.png');LEDGER.append(dict(role='UI paper',sourceSHA256=row['sha256'],crop=crop))
    core=json.loads((WORK/'extra-inventory.json').read_text());effects=RES/'Effects';effects.mkdir(exist_ok=True)
    for label,name in [('Leaf','fallingleaf'),('Blossom','sakura'),('Steam','fog1'),('Wind','wind_03'),('Cloud','cloud_02'),('Flame','fire_11'),('Spark','water_spl00')]:
        r=next(r for r in core if r['type']=='DDS' and r['name']==name);im=Image.open(r['cache']);im.save(effects/(label+'.png'));LEDGER.append(dict(role='effect '+label,name=name,sourceSHA256=r['sha256'],parent=r['parent']))
    kept=trim_human_banks()
    for entry in LEDGER:
        if entry.get('package') in kept and entry.get('motions'):entry['motions']=[r for r in entry['motions'] if r['name'] in kept[entry['package']]]
    for p in [OUT,*OUT.rglob('*')]:
        if not p.name.endswith('.meta'):guid(p)
    Path(__file__).with_name('asset-conversions.json').write_text(json.dumps(LEDGER,indent=2))

if __name__=='__main__':run()
