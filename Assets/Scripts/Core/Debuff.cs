using UnityEngine;

// 디버프 값. 프로필과 시트에서 쓸 때마다 읽으므로 챕터가 바뀌면 저절로 바뀐다. 라운드 코드는 읽기만 한다
public static class Debuff
{
    public const float OpenHz = 22000f;

    static CharacterProfile P => GameState.I != null ? GameState.I.Profile : null;

    /// <summary>화면 쿼드 번짐 반지름. 눈치 BlurStep 가산은 KioskLens가 더한다.</summary>
    public static float KioskBlur => P != null && P.kioskBlur ? Bal.Age("KioskBlur", 0f, 3f, 7f, 35f) : 0f;

    public static float MuffleCutoff => P != null && P.muffle ? Bal.Age("MuffleCutoff", OpenHz, 6000f, 3000f, 1800f) : OpenHz;

    /// <summary>0 또렷, 1 최대</summary>
    public static float Muffle01 => 1f - Mathf.InverseLerp(Mathf.Log(1000f), Mathf.Log(OpenHz), Mathf.Log(MuffleCutoff));

    public static float Tremble => P != null && P.tremble ? Bal.Age("Tremble", 0f, 0f, 0.6f, 1f) : 0f;

    /// <summary>손떨림 폭. level은 인물과 눈치를 합친 값, sec은 떨림이 시작된 뒤 지난 시간. 큰 폭에서 줄어들어 작은 폭으로 계속된다.</summary>
    public static float TrembleAmp(float level, float sec)
    {
        float peak = Bal.G("Tremble_Peak", 0.7f) * level, floor = Bal.G("Tremble_Base", 0.22f) * level;
        return floor + (peak - floor) * Mathf.Exp(-sec / Mathf.Max(Bal.G("Tremble_Tau", 0.8f), 0.01f));
    }

    public static float CursorLagSec => P != null && P.cursorLag ? Bal.Age("CursorLagSec", 0f, 0f, 0.12f, 0.2f) : 0f;

    /// <summary>돋보기 초점 흐림 0~1. 주기 끝의 Lens_FocusBlurSec 동안 서서히 흐려졌다 돌아온다.</summary>
    public static float LensBlur01
    {
        get
        {
            if (P == null || !P.lensFocus) return 0f;
            float period = Mathf.Max(Bal.G("Lens_FocusPeriodSec", 8f), 0.1f), blur = Bal.G("Lens_FocusBlurSec", 2f);
            float left = period - Time.time % period;
            return left < blur ? Mathf.Sin(left / Mathf.Max(blur, 0.01f) * Mathf.PI) : 0f;
        }
    }

    /// <summary>흐려진 구간이면 false. Readable이 이때 onRead를 내지 않는다.</summary>
    public static bool LensFocused => LensBlur01 < 0.5f;
}
