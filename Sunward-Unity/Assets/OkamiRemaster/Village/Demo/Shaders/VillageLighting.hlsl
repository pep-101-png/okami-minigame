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
// Original paint keeps its daylight look; sleep-driven night adds cool
// moonlight and warm pools at the original festival/indoor lanterns.
float _SunwardNight;
float4 _SunwardFestivalLights[24];
float3 VillageNightPaint(float3 world,float3 daylight)
{
    if(world.y<-180)return float3(.88,.77,.62); // isolated furnished interiors
    float night=_SunwardNight*step(-5,world.y);
    if(night<.001)return daylight;
    float3 warm=0;
    [loop] for(int i=0;i<24;i++)
    {
        float4 lamp=_SunwardFestivalLights[i];
        float radius=max(.001,lamp.w);
        float falloff=saturate(1-distance(world,lamp.xyz)/radius)*step(.01,lamp.w);
        warm+=float3(1,.49,.16)*falloff*falloff*.75;
    }
    return lerp(daylight,float3(.13,.18,.31)+warm,night);
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
