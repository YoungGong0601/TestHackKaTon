// SignBlur 레이어가 화면에서 보이는 자리를 흰색으로 그린다. 앞 물체에 가린 곳은 깊이 비교로 뺀다.
// KioskPostFeature가 이 마스크로 그 자리만 번짐 피라미드 쪽으로 섞는다.
Shader "Hidden/Graybox/SignMask"
{
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }
        Pass
        {
            ZTest Always ZWrite Off Cull Off Blend Off
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment Frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            float _SignNear;

            struct Attributes { float4 positionOS : POSITION; };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float4 screen : TEXCOORD0;
                float eye : TEXCOORD1;
            };

            Varyings Vert(Attributes v)
            {
                Varyings o;
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.screen = ComputeScreenPos(o.positionCS);
                o.eye = o.positionCS.w;
                return o;
            }

            half4 Frag(Varyings i) : SV_Target
            {
                float raw = SampleSceneDepth(i.screen.xy / i.screen.w);
                clip(LinearEyeDepth(raw, _ZBufferParams) + 0.03 - i.eye);
                return half4(1, saturate(_SignNear / max(i.eye, 0.1)), 0, 1);
            }
            ENDHLSL
        }
    }
}
