// 화면 쿼드의 셰이더 값. 본 카메라에는 RT_Base 번짐, 돋보기 카메라에는 RT_Sharp가 보인다.
// 셰이더 Graybox/LensScreen 속성: _BlurRadius(캔버스 px 번짐 반지름)
using UnityEngine;

public sealed class KioskLens
{
    static readonly int BlurRadius = Shader.PropertyToID("_BlurRadius");

    readonly Renderer screen;
    readonly MaterialPropertyBlock block = new MaterialPropertyBlock();

    public KioskLens(Renderer screen) { this.screen = screen; }

    public void Apply(int blurStep)
    {
        if (!screen) return;

        // 번짐 반지름은 캔버스 픽셀(1080 x 1920) 기준, 셰이더가 mip 위에서 16점으로 번지게 한다
        float px = 0f;
        var profile = GameState.I != null ? GameState.I.Profile : null;
        if (profile != null && profile.kioskBlur)
            px = Bal.G("Kiosk_BlurBase", 12f) + blurStep * Bal.G("Nunchi_ScreenBlurPerStep", 5f);

        screen.GetPropertyBlock(block);
        block.SetFloat(BlurRadius, px);
        screen.SetPropertyBlock(block);
    }
}
