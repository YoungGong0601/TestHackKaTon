// Pack 화면을 켜고 끄고, 쿼드 UV를 버튼으로 바꾼다. 화면 요소는 전부 프리팹에 배치되어 있고 코드는 값만 바꾼다.
// 배치: canvas = KioskCanvas (World Space, 레이어 KioskUI, 크기 1080 x 1920, 카메라 2대가 찍음)
// 배치: screens = Pack의 화면들 (평소 꺼짐)
// 배치: toast = Overlay_Toast (KioskFields, 키 text), 캔버스 맨 뒤 자식
// 배치: timer = Overlay_Timer (KioskFields, 키 sec low), 오른쪽 위
// 뜻 풀이는 레이어 KioskReveal의 자식 Canvas 아래에 둔다(레이어는 Canvas 단위로 걸러짐).
using System.Collections.Generic;
using UnityEngine;

public class KioskScreens : MonoBehaviour
{
    [SerializeField] RectTransform canvas;
    [SerializeField] KioskScreen[] screens = new KioskScreen[0];
    [SerializeField] KioskFields toast;
    [SerializeField] KioskFields info;
    [SerializeField] KioskButton infoClose;
    [SerializeField] KioskButton infoSkip;
    [SerializeField] KioskButton infoX;
    [SerializeField] KioskButton infoNo;
    [SerializeField] KioskFields timer;

    Vector2? infoHome;

    public KioskScreen Current { get; private set; }
    public RectTransform Canvas => canvas;

    // Pack 프리팹은 부모 캔버스를 저장할 수 없어 KioskController가 넣어 준다
    public void Bind(RectTransform c) => canvas = c;

    public void Show(string id)
    {
        Current = null;
        foreach (var s in screens) if (s.id == id) Current = s;
        var back = Current ? Current.backdrop : null;
        foreach (var s in screens) s.gameObject.SetActive(s == Current || s == back);
    }

    public KioskScreen Get(string id)
    {
        foreach (var s in screens) if (s.id == id) return s;
        return null;
    }

    public void SetToast(string text)
    {
        if (!toast) return;
        toast.gameObject.SetActive(text != null);
        if (text != null) toast.Text("text", text);
    }

    public void SetInfo(KioskInfo i)
    {
        if (!info) return;
        info.gameObject.SetActive(i != null);
        if (i == null) return;
        info.Text("title", i.title);
        info.Text("line0", i.lines.Length > 0 ? i.lines[0] : "");
        info.Text("line1", i.lines.Length > 1 ? i.lines[1] : "");
        info.Text("mean", KioskData.Mean(i.mean));
        info.Show("qr", i.qr);
        foreach (var k in new[] { "app", "code", "point" }) info.Show("v_" + k, i.kind == k);
        info.Text("yes", i.yes);
        info.Text("no", i.no ?? "");
        info.Text("terms", i.terms ?? "");
        if (infoSkip) infoSkip.gameObject.SetActive(i.skip);
        if (infoNo) infoNo.gameObject.SetActive(i.no != null && !i.skip);
    }

    /// <summary>안내 창 판을 가운데에서 옮긴다. jitter가 false면 제자리. 판이 화면 밖으로 나가지 않게 줄인다.</summary>
    public void MoveInfo(bool jitter)
    {
        var panel = info ? info.transform.Find("Panel") as RectTransform : null;
        if (!panel || !canvas) return;
        if (infoHome == null) infoHome = panel.anchoredPosition;
        panel.anchoredPosition = infoHome.Value;
        if (!jitter) return;
        float range = canvas.rect.width * Bal.G("Kiosk_PopJitter", 0.06f);
        var off = new Vector2(Random.Range(-range, range), Random.Range(-range, range));
        var corners = new Vector3[4];
        panel.GetWorldCorners(corners);
        Vector2 lo = canvas.InverseTransformPoint(corners[0]), hi = canvas.InverseTransformPoint(corners[2]);
        var r = canvas.rect;
        off.x = Mathf.Clamp(off.x, Mathf.Min(r.xMin - lo.x, 0f), Mathf.Max(r.xMax - hi.x, 0f));
        off.y = Mathf.Clamp(off.y, Mathf.Min(r.yMin - lo.y, 0f), Mathf.Max(r.yMax - hi.y, 0f));
        float toPanel = canvas.lossyScale.x / Mathf.Max(panel.parent.lossyScale.x, 1e-6f);   // 내용 루트 배율이 걸려 있어도 같은 거리로
        panel.anchoredPosition = infoHome.Value + off * toPanel;
    }

    public void SetTimer(int sec, bool show)
    {
        if (!timer) return;
        timer.gameObject.SetActive(show);
        if (!show) return;
        timer.Text("sec", sec.ToString());
        timer.Show("low", sec <= Bal.I("Kiosk_TimerLow", 5));
    }

    /// <summary>지금 누를 수 있는 버튼. 안내 창이 떠 있으면 그 창 버튼만.</summary>
    public List<KioskButton> Buttons()
    {
        var list = new List<KioskButton>();
        if (info && info.gameObject.activeInHierarchy)
        {
            if (infoClose) list.Add(infoClose);
            if (infoNo && infoNo.gameObject.activeInHierarchy) list.Add(infoNo);
            if (infoX) list.Add(infoX);
            if (infoSkip && infoSkip.gameObject.activeInHierarchy) list.Add(infoSkip);
            return list;
        }
        if (!Current) return list;
        foreach (var b in Current.buttons) if (b && b.gameObject.activeInHierarchy) list.Add(b);
        return list;
    }

    /// <summary>쿼드 UV를 캔버스 위 세계 좌표로.</summary>
    public Vector3 World(Vector2 uv)
    {
        var r = canvas.rect;
        return canvas.TransformPoint(new Vector3(r.xMin + uv.x * r.width, r.yMin + uv.y * r.height, 0f));
    }

    /// <summary>쿼드 UV 위의 버튼. 위에 그려진 것부터 찾는다.</summary>
    public KioskButton At(Vector2 uv)
    {
        Vector3 world = World(uv);
        var list = Buttons();
        for (int i = list.Count - 1; i >= 0; i--) if (list[i].Contains(world)) return list[i];
        return null;
    }

    public Vector2 Uv(KioskButton b)
    {
        var r = canvas.rect;
        Vector3 p = canvas.InverseTransformPoint(b.CenterWorld);
        return new Vector2((p.x - r.xMin) / r.width, (p.y - r.yMin) / r.height);
    }

    public KioskButton Find(string id)
    {
        foreach (var b in Buttons()) if (b.id == id) return b;
        return null;
    }
}
