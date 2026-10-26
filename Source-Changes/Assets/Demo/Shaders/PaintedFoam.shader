Shader "VillageDemo/Drifting Painted Foam" {
 Properties {
  _MainTex ("Original ST2 wave artwork", 2D) = "white" {}
  _Color ("Paint", Color) = (1,1,1,1)
  _UVMatrix ("Original atlas mapping", Vector) = (1,0,0,1)
  _UVOffset ("Original atlas offset", Vector) = (0,0,0,0)
  _WaterMode ("Water animation", Float) = 1
  _FoamMode ("Travelling foam", Float) = 1
  _FlowTime ("Controlled time", Float) = 0
  _FoamPhaseOffset ("Paired phase", Float) = 0
  _FlowSpeed ("World drift metres per cycle", Vector) = (0,-.9,0,0)
  _WaveStrength ("Ripple height", Float) = .012
 }
 SubShader {
  Tags { "RenderType"="Transparent" "Queue"="Transparent" "IgnoreProjector"="True" }
  Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Off
  Pass {
   CGPROGRAM
   #pragma target 3.0
   #pragma vertex vert
   #pragma fragment frag
   #include "UnityCG.cginc"
   sampler2D _MainTex;float4 _Color,_UVMatrix,_UVOffset,_FlowSpeed;
   float _FlowTime,_FoamPhaseOffset,_FoamMode,_WaveStrength;
   struct appdata { float4 vertex:POSITION;float2 uv:TEXCOORD0;float4 color:COLOR; };
   struct v2f { float4 pos:SV_POSITION;float2 uv:TEXCOORD0;float alpha:TEXCOORD1;float2 localUV:TEXCOORD2; };
   v2f vert(appdata v) {
    v2f o;float3 world=mul(unity_ObjectToWorld,v.vertex).xyz;
    float phase=frac(_FlowTime/5.5+_FoamPhaseOffset+world.z*.037+world.x*.11);
    float fade=sin(UNITY_PI*phase);fade*=fade;
    // Atlas UVs stay attached to the original painted mesh. Move and fade
    // the wave itself, not a rectangular image under a stationary wave.
    world.xz+=(_FlowSpeed.xy+float2(sin(world.z*.8)*.10,0))*(phase-.5)*v.color.a;
    world.y+=sin(world.x*1.7+world.z*.8-_FlowTime*1.5)*_WaveStrength*v.color.a;
    o.pos=mul(UNITY_MATRIX_VP,float4(world,1));o.uv=float2(dot(_UVMatrix.xy,v.uv),dot(_UVMatrix.zw,v.uv))+_UVOffset.xy;
    o.alpha=lerp(.78,fade*.75,saturate(_FoamMode));o.localUV=v.uv;return o;
   }
   fixed4 frag(v2f i):SV_Target {
    fixed4 paint=tex2D(_MainTex,i.uv)*_Color;
    // The source alpha carries the brush edge; avoid square hard clipping.
    float edge=smoothstep(0,.08,i.localUV.x)*smoothstep(0,.08,1-i.localUV.x);
    paint.a*=i.alpha*lerp(1,edge,saturate(_FoamMode));
    return paint;
   }
   ENDCG
  }
 }
 Fallback Off
}
