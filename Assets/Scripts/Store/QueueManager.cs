// 줄 손님, 픽업 대기 손님, 드나드는 문. Store 씬 Director 오브젝트에 부착.
// 좌표는 HTML판 값의 z에 -1을 곱한 Unity 좌표. L.KX -0.6, L.KZ -3.82 기준.
// 배치: kiosk = PH_Kiosk (KioskController)
// 배치: nunchi = PH_Kiosk 쪽 NunchiSystem
// 배치: stand = Anchor_KioskStand (-0.6, 0, 3.08) 키오스크 앞 자리
// 배치: queueFront = Anchor_QueueFront (-0.6, 0, 1.77) 줄 맨 앞, 뒷사람은 stand 반대쪽으로 간격만큼 뒤에 선다
// 배치: kioskLook = Anchor_KioskLook (-0.6, 1.32, 3.82) 키오스크 화면
// 배치: doorIn = Anchor_DoorIn (1.4, 0, -3.1) 문 안쪽
// 배치: doorOut = Anchor_DoorOut (1.4, 0, -4.7) 문 바깥
// 배치: doorPivot = PH_Door_Glass 안의 DoorPivot (Store 씬은 시작할 때 열려 있다가 닫힘)
// 배치: pickupFront = Anchor_PickupFront (-2.2, 0, -0.85) 손님이 받는 자리
// 배치: pickupLook = Anchor_PickupLook (-2.92, 1.08, -0.85) 픽업 대
// 배치: boardLook = Anchor_Board (-2.72, 2.62, -0.9) 대기 손님이 보는 전광판
// 배치: pool = NPC_Queue0..4 (NpcMover 5개, 어디 두어도 시작할 때 숨겨짐)
// 배치: waiters = NPC_Wait0 (-1.72, 0, 0.25), NPC_Wait1 (-1.5, 0, -0.3), NPC_Wait2 (-1.1, 0, -2.4) 받는 자리와 나가는 길을 비운 자리
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class QueueManager : MonoBehaviour
{
    [SerializeField] KioskController kiosk;
    [SerializeField] NunchiSystem nunchi;
    [SerializeField] Transform stand;
    [SerializeField] Transform queueFront;
    [SerializeField] Transform kioskLook;
    [SerializeField] Transform doorIn;
    [SerializeField] Transform doorOut;
    [SerializeField] Transform doorPivot;
    [SerializeField] Transform pickupFront;
    [SerializeField] Transform pickupLook;
    [SerializeField] Transform boardLook;
    [SerializeField] List<NpcMover> pool = new List<NpcMover>();
    [SerializeField] List<NpcMover> waiters = new List<NpcMover>();

    readonly List<NpcMover> queue = new List<NpcMover>();

    float nextArrive;
    float doorA, doorWant, doorUntil;
    bool serving;
    Quaternion doorBase;

    /// <summary>키오스크 조작 중에만 줄이 늘어난다.</summary>
    public bool KioskOn { get; set; }
    public int Count => queue.Count;
    [SerializeField] bool wideLine;   // 카페처럼 사람이 낑기는 곳은 R2_QueueSpacing을 쓴다

    public float Spacing => wideLine ? Bal.G("R2_QueueSpacing", 1f) : Bal.G("Queue_Spacing", 0.82f);

    public Vector3 QueuePos => Slot(0) + Vector3.up * 1.5f;

    /// <summary>줄에서 이 성별인 맨 앞사람의 머리 자리. 없으면 null.</summary>
    public Vector3? VoicePos(bool female)
    {
        foreach (NpcMover n in queue)
            if (n.TryGetComponent(out NpcPose pose) && pose.Female == female)
                return n.transform.position + Vector3.up * 1.5f;
        return null;
    }

    float WalkSpeed => Bal.G("Queue_WalkSpeed", 1.25f);
    float WaiterSpeed => Bal.G("Queue_WaiterSpeed", 1.2f);
    Vector3 Back
    {
        get
        {
            Vector3 d = queueFront.position - stand.position;
            d.y = 0f;
            return d.normalized;
        }
    }

    Vector3 Slot(int i)
    {
        return queueFront.position + Back * (i * Spacing);
    }

    void Awake()
    {
        doorBase = doorPivot.localRotation;
        foreach (NpcMover n in pool) n.Hide();
        foreach (NpcMover n in waiters) n.Face(boardLook.position);
    }

    void Start()
    {
        doorA = Bal.G("Door_StoreOpenAngle", 1.15f);
        nextArrive = Bal.G("Queue_FirstArrive", 5f);
    }

    void OnEnable() => nunchi.Sorried += Sorry;
    void OnDisable() => nunchi.Sorried -= Sorry;

    /// <summary>사과: 앞사람은 고개를 까딱, 뒷사람은 고개를 살짝 돌림.</summary>
    public void Sorry()
    {
        for (int i = 0; i < queue.Count; i++)
            queue[i].React(i == 0);
    }

    void Update()
    {
        float dt = Time.deltaTime;

        if (doorWant != 0f && Time.time > doorUntil)
        {
            doorWant = 0f;
            AudioManager.I.Play("door_handle", doorPivot.position, 0.2f);
        }
        doorA = StoreFlow.Damp(doorA, doorWant, doorWant != 0f ? 5f : 3f, dt);
        doorPivot.localRotation = doorBase * Quaternion.Euler(0f, doorA * Mathf.Rad2Deg, 0f);

        // 줄은 게이지를 따라 길어진다
        if ((KioskOn || (nunchi != null && nunchi.Running)) && nunchi != null)
        {
            int max = Bal.I("Queue_Max", 4);
            int want = Mathf.Max(Bal.I("Queue_MinBack", 2), 1 + Mathf.FloorToInt(nunchi.Value / Mathf.Max(Bal.G("Nunchi_Max", 100f), 1f) * max));
            nextArrive -= dt;
            if (nextArrive <= 0f && queue.Count < Mathf.Min(want, max) && pool.Count > 0)
            {
                nextArrive = Bal.G("Queue_GrowGapSec", 3f);
                Arrive();
            }
        }
    }

    // 이미 열렸거나 열리는 중이면 시간만 늘린다. 소리는 닫혀 있던 문이 열릴 때 한 번만 난다
    public void OpenDoor(float sec = 1.6f)
    {
        bool shut = doorWant == 0f && doorA < 0.03f;
        doorWant = Bal.G("Door_StoreOpenAngle", 1.15f);
        doorUntil = Mathf.Max(doorUntil, Time.time + sec);
        if (shut) AudioManager.I.Play("door_chime", doorPivot.position + Vector3.up * 2f, 0.55f);
    }

    /// <summary>주문을 끝내고 나간 손님을 풀로 돌린다.</summary>
    public void Done(NpcMover n)
    {
        queue.Remove(n);
        if (n.TryGetComponent(out NpcPose pose)) pose.pose = "Idle";
        n.Hide();
        if (!pool.Contains(n)) pool.Add(n);
    }

    /// <summary>줄이 비지 않게 최소 인원까지 바로 세운다.</summary>
    public void Refill()
    {
        int min = Bal.I("Queue_MinBack", 2);
        while (queue.Count < min && pool.Count > 0)
        {
            NpcMover n = TakeFromPool();
            n.Place(Slot(queue.Count));
            n.Show();
            queue.Add(n);
            Settle(n);
        }
    }

    void Arrive()
    {
        NpcMover n = TakeFromPool();
        if (!n) return;
        n.Place(doorOut.position);
        n.Show();
        queue.Add(n);
        OpenDoor();
        n.Go(doorIn.position, WalkSpeed, () =>
        {
            if (!queue.Contains(n)) return;
            n.Go(Slot(queue.IndexOf(n)), WalkSpeed, () => Settle(n));
        });
    }

    NpcMover TakeFromPool()
    {
        if (pool.Count == 0) return null;
        NpcMover n = pool[0];
        pool.RemoveAt(0);
        return n;
    }

    void Settle(NpcMover n)
    {
        n.Face(kioskLook.position);
    }

    void CloseUp()
    {
        for (int i = 0; i < queue.Count; i++)
        {
            NpcMover q = queue[i];
            q.Go(Slot(i), WalkSpeed, () => Settle(q));
        }
    }

    /// <summary>주문을 마친 뒤 줄이 앞으로 간다. 플레이어가 서 있어도 멈추지 않는다.</summary>
    public void ShuffleForward()
    {
        StartCoroutine(NextUp());
    }

    IEnumerator NextUp()
    {
        if (queue.Count == 0) yield break;
        NpcMover n = queue[0];
        queue.RemoveAt(0);
        n.Go(stand.position, WalkSpeed, () =>
        {
            n.Face(kioskLook.position);
            if (n.TryGetComponent(out NpcPose pose)) pose.pose = "Tap";
        });
        CloseUp();
    }

    // ---- 다음 손님: 플레이어가 키오스크 앞 구역을 벗어난 뒤에만 출발한다 ----

    /// <summary>손님이 기계를 쓰는 중. 플레이어는 이때 키오스크를 쓰지 못한다.</summary>
    public bool Serving { get; private set; }

    bool PlayerNear(float dist)
    {
        var p = PlayerController.I;
        if (!p) return false;
        Vector3 d = p.transform.position - stand.position;
        d.y = 0f;
        return d.magnitude < dist;
    }

    /// <summary>줄 맨 앞 손님부터 차례로 키오스크를 쓰고 나간다. 이미 돌고 있으면 그대로 둔다.</summary>
    public void ServeWhenClear(IEnumerable<Transform> via = null)
    {
        if (!serving) StartCoroutine(ServeLoop(via));
    }

    IEnumerator ServeLoop(IEnumerable<Transform> via)
    {
        serving = true;
        while (queue.Count > 0)
        {
            while (PlayerNear(Bal.G("Queue_ClearDist", 1.1f))) yield return null;
            NpcMover n = queue[0];
            queue.RemoveAt(0);
            CloseUp();
            yield return UseKiosk(n);
            Leave(n, via);
            yield return new WaitForSeconds(Bal.G("Queue_NextGapSec", 1f));
        }
        if (kiosk && kiosk.Pack) kiosk.Pack.ShowCustomer(kiosk.Pack.FirstScreen);
        serving = false;
    }

    /// <summary>손님이 키오스크 앞으로 가서 실제 화면을 넘기며 쓴다. 자리에 플레이어가 있으면 비킬 때까지 멈춘다.</summary>
    public IEnumerator UseKiosk(NpcMover n)
    {
        float block = Bal.G("Queue_StandBlockDist", 0.7f);
        n.Go(stand.position, WalkSpeed);
        while (n.Walking)
        {
            if (PlayerNear(block))
            {
                n.Stop();
                while (PlayerNear(block)) yield return null;
                n.Go(stand.position, WalkSpeed);
            }
            yield return null;
        }
        n.Face(kioskLook.position);
        n.TryGetComponent(out NpcPose pose);
        if (pose) pose.pose = "Tap";
        Serving = true;
        yield return kiosk.CustomerUse();
        Serving = false;
        if (pose) pose.pose = "Idle";
    }

    void Leave(NpcMover n, IEnumerable<Transform> via)
    {
        System.Action outside = () =>
        {
            OpenDoor(2.2f);
            n.Go(doorOut.position, WalkSpeed, () => Done(n));
        };
        if (via != null) n.GoVia(via, doorIn.position, WalkSpeed, outside);
        else n.Go(doorIn.position, WalkSpeed, outside);
    }

    /// <summary>문을 이 각도로 열린 채 넘겨받는다. 곧 닫힌다.</summary>
    public void SetDoor(float angle)
    {
        doorA = angle;
        doorWant = 0f;
    }

    /// <summary>대기 손님 한 명이 픽업 대로 가서 받고 나간다. taken은 봉투를 집는 순간 불린다.</summary>
    public IEnumerator WaiterPickup(System.Action taken)
    {
        if (waiters.Count == 0)
        {
            yield return new WaitForSeconds(3f);
            taken();
            yield break;
        }
        NpcMover n = waiters[0];
        waiters.RemoveAt(0);
        yield return new WaitForSeconds(0.6f);
        yield return n.WalkTo(pickupFront.position, WaiterSpeed);
        n.Face(pickupLook.position);
        yield return new WaitForSeconds(0.7f);
        AudioManager.I.Play("bag_rustle", pickupLook.position, 0.5f);
        taken();
        n.ShowBag();
        n.Go(doorIn.position, WaiterSpeed, () =>
        {
            OpenDoor(2.2f);
            n.Go(doorOut.position, WaiterSpeed, n.Hide);
        });
    }
}
