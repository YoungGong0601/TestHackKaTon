// 주문 흐름: 화면 전환, 버튼 처리, 장바구니, 결제, 카드 틈, 영수증. 원본 flow.js.
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using static KioskData;

public sealed class KioskFlow
{
    static readonly Dictionary<string, (string vo, string text)> Voice = new Dictionary<string, (string, string)>
    {
        ["place"] = ("k_place", "드시고 가시나요, 가져가시나요?"),
        ["member"] = ("k_member", "멤버십 적립을 원하시면 휴대폰 번호를 입력해 주세요."),
        ["menu"] = ("k_menu", "원하시는 메뉴를 선택해 주세요."),
        ["option"] = ("k_combo", "콤보로 업그레이드 하시겠습니까?"),
        ["pay"] = ("k_pay", "결제 수단을 선택해 주세요."),
        ["card"] = ("k_card", "카드를 투입구에 삽입해 주세요."),
        ["paying"] = ("k_cardhold", "결제가 완료될 때까지 카드를 빼지 마세요."),
        ["cardout"] = ("k_cardout", "카드를 제거해 주세요."),
        ["done"] = ("k_receipt", "영수증을 받아 가세요."),
    };
    static readonly Dictionary<string, string> Back = new Dictionary<string, string>
    {
        ["option"] = "menu", ["side"] = "option", ["drink"] = "side", ["cart"] = "menu", ["pay"] = "cart", ["card"] = "pay",
    };
    static readonly Dictionary<string, KioskInfo> Infos = new Dictionary<string, KioskInfo>
    {
        ["qr"] = new KioskInfo { title = "QR PAY", qr = true, lines = new[] { "왕관페이 앱에서 QR을 스캔해 주세요" }, mean = "휴대폰 앱이 있어야 함" },
        ["coupon"] = new KioskInfo { title = "쿠폰", lines = new[] { "쿠폰 바코드를 리더기에 읽혀 주세요", "등록된 쿠폰이 없습니다" }, mean = "쿠폰 없으면 안 됨" },
        ["point"] = new KioskInfo { title = "제휴 포인트", lines = new[] { "제휴사 앱 인증이 필요합니다", "조회 가능한 포인트가 없습니다" }, mean = "포인트 없으면 안 됨" },
    };

    public readonly KioskState K = new KioskState();
    readonly KioskController ctl;
    readonly KioskPresenter view;

    public KioskFlow(KioskController ctl, KioskScreens screens)
    {
        this.ctl = ctl;
        view = new KioskPresenter(screens, K);
    }

    static RunStats St => GameState.I.Stats;
    static OrderData Od => GameState.I.Order;
    static float TimerFull => Bal.G("Kiosk_Timer", 90f);
    static float Rand(string a, float fa, string b, float fb) => Random.Range(Bal.G(a, fa), Bal.G(b, fb));

    public void Redraw() => view.Redraw();

    /// <summary>시간 제한이 도는 화면</summary>
    public bool Timed => K.screen != "idle" && K.screen != "paying" && K.screen != "cardout" && K.screen != "done";
    /// <summary>폭발해도 되는 화면</summary>
    public bool Safe => K.screen != "paying" && K.screen != "cardout" && K.screen != "done";

    void Go(string s, bool silent = false)
    {
        K.screen = s; K.info = null;
        if (s != "card") K.cardMsg = null;
        Redraw();
        if (!silent && Voice.TryGetValue(s, out var v)) ctl.Say("kiosk", v.text, v.vo);
        if (s == "menu") K.adAt = Time.time + Rand("Kiosk_AdFirstMin", 7f, "Kiosk_AdFirstMax", 11f);
    }

    void Wrong(float n, string sound = null, float vol = 0.8f)
    {
        St.wrong++;
        ctl.AddNunchi(n);
        if (sound != null) ctl.Sfx(sound, vol);
        if (Random.value < Bal.G("Kiosk_WrongMutterChance", 0.7f)) ctl.Mutter();
    }

    static float WrongTouch => Bal.G("Kiosk_WrongTouch", 4f);
    static float ErrorVol => Bal.G("Kiosk_ErrorVolume", 0.3f);   // 진짜 거부에만 나는 소리

    void Toast(string t, float sec = 2f)
    {
        K.toast = t; K.toastUntil = Time.time + sec;
        Redraw();
    }

    void SyncOrder()
    {
        var o = Od; var cart = K.cart;
        var main = cart.LastOrDefault(l => ById(l.item).kind == "burger") ?? cart.LastOrDefault();
        o.item = main?.item; o.combo = main?.combo; o.side = main?.side; o.drink = main?.drink; o.sizeUp = main != null && main.sizeUp;
        if (o.side == null) o.side = cart.FirstOrDefault(l => ById(l.item).kind == "side")?.item;
        if (o.drink == null) o.drink = cart.FirstOrDefault(l => ById(l.item).kind == "drink")?.item;
        if (o.drink == "cola_full") o.drink = "cola";
    }

    void ClearOrder()
    {
        var o = Od;
        o.place = o.item = o.combo = o.side = o.drink = null;
        o.sizeUp = false; o.paid = false;
    }

    public void ResetAll()
    {
        K.demoNo = null;
        K.run++;
        K.cart.Clear();
        K.draft = null; K.place = null; K.phone = ""; K.memberErr = false; K.memberErrs = 0; K.toast = null; K.ad = false; K.info = null;
        K.cardMsg = null; K.payProgress = 0f; K.timer = TimerFull; K.icTried = false; K.canTear = false; K.cardPulled = false; K.tab = "SIGNATURE";
        ClearOrder();
        ctl.HardwareReset();
        K.screen = "idle";
        Redraw();
    }

    void FinishDraft()
    {
        var d = K.draft;
        var it = ById(d.item);
        var combo = Combo(d.combo);
        int side = SideOpts.FirstOrDefault(s => s.id == d.side).add, drink = DrinkOpts.FirstOrDefault(s => s.id == d.drink).add;
        var line = new CartLine
        {
            item = d.item, combo = d.combo, sizeUp = d.sizeUp,
            price = it.price + combo.add + (d.combo == "single" ? 0 : side + drink) + (d.sizeUp ? Bal.I("Kiosk_SizeUpPrice", 800) : 0),
        };
        if (d.combo != "single") { line.side = d.side; line.drink = d.drink; }
        K.cart.Add(line);
        K.draft = null;
        SyncOrder();
        Go("cart");
    }

    // ---- 버튼 ----

    void Press(string id)
    {
        switch (id)
        {
            case "start": ctl.Sfx("kiosk_ok", 0.5f); Go("place"); return;
            case "dine": case "takeout":
                K.place = id; Od.place = id; ctl.Sfx("kiosk_popup", 0.7f); Go("member"); return;
            case "confirm":
                K.memberErr = true; K.memberErrs++; K.phone = ""; Wrong(WrongTouch, "kiosk_error", ErrorVol); Redraw(); return;
            case "skip": Go("menu"); return;
            case "next":
                if (K.screen == "side") Go("drink", true);
                else { ctl.Sfx("kiosk_popup", 0.7f); Go("upsell", true); }
                return;
            case "up_yes": K.draft.sizeUp = true; ctl.Sfx("kiosk_ok", 0.5f); FinishDraft(); return;
            case "up_no": K.draft.sizeUp = false; FinishDraft(); return;
            case "back": if (Back.TryGetValue(K.screen, out var b)) Go(b, true); return;
            case "add_more": Go("menu", true); return;
            case "cart":
                if (!K.cart.Any()) { Wrong(WrongTouch, "kiosk_error", ErrorVol); Toast("메뉴를 먼저 선택해 주세요"); return; }
                Go("cart", true); return;
            case "checkout":
                if (!K.cart.Any()) { Wrong(WrongTouch, "kiosk_error", ErrorVol); Toast("메뉴를 먼저 선택해 주세요"); return; }
                Go("pay"); return;
            case "info_close": K.info = null; Redraw(); return;
            case "home": St.resets++; ResetAll(); return;
            case "ad_close":
                K.ad = false; K.adAt = Time.time + Rand("Kiosk_AdCloseGapMin", 24f, "Kiosk_AdCloseGapMax", 34f); Redraw(); return;
            case "ad": case "hero": case "promo":
                AdTap(); return;
            case "easy": case "access":
                Wrong(WrongTouch, "kiosk_error", ErrorVol); Toast("서비스 준비 중입니다"); return;
        }
        if (id.StartsWith("lang") || id.StartsWith("filter")) { Wrong(WrongTouch, "kiosk_error", ErrorVol); Toast("서비스 준비 중입니다"); return; }
        if (id.StartsWith("key")) Key(id.Substring(3));
        else if (id.StartsWith("rec")) AdTap();
        else if (id.StartsWith("tab_")) Tab(id.Substring(4));
        else if (id.StartsWith("item_")) Item(ById(id.Substring(5)));
        else if (id.StartsWith("opt_"))
        {
            K.draft.combo = id.Substring(4);
            if (K.draft.combo == "single") FinishDraft(); else Go("side", true);
        }
        else if (id.StartsWith("side_")) { K.draft.side = id.Substring(5); Redraw(); }
        else if (id.StartsWith("drink_")) { K.draft.drink = id.Substring(6); Redraw(); }
        else if (id.StartsWith("del_"))
        {
            K.cart.RemoveAt(int.Parse(id.Substring(4)));
            SyncOrder(); Redraw();
        }
        else if (id.StartsWith("pay_")) Pay(id.Substring(4));
    }

    void Key(string k)
    {
        K.memberErr = false;
        if (k == "DEL") { if (K.phone.Length > 0) K.phone = K.phone.Substring(0, K.phone.Length - 1); }
        else if (k == "CLR") K.phone = "";
        else if (K.phone.Length < 8) K.phone += k;
        Redraw();
    }

    void Tab(string t)
    {
        K.tab = t; K.ad = false;
        Redraw();
        if (t == "CLASSIC" && !K.classicSeen) { K.classicSeen = true; K.adAt = Time.time + Bal.G("Kiosk_AdClassicDelay", 2.2f); }
    }

    void Item(MenuItem it)
    {
        if (it.kind == "burger") { K.draft = new DraftOrder { item = it.id }; Go("option"); return; }
        K.cart.Add(new CartLine { item = it.id, price = it.price });
        SyncOrder();
        ctl.Sfx("kiosk_ok", 0.5f);
        Toast("장바구니에 담았습니다", 1.4f);
    }

    void Pay(string id)
    {
        if (id == "card") { K.cardMsg = null; Go("card"); return; }
        Wrong(WrongTouch, "kiosk_popup");
        K.info = Infos[id];
        Redraw();
    }

    void AdTap()
    {
        Wrong(WrongTouch, "kiosk_popup");
        Toast("앱에서만 이용 가능합니다");
    }

    // ---- 터치 ----

    /// <summary>화면 터치. uv는 쿼드 좌표(왼쪽 아래 0).</summary>
    public bool Touch(Vector2 uv, bool bot = false)
    {
        St.touches++;
        K.timer = TimerFull;
        // 마른 손가락: 가끔 터치가 안 먹는다. 낮고 둔한 소리로 빗나갔음을 알린다
        if (!bot && K.screen != "idle" && GameState.I.Profile.kioskTouchFail && Random.value < Bal.G("Kiosk_TouchFailChance", 0.07f))
        {
            ctl.Sfx("kiosk_tap", 0.3f, 0.6f);
            ctl.Mutter();
            return false;
        }
        ctl.Sfx("kiosk_tap", 0.8f, Random.Range(0.95f, 1.08f));
        var b = ctl.Screens.At(uv);
        if (!b)
        {
            if (K.screen != "idle") Wrong(WrongTouch);
            return false;
        }
        b.Flash();
        Press(b.id);
        return true;
    }

    /// <summary>본체 부위 터치. poster, body, cover, paper, call</summary>
    public bool Spot(string id)
    {
        switch (id)
        {
            case "poster": ctl.Sfx("paper_rustle", 0.35f); return false;
            case "body": ctl.Sfx("kiosk_tap", 0.35f, 0.7f); return false;
            case "cover":
                St.touches++; K.timer = TimerFull;
                ctl.OpenCover();
                ctl.Sfx("paper_rustle", 0.8f);
                return true;
            case "paper": return TakeReceipt();
            case "call":
                St.touches++;
                ctl.Sfx("kiosk_tap", 0.7f, 0.8f); ctl.Sfx("fryer_beep", 0.6f);
                Toast("직원을 호출했습니다", 2.4f);
                return true;
        }
        return Slot(id);
    }

    /// <summary>틈에 카드 넣기</summary>
    public bool Slot(string id, bool bot = false)
    {
        St.touches++;
        if (K.screen == "cardout")
        {
            if (id == "ic") K.cardPulled = true;
            else ctl.Sfx("kiosk_tap", 0.35f, 0.7f);
            return true;
        }
        if (K.screen != "card") { ctl.Sfx("kiosk_tap", 0.35f, 0.7f); return false; }
        K.timer = TimerFull;
        if (HandRig.I.Held != ItemId.Card && GameState.I.Profile.Has(ItemId.Card))
        {
            if (!bot) { ctl.Say(ctl.Speaker, "카드를 어디다 넣으라는 거야.", ctl.Speaker + "_card1"); return false; }
            HandRig.I.Equip(ItemId.Card);
        }
        if (id == "ic")
        {
            if (!ctl.CoverOpened) return false;
            if (!K.icTried)
            {
                K.icTried = true; K.cardMsg = "IC칩 방향을 확인하세요";
                ctl.CardAt("ic", KioskCard.Move.Bounce);
                ctl.Sfx("card_reject", 0.9f); ctl.Sfx("kiosk_error", ErrorVol);
                ctl.Mutter();
                Redraw();
                return false;
            }
            K.cardMsg = null;
            ctl.StartCoroutine(RunPayment());
            return true;
        }
        K.cardMsg = id == "receipt" ? "인식할 수 없는 매체입니다" : "카드를 인식할 수 없습니다";
        ctl.CardAt(id, KioskCard.Move.Bounce);
        ctl.Sfx("card_slide_wrong", 0.9f);
        Wrong(Bal.G("Kiosk_WrongSlot", 6f), "kiosk_error", ErrorVol);
        Redraw();
        return false;
    }

    IEnumerator RunPayment()
    {
        int run = ++K.run;
        HandRig.I.Equip(ItemId.None);
        ctl.CardAt("ic", KioskCard.Move.In);
        ctl.Sfx("card_insert", 0.9f);
        K.payProgress = 0f;
        Go("paying");
        int steps = Bal.I("Kiosk_PaySteps", 8);
        for (int i = 1; i <= steps; i++)
        {
            yield return new WaitForSeconds(Bal.G("Kiosk_PayStepSec", 0.5f));
            if (run != K.run) yield break;
            K.payProgress = (float)i / steps;
            Redraw();
        }
        Od.paid = true;
        ctl.Sfx("kiosk_ok", 0.8f);
        K.cardPulled = false;
        Go("cardout");
        float until = Time.time + Bal.G("Kiosk_CardOutWait", 6f);
        while (!K.cardPulled && Time.time < until) yield return null;
        if (run != K.run) yield break;
        ctl.CardAt("ic", KioskCard.Move.Out);
        ctl.Sfx("card_insert", 0.5f, 1.25f);
        yield return new WaitForSeconds(Bal.G("Kiosk_CardOutDelay", 0.5f));
        if (run != K.run) yield break;
        Go("done");
        float print = Bal.G("Kiosk_ReceiptPrintSec", 3.1f);
        ctl.PrintReceipt(ReceiptLines(), Won(K.Total), Od.number, print);
        ctl.Sfx("receipt_print", 0.9f);
        yield return new WaitForSeconds(print);
        if (run != K.run) yield break;
        ctl.ReceiptReady();
        K.canTear = true;
    }

    string ReceiptLines()
    {
        var rows = new List<string>();
        foreach (var l in K.cart)
        {
            rows.Add($"{ById(l.item).name}  {Won(l.price)}");
            if (l.side != null) rows.Add("  " + ById(l.side).name);
            if (l.drink != null) rows.Add("  " + ById(l.drink).name);
        }
        return string.Join("\n", rows);
    }

    public bool TakeReceipt()
    {
        if (!K.canTear) return false;
        K.canTear = false;
        ctl.Sfx("paper_tear", 0.9f);
        ctl.TearReceipt();
        ctl.Finish();
        return true;
    }

    /// <summary>눈치 폭발 동안 젊은 사람이 빠르게 주문하는 화면</summary>
    public IEnumerator Demo()
    {
        int run = ++K.run;
        K.demoNo = Bal.I("Kiosk_DemoNumber", 273); // 끼어든 사람의 번호. 주문번호 274는 그대로 남긴다
        K.place = "takeout";
        K.cart.Clear();
        K.cart.Add(new CartLine { item = "crown3", combo = "large", side = "fries_l", drink = "cola", price = 14700 });
        K.draft = new DraftOrder { item = "crown3", combo = "combo" };
        foreach (var s in new[] { "place", "menu", "option", "drink", "cart", "pay", "card", "paying", "done" })
        {
            yield return new WaitForSeconds(Bal.G("Kiosk_DemoStepSec", 0.85f));
            if (run != K.run) yield break;
            ctl.Sfx("kiosk_tap", 0.5f, 1.2f);
            K.screen = s; K.ad = false;
            Redraw();
        }
    }

    public void Tick()
    {
        if (K.toast != null && Time.time > K.toastUntil) { K.toast = null; Redraw(); }
        if (K.screen != "menu") return;
        if (!K.ad && Time.time > K.adAt)
        {
            K.ad = true; K.adUntil = Time.time + Bal.G("Kiosk_AdShowSec", 12f);
            ctl.Sfx("kiosk_popup", 0.5f);
            Redraw();
        }
        else if (K.ad && Time.time > K.adUntil)
        {
            K.ad = false; K.adAt = Time.time + Rand("Kiosk_AdGapMin", 20f, "Kiosk_AdGapMax", 30f);
            Redraw();
        }
    }

    public void TimedOut()
    {
        ctl.Say("kiosk", "시간이 초과되어 처음 화면으로 돌아갑니다.", "k_timeout");
        ctl.Sfx("kiosk_error", ErrorVol);
        ctl.Mutter();
        St.resets++;
        ResetAll();
    }
}
