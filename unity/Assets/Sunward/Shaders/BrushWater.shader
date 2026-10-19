Shader "Sunward/Brush River" {
 Properties {_FlowMap("Painted currents",2D)="white"{} _FlowNormal("Linear current relief",2D)="bump"{} _BaseColor("River wash",Color)=(.32,.62,.66,.7)}
 SubShader {Tags{"RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent"}Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Off
 Pass {Tags{"LightMode"="UniversalForward"}
 HLSLPROGRAM
 #pragma vertex Vert
 #pragma fragment Frag
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareOpaqueTexture.hlsl"
 TEXTURE2D(_FlowMap);SAMPLER(sampler_FlowMap);TEXTURE2D(_FlowNormal);SAMPLER(sampler_FlowNormal);
 CBUFFER_START(UnityPerMaterial)
 float4 _BaseColor;
 CBUFFER_END
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;};struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float3 world:TEXCOORD1;float fog:TEXCOORD2;};
 V Vert(A i){V o;o.world=TransformObjectToWorld(i.p.xyz);o.p=TransformWorldToHClip(o.world);o.uv=i.uv;o.fog=ComputeFogFactor(o.p.z);return o;}
 float Raw(float z){return 1.1*sin(z*.13)+.45*sin(z*.31)+2*exp(-pow((z+8)/4,2));}
 half4 Frag(V i):SV_Target{float z=-i.world.z,cross=exp(-pow(26./4.,2)),a=(Raw(12)-Raw(-14)*cross)/(1-cross*cross),b=Raw(-14)-a*cross;float cx=-23+Raw(z)-a*exp(-pow((z-12)/4,2))-b*exp(-pow((z+14)/4,2));float width=2.45+.4*sin(z*.17+.4)+.25*cos(z*.31),n=abs(i.world.x-cx)/width,depth=(1-smoothstep(.56,1.12,n))*1.3;clip(depth-.01);float travel=i.uv.y-_Time.y*.75,streak=pow(max(0,sin(travel*6+sin(i.uv.x*35)*.7)),14)*(.2+.6*pow(sin(i.uv.x*21),2));float shore=pow(saturate(n),10)*(.4+.3*sin(travel*7));float3 c=lerp(float3(.50,.73,.67),float3(.18,.43,.49),smoothstep(.08,1.3,depth));c=lerp(c,float3(.90,.94,.84),saturate(streak*.4+shore));c+=sin(travel*11+i.uv.x*45)*.017;
 float2 screenUV=GetNormalizedScreenSpaceUV(i.p);
 float sceneDepth=LinearEyeDepth(SampleSceneDepth(screenUV),_ZBufferParams);
 float waterEye=-TransformWorldToView(i.world).z;
 float gap=max(0,sceneDepth-waterEye);
 float shoreline=(1-smoothstep(.015,.35,gap))*(.45+.15*sin(travel*8+i.world.x*3));
 float2 ripple=float2(sin(i.world.z*3-_Time.y*2),cos(i.world.x*5+_Time.y))*min(.0015,gap*.001);
 half3 refracted=SampleSceneColor(saturate(screenUV+ripple));
 float2 flowUV=float2((i.world.x-cx)/(width*2)+.5,z*.045-_Time.y*.055);
 half3 paintedCurrent=SAMPLE_TEXTURE2D(_FlowMap,sampler_FlowMap,flowUV).rgb;
 float3 flowNormal=SAMPLE_TEXTURE2D(_FlowNormal,sampler_FlowNormal,flowUV).rgb*2-1;
 float3 normal=normalize(float3(flowNormal.x*.12+sin(travel*3)*.035,1,flowNormal.y*.12+cos(i.world.x*6+travel*4)*.045));
 float3 view=GetWorldSpaceNormalizeViewDir(i.world);
 float fresnel=pow(1-saturate(dot(view,normal)),4);
 half3 reflection=GlossyEnvironmentReflection(reflect(-view,normal),.35,1);
 c=lerp(refracted,c,1-exp(-max(.08,gap)*.85));
 c=lerp(c,paintedCurrent,.38);
 c=lerp(c,reflection+float3(.15,.23,.23),fresnel*.28);
 c=lerp(c,float3(.93,.95,.87),saturate((paintedCurrent.r-.62)*2.5)*.42);
 c=lerp(c,float3(.90,.94,.84),saturate(shoreline+streak*.12));
 Light sun=GetMainLight();float glint=pow(saturate(dot(normal,normalize(sun.direction+view))),90);
 c+=sun.color*glint*.20;
 return half4(MixFog(c,i.fog),lerp(.35,.90,saturate(gap)));
}
 ENDHLSL
 }}
}
