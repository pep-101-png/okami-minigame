Shader "Sunward/Original Impact Dust"
{
    Properties { _MainTex("Original sand painting",2D)="white"{} _Tiles("Original atlas columns",Float)=1 }
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
            TEXTURE2D(_MainTex);SAMPLER(sampler_MainTex);float _Tiles;
            struct A {float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
            struct V {float4 p:SV_POSITION;float2 uv:TEXCOORD0;half4 color:COLOR;};
            V vert(A i){V o;o.p=TransformObjectToHClip(i.p.xyz);o.uv=i.uv;o.color=i.color;return o;}
            half4 frag(V i):SV_Target
            {
                half4 c=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv)*i.color;
                float2 local=frac(i.uv*_Tiles);float2 edge=min(local,1-local);c.a*=smoothstep(0,.14,min(edge.x,edge.y));return c;
            }
            ENDHLSL
        }
    }
}
