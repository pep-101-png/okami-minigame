Shader "VillageDemo/Painted Surface" {
 Properties {
  _MainTex ("Painted artwork", 2D) = "white" {}
  _Color ("Paint tint", Color) = (1,1,1,1)
  _UVMatrix ("UV matrix", Vector) = (1,0,0,1)
  _UVOffset ("UV offset", Vector) = (0,0,0,0)
  _RepeatUV ("Repeat inside atlas panel", Float) = 0
  _Cutoff ("Cutout threshold", Range(0,1)) = 0
  _WindStrength ("Soft foliage breeze", Float) = 0
  _WaterMode ("Water animation", Float) = 0
  _FlowTime ("Flow time", Float) = 0
  _FlowSpeed ("Flow speed", Vector) = (0.07,0,0,0)
  _WaveStrength ("Surface ripple", Float) = 0.018
 }
 SubShader {
  Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry" }
  Cull Off

  HLSLINCLUDE
  #include "VillageLighting.hlsl"
  sampler2D _MainTex;
  CBUFFER_START(UnityPerMaterial)
  float4 _Color, _UVMatrix, _UVOffset, _FlowSpeed; float _RepeatUV, _Cutoff, _WindStrength, _WaterMode, _FlowTime, _WaveStrength;
  CBUFFER_END
  struct appdata { float4 vertex:POSITION;float3 normal:NORMAL;float2 uv:TEXCOORD0;float4 color:COLOR; };
  struct v2f { float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float3 normal:TEXCOORD1;float3 world:TEXCOORD2;float4 color:COLOR; };
  float ripple(float2 p,float t) { return sin(dot(p,float2(1.7,.8))-t*1.5)*.6+sin(dot(p,float2(-.7,2.2))+t*1.1)*.4; }
  appdata deform(appdata v) { float3 world = TransformObjectToWorld(v.vertex.xyz);
   float sway = sin(_Time.y*1.15+world.x*.8+world.z*.47)*_WindStrength*v.color.a;
   v.vertex.x += sway; v.vertex.z += sway*.38;
   v.vertex.y += _WaterMode*_WaveStrength*sin(world.x*2.1+world.z*1.6+_FlowTime*1.7)*v.color.a; return v; }
  v2f vert(appdata v) { v=deform(v);v2f o;o.pos=TransformObjectToHClip(v.vertex.xyz);o.world=TransformObjectToWorld(v.vertex.xyz);o.normal=TransformObjectToWorldNormal(v.normal);o.uv=v.uv;o.color=v.color;return o; }
  half4 frag(v2f i):SV_Target { float2 uv=i.uv+_WaterMode*_FlowTime*_FlowSpeed.xy;
   if (_RepeatUV>.5 || _WaterMode>.5) uv=frac(uv);
   uv=float2(dot(_UVMatrix.xy,uv),dot(_UVMatrix.zw,uv))+_UVOffset.xy;
   half4 c=tex2D(_MainTex,uv)*_Color;clip(c.a-_Cutoff);
   c.rgb*=1+.025*_WaterMode*sin(i.uv.x*24+i.uv.y*17-_FlowTime*1.4);
   Light light=VillageMainLight(i.world); float shade=saturate(dot(normalize(i.normal),light.direction));
   c.rgb*=.73+.27*shade*light.shadowAttenuation;c.a=1;return c; }
  ENDHLSL
  Pass {
   Name "PaintedForward"
   Tags { "LightMode"="UniversalForwardOnly" }
   HLSLPROGRAM
   #pragma target 3.5
   #pragma vertex vert
   #pragma fragment frag
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
   half4 fragShadow(v2f i):SV_Target { float2 uv=i.uv+_WaterMode*_FlowTime*_FlowSpeed.xy;
   if (_RepeatUV>.5 || _WaterMode>.5) uv=frac(uv);
   uv=float2(dot(_UVMatrix.xy,uv),dot(_UVMatrix.zw,uv))+_UVOffset.xy;
   clip(tex2D(_MainTex,uv).a*_Color.a-_Cutoff);return 0; }
   ENDHLSL
  }
 }
 Fallback Off
}
