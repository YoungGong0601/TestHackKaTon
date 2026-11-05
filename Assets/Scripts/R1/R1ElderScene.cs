// 1회차 어르신 장면. 어르신은 주문을 끝내고 결제 화면에서 지폐를 넣으려다 실패한다.
// 플레이어는 카드만 꽂았다 빼 주고 지폐를 받는다. 메뉴와 화면 조작은 대신하지 않는다.
// 어르신은 픽업대 근처에서 기다리다 호출에 버거를 받고 나간다(TakeOrder).
// 배치: elder = NPC_Elder (NpcMover), head = 그 HeadPivot
// 배치: arm = NPC_Elder 의 Arm_Pivot (Visual 안 소매, 손, 반지, 손목시계), restArm = 팔 로컬 회전
// 배치: slot = PH_Kiosk 의 Slot_ic, kiosk = PH_Kiosk, stand = Anchor_KioskStand, kioskLook = Anchor_KioskLook
// 배치: door = Anchor_DoorIn, doorOut = Anchor_DoorOut, queue = QueueManager (문 열기)
// 배치: aside = Anchor_QueueSide0 (잠깐 비켜 서는 자리), waitSpot = Anchor_ElderWait
// 배치: pickupFront = Anchor_PickupFront, pickupLook = Anchor_PickupLook, bill = Elder_Bill (꺼 둔 지폐)
using System.Collections;
using UnityEngine;

public class R1ElderScene : MonoBehaviour
{
    [SerializeField] NpcMover elder;
    [SerializeField] Transform head;
    [SerializeField] Transform arm;
    [SerializeField] Vector3 restArm;
    [SerializeField] Transform slot;
    [SerializeField] Transform door;
    [SerializeField] Transform doorOut;
    [SerializeField] QueueManager queue;
    [SerializeField] KioskController kiosk;
    [SerializeField] Transform stand;
    [SerializeField] Transform kioskLook;
    [SerializeField] Transform aside;
    [SerializeField] Transform waitSpot;
    [SerializeField] Transform pickupFront;
    [SerializeField] Transform pickupLook;
    [SerializeField] Transform bill;

    static readonly (string text, string vo)[] Mutters =
    {
        ("이게 어디를 누르는 거여...", "gp_where_press"),
        ("왜 안 되지?", "gp_why1"),
        ("글씨가 왜 이렇게 작아.", "gp_read1"),
    };

    static PlayerController Player => PlayerController.I;
    static string Me => GameState.I.Profile.speakerKey;
    Vector3 ElderHead => head.position;
    float Speed => Bal.G("R1_ElderWalkSpeed", 1.1f);

    void Awake()
    {
        arm.localRotation = Quaternion.Euler(restArm);
        bill.gameObject.SetActive(false);
    }

    R1ProtoPack Pack => kiosk.GetComponentInChildren<R1ProtoPack>(true);

    // KioskController.Start가 첫 화면을 띄운 다음 프레임에 결제 화면으로 둔다
    IEnumerator Start()
    {
        yield return null;
        Pack.ElderScreen();
    }

    public IEnumerator Play()
    {
        // 줄. 걷기만 막고 시선은 자유다(T12). 혼잣말과 지폐 넣기가 같이 간다
        Player.HoldStill = true;
        float gap = Bal.G("R1_ElderMutterGapSec", 0.4f);
        elder.TryGetComponent(out NpcPose pose);
        if (pose) pose.pose = "Tap";
        foreach (var line in Mutters)
        {
            StartCoroutine(Bounce());
            yield return Hud.I.Say("elder", line.text, line.vo, -1f, ElderHead);
            yield return new WaitForSeconds(gap);
        }
        AudioManager.I.Play("sigh_m_1", null, 0.8f, 1f, clear: true);   // N14
        yield return Hud.I.Say("elder", "왜 기계가 돈을 안먹지? 이상하네", "gp_no_eat", -1f, ElderHead);
        if (pose) pose.pose = "Idle";

        // 입력 없음
        Player.Freeze(true);
        Player.HoldStill = false;
        elder.Face(Player.transform.position, 5f);
        yield return Player.LookAt(ElderHead, 0.4f);
        yield return Hud.I.Say(Me, "어르신, 이거 돈 안 들어가요.", Me + "_cant1");
        yield return Hud.I.Say("elder", "아, 그려?", "gp_really", -1f, ElderHead);
        yield return Hud.I.Say("elder", "그러면 방법이 없는겨?", "gp_nomore", -1f, ElderHead);
        yield return Hud.I.Say(Me, "제 카드로 결제해 드릴게요.", Me + "_paycard");

        // 어르신이 비켜 주고 플레이어가 대신 결제한다
        Vector3 back = Player.transform.position;
        float walk = Bal.F("MoveSpeed", 2.2f);
        elder.Go(aside.position, Speed, () => elder.Face(stand.position));
        yield return new WaitForSeconds(0.3f);
        StartCoroutine(Player.LookAt(kioskLook.position, 0.5f));
        yield return StoreFlow.Race(this, Player.WalkTo(stand.position, walk), 2f);
        yield return Player.LookAt(kioskLook.position, 0.2f);
        yield return Pack.ProxyPay(slot);

        // 플레이어가 비키고 어르신이 돌아와 지폐를 건넨다
        Vector3 toStand = stand.position - back;
        toStand.y = 0f;
        StartCoroutine(Player.LookAt(ElderHead, 0.5f));
        yield return StoreFlow.Race(this, Player.WalkTo(back, walk), 2f);
        elder.Go(back + toStand.normalized * Bal.G("R1_ElderHandDist", 0.95f), Speed);
        while (elder.Walking) yield return null;
        elder.Face(Player.transform.position, 5f);
        yield return Player.LookAt(ElderHead, 0.3f);
        HandRig.I.Equip(ItemId.Cash);
        yield return Hud.I.Say("elder", "아이고, 고맙구먼.", "gp_thanks", -1f, ElderHead);
        HandRig.I.Equip(ItemId.None);
        Pack.ShowCustomer(Pack.FirstScreen);
        elder.Go(waitSpot.position, Speed, () => elder.Face(pickupLook.position));
    }

    /// <summary>호출을 듣고 픽업대로 가서 버거를 받아 나간다.</summary>
    public void TakeOrder() => StartCoroutine(Take());

    IEnumerator Take()
    {
        yield return elder.WalkTo(pickupFront.position, Speed);
        elder.Face(pickupLook.position);
        yield return new WaitForSeconds(0.6f);
        AudioManager.I.Play("bag_rustle", pickupLook.position, 0.5f);
        elder.ShowBag();
        elder.Go(door.position, Speed, () =>
        {
            queue.OpenDoor(2.2f);
            elder.Go(doorOut.position, Speed, elder.Hide);
        });
    }

    // 지폐가 틈에 들어가다 밀려 나온다. 끝나면 꺼서 공중에 남지 않는다
    IEnumerator Bounce()
    {
        const float Sec = 0.6f;
        Vector3 outward = kiosk.Out;
        bill.rotation = Quaternion.LookRotation(Vector3.up, outward);
        bill.gameObject.SetActive(true);
        bool rejected = false;
        for (float t = 0f; t < Sec; t += Time.deltaTime)
        {
            float k = t / Sec;
            bill.position = slot.position + outward * (0.14f - Mathf.Sin(k * Mathf.PI) * 0.1f);
            if (!rejected && k >= 0.5f)
            {
                rejected = true;
                AudioManager.I.Play("card_reject", slot.position, 0.8f);
                AudioManager.I.Play("kiosk_error", slot.position, 0.5f);
            }
            yield return null;
        }
        bill.gameObject.SetActive(false);
    }
}
