Shader "Sunward/Original Paper Sky" {
 Properties { _MainTex("Original illustrated paper",2D)="white"{} }
 SubShader { Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
 Cull Off ZWrite Off
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 struct A { float4 position:POSITION; };
 struct V { float4 position:SV_POSITION;float3 direction:TEXCOORD0; };
 V vert(A i) { V o;o.position=TransformObjectToHClip(i.position.xyz);o.direction=i.position.xyz;return o; }
 half4 frag(V i):SV_Target { float3 d=normalize(i.direction);float2 uv=float2(atan2(d.z,d.x)/6.28318530718+.5,asin(clamp(d.y,-1,1))/3.14159265359+.5);return SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,uv); }
 ENDHLSL }
 } Fallback Off
}