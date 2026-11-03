Shader "Sunward/Original Celestial Ground" {
 Properties { _MainTex("Original stone paint",2D)="white"{} _GroundPaint("Original meadow painting",2D)="white"{} _CloudPaint("Original celestial cloud artwork",2D)="white"{} _SurfaceKind("Stone, garden or cloud sea",Float)=0 _Cull("Native face culling",Float)=2 }
 SubShader { Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" } Cull [_Cull] ZWrite On
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 TEXTURE2D(_GroundPaint);SAMPLER(sampler_GroundPaint);
 TEXTURE2D(_CloudPaint);SAMPLER(sampler_CloudPaint);
 CBUFFER_START(UnityPerMaterial)
 float _SurfaceKind;
 CBUFFER_END
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float3 world:TEXCOORD1;half4 color:COLOR;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;o.world=TransformObjectToWorld(i.p.xyz);o.color=i.color;return o;}
 half4 frag(V i):SV_Target {
 // These are solid supporting surfaces. Source vertex alpha is a stage fade,
 // not a hole mask; multiplying it into clip() removed real ground triangles.
 half3 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv).rgb*i.color.rgb;
 if(_SurfaceKind>.5){
 float2 p=i.world.xz-float2(230,0);float2 turn=float2(p.x*.866-p.y*.5,p.x*.5+p.y*.866);
 half3 paint=lerp(SAMPLE_TEXTURE2D(_GroundPaint,sampler_GroundPaint,p*.065).rgb,SAMPLE_TEXTURE2D(_GroundPaint,sampler_GroundPaint,turn*.047+.31).rgb,.45);
 half shade=dot(paint,half3(.3,.5,.2));c=lerp(half3(.60,.78,.75),half3(.97,.91,.79),saturate(shade*.8+.18));
 half3 cloud=SAMPLE_TEXTURE2D(_CloudPaint,sampler_CloudPaint,p*.014).rgb;half curl=saturate((.8-dot(cloud,half3(.333,.333,.334)))*4);
 c=lerp(c,half3(.72,.64,.87),curl*.24);
 if(_SurfaceKind>1.5)c=lerp(half3(.94,.95,1),half3(.86,.84,.95),curl*.4);
 }
 return half4(c,1);
 }
 ENDHLSL }
 } Fallback Off
}
