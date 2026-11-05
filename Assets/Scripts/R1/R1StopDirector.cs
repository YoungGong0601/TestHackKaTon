// 1-0~1-3a 골목과 정류장. 현관에서 나와 정류장까지 걷기, 안내, 112번 버스, 버스카드 찍기, 빈자리에 앉아 버거집 앞까지(BusRide).
// 배치: stopZone = StopZone (들어오면 안내와 버스가 시작된다)
// 배치: bus = Bus2 (BusMover, 번호 판 112), busStart, busStop = 기존 앵커
// 배치: boardUse = BoardUse (label 버스 타기), stepBottom, stepTop = 버스 앞문 계단 앵커
// 배치: busInside = Anchor_BusInside, terminal = PH_BusTerminal 의 PayPoint, terminalLook = 단말기 안내문 높이
// Interactable.onUse, PayPoint 이벤트는 코드에서 구독한다.
using System.Collections;
using UnityEngine;

public class R1StopDirector : MonoBehaviour
{
    [SerializeField] Collider stopZone;
    [SerializeField] BusMover bus;
    [SerializeField] Transform busStart;
    [SerializeField] Transform busStop;
    [SerializeField] Interactable boardUse;
    [SerializeField] Transform stepBottom;
    [SerializeField] Transform stepTop;
    [SerializeField] Transform busInside;
    [SerializeField] Transform terminalLook;
    [SerializeField] PayPoint terminal;

    bool boarding, paid;

    static PlayerController Player => PlayerController.I;

    void Awake()
    {
        boardUse.active = false;
        bus.gameObject.SetActive(false);
    }

    void OnEnable()
    {
        boardUse.onUse.AddListener(OnBoard);
        terminal.Approved += OnPaid;
        terminal.Empty += OnEmpty;
    }

    void OnDisable()
    {
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
        while (!stopZone.bounds.Contains(Player.transform.position)) yield return null;
        Hud.I.SideNote("{y:112번} 버스를 탄다");
        yield return new WaitForSeconds(Bal.G("R1_BusArriveSec", 6f));
        yield return Arrive();
        boardUse.active = true;
    }

    IEnumerator Arrive()
    {
        Vector3 stop = busStop.position;
        TrafficMover.BusBusy = true;
        bus.gameObject.SetActive(true);
        float arrive = Bal.G("R1_BusDriveSec", 7f);
        AudioManager.I.Loop("bus_idle", 0.32f, arrive);   // 멀리서 엔진음이 서서히 커진다
        StartCoroutine(BrakeSound(stop, arrive));
        yield return bus.Drive(busStart.position, stop, arrive, Bal.G("Bus_ArriveEase", 2.4f), true);
        AudioManager.I.Ambience(("amb_city_morning", 0.62f), ("bus_idle", 0.32f));
        AudioManager.I.Play("bus_door_open", stop + new Vector3(4f, 1f, 0f), 0.9f);
        bus.Doors(true);
    }

    // bus_arrive 앞부분이 브레이크 소리다. 버스가 서기 5초 전에 틀어야 멈출 때 들린다
    IEnumerator BrakeSound(Vector3 stop, float arrive)
    {
        yield return new WaitForSeconds(Mathf.Max(0f, arrive - 5f));
        AudioManager.I.Play("bus_arrive", stop + new Vector3(-6f, 1f, 0f), 1f);
    }

    void OnBoard()
    {
        if (boarding) return;
        boarding = true;
        boardUse.active = false;
        Hud.I.SideNote(null);
        StartCoroutine(Board());
    }

    IEnumerator Board()
    {
        Player.Freeze(true);
        Hud.I.ClearSubs();
        StartCoroutine(Player.LookAt(stepTop.position + Vector3.up * 1.4f, Bal.G("Cine_BlendSec", 1f)));
        yield return StoreFlow.Race(this, Player.WalkTo(stepBottom.position, Bal.F("MoveSpeed", 2.2f)), 2.5f);
        yield return Steps.Climb(stepBottom, stepTop);
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

    void OnEmpty() => Hud.I.Say(null, $"{ItemKeys.Of(ItemId.Card)} 버스카드", null, 1.5f);

    void OnPaid()
    {
        if (paid) return;
        paid = true;
        terminal.GetComponent<Interactable>().active = false;
        StartCoroutine(Leave());
    }

    // 찍은 뒤 안내문을 볼 틈을 두고, 암전 없이 자리로 간다
    IEnumerator Leave()
    {
        HandRig.I.Equip(ItemId.None);
        Hud.I.CardName = "카드";
        yield return new WaitForSeconds(Bal.G("Bus_NoticeLookSec", 2f));
        yield return BusRide.Run(this);
        TrafficMover.BusBusy = false;
        GameState.I.CompleteChapter();
    }
}
