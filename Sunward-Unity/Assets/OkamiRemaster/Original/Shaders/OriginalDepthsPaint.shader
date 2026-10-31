Shader "Sunward/Original Okami Depths Paint" {
 Properties { _MainTex("Original painted animal",2D)="white"{} _Color("Pigment",Color)=(1,1,1,1) _Cutoff("Brush alpha",Range(0,1))=.30 }
 SubShader {
  Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="TransparentCutout" "Queue"="AlphaTest" }
  Cull Back

  HLSLINCLUDE
  #include "../../Village/Demo/Shaders/VillageLighting.hlsl"
  sampler2D _MainTex;
  CBUFFER_START(UnityPerMaterial)
  float4 _Color;float _Cutoff;
  CBUFFER_END
  struct appdata { float4 vertex:POSITION;float3 normal:NORMAL;float2 uv:TEXCOORD0;float4 color:COLOR; };
  struct v2f { float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float3 normal:TEXCOORD1;float3 world:TEXCOORD2;float4 color:COLOR; };
  float ripple(float2 p,float t) { return sin(dot(p,float2(1.7,.8))-t*1.5)*.6+sin(dot(p,float2(-.7,2.2))+t*1.1)*.4; }
  appdata deform(appdata v) {  return v; }
  v2f vert(appdata v) { v=deform(v);v2f o;o.pos=TransformObjectToHClip(v.vertex.xyz);o.world=TransformObjectToWorld(v.vertex.xyz);o.normal=TransformObjectToWorldNormal(v.normal);o.uv=v.uv;o.color=v.color;return o; }
  half4 frag(v2f i):SV_Target { half4 c=tex2D(_MainTex,i.uv)*_Color;clip(c.a-_Cutoff);Light light=VillageMainLight(i.world);
   float shade=saturate(dot(normalize(i.normal),light.direction));float3 localGlow=0;
#if defined(_ADDITIONAL_LIGHTS)
   uint count=GetAdditionalLightsCount();for(uint k=0;k<min(count,8u);k++){Light glow=GetAdditionalLight(k,i.world);localGlow+=glow.color*glow.distanceAttenuation*(.25+.75*saturate(dot(normalize(i.normal),glow.direction)));}
#endif
   c.rgb*=i.color.rgb*(.23+.08*shade*light.shadowAttenuation+min(localGlow*.45,1.2));float distanceFog=saturate((distance(i.world,_WorldSpaceCameraPos)-30)/120)*.7;c.rgb=lerp(c.rgb,float3(.045,.015,.025),distanceFog);c.a=1;return c; }
  ENDHLSL
  Pass {
   Name "PaintedForward"
   Tags { "LightMode"="UniversalForwardOnly" }
   HLSLPROGRAM
   #pragma target 3.5
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile _ _ADDITIONAL_LIGHTS
   #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
   #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
   ENDHLSL
  }
  Pass {
   Name "ShadowCaster"
   Tags { "LightMode"="ShadowCaster" }
   ZWrite On ZTest LEqual ColorMask 0
   HLSLPROGRAM
   #pragma target 3.5
   #pragma vertex vertShadow
   #pragma fragment fragShadow
   #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
   v2f vertShadow(appdata v) { v=deform(v);v2f o=(v2f)0;o.pos=VillageShadowPosition(v.vertex.xyz,v.normal);o.uv=v.uv;return o; }
   half4 fragShadow(v2f i):SV_Target { clip(tex2D(_MainTex,i.uv).a*_Color.a-_Cutoff);return 0; }
   ENDHLSL
  }
 }
 Fallback Off
}
