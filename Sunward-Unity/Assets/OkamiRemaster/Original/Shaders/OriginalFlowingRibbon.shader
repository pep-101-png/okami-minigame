Shader "Sunward/Original Flowing Spirit Ribbon"
{
    Properties { _MainTex("Original ES paint",2D)="white"{} _Tint("Spirit pigment",Color)=(.92,.95,1,.38) _CurveLength("Original strand length",Float)=3.8271732 }
    SubShader
    {
        Tags { "RenderType"="Transparent" "Queue"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off Cull Off
        Pass
        {
            HLSLPROGRAM
            #pragma target 3.5
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);half4 _Tint;float _CurveLength;float4 _CurvePoints[41];
            struct A { float4 p:POSITION;float2 uv:TEXCOORD0;half4 color:COLOR; };
            struct V { float4 p:SV_POSITION;float3 n:TEXCOORD1;float3 world:TEXCOORD2;float2 uv:TEXCOORD0;half4 color:COLOR; };
            float3 Curve(float u)
            {
                float f=saturate(u)*40;int k=min(39,(int)floor(f));float t=f-k;
                float3 a=_CurvePoints[max(0,k-1)].xyz,b=_CurvePoints[k].xyz,c=_CurvePoints[k+1].xyz,d=_CurvePoints[min(40,k+2)].xyz;
                return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
            }
            V vert(A i)
            {
                V o;float u=saturate(i.p.z/_CurveLength);float3 tangent=normalize(Curve(min(1,u+.002))-Curve(max(0,u-.002)));
                float3 right=normalize(cross(float3(0,1,0),tangent)),up=cross(tangent,right);
                float width=.9+2.1*sin(u*3.14159265);
                float3 p=Curve(u)+(right*i.p.x+up*i.p.y)*width;
                float2 radial=length(i.p.xy)>.00001?normalize(i.p.xy):float2(1,0);float3 n=right*radial.x+up*radial.y;
                o.world=TransformObjectToWorld(p);o.p=TransformWorldToHClip(o.world);o.n=TransformObjectToWorldNormal(n);o.uv=i.uv;o.color=i.color;return o;
            }
            half4 frag(V i):SV_Target
            {
                half4 paint=SAMPLE_TEXTURE2D(_MainTex,sampler_MainTex,i.uv);half energy=max(i.color.r,max(i.color.g,i.color.b));half3 pigment=energy>.001?i.color.rgb/energy:half3(1,1,1);
                float facing=abs(dot(normalize(i.n),normalize(GetWorldSpaceViewDir(i.world))));
                half softness=smoothstep(.02,.85,facing);
                return half4(saturate(paint.rgb*pigment*_Tint.rgb),paint.a*i.color.a*sqrt(saturate(energy))*_Tint.a*softness);
            }
            ENDHLSL
        }
    }
}
