// 80대 가는 길. 프로토타입 StreetDirector, BusDirector 진행: 골목을 걸어 정류장으로, 전광판이 안 보임, 행인 2명, 첫 버스를 눈앞에서 놓침, 돋보기로 112 확인, 다음 112번 자동 승차, 버스 안 뒤 가게 앞으로.
// R4_Stop 씬 Director 오브젝트에 부착.
// 배치: stopZone = StopZone, bisZone = BisZone, bisLook = PH_BIS 의 BisLook, bisFaces = BisFaceA, BisFaceB
// 배치: rowsBefore, rowsAfter = 각 면 Sharp 아래 RowsBefore, RowsAfter
// 배치: student, worker = Student, Worker (StreetNpc), askStudent, askWorker = 각 AskUse
// 배치: workerStart, npcPass, npcExit = WorkerStart, NpcPass, NpcExit
// 배치: bus1, bus2 = Bus1(2413), Bus2(112), busStart, busStop, busEnd = BusStart, BusStop, BusEnd
// 배치: stepBottom, stepTop = 버스 앞문 계단 아래와 위, inside = Anchor_BusInside
using System;
using System.Collections;
using UnityEngine;

public class R4StopDirector : MonoBehaviour
{
    enum Ask { None, Student, Worker }

    [SerializeField] Collider stopZone;
    [SerializeField] Collider bisZone;
    [SerializeField] Transform bisLook;
    [SerializeField] Readable[] bisFaces;
    [SerializeField] GameObject[] rowsBefore;
    [SerializeField] GameObject[] rowsAfter;
    [SerializeField] StreetNpc student;
    [SerializeField] StreetNpc worker;
    [SerializeField] Interactable askStudent;
    [SerializeField] Interactable askWorker;
    [SerializeField] Transform workerStart;
    [SerializeField] Transform npcPass;
    [SerializeField] Transform npcExit;
    [SerializeField] BusMover bus1;
    [SerializeField] BusMover bus2;
    [SerializeField] Transform busStart;
    [SerializeField] Transform busStop;
    [SerializeField] Transform busEnd;
    [SerializeField] Transform stepBottom;
    [SerializeField] Transform stepTop;
    [SerializeField] Transform inside;

    Ask ask = Ask.None;
    bool askedStudent, askedWorker, lensRead, wantLens, tracking;

    static string Me => GameState.I.Profile.speakerKey;
    static Hud Ui => Hud.I;
    static PlayerController Player => PlayerController.I;
    static AudioManager Sound => AudioManager.I;

    void Awake()
    {
        askStudent.active = false;
        askWorker.active = false;
        worker.gameObject.SetActive(false);
        bus1.gameObject.SetActive(false);
        bus2.gameObject.SetActive(false);
    }

    void OnEnable()
    {
        askStudent.onUse.AddListener(AskStudent);
        askWorker.onUse.AddListener(AskWorker);
    }

    void OnDisable()
    {
        askStudent.onUse.RemoveListener(AskStudent);
        askWorker.onUse.RemoveListener(AskWorker);
    }

    void OnDestroy()
    {
        TrafficMover.BusBusy = false;
        if (Player) Player.HoldStill = false;
        if (Hud.I) Hud.I.SideNote(null);
    }

    IEnumerator Start()
    {
        CityAmbience();
        Sound.Play("door_close_metal", null, 0.6f);
        yield return Round.Open();
        yield return Script();
    }

    void Update()
    {
        askStudent.active = ask == Ask.Student;
        askWorker.active = ask == Ask.Worker && worker.gameObject.activeSelf;
        // onRead는 조준 시작 때 한 번만 오므로, 멀리서 조준한 채 다가와도 인정되게 지금 보이는지를 본다
        foreach (var face in bisFaces)
            if (face.isActiveAndEnabled && face.Seen
                && Vector3.Distance(Player.transform.position, bisLook.position) < Bal.G("Street_BisReadDist", 9.5f)) lensRead = true;
        if (wantLens && !lensRead && HandRig.I.Held != ItemId.Lens) Ui.Prompt($"<b>{ItemKeys.Of(ItemId.Lens)}</b> 돋보기");
    }

    IEnumerator Script()
    {
        yield return new WaitForSeconds(Bal.G("R4_GrandsonWalkDelaySec", 3f));
        yield return Ui.Say(Me, "우리 손주 좋아하겠구먼.", Me + "_grandson_walk");
        yield return Until(() => Inside(stopZone));
        Hud.I.SideNote("{y:시장 입구} 가는 버스를 {y:전광판}에서 찾는다");
        yield return Ui.Say(Me, "시장 입구 가는 버스가 몇 번이더라...", Me + "_whichbus");

        yield return Until(
            () => Looking(bisLook.position, Bal.G("Street_LookBisDist", 8.5f), Bal.G("Street_LookBisDot", 0.9f)) || Inside(bisZone),
            Bal.G("Street_LookBisMaxSec", 12f));
        yield return new WaitForSeconds(0.5f);
        yield return Ui.Say(Me, "안 보이네... 몇 번이 온다는 거야.", Me + "_toofar");

        ask = Ask.Student;
        yield return Until(() => askedStudent);
        yield return new WaitForSeconds(Bal.G("Street_AskGapSec", 1.6f));
        ask = Ask.Worker;
        StartCoroutine(WorkerLoop());
        yield return Until(() => askedWorker);
        yield return new WaitForSeconds(0.7f);
        yield return Ui.Say(Me, "허허... 다들 바쁘구먼.", Me + "_ask3");
        yield return new WaitForSeconds(Bal.G("Street_AfterAskSec", 0.8f));

        yield return Arrive(bus1);
        yield return new WaitForSeconds(Bal.G("Bus_FirstStopSec", 3.2f));
        Coroutine bye = StartCoroutine(Leave(bus1));
        yield return new WaitForSeconds(0.5f);
        yield return Ui.Say(Me, "아 이보시게 잠시만요!", Me + "_wait_bus", 2f);
        ShowRowsAfter();

        // 버스가 떠나는 동안 전광판을 읽는다
        lensRead = false;
        wantLens = true;
        float last = Time.time;
        while (!lensRead)
        {
            yield return new WaitForSeconds(0.12f);
            if (Time.time - last > Bal.G("Street_ReadNagSec", 16f))
            {
                last = Time.time;
                yield return Ui.Say(Me, "글씨가 왜 이렇게 작아.", Me + "_read1");
            }
        }
        Hud.I.SideNote(null);
        wantLens = false;
        yield return bye;
        yield return new WaitForSeconds(Bal.G("Bus_SecondWaitSec", 1f));
        yield return Arrive(bus2);
        yield return new WaitForSeconds(Bal.G("Bus_BoardDelaySec", 0.8f));
        yield return Board();
    }

    // ---- 행인 ----

    void AskStudent()
    {
        if (ask != Ask.Student) return;
        ask = Ask.None;
        StartCoroutine(AskStudentRoutine());
    }

    IEnumerator AskStudentRoutine()
    {
        Player.Freeze(true);
        yield return Player.LookAt(student.HeadPos, 0.45f);
        yield return Ui.Say(Me, "저기, 학생. 이거 몇 번 버스가...", Me + "_ask1");
        student.Nod();
        student.Face(Player.transform.position);
        yield return new WaitForSeconds(0.45f);
        StartCoroutine(StudentLeave());
        yield return Ui.Say("pass", "아, 저도 잘 모르겠어요.", "pass_1");
        Player.Freeze(false);
        askedStudent = true;
    }

    IEnumerator StudentLeave()
    {
        float speed = Bal.G("Street_StudentWalkSpeed", 1.3f);
        yield return student.WalkTo(npcPass.position, speed);
        yield return student.WalkTo(npcExit.position, speed);
        student.gameObject.SetActive(false);
    }

    void AskWorker()
    {
        if (ask != Ask.Worker) return;
        ask = Ask.None;
        StartCoroutine(AskWorkerRoutine());
    }

    IEnumerator AskWorkerRoutine()
    {
        Player.Freeze(true);
        tracking = true;
        StartCoroutine(TrackWorker());
        yield return Ui.Say(Me, "저기요, 말 좀 물읍시다.", Me + "_ask2");
        worker.Glance();
        yield return Ui.Say("pass", "저 바빠서요.", "pass_2");
        tracking = false;
        Player.Freeze(false);
        askedWorker = true;
    }

    // 지나가는 사람을 눈으로 좇는다
    IEnumerator TrackWorker()
    {
        while (tracking && worker.gameObject.activeSelf) yield return Player.LookAt(worker.HeadPos, 0.15f);
    }

    // 말을 걸어도 멈추지 않고, 놓치면 다시 지나간다
    IEnumerator WorkerLoop()
    {
        while (!askedWorker)
        {
            float speed = Bal.G("Street_WorkerWalkSpeed", 1.28f);
            worker.transform.position = workerStart.position;
            worker.gameObject.SetActive(true);
            yield return worker.WalkTo(npcPass.position, speed);
            yield return worker.WalkTo(npcExit.position, speed);
            worker.gameObject.SetActive(false);
            if (ask == Ask.Worker) yield return new WaitForSeconds(Bal.G("Street_WorkerRetrySec", 2.5f));
        }
    }

    // ---- 버스 ----

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
        Sound.Play("bus_door_close", stop + new Vector3(4f, 1f, 0f), 0.9f);
        yield return new WaitForSeconds(0.9f);
        CityAmbience();
        Sound.Play("bus_leave", stop + Vector3.up, 1f);
        yield return bus.Drive(stop, busEnd.position, Bal.G("Bus_LeaveSec", 13f), Bal.G("Bus_LeaveEase", 2.2f), false);
        bus.gameObject.SetActive(false);
        TrafficMover.BusBusy = false;
    }

    // 입력 없이 올라타서 자리에 앉아 간다. 요금 단계는 없다
    IEnumerator Board()
    {
        Player.Freeze(true);
        Ui.ClearSubs();
        HandRig.I.Equip(ItemId.None);
        if (Vector3.Distance(Player.transform.position, stepBottom.position) > Bal.G("R4_BoardCutDist", 5f))
        {
            yield return Ui.Fade(1f, 0.25f);
            Player.Teleport(stepBottom.position, stepBottom.eulerAngles.y);
            yield return Ui.Fade(0f, 0.25f);
        }
        StartCoroutine(Player.LookAt(stepTop.position + Vector3.up * 1.4f, Bal.G("Cine_BlendSec", 1f)));
        yield return StoreFlow.Race(this, Player.WalkTo(stepBottom.position, Bal.F("MoveSpeed", 1.15f)), 3f);
        yield return Steps.Climb(stepBottom, stepTop);

        yield return Ui.Fade(1f, Bal.G("Bus_RideFadeSec", 0.8f));
        bus2.gameObject.SetActive(false);
        TrafficMover.BusBusy = false;
        Player.Teleport(inside.position, inside.eulerAngles.y);
        yield return Player.LookAt(Player.EyePos + inside.forward, 0.01f);
        Ui.Fade(0f, Bal.G("Bus_InsideFadeSec", 1f));
        yield return BusRide.Run(this);
        GameState.I.CompleteChapter();
    }

    // ---- 도움 ----

    static void CityAmbience() => Sound.Ambience(("amb_city_morning", 0.62f));

    void ShowRowsAfter()
    {
        foreach (var row in rowsBefore) row.SetActive(false);
        foreach (var row in rowsAfter) row.SetActive(true);
    }

    static bool Inside(Collider zone) => zone.bounds.Contains(Player.transform.position);

    static bool Looking(Vector3 point, float dist, float dot)
    {
        Transform eye = Player.Eye.transform;
        Vector3 d = point - eye.position;
        return d.magnitude < dist && Vector3.Dot(d.normalized, eye.forward) > dot;
    }

    static IEnumerator Until(Func<bool> done, float max = float.PositiveInfinity)
    {
        float t0 = Time.time;
        while (!done() && Time.time - t0 < max) yield return new WaitForSeconds(0.12f);
    }
}
