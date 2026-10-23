"""Original quiet bowed-string melody, wood practice taps and wordless chatter.
These are synthesized sound design, not recordings of a professional violin.
"""
from pathlib import Path
import hashlib,math,wave
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Sunward-Unity/Assets/Sunward/Generated/LivingVillagers';RATE=22050

def write(name,samples):
 path=OUT/(name+'.wav');samples=np.clip(samples,-.92,.92).copy()
 fade=min(len(samples)//4,int(RATE*.012));samples[:fade]*=np.linspace(0,1,fade);samples[-fade:]*=np.linspace(1,0,fade)
 with wave.open(str(path),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(RATE);f.writeframes((samples*32767).astype('<i2').tobytes())
 meta=Path(str(path)+'.meta');g=hashlib.md5(str(path.relative_to(ROOT)).encode()).hexdigest();meta.write_text('fileFormatVersion: 2\nguid: '+g+'\nAudioImporter:\n  externalObjects: {}\n  serializedVersion: 7\n  defaultSettings:\n    serializedVersion: 2\n    loadType: 0\n    sampleRateSetting: 0\n    sampleRateOverride: 44100\n    compressionFormat: 1\n    quality: 0.8\n    conversionMode: 0\n  platformSettingOverrides: {}\n  forceToMono: 1\n  normalize: 0\n  preloadAudioData: 1\n  loadInBackground: 0\n  ambisonic: 0\n  3D: 1\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n');return g

def generate():
 OUT.mkdir(exist_ok=True);rng=np.random.default_rng(421)
 # Original 48-second Japanese in-sen phrase: koto-like plucked strings,
 # restrained kokyu-style bowed lead and sparse shakuhachi-style answering notes.
 # These are synthesized instruments, not sampled/recorded performers.
 duration=48;music=np.zeros(RATE*duration)
 def add_note(midi,start,length,gain,kind):
  t=np.arange(int(RATE*length))/RATE;freq=440*2**((midi-69)/12)
  phase=np.cumsum(math.tau*freq/RATE*(1+.0018*np.sin(t*math.tau*4.7)))
  if kind=='pluck':
   tone=sum(np.sin(phase*k+.04*k*k)*np.exp(-t*(1.6+k*.65))/(k**1.55) for k in range(1,12))
   env=np.minimum(1,t/.012)*np.minimum(1,(length-t)/.16)
  elif kind=='bow':
   tone=sum(np.sin(phase*k)/(k**1.85) for k in range(1,7));env=np.minimum(1,t/.28)*np.minimum(1,(length-t)/.42)
  else:
   tone=np.sin(phase)+.14*np.sin(phase*2)+.045*np.sin(phase*3);env=np.sin(np.minimum(1,t/length)*math.pi)**.8
  tone*=env*gain;i=int(start*RATE);count=min(len(tone),len(music)-i)
  if count>0:music[i:i+count]+=tone[:count]
 # E-F-A-B-D uses the characteristic semitone and open fourth, with space
 # between phrases rather than the former continuous synthetic violin drone.
 phrase=[(64,0,1.7),(65,2,1.2),(69,3.5,2.0),(71,6,1.4),(69,8,2.2),(65,10.5,1.2),(64,12,3.0),
         (62,16,2.0),(64,18.5,1.2),(65,20,1.5),(69,22,2.8),(71,26,1.8),(74,28.5,2.8),(71,32,2.0),(69,35,3.0),(65,39,1.8),(64,42,4.0)]
 for midi,start,length in phrase:
  add_note(midi,start+.18,length,.10,'bow')
  add_note(midi+12,start,length+1.0,.105,'pluck')
 for start in range(0,44,4):
  add_note(40 if start%8==0 else 45,start+.05,3.5,.09,'pluck')
  add_note(52 if start%8==0 else 57,start+.8,2.8,.05,'pluck')
 for midi,start in [(76,14.3),(77,24.7),(81,30.6),(76,37.4)]:add_note(midi,start,2.2,.06,'flute')
 music[:RATE//2]*=np.linspace(0,1,RATE//2);music[-RATE:]*=np.linspace(1,0,RATE)
 # No white-noise layer: a quiet voiced exchange with smooth formant-weighted
 # harmonics. Shared runtime phrase gating prevents eighteen overlapping voices.
 chatter=np.zeros(int(RATE*2.8))
 syllables=[(.14,.28,132,0),(.52,.23,146,1),(.86,.34,139,2),(1.55,.30,181,1),(1.98,.30,172,0),(2.39,.23,188,2)]
 for start,dur,freq,vowel in syllables:
  t=np.arange(int(dur*RATE))/RATE;voice=np.zeros(len(t));f1,f2=[(650,1080),(420,1650),(500,1200)][vowel]
  fundamental=freq*(1+.035*np.sin(t*math.pi/dur))
  phase=np.cumsum(math.tau*fundamental/RATE)
  for k in range(1,20):
   hz=k*freq;amp=(.45*math.exp(-((hz-f1)/190)**2)+.20*math.exp(-((hz-f2)/290)**2)+.08)/k**1.2
   voice+=np.sin(phase*k)*amp
  voice*=np.sin(np.linspace(0,math.pi,len(t)))**2*.24;i=int(start*RATE);chatter[i:i+len(t)]+=voice
 t=np.arange(int(.12*RATE))/RATE
 tap=(np.sin(t*math.tau*260)*.22+np.sin(t*math.tau*510)*.06)*np.exp(-t*45)*np.minimum(t/.006,1)
 # A soft sole sample with no pitched oscillator and a bounded 90ms tail.
 n=int(RATE*.09);noise=rng.normal(0,1,n);low=np.zeros(n)
 for i in range(1,n):low[i]=low[i-1]+.07*(noise[i]-low[i-1])
 tt=np.arange(n)/RATE;sole=low*.22*np.sin(np.linspace(0,math.pi,n))*np.exp(-tt*32)
 return {'music':write('Foodhall-bowed-pentatonic',music),'conversation':write('Market-wordless-conversation',chatter),'practice':write('Dojo-wood-contact',tap),'sole':write('Village-soft-sole',sole)}
if __name__=='__main__':print(generate())
