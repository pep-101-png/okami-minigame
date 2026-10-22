Shader "Sunward/Brush River" {
 Properties {_FlowMap("Painted currents",2D)="white"{} _FlowNormal("Linear current relief",2D)="bump"{} _BaseColor("River wash",Color)=(.32,.62,.66,.7) _RockCount("Seated rock contacts",Float)=0}
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
 float4 _BaseColor;float _RockCount;
 CBUFFER_END
 float4 _RockCenters[16];
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;};
 struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float3 world:TEXCOORD1;float fog:TEXCOORD2;};
 V Vert(A i){V o;o.world=TransformObjectToWorld(i.p.xyz);o.p=TransformWorldToHClip(o.world);o.uv=i.uv;o.fog=ComputeFogFactor(o.p.z);return o;}
 float Square(float x){return x*x;}
 float Raw(float z){return 1.1*sin(z*.13)+.45*sin(z*.31)+2*exp(-Square((z+8)/4));}
 half4 Frag(V i):SV_Target{
 float z=-i.world.z,cross=exp(-Square(26./4.)),a=(Raw(12)-Raw(-14)*cross)/(1-cross*cross),b=Raw(-14)-a*cross;
 float cx=-23+Raw(z)-a*exp(-Square((z-12)/4))-b*exp(-Square((z+14)/4));
 float width=2.45+.4*sin(z*.17+.4)+.25*cos(z*.31),bank=abs(i.world.x-cx)/width;
 float analyticDepth=(1-smoothstep(.56,1.12,bank))*1.3;clip(analyticDepth-.01);
 float time=_Time.y;
 float2 flowUV=float2((i.world.x-cx)/(width*2)+.5,z*.052-time*.026);
 float3 n1=SAMPLE_TEXTURE2D(_FlowNormal,sampler_FlowNormal,flowUV).rgb*2-1;
 float3 n2=SAMPLE_TEXTURE2D(_FlowNormal,sampler_FlowNormal,flowUV*1.83+float2(.31,-time*.011)).rgb*2-1;
 float phase=i.world.z*2.1+time*.85+sin(i.world.x*2.8)*.65;
 float3 normal=normalize(float3(n1.x*.16+n2.y*.09+cos(phase)*.035,1,n1.y*.15+n2.x*.08+sin(phase*.71)*.045));
 float2 screenUV=GetNormalizedScreenSpaceUV(i.p);
 float eye=-TransformWorldToView(i.world).z;
 float sceneDepth=LinearEyeDepth(SampleSceneDepth(screenUV),_ZBufferParams);
 float gap=clamp(sceneDepth-eye,0,60);
 float2 refractionUV=saturate(screenUV+normal.xz*min(.012,gap*.008));
 half3 below=SampleSceneColor(refractionUV);
 half3 painted=SAMPLE_TEXTURE2D(_FlowMap,sampler_FlowMap,flowUV).rgb;
 half3 tint=lerp(_BaseColor.rgb*float3(1.18,1.08,.88),_BaseColor.rgb*float3(.40,.62,.66),saturate(gap*.75));
 float absorption=1-exp(-gap*.66);
 half3 c=lerp(below,tint,absorption*.80);
 c*=lerp(half3(.93,.97,.94),half3(1.05,1.06,1.02),painted.r);
 float3 view=GetWorldSpaceNormalizeViewDir(i.world);float fresnel=pow(1-saturate(dot(view,normal)),4);
 half3 reflection=GlossyEnvironmentReflection(reflect(-view,normal),.22,1);
 c=lerp(c,reflection+float3(.14,.21,.22),fresnel*.17);
 // Long, broken calligraphic ribbons follow the river rather than noisy glitter.
 float ribbonCoord=(i.world.x-cx)*3.7+sin(z*.55-time*.38)*.72;
 float strokeAA=max(.025,fwidth(ribbonCoord));
 float ribbon=1-smoothstep(.10,.10+strokeAA,abs(frac(ribbonCoord)-.5));
 float broken=smoothstep(.12,.58,sin(z*1.2-time*.40)+sin(i.world.x*4)*.3);
 float flow=ribbon*broken*.45;
 float shore=(1-smoothstep(.03,.24,gap))*(.42+.13*sin(phase*.7));
 float foam=shore+flow*.23;
 [loop] for(int k=0;k<min(16,(int)_RockCount);k++){
  float2 delta=i.world.xz-_RockCenters[k].xy;
  // Flow travels towards -Z: two broken wake filaments curl downstream.
  float radius=_RockCenters[k].z;float distance=length(delta);
  float rim=1-smoothstep(.025,.16,abs(distance-radius));
  float downstream=saturate(-delta.y*2+.2);
  float trail=exp(-abs(abs(delta.x)-radius*.7)*15)*exp(-abs(delta.y)*1.5)*step(delta.y,0);
  foam+=(rim*.4+trail*.22)*downstream*(.55+.2*sin(distance*15+phase));
 }
 c=lerp(c,float3(.88,.94,.79),saturate(foam));
 // One broken dark shoreline reads as a brushstroke, not a glowing water border.
 float bankStroke=smoothstep(.94,1.06,bank)*(.56+.18*sin(z*6.2));
 float thinInk=ribbon*broken*.055*(1-saturate(foam));
 c=lerp(c,float3(.025,.055,.040),saturate(bankStroke+thinInk));
 Light sun=GetMainLight();float sparkle=pow(saturate(dot(normal,normalize(sun.direction+view))),76);
 c+=sun.color*sparkle*.085;
 float alpha=lerp(.28,.88,saturate(gap*.65+fresnel*.3));
 return half4(MixFog(c,i.fog),alpha);
 }
 ENDHLSL
 }}
}
