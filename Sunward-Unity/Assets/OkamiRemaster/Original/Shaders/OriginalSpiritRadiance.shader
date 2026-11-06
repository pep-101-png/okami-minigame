Shader "Sunward/Original Spirit Radiance"
{
    Properties { _MainTex("Original spirit paint",2D)="white"{} _Tint("Native spirit radiance",Color)=(1,1,1,1) _NativeRibbons("Original ES mesh",Float)=0 }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha One
        ZWrite Off Cull Off
        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);float4 _Tint;float _NativeRibbons;
            struct A { float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR; };
            struct V { float4 p:SV_POSITION;float2 uv:TEXCOORD0;half4 color:COLOR; };
            V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;o.color=i.color;return o;}
            half4 frag(V i):SV_Target{half4 paint=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv);half4 c=paint*i.color;if(_NativeRibbons>.5){c.rgb=paint.rgb*lerp(.2,1,i.color.rgb)*_Tint.rgb;c.a*=_Tint.a;}return c;}
            ENDHLSL
        }
    }
}
