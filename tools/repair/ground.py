"""Bind continuous recovered paintings to the real terrain and arena materials."""
from pathlib import Path
import re,hashlib,json,shutil
import numpy as np
from PIL import Image
from scene_data import ROOT,A,World
OUT=A/'OkamiRemaster/Windflower'
def guid(path):
    p=Path(path);meta=Path(str(p)+'.meta')
    if meta.exists():return re.search(r'^guid: (\w+)',meta.read_text(),re.M)[1]
    value=hashlib.sha256(('WindflowerRepair/'+str(p.relative_to(A))).encode()).hexdigest()[:32]
    if p.suffix=='.png':
        template=(OUT/'Textures/Recovered-Meadow.png.meta').read_text();meta.write_text(re.sub(r'^guid: \w+','guid: '+value,template,flags=re.M))
    else:
        kind='NativeFormatImporter:\n  externalObjects: {}\n  mainObjectFileID: 2100000\n' if p.suffix=='.mat' else 'ShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n' if p.suffix=='.shader' else 'MonoImporter:\n  externalObjects: {}\n  serializedVersion: 2\n  defaultReferences: []\n  executionOrder: 0\n' if p.suffix=='.cs' else 'TextScriptImporter:\n  externalObjects: {}\n'
        meta.write_text('fileFormatVersion: 2\nguid: '+value+'\n'+kind+'  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
    return value
def ease(a,b,v):
    t=np.clip((v-a)/(b-a),0,1);return t*t*(3-2*t)
def river(z):
    raw=lambda q:1.1*np.sin(q*.13)+.45*np.sin(q*.31)+2*np.exp(-((q+8)/4)**2)
    cross=np.exp(-(26/4)**2);a=(raw(12)-raw(-14)*cross)/(1-cross*cross);b=raw(-14)-a*cross
    return -23+raw(z)-a*np.exp(-((z-12)/4)**2)-b*np.exp(-((z+14)/4)**2)
def run():
    w=World();rows=list(w.renderers());n=1024;m=768
    x,z=np.meshgrid(np.linspace(-60,70,n),np.linspace(48,-48,m))
    market=(1-ease(3.2,4.1,abs(x)))*(1-ease(22,24,abs(z)))
    west=(1-ease(1.5,2.1,abs(x+32)))*(1-ease(26,28,abs(z)))
    cross=np.maximum(1-ease(1.15,1.8,abs(z+8)),1-ease(1.15,1.8,abs(z-14)))*ease(-34,-32,x)*(1-ease(-14,-12,x))
    trial=(1-ease(2.1,2.8,abs(z)))*ease(0,2,x)*(1-ease(19,21,x))
    arena=1-ease(17.4,18.6,np.sqrt((x-35)**2+z*z))
    road=np.maximum.reduce([market,west,cross,trial,arena])
    width=2.45+.4*np.sin(-z*.17+.4)+.25*np.cos(-z*.31)
    bank=1-ease(width+.3,width+1.65,abs(x-river(-z)))
    pond=np.sqrt(((x+15)/3.05)**2+((z+22)/2.05)**2);bank=np.maximum(bank,1-ease(1.15,1.65,pond))
    mask=OUT/'Textures/Existing-Road-Bank-Mask.png';Image.fromarray(np.uint8(np.stack([road,bank,np.zeros_like(x),np.ones_like(x)],axis=-1)*255)).save(mask)
    grass=OUT/'Textures/Continuous-Grass.png';earth=OUT/'Textures/Continuous-Earth.png'
    shutil.copyfile(OUT/'Textures/Recovered-Meadow.png',grass)
    earthsource=A/'OkamiRemaster/Village/Demo/Textures/91b5ed75723a7cc7.png';shutil.copyfile(earthsource,earth)
    for p in [mask,grass,earth]:guid(p)
    for p in [grass,earth]:
        meta=Path(str(p)+'.meta');s=meta.read_text()
        for axis in ['U','V','W']:s=re.sub(r'wrap'+axis+r': \d+',r'wrap'+axis+': 2',s)
        s=re.sub(r'aniso: \d+','aniso: 8',s);meta.write_text(s)
    meta=Path(str(mask)+'.meta');s=meta.read_text().replace('sRGBTexture: 1','sRGBTexture: 0')
    for axis in ['U','V','W']:s=re.sub(r'wrap'+axis+r': \d+','wrap'+axis+': 1',s)
    meta.write_text(s)
    shader=guid(OUT/'Shaders/ContinuousGround.shader')
    material=OUT/'Materials/Continuous-Ground.mat'
    material.write_text('''%YAML 1.1
%TAG !u! tag:unity3d.com,2011:
--- !u!21 &2100000
Material:
  serializedVersion: 8
  m_Name: Continuous recovered ground paintings
  m_Shader: {fileID: 4800000, guid: '''+shader+''', type: 3}
  m_EnableInstancingVariants: 1
  m_SavedProperties:
    serializedVersion: 3
    m_TexEnvs:
'''+''.join('    - '+slot+':\n        m_Texture: {fileID: 2800000, guid: '+guid(p)+', type: 3}\n        m_Scale: {x: 1, y: 1}\n        m_Offset: {x: 0, y: 0}\n' for slot,p in [('_GrassTex',grass),('_EarthTex',earth),('_LayoutMask',mask)])+'''    m_Ints: []
    m_Floats:
    - _GrassScale: 0.035
    - _EarthScale: 0.05
    m_Colors:
    - _MapBounds: {r: -60, g: -48, b: 130, a: 96}
''');new=guid(material)
    replaced=[]
    from build import Sources
    src=Sources(w.scene)
    for r in rows:
        match=any(g in w.assets and re.search(r'_TerrainBlend: 1\b',w.assets[g].read_text()) for g in r['materials'])
        if not match:continue
        if r['instance']==src.instance:src.patch(r['renderer'],'m_Materials.Array.data[0]',reference='{fileID: 2100000, guid: '+new+', type: 2}')
        elif not r['instance']:
            w.scene.blocks[r['renderer']]=re.sub(r'(  m_Materials:\n  - )[^\n]+',lambda m:m[1]+'{fileID: 2100000, guid: '+new+', type: 2}',w.scene.blocks[r['renderer']])
        else:continue
        replaced.append(r['name'])
    w.scene.save()
    return dict(boundRenderers=replaced,grassSource='Recovered-Meadow.png',earthSource=str(earthsource.relative_to(A)),sourceEarthArchiveIdentity='unverified; retained recovered painting, not a claim of a verified original dirt archive',atlasSamplingRemoved=True,syntheticNoise=False,grassPeriodMetres=1/.035,UnityVerified=False)
if __name__=='__main__':print(json.dumps(run(),indent=2))
