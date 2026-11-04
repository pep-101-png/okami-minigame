Shader "Sunward/Original Celestial Water" {
 Properties { _MainTex("Original water painting",2D)="white"{} _RipplePaint("Original wave artwork",2D)="black"{} _CentreX("Pond X",Float)=0 _CentreZ("Pond Z",Float)=0 _RadiusX("Water radius X",Float)=4 _RadiusZ("Water radius Z",Float)=4 _WaterLevel("Actual water level",Float)=70 }
 SubShader { Tags { "Queue"="Transparent" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" } Cull Off ZWrite Off Blend SrcAlpha OneMinusSrcAlpha
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);TEXTURE2D(_RipplePaint);SAMPLER(sampler_RipplePaint);
 CBUFFER_START(UnityPerMaterial)
 float _CentreX,_CentreZ,_RadiusX,_RadiusZ,_WaterLevel;
 CBUFFER_END
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float3 world:TEXCOORD1;half4 color:COLOR;};
 V vert(A i){V o;o.world=TransformObjectToWorld(i.p.xyz);o.world.y=_WaterLevel;o.p=TransformWorldToHClip(o.world);o.uv=i.uv;o.color=i.color;return o;}
 half4 frag(V i):SV_Target {
 float2 d=(i.world.xz-float2(_CentreX,_CentreZ))/float2(_RadiusX,_RadiusZ);float radius=length(d);float edge=.97+.015*sin(atan2(d.y,d.x)*7);clip(edge-radius);
 float2 uv=i.uv+float2(sin(_Time.y*.3+i.world.z*.7)*.006,_Time.y*.007);
 half3 waterPaint=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,uv).rgb*i.color.rgb;
 half fresnel=pow(1-saturate(dot(normalize(GetWorldSpaceViewDir(i.world)),float3(0,1,0))),3);
 half3 c=lerp(waterPaint*.95,half3(.54,.75,.82),fresnel*.35);
 half4 wave=SAMPLE_TEXTURE2D(_RipplePaint,sampler_RipplePaint,i.world.xz*.15+float2(_Time.y*.008,-_Time.y*.006));
 half glint=wave.a*smoothstep(.7,1,dot(wave.rgb,half3(.333,.333,.334)))*.10;
 c=lerp(c,half3(.85,.98,1),glint);
 half alpha=(.48+.16*(1-radius)+fresnel*.18)*smoothstep(0,.10,edge-radius);
 return half4(c,alpha);
 }
 ENDHLSL }
 } Fallback Off
}
