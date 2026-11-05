// 1-0~1-3a 골목과 정류장. 현관에서 나와 정류장까지 걷기, 안내, 친절한 행인, 112번 버스, 쉬운 마싱, 버스카드 찍기, 암전 컷으로 버거집 앞까지.
// 배치: stopZone = StopZone (들어오면 안내와 버스가 시작된다)
// 배치: passer = Student (StreetNpc), askPasser = Student 의 AskUse (label 말 걸기)
// 배치: bus = Bus2 (BusMover, 번호 판 112), busStart, busStop = 기존 앵커
// 배치: boardUse = BoardUse (label 버스 타기), stepBottom, stepTop = 버스 앞문 계단 앵커
// 배치: busInside = Anchor_BusInside, terminal = PH_BusTerminal 의 PayPoint, terminalLook = 단말기 안내문 높이
// Interactable.onUse, PayPoint 이벤트는 코드에서 구독한다.
using System.Collections;
using UnityEngine;

public class R1StopDirector : MonoBehaviour
{
    [SerializeField] Collider stopZone;
    [SerializeField] StreetNpc passer;
    [SerializeField] Interactable askPasser;
    [SerializeField] BusMover bus;
    [SerializeField] Transform busStart;
    [SerializeField] Transform busStop;
    [SerializeField] Interactable boardUse;
    [SerializeField] Transform stepBottom;
    [SerializeField] Transform stepTop;
    [SerializeField] Transform busInside;
    [SerializeField] Transform terminalLook;
    [SerializeField] PayPoint terminal;

    bool asking, boarding, paid;

    static PlayerController Player => PlayerController.I;

    void Awake()
    {
        boardUse.active = false;
        bus.gameObject.SetActive(false);
    }

    void OnEnable()
    {
        askPasser.onUse.AddListener(OnAsk);
        boardUse.onUse.AddListener(OnBoard);
        terminal.Approved += OnPaid;
        terminal.Empty += OnEmpty;
    }

    void OnDisable()
    {
        askPasser.onUse.RemoveListener(OnAsk);
        boardUse.onUse.RemoveListener(OnBoard);
        terminal.Approved -= OnPaid;
        terminal.Empty -= OnEmpty;
    }

    void OnDestroy() => TrafficMover.BusBusy = false;

    IEnumerator Start()
    {
        AudioManager.I.Ambience(("amb_city_morning", 0.62f));
        AudioManager.I.Play("door_close_metal", null, 0.6f);
        yield return Round.Open();
        Note.Peek();
        while (!stopZone.bounds.Contains(Player.transform.position)) yield return null;
        yield return Hud.I.Say(null, "112번 버스를 타세요.", "bus_take");
        yield return new WaitForSeconds(Bal.G("R1_BusArriveSec", 6f));
        yield return Arrive();
        boardUse.active = true;
    }

    IEnumerator Arrive()
    {
        Vector3 stop = busStop.position;
        TrafficMover.BusBusy = true;
        bus.gameObject.SetActive(true);
        AudioManager.I.Play("bus_arrive", stop + new Vector3(-30f, 1f, 0f), 1f);
        yield return bus.Drive(busStart.position, stop, Bal.G("R1_BusDriveSec", 7f), Bal.G("Bus_ArriveEase", 2.4f), true);
        AudioManager.I.Ambience(("amb_city_morning", 0.62f), ("bus_idle", 0.32f));
        AudioManager.I.Play("bus_door", stop + new Vector3(4f, 1f, 0f), 0.9f);
        bus.Doors(true);
    }

    void OnAsk()
    {
        if (!asking) StartCoroutine(Ask());
    }

    IEnumerator Ask()
    {
        asking = true;
        passer.Face(Player.transform.position);
        passer.Nod();
        yield return Hud.I.Say(null, "112번 타시면 돼요. 곧 와요.", "pass_3", -1f, passer.HeadPos);
        asking = false;
    }

    void OnBoard()
    {
        if (boarding) return;
        boarding = true;
        boardUse.active = false;
        StartCoroutine(Board());
    }

    IEnumerator Board()
    {
        Player.Freeze(true);
        Hud.I.ClearSubs();
        StartCoroutine(Player.LookAt(stepTop.position + Vector3.up * 1.4f, 0.4f));
        yield return StoreFlow.Race(this, Player.WalkTo(stepBottom.position, Bal.F("MoveSpeed", 2.2f)), 2.5f);
        yield return Mash.Climb(stepBottom, stepTop);
        yield return Hud.I.Fade(1f, 0.2f);
        Vector3 d = terminalLook.position - busInside.position;
        Player.Teleport(busInside.position, Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg);
        Player.HoldStill = true;
        yield return Player.LookAt(terminalLook.position, 0.01f);
        Hud.I.CardName = "버스카드";
        HandRig.I.SetEnabled(true);
        HandRig.I.Equip(ItemId.Card);
        yield return Hud.I.Fade(0f, 0.25f);
        Player.Freeze(false);
    }

    void OnEmpty() => Hud.I.Say(null, "3 버스카드", null, 1.5f);

    void OnPaid()
    {
        if (paid) return;
        paid = true;
        StartCoroutine(Leave());
    }

    IEnumerator Leave()
    {
        Player.Freeze(true);
        Player.HoldStill = false;
        HandRig.I.Equip(ItemId.None);
        Hud.I.CardName = "카드";
        yield return new WaitForSeconds(Bal.G("R1_AfterTapSec", 0.7f));
        AudioManager.I.Play("bus_door", null, 0.8f);
        AudioManager.I.Play("bus_leave", null, 0.9f);   // N13
        yield return Hud.I.Fade(1f, 0.35f);             // 1-3a 짧은 암전 컷
        yield return new WaitForSeconds(Bal.G("R1_RideSec", 1.6f));
        AudioManager.I.Play("bus_door", null, 0.8f);
        TrafficMover.BusBusy = false;
        GameState.I.CompleteChapter();
    }
}
