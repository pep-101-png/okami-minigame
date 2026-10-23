"""Original quiet bowed-string melody, wood practice taps and wordless chatter.
These are synthesized sound design, not recordings of a professional violin.
"""
from pathlib import Path
import hashlib,math,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Sunward-Unity/Assets/Sunward/Generated/LivingVillagers';RATE=22050

def write(name,samples):
 path=OUT/(name+'.wav');samples=np.clip(samples,-.92,.92)
 with wave.open(str(path),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes((samples*32767).astype('<i2').tobytes())
 meta=Path(str(path)+'.meta');g=hashlib.md5(str(path.relative_to(ROOT)).encode()).hexdigest();meta.write_text('fileFormatVersion: 2\nguid: '+g+'\nAudioImporter:\n  externalObjects: {}\n  serializedVersion: 7\n  defaultSettings:\n    serializedVersion: 2\n    loadType: 0\n    sampleRateSetting: 0\n    sampleRateOverride: 44100\n    compressionFormat: 1\n    quality: 0.8\n    conversionMode: 0\n  platformSettingOverrides: {}\n  forceToMono: 1\n  normalize: 0\n  preloadAudioData: 1\n  loadInBackground: 0\n  ambisonic: 0\n  3D: 1\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n');return g

def generate():
 OUT.mkdir(exist_ok=True);rng=np.random.default_rng(421)
 music=np.zeros(RATE*24)
 # A restrained pentatonic phrase; a warm body-filtered harmonic series and
 # vibrato/slow bow envelopes avoid the prior metallic cue-like timbre.
 notes=[(62,0,1.5),(65,1.5,1),(67,2.5,2),(69,4.5,1.5),(67,6,2),(65,8,1),(62,9,2.5),(60,12,1.5),(62,13.5,1),(65,14.5,2),(67,16.5,1.5),(65,18,2),(62,20,3)]
 for midi,start,length in notes:
  t=np.arange(int(RATE*length))/RATE;freq=440*2**((midi-69)/12);phase=np.cumsum((math.tau*freq/RATE)*(1+.0025*np.sin(t*math.tau*5)))
  tone=np.zeros(len(t))
  for k in range(1,8):
   # Bow bridge body resonance; higher harmonics reduced to keep night music soft.
   amp=(1/k**1.65)*(.45+.55*math.exp(-((k*freq-1700)/1600)**2));tone+=np.sin(phase*k)*amp
  env=np.minimum(1,t/.18)*np.minimum(1,(length-t)/.25)
  tone=(tone*.17+rng.normal(0,.0006,len(t)))*env*(.94+.06*np.sin(t*math.tau*1.3))
  i=int(start*RATE);music[i:i+len(t)]+=tone
 # Both loop endpoints have half a second of silence, avoiding a seam click.
 music[:RATE//3]*=np.linspace(0,1,RATE//3);music[-RATE//3:]*=np.linspace(1,0,RATE//3)
 chatter=np.zeros(int(RATE*2.4))
 for start,dur,freq,vowel in [(.10,.23,146,0),(.38,.15,153,1),(.60,.27,138,2),(1.28,.22,205,1),(1.58,.30,192,0),(1.98,.15,201,2)]:
  t=np.arange(int(dur*RATE))/RATE;voice=np.zeros(len(t));f1,f2=[(600,1100),(400,1700),(700,1300)][vowel]
  for k in range(1,22):
   hz=k*freq;amp=(math.exp(-((hz-f1)/260)**2)*.6+math.exp(-((hz-f2)/450)**2)*.3+.015)/k
   voice+=np.sin(math.tau*freq*k*t+np.sin(t*math.tau*5)*.1)*amp
  voice*=np.sin(np.linspace(0,math.pi,len(t)))**1.3*.35;i=int(start*RATE);chatter[i:i+len(t)]+=voice
 t=np.arange(int(.18*RATE))/RATE
 tap=(np.sin(t*math.tau*320)*.3+np.sin(t*math.tau*735)*.13+rng.normal(0,.16,len(t)))*np.exp(-t*35)*np.minimum(t/.003,1)
 return {'music':write('Foodhall-bowed-pentatonic',music),'conversation':write('Market-wordless-conversation',chatter),'practice':write('Dojo-wood-contact',tap)}
if __name__=='__main__':print(generate())
