// 4-3~4-10b: 게이지가 다 차면 줄 맨 뒤로 갔다가 다시 시도하고, 지폐가 3번 튕기면 시선을 받으며 문까지 걸어 나간다. 가게를 나가는 길은 이것뿐이다.
// 도움을 받는 분기와 성공 경로는 없다. R4_Store 씬 Director 오브젝트에 부착.
// 배치: kiosk = PH_Kiosk, pack = KioskCanvas (R4ProtoPack), queue = QueueManager
// 배치: stand = Anchor_KioskStand, kioskLook = Anchor_KioskLook, staffPos = Anchor_Staff, exitPos = Anchor_FrontDoor
// 배치: orderKiosk = Interact_Order, talkStaff = Interact_Staff, brokenKiosk = Interact_Broken, exitDoor = Interact_Exit (label 나가기)
// 배치: pool = 줄 손님 NPC_Queue0~4 (맨 앞 사람이 뒷사람), tray = Tray_Pass (쟁반, 처음 꺼짐), trayFrom, trayTo = 쟁반이 지나는 양 끝
// 배치: watchers = 문까지 가는 길 양옆 사람들 (NpcMover, 처음 꺼짐)
using System.Collections;
using UnityEngine;

public class R4StoreDirector : MonoBehaviour
{
    enum Leave { None, Bounced, Back }

    [SerializeField] KioskController kiosk;
    [SerializeField] R4ProtoPack pack;
    [SerializeField] QueueManager queue;
    [SerializeField] R4Gaze gaze;
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
    [SerializeField] NpcMover[] watchers;

    Leave leave;
    NpcMover rival;
    bool talking, muttering, ordered, atKiosk;
    int retries;

    static string Me => GameState.I.Profile.speakerKey;
    static Hud Ui => Hud.I;

    void Awake()
    {
        exitDoor.active = false;
        if (tray) tray.SetActive(false);
        foreach (var w in watchers) w.gameObject.SetActive(false);
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
        if (Wallet.I) Wallet.I.NoteMissed -= OnNoteMissed;
    }

    IEnumerator Start()
    {
        AudioManager.I.Ambience(("amb_restaurant", 0.36f), ("amb_kitchen", 0.2f));
        yield return Round.Open();
        Wallet.I.NoteMissed += OnNoteMissed;
    }

    void OnNoteMissed() => Ui.Say(null, "뭐라고 썼더라.", Me + "_note");

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
            yield return StoreFlow.Race(this, player.WalkTo(stand.position, Bal.F("MoveSpeed", 0.9f)), 4f);
            yield return player.LookAt(kioskLook.position, 0.5f);
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
        yield return StoreFlow.Race(this, player.WalkTo(tail + Vector3.right * 0.8f, Bal.F("MoveSpeed", 0.9f)), Bal.G("R4_RequeueWalkSec", 3f));
        yield return player.LookAt(kioskLook.position, 0.5f);
        yield return Takeover();
        yield return Tray();
        rival.Go(exitPos.position, Bal.G("R4_RivalSpeed", 1.4f), rival.Hide);
        yield return new WaitForSeconds(Bal.G("R4_RequeueWaitSec", 2f));
    }

    void OnBounced()
    {
        if (leave != Leave.None) return;
        leave = Leave.Bounced;
        kiosk.Finish();
    }

    void OnFull()
    {
        if (leave != Leave.None) return;
        leave = Leave.Back;
        pack.Stop();
        kiosk.Finish();
    }

    // 4-10a. 입력 없음
    IEnumerator Sent()
    {
        var player = PlayerController.I;
        rival = Front();
        Vector3 back = rival.transform.position + Vector3.up * 1.5f;
        {
            yield return player.LookAt(back, 0.7f);
            yield return Ui.Say(null, "그거 지폐 안 받아요.", "a20_nobill", 2f, rival.transform.position + Vector3.up * 1.5f, 1f, true);
            yield return new WaitForSeconds(0.4f);
            yield return Ui.Say(null, "그려? 어쩔 수 없구만...", Me + "_giveup", 2.4f);
        }

        // 임시 T13: 슬픈 얼굴은 보이지 않고 시선을 내리고 돌아선다
        yield return player.TurnTo(player.Yaw, Bal.G("R4_SadPitch", -28f), Bal.G("R4_SadLookSec", 1.2f));
        yield return player.TurnTo(player.Yaw + 180f, Bal.G("R4_SadPitch", -28f), Bal.G("R4_SadTurnSec", 1.6f));

        StartCoroutine(Takeover());
        yield return Tray();
        yield return player.TurnTo(player.Yaw, 0f, 0.8f);

        // 4-10b
        foreach (var w in watchers) w.gameObject.SetActive(true);
        foreach (var npc in FindObjectsByType<NpcMover>(FindObjectsSortMode.None))
            if (npc.gameObject.scene == gameObject.scene) gaze.Add(npc);
        exitDoor.active = true;
        player.Freeze(false);
        StartCoroutine(LookAround());
    }

    // 4-10b 임시 타이밍: 문까지 절반쯤 걸으면 입력 없이 주위를 한 번 둘러본다. 멈추면 그대로 기다린다
    IEnumerator LookAround()
    {
        var player = PlayerController.I;
        float start = Flat(player.transform.position, exitPos.position);
        while (Flat(player.transform.position, exitPos.position) > start * 0.5f) yield return null;
        player.Freeze(true);
        float yaw = player.Yaw, pitch = player.Pitch, arc = Bal.G("R4_LookAroundDeg", 75f), sec = Bal.G("R4_LookAroundSec", 3f);
        yield return player.TurnTo(yaw - arc, pitch, sec * 0.3f);
        yield return player.TurnTo(yaw + arc, pitch, sec * 0.45f);
        yield return player.TurnTo(yaw, pitch, sec * 0.25f);
        player.Freeze(false);
    }

    static float Flat(Vector3 a, Vector3 b)
    {
        a.y = b.y = 0f;
        return Vector3.Distance(a, b);
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

    // 뒷사람이 카드로 금방 결제한다
    IEnumerator Takeover()
    {
        Vector3 at = kiosk.transform.position;
        yield return rival.WalkTo(stand.position, Bal.G("R4_RivalSpeed", 1.4f));
        yield return new WaitForSeconds(0.4f);
        AudioManager.I.Play("kiosk_tap", at, 0.6f);
        yield return new WaitForSeconds(0.35f);
        AudioManager.I.Play("kiosk_tap", at, 0.6f);
        yield return new WaitForSeconds(0.35f);
        AudioManager.I.Play("card_insert", at, 0.8f);
        yield return new WaitForSeconds(0.5f);
        AudioManager.I.Play("kiosk_ok", at, 0.8f);
    }

    IEnumerator Tray()
    {
        if (!tray) yield break;
        tray.SetActive(true);
        float sec = Bal.G("R4_TraySec", 2.4f);
        AudioManager.I.Play("tray_put", trayFrom.position, 0.4f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            tray.transform.position = Vector3.Lerp(trayFrom.position, trayTo.position, t);
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
