Shader "Sunward/Original Flowing Spirit Ribbon"
{
    Properties { _MainTex("Original ES paint",2D)="white"{} _Tint("Spirit pigment",Color)=(.94,.96,1,.72) }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off Cull Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);half4 _Tint;
            struct A { float4 p:POSITION;float3 n:NORMAL;float2 uv:TEXCOORD0;half4 color:COLOR; };
            struct V { float4 p:SV_POSITION;float3 n:TEXCOORD1;float2 uv:TEXCOORD0;half4 color:COLOR; };
            V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.n=TransformObjectToWorldNormal(i.n);o.uv=i.uv;o.color=i.color;return o;}
            half4 frag(V i):SV_Target
            {
                half4 paint=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv);
                half shade=.82+.16*abs(dot(normalize(i.n),normalize(float3(.4,.8,.3))));
                // Bounded pigment and ordinary transparency: overlaps cannot add
                // six HDR whites or erase Amaterasu's native body markings.
                half energy=max(i.color.r,max(i.color.g,i.color.b));
                half3 pigment=energy>.001?i.color.rgb/energy:half3(1,1,1);
                // The native additive mesh encodes fading in RGB. Carry that
                // energy into alpha so dark fade vertices stay transparent.
                return half4(saturate(paint.rgb*pigment*_Tint.rgb*shade),paint.a*i.color.a*sqrt(saturate(energy))*_Tint.a);
            }
            ENDHLSL
        }
    }
}
