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

    public void Flash()
    {
        var g = button ? button.targetGraphic : null;
        if (!g) return;
        g.CrossFadeColor(Color.gray, 0f, true, false);
        g.CrossFadeColor(Color.white, 0.2f, true, false);
    }

    void Reset() => button = GetComponent<Button>();
}
