//
// Copyright (c) Microsoft. All rights reserved.
// This code is licensed under the MIT License (MIT).
// THIS CODE IS PROVIDED *AS IS* WITHOUT WARRANTY OF
// ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING ANY
// IMPLIED WARRANTIES OF FITNESS FOR A PARTICULAR
// PURPOSE, MERCHANTABILITY, OR NON-INFRINGEMENT.
//
// Developed by Minigraph
//
// Author(s):	James Stanard
//				Alex Nankervis
//
// Thanks to Michal Drobot for his feedback.

#include "Common.hlsli"
#include "LightGrid.hlsli"

cbuffer PSConstants : register(b0)
{
    float3 SunDirection;
    float3 SunColor;
    float3 AmbientColor;
    float4 ShadowTexelSize;

    float4 InvTileDim;
    uint4 TileCount;
    uint4 FirstLightIndex;

    uint FrameIndexMod2;
}

StructuredBuffer<LightData> lightBuffer : register(t14);
Texture2DArray<float> lightShadowArrayTex : register(t15);
ByteAddressBuffer lightGrid : register(t16);
ByteAddressBuffer lightGridBitMask : register(t17);

void AntiAliasSpecular(inout float3 texNormal, inout float gloss)
{
    float normalLenSq = dot(texNormal, texNormal);
    float invNormalLen = rsqrt(normalLenSq);
    texNormal *= invNormalLen;
    float normalLen = normalLenSq * invNormalLen;
    float flatness = saturate(1 - abs(ddx(normalLen)) - abs(ddy(normalLen)));
    gloss = exp2(lerp(0, log2(gloss), flatness));
}

// Apply fresnel to modulate the specular albedo
void FSchlick(inout float3 specular, inout float3 diffuse, float3 lightDir, float3 halfVec)
{
    float fresnel = pow(1.0 - saturate(dot(lightDir, halfVec)), 5.0);
    specular = lerp(specular, 1, fresnel);
    diffuse = lerp(diffuse, 0, fresnel);
}

float3 ApplyAmbientLight(
    float3 diffuse,   // Diffuse albedo
    float ao,         // Pre-computed ambient-occlusion
    float3 lightColor // Radiance of ambient light
)
{
    return ao * diffuse * lightColor;
}

float GetDirectionalShadow(float3 ShadowCoord, Texture2D<float> texShadow)
{
    const float Dilation = 2.0;
    float d1 = Dilation * ShadowTexelSize.x * 0.125;
    float d2 = Dilation * ShadowTexelSize.x * 0.875;
    float d3 = Dilation * ShadowTexelSize.x * 0.625;
    float d4 = Dilation * ShadowTexelSize.x * 0.375;
    float result = (2.0 * texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy, ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(-d2, d1), ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(-d1, -d2), ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(d2, -d1), ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(d1, d2), ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(-d4, d3), ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(-d3, -d4), ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(d4, -d3), ShadowCoord.z) +
                    texShadow.SampleCmpLevelZero(shadowSampler, ShadowCoord.xy + float2(d3, d4), ShadowCoord.z)) /
                   10.0;
    return result * result;
}

float GetShadowConeLight(uint lightIndex, float3 shadowCoord)
{
    float result = lightShadowArrayTex.SampleCmpLevelZero(
        shadowSampler, float3(shadowCoord.xy, lightIndex), shadowCoord.z);
    return result * result;
}

float3 ApplyLightCommon(
    float3 diffuseColor,  // Diffuse albedo
    float3 specularColor, // Specular albedo
    float specularMask,   // Where is it shiny or dingy?
    float gloss,          // Specular power
    float3 normal,        // World-space normal
    float3 viewDir,       // World-space vector from eye to point
    float3 lightDir,      // World-space vector from point to light
    float3 lightColor     // Radiance of directional light
)
{
    float3 halfVec = normalize(lightDir - viewDir);
    float nDotH = saturate(dot(halfVec, normal));

    FSchlick(diffuseColor, specularColor, lightDir, halfVec);

    float specularFactor = specularMask * pow(nDotH, gloss) * (gloss + 2) / 8;

    float nDotL = saturate(dot(normal, lightDir));

    return nDotL * lightColor * (diffuseColor + specularFactor * specularColor);
}

float3 ApplyDirectionalLight(
    float3 diffuseColor,  // Diffuse albedo
    float3 specularColor, // Specular albedo
    float specularMask,   // Where is it shiny or dingy?
    float gloss,          // Specular power
    float3 normal,        // World-space normal
    float3 viewDir,       // World-space vector from eye to point
    float3 lightDir,      // World-space vector from point to light
    float3 lightColor,    // Radiance of directional light
    float3 shadowCoord,   // Shadow coordinate (Shadow map UV & light-relative Z)
    Texture2D<float> ShadowMap)
{
    float shadow = GetDirectionalShadow(shadowCoord, ShadowMap);

    return shadow * ApplyLightCommon(
                        diffuseColor,
                        specularColor,
                        specularMask,
                        gloss,
                        normal,
                        viewDir,
                        lightDir,
                        lightColor);
}

float3 ApplyPointLight(
    float3 diffuseColor,  // Diffuse albedo
    float3 specularColor, // Specular albedo
    float specularMask,   // Where is it shiny or dingy?
    float gloss,          // Specular power
    float3 normal,        // World-space normal
    float3 viewDir,       // World-space vector from eye to point
    float3 worldPos,      // World-space fragment position
    float3 lightPos,      // World-space light position
    float lightRadiusSq,
    float3 lightColor // Radiance of directional light
)
{
    float3 lightDir = lightPos - worldPos;
    float lightDistSq = dot(lightDir, lightDir);
    float invLightDist = rsqrt(lightDistSq);
    lightDir *= invLightDist;

    // modify 1/d^2 * R^2 to fall off at a fixed radius
    // (R/d)^2 - d/R = [(1/d^2) - (1/R^2)*(d/R)] * R^2
    float distanceFalloff = lightRadiusSq * (invLightDist * invLightDist);
    distanceFalloff = max(0, distanceFalloff - rsqrt(distanceFalloff));

    return distanceFalloff * ApplyLightCommon(
                                 diffuseColor,
                                 specularColor,
                                 specularMask,
                                 gloss,
                                 normal,
                                 viewDir,
                                 lightDir,
                                 lightColor);
}

float3 ApplyConeLight(
    float3 diffuseColor,  // Diffuse albedo
    float3 specularColor, // Specular albedo
    float specularMask,   // Where is it shiny or dingy?
    float gloss,          // Specular power
    float3 normal,        // World-space normal
    float3 viewDir,       // World-space vector from eye to point
    float3 worldPos,      // World-space fragment position
    float3 lightPos,      // World-space light position
    float lightRadiusSq,
    float3 lightColor, // Radiance of directional light
    float3 coneDir,
    float2 coneAngles)
{
    float3 lightDir = lightPos - worldPos;
    float lightDistSq = dot(lightDir, lightDir);
    float invLightDist = rsqrt(lightDistSq);
    lightDir *= invLightDist;

    // modify 1/d^2 * R^2 to fall off at a fixed radius
    // (R/d)^2 - d/R = [(1/d^2) - (1/R^2)*(d/R)] * R^2
    float distanceFalloff = lightRadiusSq * (invLightDist * invLightDist);
    distanceFalloff = max(0, distanceFalloff - rsqrt(distanceFalloff));

    float coneFalloff = dot(-lightDir, coneDir);
    coneFalloff = saturate((coneFalloff - coneAngles.y) * coneAngles.x);

    return (coneFalloff * distanceFalloff) * ApplyLightCommon(
                                                 diffuseColor,
                                                 specularColor,
                                                 specularMask,
                                                 gloss,
                                                 normal,
                                                 viewDir,
                                                 lightDir,
                                                 lightColor);
}

float3 ApplyConeShadowedLight(
    float3 diffuseColor,  // Diffuse albedo
    float3 specularColor, // Specular albedo
    float specularMask,   // Where is it shiny or dingy?
    float gloss,          // Specular power
    float3 normal,        // World-space normal
    float3 viewDir,       // World-space vector from eye to point
    float3 worldPos,      // World-space fragment position
    float3 lightPos,      // World-space light position
    float lightRadiusSq,
    float3 lightColor, // Radiance of directional light
    float3 coneDir,
    float2 coneAngles,
    float4x4 shadowTextureMatrix,
    uint lightIndex)
{
    float4 shadowCoord = mul(shadowTextureMatrix, float4(worldPos, 1.0));
    shadowCoord.xyz *= rcp(shadowCoord.w);
    float shadow = GetShadowConeLight(lightIndex, shadowCoord.xyz);

    return shadow * ApplyConeLight(
                        diffuseColor,
                        specularColor,
                        specularMask,
                        gloss,
                        normal,
                        viewDir,
                        worldPos,
                        lightPos,
                        lightRadiusSq,
                        lightColor,
                        coneDir,
                        coneAngles);
}

// Helper function for iterating over a sparse list of bits.  Gets the offset of the next
// set bit, clears it, and returns the offset.
uint PullNextBit(inout uint bits)
{
    uint bitIndex = firstbitlow(bits);
    bits ^= 1u << bitIndex;
    return bitIndex;
}

void ShadeLights(inout float3 colorSum, uint2 pixelPos,
                 float3 diffuseAlbedo,  // Diffuse albedo
                 float3 specularAlbedo, // Specular albedo
                 float specularMask,    // Where is it shiny or dingy?
                 float gloss,
                 float3 normal,
                 float3 viewDir,
                 float3 worldPos)
{
    uint2 tilePos = GetTilePos(pixelPos, InvTileDim.xy);
    uint tileIndex = GetTileIndex(tilePos, TileCount.x);
    uint tileOffset = GetTileOffset(tileIndex);

    // Light Grid Preloading setup
    uint lightBitMaskGroups[4] = {0, 0, 0, 0};
    uint4 lightBitMask = lightGridBitMask.Load4(tileIndex * 16);

    lightBitMaskGroups[0] = lightBitMask.x;
    lightBitMaskGroups[1] = lightBitMask.y;
    lightBitMaskGroups[2] = lightBitMask.z;
    lightBitMaskGroups[3] = lightBitMask.w;

    uint tileLightCount = lightGrid.Load(tileOffset + 0);
    uint tileLightCountSphere = (tileLightCount >> 0) & 0xff;
    uint tileLightCountCone = (tileLightCount >> 8) & 0xff;
    uint tileLightCountConeShadowed = (tileLightCount >> 16) & 0xff;

    uint tileLightLoadOffset = tileOffset + 4;

    // sphere
    uint n;
    for (n = 0; n < tileLightCountSphere; n++, tileLightLoadOffset += 4)
    {
        uint lightIndex = lightGrid.Load(tileLightLoadOffset);
        LightData lightData = lightBuffer[lightIndex];
        colorSum += ApplyPointLight(POINT_LIGHT_ARGS);
    }

    // cone
    for (n = 0; n < tileLightCountCone; n++, tileLightLoadOffset += 4)
    {
        uint lightIndex = lightGrid.Load(tileLightLoadOffset);
        LightData lightData = lightBuffer[lightIndex];
        colorSum += ApplyConeLight(CONE_LIGHT_ARGS);
    }

    // cone w/ shadow map
    for (n = 0; n < tileLightCountConeShadowed; n++, tileLightLoadOffset += 4)
    {
        uint lightIndex = lightGrid.Load(tileLightLoadOffset);
        LightData lightData = lightBuffer[lightIndex];
        colorSum += ApplyConeShadowedLight(SHADOWED_LIGHT_ARGS);
    }
}
