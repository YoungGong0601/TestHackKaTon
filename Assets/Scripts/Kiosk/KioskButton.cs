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

    public void Flash()
    {
        var g = button ? button.targetGraphic : null;
        if (!g) return;
        g.CrossFadeColor(Color.gray, 0f, true, false);
        g.CrossFadeColor(Color.white, 0.2f, true, false);
    }

    void Reset() => button = GetComponent<Button>();
}
