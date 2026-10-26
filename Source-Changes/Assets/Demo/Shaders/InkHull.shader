Shader "VillageDemo/Physical Ink Hull" {
 Properties { _Color ("Ink",Color)=(.009,.008,.004,1) _WindStrength ("Breeze",Float)=0 }
 SubShader {
  Tags { "Queue"="Geometry-1" "RenderType"="Opaque" }
  Cull Off ZWrite On
  Pass {
   CGPROGRAM
   #pragma vertex vert
   #pragma fragment frag
   #include "UnityCG.cginc"
   float4 _Color; float _WindStrength;
   struct appdata { float4 vertex:POSITION; float3 normal:NORMAL; float4 color:COLOR; };
   struct v2f { float4 pos:SV_POSITION; float3 normal:TEXCOORD0; float3 world:TEXCOORD1; };
   v2f vert(appdata v) {
    v2f o;float3 p=mul(unity_ObjectToWorld,v.vertex).xyz;float sway=sin(_Time.y*1.15+p.x*.8+p.z*.47)*_WindStrength*v.color.a;
    v.vertex.x+=sway;v.vertex.z+=sway*.38;o.pos=UnityObjectToClipPos(v.vertex);o.world=mul(unity_ObjectToWorld,v.vertex).xyz;o.normal=UnityObjectToWorldNormal(v.normal);return o;
   }
   fixed4 frag(v2f i):SV_Target {
    // Explicit normal/view clipping avoids winding-dependent solid-black shells after the coordinate conversion.
    clip(-dot(normalize(i.normal),normalize(UnityWorldSpaceViewDir(i.world))));return _Color;
   }
   ENDCG
  }
 }
}
