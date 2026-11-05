// R2_Cafe 진행. 2-1 걷기, 2-2~2-6 키오스크, 2-7 호출, 2-8 받기, 언제든 2-5 알바생.
// 배치: queue = 같은 오브젝트의 QueueManager, kiosk = PH_Kiosk, pack = Pack_R2
// 배치: stand, kioskLook, staffPos, pickupPos = Store 씬 앵커
// 배치: board = PH_PickupBoard, shelf = 픽업 대 위 컵
// 배치: talkStaff, orderKiosk, takeCup = Interactable
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class R2CafeDirector : MonoBehaviour
{
    enum Phase { Intro, Order, Kiosk, Wait, Called, End }

    const int Mine = 275;   // 임시 T14
    const int Prev = 273;

    [SerializeField] QueueManager queue;
    [SerializeField] KioskController kiosk;
    [SerializeField] R2CafePack pack;
    [SerializeField] Transform stand;
    [SerializeField] Transform kioskLook;
    [SerializeField] Transform staffPos;
    [SerializeField] Transform pickupPos;
    [SerializeField] PickupBoard board;
    [SerializeField] GameObject shelf;
    [SerializeField] Interactable talkStaff;
    [SerializeField] Interactable orderKiosk;
    [SerializeField] Interactable takeCup;

    static readonly List<int> NoReady = new List<int>();

    Phase phase;
    bool talking;

    void OnEnable()
    {
        talkStaff.onUse.AddListener(OnTalk);
        orderKiosk.onUse.AddListener(OnOrder);
        takeCup.onUse.AddListener(OnTake);
        kiosk.StaffCalled += OnStaffCalled;
    }

    void OnDisable()
    {
        talkStaff.onUse.RemoveListener(OnTalk);
        orderKiosk.onUse.RemoveListener(OnOrder);
        takeCup.onUse.RemoveListener(OnTake);
        kiosk.StaffCalled -= OnStaffCalled;
    }

    IEnumerator Start()
    {
        SetPhase(Phase.Intro);
        shelf.SetActive(false);
        board.Show(NoReady, Prev);
        GameState.I.Order.number = Mine;
        AudioManager.I.Ambience(("amb_restaurant", 0.3f));
        kiosk.Nunchi.Configure(new NunchiRule());   // N10, C7: 한숨만, 100에서 멈춤
        yield return Round.Open("아메리카노를 주문하세요.");
        SetPhase(Phase.Order);
    }

    void SetPhase(Phase p)
    {
        phase = p;
        orderKiosk.active = p == Phase.Order;
        talkStaff.active = p != Phase.Kiosk && p != Phase.End && p != Phase.Intro && !talking;
        takeCup.active = p == Phase.Wait || p == Phase.Called;
    }

    // ---- 2-5 ----

    void OnTalk() { if (!talking) StartCoroutine(Talk()); }
    void OnStaffCalled() { if (!talking) StartCoroutine(Talk()); }

    IEnumerator Talk()
    {
        talking = true;
        talkStaff.active = false;
        if (phase == Phase.Kiosk) pack.Hint();
        yield return Hud.I.Say(null, "아, 그거 여기 누르시면 돼요.", "staff_cafe", -1f, staffPos.position);
        talking = false;
        SetPhase(phase);
    }

    // ---- 2-2~2-6 ----

    void OnOrder()
    {
        if (phase == Phase.Order) StartCoroutine(RunKiosk());
    }

    IEnumerator RunKiosk()
    {
        var player = PlayerController.I;
        SetPhase(Phase.Kiosk);
        queue.KioskOn = true;
        player.Freeze(true);
        HandRig.I.Equip(ItemId.None);
        yield return StoreFlow.Race(this, player.WalkTo(stand.position, Bal.F("MoveSpeed", 1.9f)), 4f);
        yield return player.LookAt(kioskLook.position, 0.5f);
        yield return kiosk.Enter();
        queue.KioskOn = false;
        player.SetMode(PlayerController.Mode.Fps);
        HandRig.I.SetPointer(false);
        player.Freeze(false);
        Round.Goal(null);
        StartCoroutine(Calls());
    }

    // ---- 2-7 ----

    IEnumerator Calls()
    {
        SetPhase(Phase.Wait);
        queue.ShuffleForward();
        yield return new WaitForSeconds(Bal.G("R2_CallFirstSec", 6f));
        shelf.SetActive(true);
        AudioManager.I.Play("tray_put", pickupPos.position, 0.5f);
        SetPhase(Phase.Called);
        float vol = Bal.G("R2_CallVolume", 0.3f);
        while (phase == Phase.Called)
        {
            board.Show(NoReady, Mine);
            AudioManager.I.Play("pager_call", pickupPos.position, vol);
            Hud.I.Say(null, "...번 고객...", "staff_call5", -1f, pickupPos.position, vol);
            yield return new WaitForSeconds(Bal.G("R2_CallShowSec", 3f));
            if (phase != Phase.Called) break;
            board.Show(NoReady, Prev);
            yield return new WaitForSeconds(Bal.G("R2_CallRepeatSec", 12f));
        }
    }

    // ---- 2-8 ----

    void OnTake()
    {
        if (phase == Phase.Called) { StartCoroutine(Take()); return; }
        AudioManager.I.Play("kiosk_error", pickupPos.position, 0.6f);
        Hud.I.Say(null, "아직입니다", "staff_wait", -1f, pickupPos.position);
    }

    IEnumerator Take()
    {
        SetPhase(Phase.End);
        PlayerController.I.Freeze(true);
        AudioManager.I.Play("bag_rustle", null, 0.8f);
        shelf.SetActive(false);
        yield return new WaitForSeconds(0.8f);
        GameState.I.CompleteChapter();
    }
}
