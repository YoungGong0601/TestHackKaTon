// 4회차 키오스크. 프로토타입 화면 14개와 KioskFlow를 Pack 자리에 끼운다. 지폐는 튕기고 뒷사람이 자기 카드로 결제해 준다.
// 부착: PH_Kiosk_R4 의 KioskCanvas (KioskScreens와 같은 오브젝트)
// 배치: cover = IC 틈을 가린 PosterFlap
using System;
using UnityEngine;

public class R4ProtoPack : KioskPack
{
    [SerializeField] PosterFlap cover;

    /// <summary>지폐가 정해진 횟수만큼 튕겨 뒷사람이 말을 걸기 시작한다.</summary>
    public event Action Helping;
    /// <summary>뒷사람과 말을 마쳤다. 플레이어가 비켜서고 뒷사람이 결제한다.</summary>
    public event Action Bounced;

    public KioskFlow Flow { get; private set; }

    PayPoint pay;
    KioskScreens scr;
    KioskHardware hw;
    bool whatSaid, cashTold, done;
    string receiptLines = "";
    int receiptTotal;

    /// <summary>주문에 사이다가 들어갔다. 쪽지대로 샀는지 본다.</summary>
    public bool Cider { get; private set; }
    /// <summary>영수증 메뉴 줄.</summary>
    public string Lines { get; private set; } = "";
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
        if (count < Bal.I("Cash_BounceCount", 1) || cashTold) return;
        cashTold = true;
        Stop();
        StartCoroutine(CashTalk());
    }

    // 혼잣말이 끝나면 뒷사람이 말을 건다. 결제는 비켜선 뒤 HelpPay가 맡는다
    System.Collections.IEnumerator CashTalk()
    {
        yield return Ctl.Say(Me, "왜 기계가 돈을 안먹지? 이상하네", Me + "_no_eat");
        KeepOrder();
        Helping?.Invoke();
        yield return Ctl.Say("back", "어르신, 이거 돈 안 들어가요.", "a20_cant1");
        yield return Ctl.Say(Me, "아, 그려?", Me + "_really");
        yield return Ctl.Say(Me, "그러면 방법이 없는겨?");
        yield return Ctl.Say("back", "제 카드로 결제해 드릴게요.", "a20_paycard");
        Bounced?.Invoke();
    }

    // 다음 손님이 화면을 쓰면 장바구니가 비니 영수증에 쓸 내용을 남긴다
    void KeepOrder()
    {
        var names = new System.Collections.Generic.List<string>();
        string drink = null;
        foreach (var l in Flow.K.cart)
        {
            names.Add(KioskData.ById(l.item)?.name);
            if (l.side != null) names.Add(KioskData.ById(l.side)?.name);
            if (l.drink != null) { drink = l.drink; names.Add(KioskData.ById(l.drink)?.name); }
            else if (KioskData.ById(l.item)?.kind == "drink") drink = l.item;
        }
        Lines = string.Join("\n", names);
        receiptLines = string.Join("  ", names);
        receiptTotal = Flow.K.Total;
        Cider = drink != null && (drink.Contains("cider") || (KioskData.ById(drink)?.name ?? "").Contains("사이다"));
        GameState.I.Stats.memoOk = Cider;
    }

    /// <summary>뒷사람이 카드를 대고 끝낸다. 카드 소리, 화면 넘김, 영수증만 낸다. 키오스크 모드 밖에서 부른다.</summary>
    public System.Collections.IEnumerator HelpPay()
    {
        int number = Bal.I("R4_OrderNumber", 273);
        GameState.I.Order.number = number;
        var at = Ctl.transform.position + Vector3.up;
        var K = Flow.K;
        K.cardMsg = null;
        K.payProgress = 0f;
        AudioManager.I.Play("card_insert", at, 0.8f);
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.In);
        Flow.Show("paying");
        int steps = Bal.I("R4_HelpPaySteps", 3);
        for (int i = 1; i <= steps; i++)
        {
            yield return new WaitForSeconds(Bal.G("R4_HelpPayStepSec", 0.4f));
            K.payProgress = (float)i / steps;
            Flow.Redraw();
        }
        AudioManager.I.Play("kiosk_ok", at, 0.8f);
        Flow.Show("cardout");
        yield return new WaitForSeconds(Bal.G("R4_HelpPayStepSec", 0.4f));
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.Out);
        AudioManager.I.Play("card_insert", at, 0.5f, 1.25f);
        yield return new WaitForSeconds(Bal.G("R4_HelpPayStepSec", 0.4f));
        Flow.Show("done");
        float print = Bal.G("Kiosk_ReceiptPrintSec", 3.1f);
        string sum = KioskData.Won(receiptTotal);
        if (hw) hw.Print($"{receiptLines}  {sum}", sum, number, print);
        AudioManager.I.Play("receipt_print", at, 0.9f);
        yield return new WaitForSeconds(print);
    }

    /// <summary>나온 영수증을 뜯는다.</summary>
    public void TearReceipt()
    {
        AudioManager.I.Play("paper_tear", Ctl.transform.position + Vector3.up, 0.9f);
        if (hw) hw.Tear();
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
        if (!Ctl.Active) return;   // 뒷사람이 결제하는 동안
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
