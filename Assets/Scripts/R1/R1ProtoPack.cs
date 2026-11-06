// 1-7, 1-8 쉬운 키오스크. 4회차와 같은 가게, 같은 화면(Screen_ 프로토타입)이고 난이도만 다르다.
// 팝업, 광고, 시간 제한, 회원 입력, 구성 고르기 없이 시작, 장소, 메뉴, 장바구니, 결제 수단, 카드, 완료로 간다.
// 쪽지의 신메뉴(KioskPick)만 살 수 있고 첫 칸 불고기 버거 세트를 포함한 나머지는 품절이다. 결제는 PH_Kiosk_R4 의 IC 틈 PayPoint, 포스터는 처음부터 걷혀 있다.
// 부착: PH_Kiosk_R4 인스턴스의 KioskCanvas (KioskScreens와 같은 오브젝트, R4ProtoPack은 뺀다)
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using static KioskData;

public class R1ProtoPack : KioskPack
{

    static readonly Dictionary<string, (string vo, string text)> Voice = new Dictionary<string, (string, string)>
    {
        ["place"] = ("k_place", "드시고 가시나요, 가져가시나요?"),
        ["menu"] = ("k_menu", "원하시는 메뉴를 선택해 주세요."),
        ["pay"] = ("k_pay", "결제 수단을 선택해 주세요."),
        ["card"] = ("k_card", "카드를 투입구에 삽입해 주세요."),
        ["paying"] = ("k_cardhold", "결제가 완료될 때까지 카드를 빼지 마세요."),
        ["cardout"] = ("k_cardout", "카드를 제거해 주세요."),
        ["done"] = ("k_receipt", "영수증을 받아 가세요."),
    };
    static readonly Dictionary<string, string> Back = new Dictionary<string, string>
    {
        ["place"] = "idle", ["menu"] = "place", ["cart"] = "menu", ["pay"] = "cart", ["card"] = "pay",
    };

    readonly KioskState K = new KioskState();
    KioskScreens scr;
    KioskPresenter view;
    PayPoint pay;
    KioskHardware hw;
    bool paid, pulled, canTear;
    float progress;


    public override string FirstScreen => "idle";
    public override bool CanGiveUp => false;
    public override bool Timed => !paid && K.screen != "idle";
    public override bool ShowMeaning => false;   // 1회차는 쉽다. 돋보기도 뜻 풀이도 없다
    public override string[] CustomerScreens => new[] { "idle", "place", "menu" };

    public override void ShowCustomer(string id)
    {
        K.cart.Clear();
        K.toast = null;
        K.screen = id;
        Draw();
    }

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
        hw = Ctl.GetComponent<KioskHardware>();
        if (hw) hw.Clear();    // 어르신이 나간 뒤 종이는 다시 틈을 가린다
        pay = Ctl.Pay;
        if (pay)
        {
            pay.DeferOk = true;
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
        Ctl.SetDown(id == "card" || id == "paying" || id == "cardout" || id == "done");
        HandRig.I.Equip(id == "card" ? ItemId.Card : ItemId.None);
        if (Voice.TryGetValue(id, out var v)) Ctl.Say("kiosk", v.text, v.vo);
    }

    void Draw()
    {
        view.Redraw();
        var s = scr.Current;
        if (!s) return;
        if (K.screen == "menu") MenuTags(s);
        else if (K.screen == "cart" && K.cart.Count > 0 && s.cells.Length > 0)
        {
            var c = s.cells[0];
            c.Text("name", KioskPick.SetName);
            c.Text("mean", "");
        }
        else if (K.screen == "paying") s.Fill("bar", progress);
        else if (K.screen == "done") s.Text("number", GameState.I.Order.number.ToString());
    }

    // NEW는 뽑힌 신메뉴 하나에만 붙는다. 첫 탭 첫 칸은 불고기 버거 세트 자리다
    void MenuTags(KioskScreen s)
    {
        var list = KioskData.Menu[K.tab];
        for (int i = 0; i < s.cells.Length && i < list.Length; i++)
        {
            var c = s.cells[i];
            var it = list[i];
            if (it.id == KioskPick.Id)
            {
                c.Bind("item_set");
                c.Text("name", KioskPick.SetName);
                c.Text("price", Won(KioskPick.SetPrice));
                c.Text("desc", "신메뉴");
                c.Text("tag", "NEW");
                c.Show("tag_box", true);
            }
            else if (it.tag == "NEW") c.Show("tag_box", false);
            c.Text("mean", "");
        }
        if (K.tab != Tabs[0] || s.cells.Length == 0) return;
        var first = s.cells[0];
        var bulgogi = ById("bulgogi");
        first.Bind("item_bulgogi");
        first.Text("name", "불고기 버거 세트");
        first.Text("price", Won(bulgogi.price + Combo("combo").add));
        first.Text("desc", bulgogi.desc);
        first.Text("kcal", $"{bulgogi.kcal}kcal");
        first.Show("tag_box", false);
        view.Put(first, Picture("bulgogi"));
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
                GameState.I.Order.item = KioskPick.SetName;
                K.cart.Clear();
                K.cart.Add(new CartLine { item = KioskPick.Id, price = KioskPick.SetPrice });
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
            GameState.I.Stats.wrong++; Ctl.Sfx("kiosk_error", 0.5f);
            Toast("품절");
        }
        else Ctl.Sfx("kiosk_tap", 0.35f, 0.7f);
    }

    public override bool Hit(Collider col)
    {
        if (col.GetComponentInParent<PosterFlap>())
        {
            if (hw) hw.OpenCover();
            Ctl.Sfx("paper_rustle", 0.8f);
            return true;
        }
        var spot = col.GetComponentInParent<KioskSpot>();
        if (spot && spot.id == "paper")
        {
            TakeReceipt();
            return true;
        }
        if (col.GetComponentInParent<PayPoint>())
        {
            if (K.screen != "cardout") return false;
            pulled = true;
            return true;
        }
        var slot = col.GetComponentInParent<CardSlot>();
        if (slot && K.screen == "card")
        {
            K.cardMsg = slot.id == "receipt" ? "인식할 수 없는 매체입니다" : "카드를 인식할 수 없습니다";
            if (hw) hw.CardAt(slot.id, Ctl.Out, KioskCard.Move.Bounce);
            Ctl.Sfx("card_slide_wrong", 0.9f);
            Draw();
            return true;
        }
        if (spot && spot.id == "call")
        {
            Ctl.Sfx("kiosk_tap", 0.7f, 0.8f);
            Ctl.Sfx("fryer_beep", 0.6f);
            Toast("직원을 호출했습니다", 2.4f);
            return true;
        }
        if (Ctl.IsScreen(col)) return false;
        Ctl.Sfx("kiosk_tap", 0.35f, 0.7f);
        return true;
    }

    // 처음 화면으로. 장바구니를 비운다
    public override void OnTimeout()
    {
        Ctl.Say("kiosk", "처음 화면으로 돌아갑니다.", "k_home");
        Ctl.Sfx("kiosk_error", 0.3f);
        K.cart.Clear();
        K.place = null; K.toast = null; K.cardMsg = null; K.tab = Tabs[0];
        Go("idle");
    }

    void OnEmpty() => Toast(K.screen == "card" ? $"{ItemKeys.Of(ItemId.Card)} 카드" : "카드 전용");

    void OnPaid()
    {
        if (paid) return;
        if (K.screen != "card")
        {
            GameState.I.Stats.wrong++; Ctl.Sfx("kiosk_error", 0.5f);
            Toast("메뉴");
            return;
        }
        paid = true;
        StartCoroutine(Finish());
    }

    IEnumerator Finish()
    {
        int number = Bal.I("R1_OrderNumber", 274);
        GameState.I.Order.number = number;
        K.cardMsg = null;
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.In);
        progress = 0f;
        Go("paying");
        int steps = Bal.I("R1_PaySteps", 6);
        for (int i = 1; i <= steps; i++)
        {
            yield return new WaitForSeconds(Bal.G("Kiosk_PayStepSec", 0.5f));
            progress = (float)i / steps;
            Draw();
        }
        Ctl.Sfx("kiosk_ok", 0.8f);
        pulled = false;
        Go("cardout");
        // 뺄 때까지 멈춘다. 재촉만 한다
        float beep = Time.time + Bal.G("Kiosk_CardOutBeepSec", 3f);
        while (!pulled)
        {
            if (Time.time >= beep)
            {
                beep = Time.time + Bal.G("Kiosk_CardOutBeepSec", 3f);
                Ctl.Sfx("kiosk_error", 0.3f);
                Toast("카드 제거");
            }
            yield return null;
        }
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.Out);
        Ctl.Sfx("card_insert", 0.5f, 1.25f);
        yield return new WaitForSeconds(Bal.G("Kiosk_CardOutDelay", 0.5f));
        Go("done");
        float print = Bal.G("Kiosk_ReceiptPrintSec", 3.1f);
        if (hw) hw.Print($"{KioskPick.SetName}  {Won(KioskPick.SetPrice)}", Won(KioskPick.SetPrice), number, print);
        Ctl.Sfx("receipt_print", 0.9f);
        yield return new WaitForSeconds(print);
        if (hw) hw.ReceiptReady();
        canTear = true;
    }

    void TakeReceipt()
    {
        if (!canTear) return;
        canTear = false;
        Ctl.Sfx("paper_tear", 0.9f);
        if (hw) hw.Tear();
        Ctl.Finish();
    }

    /// <summary>어르신이 주문을 끝낸 결제 화면.</summary>
    public void ElderScreen()
    {
        var bulgogi = ById("bulgogi");
        K.cart.Clear();
        K.cart.Add(new CartLine { item = bulgogi.id, price = bulgogi.price + Combo("combo").add });
        K.screen = "pay";
        Draw();
    }

    /// <summary>어르신 결제 화면에서 카드만 꽂고 뺀다. 메뉴와 화면 조작은 하지 않는다.</summary>
    public IEnumerator ProxyPay(Transform slot)
    {
        var player = PlayerController.I;
        hw = Ctl.GetComponent<KioskHardware>();
        float step = Bal.G("R1_ProxyStepSec", 0.35f);
        HandRig.I.Equip(ItemId.Card);
        yield return player.LookAt(slot.position, 0.3f);
        AudioManager.I.Play("card_insert", slot.position, 0.8f);
        HandRig.I.Equip(ItemId.None);
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.In);
        progress = 0f;
        K.screen = "paying";
        Draw();
        for (int i = 1; i <= 3; i++)
        {
            yield return new WaitForSeconds(step);
            progress = i / 3f;
            Draw();
        }
        AudioManager.I.Play("kiosk_ok", slot.position, 0.8f);
        K.screen = "cardout";
        Draw();
        yield return new WaitForSeconds(step);
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.Out);
        AudioManager.I.Play("card_insert", slot.position, 0.5f, 1.25f);
        HandRig.I.Equip(ItemId.Card);
        yield return new WaitForSeconds(step);
        HandRig.I.Equip(ItemId.None);
        int number = Bal.I("R1_ElderNumber", 273);
        GameState.I.Order.number = number;
        K.screen = "done";
        Draw();
        string price = Won(K.cart[0].price);
        float print = Bal.G("R1_ProxyPrintSec", 1.2f);
        if (hw) hw.Print($"불고기 버거 세트  {price}", price, number, print);
        AudioManager.I.Play("receipt_print", slot.position, 0.9f);
        yield return new WaitForSeconds(print);
        AudioManager.I.Play("paper_tear", slot.position, 0.9f);
        if (hw) hw.Tear();
        K.cart.Clear();
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
