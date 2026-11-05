// 매장 안: 안 도와주는 알바생, 키오스크 진입, 픽업, 받기, 결과. Store 씬 Director 오브젝트에 부착(QueueManager와 같이).
// 좌표는 HTML판 값의 z에 -1을 곱한 Unity 좌표.
// 배치: queue = 같은 오브젝트의 QueueManager
// 배치: kiosk = PH_Kiosk (KioskController)
// 배치: stand = Anchor_KioskStand (-0.6, 0, 3.08)
// 배치: kioskLook = Anchor_KioskLook (-0.6, 1.32, 3.82)
// 배치: exitLook = Anchor_ExitLook (1.4, 1.05, -3.8) 받은 뒤 문 쪽을 보는 곳
// 배치: staffPos = Anchor_Staff (-3.72, 1.3, 2.5) 말소리 위치
// 배치: pickupPos = Anchor_PickupLook (-2.92, 1.08, -0.85) 픽업 대
// 배치: chimePos = Anchor_FrontDoor (1.4, 1.2, -3.8) 문 닫히는 소리 위치
// 배치: fryerPos = Anchor_Fryer (-5.4, 1, 3) 주방 소리 위치
// 배치: cook = NPC_Cook (NpcMover (-5, 0, 1.4))
// 배치: cookA = Anchor_CookA (-4.7, 0, -0.85)
// 배치: cookB = Anchor_CookB (-3.5, 0, -0.85)
// 배치: board = PH_PickupBoard (PickupBoard)
// 배치: shelf = Pickup_Shelf 픽업 대 위 봉투 (-2.9, 1.09, -0.85)
// 배치: shelfCup = Pickup_Shelf 자식 컵
// 배치: carried = Carried_Bag 들고 가는 봉투와 컵 묶음. 시작할 때 HandRoot로 옮겨 붙는다
// 배치: receiptView = Receipt_View (Readable, 앞면이 로컬 -Z, 0.105 x 0.2). 시작할 때 HandRoot로 옮겨 붙는다
// 배치: receiptNumber = Receipt_View/Sharp 번호 TMP (번진 쪽은 회색 막대)
// 배치: receiptLines = Receipt_View/Sharp 메뉴 줄 TMP
// 배치: cupLabels = shelfCup과 Carried_Bag 컵의 TMP들
// 배치: talkStaff = Interact_Staff (label 말 걸기, E, radius 2, cone 0.7, 위치 (-2.8, 1.3, 2.5))
// 배치: orderKiosk = Interact_Order (label 주문하기, E, radius 1.9, cone 0.62, 위치 (-0.6, 1.35, 3.72))
// 배치: brokenKiosk = Interact_Broken (label 화면 누르기, E, radius 1.7, cone 0.8, 위치 (0.72, 1.35, 3.72))
// 배치: takeBag = Interact_Take (label 받기, E, radius 2.1, cone 0.68, 위치 (-2.92, 1.2, -0.85))
// 배치: eater = NPC_Eater (매장 앞에서 유리 너머로 보이는 손님)
// 배치: spawn = PlayerSpawn
// 배치: sharedRoom = Room 아래 Floor, Floor_Outside, Ceiling, Wall_Back, Wall_West, Wall_East, PH_Storefront (매장 앞 씬에 같은 것이 있어 미리 불러올 때 끈다)
// 배치: frontDoor = Room/PH_Door_Glass (문을 지나 들어오는 순간 켠다)
// 배치: bounds = Bounds (Bound_Front가 인도를 막으므로 들어올 때 켠다)
// 미리 불러오기: StorefrontDirector가 PreviewNext를 켜고 Additive로 부르면 이 씬은 보이기만 하고 진행은 멈춘다.
// 문을 지나면 EnterFromDoor로 이어 받는다. 이 씬을 Single로 바로 열면 지금까지와 같다.
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

public class StoreDirector : MonoBehaviour
{
    enum Phase { Preview, Enter, Order, Kiosk, Pickup, Called, End }

    /// <summary>다음에 깨어나는 StoreDirector를 미리 보기로 둔다. 깨어나면 꺼진다.</summary>
    public static bool PreviewNext { get; set; }
    /// <summary>미리 불러온 채 플레이어를 기다리는 매장.</summary>
    public static StoreDirector Waiting { get; private set; }

    [SerializeField] QueueManager queue;
    [SerializeField] KioskController kiosk;
    [SerializeField] Transform stand;
    [SerializeField] Transform kioskLook;
    [SerializeField] Transform exitLook;
    [SerializeField] Transform staffPos;
    [SerializeField] Transform pickupPos;
    [SerializeField] Transform chimePos;
    [SerializeField] Transform fryerPos;
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
    [SerializeField] Interactable talkStaff;
    [SerializeField] Interactable orderKiosk;
    [SerializeField] Interactable brokenKiosk;
    [SerializeField] Interactable takeBag;
    [SerializeField] NpcMover eater;
    [SerializeField] PlayerSpawn spawn;
    [SerializeField] GameObject[] sharedRoom;
    [SerializeField] GameObject frontDoor;
    [SerializeField] GameObject bounds;

    public NpcMover Eater => eater;

    Phase phase;
    CharacterController body;
    float bodyStep;
    int talk;
    bool talking, muttering;
    float nextBeep = 12f, nextNotify = 16f;

    readonly List<int> ready = new List<int> { 269, 271, 272 };
    int call = 268;

    bool receiptHave, receiptOn;
    float receiptT, carryT, carryWant;

    string Me => GameState.I.Profile.speakerKey;
    OrderData Order => GameState.I.Order;

    bool DrinkIsCider
    {
        get
        {
            string d = Order.drink ?? "";
            return d.Contains("cider") || d.Contains("사이다") || d.Contains("라임");
        }
    }

    void Awake()
    {
        if (!PreviewNext) return;
        PreviewNext = false;
        Waiting = this;
        foreach (GameObject g in sharedRoom) g.SetActive(false);
        frontDoor.SetActive(false);
        bounds.SetActive(false);
    }

    void OnEnable()
    {
        talkStaff.onUse.AddListener(OnTalk);
        orderKiosk.onUse.AddListener(OnOrder);
        brokenKiosk.onUse.AddListener(OnBroken);
        takeBag.onUse.AddListener(OnTake);
    }

    void OnDisable()
    {
        talkStaff.onUse.RemoveListener(OnTalk);
        orderKiosk.onUse.RemoveListener(OnOrder);
        brokenKiosk.onUse.RemoveListener(OnBroken);
        takeBag.onUse.RemoveListener(OnTake);
    }

    void OnDestroy()
    {
        if (Waiting == this) Waiting = null;
        if (body) body.stepOffset = bodyStep;
        // 손은 씬을 건너가므로 이 씬에서 붙인 물건은 같이 치운다
        if (carried) Destroy(carried.gameObject);
        if (receiptView) Destroy(receiptView);
    }

    void Start()
    {
        shelf.SetActive(false);
        shelfCup.SetActive(false);
        carried.gameObject.SetActive(false);
        receiptView.SetActive(false);
        Transform hand = PlayerController.I.HandRoot;
        carried.SetParent(hand, false);
        receiptView.transform.SetParent(hand, false);
        ready.Add(Order.number);
        board.Show(ready, call);
        if (Waiting == this)
        {
            SetPhase(Phase.Preview);
            return;
        }
        Begin();
    }

    /// <summary>문을 지나 들어온 플레이어를 이어 받는다. doorAngle은 QueueManager 문 각도, 라디안.</summary>
    public void EnterFromDoor(float doorAngle)
    {
        Waiting = null;
        frontDoor.SetActive(true);
        bounds.SetActive(true);
        queue.SetDoor(doorAngle);
        SceneManager.SetActiveScene(gameObject.scene);
        PlayerController.I.Ground = spawn.ground;
        HandRig.I.Clear();
        Begin();
    }

    void Begin()
    {
        // 높이가 고정된 플레이어가 턱을 오르다 되돌아오는 일이 없게 매장 안에서는 오르지 않는다
        body = PlayerController.I.GetComponent<CharacterController>();
        if (body)
        {
            bodyStep = body.stepOffset;
            body.stepOffset = 0f;
        }
        SetPhase(Phase.Enter);
        StartCoroutine(Intro());
    }

    void SetPhase(Phase p)
    {
        phase = p;
        bool before = p == Phase.Enter || p == Phase.Order;
        talkStaff.active = p != Phase.Kiosk && p != Phase.Preview;
        orderKiosk.active = before;
        brokenKiosk.active = before;
        takeBag.active = p == Phase.Called;
    }

    IEnumerator Intro()
    {
        var player = PlayerController.I;
        AudioManager.I.Ambience(("amb_restaurant", 0.36f), ("amb_kitchen", 0.5f));
        player.SetMode(PlayerController.Mode.Fps);
        player.Freeze(true);
        HandRig.I.SetEnabled(false);
        AudioManager.I.Play("door_close_metal", chimePos.position, 0.5f);
        Hud.I.Fade(0f, 0.8f);
        yield return new WaitForSeconds(0.9f);
        yield return Hud.I.Say(Me, "주문은... 어디다 하는 거지.", Me + "_whereorder");
        if (phase == Phase.Enter) SetPhase(Phase.Order);
        Hud.I.Objective("{y:주문}", 5f);
        HandRig.I.SetEnabled(true);
        player.Freeze(false);
    }

    void OnTalk()
    {
        if (talking) return;
        StartCoroutine(Talk());
    }

    IEnumerator Talk()
    {
        talking = true;
        talk++;
        if (talk == 1) yield return Hud.I.Say(Me, "저기요...", Me + "_staff2");
        if (phase == Phase.Order || phase == Phase.Enter)
        {
            if (talk % 3 == 2) yield return Hud.I.Say("staff", "거기 화면 누르시면 돼요.", "staff_3");
            else if (talk % 3 == 0) yield return Hud.I.Say("staff", "네?", "staff_2");
            else yield return Hud.I.Say("staff", "주문은 키오스크에서 해주세요.", "staff_1");
        }
        else
        {
            yield return Hud.I.Say("staff", "네?", "staff_2");
        }
        if (phase == Phase.Order) Hud.I.Objective("{y:키오스크}", 5f);
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
        yield return Hud.I.Say(Me, "이게 왜 안 돼.", Me + "_why2");
        muttering = false;
    }

    void OnOrder()
    {
        if (phase != Phase.Order && phase != Phase.Enter) return;
        StartCoroutine(RunKiosk());
    }

    IEnumerator RunKiosk()
    {
        var player = PlayerController.I;
        SetPhase(Phase.Kiosk);
        queue.KioskOn = true;
        player.Freeze(true);
        HandRig.I.Equip(ItemId.None);
        yield return StoreFlow.Race(this, player.WalkTo(stand.position, Bal.F("MoveSpeed", 1.15f)), 4f);
        yield return player.LookAt(kioskLook.position, 0.5f);
        yield return kiosk.Enter();
        queue.KioskOn = false;
        player.SetMode(PlayerController.Mode.Fps);
        HandRig.I.SetPointer(false);
        player.Freeze(false);
        StartCoroutine(Pickup());
    }

    IEnumerator Pickup()
    {
        SetPhase(Phase.Pickup);
        int mine = Order.number;
        float cookSpeed = Bal.G("Queue_CookSpeed", 1.3f);
        cook.Go(cookA.position, cookSpeed, () => cook.Go(cookB.position, cookSpeed, () => cook.Face(pickupPos.position)));
        FillReceipt();
        receiptHave = true;
        receiptOn = true;
        Hud.I.Views("4 영수증");
        AudioManager.I.Play("paper_rustle", null, 0.5f);
        queue.ShuffleForward();
        Hud.I.Objective("{y:대기}", 5f);
        yield return new WaitForSeconds(Bal.G("Pickup_ReadDelay", 2.2f));
        yield return Hud.I.Say(Me, "글씨가 왜 이렇게 작아.", Me + "_read1");

        foreach (int num in new[] { 269, 271, 272 })
        {
            yield return new WaitForSeconds(Random.Range(Bal.G("Pickup_CallMin", 8f), Bal.G("Pickup_CallMax", 10f)));
            yield return CallOne(num);
        }
        yield return new WaitForSeconds(Random.Range(Bal.G("Pickup_LastMin", 7f), Bal.G("Pickup_LastMax", 9f)));

        string cup = DrinkIsCider ? "사이다" : "콜라";
        foreach (TMP_Text t in cupLabels) t.text = cup;
        ready.Clear();
        call = mine;
        board.Show(ready, call);
        shelf.SetActive(true);
        shelfCup.SetActive(true);
        SetPhase(Phase.Called);
        PutOnShelf();
        AudioManager.I.Play("pager_call", pickupPos.position, 1f);
        Hud.I.Say("staff", $"{{g:{mine}번}} 고객님.", "staff_call");
        yield return new WaitForSeconds(3f);
        Hud.I.Objective("{y:계산대}", 6f);

        bool scold = false;
        while (phase == Phase.Called)
        {
            yield return new WaitForSeconds(Bal.G("Pickup_RecallSec", 13f));
            if (phase != Phase.Called) break;
            AudioManager.I.Play("pager_call", pickupPos.position, 0.8f);
            if (scold) Hud.I.Say("staff", $"{{g:{mine}번}} 고객님, 메뉴 가져가세요.", "staff_call3");
            else Hud.I.Say("staff", $"{{g:{mine}번}} 고객님.", "staff_call");
            scold = !scold;
        }
    }

    IEnumerator CallOne(int num)
    {
        ready.Remove(num);
        call = num;
        board.Show(ready, call);
        AudioManager.I.Play("pager_call", pickupPos.position, 0.8f);
        Hud.I.Say("staff", $"{{g:{num}번}} 고객님.", $"staff_call_{num}", -1f, staffPos.position);
        shelf.SetActive(true);
        PutOnShelf();
        yield return queue.WaiterPickup(() => shelf.SetActive(false));
    }

    // 받는 곳에 음식이 놓이는 소리. HTML판은 파일만 있고 쓰지 않아 선반이 나타나는 순간에 둔다
    void PutOnShelf() => AudioManager.I.Play("tray_put", pickupPos.position, Bal.G("Pickup_TrayVolume", 0.6f));

    void FillReceipt()
    {
        string lines = string.Join("\n",
            KioskData.ById(Order.item)?.name ?? "K-BBQ 스모키 비프",
            KioskData.Combo(Order.combo)?.name ?? "COMBO",
            KioskData.ById(Order.side)?.name ?? "프렌치 프라이 R",
            KioskData.ById(Order.drink)?.name ?? "제로 콜라");
        foreach (TMP_Text t in receiptNumber) t.text = Order.number.ToString();
        foreach (TMP_Text t in receiptLines) t.text = lines;
    }

    void OnTake()
    {
        if (phase != Phase.Called) return;
        StartCoroutine(Take());
    }

    IEnumerator Take()
    {
        var player = PlayerController.I;
        SetPhase(Phase.End);
        GameState.I.Stats.endTime = Time.time;
        player.Freeze(true);
        receiptOn = false;
        receiptHave = false;
        HandRig.I.SetEnabled(false);
        Hud.I.Views("");
        Hud.I.ClearSubs();
        AudioManager.I.Play("bag_rustle", null, 0.9f);
        shelf.SetActive(false);
        carried.gameObject.SetActive(true);
        carryWant = 1f;
        StartCoroutine(player.LookAt(exitLook.position, 1.1f));
        yield return new WaitForSeconds(1f);
        yield return Hud.I.Say(Me, "됐다... 됐어.", Me + "_done");
        yield return new WaitForSeconds(0.5f);
        if (!DrinkIsCider) yield return Hud.I.Say(null, "{r:콜라}", null, 1.6f);
        yield return Hud.I.Say(Me, "이거 하나 사기가 이렇게 힘들어서야.", Me + "_end");
        yield return new WaitForSeconds(0.7f);
        yield return Hud.I.Fade(1f, 1.8f);
        GameState.I.CompleteChapter();
    }

    void Update()
    {
        float dt = Time.deltaTime;
        if (phase == Phase.Preview) return;

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

        if (GameState.I.DebugToKiosk && phase != Phase.Enter)
        {
            GameState.I.DebugToKiosk = false;
            if (phase == Phase.Order) OnOrder();
        }

        var kb = Keyboard.current;
        if (receiptHave && kb != null && kb.digit4Key.wasPressedThisFrame)
        {
            receiptOn = !receiptOn;
            AudioManager.I.Play("paper_rustle", null, 0.5f);
        }

        // 돋보기를 든 채 영수증을 볼 수 있어야 하므로 HandRig 소지품이 아니라 따로 올라온다
        receiptT = StoreFlow.Damp(receiptT, receiptOn ? 1f : 0f, 9f, dt);
        bool showReceipt = receiptT > 0.01f;
        if (receiptView.activeSelf != showReceipt) receiptView.SetActive(showReceipt);
        receiptView.transform.localPosition = new Vector3(0f, -0.038f - (1f - receiptT) * 0.34f, 0.4f);

        carryT = StoreFlow.Damp(carryT, carryWant, 4f, dt);
        carried.localPosition = new Vector3(0.06f, -0.62f + carryT * 0.33f + Mathf.Sin(Time.time * 1.6f) * 0.004f, 0.5f);
        carried.localRotation = Quaternion.Euler(-6.9f, 14.3f, 2.3f);
    }
}
