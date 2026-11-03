Shader "Sunward/Original Heaven Cloud" {
 Properties { _MainTex("Original cloud painting",2D)="white"{} }
 SubShader { Tags { "Queue"="Geometry+5" "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
 Cull Off ZWrite On
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 struct A {float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 struct V {float4 p:SV_POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;o.color=i.color;return o;}
 half4 frag(V i):SV_Target {half4 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv);clip(c.a-.2);return half4(lerp(half3(.93,.93,1),c.rgb, .55)*half3(1,.98,1),1);}
 ENDHLSL }
 } Fallback Off
}
