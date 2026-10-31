Shader "Sunward/Recovered Continuous Ground"
{
 Properties
 {
  _GrassTex("Recovered grass painting",2D)="white"{}
  _EarthTex("Recovered earth painting",2D)="white"{}
  _LayoutMask("Existing roads and riverbanks",2D)="black"{}
  _MapBounds("Layout X Z Width Depth",Vector)=(-60,-48,130,96)
  _GrassScale("Grass painting repeats per metre",Float)=.035
  _EarthScale("Earth painting repeats per metre",Float)=.05
 }
 SubShader
 {
  Tags {"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"}
  Cull Back
  Pass
  {
   Name "ContinuousPaint" Tags {"LightMode"="UniversalForwardOnly"}
   HLSLPROGRAM
   #pragma target 3.5
   #pragma vertex Vert
   #pragma fragment Frag
   #pragma multi_compile_instancing
   #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
   #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
   #pragma multi_compile_fog
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
   TEXTURE2D(_GrassTex); SAMPLER(sampler_GrassTex);
   TEXTURE2D(_EarthTex); SAMPLER(sampler_EarthTex);
   TEXTURE2D(_LayoutMask); SAMPLER(sampler_LayoutMask);
   CBUFFER_START(UnityPerMaterial)
   float4 _MapBounds;float _GrassScale,_EarthScale;
   CBUFFER_END
   struct A {float4 positionOS:POSITION;float3 normalOS:NORMAL;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct V {float4 positionCS:SV_POSITION;float3 world:TEXCOORD0;float3 normal:TEXCOORD1;float fog:TEXCOORD2;float4 shadow:TEXCOORD3;UNITY_VERTEX_INPUT_INSTANCE_ID};
   V Vert(A i)
   {
    V o;UNITY_SETUP_INSTANCE_ID(i);UNITY_TRANSFER_INSTANCE_ID(i,o);
    o.world=TransformObjectToWorld(i.positionOS.xyz);o.normal=TransformObjectToWorldNormal(i.normalOS);
    o.positionCS=TransformWorldToHClip(o.world);o.fog=ComputeFogFactor(o.positionCS.z);
    #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
    o.shadow=ComputeScreenPos(o.positionCS);
    #else
    o.shadow=TransformWorldToShadowCoord(o.world);
    #endif
    return o;
   }
   half4 Frag(V i):SV_Target
   {
    UNITY_SETUP_INSTANCE_ID(i);
    float2 uv=i.world.xz;
    // Full paintings, mirrored at their boundaries by the import sampler.
    // No atlas cells, tiny per-metre repeats, old wash grid or synthetic noise.
    half3 a=SAMPLE_TEXTURE2D(_GrassTex,sampler_GrassTex,uv*_GrassScale).rgb;
    float2 rotated=float2(uv.x*.9397-uv.y*.3420,uv.x*.3420+uv.y*.9397);
    half3 b=SAMPLE_TEXTURE2D(_GrassTex,sampler_GrassTex,rotated*(_GrassScale*.73)+float2(.31,.57)).rgb;
    half3 grass=lerp(a,b,.35);
    half3 earth=SAMPLE_TEXTURE2D(_EarthTex,sampler_EarthTex,uv*_EarthScale).rgb;
    half2 mask=SAMPLE_TEXTURE2D(_LayoutMask,sampler_LayoutMask,saturate((uv-_MapBounds.xy)/_MapBounds.zw)).rg;
    float3 normal=normalize(i.normal);
    float slope=1-smoothstep(.58,.85,normal.y);
    half3 paint=lerp(grass,earth,saturate(max(mask.r,max(mask.g,slope))));
    Light light=GetMainLight(i.shadow);
    half shade=saturate(dot(normal,light.direction));
    half3 illumination=SampleSH(normal)*.60+light.color*(.32+.48*shade)*lerp(.65,1,light.shadowAttenuation);
    return half4(MixFog(paint*illumination,i.fog),1);
   }
   ENDHLSL
  }
  UsePass "Universal Render Pipeline/Lit/ShadowCaster"
  UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
 Fallback Off
}
