Shader "VillageDemo/Continuous Painted Water" {
 Properties {
  _MainTex ("Seamless ST2 water paint", 2D) = "white" {}
  _Color ("Water pigment", Color) = (1,1,1,1)
  _WaterMode ("Water animation", Float) = 1
  _FlowTime ("Controlled time", Float) = 0
  _FlowSpeed ("World flow direction and strength", Vector) = (0,-1,0,0)
  _WaveStrength ("Ripple height", Float) = .012
  _WorldScale ("Brush scale", Float) = .31
 }
 SubShader {
  Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry+10" }
  Cull Off

  HLSLINCLUDE
  #include "VillageLighting.hlsl"
  sampler2D _MainTex;
  CBUFFER_START(UnityPerMaterial)
  float4 _Color, _FlowSpeed;float _FlowTime,_WaveStrength,_WorldScale;
  CBUFFER_END
  struct appdata { float4 vertex:POSITION;float3 normal:NORMAL;float2 uv:TEXCOORD0;float4 color:COLOR; };
  struct v2f { float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float3 normal:TEXCOORD1;float3 world:TEXCOORD2;float4 color:COLOR; };
  float ripple(float2 p,float t) { return sin(dot(p,float2(1.7,.8))-t*1.5)*.6+sin(dot(p,float2(-.7,2.2))+t*1.1)*.4; }
  appdata deform(appdata v) { float3 world = TransformObjectToWorld(v.vertex.xyz);
   world.y+=ripple(world.xz,_FlowTime)*_WaveStrength*v.color.a;
   v.vertex.xyz=TransformWorldToObject(world); return v; }
  v2f vert(appdata v) { v=deform(v);v2f o;o.pos=TransformObjectToHClip(v.vertex.xyz);o.world=TransformObjectToWorld(v.vertex.xyz);o.normal=TransformObjectToWorldNormal(v.normal);o.uv=v.uv;o.color=v.color;return o; }
  half4 frag(v2f i):SV_Target {     float2 uv=i.world.xz*_WorldScale;
    // Two advection phases cross-fade to zero at their own reset. UVs remain
    // continuous in world space: never frac a cropped atlas or move a mesh tile.
    float p=frac(_FlowTime/9),q=frac(_FlowTime/9+.5);
    float w=sin(PI*p);w*=w;
    float current=.83+.17*sin(i.world.z*.61+i.world.x*1.7);
    float2 flow=_FlowSpeed.xy*.43*current;
    half3 a=tex2D(_MainTex,uv-flow*p).rgb;
    half3 b=tex2D(_MainTex,uv-flow*q+float2(.29,.17)).rgb;
    half3 still=tex2D(_MainTex,uv*.37+float2(.11,.43)).rgb;
    half3 paint=lerp(still,lerp(b,a,w),.66)*_Color.rgb;
    float2 p0=i.world.xz;float h=ripple(p0,_FlowTime);
    float dx=(ripple(p0+float2(.03,0),_FlowTime)-h)/.03;
    float dz=(ripple(p0+float2(0,.03),_FlowTime)-h)/.03;
    float3 n=normalize(float3(-dx*.09*i.color.a,1,-dz*.09*i.color.a));
    float3 view=normalize(_WorldSpaceCameraPos-i.world);
    float sheen=pow(saturate(dot(reflect(-VillageMainLight(i.world).direction,n),view)),24);
    float fresnel=pow(1-saturate(dot(n,view)),3);
    float shadow=VillageMainLight(i.world).shadowAttenuation;
    paint*=.86+.14*shadow;
    paint=lerp(paint,float3(.33,.61,.57),fresnel*.22);
    paint+=float3(.60,.70,.57)*sheen*.11;
    return half4(paint,1); }
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
 }
 Fallback Off
}
