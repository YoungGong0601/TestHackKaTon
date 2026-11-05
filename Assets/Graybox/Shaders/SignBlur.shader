// 간판 앞 흐림 판. 불투명 화면을 뒤에서 읽어 원 모양으로 여러 번 샘플한다. 세기는 재질의 _Radius
Shader "Graybox/SignBlur"
{
    Properties
    {
        _Radius ("Radius (world m)", Range(0, 0.6)) = 0.16
        _Mix ("Mix", Range(0, 1)) = 1
    }
    SubShader
    {
        Tags { "RenderType" = "Transparent" "Queue" = "Transparent" "RenderPipeline" = "UniversalPipeline" }
        Pass
        {
            Name "SignBlur"
            ZWrite Off
            Cull Back
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareOpaqueTexture.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float _Radius;
                float _Mix;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings { float4 positionCS : SV_POSITION; float4 screen : TEXCOORD0; };

            Varyings Vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.screen = ComputeScreenPos(o.positionCS);
                return o;
            }

            half4 Frag(Varyings i) : SV_Target
            {
                float2 uv = i.screen.xy / i.screen.w;
                // 세계 크기 기준이라 멀수록 화면 반지름이 줄어든다. 글자도 같이 줄어 안 읽히는 정도가 같다
                float r = _Radius * UNITY_MATRIX_P[1][1] / max(i.screen.w, 0.01) * 0.5;
                float2 aspect = float2(_ScreenParams.y / _ScreenParams.x, 1);
                half3 sum = SampleSceneColor(uv);
                float w = 1;
                [unroll] for (int k = 0; k < 24; k++)
                {
                    float a = k * 2.399963;
                    float d = sqrt((k + 0.5) / 24.0);
                    float2 o = float2(cos(a), sin(a)) * d * r * aspect;
                    sum += SampleSceneColor(uv + o);
                    w += 1;
                }
                half3 c = sum / w;
                return half4(lerp(SampleSceneColor(uv), c, _Mix), 1);
            }
            ENDHLSL
        }
    }
}
