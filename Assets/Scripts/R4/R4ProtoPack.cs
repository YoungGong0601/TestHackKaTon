// 4회차 키오스크. 프로토타입 화면 14개와 KioskFlow를 Pack 자리에 끼운다. 성공 경로가 없다: IC 틈은 지폐를 튕길 뿐이다.
// 부착: PH_Kiosk_R4 의 KioskCanvas (KioskScreens와 같은 오브젝트)
// 배치: cover = IC 틈을 가린 PosterFlap
using System;
using UnityEngine;

public class R4ProtoPack : KioskPack
{
    [SerializeField] PosterFlap cover;

    /// <summary>지폐가 정해진 횟수만큼 튕겼다. 4-10a로 넘어간다.</summary>
    public event Action Bounced;

    public KioskFlow Flow { get; private set; }

    PayPoint pay;
    KioskScreens scr;
    bool moneySaid, whatSaid, done;
    float blinkT;

    static string Me => GameState.I.Profile.speakerKey;

    public override string FirstScreen => "idle";
    public override bool Timed => Flow != null && Flow.Timed && !done;
    public override bool CanGiveUp => Flow != null && Flow.K.screen != "pay" && Flow.K.screen != "card" && !done;

    void Awake() => scr = GetComponent<KioskScreens>();

    public override void OnEnter()
    {
        done = false;
        moneySaid = false;
        blinkT = 0f;
        if (Flow == null) Flow = new KioskFlow(this, scr);
        Flow.ResetAll();
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
        if (!moneySaid)
        {
            moneySaid = true;
            Ctl.Say(Me, "돈을 어디다 넣으라는 거야.", Me + "_money");
        }
        if (count < Bal.I("Cash_BounceCount", 3)) return;
        done = true;
        Unhook();
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
        var hw = Ctl.GetComponent<KioskHardware>();
        if (hw) hw.Clear();
        else if (cover) cover.Close();
    }
    public void OpenCover() { if (cover) cover.Open(); }
    public void AddNunchi(float n) { if (Ctl.Nunchi) Ctl.Nunchi.Add(n); }
    public void Mutter() => Ctl.Mutter();
    public void Sfx(string key, float vol, float rate = 1f) => Ctl.Sfx(key, vol, rate);
    public void Say(string who, string text, string vo = null) => Ctl.Say(who, text, vo);
}
