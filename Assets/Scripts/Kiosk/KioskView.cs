// 키오스크 앞 시선. D 키오스크, A 알바생, S 뒤, W 아래. PlayerController 다음 순서로 카메라를 매 프레임 직접 놓는다. 원본 index.js applyCamera.
using UnityEngine;

public sealed class KioskView
{
    readonly KioskController ctl;
    float down, downTarget, edge, fov;
    Vector3 pos;
    Quaternion rot;

    public KioskView(KioskController ctl) { this.ctl = ctl; }

    public bool Down => downTarget > 0f;

    static float Damp(float a, float b, float k, float dt) => Mathf.Lerp(a, b, 1f - Mathf.Exp(-k * dt));

    /// <summary>카메라 위치는 PlayerController가 매 프레임 다시 놓으므로 화각만 기억한다.</summary>
    public void Save(Camera eye) => fov = eye.fieldOfView;

    public void Restore(Camera eye) => eye.fieldOfView = fov;

    /// <summary>지금 카메라 자리에서 부드럽게 이어 간다.</summary>
    public void Begin(Camera eye)
    {
        pos = eye.transform.position;
        rot = eye.transform.rotation;
        down = downTarget = 0f; edge = 0f;
        eye.fieldOfView = Bal.G("Kiosk_Fov", 60f);
    }

    public void ToggleDown() => downTarget = Down ? 0f : 1f;

    public void SetDown(bool on) => downTarget = on ? 1f : 0f;

    /// <summary>포인터를 화면 위아래 끝에 대고 있으면 고개를 움직인다.</summary>
    public bool EdgeTick(float cursorDown, float dt)
    {
        float low = Bal.G("Kiosk_EdgeLow", 0.955f), high = Bal.G("Kiosk_EdgeHigh", 0.045f), hold = Bal.G("Kiosk_EdgeHold", 0.35f);
        if (cursorDown > low || cursorDown < high)
        {
            edge += dt;
            if (edge <= hold) return false;
            if (cursorDown > low && !Down) { downTarget = 1f; return true; }
            if (cursorDown < high && Down) { downTarget = 0f; return true; }
            return false;
        }
        edge = 0f;
        return false;
    }

    public void Apply(Camera eye, PlayerController pc, string view, Vector2 cursorCentered, Vector3 lookTarget, float dt, bool snap = false)
    {
        // 플레이어가 이번 프레임에 넣은 흔들림만 이어 받는다
        Vector3 shake = eye.transform.localPosition - Vector3.up * pc.EyeHeight;
        down = snap ? downTarget : Damp(down, downTarget, 5f, dt);
        float h = Mathf.Lerp(Bal.Age("KioskEye", 1.58f, 1.56f, 1.52f, 1.47f), Bal.F("KioskEyeDown", 1.3f), down);
        float dist = Mathf.Lerp(Bal.G("Kiosk_Dist", 0.76f), Bal.G("Kiosk_DistDown", 0.6f), down);
        float aimY = Mathf.Lerp(Bal.G("Kiosk_AimY", 1.372f), Bal.G("Kiosk_AimYDown", 0.74f), down);

        Vector3 floor = ctl.Floor, want = floor + ctl.Out * dist + Vector3.up * h;
        pos = snap ? want : Vector3.Lerp(pos, want, 1f - Mathf.Exp(-7f * dt));

        Quaternion target;
        if (view == "kiosk")
        {
            float yaw = cursorCentered.x * Bal.G("Kiosk_LookYaw", 0.11f) * Mathf.Rad2Deg;
            float pitch = cursorCentered.y * Bal.G("Kiosk_LookPitch", 0.08f) * Mathf.Rad2Deg;
            target = Quaternion.LookRotation(floor + Vector3.up * aimY - want) * Quaternion.Euler(pitch, yaw, 0f);
        }
        else target = Quaternion.LookRotation(lookTarget - pos);

        rot = snap ? target : Quaternion.Slerp(rot, target, 1f - Mathf.Exp(-(view == "kiosk" ? 5f : 6f) * dt));
        eye.transform.SetPositionAndRotation(pos + shake, rot);
    }
}
