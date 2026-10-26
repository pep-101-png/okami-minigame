Shader "VillageDemo/Grass Dirt Transition" {
 Properties { _MainTex("Original grass painting",2D)="white"{} _DirtTex("Earth brushwork",2D)="white"{} _DirtTint("Earth tint",Color)=(.85,.77,.59,1) }
 SubShader {
  Tags { "RenderType"="Opaque" }
  Cull Off
  Pass {
   Tags { "LightMode"="ForwardBase" }
   CGPROGRAM
   #pragma target 3.0
   #pragma vertex vert
   #pragma fragment frag
   #pragma multi_compile_fwdbase
   #include "UnityCG.cginc"
   #include "Lighting.cginc"
   #include "AutoLight.cginc"
   sampler2D _MainTex,_DirtTex; float4 _DirtTint;
   struct appdata { float4 vertex:POSITION; float3 normal:NORMAL; float2 uv:TEXCOORD0; float4 color:COLOR; float2 texcoord1:TEXCOORD1; };
   struct v2f { float4 pos:SV_POSITION; float2 uv:TEXCOORD0; float coverage:TEXCOORD1; float3 normal:TEXCOORD2; SHADOW_COORDS(3) };
   v2f vert(appdata v) { v2f o; o.pos=UnityObjectToClipPos(v.vertex);o.uv=v.uv;o.coverage=v.color.r;o.normal=UnityObjectToWorldNormal(v.normal);TRANSFER_SHADOW(o);return o; }
   fixed4 frag(v2f i):SV_Target {
    fixed3 grass=tex2D(_MainTex,i.uv*float2(4,3)).rgb;
    fixed3 dirt=tex2D(_DirtTex,frac(i.uv*8)*float2(.30,.45)+float2(.015,.015)).rgb*_DirtTint.rgb;
    // Grass pigment breaks up the feathered border without alpha sorting or overlapping path planes.
    float boundary=saturate(i.coverage+(dot(grass,float3(.3,.5,.2))-.3)*.16*sin(saturate(i.coverage)*3.14159265));
    fixed3 c=lerp(grass,dirt,boundary);float shade=saturate(dot(normalize(i.normal),normalize(_WorldSpaceLightPos0.xyz)));c*=.73+.27*shade*SHADOW_ATTENUATION(i);return fixed4(c,1);
   }
   ENDCG
  }
  UsePass "Legacy Shaders/VertexLit/SHADOWCASTER"
 }
 Fallback "Diffuse"
}
