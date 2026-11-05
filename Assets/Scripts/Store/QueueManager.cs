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
    Quaternion doorBase;

    /// <summary>키오스크 조작 중에만 줄이 늘어난다.</summary>
    public bool KioskOn { get; set; }
    public int Count => queue.Count;
    public Vector3 QueuePos => Slot(0) + Vector3.up * 1.5f;

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
        return queueFront.position + Back * (i * Bal.G("Queue_Spacing", 0.82f));
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

    void Update()
    {
        float dt = Time.deltaTime;

        if (doorWant != 0f && Time.time > doorUntil) doorWant = 0f;
        doorA = StoreFlow.Damp(doorA, doorWant, doorWant != 0f ? 5f : 3f, dt);
        doorPivot.localRotation = doorBase * Quaternion.Euler(0f, doorA * Mathf.Rad2Deg, 0f);

        // 줄은 게이지를 따라 길어진다
        if ((KioskOn || (nunchi != null && nunchi.Running)) && nunchi != null)
        {
            int max = Bal.I("Queue_Max", 4);
            int want = 1 + Mathf.FloorToInt(nunchi.Value / Mathf.Max(Bal.G("Nunchi_Max", 100f), 1f) * max);
            nextArrive -= dt;
            if (nextArrive <= 0f && queue.Count < Mathf.Min(want, max) && pool.Count > 0)
            {
                nextArrive = Bal.G("Queue_GrowGapSec", 3f);
                Arrive();
            }
        }
    }

    public void OpenDoor(float sec = 1.6f)
    {
        doorWant = Bal.G("Door_StoreOpenAngle", 1.15f);
        doorUntil = Time.time + sec;
        AudioManager.I.Play("door_chime", doorPivot.position + Vector3.up * 2f, 0.55f);
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

    /// <summary>주문을 마친 뒤 줄이 앞으로 간다. 플레이어가 키오스크 앞을 비울 때까지 맨 앞 손님은 기다리며 재촉한다.</summary>
    public void ShuffleForward()
    {
        StartCoroutine(NextUp());
    }

    bool PlayerAtStand
    {
        get
        {
            Vector3 d = PlayerController.I.transform.position - stand.position;
            d.y = 0f;
            return d.magnitude < Bal.G("Queue_MoveClearDist", 0.9f);
        }
    }

    IEnumerator NextUp()
    {
        float wait = Bal.G("Queue_MoveWaitSec", 6f);
        while (queue.Count > 0 && PlayerAtStand)
        {
            wait -= Time.deltaTime;
            if (wait <= 0f)
            {
                NpcMover front = queue[0];
                front.Face(PlayerController.I.transform.position);
                Vector3 head = front.transform.position + Vector3.up * 1.5f;
                Hud.I.Say(null, "비키세요.", "y_move2", -1f, head);
                wait = Bal.G("Queue_MoveAgainSec", 7f);
            }
            yield return null;
        }
        if (queue.Count == 0) yield break;
        NpcMover n = queue[0];
        queue.RemoveAt(0);
        n.Go(stand.position, WalkSpeed, () => n.Face(kioskLook.position));
        CloseUp();
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
