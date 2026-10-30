"""Restore source-only audio with explicit source IDs and cue-adaptation notes."""
from pathlib import Path
import hashlib,json,struct,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/original-remake'));from export_assets import RES,guid,A
sys.path.insert(0,'/workspace/work/full-asset-inspection');from scan import decrypt,inspect_sound
WORK=Path('/workspace/work/playtest-repair');SOURCE=Path('/workspace/work/full-asset-inspection')
OUT=RES/'NativeAudio';OUT.mkdir(exist_ok=True)
records=[];cues=[]

def convert(cue,raw,source,index,loop=False):
    original=WORK/'audio-extracted'/('source-'+hashlib.sha256(raw).hexdigest()+'.adx');original.write_bytes(raw)
    name=cue+'-'+str(index);target=OUT/(name+('.ogg' if loop else '.wav'))
    sys.path.insert(0,str(ROOT/'tools/playtest-followup'))
    from repair_audio import render
    decoding=render(raw,target,cue,loop)
    g=hashlib.sha256(('OriginalOnly/'+str(target.relative_to(A))).encode()).hexdigest()[:32]
    template=(RES/'Audio/Amaterasu-0.wav.meta').read_text();import re
    template=re.sub(r'^guid: \w+','guid: '+g,template,flags=re.M)
    if loop:template=template.replace('loadType: 0','loadType: 1')
    Path(str(target)+'.meta').write_text(template)
    cues.append(dict(cue=cue,resource='Okami/NativeAudio/'+name))
    records.append(dict(cue=cue,resource='Okami/NativeAudio/'+name,source=source,stream=index,sourceStreamSHA256=hashlib.sha256(raw).hexdigest(),outputSHA256=hashlib.sha256(target.read_bytes()).hexdigest(),assignment='Original waveform; flagged ADX frame scales decrypted; attenuation/DC removal/edge fades only',decoding=decoding))

def ses(bank,indices,cue):
    p=WORK/'source-native/data_pc/se'/bank;data=decrypt(p.read_bytes());clips=inspect_sound(data)['ADX']
    for i in indices:
        r=clips[i];convert(cue,data[r['offset']:r['offset']+r['bytes']],str(p.relative_to(WORK/'source-native')),i)

def afs(path,indices,cue):
    p=WORK/'source-native'/path;data=p.read_bytes();assert data[:4]==b'AFS2';n=struct.unpack_from('<I',data,8)[0];off=16+n*data[6];align=struct.unpack_from('<H',data,12)[0]
    offsets=[int.from_bytes(data[off+i*data[5]:off+(i+1)*data[5]],'little') for i in range(n+1)]
    for i in indices:
        a=(offsets[i]+align-1)//align*align;raw=data[a:offsets[i+1]];assert raw[:2]==b'\x80\x00';convert(cue,raw,path,i,loop=True)

def run():
    for cue,indices in [('bark',[0,1]),('growl',[2]),('hurt',[3]),('jump',[8]),('land',[10]),('dash',[12])]:ses('pl/pl00.ses',indices,cue)
    ses('fs/fs102.ses',[0,1,2,3],'step');ses('wp/wp24.ses',[0],'flame')
    for cue,bank in [('cow','an1f'),('pig','an0e'),('rooster','an0b')]:ses('an/'+bank+'.ses',[0],cue)
    ses('wp/wp25.ses',[0,1],'attack');ses('wp/wp25.ses',[2],'heavy')
    for cue,index in [('impact',20),('heavy-impact',21),('collect',2),('bell',15),('menu',0),('water',8)]:ses('core/core.ses',[index],cue)
    # Voices come from each displayed character's own original archive.
    refs=json.loads((SOURCE/'audio-references.json').read_text());clips={r['sha256']:r for r in json.loads((SOURCE/'audio-clips.json').read_text())}
    for index,package in enumerate(['hm01','hm29','hm44','hm00','hm05','hm68','hm0f']):
        r=next(r for r in refs if r['package']==package and r['group']=='HM');clip=clips[r['sha256']];raw=(SOURCE/clip['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sha256'];convert('npc'+str(index),raw,'HM/'+package,index)
    for index,package in enumerate(['em00','em01','em02','em03','em04','em11']):
        p=WORK/'source-native/data_pc/se/em'/(package+'.ses');data=decrypt(p.read_bytes());candidates=inspect_sound(data)['ADX'];short=[r for r in candidates if r['seconds']<=1.2];r=(short or candidates)[0]
        raw=data[r['offset']:r['offset']+r['bytes']];convert('enemy'+str(index),raw,'data_pc/se/em/'+package+'.ses',index)
    afs('data_pc/bgm/bgm00.afs2',[1],'town');afs('data_pc/bgm/bgm00.afs2',[10],'battle');afs('data_pc/bgm/bgm00.afs2',[5],'housemusic')
    afs('data_pc/se/st/st102.afs2',[0],'wind');afs('data_pc/se/st/st102.afs2',[2],'river')
    (RES/'NativeAudio.json').write_text(json.dumps(dict(cues=cues),indent=2))
    for p in [OUT,*OUT.iterdir()]:
        if not p.name.endswith('.meta'):guid(p)
    Path(__file__).with_name('audio-provenance.json').write_text(json.dumps(records,indent=2))
    print('Original-only cue recordings',len(records))

if __name__=='__main__':run()
