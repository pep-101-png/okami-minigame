Shader "Sunward/Original Paper Sky" {
 Properties { _MainTex("Original illustrated paper",2D)="white"{} }
 SubShader { Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
 Cull Off ZWrite Off
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 float _SunwardNight,_SunwardHeaven,_HeavenPalace;
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 TEXTURE2D(_SunwardSunArt);SAMPLER(sampler_SunwardSunArt);TEXTURE2D(_SunwardMoonArt);SAMPLER(sampler_SunwardMoonArt);
 TEXTURE2D(_SunwardHeavenClouds);SAMPLER(sampler_SunwardHeavenClouds);
 struct A { float4 position:POSITION; };
 struct V { float4 position:SV_POSITION;float3 direction:TEXCOORD0; };
 V vert(A i) { V o;o.position=TransformObjectToHClip(i.position.xyz);o.direction=i.position.xyz;return o; }
 half4 frag(V i):SV_Target {
 float3 d=normalize(i.direction);float2 uv=float2(atan2(d.z,d.x)/6.28318530718+.5,asin(clamp(d.y,-1,1))/3.14159265359+.5);
 half4 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,uv);
 half3 horizon=lerp(half3(.98,.92,.86),half3(.64,.79,.95),saturate(d.y*.8+.2));
 half3 cloud=SAMPLE_TEXTURE2D(_SunwardHeavenClouds,sampler_SunwardHeavenClouds,float2(uv.x*3+_Time.y*.0015,uv.y*2)).rgb;
 half curl=saturate((.83-dot(cloud,half3(.333,.333,.334)))*3);
 half3 heaven=lerp(horizon,half3(.85,.77,.91),curl*.45);
 c.rgb=lerp(c.rgb,heaven,_SunwardHeaven);c.rgb*=lerp(float3(1,1,1),float3(.055,.085,.18),_SunwardNight);if(_SunwardHeaven<.5){float3 orb=normalize(float3(-.45,.5,.72));float3 right=normalize(cross(float3(0,1,0),orb));float3 up=cross(orb,right);float2 p=float2(dot(d,right),dot(d,up))/.22+.5;half4 sun=SAMPLE_TEXTURE2D(_SunwardSunArt,sampler_SunwardSunArt,p);half4 moon=SAMPLE_TEXTURE2D(_SunwardMoonArt,sampler_SunwardMoonArt,p);half4 art=lerp(sun,moon,_SunwardNight);float inside=step(0,p.x)*step(p.x,1)*step(0,p.y)*step(p.y,1)*step(.5,dot(d,orb));c.rgb=lerp(c.rgb,art.rgb,art.a*inside);}

 if(_HeavenPalace>.5)c.rgb=lerp(half3(.995,.995,1),half3(.92,.95,1),curl*.4);return c;
 }
 ENDHLSL }
 } Fallback Off
}