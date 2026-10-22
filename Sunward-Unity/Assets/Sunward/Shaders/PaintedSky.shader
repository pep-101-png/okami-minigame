Shader "Sunward/Painted Dawn Sky"
{
 Properties { _Zenith("Indigo sky",Color)=(.15,.34,.48,1) _Horizon("Apricot mist",Color)=(.94,.73,.48,1) _Cloud("Rice paper clouds",Color)=(1,.92,.74,1) }
 SubShader
 {
  Tags { "Queue"="Background" "RenderType"="Background" "PreviewType"="Skybox" "RenderPipeline"="UniversalPipeline" }
  Cull Off ZWrite Off
  Pass
  {
   HLSLPROGRAM
   #pragma vertex Vert
   #pragma fragment Frag
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   CBUFFER_START(UnityPerMaterial)
   half4 _Zenith,_Horizon,_Cloud;
   CBUFFER_END
   struct A { float4 positionOS:POSITION; };
   struct V { float4 positionCS:SV_POSITION; float3 direction:TEXCOORD0; };
   V Vert(A v) { V o; o.positionCS=TransformObjectToHClip(v.positionOS.xyz); o.direction=v.positionOS.xyz; return o; }
   float Wave(float a) { return sin(a)*.5+sin(a*2.13+1.7)*.24+sin(a*4.19)*.12; }
   half4 Frag(V i):SV_Target
   {
    float3 d=normalize(i.direction);float altitude=d.y;
    float angle=atan2(d.z,d.x);
    half3 color=lerp(_Horizon.rgb,_Zenith.rgb,pow(saturate(altitude),.55));
    // Layered ink-wash mountains and broad calligraphic cloud forms. This is
    // distant background painting, never a substitute for actual near geometry.
    float farRidge=.026+Wave(angle*6)*.025;
    float middleRidge=.003+Wave(angle*9+1.7)*.033;
    float nearRidge=-.028+Wave(angle*13+3)*.037;
    float ridgeAA=max(.0012,fwidth(altitude));
    color=lerp(color,half3(.52,.62,.57),1-smoothstep(farRidge-ridgeAA*3,farRidge+ridgeAA*3,altitude));
    color=lerp(color,half3(.33,.48,.44),1-smoothstep(middleRidge-ridgeAA*2,middleRidge+ridgeAA*2,altitude));
    color=lerp(color,half3(.18,.32,.29),1-smoothstep(nearRidge-ridgeAA,nearRidge+ridgeAA,altitude));
    float ridgeInk=(1-smoothstep(ridgeAA*.7,ridgeAA*3,abs(altitude-middleRidge)))*.48;
    color=lerp(color,half3(.075,.15,.13),ridgeInk);
    float curl=Wave(angle*4.5)+sin(angle*13+altitude*12)*.12;
    float ribbon=sin(altitude*38+curl*2.8);
    float broken=smoothstep(-.30,.38,Wave(angle*7+altitude*9));
    float cloudAltitude=smoothstep(.055,.14,altitude)*(1-smoothstep(.46,.71,altitude));
    float clouds=smoothstep(.57,.85,ribbon)*broken*cloudAltitude;
    color=lerp(color,_Cloud.rgb,clouds*.77);
    float lowerInk=(1-smoothstep(.045,.11,abs(ribbon-.57)))*broken*cloudAltitude;
    color=lerp(color,half3(.23,.32,.26),lowerInk*.30);
    // Rice-paper grain is fixed in sky direction; no temporal sparkle.
    float paper=sin(d.x*380+d.z*170)*sin(d.y*310+d.z*270);
    color*=1+paper*.009;
    float sunDot=dot(d,normalize(float3(-.55,.28,.8)));
    color+=half3(.17,.085,.025)*pow(saturate(sunDot),24);
    float sunAA=max(.000015,fwidth(sunDot));
    float outerSun=smoothstep(.99875-sunAA,.99875+sunAA,sunDot);
    color=lerp(color,half3(.27,.12,.065),outerSun);
    float sunDisk=smoothstep(.99898-sunAA,.99898+sunAA,sunDot);
    color=lerp(color,half3(.91,.40,.17),sunDisk);
    // A warm uneven wash within the red/gold seal-like sun.
    color=lerp(color,half3(1,.69,.27),sunDisk*smoothstep(.9995,.99995,sunDot)*.55);
    return half4(color,1);
   }
   ENDHLSL
  }
 }
}
