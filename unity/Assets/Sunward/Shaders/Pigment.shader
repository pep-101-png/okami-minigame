Shader "Sunward/Surface Pigment" {
 Properties {_DetailMap("Connected watercolour artwork",2D)="white"{} _DetailNormal("Linear RGB relief",2D)="bump"{} _PathMap("Path wash",2D)="white"{} _PathNormal("Path relief",2D)="bump"{} _ArtStrength("Artwork",Range(0,1))=0 _ArtTiling("World paint scale",Float)=.35 _NormalStrength("Normal relief",Range(0,1))=.3 _TerrainBlend("Terrain blend",Float)=0 _BaseMap("Painted wash",2D)="white"{} _BaseColor("Pigment",Color)=(1,1,1,1) _Cutoff("Paper cutout",Range(0,1))=.01 _Pigment("Dry brush strength",Range(0,1))=.22 _Wind("Leaf wind",Float)=0 _SurfaceKind("Surface family",Float)=0 _Relief("Paint relief",Range(0,1))=.08 [Enum(UnityEngine.Rendering.CullMode)]_Cull("Cull",Float)=2 [Enum(UnityEngine.Rendering.BlendMode)]_SrcBlend("Source",Float)=1 [Enum(UnityEngine.Rendering.BlendMode)]_DstBlend("Destination",Float)=0 _ZWrite("Depth write",Float)=1}
 SubShader {Tags{"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"} Cull[_Cull] Blend[_SrcBlend][_DstBlend] ZWrite[_ZWrite]
 Pass {Name "PaintedForward" Tags{"LightMode"="UniversalForward"}
 HLSLPROGRAM
 #pragma vertex Vert
 #pragma fragment Frag
 #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
 #pragma multi_compile_fragment _ _SHADOWS_SOFT
 #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
 #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
 #pragma multi_compile_fog
 #pragma multi_compile_instancing
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 TEXTURE2D(_DetailMap);SAMPLER(sampler_DetailMap);TEXTURE2D(_DetailNormal);SAMPLER(sampler_DetailNormal);TEXTURE2D(_PathMap);SAMPLER(sampler_PathMap);TEXTURE2D(_PathNormal);SAMPLER(sampler_PathNormal);
 TEXTURE2D(_BaseMap);SAMPLER(sampler_BaseMap);
 CBUFFER_START(UnityPerMaterial)
 float4 _BaseMap_ST,_BaseColor;float _ArtStrength,_ArtTiling,_NormalStrength,_TerrainBlend;float _Cutoff,_Pigment,_Wind,_SurfaceKind,_Relief,_Cull,_SrcBlend,_DstBlend,_ZWrite;
 CBUFFER_END
 float3 PaintColor(float3 world,float3 weights){return SAMPLE_TEXTURE2D(_DetailMap,sampler_DetailMap,world.zy).rgb*weights.x+SAMPLE_TEXTURE2D(_DetailMap,sampler_DetailMap,world.xz).rgb*weights.y+SAMPLE_TEXTURE2D(_DetailMap,sampler_DetailMap,world.xy).rgb*weights.z;}
 float3 PaintNormal(float3 world,float3 weights,float3 geometric){float3 a=SAMPLE_TEXTURE2D(_DetailNormal,sampler_DetailNormal,world.zy).rgb*2-1,b=SAMPLE_TEXTURE2D(_DetailNormal,sampler_DetailNormal,world.xz).rgb*2-1,c=SAMPLE_TEXTURE2D(_DetailNormal,sampler_DetailNormal,world.xy).rgb*2-1;float3 n=float3(a.z*sign(geometric.x),a.y,a.x)*weights.x+float3(b.x,b.z*sign(geometric.y),b.y)*weights.y+float3(c.x,c.y,c.z*sign(geometric.z))*weights.z;return normalize(n+geometric*.001);}
 float Hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 float Noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(Hash(i),Hash(i+float2(1,0)),f.x),lerp(Hash(i+float2(0,1)),Hash(i+1),f.x),f.y);}
 struct A{float4 positionOS:POSITION;float3 normalOS:NORMAL;float2 uv:TEXCOORD0;float4 color:COLOR;UNITY_VERTEX_INPUT_INSTANCE_ID};
 struct V{float4 positionCS:SV_POSITION;float3 world:TEXCOORD0;float3 normal:TEXCOORD1;float2 uv:TEXCOORD2;float4 color:COLOR;float fog:TEXCOORD3;UNITY_VERTEX_INPUT_INSTANCE_ID};
 V Vert(A v){V o;UNITY_SETUP_INSTANCE_ID(v);UNITY_TRANSFER_INSTANCE_ID(v,o);float3 p=TransformObjectToWorld(v.positionOS.xyz);p.x+=sin(_Time.y*1.3+p.x*.7-p.z*.45)*.065*v.uv.y*_Wind;o.world=p;o.positionCS=TransformWorldToHClip(p);o.normal=TransformObjectToWorldNormal(v.normalOS);o.uv=TRANSFORM_TEX(v.uv,_BaseMap);o.color=v.color;o.fog=ComputeFogFactor(o.positionCS.z);return o;}
 half4 Frag(V i):SV_Target{UNITY_SETUP_INSTANCE_ID(i);half4 base=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,i.uv)*_BaseColor*i.color;clip(base.a-_Cutoff);float wash=Noise(i.world.xz*.70+i.world.y*.45),dry=Noise(float2(i.world.x*22+i.world.y*3,i.world.y*2+i.world.z*3));base.rgb*=1+_Pigment*((wash-.5)*.45+(dry-.5)*.13);base.rgb=lerp(base.rgb,float3(.97,.95,.88),smoothstep(.70,.96,dry)*_Pigment*.15);Light light=GetMainLight(TransformWorldToShadowCoord(i.world));float3 normal=normalize(i.normal);
 if(_ArtStrength>.01){
 float3 weights=pow(abs(normal),4);weights/=max(.001,weights.x+weights.y+weights.z);
 float3 painted=PaintColor(i.world*_ArtTiling,weights);
 float3 paintedNormal=PaintNormal(i.world*_ArtTiling,weights,normal);
 if(_TerrainBlend>.5){float path=smoothstep(-.015,.09,i.color.r-i.color.g);float3 dust=SAMPLE_TEXTURE2D(_PathMap,sampler_PathMap,i.world.xz*.22).rgb;painted=lerp(painted,dust,path);float3 pn=SAMPLE_TEXTURE2D(_PathNormal,sampler_PathNormal,i.world.xz*.22).rgb*2-1;paintedNormal=normalize(lerp(paintedNormal,float3(pn.x,pn.z,pn.y),path));}
 base.rgb*=lerp(float3(1,1,1),painted*1.18,_ArtStrength);
 normal=normalize(lerp(normal,paintedNormal,_NormalStrength*_ArtStrength));
 }

 // World-space wash detail complements the original low-resolution maps; no
 // invented 4K source textures. Derivatives keep relief subtle and scale aware.
 float grain=Noise(float2(i.world.y*22+i.world.x*.65,i.world.z*2.3));
 float stone=Noise(i.world.xz*8+i.world.y*3)*.65+Noise(i.world.xz*27)*.35;
 float family=_SurfaceKind;
 float detail=family>.5&&family<1.5?grain:stone;
 float3 dpdx=ddx(i.world),dpdy=ddy(i.world);
 float3 r1=cross(dpdy,normal),r2=cross(normal,dpdx);
 float determinant=dot(dpdx,r1);
 float3 gradient=sign(determinant)*(ddx(detail)*r1+ddy(detail)*r2)/max(abs(determinant),.0001);
 normal=normalize(normal-gradient*_Relief*.22);
 base.rgb*=1+(detail-.5)*(_SurfaceKind==1?.09:.06);
 float contour=pow(1-saturate(abs(dot(normal,GetWorldSpaceNormalizeViewDir(i.world)))),5);
 float inkEdge=contour*(.14+Noise(i.world.xy*5)*.11);
 base.rgb*=1-inkEdge;
 float diffuse=smoothstep(-.25,.90,dot(normal,light.direction));float shadow=lerp(.70,1,light.shadowAttenuation);float3 illumination=SampleSH(normal)*.72+light.color*(.36+diffuse*.48)*shadow;
 #if defined(_ADDITIONAL_LIGHTS)
 uint count=GetAdditionalLightsCount();for(uint l=0;l<count;l++){Light extra=GetAdditionalLight(l,i.world);illumination+=extra.color*extra.distanceAttenuation*(.25+.65*saturate(dot(normal,extra.direction)));}
 #endif
 #if defined(_SCREEN_SPACE_OCCLUSION)
 AmbientOcclusionFactor ao=GetScreenSpaceAmbientOcclusion(GetNormalizedScreenSpaceUV(i.positionCS));
 illumination*=lerp(1,ao.indirectAmbientOcclusion,.65);
 #endif
 half3 rgb=base.rgb*illumination;return half4(MixFog(rgb,i.fog),base.a);}
 ENDHLSL
 }
 UsePass "Universal Render Pipeline/Lit/ShadowCaster"
 UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
