Shader "Sunward/Original Falling Water"{
Properties{_MainTex("Original waterfall painting",2D)="white"{} _Color("Colour",Color)=(1,1,1,1) _FlowDirection("Native layer flow",Float)=-1}
SubShader{Tags{"RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent"} Cull Off ZWrite Off Blend SrcAlpha OneMinusSrcAlpha
Pass{Tags{"LightMode"="UniversalForwardOnly"}
HLSLPROGRAM
#pragma vertex vert
#pragma fragment frag
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
sampler2D _MainTex;float4 _Color;float _SunwardRiverClock,_FlowDirection;
struct A{float4 vertex:POSITION;float2 uv:TEXCOORD0;};struct V{float4 pos:SV_POSITION;float2 uv:TEXCOORD0;};
V vert(A i){V o;o.pos=TransformObjectToHClip(i.vertex.xyz);o.uv=i.uv;return o;}
half4 frag(V i):SV_Target{half4 c=tex2D(_MainTex,i.uv+float2(0,_SunwardRiverClock*.17*_FlowDirection))*_Color;c.a*=.88;return c;}
ENDHLSL
}}}
