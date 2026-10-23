Shader "Sunward/Spectral Flame"
{
 Properties { _BaseColor("Flame tint",Color)=(1,1,1,1) }
 SubShader
 {
  Tags {"RenderPipeline"="UniversalPipeline" "Queue"="Transparent+10" "RenderType"="Transparent"}
  Blend SrcAlpha One
  ZWrite Off Cull Off
  Pass
  {
   Tags {"LightMode"="UniversalForward"}
   HLSLPROGRAM
   #pragma vertex Vert
   #pragma fragment Frag
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   CBUFFER_START(UnityPerMaterial)
   half4 _BaseColor;
   CBUFFER_END
   struct A {float4 p:POSITION;float4 color:COLOR;float2 uv:TEXCOORD0;};
   struct V {float4 p:SV_POSITION;float4 color:COLOR;float2 uv:TEXCOORD0;};
   V Vert(A i) {V o;o.p=TransformObjectToHClip(i.p.xyz);o.color=i.color*_BaseColor;o.uv=i.uv;return o;}
   half4 Frag(V i):SV_Target
   {
    float edge=pow(saturate(1-abs(i.uv.y*2-1)),.55);
    float shimmer=.9+.1*sin(i.uv.x*24-_Time.y*5);
    return half4(i.color.rgb*1.7,i.color.a*edge*shimmer);
   }
   ENDHLSL
  }
 }
}
