"""Bind byte-identified original paintings/voices; no synthetic fallback media."""
from pathlib import Path
import hashlib,json,re,subprocess,sys
import numpy as np
from PIL import Image
from export_assets import ROOT,A,OUT,RES,guid
sys.path.insert(0,str(ROOT/'tools/repair'));from scene_data import World,ref
from install_world import patch

def run(source):
    rows=[json.loads(l) for l in (source/'inventory.jsonl').read_text().splitlines()];provenance=[]
    def painting(package,name,path,crop=None):
        e=next(e for e in rows if e['package']==package and e['name']==name and e.get('status')=='DDS decoded');data=(source/e['cache']).read_bytes();assert hashlib.sha256(data).hexdigest()==e['sha256']
        path.parent.mkdir(parents=True,exist_ok=True);im=Image.open(source/e['cache'])
        if crop:
            assert 0<=crop[0]<crop[2]<=im.width and 0<=crop[1]<crop[3]<=im.height,('Crop exceeds original pixels',package,name,im.size,crop)
            im=im.crop(crop)
        im.save(path);g=guid(path);provenance.append(dict(group=e['group'],package=package,name=name,sourceSHA256=e['sha256'],crop=crop,output=str(path.relative_to(A)),outputSHA256=hashlib.sha256(path.read_bytes()).hexdigest()));return g
    textures=OUT/'Textures';textures.mkdir(exist_ok=True)
    grass=painting('r102','neoK001',textures/'Kamiki-grass.png');earth=painting('r102','neoK021',textures/'Kamiki-earth.png')
    floor=painting('r102','ita_01',textures/'Kamiki-floorboards.png')
    water=painting('r102','namitex',textures/'Kamiki-water.png',crop=(0,64,256,256))
    # Native illustrated book paper, retaining original pixels. The existing UI
    # layout/fonts and controls remain functional; no procedural parchment.
    paper=next(e for e in rows if e['group']=='ID' and e['package']=='EmFileRoll' and e['type']=='DDS' and e['name']=='EmFileRoll-42')
    crop=(int(paper['width']*.2),int(paper['height']*.6),int(paper['width']*.8),int(paper['height']*.85))
    paper_guid=painting(paper['package'],paper['name'],RES/'UI/Paper.png',crop=crop)
    painting('wp24','kagami500',RES/'UI/Ink.png')
    ground=A/'OkamiRemaster/Windflower/Materials/Continuous-Ground.mat';text=ground.read_text()
    for slot,g in [('_GrassTex',grass),('_EarthTex',earth)]:text=re.sub(r'(- '+slot+r':\n        m_Texture: )[^\n]+',lambda m:m[1]+'{fileID: 2800000, guid: '+g+', type: 3}',text)
    destination=OUT/'Materials/Original-Ground.mat';destination.write_text(text.replace('Continuous recovered ground paintings','Original Kamiki ground paintings'));groundguid=guid(destination)
    floorMat=OUT/'Materials/Original-Floorboards.mat';template=(OUT/'Materials/vta0-0.mat').read_text();template=template.replace(guid(RES/'vta0/Texture-0.png'),floor);floorMat.write_text(template.replace('Original vta0 paint','Original Kamiki floorboards'));floorguid=guid(floorMat)
    w=World();scene=w.scene;rebound=[]
    sky=OUT/'Shaders/OriginalPaperSky.shader'
    sky.write_text('''Shader "Sunward/Original Paper Sky" {
 Properties { _MainTex("Original illustrated paper",2D)="white"{} }
 SubShader { Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
 Cull Off ZWrite Off
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 struct A { float4 position:POSITION; };
 struct V { float4 position:SV_POSITION;float3 direction:TEXCOORD0; };
 V vert(A i) { V o;o.position=TransformObjectToHClip(i.position.xyz);o.direction=i.position.xyz;return o; }
 half4 frag(V i):SV_Target { float3 d=normalize(i.direction);float2 uv=float2(atan2(d.z,d.x)/6.28318530718+.5,asin(clamp(d.y,-1,1))/3.14159265359+.5);return SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,uv); }
 ENDHLSL }
 } Fallback Off
}''')
    sky_mat=OUT/'Materials/Original-Paper-Sky.mat'
    sky_text=(OUT/'Materials/vta0-0.mat').read_text().replace(guid(OUT/'Shaders/OriginalPaint.shader'),guid(sky)).replace(guid(RES/'vta0/Texture-0.png'),paper_guid).replace('Original vta0 paint','Original illustrated paper sky adaptation');sky_mat.write_text(sky_text)
    for id,b in list(scene.blocks.items()):
        if scene.kind(id)==104:scene.blocks[id]=re.sub(r'm_SkyboxMaterial: [^\n]+','m_SkyboxMaterial: {fileID: 2100000, guid: '+guid(sky_mat)+', type: 2}',b)
    def rebind(r,g):
        reference='{fileID: 2100000, guid: '+g+', type: 2}'
        if r['instance']:patch(scene,r['instance'],r['renderer'],'m_Materials.Array.data[0]',reference=reference)
        else:scene.blocks[r['renderer']]=re.sub(r'(  m_Materials:\n  - )[^\n]+',lambda m:m[1]+reference,scene.blocks[r['renderer']])
        rebound.append(dict(renderer=r['renderer'],instance=r['instance'],name=r['name'],material=g))
    surfaces=json.loads(Path(__file__).with_name('world-install.json').read_text())['retainedLayoutSurfaceRenderers'];keys={(e['instance'],e['renderer']) for e in surfaces}
    water_materials={}
    for r in w.renderers():
        if (r['instance'],r['renderer']) not in keys:continue
        p=w.assets.get(r['materials'][0]) if r['materials'] else None
        if p and p.suffix=='.mat':
            raw=p.read_text()
            if '_FlowMap:' in raw or '_OriginalPaint:' in raw:
                slot='_FlowMap' if '_FlowMap:' in raw else '_OriginalPaint';raw=re.sub(r'(- '+slot+r':\n        m_Texture: )[^\n]+',lambda m:m[1]+'{fileID: 2800000, guid: '+water+', type: 3}',raw)
                base_name=re.sub(r'^(?:Original-)+','',p.name)
                target=OUT/'Materials'/('Original-'+base_name);target.write_text(raw);g=guid(target);water_materials[r['materials'][0]]=g;rebind(r,g);continue
            if p.name=='Continuous-Ground.mat':rebind(r,groundguid);continue
        if r['lo'] is not None and r['lo'][0]>-40 and r['hi'][0]<-28:rebind(r,floorguid)
        else:rebind(r,groundguid)
    # Keep the water-contact script referring to the actual live cloned materials.
    for id,b in list(scene.blocks.items()):
        if 'Assembly-CSharp::Sunward.RiverSurfaceDetail\n' in b:
            for old,new in water_materials.items():b=b.replace(old,new)
            scene.blocks[id]=b
    scene.save()

    models={e['package']:e for e in json.loads(Path(__file__).with_name('original-assets.json').read_text())['models']}
    def feedback(package,radius=None):
        e=models[package];lo=np.asarray(e['boundsMin']);hi=np.asarray(e['boundsMax']);center=(lo+hi)/2;extent=np.maximum(hi-lo,.001)
        if radius:scale=np.ones(3)*(radius*2/max(extent[0],extent[2]))
        else:scale=np.array([2/extent[0],.045/extent[1],2/extent[2]])
        offset=-center*scale
        if not radius:offset[1]=-hi[1]*scale[1]
        return dict(resource='Okami/'+package,offset=dict(zip('xyz',offset.tolist())),scale=dict(zip('xyz',scale.tolist())))
    (RES/'Feedback.json').write_text(json.dumps(dict(ring=feedback('et08'),warning=feedback('et09'),projectile=feedback('et24',.20)),indent=2))
    refs=json.loads((source/'audio-references.json').read_text());clips={e['sha256']:e for e in json.loads((source/'audio-clips.json').read_text())};audio=[]
    for i in range(3):
        r=next(e for e in refs if e['group']=='PL' and e['package']=='pl02' and e['clip']==i);clip=clips[r['sha256']];path=source/clip['path'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
        target=RES/'Audio'/('Amaterasu-'+str(i)+'.wav');target.parent.mkdir(exist_ok=True)
        subprocess.run(['ffmpeg','-v','error','-i',str(path),'-c:a','pcm_s16le','-y',str(target)],check=True)
        meta=Path(str(target)+'.meta');g=hashlib.sha256(('OriginalOnly/'+str(target.relative_to(A))).encode()).hexdigest()[:32]
        meta.write_text('fileFormatVersion: 2\nguid: '+g+'\nAudioImporter:\n  externalObjects: {}\n  serializedVersion: 7\n  defaultSettings:\n    serializedVersion: 2\n    loadType: 0\n    sampleRateSetting: 0\n    sampleRateOverride: 44100\n    compressionFormat: 1\n    quality: 1\n    conversionMode: 0\n    preloadAudioData: 1\n  platformSettingOverrides: {}\n  forceToMono: 0\n  normalize: 0\n  ambisonic: 0\n  loadInBackground: 0\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
        audio.append(dict(**r,output=str(target.relative_to(A)),seconds=clip['seconds'],cueAssignment='Sunward adaptation; original event role unverified'))
    for file in [OUT,*sorted(OUT.rglob('*'))]:
        if not file.name.endswith('.meta'):guid(file)
    report=dict(paintings=provenance,audio=audio,surfaceBindings=rebound,missingAuthenticAudio=['music','ambience','general combat/footstep/bell/collect banks'],feedback='Original ET08/ET09/ET24 models and paintings adapted to existing Sunward cues/lifetimes; not a recovered original EST/SEQ dispatcher.',UIFonts='Existing readable UI fonts retained; original font bank not supplied.',UnityVerified=False)
    Path(__file__).with_name('media-bindings.json').write_text(json.dumps(report,indent=2));print(json.dumps(dict(paintings=len(provenance),audioClips=len(audio),surfaceBindings=len(rebound))))

if __name__=='__main__':run(Path(sys.argv[1]))
