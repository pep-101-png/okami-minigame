Shader "Sunward/Original Heaven Cloud" {
 Properties { _MainTex("Original cloud painting",2D)="white"{} }
 SubShader { Tags { "Queue"="Transparent-10" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" }
 Cull Off ZWrite Off Blend SrcAlpha OneMinusSrcAlpha
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 float _HeavenPalace;TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 struct A {float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 struct V {float4 p:SV_POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;o.color=i.color;return o;}
 half4 frag(V i):SV_Target {half4 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv+float2(_Time.y*.001,0));clip(c.a-.2);half curl=saturate(1-dot(c.rgb,half3(.333,.333,.334)));half3 ink=lerp(half3(.96,.91,.84),half3(.59,.63,.79),curl);if(_HeavenPalace>.5)ink=lerp(half3(.995,.995,1),half3(.91,.95,1),curl*.35);return half4(ink,saturate(i.color.a*3)*.72);}
 ENDHLSL }
 } Fallback Off
}
