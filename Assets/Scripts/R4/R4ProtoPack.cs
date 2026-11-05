// 4회차 키오스크. 프로토타입 화면 14개와 KioskFlow를 Pack 자리에 끼운다. 지폐는 튕기고 카드가 없어 사지 못한다.
// 부착: PH_Kiosk_R4 의 KioskCanvas (KioskScreens와 같은 오브젝트)
// 배치: cover = IC 틈을 가린 PosterFlap
using System;
using UnityEngine;

public class R4ProtoPack : KioskPack
{
    [SerializeField] PosterFlap cover;

    /// <summary>지폐가 정해진 횟수만큼 튕기고 뒷사람과 말을 마쳤다. 4-10a로 넘어간다.</summary>
    public event Action Bounced;

    public KioskFlow Flow { get; private set; }

    PayPoint pay;
    KioskScreens scr;
    KioskHardware hw;
    bool whatSaid, cashTold, done;
    int cashLine;
    float blinkT;

    static string Me => GameState.I.Profile.speakerKey;

    public override string FirstScreen => "idle";
    public override bool Timed => Flow != null && Flow.Timed && !done;
    public override bool CanGiveUp => Flow != null && !done;
    /// <summary>더 받지 않는다. 대화 중 게이지가 차도 줄로 돌아가지 않는다.</summary>
    public bool Done => done;
    public override string[] CustomerScreens => new[] { "idle", "place", "menu" };
    public override void ShowCustomer(string id) { if (Flow != null) Flow.ShowCustomer(id); }

    void Awake() => scr = GetComponent<KioskScreens>();

    public override void OnEnter()
    {
        done = false;
        cashLine = 0;
        cashTold = false;
        blinkT = 0f;
        hw = Ctl.GetComponent<KioskHardware>();
        if (Flow == null) Flow = new KioskFlow(this, scr);
        Flow.ResetAll();
        pay = Ctl.Pay;
        if (!pay) return;
        pay.ResetCount();
        Unhook();
        pay.DeferOk = true;
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

    public override void OnPress(string id) => Flow.Press(id);

    public override bool Hit(Collider col)
    {
        if (col.GetComponentInParent<PosterFlap>()) { Flow.Spot("cover"); return true; }
        if (col.GetComponentInParent<PayPoint>()) return false;
        var slot = col.GetComponentInParent<CardSlot>();
        if (slot) { Flow.WrongSlot(slot.id); return true; }
        var spot = col.GetComponentInParent<KioskSpot>();
        if (spot) { Flow.Spot(spot.id); return true; }
        if (Ctl.IsScreen(col)) return false;
        Flow.Spot("body");
        return true;
    }

    public override void OnTick(float dt)
    {
        Flow?.Tick();
        if (blinkT <= 0f) return;
        blinkT -= dt;
        var card = scr.Get("card");
        if (card) card.Show("msg_box", blinkT <= 0f || Mathf.Repeat(blinkT, 0.3f) > 0.15f);
    }

    public override void OnTimeout() => Flow.TimedOut();

    void OnCash(int count)
    {
        if (done) return;
        Touched();
        if (Flow.K.screen != "card")
        {
            pay.ResetCount();    // 튕김은 결제 창에서만 센다
            Flow.Toast("카드 전용");
            return;
        }
        Flow.CardOnly();
        blinkT = Bal.G("R4_CardOnlyBlinkSec", 1.2f);
        // 첫 튕김은 1회차 어르신과 같은 머뭇거림, 그 뒤는 두 혼잣말을 번갈아 한다
        if (cashLine == 0) Ctl.Say(Me, "왜 안 되지?", Me + "_why1");
        else if (cashLine % 2 == 1) Ctl.Say(Me, "돈을 어디다 넣으라는 거야.", Me + "_money");
        else Ctl.Say(Me, "왜 기계가 돈을 안먹지? 이상하네", Me + "_no_eat");
        cashLine++;
        if (count < Bal.I("Cash_BounceCount", 3) || cashTold) return;
        cashTold = true;
        Stop();
        StartCoroutine(CashTalk());
    }

    // 뒷사람이 1회차에 플레이어가 고른 말을 그대로 한다
    System.Collections.IEnumerator CashTalk()
    {
        int said = GameState.I.CashLine;
        yield return Ctl.Say("back", KioskData.CashLines[said], KioskData.CashVo("back", said));
        yield return Ctl.Say(Me, "아, 그려?", Me + "_really");
        yield return Ctl.Say(Me, "그러면 방법이 없는겨?", Me + "_nomore");
        yield return Ctl.Say("back", "일단 현금은 안된다네요.", "back_nocash");
        yield return Ctl.Say(Me, "그려? 어쩔 수 없구만...", Me + "_giveup");
        Bounced?.Invoke();
    }

    void OnEmpty()
    {
        if (done) return;
        Touched();
        if (Flow.K.screen == "card") { Flow.CardOnly(); blinkT = Bal.G("R4_CardOnlyBlinkSec", 1.2f); }
        else Flow.Toast("카드 전용");
    }

    /// <summary>선택지로 물러날 때 더 받지 않는다.</summary>
    public void Stop()
    {
        done = true;
        Unhook();
    }

    // ---- KioskFlow가 부르는 것 ----

    public void ScreenChanged(string id)
    {
        Ctl.SetDown(id == "card");
        if (id == "menu" && !whatSaid) { whatSaid = true; StartCoroutine(WhatLine()); }
    }

    // 메뉴 안내 음성이 끝난 뒤 혼잣말
    System.Collections.IEnumerator WhatLine()
    {
        yield return new WaitForSeconds(Bal.G("R4_WhatLineDelaySec", 2.6f));
        if (!done) Ctl.Say(Me, "이건 또 뭐야.", Me + "_why3");
    }

    // 임시 T21: 화면 내용을 왼쪽 위 고정으로 키워 결제 버튼을 화면 밖으로 민다
    public bool Big { get; private set; }

    public void ToggleBig()
    {
        SetBig(!Big);
        Sfx("kiosk_tap", 0.8f);
    }

    public void SetBig(bool on)
    {
        Big = on;
        float k = on ? Bal.G("R4_BigTextScale", 1.6f) : 1f;
        foreach (var s in GetComponentsInChildren<KioskScreen>(true))
        {
            var r = (RectTransform)s.transform;
            r.pivot = new Vector2(0f, 1f);
            r.localScale = new Vector3(k, k, 1f);
        }
    }

    public void Touched() => Ctl.ResetTimer();

    public void HardwareReset()
    {
        if (hw) hw.Clear();
        else if (cover) cover.Close();
    }
    public void OpenCover() { if (cover) cover.Open(); }
    public void AddNunchi(float n) { if (Ctl.Nunchi) Ctl.Nunchi.Add(n); }
    public void Mutter() => Ctl.Mutter();
    public void Sfx(string key, float vol, float rate = 1f) => Ctl.Sfx(key, vol, rate);
    public void Say(string who, string text, string vo = null) => Ctl.Say(who, text, vo);
}
