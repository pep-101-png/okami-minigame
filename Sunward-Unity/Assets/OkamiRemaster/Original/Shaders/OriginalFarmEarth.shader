Shader "Sunward/Original Farm Earth Blend"
{
 Properties{_EarthTex("Original earth",2D)="white"{} _GrassTex("Original grass",2D)="white"{}}
 SubShader{
 Tags{"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"}
 Pass{
 Tags{"LightMode"="UniversalForwardOnly"}
 HLSLPROGRAM
 #pragma vertex vert
 #pragma fragment frag
 #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
 #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
 #include "../../Village/Demo/Shaders/VillageLighting.hlsl"
 sampler2D _EarthTex,_GrassTex;
 struct A{float4 vertex:POSITION;float3 normal:NORMAL;};struct V{float4 pos:SV_POSITION;float3 world:TEXCOORD0;};
 V vert(A v){V o;o.world=TransformObjectToWorld(v.vertex.xyz);o.pos=TransformWorldToHClip(o.world);return o;}
 half4 frag(V i):SV_Target{
 float2 d=abs((i.world.xz-float2(46,23.5))/float2(6.4,3.4));
 float edge=max(d.x,d.y)+.025*sin(i.world.x*2.7)+.02*sin(i.world.z*3.4);
 float bed=1-smoothstep(.63,.99,edge);
 float2 uv=i.world.xz;float2 rotated=float2(uv.x*.9397-uv.y*.3420,uv.x*.3420+uv.y*.9397);
 half3 grass=lerp(tex2D(_GrassTex,uv*.035).rgb,tex2D(_GrassTex,rotated*(.035*.73)+float2(.31,.57)).rgb,.35);
 half3 earth=tex2D(_EarthTex,i.world.xz*.08).rgb*half3(.72,.61,.47);
 half3 paint=lerp(grass,earth,bed);Light light=GetMainLight(TransformWorldToShadowCoord(i.world));
 half3 illumination=SampleSH(float3(0,1,0))*.60+light.color*(.32+.48*saturate(light.direction.y))*lerp(.65,1,light.shadowAttenuation);
 return half4(paint*VillageNightPaint(i.world,illumination),1);
 }
 ENDHLSL
 }
 }
}
