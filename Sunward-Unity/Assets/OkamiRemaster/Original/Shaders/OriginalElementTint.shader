Shader "Sunward/Original Element Tint" {
 Properties{_MainTex("Original painting",2D)="white"{} _Tint("Element colour",Color)=(1,.8,.1,1) _Color("Lifetime fade",Color)=(1,1,1,1)}
 SubShader{Tags{"Queue"="Transparent+3" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline"}Blend SrcAlpha One Cull Off ZWrite Off
 Pass{HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);half4 _Tint,_Color;
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;o.color=i.color;return o;}
 half4 frag(V i):SV_Target{half4 p=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv);half glow=max(p.r,max(p.g,p.b));return half4(_Tint.rgb*glow*1.35,p.a*i.color.a*_Tint.a*_Color.a);}
 ENDHLSL}
 }Fallback Off
}
