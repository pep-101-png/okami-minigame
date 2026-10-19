"""Original synthetic pentatonic composition and Foley; no sampled/copyright music."""
from pathlib import Path
import numpy as np,wave,json,hashlib
R=Path(__file__).resolve().parents[1];out=R/'Assets/Sunward/Audio';rate=22050;rng=np.random.default_rng(4102)
def save(name,s):
 s=np.clip(s,-.95,.95);p=out/name
 with wave.open(str(p),'wb')as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(rate);f.writeframes((s*32767).astype('<i2').tobytes())
 return {'file':name,'seconds':len(s)/rate,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
n=rate*48;music=np.zeros(n)
notes=[62,69,74,76,81,76,74,69,67,69,74,69,62,67,69,74]
for i in range(64):
 midi=notes[i%16]-(12 if i%8==0 else 0);freq=440*2**((midi-69)/12);t=np.arange(int(rate*2.6))/rate
 tone=sum(np.sin(2*np.pi*freq*h*t+np.exp(-t*6)*.15)/(h**1.65)for h in [1,2,3,4,6]);tone*=np.exp(-t*2.2)*(1-np.exp(-t*180))*.17
 start=int(i*.75*rate);end=min(n,start+len(tone));music[start:end]+=tone[:end-start]
# A restrained sustained flute-like answer, deliberately labelled synthesized.
for i,midi in enumerate([74,76,81,76,74,69]):
 t=np.arange(rate*3)/rate;f=440*2**((midi-69)/12);a=np.sin(np.pi*np.arange(len(t))/len(t))**2
 tone=(np.sin(2*np.pi*f*t+np.sin(t*31)*.012)+rng.normal(0,.035,len(t)))*a*.045
 start=int((13+i*3)*rate);music[start:start+len(tone)]+=tone
music[:rate]*=np.linspace(0,1,rate);music[-rate:]*=np.linspace(1,0,rate)
ambient=np.zeros(rate*24)
for _ in range(45):
 start=rng.integers(0,len(ambient)-rate);t=np.arange(rate//2)/rate
 sound=(rng.normal(0,.15,len(t))*np.exp(-t*20)+np.sin(2*np.pi*rng.choice([780,990,1200])*t)*np.exp(-t*30))*.10
 ambient[start:start+len(t)]+=sound
ambient[:rate]*=np.linspace(0,1,rate);ambient[-rate:]*=np.linspace(1,0,rate)
t=np.arange(int(rate*.09))/rate;step=rng.normal(0,.18,len(t))*np.exp(-t*45)+np.sin(2*np.pi*95*t)*np.exp(-t*60)*.15
report={'license':'Original generated music/Foley for this project; no external samples. Synthesized plucked-string and flute-like placeholders, not recordings of traditional instruments or human market chatter.','audio':[save('market-pentatonic.wav',music),save('market-ambience.wav',ambient),save('resident-footstep.wav',step)]}
(R/'Review/market-audio.json').write_text(json.dumps(report,indent=2));print('Wrote original music, ambience and footstep WAVs')
