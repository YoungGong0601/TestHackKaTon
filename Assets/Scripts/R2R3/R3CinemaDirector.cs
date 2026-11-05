// R3_Cinema 진행. 3-1~3-9 키오스크, 언제든 3-6 알바생, 3-7 재촉, 실패와 선택지.
// 배치: queue = 같은 오브젝트의 QueueManager, kiosk = PH_Kiosk, pack = Pack_R3
// 배치: stand, kioskLook = Store 씬 앵커, doorLook = 나가는 쪽을 보는 곳
// 배치: buyer = 표를 금방 사는 뒷사람(NpcMover, 시작할 때 숨김), buyerFrom = 줄 맨 앞 자리
// 배치: talkStaff, orderKiosk = Interactable
using System.Collections;
using UnityEngine;

public class R3CinemaDirector : MonoBehaviour
{
    enum Phase { Intro, Order, Kiosk, End }

    [SerializeField] QueueManager queue;
    [SerializeField] KioskController kiosk;
    [SerializeField] R3CinemaPack pack;
    [SerializeField] Transform stand;
    [SerializeField] Transform kioskLook;
    [SerializeField] Transform doorLook;
    [SerializeField] NpcMover buyer;
    [SerializeField] Transform buyerFrom;
    [SerializeField] Interactable talkStaff;
    [SerializeField] Interactable orderKiosk;

    Phase phase;
    bool talking, left;

    void OnEnable()
    {
        talkStaff.onUse.AddListener(OnTalk);
        orderKiosk.onUse.AddListener(OnOrder);
        kiosk.StaffCalled += OnStaffCalled;
    }

    void OnDisable()
    {
        talkStaff.onUse.RemoveListener(OnTalk);
        orderKiosk.onUse.RemoveListener(OnOrder);
        kiosk.StaffCalled -= OnStaffCalled;
    }

    IEnumerator Start()
    {
        SetPhase(Phase.Intro);
        buyer.Hide();
        AudioManager.I.Ambience(("amb_restaurant", 0.25f));
        kiosk.Nunchi.Configure(new NunchiRule
        {
            mid = new[] { "아, 좀 빨리요." },
            high = new[] { "영화 시작하는데요." },
            choices = new[] { "다음에 볼게요", "조금만요" },
            onLeave = OnLeave,
        });
        yield return Round.Open("영화표를 사세요.");
        SetPhase(Phase.Order);
    }

    void SetPhase(Phase p)
    {
        phase = p;
        orderKiosk.active = p == Phase.Order;
        talkStaff.active = p == Phase.Order && !talking;
    }

    // ---- 3-6 ----

    void OnTalk() { if (!talking) StartCoroutine(Talk()); }
    void OnStaffCalled() { if (!talking) StartCoroutine(Talk()); }

    IEnumerator Talk()
    {
        talking = true;
        talkStaff.active = false;
        yield return Hud.I.Say(null, "거기 다 나와 있어요.", "staff_cinema");
        talking = false;
        SetPhase(phase);
    }

    // ---- 키오스크 ----

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
        yield return StoreFlow.Race(this, player.WalkTo(stand.position, Bal.F("MoveSpeed", 1.5f)), 4f);
        yield return player.LookAt(kioskLook.position, 0.5f);
        yield return kiosk.Enter();
        queue.KioskOn = false;
        SetPhase(Phase.End);
        player.Freeze(true);
        if (left) yield return Buyer();
        else yield return new WaitForSeconds(0.8f);
        GameState.I.CompleteChapter();
    }

    // ---- 선택지 "다음에 볼게요" ----

    void OnLeave()
    {
        left = true;
        pack.Leave();
    }

    IEnumerator Buyer()
    {
        var player = PlayerController.I;
        buyer.Place(buyerFrom.position);
        buyer.Show();
        buyer.Go(stand.position, Bal.G("Queue_WalkSpeed", 1.25f), () => buyer.Face(kioskLook.position));
        yield return player.LookAt(stand.position + Vector3.up * 1.4f, 0.6f);
        while (buyer.Walking) yield return null;
        for (int i = 0; i < 3; i++)
        {
            AudioManager.I.Play("kiosk_tap", kioskLook.position, 0.6f);
            yield return new WaitForSeconds(0.3f);
        }
        AudioManager.I.Play("kiosk_ok", kioskLook.position, 0.7f);
        AudioManager.I.Play("receipt_print", kioskLook.position, 0.6f);
        yield return new WaitForSeconds(0.9f);
        yield return player.LookAt(doorLook.position, 0.8f);
    }
}
