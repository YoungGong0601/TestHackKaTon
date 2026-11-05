// 키오스크 화면 쿼드. 본 카메라에는 _BaseTex를 번지게, 돋보기 카메라(_LensView 1)에는 _SharpTex를 그대로.
// 번짐은 RT의 mip(이미 만들어진 다운샘플) 위에서 16점 나선으로 읽는다. 추가 RT와 패스가 없고 쿼드 픽셀만 비용이 든다.
// _BlurRadius: 번짐 반지름(_BaseTex 픽셀). 원과 확대는 돋보기 카메라와 후처리 합성이 맡는다
Shader "Graybox/LensScreen"
{
    Properties
    {
        _BaseTex ("Base", 2D) = "gray" {}
        _SharpTex ("Sharp", 2D) = "gray" {}
        _BlurRadius ("Blur Radius", Float) = 0
    }
    SubShader
    {
        Tags { "RenderType" = "Opaque" "RenderPipeline" = "UniversalPipeline" "Queue" = "Geometry" }
        Pass
        {
            Name "Unlit"
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_BaseTex); SAMPLER(sampler_BaseTex);
            TEXTURE2D(_SharpTex); SAMPLER(sampler_SharpTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseTex_ST;
                float4 _SharpTex_ST;
                float4 _BaseTex_TexelSize;
                float _BlurRadius;
            CBUFFER_END
            float _LensView;

            struct Attributes { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct Varyings { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.uv = v.uv;
                return o;
            }

            half4 Blurred(float2 uv)
            {
                if (_BlurRadius < 1.0) return SAMPLE_TEXTURE2D(_BaseTex, sampler_BaseTex, uv);
                float lod = max(log2(_BlurRadius) - 1.0, 0.0);
                float2 r = _BaseTex_TexelSize.xy * _BlurRadius;
                half4 sum = 0;
                [unroll] for (int k = 0; k < 16; k++)
                {
                    float a = k * 2.399963;
                    float q = sqrt((k + 0.5) / 16.0);
                    sum += SAMPLE_TEXTURE2D_LOD(_BaseTex, sampler_BaseTex, uv + float2(cos(a), sin(a)) * q * r, lod);
                }
                return sum / 16.0;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half4 c = _LensView > 0.5 ? SAMPLE_TEXTURE2D(_SharpTex, sampler_SharpTex, i.uv) : Blurred(i.uv);
                return half4(c.rgb, 1);
            }
            ENDHLSL
        }
    }
}
