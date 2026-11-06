// 4회차 가게. 프로토타입 StoreDirector 진행: 안 도와주는 알바생, 키오스크, 게이지가 다 차면 줄 맨 뒤로 갔다가 다시 시도. 지폐가 튕기면 장면 A 주인공인 뒷사람이 자기 카드로 결제해 주고, 호출, 수령, 대사 뒤 결과로 끝난다.
// R4_Store 씬 Director 오브젝트에 부착.
// 배치: kiosk = PH_Kiosk, pack = KioskCanvas (R4ProtoPack), queue = QueueManager
// 배치: stand = Anchor_KioskStand, kioskLook = Anchor_KioskLook, staffPos = Anchor_Staff, exitPos = Anchor_FrontDoor, exitLook = Anchor_ExitLook
// 배치: orderKiosk = Interact_Order, talkStaff = Interact_Staff, brokenKiosk = Interact_Broken, exitDoor = Interact_Exit (늘 꺼 둔다), takeBag = Interact_Take
// 배치: pool = 줄 손님 NPC_Queue1~4, 뒷사람은 QueueManager.regular (NPC_Helper), tray = Tray_Pass (쟁반, 처음 꺼짐), trayFrom, trayTo = 쟁반이 지나는 양 끝
// 배치: pickupPos = Anchor_PickupLook, cook = NPC_Cook, cookA, cookB = Anchor_CookA, Anchor_CookB, board = PH_PickupBoard
// 배치: shelf = Pickup_Shelf, shelfCup = 그 자식 Cup, carried = Carried_Bag, cupLabels = 두 컵의 Label
// 배치: receiptView = Receipt_View (시작할 때 HandRoot로), receiptNumber = Sharp/Number, receiptLines = Sharp/Lines
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

public class R4StoreDirector : MonoBehaviour
{
    enum Leave { None, Bounced, Back }
    enum Phase { Order, Kiosk, Pickup, Called, End }

    [SerializeField] KioskController kiosk;
    [SerializeField] R4ProtoPack pack;
    [SerializeField] QueueManager queue;
    [SerializeField] Transform stand;
    [SerializeField] Transform kioskLook;
    [SerializeField] Transform staffPos;
    [SerializeField] Transform exitPos;
    [SerializeField] Interactable orderKiosk;
    [SerializeField] Interactable talkStaff;
    [SerializeField] Interactable brokenKiosk;
    [SerializeField] Interactable exitDoor;
    [SerializeField] NpcMover[] pool;
    [SerializeField] GameObject tray;
    [SerializeField] Transform trayFrom;
    [SerializeField] Transform trayTo;
    [SerializeField] Transform exitLook;
    [SerializeField] Transform pickupPos;
    [SerializeField] NpcMover cook;
    [SerializeField] Transform cookA;
    [SerializeField] Transform cookB;
    [SerializeField] PickupBoard board;
    [SerializeField] GameObject shelf;
    [SerializeField] GameObject shelfCup;
    [SerializeField] Transform carried;
    [SerializeField] GameObject receiptView;
    [SerializeField] TMP_Text[] receiptNumber;
    [SerializeField] TMP_Text[] receiptLines;
    [SerializeField] TMP_Text[] cupLabels;
    [SerializeField] Interactable takeBag;

    Leave leave;
    Phase phase;
    NpcMover rival;
    bool talking, muttering, ordered, atKiosk;
    int retries, talk;
    float nextBeep = 12f, nextNotify = 16f, carryT, carryWant;
    Transform fryerPos;
    readonly List<int> ready = new List<int> { 269, 271, 272 };
    int call = 268;

    static string Me => GameState.I.Profile.speakerKey;
    static Hud Ui => Hud.I;

    void Awake()
    {
        exitDoor.active = false;
        if (tray) tray.SetActive(false);
        GameObject fryer = GameObject.Find("Anchor_Fryer");
        fryerPos = fryer ? fryer.transform : staffPos;
    }

    void OnEnable()
    {
        orderKiosk.onUse.AddListener(OnOrder);
        talkStaff.onUse.AddListener(OnTalk);
        if (brokenKiosk) brokenKiosk.onUse.AddListener(OnBroken);
        takeBag.onUse.AddListener(OnTake);
        kiosk.StaffCalled += OnStaffCalled;
        pack.Helping += OnHelping;
        pack.Bounced += OnBounced;
    }

    void OnDisable()
    {
        orderKiosk.onUse.RemoveListener(OnOrder);
        talkStaff.onUse.RemoveListener(OnTalk);
        if (brokenKiosk) brokenKiosk.onUse.RemoveListener(OnBroken);
        takeBag.onUse.RemoveListener(OnTake);
        kiosk.StaffCalled -= OnStaffCalled;
        pack.Helping -= OnHelping;
        pack.Bounced -= OnBounced;
    }

    void OnDestroy()
    {
        // 손은 씬을 건너가므로 붙인 물건은 같이 치운다
        if (carried) Destroy(carried.gameObject);
        if (receiptView) Destroy(receiptView);
    }

    IEnumerator Start()
    {
        shelf.SetActive(false);
        shelfCup.SetActive(false);
        carried.gameObject.SetActive(false);
        Transform hand = PlayerController.I.HandRoot;
        carried.SetParent(hand, false);
        HandRig.I.SetReceiptView(receiptView.transform);
        takeBag.active = false;
        ready.Add(Number);
        board.Show(ready, call);
        AudioManager.I.Ambience(("amb_restaurant", 0.36f), ("amb_kitchen", 0.5f));
        yield return Round.Open();
        PlayerController.I.Freeze(true);
        yield return Ui.Say(Me, "주문은... 어디다 하는 거지.", Me + "_whereorder");
        if (!ordered) PlayerController.I.Freeze(false);
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

    int Number => Bal.I("R4_OrderNumber", 273);

    // ---- 알바생과 고장 난 기계 ----

    void OnTalk()
    {
        if (talking) return;
        StartCoroutine(Talk(true));
    }

    void OnStaffCalled()
    {
        if (talking) return;
        StartCoroutine(Talk(false));
    }

    // 임시 T08: 4-7 휴대폰만 보고 말한다. 프로토타입 Talk의 세 문구를 돈다
    IEnumerator Talk(bool ask)
    {
        talking = true;
        talk++;
        if (ask && talk == 1) yield return Ui.Say(Me, "저기요...", Me + "_staff2");
        AudioManager.I.Play("phone_notify", staffPos.position, 0.3f);
        if (phase == Phase.Pickup || phase == Phase.Called) yield return Ui.Say("staff", "네?", "staff_2", -1f, staffPos.position);
        else if (talk % 3 == 2) yield return Ui.Say("staff", "거기 화면 누르시면 돼요.", "staff_3", -1f, staffPos.position);
        else if (talk % 3 == 0) yield return Ui.Say("staff", "네?", "staff_2", -1f, staffPos.position);
        else yield return Ui.Say("staff", "주문은 키오스크에서 해주세요.", "staff_1", -1f, staffPos.position);
        talking = false;
    }

    void OnBroken()
    {
        if (muttering) return;
        StartCoroutine(Broken());
    }

    IEnumerator Broken()
    {
        muttering = true;
        AudioManager.I.Play("kiosk_tap", brokenKiosk.transform.position, 0.5f);
        yield return Ui.Say(Me, "이게 왜 안 돼.", Me + "_why2");
        muttering = false;
    }

    // ---- 키오스크 ----

    void OnOrder()
    {
        if (ordered) return;
        ordered = true;
        StartCoroutine(RunKiosk());
    }

    NunchiRule Rule() => new NunchiRule
    {
        onFull = OnFull,
        start = retries > 0 ? Bal.G("R4_RetryNunchi", 50f) : 0f,   // 임시: 초기화 값 미정, 절반
    };

    IEnumerator RunKiosk()
    {
        var player = PlayerController.I;
        phase = Phase.Kiosk;
        orderKiosk.active = false;
        if (brokenKiosk) brokenKiosk.active = false;
        talkStaff.active = false;
        queue.KioskOn = true;
        player.Freeze(true);
        HandRig.I.Equip(ItemId.None);
        while (true)
        {
            yield return StoreFlow.Race(this, player.WalkTo(stand.position, Bal.F("MoveSpeed", 1.15f)), 4f);
            yield return player.LookAt(kioskLook.position, Bal.G("Cine_BlendSec", 1f));
            kiosk.Nunchi.Configure(Rule());
            queue.KioskOn = true;
            atKiosk = true;
            yield return kiosk.Enter();
            atKiosk = false;
            queue.KioskOn = false;
            player.Freeze(true);
            player.SetMode(PlayerController.Mode.Fps);
            HandRig.I.SetPointer(false);
            if (leave != Leave.Back) break;
            yield return Requeue();
            leave = Leave.None;
            retries++;
        }
        yield return Helped();
        StartCoroutine(Pickup());
    }

    // 임시: 대기 시간 미정. 비켜나 줄 맨 뒤로 가고, 앞사람이 카드로 금방 결제하고, 쟁반이 지나간 뒤 차례가 온다
    IEnumerator Requeue()
    {
        var player = PlayerController.I;
        rival = Front();
        Vector3 back = queue.QueuePos - stand.position;
        back.y = 0f;
        Vector3 tail = stand.position + back.normalized * (back.magnitude + Bal.G("R4_RequeueGap", 0.9f) * Mathf.Max(queue.Count, 1));
        tail.y = player.transform.position.y;
        yield return StoreFlow.Race(this, player.WalkTo(tail + Vector3.right * 0.8f, Bal.F("MoveSpeed", 1.15f)), Bal.G("R4_RequeueWalkSec", 3f));
        yield return player.LookAt(kioskLook.position, Bal.G("Cine_BlendSec", 1f));
        yield return Takeover();
        yield return Tray(rival);
        var served = rival;
        served.Go(exitPos.position, Bal.G("R4_RivalSpeed", 1.4f), () => queue.Done(served));
        yield return new WaitForSeconds(Bal.G("R4_RequeueWaitSec", 2f));

        // 앞사람이 끝나면 암전으로 차례가 온다. 뒤에는 새 손님이 선다
        yield return Ui.Fade(1f, 0.4f);
        if (served.isActiveAndEnabled) queue.Done(served);
        queue.Refill();
        Vector3 to = kioskLook.position - stand.position;
        player.Teleport(stand.position, Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg);
        yield return player.LookAt(kioskLook.position, 0.01f);
        yield return Ui.Fade(0f, 0.4f);
    }

    void OnBounced()
    {
        if (leave != Leave.None) return;
        leave = Leave.Bounced;
        kiosk.Finish();
    }

    void OnFull()
    {
        if (leave != Leave.None || pack.Done) return;
        leave = Leave.Back;
        pack.Stop();
        kiosk.Finish(Bal.G("Nunchi_FullLeaveSec", 0.2f));
    }

    // 도와주는 사람은 장면 A 주인공. 줄 손님이 아니라 고정 손님이다
    void OnHelping() => rival = queue.Regular();

    // 입력 없음. 비켜서면 뒷사람이 와서 카드를 대고, 비켜 준 자리로 돌아와 지폐를 내밀며 인사한다
    IEnumerator Helped()
    {
        var player = PlayerController.I;
        float speed = Bal.F("MoveSpeed", 1.15f);
        Vector3 right = Vector3.right * Bal.G("R4_HelpAsideX", 1.1f), back = Vector3.back * Bal.G("R4_HelpAsideZ", 0.6f);
        Vector3 aside = stand.position + right + back;
        aside.y = player.transform.position.y;
        yield return StoreFlow.Race(this, player.WalkTo(aside, speed), Bal.G("R4_HelpWalkSec", 2.5f));
        yield return player.LookAt(kioskLook.position, Bal.G("Cine_BlendSec", 1f));

        float rivalSpeed = Bal.G("R4_RivalSpeed", 1.4f);
        yield return StoreFlow.Race(this, rival.WalkTo(stand.position, rivalSpeed), Bal.G("R4_RivalWalkSec", 5f));
        rival.Face(kioskLook.position);
        rival.TryGetComponent(out NpcPose pose);
        if (pose) pose.pose = "Tap";
        yield return pack.HelpPay();
        if (pose) pose.pose = "Idle";

        // 뒷사람은 왼쪽으로 비켜 주고 플레이어가 키오스크 앞으로 돌아온다
        Vector3 side = stand.position - right + back;
        yield return StoreFlow.Race(this, rival.WalkTo(side, rivalSpeed), Bal.G("R4_HelpWalkSec", 2.5f));
        rival.Face(stand.position);
        Vector3 home = stand.position;
        home.y = player.transform.position.y;
        yield return StoreFlow.Race(this, player.WalkTo(home, speed), Bal.G("R4_HelpWalkSec", 2.5f));
        yield return player.LookAt(rival.transform.position + Vector3.up * 1.5f, Bal.G("Cine_BlendSec", 1f));

        HandRig.I.Equip(ItemId.Cash);
        yield return Ui.Say(Me, "아이고, 고맙구먼.", Me + "_thanks");
        HandRig.I.Equip(ItemId.None);
        rival.React(true);
        yield return player.LookAt(kioskLook.position, Bal.G("Cine_BlendSec", 1f));
        pack.TearReceipt();
        yield return new WaitForSeconds(Bal.G("R4_TearSec", 0.5f));
        player.Freeze(false);
    }

    // 지금 키오스크에 가장 가까운 줄 손님. 아직 아무도 안 왔으면 줄 맨 앞에 세운다
    NpcMover Front()
    {
        NpcMover best = null;
        float bestDist = float.MaxValue;
        foreach (var n in pool)
        {
            if (!n.isActiveAndEnabled) continue;
            float d = (n.transform.position - stand.position).sqrMagnitude;
            if (d < bestDist) { bestDist = d; best = n; }
        }
        if (best) return best;
        best = pool[0];
        best.Place(queue.QueuePos - Vector3.up * 1.5f);
        best.Show();
        return best;
    }

    // 뒷사람이 실제 화면을 넘기며 결제한다. 다음 손님 규칙은 QueueManager가 맡는다
    IEnumerator Takeover()
    {
        yield return queue.UseKiosk(rival);
    }

    // 결제한 손님이 두 손으로 쟁반을 들고 지나간다. 들고 갈 사람이 없으면 쟁반은 안 보인다
    IEnumerator Tray(NpcMover carrier)
    {
        if (!tray) yield break;
        if (!carrier || !carrier.isActiveAndEnabled) { tray.SetActive(false); yield break; }
        float hand = Bal.G("R4_TrayHandY", 1.05f), reach = Bal.G("R4_TrayReach", 0.32f), sec = Bal.G("R4_TraySec", 2.4f);
        Vector3 to = trayTo.position;
        to.y = carrier.transform.position.y;
        carrier.Go(to, Vector3.Distance(carrier.transform.position, to) / Mathf.Max(sec, 0.01f));
        tray.SetActive(true);
        AudioManager.I.Play("tray_put", carrier.transform.position, 0.4f);
        for (float t = 0f; t < sec && carrier.isActiveAndEnabled; t += Time.deltaTime)
        {
            var c = carrier.transform;
            tray.transform.position = c.position + Vector3.up * hand + c.forward * reach;
            tray.transform.rotation = Quaternion.Euler(0f, c.eulerAngles.y, 0f);
            yield return null;
        }
        tray.SetActive(false);
    }

    // ---- 호출과 수령. 프로토타입 Pickup, Take ----

    IEnumerator Pickup()
    {
        phase = Phase.Pickup;
        talkStaff.active = true;
        float cookSpeed = Bal.G("Queue_CookSpeed", 1.3f);
        cook.Go(cookA.position, cookSpeed, () => cook.Go(cookB.position, cookSpeed, () => cook.Face(pickupPos.position)));
        FillReceipt();
        HandRig.I.GiveReceipt();
        queue.ServeWhenClear();
        yield return new WaitForSeconds(Bal.G("Pickup_ReadDelay", 2.2f));
        yield return Ui.Say(Me, "글씨가 왜 이렇게 작아.", Me + "_read1");

        foreach (int num in new[] { 269, 271, 272 })
        {
            yield return new WaitForSeconds(Random.Range(Bal.G("Pickup_CallMin", 8f), Bal.G("Pickup_CallMax", 10f)));
            yield return CallOne(num);
        }
        yield return new WaitForSeconds(Random.Range(Bal.G("Pickup_LastMin", 7f), Bal.G("Pickup_LastMax", 9f)));

        string cup = pack.Cider ? "사이다" : "콜라";
        foreach (TMP_Text t in cupLabels) t.text = cup;
        ready.Clear();
        call = Number;
        board.Show(ready, call);
        shelf.SetActive(true);
        shelfCup.SetActive(true);
        phase = Phase.Called;
        takeBag.active = true;
        PutOnShelf();
        AudioManager.I.Play("pager_call", pickupPos.position, 1f);
        Ui.Say("crew", $"{{g:{Number}번}} 고객님.", $"staff_call_{Number}");
        yield return new WaitForSeconds(3f);

        bool scold = false;
        while (phase == Phase.Called)
        {
            yield return new WaitForSeconds(Bal.G("Pickup_RecallSec", 13f));
            if (phase != Phase.Called) break;
            AudioManager.I.Play("pager_call", pickupPos.position, 0.8f);
            if (scold) Ui.Say("crew", $"{{g:{Number}번}} 고객님, 메뉴 가져가세요.", $"staff_scold_{Number}");
            else Ui.Say("crew", $"{{g:{Number}번}} 고객님.", $"staff_call_{Number}");
            scold = !scold;
        }
    }

    IEnumerator CallOne(int num)
    {
        ready.Remove(num);
        call = num;
        board.Show(ready, call);
        AudioManager.I.Play("pager_call", pickupPos.position, 0.8f);
        // 269, 271, 272는 새 목소리 파일이 없다. 키를 넘기면 JW 폴더의 옛 남자 음성이 나오니 자막만 낸다
        Ui.Say("crew", $"{{g:{num}번}} 고객님.", null, -1f, staffPos.position);
        shelf.SetActive(true);
        PutOnShelf();
        yield return queue.WaiterPickup(() => shelf.SetActive(false));
    }

    // 받는 곳에 음식이 놓이는 소리
    void PutOnShelf() => AudioManager.I.Play("tray_put", pickupPos.position, Bal.G("Pickup_TrayVolume", 0.6f));

    void FillReceipt()
    {
        foreach (TMP_Text t in receiptNumber) t.text = Number.ToString();
        foreach (TMP_Text t in receiptLines) t.text = pack.Lines;
    }

    void OnTake()
    {
        if (phase != Phase.Called) return;
        StartCoroutine(Take());
    }

    // 받고 대사 뒤 문 쪽을 본 채 결과로 간다
    IEnumerator Take()
    {
        var player = PlayerController.I;
        phase = Phase.End;
        takeBag.active = false;
        talkStaff.active = false;
        player.Freeze(true);
        HandRig.I.TakeReceipt();
        HandRig.I.SetEnabled(false);
        Ui.Views(null);
        Ui.ClearSubs();
        AudioManager.I.Play("bag_rustle", null, 0.9f);
        shelf.SetActive(false);
        carried.gameObject.SetActive(true);
        carryWant = 1f;
        StartCoroutine(player.LookAt(exitLook.position, 1.1f));
        yield return new WaitForSeconds(1f);
        yield return Ui.Say(Me, "됐다... 됐어.", Me + "_done");
        yield return new WaitForSeconds(0.5f);
        if (!pack.Cider) yield return Ui.Say(null, "{r:콜라}", null, 1.6f);
        yield return Ui.Say(Me, "이거 하나 사기가 이렇게 힘들어서야.", Me + "_end");
        yield return new WaitForSeconds(0.7f);
        yield return Ui.Fade(1f, 1.8f);
        GameState.I.CompleteChapter();
    }
}
