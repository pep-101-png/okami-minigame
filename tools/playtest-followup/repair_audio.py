"""Decode original ADX type-8 frame scales before transcoding; never synthesize sound.

Reference: vgmstream src/meta/adx_keys.h (Okami / Clover type-8 parameters),
src/coding/adx_decoder.c. Sources stay byte-identical. Derivatives receive only
attenuation, DC removal and short edge fades, without pitch/time changes.
"""
from pathlib import Path
import hashlib,json,struct,subprocess,wave,tempfile
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
RES=ROOT/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami'
WORK=Path('/workspace/work/playtest-repair/audio-extracted')

def decode_adx(raw):
    assert raw[:2]==b'\x80\x00'
    version=struct.unpack_from('>H',raw,18)[0]
    if version in (0x0300,0x0400,0x0500):return raw,dict(sourceVersion=hex(version),frameScalesDecrypted=False)
    if version!=0x0408:raise ValueError('Unsupported ADX encryption revision '+hex(version))
    d=bytearray(raw);start=struct.unpack_from('>H',d,2)[0]+4;channels=d[7];samples=struct.unpack_from('>I',d,12)[0]
    assert d[4]==3 and d[5]==18 and d[6]==4
    key=0x49e1;frames=((samples+31)//32)*channels;assert start+frames*18<=len(d)
    for index in range(frames):
        off=start+index*18;scale=struct.unpack_from('>H',d,off)[0]
        struct.pack_into('>H',d,off,(scale^key)&0x1fff)
        key=(key*0x4a57+0x553d)&0x7fff
    d[19]=0
    return bytes(d),dict(sourceVersion=hex(version),frameScalesDecrypted=True,frames=frames,reference='vgmstream Okami type-8 frame-scale decoder')

def metrics(x):
    return dict(rmsDBFS=round(float(20*np.log10(np.sqrt(np.mean(x*x))+1e-12)),3),peak=round(float(np.abs(x).max()),6),clippedFraction=round(float(np.mean(abs(x)>=.999)),8))

def render(raw,target,cue,loop=False):
    clear,info=decode_adx(raw)
    with tempfile.TemporaryDirectory(prefix='sunward-audio-',dir='/tmp') as temp:
        p=Path(temp);(p/'clear.adx').write_bytes(clear)
        subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'clear.adx'),'-ac','2' if loop else '1','-ar','32000','-c:a','pcm_s16le',str(p/'clear.wav')],check=True)
        with wave.open(str(p/'clear.wav')) as f:
            channels=f.getnchannels();rate=f.getframerate();x=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(np.float64).reshape(-1,channels)/32768
        info['decoded']=metrics(x);x-=np.mean(x,axis=0)
        cap=-29 if cue=='step' else -27 if cue in ['cow','pig','rooster'] else -25 if cue.startswith('npc') else -24 if loop else -23
        rms=float(np.sqrt(np.mean(x*x)));peak=float(np.abs(x).max());gain=min(1,10**(cap/20)/max(rms,1e-12),.45/max(peak,1e-12));x*=gain
        if not loop:
            n=min(len(x)//2,int(rate*.008));x[:n]*=np.linspace(0,1,n)[:,None];x[-n:]*=np.linspace(1,0,n)[:,None]
        with wave.open(str(p/'quiet.wav'),'wb') as f:
            f.setnchannels(channels);f.setsampwidth(2);f.setframerate(rate);f.writeframes(np.rint(np.clip(x,-1,1)*32767).astype('<i2').tobytes())
        if loop:subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'quiet.wav'),'-c:a','libvorbis','-q:a','5',str(target)],check=True)
        else:target.write_bytes((p/'quiet.wav').read_bytes())
        info.update(output=metrics(x),gainDB=round(float(20*np.log10(gain)),3),seconds=round(len(x)/rate,4),clearADX_SHA256=hashlib.sha256(clear).hexdigest())
        return info

def run():
    ledger=ROOT/'tools/playtest-repair/audio-provenance.json';records=json.loads(ledger.read_text());report=[]
    for r in records:
        raw=(WORK/('source-'+r['sourceStreamSHA256']+'.adx')).read_bytes();assert hashlib.sha256(raw).hexdigest()==r['sourceStreamSHA256']
        resource=r['resource'];targets=list((RES/'NativeAudio').glob(Path(resource).name+'.*'));target=next(p for p in targets if p.suffix in ['.wav','.ogg']);old=hashlib.sha256(target.read_bytes()).hexdigest();info=render(raw,target,r['cue'],target.suffix=='.ogg')
        r.setdefault('previousBadOutputSHA256',old);r['outputSHA256']=hashlib.sha256(target.read_bytes()).hexdigest();r['decoding']=info;r['assignment']='Original waveform; ADX type-8 frame scales decrypted when flagged; attenuation/DC removal/edge fades only'
        report.append(dict(cue=r['cue'],file=str(target.relative_to(ROOT)),sourceSHA256=r['sourceStreamSHA256'],outputSHA256=r['outputSHA256'],**info))
    ledger.write_text(json.dumps(records,indent=2)+'\n');Path(__file__).with_name('audio-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('Rebuilt',len(report),'original cues; encrypted',sum(r['frameScalesDecrypted'] for r in report),'worst output peak',max(r['output']['peak'] for r in report),flush=True)
if __name__=='__main__':run()
