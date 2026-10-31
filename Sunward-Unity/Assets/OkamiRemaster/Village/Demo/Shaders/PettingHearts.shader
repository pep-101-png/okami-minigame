Shader "VillageDemo/Petting Ink Hearts" {
 Properties { _MainTex("Painted heart",2D)="white"{} _Opacity("Fade",Range(0,1))=1 }
 SubShader {
  Tags { "RenderPipeline"="UniversalPipeline" "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True"} Cull Off ZWrite Off Blend SrcAlpha OneMinusSrcAlpha
 Pass { Tags { "LightMode"="UniversalForwardOnly" } HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 sampler2D _MainTex;
 CBUFFER_START(UnityPerMaterial)
 float _Opacity;
 CBUFFER_END
 struct input {float4 vertex:POSITION;float2 uv:TEXCOORD0;};struct output {float4 pos:SV_POSITION;float2 uv:TEXCOORD0;};
 output vert(input v){output o;o.pos=TransformObjectToHClip(v.vertex.xyz);o.uv=v.uv;return o;}
 half4 frag(output i):SV_Target{half4 c=tex2D(_MainTex,i.uv);c.a*=_Opacity;return c;}
 ENDHLSL }
 } Fallback Off
}
