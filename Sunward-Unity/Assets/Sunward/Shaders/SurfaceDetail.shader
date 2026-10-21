Shader "Sunward/Surface Detail PBR"
{
 Properties
 {
  _BaseMap("Base",2D)="white"{} _BaseColor("Tint",Color)=(1,1,1,1)
  _DetailColor("Surface albedo",2D)="white"{} [Normal]_DetailNormal("Surface normal",2D)="bump"{} _DetailMask("Metal AO Smoothness",2D)="white"{}
  _EarthColor("Soil albedo",2D)="white"{} [Normal]_EarthNormal("Soil normal",2D)="bump"{} _EarthMask("Soil mask",2D)="white"{}
  _Scale("World repeats per metre",Float)=.7 _Terrain("Terrain blend",Float)=0
  _Cutoff("Cutoff",Float)=.01 _Cull("Cull",Float)=2
 }
 SubShader
 {
  Tags {"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque"} Cull Back
  Pass
  {
   Name "DetailForward" Tags {"LightMode"="UniversalForward"}
   HLSLPROGRAM
   #pragma vertex Vert
   #pragma fragment Frag
   #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
   #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
   #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
   #pragma multi_compile_fragment _ _SHADOWS_SOFT
   #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
   #pragma multi_compile_fog
   #pragma multi_compile_instancing
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
   #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
   TEXTURE2D(_DetailColor); SAMPLER(sampler_DetailColor);
   TEXTURE2D(_DetailNormal); SAMPLER(sampler_DetailNormal);
   TEXTURE2D(_DetailMask); SAMPLER(sampler_DetailMask);
   TEXTURE2D(_EarthColor); SAMPLER(sampler_EarthColor);
   TEXTURE2D(_EarthNormal); SAMPLER(sampler_EarthNormal);
   TEXTURE2D(_EarthMask); SAMPLER(sampler_EarthMask);
   CBUFFER_START(UnityPerMaterial)
   float4 _BaseColor; float _Scale,_Terrain,_Cutoff,_Cull;
   CBUFFER_END
   struct A {float4 positionOS:POSITION;float3 normalOS:NORMAL;float4 color:COLOR;UNITY_VERTEX_INPUT_INSTANCE_ID};
   struct V {float4 positionCS:SV_POSITION;float3 world:TEXCOORD0;float3 normal:TEXCOORD1;float4 color:TEXCOORD2;half fog:TEXCOORD3;float4 shadow:TEXCOORD4;UNITY_VERTEX_INPUT_INSTANCE_ID};
   V Vert(A a) {V o;UNITY_SETUP_INSTANCE_ID(a);UNITY_TRANSFER_INSTANCE_ID(a,o);o.world=TransformObjectToWorld(a.positionOS.xyz);o.positionCS=TransformWorldToHClip(o.world);o.normal=TransformObjectToWorldNormal(a.normalOS);o.color=a.color;o.fog=ComputeFogFactor(o.positionCS.z);
   #if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
   o.shadow=ComputeScreenPos(o.positionCS);
   #else
   o.shadow=TransformWorldToShadowCoord(o.world);
   #endif
   return o;}
   float BrushNoise(float2 p) { return sin(p.x*.71+sin(p.y*.43))*sin(p.y*.59+sin(p.x*.37)); }
   half4 Frag(V i):SV_Target
   {
    UNITY_SETUP_INSTANCE_ID(i);
    float3 g=normalize(i.normal),w=pow(abs(g),4);w/=max(dot(w,float3(1,1,1)),.001);float3 p=i.world*_Scale;
    // Slow continuous warp breaks a repeated grid while preserving seamless sampling.
    p+=sin(i.world.zxy*.13)*.19;
    half3 col=SAMPLE_TEXTURE2D(_DetailColor,sampler_DetailColor,p.zy).rgb*w.x+SAMPLE_TEXTURE2D(_DetailColor,sampler_DetailColor,p.xz).rgb*w.y+SAMPLE_TEXTURE2D(_DetailColor,sampler_DetailColor,p.xy).rgb*w.z;
    half4 mask=SAMPLE_TEXTURE2D(_DetailMask,sampler_DetailMask,p.zy)*w.x+SAMPLE_TEXTURE2D(_DetailMask,sampler_DetailMask,p.xz)*w.y+SAMPLE_TEXTURE2D(_DetailMask,sampler_DetailMask,p.xy)*w.z;
    float3 nx=UnpackNormal(SAMPLE_TEXTURE2D(_DetailNormal,sampler_DetailNormal,p.zy));
    float3 ny=UnpackNormal(SAMPLE_TEXTURE2D(_DetailNormal,sampler_DetailNormal,p.xz));
    float3 nz=UnpackNormal(SAMPLE_TEXTURE2D(_DetailNormal,sampler_DetailNormal,p.xy));
    float3 n=normalize(float3(nx.z*sign(g.x),nx.y,nx.x)*w.x+float3(ny.x,ny.z*sign(g.y),ny.y)*w.y+float3(nz.x,nz.y,nz.z*sign(g.z))*w.z);
    if(_Terrain>.5)
    {
     // The frozen terrain export has white vertex colours. Define connected
     // road corridors in world coordinates rather than reading a nonexistent mask.
     float market=(1-smoothstep(3.5,4.2,abs(i.world.x+.12*sin(i.world.z*.55))))*(1-smoothstep(22,24,abs(i.world.z)));
     float west=(1-smoothstep(1.5,2.1,abs(i.world.x+32)))*(1-smoothstep(26,28,abs(i.world.z)));
     float crossing=(1-smoothstep(1.25,1.7,abs(i.world.z+8)))*smoothstep(-33,-31,i.world.x)*(1-smoothstep(-15,-13,i.world.x));
     float trial=(1-smoothstep(2.1,2.8,abs(i.world.z)))*smoothstep(0,2,i.world.x)*(1-smoothstep(18,20,i.world.x));
     float road=max(max(market,west),max(crossing,trial));
     // Soft broken brush borders keep the original safe walking corridors.
     road=saturate(road+(1-abs(road*2-1))*BrushNoise(i.world.xz*3)*.14);
     col=lerp(col,SAMPLE_TEXTURE2D(_EarthColor,sampler_EarthColor,p.xz).rgb,road);
     mask=lerp(mask,SAMPLE_TEXTURE2D(_EarthMask,sampler_EarthMask,p.xz),road);
     float3 en=UnpackNormal(SAMPLE_TEXTURE2D(_EarthNormal,sampler_EarthNormal,p.xz));n=normalize(lerp(n,float3(en.x,en.z,en.y),road));
    }
    // Metre-scale pigment washes interrupt repetition without extra texture fetches.
    float wash=BrushNoise(i.world.xz*.31+i.world.y*.12);
    col*=1+wash*.13;
    float facing=pow(1-saturate(abs(dot(g,GetWorldSpaceNormalizeViewDir(i.world)))),4);
    col*=1-facing*.12;
    InputData input=(InputData)0;
    input.positionWS=i.world;input.normalWS=normalize(lerp(g,n,.65));input.viewDirectionWS=GetWorldSpaceNormalizeViewDir(i.world);
    input.shadowCoord=i.shadow;input.fogCoord=i.fog;input.bakedGI=SampleSH(input.normalWS);
    #if defined(_ADDITIONAL_LIGHTS_VERTEX)
    input.vertexLighting=VertexLighting(i.world,input.normalWS);
    #endif
    input.normalizedScreenSpaceUV=GetNormalizedScreenSpaceUV(i.positionCS);input.shadowMask=half4(1,1,1,1);
    SurfaceData surface=(SurfaceData)0;surface.albedo=col*_BaseColor.rgb;surface.alpha=1;surface.metallic=0;surface.specular=half3(.04,.04,.04);surface.smoothness=mask.a;surface.occlusion=mask.g;surface.normalTS=half3(0,0,1);
    half4 result=UniversalFragmentPBR(input,surface);result.rgb=MixFog(result.rgb,i.fog);return result;
   }
   ENDHLSL
  }
  UsePass "Universal Render Pipeline/Lit/ShadowCaster"
  UsePass "Universal Render Pipeline/Lit/DepthOnly"
 }
}
