// 화면 위 누를 곳. 판정은 쿼드 UV에서 캔버스 좌표로 바꿔 RectTransform 안인지 본다(EventSystem 안 씀).
// 배치: id = 버튼 id, button = 같은 오브젝트의 Button(눌림 표시용, 없어도 됨)
using UnityEngine;
using UnityEngine.UI;

[RequireComponent(typeof(RectTransform))]
public class KioskButton : MonoBehaviour
{
    public string id;
    public Button button;

    RectTransform Rect => (RectTransform)transform;

    public bool Contains(Vector3 world) => Rect.rect.Contains((Vector2)Rect.InverseTransformPoint(world));

    public Vector3 CenterWorld => Rect.TransformPoint(Rect.rect.center);

    /// <summary>가운데 0, 가장자리 1. 터치가 버튼 끝에 얼마나 가까운가.</summary>
    public float EdgeRatio(Vector3 world)
    {
        var r = Rect.rect;
        Vector2 p = (Vector2)Rect.InverseTransformPoint(world) - r.center;
        return Mathf.Max(Mathf.Abs(p.x) / Mathf.Max(r.width * 0.5f, 1f), Mathf.Abs(p.y) / Mathf.Max(r.height * 0.5f, 1f));
    }

    // 터치 표시는 잠깐만. 트윈은 화면이 꺼지거나 다시 그려질 때 끊겨 회색이 남으니 쓰지 않고 시간을 직접 센다. 선택 표시는 on 필드가 따로 맡는다
    float flash;

    public void Flash()
    {
        var g = button ? button.targetGraphic : null;
        if (!g) return;
        flash = FlashSec;
        g.canvasRenderer.SetColor(Color.gray);
    }

    static float FlashSec => Mathf.Max(Bal.G("Kiosk_FlashSec", 0.2f), 0.01f);

    /// <summary>터치 표시를 sec만큼 진행한다. 다 되면 정확히 흰색으로 돌아간다.</summary>
    public void FlashTick(float sec)
    {
        if (flash <= 0f) return;
        flash -= sec;
        var g = button ? button.targetGraphic : null;
        if (!g || flash <= 0f) { ClearPress(); return; }
        g.canvasRenderer.SetColor(Color.Lerp(Color.white, Color.gray, flash / FlashSec));
    }

    void Update() => FlashTick(Time.unscaledDeltaTime);

    void ClearPress()
    {
        flash = 0f;
        var g = button ? button.targetGraphic : null;
        if (g) g.canvasRenderer.SetColor(Color.white);
    }

    void OnEnable() => ClearPress();
    void OnDisable() => ClearPress();

    void Reset() => button = GetComponent<Button>();
}
