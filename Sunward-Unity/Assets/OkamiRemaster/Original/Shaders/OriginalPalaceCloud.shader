Shader "Sunward/Original Palace Cloud"{
 Properties{_MainTex("Original cloud artwork",2D)="white"{}}
 SubShader{Tags{"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"}Cull Off
 Pass{HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 struct A{float4 p:POSITION;};struct V{float4 p:SV_POSITION;float3 w:TEXCOORD0;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.w=TransformObjectToWorld(i.p.xyz);return o;}
 half4 frag(V i):SV_Target{half3 cloud=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.w.xz*.035+_Time.y*.001).rgb;half curl=saturate((.85-dot(cloud,half3(.333,.333,.334)))*2);return half4(lerp(half3(.995,.995,1),half3(.90,.94,.99),curl*.45),1);}
 ENDHLSL}
 }Fallback Off
}
