Shader "VillageDemo/Grass Dirt Transition" {
 Properties { _MainTex("Original grass painting",2D)="white"{} _DirtTex("Earth brushwork",2D)="white"{} _DirtTint("Earth tint",Color)=(.85,.77,.59,1) }
 SubShader {
  Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" }
  Cull Off

  HLSLINCLUDE
  #include "VillageLighting.hlsl"
  sampler2D _MainTex,_DirtTex;
  CBUFFER_START(UnityPerMaterial)
  float4 _DirtTint;
  CBUFFER_END
  struct appdata { float4 vertex:POSITION;float3 normal:NORMAL;float2 uv:TEXCOORD0;float4 color:COLOR; };
  struct v2f { float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float3 normal:TEXCOORD1;float3 world:TEXCOORD2;float4 color:COLOR; };
  float ripple(float2 p,float t) { return sin(dot(p,float2(1.7,.8))-t*1.5)*.6+sin(dot(p,float2(-.7,2.2))+t*1.1)*.4; }
  appdata deform(appdata v) {  return v; }
  v2f vert(appdata v) { v=deform(v);v2f o;o.pos=TransformObjectToHClip(v.vertex.xyz);o.world=TransformObjectToWorld(v.vertex.xyz);o.normal=TransformObjectToWorldNormal(v.normal);o.uv=v.uv;o.color=v.color;return o; }
  half4 frag(v2f i):SV_Target { half3 grass=tex2D(_MainTex,i.uv*float2(4,3)).rgb;
   half3 dirt=tex2D(_DirtTex,frac(i.uv*8)*float2(.30,.45)+float2(.015,.015)).rgb*_DirtTint.rgb;
   float boundary=saturate(i.color.r+(dot(grass,float3(.3,.5,.2))-.3)*.16*sin(saturate(i.color.r)*PI));
   half3 c=lerp(grass,dirt,boundary);Light light=VillageMainLight(i.world);
   float shade=saturate(dot(normalize(i.normal),light.direction));c*=.73+.27*shade*light.shadowAttenuation;return half4(c,1); }
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
   half4 fragShadow(v2f i):SV_Target { return 0; }
   ENDHLSL
  }
 }
 Fallback Off
}
