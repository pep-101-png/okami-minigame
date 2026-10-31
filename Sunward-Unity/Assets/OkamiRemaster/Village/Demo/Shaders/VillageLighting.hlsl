#ifndef SUNWARD_VILLAGE_LIGHTING_INCLUDED
#define SUNWARD_VILLAGE_LIGHTING_INCLUDED
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
#include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
Light VillageMainLight(float3 world)
{
#if defined(_MAIN_LIGHT_SHADOWS_SCREEN)
    float4 coord = ComputeScreenPos(TransformWorldToHClip(world));
#else
    float4 coord = TransformWorldToShadowCoord(world);
#endif
    return GetMainLight(coord);
}
float3 _LightDirection;
float3 _LightPosition;
float4 VillageShadowPosition(float3 positionOS, float3 normalOS)
{
    float3 world = TransformObjectToWorld(positionOS);
    float3 normal = TransformObjectToWorldNormal(normalOS);
#if defined(_CASTING_PUNCTUAL_LIGHT_SHADOW)
    float3 lightDirection = normalize(_LightPosition - world);
#else
    float3 lightDirection = _LightDirection;
#endif
    float4 clipPos = TransformWorldToHClip(ApplyShadowBias(world, normal, lightDirection));
#if UNITY_REVERSED_Z
    clipPos.z = min(clipPos.z, UNITY_NEAR_CLIP_VALUE * clipPos.w);
#else
    clipPos.z = max(clipPos.z, UNITY_NEAR_CLIP_VALUE * clipPos.w);
#endif
    return clipPos;
}
#endif
