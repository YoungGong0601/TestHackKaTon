// 1-5~1-11 버거집 안. 어르신 장면, 키오스크, 픽업, 회차 전환.
// 배치: queue = QueueManager, kiosk = PH_Kiosk, stand, kioskLook, staffPos, pickupPos, chimePos, fryerPos = 기존 앵커
// 배치: elder = R1ElderScene (같은 오브젝트)
// 배치: board = PH_PickupBoard, shelf = Pickup_Shelf, carried = Carried_Bag(시작할 때 HandRoot로)
// 배치: talkStaff = Interact_Staff, orderKiosk = Interact_Order, takeBag = Interact_Take
// 배치: exitDoor = Interact_Exit (label 나가기, 문 앞)
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class R1StoreDirector : MonoBehaviour
{
    enum Phase { Queue, Order, Kiosk, Pickup, Called, Taken, End }

    [SerializeField] QueueManager queue;
    [SerializeField] KioskController kiosk;
    [SerializeField] R1ElderScene elder;
    [SerializeField] Transform stand;
    [SerializeField] Transform kioskLook;
    [SerializeField] Transform staffPos;
    [SerializeField] Transform pickupPos;
    [SerializeField] Transform chimePos;
    [SerializeField] Transform fryerPos;
    [SerializeField] PickupBoard board;
    [SerializeField] GameObject shelf;
    [SerializeField] Transform carried;
    [SerializeField] Interactable talkStaff;
    [SerializeField] Interactable orderKiosk;
    [SerializeField] Interactable takeBag;
    [SerializeField] Interactable exitDoor;

    Phase phase;
    bool talking, early;
    float staffQuietUntil, nextBeep = 12f, nextNotify = 16f, carryT, carryWant;

    static PlayerController Player => PlayerController.I;
    int Number => Bal.I("R1_OrderNumber", 274);
    string CallLine => Number + "번 고객님, 주문하신 메뉴 나왔습니다.";

    void OnEnable()
    {
        talkStaff.onUse.AddListener(OnTalk);
        orderKiosk.onUse.AddListener(OnOrder);
        takeBag.onUse.AddListener(OnTake);
        exitDoor.onUse.AddListener(OnExit);
        kiosk.ViewChanged += OnView;
        kiosk.StaffCalled += OnTalk;
    }

    void OnDisable()
    {
        talkStaff.onUse.RemoveListener(OnTalk);
        orderKiosk.onUse.RemoveListener(OnOrder);
        takeBag.onUse.RemoveListener(OnTake);
        exitDoor.onUse.RemoveListener(OnExit);
        kiosk.ViewChanged -= OnView;
        kiosk.StaffCalled -= OnTalk;
    }

    void OnDestroy()
    {
        // 손은 씬을 건너가므로 붙인 물건은 같이 치운다
        if (carried) Destroy(carried.gameObject);
    }

    IEnumerator Start()
    {
        shelf.SetActive(false);
        carried.gameObject.SetActive(false);
        carried.SetParent(Player.HandRoot, false);
        ShowBoard(268);
        SetPhase(Phase.Queue);
        AudioManager.I.Ambience(("amb_restaurant", 0.36f), ("amb_kitchen", 0.5f));
        Player.HoldStill = true;
        yield return Round.Open();
        yield return elder.Play();
        Player.Freeze(false);
        SetPhase(Phase.Order);
        yield return new WaitForSeconds(Bal.G("R1_GreetDelaySec", 0.5f));
        Hud.I.Say(null, "어서 오세요!", "staff_hello", -1f, staffPos.position);
    }

    void SetPhase(Phase p)
    {
        phase = p;
        talkStaff.active = p != Phase.Queue && p != Phase.Kiosk && p != Phase.End;
        orderKiosk.active = p == Phase.Order;
        takeBag.active = p == Phase.Pickup || p == Phase.Called;
        exitDoor.active = p == Phase.Taken;
    }

    void ShowBoard(int call)
    {
        var ready = new List<int> { 269, 271, 272 };
        if (call != Number) ready.Add(Number);
        board.Show(ready, call);
    }

    // ---- 1-9 알바생 ----

    void OnView(string v)
    {
        if (v == "staff" && Time.time > staffQuietUntil) OnTalk();
    }

    void OnTalk()
    {
        if (!talking) StartCoroutine(Talk());
    }

    IEnumerator Talk()
    {
        talking = true;
        staffQuietUntil = Time.time + Bal.G("R1_StaffQuietSec", 6f);
        if (phase == Phase.Pickup)
        {
            yield return Hud.I.Say(null, "아직입니다", "staff_wait", -1f, staffPos.position);
        }
        else if (phase == Phase.Called || phase == Phase.Taken)
        {
            yield return Hud.I.Say(null, CallLine, "staff_call2", -1f, staffPos.position);
        }
        else
        {
            var pack = kiosk.GetComponentInChildren<R1ProtoPack>(true);
            if (pack && phase == Phase.Kiosk) pack.Hint();
            yield return Hud.I.Say(null, "여기 누르시면 돼요. 제가 도와드릴게요.", "staff_help", -1f, staffPos.position);
        }
        talking = false;
    }

    // ---- 1-7, 1-8 키오스크 ----

    void OnOrder()
    {
        if (phase == Phase.Order) StartCoroutine(RunKiosk());
    }

    IEnumerator RunKiosk()
    {
        SetPhase(Phase.Kiosk);
        queue.KioskOn = true;
        Player.Freeze(true);
        HandRig.I.Equip(ItemId.None);
        yield return StoreFlow.Race(this, Player.WalkTo(stand.position, Bal.F("MoveSpeed", 2.2f)), 2.5f);
        yield return Player.LookAt(kioskLook.position, Bal.G("Cine_BlendSec", 1f));
        kiosk.Nunchi.Configure(new NunchiRule());
        yield return kiosk.Enter();
        queue.KioskOn = false;
        Player.SetMode(PlayerController.Mode.Fps);
        HandRig.I.SetPointer(false);
        Player.Freeze(false);
        StartCoroutine(Pickup());
    }

    // ---- 1-10 픽업 ----

    IEnumerator Pickup()
    {
        SetPhase(Phase.Pickup);
        CookWalk();
        yield return new WaitForSeconds(Bal.G("R1_PickupWaitSec", 5f));
        ShowBoard(Number);
        shelf.SetActive(true);
        AudioManager.I.Play("tray_put", pickupPos.position, Bal.G("Pickup_TrayVolume", 0.6f));
        SetPhase(Phase.Called);
        while (phase == Phase.Called)
        {
            AudioManager.I.Play("pager_call", pickupPos.position, 0.9f);
            Hud.I.Say(null, CallLine, "staff_call2", -1f, pickupPos.position);
            yield return new WaitForSeconds(Bal.G("Pickup_RecallSec", 13f));
        }
    }

    // 요리사가 받는 곳으로 간다. 씬 필드를 늘리지 않고 이름으로 찾고, 없으면 건너뛴다
    void CookWalk()
    {
        GameObject c = GameObject.Find("NPC_Cook"), a = GameObject.Find("Anchor_CookA"), b = GameObject.Find("Anchor_CookB");
        if (!c || !a || !b || !c.TryGetComponent(out NpcMover cook)) return;
        float speed = Bal.G("Queue_CookSpeed", 1.3f);
        cook.Go(a.transform.position, speed, () => cook.Go(b.transform.position, speed, () => cook.Face(pickupPos.position)));
    }

    void OnTake()
    {
        if (phase == Phase.Pickup)
        {
            if (!early) StartCoroutine(TooEarly());
            return;
        }
        if (phase != Phase.Called) return;
        SetPhase(Phase.Taken);
        Hud.I.ClearSubs();
        AudioManager.I.Play("bag_rustle", null, 0.9f);
        shelf.SetActive(false);
        carried.gameObject.SetActive(true);
        carryWant = 1f;
    }

    IEnumerator TooEarly()
    {
        early = true;
        AudioManager.I.Play("kiosk_error", pickupPos.position, 0.4f);
        yield return Hud.I.Say(null, "아직입니다", "staff_wait", -1f, pickupPos.position);
        early = false;
    }

    // ---- 1-11 나가기 ----

    void OnExit()
    {
        if (phase != Phase.Taken) return;
        SetPhase(Phase.End);
        Player.Freeze(true);
        queue.OpenDoor();
        AudioManager.I.Play("door_glass_open", chimePos.position, 0.7f);
        GameState.I.CompleteChapter();
    }

    void Update()
    {
        float dt = Time.deltaTime;
        nextBeep -= dt;
        if (nextBeep <= 0f)
        {
            nextBeep = Random.Range(Bal.G("Store_FryerBeepMin", 18f), Bal.G("Store_FryerBeepMax", 32f));
            AudioManager.I.Play("fryer_beep", fryerPos.position, 0.8f);
        }
        nextNotify -= dt;
        if (nextNotify <= 0f)
        {
            nextNotify = Random.Range(Bal.G("Store_PhoneNotifyMin", 24f), Bal.G("Store_PhoneNotifyMax", 40f));
            AudioManager.I.Play("phone_notify", staffPos.position, 0.22f);
        }
        carryT = StoreFlow.Damp(carryT, carryWant, 4f, dt);
        carried.localPosition = new Vector3(0.06f, -0.62f + carryT * 0.33f + Mathf.Sin(Time.time * 1.6f) * 0.004f, 0.5f);
        carried.localRotation = Quaternion.Euler(-6.9f, 14.3f, 2.3f);
    }
}
