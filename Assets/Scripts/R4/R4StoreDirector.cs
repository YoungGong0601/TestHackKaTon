// 4-3~4-10b: 키오스크 앞에서 버티다 지폐가 3번 튕기거나 "먼저 하세요"로 비키고, 시선을 받으며 문까지 걸어 나간다.
// 도움을 받는 분기와 성공 경로는 없다. R4_Store 씬 Director 오브젝트에 부착.
// 배치: kiosk = PH_Kiosk, pack = Pack_R4 (R4BurgerPack), queue = QueueManager
// 배치: stand = Anchor_KioskStand, kioskLook = Anchor_KioskLook, staffPos = Anchor_Staff, exitPos = Anchor_FrontDoor
// 배치: orderKiosk = Interact_Order, talkStaff = Interact_Staff, brokenKiosk = Interact_Broken, exitDoor = Interact_Exit (label 나가기)
// 배치: pool = 줄 손님 NPC_Queue0~4 (맨 앞 사람이 뒷사람), tray = Tray_Pass (쟁반, 처음 꺼짐), trayFrom, trayTo = 쟁반이 지나는 양 끝
// 배치: watchers = 문까지 가는 길 양옆 사람들 (NpcMover, 처음 꺼짐)
using System.Collections;
using UnityEngine;

public class R4StoreDirector : MonoBehaviour
{
    enum Leave { None, Bounced, GaveUp }

    [SerializeField] KioskController kiosk;
    [SerializeField] R4BurgerPack pack;
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
        choices = new[] { "먼저 하세요", "조금만요" },
        onLeave = OnGaveUp,
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
        yield return StoreFlow.Race(this, player.WalkTo(stand.position, Bal.F("MoveSpeed", 0.9f)), 4f);
        yield return player.LookAt(kioskLook.position, 0.5f);
        kiosk.Nunchi.Configure(Rule());
        atKiosk = true;
        yield return kiosk.Enter();
        atKiosk = false;
        queue.KioskOn = false;
        player.Freeze(true);
        player.SetMode(PlayerController.Mode.Fps);
        HandRig.I.SetPointer(false);
        yield return Sent();
    }

    void OnBounced()
    {
        if (leave != Leave.None) return;
        leave = Leave.Bounced;
        kiosk.Finish();
    }

    void OnGaveUp()
    {
        if (leave != Leave.None) return;
        leave = Leave.GaveUp;
        pack.Stop();
        kiosk.Finish();
    }

    // 4-10a와 선택지 "먼저 하세요". 입력 없음
    IEnumerator Sent()
    {
        var player = PlayerController.I;
        rival = Front();
        Vector3 back = rival.transform.position + Vector3.up * 1.5f;
        if (leave == Leave.Bounced)
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
