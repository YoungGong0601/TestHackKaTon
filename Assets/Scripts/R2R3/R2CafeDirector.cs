// R2_Cafe 진행. 2-1 도심 길을 걸어 카페로, 2-2~2-6 키오스크, 2-7 호출, 2-8 커피 2잔 받기, 언제든 2-5 알바생.
// 눈치가 다 차면 비켜나 줄 맨 뒤로 갔다가 차례가 오면 처음부터 다시 주문한다.
// 배치: queue = 같은 오브젝트의 QueueManager, kiosk = PH_Kiosk, pack = Pack_R2
// 배치: stand, kioskLook, staffPos, pickupPos = 씬 앵커
// 배치: board = PH_PickupBoard, shelf = 픽업 자리의 PH_CoffeeCups
// 배치: talkStaff, orderKiosk, takeCup = Interactable
// 배치: doorSpot = Anchor_FrontDoor, doorIn, doorOut = 문 안팎 앵커, line = NPC_Queue0..4, aside = Anchor_QueueSide0, 1(줄 옆 길)
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
    [SerializeField] Transform doorSpot;
    [SerializeField] Transform doorIn;
    [SerializeField] Transform doorOut;
    [SerializeField] List<NpcMover> line = new List<NpcMover>();
    [SerializeField] List<Transform> aside = new List<Transform>();

    static readonly List<int> NoReady = new List<int>();

    Phase phase;
    bool talking, inside;
    float doorAgain;

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
        AudioManager.I.Ambience(("amb_city_morning", 0.5f));
        kiosk.Nunchi.Configure(new NunchiRule { onLeave = pack.Leave });   // N10: 한숨만. 다 차면 Pack이 비켜난다
        Note.Set("김 대리 아이스 아메리카노 샷 추가\n이 과장 아이스 카페라떼 얼음 적게", Bal.G("R2_NoteSoft", 0.25f));
        yield return Round.Open();
        Note.Peek();
        SetPhase(Phase.Order);
    }

    // 2-1: 자동문. 다가가면 열리고, 문턱을 넘으면 소리가 안쪽으로 바뀐다
    void Update()
    {
        var p = PlayerController.I;
        if (!p) return;
        Vector3 d = p.transform.position - doorSpot.position;
        d.y = 0f;
        if (d.magnitude < Bal.G("R2_DoorOpenDist", 2.4f) && Time.time >= doorAgain)
        {
            float sec = Bal.G("R2_DoorOpenSec", 2.5f);
            queue.OpenDoor(sec);
            doorAgain = Time.time + sec;
        }
        bool nowInside = p.transform.position.z > doorSpot.position.z;
        if (nowInside == inside) return;
        inside = nowInside;
        if (inside) AudioManager.I.Ambience(("amb_restaurant", 0.3f));
        else AudioManager.I.Ambience(("amb_city_morning", 0.5f));
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
        HandRig.I.Equip(ItemId.None);
        while (true)
        {
            queue.KioskOn = true;
            player.Freeze(true);
            yield return StoreFlow.Race(this, player.WalkTo(stand.position, Bal.F("MoveSpeed", 1.9f)), 4f);
            yield return player.LookAt(kioskLook.position, Bal.G("Cine_BlendSec", 1f));
            yield return kiosk.Enter();
            queue.KioskOn = false;
            player.SetMode(PlayerController.Mode.Fps);
            HandRig.I.SetPointer(false);
            if (pack.Paid) break;
            player.Freeze(true);
            yield return Requeue();
        }
        player.Freeze(false);
        StartCoroutine(Calls());
    }

    // ---- 눈치가 다 찼을 때: 비켜나 줄 맨 뒤로, 앞사람들이 금방 주문하고 차례가 온다 ----

    // QueueManager의 Slot과 같은 자리. 줄 맨 앞은 QueuePos, 뒤로 간격만큼
    Vector3 Tail(int i)
    {
        Vector3 head = queue.QueuePos - Vector3.up * 1.5f;
        Vector3 back = head - stand.position;
        back.y = 0f;
        return head + back.normalized * (i * Bal.G("Queue_Spacing", 0.82f));
    }

    IEnumerator Requeue()
    {
        var player = PlayerController.I;
        float speed = Bal.F("MoveSpeed", 1.9f);
        foreach (var t in aside) yield return StoreFlow.Race(this, player.WalkTo(t.position, speed), 3f);
        yield return StoreFlow.Race(this, player.WalkTo(Tail(queue.Count), speed), 3f);
        yield return player.LookAt(kioskLook.position, Bal.G("Cine_BlendSec", 1f));
        while (queue.Count > 0)
        {
            queue.ShuffleForward();
            yield return null;   // 맨 앞 손님이 줄에서 빠진다
            yield return StoreFlow.Race(this, player.WalkTo(Tail(queue.Count), speed), 2f);
            yield return Served(Nearest());
        }

        // 앞사람이 끝나면 암전으로 차례가 온다. 뒤에는 새 손님이 선다
        yield return Hud.I.Fade(1f, 0.4f);
        queue.Refill();
        Vector3 to = kioskLook.position - stand.position;
        player.Teleport(stand.position, Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg);
        yield return player.LookAt(kioskLook.position, 0.01f);
        yield return Hud.I.Fade(0f, 0.4f);
    }

    // 지금 키오스크에 가장 가까운 줄 손님
    NpcMover Nearest()
    {
        NpcMover best = null;
        float dist = float.MaxValue;
        foreach (var n in line)
        {
            if (!n.isActiveAndEnabled) continue;
            float d = (n.transform.position - stand.position).sqrMagnitude;
            if (d < dist) { dist = d; best = n; }
        }
        return best;
    }

    // 앞사람은 카드로 금방 결제하고 나간다
    IEnumerator Served(NpcMover n)
    {
        if (!n) yield break;
        float walk = Bal.G("Queue_WalkSpeed", 1.25f);
        Vector3 at = kiosk.transform.position;
        yield return n.WalkTo(stand.position, walk);
        n.Face(kioskLook.position);
        float gap = Bal.G("R2_ServeTapSec", 0.4f);
        yield return new WaitForSeconds(gap);
        AudioManager.I.Play("kiosk_tap", at, 0.6f);
        yield return new WaitForSeconds(gap);
        AudioManager.I.Play("card_insert", at, 0.8f);
        yield return new WaitForSeconds(gap);
        AudioManager.I.Play("kiosk_ok", at, 0.8f);
        n.GoVia(aside, doorIn.position, walk, () =>
        {
            queue.OpenDoor(2.2f);
            n.Go(doorOut.position, walk, () => queue.Done(n));
        });
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
        AudioManager.I.Play("tray_put", null, 0.8f);
        shelf.SetActive(false);
        yield return new WaitForSeconds(0.8f);
        GameState.I.CompleteChapter();
    }
}
