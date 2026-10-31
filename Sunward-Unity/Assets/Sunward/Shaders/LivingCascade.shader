// Flow is evaluated on the GPU from authored UVs: no per-frame mesh allocations.
Shader "Sunward/Living Cascade"
{
 Properties
 {
  _Deep("Painted jade",Color)=(.15,.42,.37,1)
  _Foam("Rice-white foam",Color)=(.91,.94,.76,1)
  _FlowSpeed("Downward flow speed",Range(.1,4))=1.7
 }
 SubShader
 {
  Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
  Cull Off ZWrite On
  Pass
  {
   Name "PaintedFlow"
   Tags { "LightMode"="UniversalForward" }
   HLSLPROGRAM
   #pragma vertex Vert
   #pragma fragment Frag
   #pragma multi_compile_fog
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   CBUFFER_START(UnityPerMaterial)
   half4 _Deep,_Foam;float _FlowSpeed;
   CBUFFER_END
   struct A { float4 positionOS:POSITION;float2 uv:TEXCOORD0; };
   struct V { float4 positionCS:SV_POSITION;float2 uv:TEXCOORD0;float fog:TEXCOORD1; };
   V Vert(A v)
   {
    V o;float3 p=v.positionOS.xyz;
    // Tiny ripples preserve contact with the stone lip and bottom of the river.
    p.z+=sin(v.uv.x*36+v.uv.y*12+_Time.y*2.4)*.018*sin(saturate(v.uv.y)*3.14159);
    o.positionCS=TransformObjectToHClip(p);o.uv=v.uv;o.fog=ComputeFogFactor(o.positionCS.z);return o;
   }
   half4 Frag(V i):SV_Target
   {
    float flow=i.uv.y*21+_Time.y*_FlowSpeed;
    float fibre=sin(i.uv.x*97+sin(i.uv.x*31)*2+flow*.55);
    float streak=smoothstep(.45,.88,fibre)*(.5+.5*sin(flow+i.uv.x*17));
    float foam=smoothstep(.10,.005,i.uv.y)*(.75+.25*sin(_Time.y*3+i.uv.x*37));
    half3 color=lerp(_Deep.rgb,_Foam.rgb,saturate(streak*.72+foam*.86));
    color*=.88+.12*sin(i.uv.x*27+flow*.13);
    return half4(MixFog(color,i.fog),1);
   }
   ENDHLSL
  }
 }
}
