Shader "Sunward/Calligraphic Energy" {
 Properties {_BaseColor("Ink and light",Color)=(.55,.65,.53,.65) _Barrier("Calligraphic wall",Float)=0}
 SubShader{Tags{"RenderPipeline"="UniversalPipeline" "Queue"="Transparent"}Blend SrcAlpha OneMinusSrcAlpha ZWrite Off Cull Off
 Pass{Tags{"LightMode"="UniversalForward"}
 HLSLPROGRAM
 #pragma vertex Vert
 #pragma fragment Frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 CBUFFER_START(UnityPerMaterial)
 float4 _BaseColor;float _Barrier;
 CBUFFER_END
 struct A{float4 p:POSITION;float2 uv:TEXCOORD0;float4 color:COLOR;};struct V{float4 p:SV_POSITION;float2 uv:TEXCOORD0;float4 color:COLOR;};
 V Vert(A i){V o;float3 p=i.p.xyz;p.y+=sin(_Time.y*2+p.x*.6+p.z*.4)*.06*_Barrier;o.p=TransformObjectToHClip(p);o.uv=i.uv;o.color=i.color;return o;}
 half4 Frag(V i):SV_Target{float fiber=sin(i.uv.x*83+sin(i.uv.y*11)*2)*.08;float stroke=pow(max(0,sin(i.uv.x*3+sin(i.uv.y*6-_Time.y*1.2))),7);float fade=pow(saturate(1-i.uv.y),.65);float alpha=lerp(1,(.07+stroke*.60)*fade,_Barrier)*(.90+fiber);float4 c=_BaseColor*i.color;return half4(c.rgb,c.a*alpha);}
 ENDHLSL
 }}
}
