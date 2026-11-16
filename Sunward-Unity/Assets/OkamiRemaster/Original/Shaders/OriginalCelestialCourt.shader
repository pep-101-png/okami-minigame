Shader "Sunward/Original Celestial Court"{
 Properties{_StonePaint("Original stone paint",2D)="white"{} _GrassPaint("Original meadow paint",2D)="white"{} _CloudPaint("Original cloud painting",2D)="white"{} _CourtCentre("Court centre",Vector)=(380,70,0,0) _Eclipse("Eclipse courtyard",Float)=0 _Moonlit("Moonlit forest path",Float)=0}
 SubShader{Tags{"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"} Cull Off
 Pass{HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_StonePaint);SAMPLER(sampler_StonePaint);TEXTURE2D(_GrassPaint);SAMPLER(sampler_GrassPaint);TEXTURE2D(_CloudPaint);SAMPLER(sampler_CloudPaint);
 float4 _CourtCentre;float _Eclipse,_Moonlit;
 struct A{float4 p:POSITION;};struct V{float4 p:SV_POSITION;float3 w:TEXCOORD0;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.w=TransformObjectToWorld(i.p.xyz);return o;}
 float segmentDistance(float2 p,float2 a,float2 b){float2 d=b-a;return length(p-a-d*saturate(dot(p-a,d)/dot(d,d)));}
 half4 frag(V i):SV_Target{
 float2 p=i.w.xz-_CourtCentre.xz;float r=length(p);half3 cloud=SAMPLE_TEXTURE2D(_CloudPaint,sampler_CloudPaint,p*.032+_Time.y*.001).rgb;
 float curl=dot(cloud,half3(.333,.333,.334));half3 stone=SAMPLE_TEXTURE2D(_StonePaint,sampler_StonePaint,p*.11).rgb;
 half3 meadow=SAMPLE_TEXTURE2D(_GrassPaint,sampler_GrassPaint,p*.16).rgb*half3(.8,.93,.84);
 float border=smoothstep(16+curl,22+curl,r);half3 ground=lerp(stone*.92,meadow,border);
 if(_Moonlit>.5){
 float path=min(min(segmentDistance(p,float2(0,-22),float2(-12,-10)),segmentDistance(p,float2(-12,-10),float2(8,2))),min(segmentDistance(p,float2(8,2),float2(-4,14)),segmentDistance(p,float2(-4,14),float2(0,20))));
 float edge=smoothstep(1.1,2.2,path+sin(p.x*1.7+p.y)*.16);
 half3 paving=SAMPLE_TEXTURE2D(_StonePaint,sampler_StonePaint,p*.5).rgb;
 ground=lerp(paving*.75,meadow,edge);
 }
 ground=lerp(ground,ground*half3(.63,.67,.87),_Eclipse*.55);
 half3 mist=lerp(half3(.98,.98,1),half3(.81,.85,.96),saturate((.85-curl)*2));
 float rim=smoothstep(24,29+curl,r);ground=lerp(ground,mist,rim);
 float ring=(1-smoothstep(.04,.12,abs(r-13.5)))*.35*(1-_Moonlit);ground=lerp(ground,half3(.9,.76,.47),ring);
 return half4(ground,1);}
 ENDHLSL}
 }Fallback Off
}
