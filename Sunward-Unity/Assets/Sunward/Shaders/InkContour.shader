// Used by explicit, shared-mesh shell renderers on closed environment solids.
// One UniversalForward pass per renderer; no renderer feature or extra camera.
Shader "Sunward/Ink Contour"
{
 Properties
 {
  _InkColor("Sumi ink",Color)=(.018,.014,.010,1)
  _InkPixels("Stroke width at 1080p",Range(.5,6))=2.7
  _InkWorldMax("Maximum world expansion",Range(.001,.15))=.055
  _InkIrregularity("Brush pressure variation",Range(0,.7))=.32
 }
 SubShader
 {
  Tags {"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry-1"}
  Cull Front ZWrite On ZTest LEqual
  Pass
  {
   Name "EnvironmentInkContour"
   Tags {"LightMode"="UniversalForward"}
   HLSLPROGRAM
   #pragma vertex Vert
   #pragma fragment Frag
   #pragma multi_compile_fog
   #pragma multi_compile_instancing
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   CBUFFER_START(UnityPerMaterial)
   half4 _InkColor;
   float _InkPixels,_InkWorldMax,_InkIrregularity;
   CBUFFER_END
   struct A {float4 positionOS:POSITION;float3 normalOS:NORMAL;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct V {float4 positionCS:SV_POSITION;float fog:TEXCOORD0;float3 world:TEXCOORD1;UNITY_VERTEX_INPUT_INSTANCE_ID};
   V Vert(A v)
   {
    V o;UNITY_SETUP_INSTANCE_ID(v);UNITY_TRANSFER_INSTANCE_ID(v,o);
    float3 world=TransformObjectToWorld(v.positionOS.xyz);
    // Inverse-transpose transform preserves thickness under nonuniform scale.
    float3 normalWS=normalize(TransformObjectToWorldNormal(v.normalOS));
    float4 clip=TransformWorldToHClip(world);
    // Width refers to a 1080-line output; supersampling retains the same apparent
    // stroke. A world-space cap prevents large distant hulls/foreground spikes.
    float metresPerPixel=2*max(.01,clip.w)/(max(.001,abs(UNITY_MATRIX_P._m11))*1080);
    float brush=.58+.26*sin(world.x*5.1+world.y*9.3+sin(world.z*2.8))+.16*sin(world.z*12.7-world.x*3.4);
    float pressure=1+_InkIrregularity*(brush-.5)*2;
    float thickness=min(_InkWorldMax,_InkPixels*metresPerPixel*max(.35,pressure));
    // Geometry bounds must include the maximum expanded silhouette.
    o.world=world+normalWS*thickness;
    o.positionCS=TransformWorldToHClip(o.world);o.fog=ComputeFogFactor(o.positionCS.z);
    return o;
   }
   half4 Frag(V i):SV_Target
   {
    UNITY_SETUP_INSTANCE_ID(i);
    // A faint dry-brush variation avoids a perfectly flat black plastic rim.
    float paper=.94+.06*sin(i.world.x*49+i.world.z*31+sin(i.world.y*37));
    return half4(MixFog(_InkColor.rgb*paper,i.fog),1);
   }
   ENDHLSL
  }
 }
}
