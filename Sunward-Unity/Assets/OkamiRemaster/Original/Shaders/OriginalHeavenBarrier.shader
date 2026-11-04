Shader "Sunward/Original Heaven Barrier" {
 Properties { _MainTex("Original spirit glow artwork",2D)="white"{} }
 SubShader { Tags { "Queue"="Transparent+5" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" } Cull Off ZWrite Off Blend SrcAlpha One
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;return o;}
 half4 frag(V i):SV_Target {half glow=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,float2(i.uv.x,frac(i.uv.y-_Time.y*.18))).r;half edge=smoothstep(0,.15,i.uv.y)*smoothstep(0,.15,1-i.uv.y);return half4(.25,.75,1,glow*edge*.12);}
 ENDHLSL }
 }Fallback Off
}
