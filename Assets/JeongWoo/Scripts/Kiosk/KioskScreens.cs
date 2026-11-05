// 14개 화면을 켜고 끄고, 쿼드 UV를 버튼으로 바꾼다. 화면 요소는 전부 프리팹에 배치되어 있고 코드는 값만 바꾼다.
//
// 배치: canvas = KioskCanvas (World Space, 레이어 KioskUI, 크기 1080 x 1920, 카메라 2대가 찍음)
// 배치: screens = Screen_<id> 인스턴스 14개(캔버스 자식, 평소 꺼짐)
// 배치: toast = Overlay_Toast (KioskFields, 키 text), 캔버스 맨 뒤 자식
// 배치: info = Overlay_Info (KioskFields, 키 title line0 line1 mean qr), 캔버스 맨 뒤 자식
// 배치: infoClose = Overlay_Info 안 KioskButton id info_close
// 배치: timer = Overlay_Timer (KioskFields, 키 sec low), 오른쪽 위
//
// 레이어: 뜻 풀이는 레이어 KioskReveal의 자식 Canvas 아래에 둔다(레이어는 Canvas 단위로 걸러짐).
//         글자는 괄호 포함 "(뜻)". 정적 뜻 풀이는 프리팹 글자에 직접 적고, 아래 mean 키만 코드가 쓴다.
//
// 화면별 키(KioskField key), 버튼(KioskButton id). 칸은 KioskCell 자식이며 코드가 버튼 id를 넣는다.
// idle    : slide0 slide1 slide2 | 버튼 start(화면 전체)
// place   : 버튼 dine takeout promo easy access lang0~3
// member  : phone, err(미가입 번호 묶음), skip_dark(3회 틀린 뒤 보이는 진한 SKIP) | 버튼 key0~9 keyDEL keyCLR confirm skip
//           backdrop = place. SKIP 평소 글자는 배경과 거의 같은 색, 또렷한 SKIP과 뜻은 KioskReveal
// menu    : place, count, tab_on_<탭이름> 6개, ad(광고 묶음), thumb0~2, item_count, total, checkout_off
//           칸 9개(name mean price kcal desc tag tag_box) | 버튼 tab_<탭이름> hero filter0~4 home cart ad ad_close lang0~3
//           ad 안 버튼 ad, ad_close. ad는 칸보다 뒤 자식
// option  : place, name, desc, price, mean. 칸 3개(name sub price add mean) | 버튼 back lang0~3
// side    : place. 칸 6개(name add mean on) | 버튼 back next home lang0~3
// drink   : place. 칸 8개(name add mean on) | 버튼 back next home lang0~3
// upsell  : 버튼 up_yes up_no. backdrop = drink. 거절 글자는 흐리게, 또렷한 글자와 뜻은 KioskReveal
// cart    : place, empty, promo(광고 묶음, 안에 버튼 promo), total, checkout_off
//           칸 4개(name opts price mean, 버튼은 삭제) | 버튼 add_more checkout home rec0~3 lang0~3
// pay     : place, total | 버튼 pay_qr pay_coupon pay_point pay_card promo back home lang0~3
// card    : msg_box, msg, total | 버튼 back lang0~3
// paying  : bar(왼쪽 피벗 진행 막대)
// cardout : 없음
// done    : number
using System.Collections.Generic;
using UnityEngine;

public class KioskScreens : MonoBehaviour
{
    [SerializeField] RectTransform canvas;
    [SerializeField] KioskScreen[] screens = new KioskScreen[0];
    [SerializeField] KioskFields toast;
    [SerializeField] KioskFields info;
    [SerializeField] KioskButton infoClose;
    [SerializeField] KioskFields timer;

    public KioskScreen Current { get; private set; }

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
    }

    public void SetTimer(int sec, bool show)
    {
        if (!timer) return;
        timer.gameObject.SetActive(show);
        if (!show) return;
        timer.Text("sec", sec.ToString());
        timer.Show("low", sec <= Bal.I("Kiosk_TimerLow", 15));
    }

    /// <summary>지금 누를 수 있는 버튼. 안내 창이 떠 있으면 닫기만.</summary>
    public List<KioskButton> Buttons()
    {
        var list = new List<KioskButton>();
        if (info && info.gameObject.activeInHierarchy) { if (infoClose) list.Add(infoClose); return list; }
        if (!Current) return list;
        foreach (var b in Current.buttons) if (b && b.gameObject.activeInHierarchy) list.Add(b);
        return list;
    }

    /// <summary>쿼드 UV 위의 버튼. 위에 그려진 것부터 찾는다.</summary>
    public KioskButton At(Vector2 uv)
    {
        var r = canvas.rect;
        Vector3 world = canvas.TransformPoint(new Vector3(r.xMin + uv.x * r.width, r.yMin + uv.y * r.height, 0f));
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
