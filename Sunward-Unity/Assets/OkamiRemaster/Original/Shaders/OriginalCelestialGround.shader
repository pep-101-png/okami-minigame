Shader "Sunward/Original Celestial Ground" {
 Properties { _MainTex("Original paint",2D)="white"{} _WalkPaint("Original stone walk painting",2D)="white"{} _GroundPaint("Original meadow painting",2D)="white"{} _CloudPaint("Original cloud artwork",2D)="white"{} _SurfaceKind("Native, meadow or cloud sea",Float)=0 _Cull("Native face culling",Float)=2 }
 SubShader { Tags { "RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" } Cull [_Cull] ZWrite On
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 TEXTURE2D(_GroundPaint);SAMPLER(sampler_GroundPaint);
 TEXTURE2D(_WalkPaint);SAMPLER(sampler_WalkPaint);
 TEXTURE2D(_CloudPaint);SAMPLER(sampler_CloudPaint);
 CBUFFER_START(UnityPerMaterial)
 float _SurfaceKind;
 CBUFFER_END
 float4 _SunwardHeavenWalks[48],_SunwardHeavenWalkStyle[48];float _SunwardHeavenWalkCount;
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float3 world:TEXCOORD1;half4 color:COLOR;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;o.world=TransformObjectToWorld(i.p.xyz);o.color=i.color;return o;}
 half4 frag(V i):SV_Target {
 // Source stage alpha is a fade, not missing solid terrain.
 half3 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv).rgb*i.color.rgb;
 if(_SurfaceKind>.5){
 float2 p=i.world.xz-float2(230,0),turn=float2(p.x*.866-p.y*.5,p.x*.5+p.y*.866);
 half3 paint=lerp(SAMPLE_TEXTURE2D(_GroundPaint,sampler_GroundPaint,p*.065).rgb,SAMPLE_TEXTURE2D(_GroundPaint,sampler_GroundPaint,turn*.047+.31).rgb,.45);
 c=lerp(paint*half3(.98,1.12,1.05),half3(.50,.64,.58),.10);
 half3 cloud=SAMPLE_TEXTURE2D(_CloudPaint,sampler_CloudPaint,p*.014).rgb;half curl=saturate((.8-dot(cloud,half3(.333,.333,.334)))*4);
 c=lerp(c,half3(.72,.64,.87),curl*.035);
 if(_SurfaceKind>1.5)c=lerp(half3(.94,.95,1),half3(.86,.84,.95),curl*.4);
 else {
 // Original stone paint is composited into this same visible/collision mesh.
 // There are no separate walk meshes, elevation offsets or sheet edges.
 float nearest=1000;
 [loop]for(int j=0;j<48;j++){
 if(j>=(int)_SunwardHeavenWalkCount)break;
 float4 w=_SunwardHeavenWalks[j];float2 v=w.zw-w.xy,q=p-w.xy;float len=max(.001,length(v));float t=saturate(dot(q,v)/(len*len));float distance=length(q-v*t)-_SunwardHeavenWalkStyle[j].x;
 nearest=min(nearest,distance);
 }
 half path=1-smoothstep(-.12,.16,nearest);half3 stone=SAMPLE_TEXTURE2D(_WalkPaint,sampler_WalkPaint,p*float2(.18,.42)).rgb*1.16;
 c=lerp(c,stone,path);
 }
 }
 return half4(c,1);
 }
 ENDHLSL }
 } Fallback Off
}
