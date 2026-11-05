// 자체 제작 화면 후처리. 패스 0, 1은 번짐 피라미드(Dual Kawase), 패스 2, 3은 합성.
// 합성 한 번에 번짐, 색수차, 탈색, 딤, 테두리 쉐도우, 필름 그레인을 끝낸다.
Shader "Hidden/JeongWoo/KioskPost"
{
    HLSLINCLUDE
    #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
    #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"

    float _Spread;

    half3 Tap(float2 uv) { return SAMPLE_TEXTURE2D_X_LOD(_BlitTexture, sampler_LinearClamp, uv, 0).rgb; }

    half4 FragDown(Varyings i) : SV_Target
    {
        float2 uv = i.texcoord;
        float2 o = _BlitTexture_TexelSize.xy * _Spread;
        half3 c = Tap(uv) * 4.0;
        c += Tap(uv + float2(-o.x, -o.y));
        c += Tap(uv + float2( o.x, -o.y));
        c += Tap(uv + float2(-o.x,  o.y));
        c += Tap(uv + float2( o.x,  o.y));
        return half4(c * 0.125, 1);
    }

    half4 FragUp(Varyings i) : SV_Target
    {
        float2 uv = i.texcoord;
        float2 o = _BlitTexture_TexelSize.xy * _Spread;
        half3 c = Tap(uv + float2(-o.x * 2.0, 0));
        c += Tap(uv + float2( o.x * 2.0, 0));
        c += Tap(uv + float2(0, -o.y * 2.0));
        c += Tap(uv + float2(0,  o.y * 2.0));
        c += Tap(uv + float2(-o.x,  o.y)) * 2.0;
        c += Tap(uv + float2( o.x,  o.y)) * 2.0;
        c += Tap(uv + float2(-o.x, -o.y)) * 2.0;
        c += Tap(uv + float2( o.x, -o.y)) * 2.0;
        return half4(c / 12.0, 1);
    }

    TEXTURE2D_X(_NearTex);
    TEXTURE2D_X(_MidTex);
    TEXTURE2D_X(_FarTex);
    TEXTURE2D(_LensTex);
    float4 _MidTex_TexelSize;

    float _PostTime;
    float _Aspect;
    float _Dim, _Sat, _Grain, _Ca;
    float4 _Tint;
    float4 _ShadowColor;
    float _Depth, _Corner, _Bottom, _FieldAspect, _SoftWide, _SoftCore, _StrengthWide, _StrengthCore;
    float _WobbleAmp, _WobbleFreq, _WobbleSpeed;
    float _BlurCenter, _BlurEdge, _BlurStart;
    float _LensRim, _LensShade;
    float4 _LensHole;

    float Hash(float2 p)
    {
        float3 q = frac(float3(p.xyx) * 0.1031);
        q += dot(q, q.yzx + 33.33);
        return frac((q.x + q.y) * q.z);
    }

    float ValueNoise(float2 p)
    {
        float2 i = floor(p), f = frac(p);
        f = f * f * (3.0 - 2.0 * f);
        return lerp(lerp(Hash(i), Hash(i + float2(1, 0)), f.x),
                    lerp(Hash(i + float2(0, 1)), Hash(i + float2(1, 1)), f.x), f.y);
    }

    // 화면 가장자리까지의 거리장. 가운데 -1 근처, 가장자리 0, 모서리 바깥은 양수
    float EdgeField(float2 uv)
    {
        float2 p = (uv - 0.5) * 2.0;
        p.x *= _FieldAspect;
        float2 q = abs(p) - float2(_FieldAspect, 1.0) + _Corner;
        float d = length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - _Corner;
        float low = saturate(-p.y);
        return d + _Bottom * low * low;   // 아래쪽이 더 무겁다
    }

    half3 Composite(Varyings i, bool blur)
    {
        float2 uv = i.texcoord;
        float d = EdgeField(uv);

        // 저주파로 천천히 일렁이는 경계
        float2 np = uv * float2(_Aspect, 1.0) * _WobbleFreq;
        float t = _PostTime * _WobbleSpeed;
        float wob = ValueNoise(np + float2(t, -t * 0.7)) * 0.65 + ValueNoise(np * 2.3 + float2(-t * 1.3, t)) * 0.35;
        float dw = d + (wob - 0.5) * _WobbleAmp;

        // 색수차
        float2 c0 = uv - 0.5;
        float r = length(c0);
        float2 co = c0 * _Ca * (0.4 + r * 2.0);
        half3 c;
        c.r = SAMPLE_TEXTURE2D_X_LOD(_BlitTexture, sampler_LinearClamp, uv + co, 0).r;
        c.g = SAMPLE_TEXTURE2D_X_LOD(_BlitTexture, sampler_LinearClamp, uv, 0).g;
        c.b = SAMPLE_TEXTURE2D_X_LOD(_BlitTexture, sampler_LinearClamp, uv - co, 0).b;

        if (blur)
        {
            float e = saturate(1.0 + dw);
            float b = lerp(_BlurCenter, _BlurEdge, smoothstep(_BlurStart, 1.0, e));
            b = saturate(b) * 3.0;

            half3 nearC = SAMPLE_TEXTURE2D_X_LOD(_NearTex, sampler_LinearClamp, uv, 0).rgb;
            float2 mo = _MidTex_TexelSize.xy * 0.5;
            half3 midC = SAMPLE_TEXTURE2D_X_LOD(_MidTex, sampler_LinearClamp, uv + mo, 0).rgb;
            midC += SAMPLE_TEXTURE2D_X_LOD(_MidTex, sampler_LinearClamp, uv - mo, 0).rgb;
            midC += SAMPLE_TEXTURE2D_X_LOD(_MidTex, sampler_LinearClamp, uv + float2(mo.x, -mo.y), 0).rgb;
            midC += SAMPLE_TEXTURE2D_X_LOD(_MidTex, sampler_LinearClamp, uv + float2(-mo.x, mo.y), 0).rgb;
            midC *= 0.25;
            half3 farC = SAMPLE_TEXTURE2D_X_LOD(_FarTex, sampler_LinearClamp, uv, 0).rgb;

            c = lerp(c, nearC, saturate(b));
            c = lerp(c, midC, saturate(b - 1.0));
            c = lerp(c, farC, saturate(b - 2.0));
        }

        // 돋보기 원: 돋보기 카메라가 확대해 그린 또렷한 그림으로 바꾼다
        float inside = 0.0;
        if (_LensHole.z > 0.0)
        {
            float2 ld = (uv - _LensHole.xy) * float2(_Aspect, 1.0);
            float dist = length(ld);
            inside = 1.0 - smoothstep(_LensHole.z * 0.985, _LensHole.z, dist);
            half3 lensC = SAMPLE_TEXTURE2D_LOD(_LensTex, sampler_LinearClamp, ld / (2.0 * _LensHole.z) + 0.5, 0).rgb;
            lensC *= 1.0 - _LensRim * smoothstep(_LensHole.z * 0.94, _LensHole.z * 0.985, dist);
            c = lerp(c, lensC, inside);
        }

        // 여기부터는 HTML판과 같은 감마에 가까운 값으로 다룬다
        half3 g = sqrt(max(c, 0.0));
        half l = dot(g, half3(0.2126, 0.7152, 0.0722));
        g = lerp(l.xxx, g, _Sat) * _Tint.rgb * _Dim;

        // 테두리 쉐도우: 넓은 반영과 좁은 반영 두 겹, 안쪽으로 먹어 들어온다
        float inset = dw + _Depth;
        float wide = smoothstep(-_SoftWide, _SoftWide * 0.6, inset) * _StrengthWide;
        float core = smoothstep(-_SoftCore, _SoftCore, inset - _Depth * 0.4) * _StrengthCore;
        float shade = (1.0 - (1.0 - wide) * (1.0 - core)) * (1.0 - inside * _LensShade);
        g = lerp(g, _ShadowColor.rgb * (0.6 + 0.4 * wob), shade);

        // 어두운 곳에 더 보이는 필름 그레인
        float n = Hash(i.positionCS.xy + frac(_PostTime) * 917.0) - 0.5;
        g += n * _Grain * (0.45 + 0.55 * (1.0 - saturate(l)));

        g = max(g, 0.0);
        return g * g;
    }

    half4 FragPlain(Varyings i) : SV_Target { return half4(Composite(i, false), 1); }
    half4 FragBlur(Varyings i) : SV_Target { return half4(Composite(i, true), 1); }
    ENDHLSL

    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }
        ZTest Always ZWrite Off Cull Off Blend Off

        Pass
        {
            Name "Down"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragDown
            ENDHLSL
        }
        Pass
        {
            Name "Up"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragUp
            ENDHLSL
        }
        Pass
        {
            Name "CompositePlain"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragPlain
            ENDHLSL
        }
        Pass
        {
            Name "CompositeBlur"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment FragBlur
            ENDHLSL
        }
    }
}
