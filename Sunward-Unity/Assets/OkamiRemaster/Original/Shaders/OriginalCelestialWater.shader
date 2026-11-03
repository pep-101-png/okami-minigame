Shader "Sunward/Original Celestial Water" {
 Properties { _MainTex("Original water painting",2D)="white"{} _CentreX("Pond X",Float)=0 _CentreZ("Pond Z",Float)=0 _RadiusX("Water radius X",Float)=4 _RadiusZ("Water radius Z",Float)=4 }
 SubShader { Tags { "Queue"="Geometry+10" "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" } Cull Off
 Pass { HLSLPROGRAM
 #pragma target 3.5
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);
 CBUFFER_START(UnityPerMaterial)
 float _CentreX,_CentreZ,_RadiusX,_RadiusZ;
 CBUFFER_END
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
 struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float3 world:TEXCOORD1;half4 color:COLOR;};
 V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.world=TransformObjectToWorld(i.p.xyz);o.uv=i.uv;o.color=i.color;return o;}
 half4 frag(V i):SV_Target {float2 d=(i.world.xz-float2(_CentreX,_CentreZ))/float2(_RadiusX,_RadiusZ);clip(1-dot(d,d));float2 uv=i.uv+float2(sin(_Time.y*.12)*.008,_Time.y*.008);half4 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,uv)*i.color;return half4(c.rgb*1.15,1);}
 ENDHLSL }
 } Fallback Off
}
