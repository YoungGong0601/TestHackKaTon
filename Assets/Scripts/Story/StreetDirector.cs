// 골목과 정류장 진행: 정류장까지 걷기, 전광판, 행인 2명, 첫 버스, 돋보기 판독, 112번 승차. 버스 안은 BusDirector가 잇는다.
// 좌표는 HTML판 street.js의 z에 -1을 곱한 값이다.
// 배치: stopZone = StopZone (BoxCollider isTrigger, x 23 이상 z 30 이상을 덮음, 정류장 도착 판정)
// 배치: bisZone = BisZone (BoxCollider isTrigger, x 31 이상 z 30 이상을 덮음, 전광판을 지나친 판정)
// 배치: bisLook = PH_BIS 의 BisLook (위치 28.6,2.72,33.6)
// 배치: bisFaces = PH_BIS 의 BisFaceA, BisFaceB (Readable 양면, 위치 x 28.525 와 28.675, area 연결)
// 배치: rowsBefore = 각 면 sharp 아래 RowsBefore (첫 버스 전 글자: 2413 은행골 곧 도착 / 112 시장입구 6분 / 7 종합병원 11분)
// 배치: rowsAfter = 각 면 sharp 아래 RowsAfter (첫 버스 뒤 글자: 112 시장입구 곧 도착 / 7 종합병원 9분 / 2413 은행골 14분, 처음엔 꺼 둠)
// 배치: student = Student (PH_NPC, 위치 33.9,0,33.75, 회전 Y -34.4)
// 배치: worker = Worker (PH_NPC, 위치 13,0,33.9, 처음엔 꺼 둠)
// 배치: askStudent = Student 의 AskUse (Interactable, label 말 걸기, radius 2.7, cone 0.72, 머리 높이)
// 배치: askWorker = Worker 의 AskUse (Interactable, label 말 걸기, radius 3.3, cone 0.66, 머리 높이)
// 배치: workerStart = WorkerStart (위치 13,0,33.9)
// 배치: npcPass = NpcPass (위치 39.6,0,34.42)
// 배치: npcExit = NpcExit (위치 78,0,34)
// 배치: bus1 = Bus1 (PH_Bus에 BusMover, 번호 판은 번진 회색 상자)
// 배치: bus2 = Bus2 (PH_Bus에 BusMover, 번호 판 112 시장입구)
// 배치: busStart = BusStart (위치 -90,-0.14,37)
// 배치: busStop = BusStop (위치 31.75,-0.14,37)
// 배치: busEnd = BusEnd (위치 170,-0.14,37)
// 배치: boardUse = BoardUse (Interactable, label 버스 타기, radius 3.3, cone 0.5, 위치 36.2,1.4,35.7)
// 배치: boardWalk = BoardWalk (위치 36.2,0,34.8)
// 배치: boardLook = BoardLook (위치 36.2,1.3,36.6)
// Interactable.onUse, Readable.onRead는 코드에서 구독한다. 씬에서 UnityEvent를 연결하지 않는다.
using System;
using System.Collections;
using UnityEngine;

public class StreetDirector : MonoBehaviour
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
    [SerializeField] Interactable boardUse;
    [SerializeField] Transform boardWalk;
    [SerializeField] Transform boardLook;

    Ask ask = Ask.None;
    bool askedStudent, askedWorker, lensRead, boardable, walked, tracking;

    static string Speaker => GameState.I.Profile.speakerKey;
    static Hud Ui => Hud.I;
    static PlayerController Player => PlayerController.I;
    static AudioManager Sound => AudioManager.I;

    void Awake()
    {
        askStudent.active = false;
        askWorker.active = false;
        boardUse.active = false;
        worker.gameObject.SetActive(false);
        bus1.gameObject.SetActive(false);
        bus2.gameObject.SetActive(false);
    }

    void OnEnable()
    {
        askStudent.onUse.AddListener(AskStudent);
        askWorker.onUse.AddListener(AskWorker);
        boardUse.onUse.AddListener(BoardBus);
        foreach (var face in bisFaces) face.onRead.AddListener(ReadBis);
    }

    void OnDisable()
    {
        askStudent.onUse.RemoveListener(AskStudent);
        askWorker.onUse.RemoveListener(AskWorker);
        boardUse.onUse.RemoveListener(BoardBus);
        foreach (var face in bisFaces) face.onRead.RemoveListener(ReadBis);
    }

    IEnumerator Start()
    {
        Player.SetMode(PlayerController.Mode.Fps);
        Player.Freeze(true);
        yield return Ui.Fade(1f, 0f);
        CityAmbience();
        yield return new WaitForSeconds(0.15f);
        yield return Ui.Fade(0f, Bal.G("Street_FadeInSec", 1.2f));
        Player.Freeze(false);
        yield return Script();
    }

    void Update()
    {
        askStudent.active = ask == Ask.Student;
        askWorker.active = ask == Ask.Worker && worker.gameObject.activeSelf;
        // onRead는 조준 시작 때 한 번만 오므로, 멀리서 조준한 채 다가와도 인정되게 지금 보이는지를 본다.
        foreach (var face in bisFaces)
            if (face.isActiveAndEnabled && face.Seen) ReadBis();
    }

    void ReadBis()
    {
        float dist = Vector3.Distance(Player.transform.position, bisLook.position);
        if (dist < Bal.G("Street_BisReadDist", 9.5f)) lensRead = true;
    }

    IEnumerator Script()
    {
        Ui.Objective("{y:버스 정류장}으로 간다", 8f);
        yield return Until(() => Inside(stopZone));

        Ui.Objective("{y:시장 입구} 가는 버스를 {y:전광판}에서 찾는다", 8f);
        yield return Until(
            () => Looking(bisLook.position, Bal.G("Street_LookBisDist", 8.5f), Bal.G("Street_LookBisDot", 0.9f)) || Inside(bisZone),
            Bal.G("Street_LookBisMaxSec", 16f));
        yield return new WaitForSeconds(0.5f);
        yield return Ui.Say(Speaker, "안 보이네... 몇 번이 온다는 거야.", Speaker + "_toofar");

        Ui.Objective("옆 {y:사람}에게 묻는다", 8f);
        ask = Ask.Student;
        yield return Until(() => askedStudent);
        yield return new WaitForSeconds(Bal.G("Street_AskGapSec", 1.6f));
        ask = Ask.Worker;
        StartCoroutine(WorkerLoop());
        yield return Until(() => askedWorker);
        yield return new WaitForSeconds(0.7f);
        yield return Ui.Say(Speaker, "허허... 다들 바쁘구먼.", Speaker + "_ask3");
        yield return new WaitForSeconds(1.4f);

        yield return Arrive(bus1);
        yield return new WaitForSeconds(Bal.G("Bus_FirstStopSec", 3.2f));
        Coroutine bye = StartCoroutine(Leave(bus1));
        yield return new WaitForSeconds(0.9f);
        yield return Ui.Say(Speaker, "어어, 잠깐만... 아이고, 가버렸네.", Speaker + "_bus_missed");
        yield return bye;
        ShowRowsAfter();

        if (!lensRead && GameState.I.Profile.Has(ItemId.Lens))
        {
            Ui.Objective("{y:돋보기}로 {y:시장 입구} 가는 버스를 찾는다", 10f);
            float last = Time.time;
            while (!lensRead)
            {
                yield return new WaitForSeconds(0.12f);
                if (Time.time - last > Bal.G("Street_ReadNagSec", 16f))
                {
                    last = Time.time;
                    yield return Ui.Say(Speaker, "글씨가 왜 이렇게 작아.", Speaker + "_read1");
                    Ui.Objective("{y:돋보기}로 {y:시장 입구} 가는 버스를 찾는다", 10f);
                }
            }
            yield return new WaitForSeconds(1.2f);
        }

        Ui.Objective("{y:시장 입구} 가는 버스를 기다린다", 8f);
        yield return new WaitForSeconds(Bal.G("Bus_SecondWaitSec", 2.5f));
        yield return Arrive(bus2);
        yield return new WaitForSeconds(Bal.G("Bus_BoardDelaySec", 0.8f));
        boardable = true;
        boardUse.active = true;
        Ui.Objective("{y:시장 입구} 가는 버스를 탄다", 0f);
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
        yield return Ui.Say(Speaker, "저기, 학생. 이거 몇 번 버스가...", Speaker + "_ask1");
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
        yield return Ui.Say(Speaker, "저기요, 말 좀 물읍시다.", Speaker + "_ask2");
        worker.Glance();
        yield return Ui.Say("pass", "저 바빠서요.", "pass_2");
        tracking = false;
        Player.Freeze(false);
        askedWorker = true;
    }

    // 지나가는 사람을 눈으로 좇는다.
    IEnumerator TrackWorker()
    {
        while (tracking) yield return Player.LookAt(worker.HeadPos, 0.15f);
    }

    // 말을 걸어도 멈추지 않고, 놓치면 다시 지나간다.
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
        Sound.Play("bus_door", stop + new Vector3(4f, 1f, 0f), 0.9f);
        yield return new WaitForSeconds(0.9f);
        CityAmbience();
        Sound.Play("bus_leave", stop + Vector3.up, 1f);
        yield return bus.Drive(stop, busEnd.position, Bal.G("Bus_LeaveSec", 13f), Bal.G("Bus_LeaveEase", 2.2f), false);
        bus.gameObject.SetActive(false);
        TrafficMover.BusBusy = false;
    }

    void BoardBus()
    {
        if (!boardable) return;
        boardable = false;
        boardUse.active = false;
        StartCoroutine(BoardRoutine());
    }

    IEnumerator BoardRoutine()
    {
        Player.Freeze(true);
        Ui.ClearSubs();
        HandRig.I.SetEnabled(false);
        StartCoroutine(Player.LookAt(boardLook.position, 0.5f));
        Coroutine walk = StartCoroutine(WalkToDoor());
        yield return Until(() => walked, Bal.G("Bus_BoardMaxSec", 2.6f));
        StopCoroutine(walk);

        yield return Ui.Fade(1f, Bal.G("Bus_RideFadeSec", 0.8f));
        GameState.I.CompleteChapter();
    }

    IEnumerator WalkToDoor()
    {
        yield return Player.WalkTo(boardWalk.position, Bal.F("MoveSpeed", 1.15f));
        walked = true;
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
