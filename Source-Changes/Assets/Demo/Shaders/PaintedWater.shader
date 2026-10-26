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
  Tags { "RenderType"="Opaque" "Queue"="Geometry+10" }
  Cull Off ZWrite On
  Pass {
   Tags { "LightMode"="ForwardBase" }
   CGPROGRAM
   #pragma target 3.0
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_fwdbase
   #include "UnityCG.cginc"
   #include "Lighting.cginc"
   #include "AutoLight.cginc"
   sampler2D _MainTex; float4 _Color, _FlowSpeed; float _FlowTime,_WaveStrength,_WorldScale;
   struct appdata { float4 vertex:POSITION; float3 normal:NORMAL; float4 color:COLOR; float2 texcoord1:TEXCOORD1; };
   struct v2f { float4 pos:SV_POSITION; float3 world:TEXCOORD0; float weight:TEXCOORD1; SHADOW_COORDS(2) };
   float ripple(float2 p,float t) { return sin(dot(p,float2(1.7,.8))-t*1.5)*.6+sin(dot(p,float2(-.7,2.2))+t*1.1)*.4; }
   v2f vert(appdata v) {
    v2f o; float3 world=mul(unity_ObjectToWorld,v.vertex).xyz;
    world.y+=ripple(world.xz,_FlowTime)*_WaveStrength*v.color.a;
    v.vertex=mul(unity_WorldToObject,float4(world,1));o.pos=UnityObjectToClipPos(v.vertex);
    o.world=world;o.weight=v.color.a;TRANSFER_SHADOW(o);return o;
   }
   fixed4 frag(v2f i):SV_Target {
    float2 uv=i.world.xz*_WorldScale;
    // Two advection phases cross-fade to zero at their own reset. UVs remain
    // continuous in world space: never frac a cropped atlas or move a mesh tile.
    float p=frac(_FlowTime/9),q=frac(_FlowTime/9+.5);
    float w=sin(UNITY_PI*p);w*=w;
    float current=.83+.17*sin(i.world.z*.61+i.world.x*1.7);
    float2 flow=_FlowSpeed.xy*.43*current;
    fixed3 a=tex2D(_MainTex,uv-flow*p).rgb;
    fixed3 b=tex2D(_MainTex,uv-flow*q+float2(.29,.17)).rgb;
    fixed3 still=tex2D(_MainTex,uv*.37+float2(.11,.43)).rgb;
    fixed3 paint=lerp(still,lerp(b,a,w),.66)*_Color.rgb;
    float2 p0=i.world.xz;float h=ripple(p0,_FlowTime);
    float dx=(ripple(p0+float2(.03,0),_FlowTime)-h)/.03;
    float dz=(ripple(p0+float2(0,.03),_FlowTime)-h)/.03;
    float3 n=normalize(float3(-dx*.09*i.weight,1,-dz*.09*i.weight));
    float3 view=normalize(_WorldSpaceCameraPos-i.world);
    float sheen=pow(saturate(dot(reflect(-normalize(_WorldSpaceLightPos0.xyz),n),view)),24);
    float fresnel=pow(1-saturate(dot(n,view)),3);
    float shadow=SHADOW_ATTENUATION(i);
    paint*=.86+.14*shadow;
    paint=lerp(paint,float3(.33,.61,.57),fresnel*.22);
    paint+=float3(.60,.70,.57)*sheen*.11;
    return fixed4(paint,1);
   }
   ENDCG
  }
 }
 Fallback Off
}
