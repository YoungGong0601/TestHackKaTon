// 4회차 주문 흐름: 프로토타입 화면 전환, 버튼 처리, 장바구니, 팝업. 지폐는 틈에서 튕기고 결제는 뒷사람 카드로 끝난다(R4ProtoPack.HelpPay).
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
    };
    static readonly Dictionary<string, string> Back = new Dictionary<string, string>
    {
        ["place"] = "idle", ["member"] = "place", ["menu"] = "member", ["option"] = "menu", ["side"] = "option", ["drink"] = "side", ["cart"] = "menu", ["pay"] = "cart", ["card"] = "pay",
    };
    static readonly Dictionary<string, KioskInfo> Infos = new Dictionary<string, KioskInfo>
    {
        ["qr"] = new KioskInfo { title = "QR PAY", qr = true, lines = new[] { "왕관페이 앱에서 QR을 스캔해 주세요" }, mean = "휴대폰 앱이 있어야 함" },
        ["coupon"] = new KioskInfo { title = "쿠폰", lines = new[] { "쿠폰 바코드를 리더기에 읽혀 주세요", "등록된 쿠폰이 없습니다" }, mean = "쿠폰 없으면 안 됨" },
        ["point"] = new KioskInfo { title = "제휴 포인트", lines = new[] { "제휴사 앱 인증이 필요합니다", "조회 가능한 포인트가 없습니다" }, mean = "포인트 없으면 안 됨" },
    };

    // 시트 4-8. 앞 둘은 x로 다음 팝업, 마지막은 x면 처음 화면, 아주 작은 "건너뛰기"면 결제 창(T22)
    static readonly KioskInfo[] Pops =
    {
        new KioskInfo { kind = "code", title = "코드 등록", lines = new string[0], mean = "코드 넣으라는 말", yes = "등록", no = "다음에", terms = "1인 1회 사용" },
        new KioskInfo { kind = "app", title = "앱 가입", lines = new string[0], mean = "앱 가입하라는 말", yes = "가입", no = "다음에", terms = "앱 회원 전용" },
        new KioskInfo { kind = "point", title = "포인트 적립", lines = new string[0], mean = "포인트 쌓으라는 말", skip = true, yes = "적립", terms = "세트 메뉴만 적립" },
    };


    public readonly KioskState K = new KioskState();
    readonly R4ProtoPack ctl;
    readonly KioskPresenter view;
    int pop = -1;

    public KioskFlow(R4ProtoPack ctl, KioskScreens screens)
    {
        this.ctl = ctl;
        view = new KioskPresenter(screens, K);
    }

    static float Rand(string a, float fa, string b, float fb) => Random.Range(Bal.G(a, fa), Bal.G(b, fb));

    public void Redraw() => view.Redraw();

    /// <summary>다음 손님이 쓰는 화면. 플레이어 주문 상태는 다음 차례에 ResetAll이 지운다.</summary>
    public void ShowCustomer(string id)
    {
        K.cart.Clear();
        K.info = null; K.toast = null; K.ad = false; K.cardMsg = null;
        K.screen = id;
        Redraw();
    }

    /// <summary>무입력 시간이 도는 화면.</summary>
    public bool Timed => K.screen != "idle";

    /// <summary>뒷사람이 결제하는 동안 화면만 넘긴다.</summary>
    public void Show(string s) => Go(s, true);

    void Go(string s, bool silent = false)
    {
        K.screen = s; K.info = null; pop = -1;
        if (s != "card") K.cardMsg = null;
        Redraw();
        ctl.ScreenChanged(s);
        if (!silent && Voice.TryGetValue(s, out var v)) ctl.Say("kiosk", v.text, v.vo);
        if (s == "menu") K.adAt = Time.time + Rand("Kiosk_AdFirstMin", 7f, "Kiosk_AdFirstMax", 11f);
    }

    void Wrong(float n, string sound = null, float vol = 0.8f)
    {
        ctl.AddNunchi(n);
        if (sound != null) ctl.Sfx(sound, vol);
        if (Random.value < Bal.G("Kiosk_WrongMutterChance", 0.7f)) ctl.Mutter();
    }

    static float WrongTouch => Bal.G("Kiosk_WrongTouch", 4f);
    static float ErrorVol => Bal.G("Kiosk_ErrorVolume", 0.3f);   // 진짜 거부에만 나는 소리

    public void Toast(string t, float sec = 2f)
    {
        K.toast = t; K.toastUntil = Time.time + sec;
        Redraw();
    }

    public void ResetAll()
    {
        K.run++;
        K.cart.Clear();
        K.draft = null; K.place = null; K.phone = ""; K.memberErr = false; K.memberErrs = 0; K.toast = null; K.ad = false; K.info = null;
        K.cardMsg = null; K.tab = "SIGNATURE"; K.classicSeen = false; pop = -1;
        ctl.HardwareReset();
        ctl.SetBig(false);
        K.screen = "idle";
        Redraw();
        ctl.ScreenChanged("idle");
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
        Go("cart");
    }

    // ---- 버튼 ----

    public void Press(string id)
    {
        switch (id)
        {
            case "start": ctl.Sfx("kiosk_ok", 0.5f); Go("place"); return;
            case "dine": case "takeout":
                K.place = id; ctl.Sfx("kiosk_popup", 0.7f); Go("member"); return;
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
                Popup(0); return;
            case "info_close": CloseInfo(); return;
            case "pop_skip": ctl.Sfx("kiosk_tap", 0.8f); Go("pay"); return;
            case "home": ResetAll(); return;
            case "ad_close":
                K.ad = false; K.adAt = Time.time + Rand("Kiosk_AdCloseGapMin", 24f, "Kiosk_AdCloseGapMax", 34f); Redraw(); return;
            case "ad": case "hero": case "promo":
                AdTap(); return;
            case "easy":
                Wrong(WrongTouch, "kiosk_error", ErrorVol); Toast("서비스 준비 중입니다"); return;
            case "access": ctl.ToggleBig(); return;   // 임시 T21: 4-5a 큰 글씨
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
            Redraw();
        }
        else if (id.StartsWith("pay_")) Pay(id.Substring(4));
    }

    void Popup(int i)
    {
        pop = i;
        K.info = Pops[i];
        ctl.Sfx("kiosk_popup", 0.8f);
        Redraw();
    }

    void CloseInfo()
    {
        if (pop < 0) { K.info = null; Redraw(); return; }
        if (pop + 1 < Pops.Length) { Popup(pop + 1); return; }
        ctl.Sfx("kiosk_error", ErrorVol);
        ctl.Say("kiosk", "처음 화면으로 돌아갑니다.", "k_home");
        ResetAll();
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

    // ---- 본체 ----

    public void Spot(string id)
    {
        switch (id)
        {
            case "cover":
                ctl.Touched();
                ctl.OpenCover();
                ctl.Sfx("paper_rustle", 0.8f);
                return;
            case "call":
                ctl.Touched();
                ctl.Sfx("kiosk_tap", 0.7f, 0.8f); ctl.Sfx("fryer_beep", 0.6f);
                Toast("직원을 호출했습니다", 2.4f);
                return;
            default: ctl.Sfx("kiosk_tap", 0.35f, 0.7f); return;
        }
    }

    /// <summary>IC 틈이 아닌 틈. 튕김 횟수에 넣지 않는다.</summary>
    public void WrongSlot(string id)
    {
        ctl.Touched();
        if (K.screen != "card") { ctl.Sfx("kiosk_tap", 0.35f, 0.7f); return; }
        K.cardMsg = id == "receipt" ? "인식할 수 없는 매체입니다" : "카드를 인식할 수 없습니다";
        ctl.Sfx("card_slide_wrong", 0.9f);
        Wrong(Bal.G("Kiosk_WrongSlot", 6f), "kiosk_error", ErrorVol);
        Redraw();
    }

    public void CardOnly()
    {
        K.cardMsg = "카드 전용";
        Redraw();
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
        ResetAll();
    }
}
