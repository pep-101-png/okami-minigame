Shader "Sunward/Painted Dawn Sky"
{
 Properties { _Zenith("Indigo sky",Color)=(.15,.34,.48,1) _Horizon("Apricot mist",Color)=(.94,.73,.48,1) _Cloud("Rice paper clouds",Color)=(1,.92,.74,1) }
 SubShader
 {
  Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
  Cull Off ZWrite Off
  Pass
  {
   HLSLPROGRAM
   #pragma vertex Vert
   #pragma fragment Frag
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   CBUFFER_START(UnityPerMaterial)
   half4 _Zenith,_Horizon,_Cloud;
   CBUFFER_END
   struct A { float4 positionOS:POSITION; };
   struct V { float4 positionCS:SV_POSITION; float3 direction:TEXCOORD0; };
   V Vert(A v) { V o; o.positionCS=TransformObjectToHClip(v.positionOS.xyz); o.direction=v.positionOS.xyz; return o; }
   float Wave(float a) { return sin(a)*.5+sin(a*2.13+1.7)*.24+sin(a*4.19)*.12; }
   half4 Frag(V i):SV_Target
   {
    float3 d=normalize(i.direction);float altitude=d.y;
    float angle=atan2(d.z,d.x);
    half3 color=lerp(_Horizon.rgb,_Zenith.rgb,pow(saturate(altitude),.55));
    // Three painted, distant ridges. No geometry, collision, or scene population.
    float farRidge=.018+Wave(angle*7)*.018;
    float nearRidge=-.025+Wave(angle*11+2)*.025;
    color=lerp(color,half3(.46,.57,.57),1-smoothstep(farRidge-.008,farRidge+.008,altitude));
    color=lerp(color,half3(.32,.46,.48),1-smoothstep(nearRidge-.006,nearRidge+.006,altitude));
    float ribbon=sin(altitude*55+Wave(angle*4)*1.8);
    float broken=smoothstep(-.15,.65,Wave(angle*9+altitude*6));
    float clouds=smoothstep(.82,.98,ribbon)*broken*smoothstep(.02,.13,altitude)*(1-smoothstep(.38,.68,altitude));
    color=lerp(color,_Cloud.rgb,clouds*.58);
    float sunDot=dot(d,normalize(float3(-.55,.28,.8)));
    color+=half3(.20,.10,.035)*pow(saturate(sunDot),24);
    color=lerp(color,half3(1,.90,.59),smoothstep(.99915,.99945,sunDot));
    return half4(color,1);
   }
   ENDHLSL
  }
 }
}
