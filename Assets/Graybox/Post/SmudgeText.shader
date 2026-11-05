// 초점이 안 맞아 뭉개진 글 줄. 글자 정보 없이 얼룩만 그려서 어떤 거리에서도 읽히지 않는다.
// 전역 _SmudgeSoft(가장자리 부드러움), _SmudgeContrast(얼룩 대비), _SmudgeDrift(흐르는 속도)는 Post_Smudge 키에서 온다
Shader "Graybox/SmudgeText"
{
    Properties
    {
        _Color ("Ink", Color) = (0.5, 0.5, 0.5, 1)
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" "RenderPipeline" = "UniversalPipeline" "IgnoreProjector" = "True" }
        Pass
        {
            Name "Unlit"
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
            CBUFFER_END
            float _SmudgeSoft, _SmudgeContrast, _SmudgeDrift;

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float2 row : TEXCOORD1; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                // 얇은 Cube 줄을 그대로 쓴다. 긴 축이 줄 방향, y가 줄 높이
                float4x4 m = GetObjectToWorldMatrix();
                float3 s = float3(length(m._m00_m10_m20), length(m._m01_m11_m21), length(m._m02_m12_m22));
                bool alongX = s.x >= s.z;
                o.uv = float2((alongX ? v.positionOS.x : v.positionOS.z) + 0.5, v.positionOS.y + 0.5);
                o.row = float2((alongX ? s.x : s.z) / max(s.y, 0.0001), dot(float3(m._m03, m._m13, m._m23), float3(3.1, 7.7, 5.3)));
                return o;
            }

            float Hash(float2 p)
            {
                float3 q = frac(float3(p.xyx) * 0.1031);
                q += dot(q, q.yzx + 33.33);
                return frac((q.x + q.y) * q.z);
            }

            float Noise(float2 p)
            {
                float2 i = floor(p), f = frac(p);
                f = f * f * (3.0 - 2.0 * f);
                return lerp(lerp(Hash(i), Hash(i + float2(1, 0)), f.x), lerp(Hash(i + float2(0, 1)), Hash(i + float2(1, 1)), f.x), f.y);
            }

            half4 frag(Varyings i) : SV_Target
            {
                float len = i.row.x;                 // 줄 높이를 1로 본 줄 길이
                float x = i.uv.x * len, y = i.uv.y;
                float t = _Time.y * _SmudgeDrift;
                float soft = max(_SmudgeSoft, 0.01);

                float along = smoothstep(0.0, soft * 2.0, x) * smoothstep(0.0, soft * 2.0, len - x);
                float across = smoothstep(0.0, soft, y) * smoothstep(0.0, soft, 1.0 - y);

                float word = Noise(float2(x * 0.55 + i.row.y, t));
                float glyph = Noise(float2(x * 1.7 - i.row.y, y * 1.4 + t * 2.0));
                float ink = lerp(1.0, smoothstep(0.25, 0.7, word * 0.6 + glyph * 0.4), _SmudgeContrast);

                return half4(_Color.rgb, _Color.a * along * across * ink);
            }
            ENDHLSL
        }
    }
}
