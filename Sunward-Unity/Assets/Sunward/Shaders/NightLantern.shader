Shader "Sunward/Painted Lantern Paper"
{
 Properties { _BaseColor("Tint",Color)=(1,.58,.20,1) }
 SubShader
 {
  Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
  Pass
  {
   HLSLPROGRAM
   #pragma vertex Vert
   #pragma fragment Frag
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   CBUFFER_START(UnityPerMaterial)
   half4 _BaseColor;
   CBUFFER_END
   float _SunwardNight;
   struct A {float4 positionOS:POSITION;float3 normalOS:NORMAL;float4 color:COLOR;float2 uv:TEXCOORD0;};
   struct V {float4 positionCS:SV_POSITION;float4 color:COLOR;float2 uv:TEXCOORD0;float3 normal:TEXCOORD1;};
   V Vert(A v) {V o;o.positionCS=TransformObjectToHClip(v.positionOS.xyz);o.color=v.color;o.uv=v.uv;o.normal=TransformObjectToWorldNormal(v.normalOS);return o;}
   half4 Frag(V i):SV_Target
   {
    float rib=pow(abs(sin(i.uv.x*18*3.14159265)),24)*.34;
    float fibers=sin(i.uv.y*150+i.uv.x*13)*.015;
    float night=saturate(_SunwardNight);
    half3 paper=i.color.rgb*_BaseColor.rgb*(1-rib+fibers);
    float daytime=.58+.42*saturate(dot(normalize(i.normal),normalize(float3(-.3,.7,.4))));
    return half4(paper*lerp(daytime,1.30,night),1);
   }
   ENDHLSL
  }
  UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
