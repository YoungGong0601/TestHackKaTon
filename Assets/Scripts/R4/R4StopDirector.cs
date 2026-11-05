// 4-11~4-21과 E-1: 버스 3대를 보내는 동안 정류장이 저문다. 세 번째 버스도 현금을 받지 않아 탑승 성공은 없다.
// R4_Stop 씬 Director 오브젝트에 부착.
// 배치: bisLook = PH_BIS 의 BisLook, notice = PH_Notice_Cashless (Readable)
// 배치: passer = 행인 (StreetNpc), askPasser = 그 자식 AskUse (label 말 걸기), passerExit = NpcExit
// 배치: buses = BusMover 3개, busStart, busStop, busEnd = BusStart, BusStop, BusEnd
// 배치: boardUse = BoardUse (label 오르기), stepBottom, stepTop = 버스 앞문 계단 아래와 위
// 배치: inside = Anchor_BusInside, askDriver = Driver 의 AskUse (label 묻기), driverPos = Driver 머리
// 배치: terminalPay = PH_BusTerminal 의 PayPoint, terminalNotice = PH_BusTerminal 안내문 Readable
// 배치: sun = Directional Light, fill = Fill Light, lamps = 가로등 빛, walker = 뒷모습 인물 (NpcMover), walkTo = 걸어가는 곳
using System;
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;

public class R4StopDirector : MonoBehaviour
{
    [SerializeField] Transform bisLook;
    [SerializeField] Readable notice;
    [SerializeField] StreetNpc passer;
    [SerializeField] Interactable askPasser;
    [SerializeField] Transform passerExit;
    [SerializeField] BusMover[] buses;
    [SerializeField] Transform busStart;
    [SerializeField] Transform busStop;
    [SerializeField] Transform busEnd;
    [SerializeField] Interactable boardUse;
    [SerializeField] Transform stepBottom;
    [SerializeField] Transform stepTop;
    [SerializeField] Transform inside;
    [SerializeField] Interactable askDriver;
    [SerializeField] Transform driverPos;
    [SerializeField] PayPoint terminalPay;
    [SerializeField] Readable terminalNotice;
    [SerializeField] Light sun;
    [SerializeField] GameObject[] lamps;
    [SerializeField] NpcMover walker;
    [SerializeField] Transform walkTo;

    [SerializeField] Light fill;

    // 낮, 노을 시작, 더 어두움, 해 질 녘. 임시 값, 씬에서 조정한다
    [SerializeField] Color[] sunColor = { new Color(0.95f, 0.96f, 0.98f), new Color(1f, 0.66f, 0.38f), new Color(0.85f, 0.42f, 0.3f), new Color(0.32f, 0.3f, 0.48f) };
    [SerializeField] float[] sunPower = { 1.3f, 0.95f, 0.55f, 0.16f };
    [SerializeField] float[] sunPitch = { 71f, 22f, 10f, 2f };
    [SerializeField] float[] fillPower = { 0.55f, 0.4f, 0.2f, 0.05f };
    [SerializeField] Color[] ambientMul = { Color.white, new Color(1f, 0.8f, 0.7f), new Color(0.7f, 0.5f, 0.55f), new Color(0.35f, 0.35f, 0.5f) };
    [SerializeField] Color[] skyTint = { new Color(0.8f, 0.8f, 0.8f), new Color(0.85f, 0.52f, 0.36f), new Color(0.45f, 0.25f, 0.3f), new Color(0.09f, 0.09f, 0.18f) };

    bool boardPressed, askPressed, toofarSaid, noticeSaid, asked, noticeRead, driverBusy, muttering;
    int stage;
    Material sky;
    Color ambSky, ambEquator, ambGround;
    Interactable terminalUse;
    TMP_Text[] terminalTexts;

    static string Me => GameState.I.Profile.speakerKey;
    static Hud Ui => Hud.I;
    static PlayerController Player => PlayerController.I;
    static AudioManager Sound => AudioManager.I;

    void Awake()
    {
        boardUse.active = false;
        askDriver.active = false;
        foreach (var bus in buses) bus.gameObject.SetActive(false);
        foreach (var lamp in lamps) lamp.SetActive(false);
        if (walker) walker.gameObject.SetActive(false);
        terminalUse = terminalPay.GetComponent<Interactable>();
        terminalUse.active = false;
        terminalTexts = terminalNotice.sharp ? terminalNotice.sharp.GetComponentsInChildren<TMP_Text>(true) : new TMP_Text[0];
        ambSky = RenderSettings.ambientSkyColor;
        ambEquator = RenderSettings.ambientEquatorColor;
        ambGround = RenderSettings.ambientGroundColor;
        if (RenderSettings.skybox) sky = RenderSettings.skybox = new Material(RenderSettings.skybox);
        ApplySky(0f);
    }

    void OnEnable()
    {
        boardUse.onUse.AddListener(OnBoard);
        askDriver.onUse.AddListener(OnAsk);
        askPasser.onUse.AddListener(OnPasser);
        terminalPay.CashRejected += OnTerminalCash;
        terminalPay.Empty += OnTerminalEmpty;
    }

    void OnDisable()
    {
        boardUse.onUse.RemoveListener(OnBoard);
        askDriver.onUse.RemoveListener(OnAsk);
        askPasser.onUse.RemoveListener(OnPasser);
        terminalPay.CashRejected -= OnTerminalCash;
        terminalPay.Empty -= OnTerminalEmpty;
        if (Wallet.I) Wallet.I.NoteMissed -= OnNoteMissed;
    }

    IEnumerator Start()
    {
        Sound.Ambience(("amb_city_morning", 0.62f));
        yield return Round.Open();
        Wallet.I.NoteMissed += OnNoteMissed;
        yield return new WaitForSeconds(Bal.G("R4_Bus1ArriveSec", 8f));   // 임시 T25
        yield return Script();
    }

    void OnNoteMissed() => Ui.Say(null, "뭐라고 썼더라.", Me + "_note");

    void Update()
    {
        // 4-11: 돋보기 없이 전광판을 보면 안 읽힌다
        if (!toofarSaid && !Player.Frozen && !Lensing && Looking(bisLook.position, Bal.G("R4_BisLookDist", 8.5f), Bal.G("R4_BisLookDot", 0.9f)))
        {
            toofarSaid = true;
            Ui.Say(null, "안 보이네... 몇 번이 온다는 거야.", Me + "_toofar");
        }
        // 4-13: 찾아 읽은 사람만 미리 안다
        if (!noticeSaid && notice && notice.Seen)
        {
            noticeSaid = true;
            Ui.Say(null, "현금 없는 버스 운행 안내", Me + "_notice", 2.4f);
        }
        if (asked && !noticeRead && terminalNotice.Seen) noticeRead = true;
    }

    static bool Lensing => HandRig.I.Held == ItemId.Lens;

    // ---- 행인 ----

    void OnPasser()
    {
        askPasser.active = false;
        StartCoroutine(Passer());
    }

    IEnumerator Passer()
    {
        Player.Freeze(true);
        yield return Player.LookAt(passer.HeadPos, 0.45f);
        yield return Ui.Say(null, "저기요, 말 좀 물읍시다.", Me + "_ask2");
        passer.Glance();
        yield return Ui.Say(null, "저 바빠서요.", "pass_2");
        StartCoroutine(PasserLeave());
        yield return new WaitForSeconds(0.6f);
        yield return Ui.Say(null, "허허... 다들 바쁘구먼.", Me + "_ask3");
        Player.Freeze(false);
    }

    IEnumerator PasserLeave()
    {
        yield return passer.WalkTo(passerExit.position, Bal.G("Street_StudentWalkSpeed", 1.3f));
        passer.gameObject.SetActive(false);
    }

    // ---- 버스 ----

    void OnBoard() => boardPressed = true;
    void OnAsk() => askPressed = true;

    IEnumerator Script()
    {
        for (int i = 0; i < 3; i++)
        {
            BusMover bus = buses[Mathf.Min(i, buses.Length - 1)];
            yield return Arrive(bus);

            // 임시 T26: 타지 않으면 문 연 채 기다린다
            boardPressed = false;
            boardUse.active = true;
            yield return Until(() => boardPressed);
            boardUse.active = false;
            Player.Freeze(true);
            Ui.ClearSubs();
            StartCoroutine(Player.LookAt(stepTop.position + Vector3.up * 1.4f, 0.4f));
            yield return StoreFlow.Race(this, Player.WalkTo(stepBottom.position, Bal.F("MoveSpeed", 0.9f)), 6f);
            yield return Mash.Climb(stepBottom, stepTop);
            if (i == 2) break;   // 4-19: 세 번째는 묻지 않아도 고개가 들리며 단말기가 보인다
            yield return Enter();

            string number = i == 0 ? "117번이요." : "172번이요.";
            yield return Ui.Say(null, number, i == 0 ? "drv_117" : "drv_172", 1.8f, driverPos.position);
            if (i == 0) yield return Ui.Say(null, "아이고, 아니구먼.", Me + "_notthis", 1.8f);
            yield return GetOff(bus);

            Coroutine leaving = StartCoroutine(Leave(bus));
            yield return Watch.Look(Bal.I(i == 0 ? "R4_WatchHour1" : "R4_WatchHour2", i == 0 ? 2 : 4));
            if (i == 0) yield return Ui.Say(null, "벌써 이렇게 됐구먼.", Me + "_watch", 2f);
            Player.Freeze(false);
            StartCoroutine(Fall(i + 1, Bal.G("R4_NextBusSec", 6f) + Bal.G("R4_DuskExtraSec", 6f)));
            yield return leaving;
            yield return new WaitForSeconds(Bal.G("R4_NextBusSec", 6f));
        }
        yield return Third();
    }

    // 묻기 전까지 버스 안에 머문다
    IEnumerator Enter()
    {
        Player.Teleport(inside.position, inside.eulerAngles.y);
        askPressed = false;
        askDriver.active = true;
        Player.Freeze(false);
        yield return Until(() => askPressed);
        askDriver.active = false;
        Player.Freeze(true);
        yield return Player.LookAt(driverPos.position, 0.5f);
    }

    // 임시 T27: 재촉은 문구 없이 소리와 먼저 닫히기 시작하는 문
    IEnumerator GetOff(BusMover bus)
    {
        Sound.Play("tsk", driverPos.position, 0.8f);
        Sound.Play("bus_door", busStop.position + new Vector3(4f, 1f, 0f), 0.9f);
        Player.Teleport(stepTop.position, stepTop.eulerAngles.y);
        yield return Mash.Descend(stepTop, stepBottom);
        bus.Doors(false);
    }

    IEnumerator Third()
    {
        BusMover bus = buses[Mathf.Min(2, buses.Length - 1)];

        // 4-19 입력 없이 고개가 들리며 단말기가 보인다
        Player.Teleport(inside.position, inside.eulerAngles.y);
        Player.Freeze(true);
        yield return Player.LookAt(terminalPay.transform.position, Bal.G("R4_TerminalLookSec", 1.2f));
        yield return Ui.Say(null, "112번이요.", "drv_112", 1.8f, driverPos.position);

        // 4-20 습관처럼 지갑을 열지만 현금뿐이다
        Wallet.I.SetOpen(true);
        yield return new WaitForSeconds(Bal.G("R4_WalletHabitSec", 2f));
        Wallet.I.SetOpen(false);
        Player.Freeze(true);

        // 4-20a
        yield return Ui.Say(null, "현금은 어디에 넣어요?", Me + "_wherecash", 2f);
        asked = true;
        terminalUse.active = true;
        foreach (var x in terminalTexts) x.alpha = 0f;     // 4-21에서 초점이 맞으며 드러난다
        Player.Freeze(false);
        StartCoroutine(Repeat());     // 돋보기를 쓸 때까지 같은 말
        yield return Until(() => noticeRead);
        Player.Freeze(true);
        terminalUse.active = false;
        Ui.ClearSubs();
        yield return Reveal();
        yield return Ui.Say(null, "현금 없는 버스 운행 안내. 이 버스는 현금을 받지 않습니다.", Me + "_notice2", 3f);

        // 4-21a 선택지는 하나뿐이다
        yield return Choice.Ask(new[] { "현금밖에 없는데요" }, _ => { });
        yield return Ui.Say(null, "현금밖에 없는데요.", Me + "_onlycash", 1.8f);
        yield return Ui.Say(null, "저희는 카드밖에 받지 않습니다.", "drv_cardonly", 2f, driverPos.position);

        // 4-21b
        Player.Teleport(stepTop.position, stepTop.eulerAngles.y);
        yield return Mash.Descend(stepTop, stepBottom);
        Sound.Play("bus_door", busStop.position + new Vector3(4f, 1f, 0f), 0.9f);
        Coroutine leaving = StartCoroutine(Leave(bus));
        HandRig.I.Equip(ItemId.Cash);     // 지폐를 쥔 손
        yield return new WaitForSeconds(Bal.G("R4_CashHoldSec", 2f));
        yield return leaving;
        HandRig.I.Equip(ItemId.None);
        yield return Watch.Look(Bal.I("R4_WatchHour3", 6));
        foreach (var lamp in lamps) lamp.SetActive(true);
        yield return Fall(3, Bal.G("R4_LastDuskSec", 2f));

        // 임시 T28: E-1
        HandRig.I.SetEnabled(false);
        walker.Place(Player.transform.position);
        walker.Show();
        yield return Cine.BackShot(walker, walkTo.position, Bal.G("R4_EndWalkSec", 8f));
        GameState.I.CompleteChapter();
    }

    IEnumerator Repeat()
    {
        while (!noticeRead)
        {
            if (!driverBusy) yield return DriverLine();
            float until = Time.time + Bal.G("R4_DriverRepeatSec", 6f);
            while (!noticeRead && Time.time < until) yield return null;
        }
    }

    IEnumerator DriverLine()
    {
        driverBusy = true;
        yield return Ui.Say(null, "거기 써 있잖아요.", "drv_there", 1.8f, driverPos.position);
        driverBusy = false;
    }

    void OnTerminalCash(int count) => OnTerminalEmpty();

    void OnTerminalEmpty()
    {
        if (!asked || noticeRead || driverBusy) return;
        StartCoroutine(DriverLine());
    }

    // 4-21: 초점이 서서히 맞으며 글씨가 드러난다
    IEnumerator Reveal()
    {
        float sec = Bal.G("R4_RevealSec", 1.6f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            foreach (var x in terminalTexts) x.alpha = t;
            yield return null;
        }
        foreach (var x in terminalTexts) x.alpha = 1f;
    }

    IEnumerator Arrive(BusMover bus)
    {
        Vector3 stop = busStop.position;
        TrafficMover.BusBusy = true;
        bus.gameObject.SetActive(true);
        yield return Until(() => TrafficMover.LaneClear(stop.x), Bal.G("Traffic_BusWaitMaxSec", 8f));
        Sound.Play("bus_arrive", stop + new Vector3(-30f, 1f, 0f), 1f);
        yield return bus.Drive(busStart.position, stop, Bal.G("Bus_ArriveSec", 11f), Bal.G("Bus_ArriveEase", 2.4f), true);
        Sound.Ambience(("amb_city_morning", 0.62f), ("bus_idle", 0.32f));
        yield return new WaitForSeconds(0.4f);
        Sound.Play("bus_door", stop + new Vector3(4f, 1f, 0f), 0.9f);
        bus.Doors(true);
    }

    IEnumerator Leave(BusMover bus)
    {
        Vector3 stop = busStop.position;
        bus.Doors(false);
        yield return new WaitForSeconds(0.9f);
        Sound.Ambience(("amb_city_morning", 0.62f));
        Sound.Play("bus_leave", stop + Vector3.up, 1f);
        yield return bus.Drive(stop, busEnd.position, Bal.G("Bus_LeaveSec", 13f), Bal.G("Bus_LeaveEase", 2.2f), false);
        bus.gameObject.SetActive(false);
        TrafficMover.BusBusy = false;
    }

    // ---- 저무는 하늘 ----

    IEnumerator Fall(int to, float sec)
    {
        int from = stage;
        stage = to;
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            ApplySky(Mathf.Lerp(from, to, t));
            yield return null;
        }
        ApplySky(to);
    }

    void ApplySky(float s)
    {
        int a = Mathf.Clamp(Mathf.FloorToInt(s), 0, 2), b = a + 1;
        float t = s - a;
        Color mul = Color.Lerp(ambientMul[a], ambientMul[b], t);
        if (sun)
        {
            sun.color = Color.Lerp(sunColor[a], sunColor[b], t);
            sun.intensity = Mathf.Lerp(sunPower[a], sunPower[b], t);
            Vector3 e = sun.transform.eulerAngles;
            sun.transform.rotation = Quaternion.Euler(Mathf.Lerp(sunPitch[a], sunPitch[b], t), e.y, e.z);
        }
        if (fill) fill.intensity = Mathf.Lerp(fillPower[a], fillPower[b], t);
        RenderSettings.ambientSkyColor = ambSky * mul;
        RenderSettings.ambientEquatorColor = ambEquator * mul;
        RenderSettings.ambientGroundColor = ambGround * mul;
        if (sky && sky.HasProperty("_Tint")) sky.SetColor("_Tint", Color.Lerp(skyTint[a], skyTint[b], t));
    }

    // ---- 도움 ----

    static bool Looking(Vector3 point, float dist, float dot)
    {
        Transform eye = Player.Eye.transform;
        Vector3 d = point - eye.position;
        return d.magnitude < dist && Vector3.Dot(d.normalized, eye.forward) > dot;
    }

    static IEnumerator Until(Func<bool> done)
    {
        while (!done()) yield return null;
    }

    static IEnumerator Until(Func<bool> done, float max)
    {
        float t0 = Time.time;
        while (!done() && Time.time - t0 < max) yield return new WaitForSeconds(0.12f);
    }
}
