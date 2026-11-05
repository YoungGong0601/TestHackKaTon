// 2회차 카페 키오스크. 프리팹 Assets/UI/Kiosk/R2/Pack_R2.prefab 루트(KioskScreens와 같은 오브젝트).
// 화면 id: menu shot ice coupon point pay done
// 버튼 id: bg(화면 전체, 맨 뒤) americano latte icon0~3 next | shot0 shot1 | ice0~2 | coupon_none | point_skip
// 표시 키: menu on_americano | done number
using System.Collections;
using UnityEngine;

public class R2CafePack : KioskPack
{
    string now;
    bool picked;
    PayPoint pay;
    KioskScreens scr;

    KioskScreens Scr => scr ? scr : scr = GetComponent<KioskScreens>();

    public override string FirstScreen => "menu";
    public override bool CanGiveUp => false;   // 2회차는 버튼 없음(C7)

    public override void OnEnter()
    {
        picked = false;
        Scr.Get("menu").Show("on_americano", false);
        To(FirstScreen);
        if (pay) return;
        pay = Ctl.Pay;
        pay.Approved += OnApproved;
        pay.Empty += OnEmpty;
    }

    void OnDestroy()
    {
        if (!pay) return;
        pay.Approved -= OnApproved;
        pay.Empty -= OnEmpty;
    }

    public override void OnPress(string id)
    {
        switch (id)
        {
            case "americano": picked = true; Scr.Get("menu").Show("on_americano", true); break;
            case "latte": case "icon0": case "icon1": case "icon2": case "icon3": Refuse("품절"); break;
            case "next": if (picked) To("shot"); else Refuse("메뉴 미선택"); break;
            case "shot0": case "shot1": To("ice"); break;
            case "ice0": case "ice1": case "ice2": To("coupon"); break;
            case "coupon_none": To("point"); break;
            case "point_skip": To("pay"); break;
            case "bg": Blank(); break;
        }
    }

    /// <summary>2-5. 지금 눌러야 할 버튼을 깜빡인다.</summary>
    public void Hint()
    {
        string id = now switch
        {
            "menu" => picked ? "next" : "americano",
            "shot" => "shot0",
            "ice" => "ice1",
            "coupon" => "coupon_none",
            "point" => "point_skip",
            _ => null,
        };
        var b = id != null ? Scr.Find(id) : null;
        if (b) StartCoroutine(Blink(b));
    }

    static IEnumerator Blink(KioskButton b)
    {
        for (int i = 0; i < 3; i++) { b.Flash(); yield return new WaitForSeconds(0.35f); }
    }

    void Blank()
    {
        Refuse(now switch
        {
            "done" => "주문 완료",
            "pay" => "카드 결제",
            "menu" => "메뉴 미선택",
            _ => "항목 미선택",
        });
    }

    void OnEmpty() => Ctl.Toast(now == "pay" ? "카드 결제" : "결제 전");

    // T14: 번호를 읽을 시간을 둔다
    IEnumerator FinishLater()
    {
        yield return new WaitForSeconds(Bal.G("R2_DoneShowSec", 2.5f));
        Ctl.Finish();
    }

    void OnApproved()
    {
        if (now != "pay") { Ctl.Toast("결제 전"); return; }
        To("done");
        Scr.Get("done").Text("number", GameState.I.Order.number.ToString());
        StartCoroutine(FinishLater());
    }

    void To(string id) { now = id; Ctl.Go(id); }
    void Refuse(string text) { Ctl.Sfx("kiosk_error", 0.8f); Ctl.Toast(text); }
}
