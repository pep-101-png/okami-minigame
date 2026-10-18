Shader "Sunward/Surface Pigment" {
 Properties {_BaseMap("Painted wash",2D)="white"{} _BaseColor("Pigment",Color)=(1,1,1,1) _Cutoff("Paper cutout",Range(0,1))=.01 _Pigment("Dry brush strength",Range(0,1))=.22 _Wind("Leaf wind",Float)=0 [Enum(UnityEngine.Rendering.CullMode)]_Cull("Cull",Float)=2 [Enum(UnityEngine.Rendering.BlendMode)]_SrcBlend("Source",Float)=1 [Enum(UnityEngine.Rendering.BlendMode)]_DstBlend("Destination",Float)=0 _ZWrite("Depth write",Float)=1}
 SubShader {Tags{"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"} Cull[_Cull] Blend[_SrcBlend][_DstBlend] ZWrite[_ZWrite]
 Pass {Name "PaintedForward" Tags{"LightMode"="UniversalForward"}
 HLSLPROGRAM
 #pragma vertex Vert
 #pragma fragment Frag
 #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
 #pragma multi_compile_fragment _ _SHADOWS_SOFT
 #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
 #pragma multi_compile_fog
 #pragma multi_compile_instancing
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 TEXTURE2D(_BaseMap);SAMPLER(sampler_BaseMap);
 CBUFFER_START(UnityPerMaterial)
 float4 _BaseMap_ST,_BaseColor;float _Cutoff,_Pigment,_Wind,_Cull,_SrcBlend,_DstBlend,_ZWrite;
 CBUFFER_END
 float Hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
 float Noise(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3-2*f);return lerp(lerp(Hash(i),Hash(i+float2(1,0)),f.x),lerp(Hash(i+float2(0,1)),Hash(i+1),f.x),f.y);}
 struct A{float4 positionOS:POSITION;float3 normalOS:NORMAL;float2 uv:TEXCOORD0;float4 color:COLOR;UNITY_VERTEX_INPUT_INSTANCE_ID};
 struct V{float4 positionCS:SV_POSITION;float3 world:TEXCOORD0;float3 normal:TEXCOORD1;float2 uv:TEXCOORD2;float4 color:COLOR;float fog:TEXCOORD3;UNITY_VERTEX_INPUT_INSTANCE_ID};
 V Vert(A v){V o;UNITY_SETUP_INSTANCE_ID(v);UNITY_TRANSFER_INSTANCE_ID(v,o);float3 p=TransformObjectToWorld(v.positionOS.xyz);p.x+=sin(_Time.y*1.3+p.x*.7-p.z*.45)*.065*v.uv.y*_Wind;o.world=p;o.positionCS=TransformWorldToHClip(p);o.normal=TransformObjectToWorldNormal(v.normalOS);o.uv=TRANSFORM_TEX(v.uv,_BaseMap);o.color=v.color;o.fog=ComputeFogFactor(o.positionCS.z);return o;}
 half4 Frag(V i):SV_Target{UNITY_SETUP_INSTANCE_ID(i);half4 base=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,i.uv)*_BaseColor*i.color;clip(base.a-_Cutoff);float wash=Noise(i.world.xz*.70+i.world.y*.45),dry=Noise(float2(i.world.x*22+i.world.y*3,i.world.y*2+i.world.z*3));base.rgb*=1+_Pigment*((wash-.5)*.45+(dry-.5)*.13);base.rgb=lerp(base.rgb,float3(.97,.95,.88),smoothstep(.70,.96,dry)*_Pigment*.15);Light light=GetMainLight(TransformWorldToShadowCoord(i.world));float diffuse=smoothstep(-.32,.88,dot(normalize(i.normal),light.direction));float shadow=lerp(.70,1,light.shadowAttenuation);float3 illumination=SampleSH(normalize(i.normal))*.55+light.color*(.36+diffuse*.48)*shadow;
 #if defined(_ADDITIONAL_LIGHTS)
 uint count=GetAdditionalLightsCount();for(uint l=0;l<count;l++){Light extra=GetAdditionalLight(l,i.world);illumination+=extra.color*extra.distanceAttenuation*(.25+.65*saturate(dot(normalize(i.normal),extra.direction)));}
 #endif
 half3 rgb=base.rgb*illumination;return half4(MixFog(rgb,i.fog),base.a);}
 ENDHLSL
 }
 UsePass "Universal Render Pipeline/Lit/ShadowCaster"
 UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
