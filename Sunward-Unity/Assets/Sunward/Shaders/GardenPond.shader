Shader "Sunward/Garden Pond" {
 Properties { _BaseColor("Jade water",Color)=(.22,.43,.36,.8) }
 SubShader { Tags {"RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent"} Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Back
 Pass { Tags {"LightMode"="UniversalForward"}
 HLSLPROGRAM
 #pragma vertex Vert
 #pragma fragment Frag
 #pragma multi_compile_fog
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareOpaqueTexture.hlsl"
 CBUFFER_START(UnityPerMaterial)
 float4 _BaseColor;
 CBUFFER_END
 struct A {float4 p:POSITION;float2 uv:TEXCOORD0;};
 struct V {float4 p:SV_POSITION;float3 world:TEXCOORD0;float2 uv:TEXCOORD1;float fog:TEXCOORD2;};
 V Vert(A v){V o;o.world=TransformObjectToWorld(v.p.xyz);o.p=TransformWorldToHClip(o.world);o.uv=v.uv;o.fog=ComputeFogFactor(o.p.z);return o;}
 half4 Frag(V i):SV_Target {
 float2 uv=GetNormalizedScreenSpaceUV(i.p);
 float depth=LinearEyeDepth(SampleSceneDepth(uv),_ZBufferParams)+TransformWorldToView(i.world).z;
 clip(depth-.002);
 float t=_Time.y;
 float2 d=i.world.xz-float2(-15,-22);float r=length(d);
 float ripple=sin(r*19-t*2.2)*exp(-r*.8);
 float3 n=normalize(float3(cos(i.world.x*8+t*.8)*.035+ripple*.025,1,sin(i.world.z*7-t*.6)*.045));
 float3 view=GetWorldSpaceNormalizeViewDir(i.world);
 half3 bottom=SampleSceneColor(saturate(uv+n.xz*min(.006,depth*.009)));
 half3 c=lerp(bottom,_BaseColor.rgb,1-exp(-depth*2.1));
 half3 sky=GlossyEnvironmentReflection(reflect(-view,n),.2,1);
 float fresnel=pow(1-saturate(dot(view,n)),4);c=lerp(c,sky,fresnel*.4);
 float shore=1-smoothstep(.005,.07,depth);c=lerp(c,float3(.62,.72,.55),shore*.22);
 Light light=GetMainLight();c+=light.color*pow(saturate(dot(n,normalize(light.direction+view))),100)*.18;
 return half4(MixFog(c,i.fog),lerp(.40,.86,saturate(depth*2)));
 }
 ENDHLSL
 }}
}
