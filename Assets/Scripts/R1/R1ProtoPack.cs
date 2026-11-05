// 1-7, 1-8 쉬운 키오스크. 4회차와 같은 가게, 같은 화면(Screen_ 프로토타입)이고 난이도만 다르다.
// 팝업, 광고, 시간 제한, 회원 입력, 구성 고르기 없이 시작, 장소, 메뉴, 장바구니, 결제 수단, 카드, 완료로 간다.
// 메뉴 첫 칸이 쪽지의 불고기 버거 세트이고 나머지는 품절이다. 결제는 PH_Kiosk_R4 의 IC 틈 PayPoint, 포스터는 처음부터 걷혀 있다.
// 부착: PH_Kiosk_R4 인스턴스의 KioskCanvas (KioskScreens와 같은 오브젝트, R4ProtoPack은 뺀다)
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using static KioskData;

public class R1ProtoPack : KioskPack
{
    const string SetName = "불고기 버거 세트";
    const string SetItem = "bulgogi";   // 장바구니 합계와 뜻 자리만 빌린다

    static readonly Dictionary<string, (string vo, string text)> Voice = new Dictionary<string, (string, string)>
    {
        ["place"] = ("k_place", "드시고 가시나요, 가져가시나요?"),
        ["menu"] = ("k_menu", "원하시는 메뉴를 선택해 주세요."),
        ["pay"] = ("k_pay", "결제 수단을 선택해 주세요."),
        ["card"] = ("k_card", "카드를 투입구에 삽입해 주세요."),
    };
    static readonly Dictionary<string, string> Back = new Dictionary<string, string>
    {
        ["cart"] = "menu", ["pay"] = "cart", ["card"] = "pay",
    };

    readonly KioskState K = new KioskState();
    KioskScreens scr;
    KioskPresenter view;
    PayPoint pay;
    bool paid;

    static int SetPrice => Bal.I("R1_SetPrice", 8900);

    public override string FirstScreen => "idle";
    public override bool CanGiveUp => false;

    void Awake()
    {
        scr = GetComponent<KioskScreens>();
        view = new KioskPresenter(scr, K);
    }

    // 어르신 장면도 같은 틈을 쓰니 처음부터 걷어 둔다
    void Start()
    {
        var cover = GetComponentInParent<KioskController>().GetComponentInChildren<PosterFlap>(true);
        if (cover) cover.Open();
    }

    public override void OnEnter()
    {
        pay = Ctl.Pay;
        if (pay)
        {
            pay.Approved += OnPaid;
            pay.Empty += OnEmpty;
        }
        Go("idle");
    }

    void OnDisable()
    {
        if (!pay) return;
        pay.Approved -= OnPaid;
        pay.Empty -= OnEmpty;
    }

    void Go(string id)
    {
        K.screen = id;
        Draw();
        Ctl.SetDown(id == "card");
        HandRig.I.Equip(id == "card" ? ItemId.Card : ItemId.None);
        if (Voice.TryGetValue(id, out var v)) Ctl.Say("kiosk", v.text, v.vo);
    }

    void Draw()
    {
        view.Redraw();
        var s = scr.Current;
        if (!s) return;
        if (K.screen == "menu" && K.tab == Tabs[0] && s.cells.Length > 0)
        {
            var c = s.cells[0];
            c.Bind("item_set");
            c.Text("name", SetName);
            c.Text("mean", "");
            c.Text("price", Won(SetPrice));
            c.Text("desc", "신메뉴");
            c.Text("tag", "NEW");
            c.Show("tag_box", true);
        }
        else if (K.screen == "cart" && K.cart.Count > 0 && s.cells.Length > 0)
        {
            var c = s.cells[0];
            c.Text("name", SetName);
            c.Text("mean", "");
        }
        else if (K.screen == "done") s.Text("number", GameState.I.Order.number.ToString());
    }

    void Toast(string text, float sec = 2f)
    {
        K.toast = text;
        K.toastUntil = Time.time + sec;
        Draw();
    }

    public override void OnTick(float dt)
    {
        if (K.toast == null || Time.time <= K.toastUntil) return;
        K.toast = null;
        Draw();
    }

    public override void OnPress(string id)
    {
        switch (id)
        {
            case "start":
                Ctl.Sfx("kiosk_ok", 0.5f);
                Go("place");
                return;
            case "dine":
            case "takeout":
                K.place = id;
                Ctl.Sfx("kiosk_popup", 0.7f);
                Go("menu");
                return;
            case "item_set":
                GameState.I.Order.item = SetName;
                K.cart.Clear();
                K.cart.Add(new CartLine { item = SetItem, price = SetPrice });
                Ctl.Sfx("kiosk_ok", 0.5f);
                Go("cart");
                return;
            case "cart":
                if (K.cart.Count > 0) Go("cart");
                return;
            case "add_more":
                Go("menu");
                return;
            case "checkout":
                if (K.cart.Count > 0) Go("pay");
                return;
            case "pay_card":
                Go("card");
                return;
            case "back":
                if (Back.TryGetValue(K.screen, out var to)) Go(to);
                return;
        }
        if (id.StartsWith("tab_"))
        {
            K.tab = id.Substring(4);
            Draw();
        }
        else if (id.StartsWith("del_"))
        {
            K.cart.Clear();
            Draw();
        }
        else if (id.StartsWith("item_"))
        {
            Ctl.Sfx("kiosk_error", 0.5f);
            Toast("품절");
        }
        else Ctl.Sfx("kiosk_tap", 0.35f, 0.7f);
    }

    public override bool Hit(Collider col)
    {
        if (col.GetComponentInParent<PayPoint>()) return false;
        if (col.GetComponentInParent<PosterFlap>() || col.GetComponentInParent<CardSlot>() || col.GetComponentInParent<KioskSpot>())
        {
            Ctl.Sfx("kiosk_tap", 0.35f, 0.7f);
            return true;
        }
        return false;
    }

    void OnEmpty() => Toast(K.screen == "card" ? "3 카드" : "카드 전용");

    void OnPaid()
    {
        if (paid) return;
        if (K.screen != "card")
        {
            Ctl.Sfx("kiosk_error", 0.5f);
            Toast("메뉴");
            return;
        }
        paid = true;
        StartCoroutine(Finish());
    }

    IEnumerator Finish()
    {
        GameState.I.Order.number = Bal.I("R1_OrderNumber", 274);
        Go("paying");
        yield return new WaitForSeconds(Bal.G("R1_PayingSec", 0.8f));
        Go("done");
        yield return new WaitForSeconds(Bal.G("R1_DoneShowSec", 1.6f));
        Ctl.Finish();
    }

    // 1-9 알바생이 도와줄 때 다음에 누를 곳을 번쩍여 보여 준다
    public void Hint()
    {
        string next = K.screen switch
        {
            "idle" => "start",
            "place" => "dine",
            "menu" => K.tab == Tabs[0] ? "item_set" : "tab_" + Tabs[0],
            "cart" => "checkout",
            "pay" => "pay_card",
            _ => null,
        };
        if (next != null) scr.Find(next)?.Flash();
        else if (K.screen == "card") Toast("카드");
    }
}
