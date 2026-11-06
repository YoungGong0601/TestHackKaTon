// 4회차 버거집 화면 묶음. 성공 경로가 없다: 결제 창의 투입구는 지폐를 튕길 뿐이다.
// Assets/UI/Kiosk/R4/Pack_R4.prefab 루트에 KioskScreens와 같이 부착.
// 배치: content = 화면들을 담은 내용 루트 (왼쪽 위 피벗, T21 배율이 걸린다)
// 화면 id와 버튼 id
// idle      : start
// menu      : list(세 줄), big(큰 글씨), hero(광고), next, item_0~8 | 키 list(목록 묶음), count, total
// pop_code  : x   (backdrop menu, 팝업 넷 모두)
// pop_app   : x
// pop_point : x, skip
// pay       : 키 total, card_on(깜빡이는 "카드 전용")
using System;
using System.Collections.Generic;
using UnityEngine;

public class R4BurgerPack : KioskPack
{
    static readonly int[] Prices = { 8900, 12400, 10900, 9900, 10400, 7900, 11200, 9400, 7900 };

    [SerializeField] RectTransform content;

    /// <summary>지폐가 정해진 횟수만큼 튕겼다. 4-10a로 넘어간다.</summary>
    public event Action Bounced;

    readonly List<int> cart = new List<int>();
    KioskScreens scr;
    PayPoint pay;
    string now = "idle";
    bool listOpen, big, whatSaid, moneySaid, done;
    float blinkT;

    KioskScreens Scr => scr ? scr : scr = GetComponent<KioskScreens>();
    static string Me => GameState.I.Profile.speakerKey;

    public override string FirstScreen => "idle";
    public override bool Timed => now != "idle" && now != "pay" && !done;     // 임시 T23
    public override bool CanGiveUp => now != "pay" && !done;

    public override void OnEnter()
    {
        done = false;
        moneySaid = false;
        Clear();
        now = "idle";
        Draw();
        pay = Ctl.Pay;
        if (!pay) return;
        pay.ResetCount();
        pay.CashRejected += OnCash;
        pay.Empty += OnEmpty;
    }

    void OnDisable() => Unhook();

    void Unhook()
    {
        if (!pay) return;
        pay.CashRejected -= OnCash;
        pay.Empty -= OnEmpty;
    }

    void Clear()
    {
        cart.Clear();
        listOpen = false;
        SetBig(false);
    }

    void SetBig(bool on)
    {
        big = on;
        float k = on ? Bal.G("R4_BigTextScale", 1.6f) : 1f;   // 임시 T21
        if (content) content.localScale = new Vector3(k, k, 1f);
    }

    void Show(string id)
    {
        now = id;
        Ctl.Go(id);
        Draw();
    }

    void Draw()
    {
        int total = 0;
        foreach (int i in cart) total += Prices[i];
        var menu = Scr.Get("menu");
        if (menu)
        {
            menu.Show("list", listOpen);
            menu.Text("count", cart.Count.ToString());
            menu.Text("total", Won(total));
        }
        var payScreen = Scr.Get("pay");
        if (payScreen) payScreen.Text("total", Won(total));
    }

    static string Won(int n) => n.ToString("N0", System.Globalization.CultureInfo.InvariantCulture) + "원";

    void Home()
    {
        Clear();
        Show("idle");
    }

    public override void OnPress(string id)
    {
        Ctl.ResetTimer();
        switch (id)
        {
            case "start":
                Ctl.Sfx("kiosk_ok", 0.5f);
                Show("menu");
                if (!whatSaid) { whatSaid = true; Ctl.Say(Me, "이건 또 뭐야.", Me + "_why3"); }
                return;
            case "list":
                listOpen = !listOpen;
                Ctl.Sfx("kiosk_popup", 0.6f);
                Draw();
                return;
            case "big":
                SetBig(!big);
                Ctl.Sfx("kiosk_tap", 0.8f);
                return;
            case "hero":
                Ctl.Sfx("kiosk_popup", 0.6f);
                Ctl.Toast("앱에서만 이용 가능합니다");
                return;
            case "next":
                if (cart.Count == 0)
                {
                    Ctl.Sfx("kiosk_error", 0.3f);
                    Ctl.Toast("메뉴를 먼저 선택해 주세요");
                    return;
                }
                Popup("pop_code");
                return;
            case "x":
                Close();
                return;
            case "skip":
                Ctl.Sfx("kiosk_tap", 0.8f);
                Show("pay");
                return;
        }
        if (id.StartsWith("item_"))
        {
            cart.Add(int.Parse(id.Substring(5)));   // 다른 메뉴를 담아도 막지 않는다
            Ctl.Sfx("kiosk_ok", 0.5f);
            Ctl.Toast("장바구니에 담았습니다");
            Draw();
        }
    }

    void Popup(string id)
    {
        Ctl.Sfx("kiosk_popup", 0.8f);
        Show(id);
    }

    // 임시 T22
    void Close()
    {
        switch (now)
        {
            case "pop_code": Popup("pop_app"); return;
            case "pop_app": Popup("pop_point"); return;
            case "pop_point":
                Ctl.Sfx("kiosk_error", 0.3f);
                Ctl.Say("kiosk", "처음 화면으로 돌아갑니다.", "k_home");
                Home();
                return;
        }
    }

    public override void OnTimeout()
    {
        Ctl.Say("kiosk", "시간이 초과되어 처음 화면으로 돌아갑니다.", "k_timeout");
        Ctl.Sfx("kiosk_error", 0.3f);
        Home();
    }

    void OnCash(int count)
    {
        if (done) return;
        blinkT = Bal.G("R4_CardOnlyBlinkSec", 1.2f);
        if (now != "pay")
        {
            pay.ResetCount();    // 튕김은 결제 창에서만 센다
            Ctl.Toast("카드 전용");
            return;
        }
        if (!moneySaid)
        {
            moneySaid = true;
            Ctl.Say(Me, "돈을 어디다 넣으라는 거야.", Me + "_money");
        }
        if (count < Bal.I("Cash_BounceCount", 1)) return;
        done = true;
        Unhook();
        Bounced?.Invoke();
    }

    void OnEmpty()
    {
        if (done) return;
        blinkT = Bal.G("R4_CardOnlyBlinkSec", 1.2f);
        Ctl.Toast("카드 전용");
    }

    /// <summary>선택지로 물러날 때 더 받지 않는다.</summary>
    public void Stop()
    {
        done = true;
        Unhook();
    }

    public override void OnTick(float dt)
    {
        if (blinkT <= 0f) return;
        blinkT -= dt;
        var p = Scr.Get("pay");
        if (p) p.Show("card_on", blinkT > 0f && Mathf.Repeat(blinkT, 0.3f) > 0.15f);
    }
}
