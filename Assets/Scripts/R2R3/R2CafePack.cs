// 2회차 카페 키오스크. 프리팹 Assets/UI/Kiosk/R2/Pack_R2.prefab 루트(KioskScreens와 같은 오브젝트).
// 화면 id: menu shot ice coupon point pay done
// 버튼 id: bg(화면 전체, 맨 뒤) americano latte icon0~3 next | shot0 shot1 | ice0~2 | coupon_none | point_skip
// 표시 키: menu on_americano on_latte cart_count | shot, ice cup_name | done number (없는 키는 무시된다, Docs/UI_REQUEST.md)
// 흐름: 2잔을 담고 다음, 잔마다 shot과 ice, 그 뒤 coupon point pay done. 쪽지와 다른 메뉴도 막지 않는다
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class R2CafePack : KioskPack
{
    const int Cups = 2;

    class Cup { public string id, name, shot, ice; }

    readonly List<Cup> cart = new List<Cup>();
    int cup;
    string now;
    bool leaving;
    PayPoint pay;
    KioskScreens scr;

    KioskScreens Scr => scr ? scr : scr = GetComponent<KioskScreens>();

    public override string FirstScreen => "menu";
    public override bool CanGiveUp => false;   // 다 차면 버튼 없이 비켜난다

    /// <summary>결제까지 끝나서 키오스크를 떠났다. false면 눈치로 비켜난 것.</summary>
    public bool Paid { get; private set; }

    public override void OnEnter()
    {
        cart.Clear();
        cup = 0;
        leaving = false;
        Paid = false;
        ShowCart();
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

    // 결제 창에 가기 전에 다 차면 비켜난다(공통 규칙)
    public override void OnTick(float dt)
    {
        if (now == "pay" || now == "done") return;
        if (Ctl.Nunchi.Running && Ctl.Nunchi.Value >= Bal.G("Nunchi_Max", 100f)) Leave();
    }

    public void Leave()
    {
        if (leaving || Ctl.Busy) return;
        leaving = true;
        Ctl.Finish();
    }

    public override void OnPress(string id)
    {
        if (leaving) return;
        switch (id)
        {
            case "americano": Add(id, "아이스 아메리카노"); break;
            case "latte": Add(id, "아이스 카페라떼"); break;
            case "icon0": case "icon1": case "icon2": case "icon3": Add(id, "다른 메뉴"); break;
            case "next": if (cart.Count == Cups) ToCup(0); else Refuse(cart.Count == 0 ? "메뉴 미선택" : "2잔 미선택"); break;
            case "shot0": case "shot1": cart[cup].shot = id == "shot1" ? "샷 추가" : null; ToIce(); break;
            case "ice0": cart[cup].ice = "얼음 적게"; NextCup(); break;
            case "ice1": cart[cup].ice = null; NextCup(); break;
            case "ice2": cart[cup].ice = "얼음 많이"; NextCup(); break;
            case "coupon_none": To("point"); break;
            case "point_skip": To("pay"); break;
            case "bg": Blank(); break;
        }
    }

    // 2잔이 차 있으면 가장 먼저 담은 잔이 빠진다
    void Add(string id, string name)
    {
        if (cart.Count == Cups) cart.RemoveAt(0);
        cart.Add(new Cup { id = id, name = name });
        ShowCart();
        Ctl.Toast($"{name} {cart.Count}잔째");
    }

    void ShowCart()
    {
        var menu = Scr.Get("menu");
        menu.Show("on_americano", cart.Exists(c => c.id == "americano"));
        menu.Show("on_latte", cart.Exists(c => c.id == "latte"));
        menu.Text("cart_count", $"{cart.Count} ITEM");
    }

    void ToCup(int i)
    {
        cup = i;
        Label("shot");
        To("shot");
        Ctl.Toast(cart[cup].name);
    }

    void ToIce()
    {
        Label("ice");
        To("ice");
        Ctl.Toast(cart[cup].name);
    }

    void Label(string screen) => Scr.Get(screen).Text("cup_name", cart[cup].name);

    void NextCup()
    {
        if (cup + 1 < cart.Count) { ToCup(cup + 1); return; }
        var lines = new List<string>();
        foreach (var c in cart)
        {
            string s = c.name;
            if (c.shot != null) s += " " + c.shot;
            if (c.ice != null) s += " " + c.ice;
            lines.Add(s);
        }
        GameState.I.Order.item = string.Join(", ", lines);
        To("coupon");
    }

    /// <summary>2-5. 쪽지대로 지금 눌러야 할 버튼을 깜빡인다.</summary>
    public void Hint()
    {
        string id = now switch
        {
            "menu" => !cart.Exists(c => c.id == "americano") ? "americano" : !cart.Exists(c => c.id == "latte") ? "latte" : "next",
            "shot" => cart[cup].id == "americano" ? "shot1" : "shot0",
            "ice" => cart[cup].id == "latte" ? "ice0" : "ice1",
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
        Paid = true;
        To("done");
        Scr.Get("done").Text("number", GameState.I.Order.number.ToString());
        StartCoroutine(FinishLater());
    }

    void To(string id) { now = id; Ctl.Go(id); }
    void Refuse(string text) { Ctl.Sfx("kiosk_error", 0.8f); Ctl.Toast(text); }
}
