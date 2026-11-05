// 4-11~4-21과 E-1: 첫 버스는 눈앞에서 떠나 놓친다. 다음 112번은 자동으로 타서 기사에게 묻고, 현금을 안 받아 내린다. 버스가 떠나고 걸어서 돌아간다.
// R4_Stop 씬 Director 오브젝트에 부착.
// 배치: bisLook = PH_BIS 의 BisLook
// 배치: passer = 행인 (StreetNpc), askPasser = 그 자식 AskUse (label 말 걸기), passerExit = NpcExit
// 배치: buses = BusMover, 첫째는 놓치는 버스, 마지막은 112번. busStart, busStop, busEnd = BusStart, BusStop, BusEnd
// 배치: boardUse = BoardUse (쓰지 않고 꺼 둔다), stepBottom, stepTop = 버스 앞문 계단 아래와 위
// 배치: inside = Anchor_BusInside, driverPos = Driver, noticeLook = PH_BusTerminal 의 Notice_Cashless
// 배치: sun = Directional Light, fill = Fill Light, lamps = 가로등 빛, walker = 뒷모습 인물 (NpcMover), walkTo = 걸어가는 곳
// 이름으로 찾는다: Anchor_WalkStart = 걷기 컷 시작 자리. 없으면 플레이어 자리
using System;
using System.Collections;
using UnityEngine;

public class R4StopDirector : MonoBehaviour
{
    [SerializeField] Transform bisLook;
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
    [SerializeField] Transform driverPos;
    [SerializeField] Transform noticeLook;
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

    bool tracking, toofarSaid;
    int stage;
    Material sky;
    Color ambSky, ambEquator, ambGround;

    static string Me => GameState.I.Profile.speakerKey;
    static Hud Ui => Hud.I;
    static PlayerController Player => PlayerController.I;
    static AudioManager Sound => AudioManager.I;

    void Awake()
    {
        boardUse.active = false;
        foreach (var bus in buses) bus.gameObject.SetActive(false);
        foreach (var lamp in lamps) lamp.SetActive(false);
        if (walker) walker.gameObject.SetActive(false);
        ambSky = RenderSettings.ambientSkyColor;
        ambEquator = RenderSettings.ambientEquatorColor;
        ambGround = RenderSettings.ambientGroundColor;
        if (RenderSettings.skybox) sky = RenderSettings.skybox = new Material(RenderSettings.skybox);
        ApplySky(0f);
    }

    void OnEnable()
    {
        askPasser.onUse.AddListener(OnPasser);
    }

    void OnDisable()
    {
        askPasser.onUse.RemoveListener(OnPasser);
    }

    IEnumerator Start()
    {
        Sound.Ambience(("amb_city_morning", 0.62f));
        yield return Round.Open();
        yield return new WaitForSeconds(Bal.G("R4_Bus1ArriveSec", 8f));   // 임시 T25
        yield return Script();
    }

    void Update()
    {
        // 4-11: 돋보기 없이 전광판을 보면 안 읽힌다
        if (!toofarSaid && !Player.Frozen && !Lensing && Looking(bisLook.position, Bal.G("R4_BisLookDist", 8.5f), Bal.G("R4_BisLookDot", 0.9f)))
        {
            toofarSaid = true;
            Ui.Say(null, "안 보이네... 몇 번이 온다는 거야.", Me + "_toofar");
        }
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
        yield return Player.LookAt(passer.HeadPos, Bal.G("Cine_BlendSec", 1f));
        yield return Ui.Say(null, "저기요, 말 좀 물읍시다.", Me + "_ask2");
        passer.Glance();
        yield return Ui.Say(null, "저 바빠서요.", "pass_2");
        StartCoroutine(PasserLeave());
        tracking = true;
        StartCoroutine(TrackPasser());
        yield return new WaitForSeconds(0.6f);
        yield return Ui.Say(null, "허허... 다들 바쁘구먼.", Me + "_ask3");
        tracking = false;
        Player.Freeze(false);
    }

    // 지나가는 사람을 눈으로 좇는다
    IEnumerator TrackPasser()
    {
        while (tracking && passer.gameObject.activeSelf) yield return Player.LookAt(passer.HeadPos, 0.15f);
    }

    IEnumerator PasserLeave()
    {
        yield return passer.WalkTo(passerExit.position, Bal.G("Street_StudentWalkSpeed", 1.3f));
        passer.gameObject.SetActive(false);
    }

    // ---- 버스 ----


    IEnumerator Script()
    {
        // 놓침은 이 한 번뿐이다. 문이 닫히는 순간 외친다
        BusMover first = buses[0];
        yield return Arrive(first);
        yield return new WaitForSeconds(Bal.G("R4_WrongBusStopSec", 3.2f));
        Coroutine leaving = StartCoroutine(Leave(first));
        Sound.Play("bus_door_close", busStop.position + new Vector3(4f, 1f, 0f), 0.9f);
        Player.Freeze(true);
        yield return Ui.Say(null, "아 이보시게 잠시만요!", Me + "_wait_bus", 2f);
        yield return Watch.Look(Bal.I("R4_WatchHour1", 2));
        yield return Ui.Say(null, "벌써 이렇게 됐구먼.", Me + "_watch", 2f);
        Player.Freeze(false);
        StartCoroutine(Fall(1, Bal.G("R4_NextBusSec", 6f) + Bal.G("R4_DuskExtraSec", 6f)));
        yield return leaving;
        yield return new WaitForSeconds(Bal.G("R4_NextBusSec", 6f));
        yield return Ride(buses[buses.Length - 1]);
    }

    // 4-19~4-21: 입력 없이 오르고, 묻고, 내린다
    IEnumerator Ride(BusMover bus)
    {
        StartCoroutine(Fall(2, Bal.G("R4_DuskExtraSec", 6f)));
        yield return Arrive(bus);
        Player.Freeze(true);
        Ui.ClearSubs();
        if (Vector3.Distance(Player.transform.position, stepBottom.position) > Bal.G("R4_BoardCutDist", 5f))
        {
            yield return Ui.Fade(1f, 0.25f);
            Player.Teleport(stepBottom.position, stepBottom.eulerAngles.y);
            yield return Ui.Fade(0f, 0.25f);
        }
        StartCoroutine(Player.LookAt(stepTop.position + Vector3.up * 1.4f, Bal.G("Cine_BlendSec", 1f)));
        yield return StoreFlow.Race(this, Player.WalkTo(stepBottom.position, Bal.F("MoveSpeed", 1.15f)), 3f);
        yield return Steps.Climb(stepBottom, stepTop);

        Player.Teleport(inside.position, inside.eulerAngles.y);
        Player.Freeze(true);
        yield return Player.LookAt(noticeLook.position, 0.01f);
        // 안내를 보는 동안 시점은 플레이어가 움직인다. 걷기만 막는다
        Player.HoldStill = true;
        Player.Freeze(false);
        yield return Ui.Say(null, "현금은 어디에 넣어요?", Me + "_wherecash", 2f);
        yield return new WaitForSeconds(Bal.G("R4_NoticeLookSec", 2f));
        yield return Ui.Say(null, "현금밖에 없는데요.", Me + "_onlycash", 1.8f);
        yield return Ui.Say(null, "저희는 카드밖에 받지 않습니다.", "drv_cardonly", 2f, driverPos.position);
        Player.Freeze(true);
        Player.HoldStill = false;

        Player.Teleport(stepTop.position, stepTop.eulerAngles.y);
        yield return Steps.Descend(stepTop, stepBottom);
        Sound.Play("bus_door_close", busStop.position + new Vector3(4f, 1f, 0f), 0.9f);
        Coroutine leaving = StartCoroutine(Leave(bus));
        yield return new WaitForSeconds(Bal.G("R4_MissHoldSec", 3f));
        yield return Watch.Look(Bal.I("R4_WatchHour3", 6));
        yield return leaving;
        foreach (var lamp in lamps) lamp.SetActive(true);
        yield return Fall(3, Bal.G("R4_LastDuskSec", 2f));
        yield return WalkHome();
    }

    // 임시 T28: E-1. 인물이 어딘가 걸려 서면 기다리지 않고 넘어간다
    IEnumerator WalkHome()
    {
        HandRig.I.SetEnabled(false);
        GameObject start = GameObject.Find("Anchor_WalkStart");
        walker.Place(start ? start.transform.position : Player.transform.position);
        walker.Show();
        Ui.Say(null, "하... 걸어가야겠구만.", Me + "_walk_home");
        bool done = false;
        StartCoroutine(BackShot(() => done = true));
        Vector3 last = walker.transform.position;
        float still = 0f, limit = Bal.G("R4_EndWalkStuckSec", 1.5f);
        while (!done && still < limit)
        {
            yield return null;
            Vector3 now = walker.transform.position;
            still = (now - last).sqrMagnitude < 1e-7f ? still + Time.deltaTime : 0f;
            last = now;
        }
        if (!done) Player.SetMode(PlayerController.Mode.Fps);
        GameState.I.CompleteChapter();
    }

    IEnumerator BackShot(Action end)
    {
        yield return Cine.BackShot(walker, walkTo.position, Bal.G("R4_EndWalkSec", 8f));
        end();
    }

    IEnumerator Arrive(BusMover bus)
    {
        Vector3 stop = busStop.position;
        TrafficMover.BusBusy = true;
        bus.gameObject.SetActive(true);
        yield return Until(() => TrafficMover.LaneClear(stop.x), Bal.G("Traffic_BusWaitMaxSec", 8f));
        float arrive = Bal.G("Bus_ArriveSec", 11f);
        Sound.Loop("bus_idle", 0.32f, arrive);   // 멀리서 엔진음이 서서히 커진다
        StartCoroutine(BrakeSound(stop, arrive));
        yield return bus.Drive(busStart.position, stop, arrive, Bal.G("Bus_ArriveEase", 2.4f), true);
        Sound.Ambience(("amb_city_morning", 0.62f), ("bus_idle", 0.32f));
        yield return new WaitForSeconds(0.4f);
        Sound.Play("bus_door_open", stop + new Vector3(4f, 1f, 0f), 0.9f);
        bus.Doors(true);
    }

    // bus_arrive 앞부분이 브레이크 소리다. 버스가 서기 5초 전에 틀어야 멈출 때 들린다
    IEnumerator BrakeSound(Vector3 stop, float arrive)
    {
        yield return new WaitForSeconds(Mathf.Max(0f, arrive - 5f));
        Sound.Play("bus_arrive", stop + new Vector3(-6f, 1f, 0f), 1f);
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
        if (sky && sky.HasProperty("_SkyTint")) sky.SetColor("_SkyTint", Color.Lerp(skyTint[a], skyTint[b], t));
        if (sky && sky.HasProperty("_Exposure")) sky.SetFloat("_Exposure", Mathf.Lerp(1.1f, Bal.G("R4_SkyExposureEnd", 0.75f), s / 3f));
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
