// 4회차 가게: 게이지가 다 차면 줄 맨 뒤로 갔다가 다시 시도한다. 지폐가 3번 튕기면 뒷사람과 말을 나누고 돌아서서 시선을 받으며 못 사고 나간다.
// R4_Store 씬 Director 오브젝트에 부착.
// 배치: kiosk = PH_Kiosk, pack = KioskCanvas (R4ProtoPack), queue = QueueManager
// 배치: stand = Anchor_KioskStand, kioskLook = Anchor_KioskLook, staffPos = Anchor_Staff, exitPos = Anchor_FrontDoor
// 배치: orderKiosk = Interact_Order, talkStaff = Interact_Staff, brokenKiosk = Interact_Broken, exitDoor = Interact_Exit (label 나가기)
// 배치: pool = 줄 손님 NPC_Queue0~4 (맨 앞 사람이 뒷사람), tray = Tray_Pass (쟁반, 처음 꺼짐), trayFrom, trayTo = 쟁반이 지나는 양 끝
using System.Collections;
using UnityEngine;

public class R4StoreDirector : MonoBehaviour
{
    enum Leave { None, Bounced, Back }

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

    Leave leave;
    NpcMover rival;
    bool talking, muttering, ordered, atKiosk;
    int retries;
    float nextBeep = 12f, nextNotify = 16f;
    Transform fryerPos;

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
        exitDoor.onUse.AddListener(OnExit);
        kiosk.StaffCalled += OnStaffCalled;
        pack.Bounced += OnBounced;
    }

    void OnDisable()
    {
        orderKiosk.onUse.RemoveListener(OnOrder);
        talkStaff.onUse.RemoveListener(OnTalk);
        if (brokenKiosk) brokenKiosk.onUse.RemoveListener(OnBroken);
        exitDoor.onUse.RemoveListener(OnExit);
        kiosk.StaffCalled -= OnStaffCalled;
        pack.Bounced -= OnBounced;
    }

    IEnumerator Start()
    {
        AudioManager.I.Ambience(("amb_restaurant", 0.36f), ("amb_kitchen", 0.5f));
        yield return Round.Open();
        PlayerController.I.Freeze(true);
        yield return Ui.Say(null, "주문은... 어디다 하는 거지.", Me + "_whereorder");
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
    }

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

    // 임시 T08: 4-7 휴대폰만 보고 같은 말을 한다
    IEnumerator Talk(bool ask)
    {
        talking = true;
        if (ask) yield return Ui.Say(null, "저기요...", Me + "_staff2");
        AudioManager.I.Play("phone_notify", staffPos.position, 0.3f);
        yield return Ui.Say(null, "주문은 키오스크에서 해주세요.", "staff_1", -1f, staffPos.position);
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
        yield return Ui.Say(null, "이게 왜 안 돼.", Me + "_why2");
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
        low = new[] { "아, 늦었는데." },
        mid = new[] { "저기요, 빨리 좀 해요.", "왜 저렇게 오래 걸려." },
        high = new[] { "뒤에 사람 기다려요.", "그거 아니에요." },   // 임시 T33
        onFull = OnFull,
        start = retries > 0 ? Bal.G("R4_RetryNunchi", 50f) : 0f,   // 임시: 초기화 값 미정, 절반
    };

    IEnumerator RunKiosk()
    {
        var player = PlayerController.I;
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
        yield return Sent();
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
        kiosk.Finish();
    }

    // 4-10a. 입력 없음. 슬픈 얼굴은 보이지 않고 시선을 내리고 돌아선 뒤, 키오스크 앞을 비우면 뒷사람이 쓴다
    IEnumerator Sent()
    {
        var player = PlayerController.I;
        rival = Front();
        float sad = Bal.G("R4_SadPitch", -28f);
        yield return player.TurnTo(player.Yaw, sad, Bal.G("R4_SadLookSec", 1.2f));
        yield return player.TurnTo(player.Yaw + 180f, sad, Bal.G("R4_SadTurnSec", 1.6f));

        Vector3 way = exitPos.position - stand.position;
        way.y = 0f;
        Vector3 aside = stand.position + way.normalized * (Bal.G("Queue_ClearDist", 1.1f) + Bal.G("R4_SentStepDist", 0.6f)) + Vector3.right * 0.8f;
        aside.y = player.transform.position.y;
        yield return StoreFlow.Race(this, player.WalkTo(aside, Bal.F("MoveSpeed", 1.15f)), Bal.G("R4_RequeueWalkSec", 3f));
        // 1회차와 같은 순서: 어르신이 돌아서 나가는 동안 뒷사람이 키오스크로 가서 카드로 결제한다
        StartCoroutine(RivalPays());
        yield return player.TurnTo(player.Yaw, 0f, Bal.G("R4_SadTurnSec", 1.6f));

        // 4-10b. 어르신은 그냥 돌아서 나간다
        exitDoor.active = true;
        player.Freeze(false);
    }

    IEnumerator RivalPays()
    {
        yield return Takeover();
        yield return Tray(rival);
        var served = rival;
        served.Go(exitPos.position, Bal.G("R4_RivalSpeed", 1.4f), () => queue.Done(served));
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

    void OnExit()
    {
        exitDoor.active = false;
        StartCoroutine(Exit());
    }

    IEnumerator Exit()
    {
        PlayerController.I.Freeze(true);
        AudioManager.I.Play("door_chime", exitPos.position, 0.7f);
        AudioManager.I.Play("door_glass_open", exitPos.position, 0.7f);
        GameState.I.CompleteChapter();   // 임시 T11
        yield break;
    }
}
