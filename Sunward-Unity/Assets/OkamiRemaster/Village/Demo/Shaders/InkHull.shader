Shader "VillageDemo/Physical Ink Hull" {
 Properties { _Color ("Ink",Color)=(.009,.008,.004,1) _WindStrength ("Breeze",Float)=0 }
 SubShader {
  Tags { "RenderPipeline"="UniversalPipeline"  "Queue"="Geometry-1" "RenderType"="Opaque" }
  Cull Off ZWrite On
  Pass { Tags { "LightMode"="UniversalForwardOnly" }
   HLSLPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   CBUFFER_START(UnityPerMaterial)
   float4 _Color; float _WindStrength;
   CBUFFER_END
   struct appdata { float4 vertex:POSITION; float3 normal:NORMAL; float4 color:COLOR; };
   struct v2f { float4 pos:SV_POSITION; float3 normal:TEXCOORD0; float3 world:TEXCOORD1; };
   v2f vert(appdata v) {
    v2f o;float3 p=TransformObjectToWorld(v.vertex.xyz);float sway=sin(_Time.y*1.15+p.x*.8+p.z*.47)*_WindStrength*v.color.a;
    v.vertex.x+=sway;v.vertex.z+=sway*.38;o.pos=TransformObjectToHClip(v.vertex.xyz);o.world=TransformObjectToWorld(v.vertex.xyz);o.normal=TransformObjectToWorldNormal(v.normal);return o;
   }
   half4 frag(v2f i):SV_Target {
    // Explicit normal/view clipping avoids winding-dependent solid-black shells after the coordinate conversion.
    clip(-dot(normalize(i.normal),normalize(GetWorldSpaceViewDir(i.world))));return _Color;
   }
   ENDHLSL
  }
 }
}
