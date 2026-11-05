// 줄 손님, 픽업 대기 손님, 드나드는 문, 눈치 폭발 끼어들기. Store 씬 Director 오브젝트에 부착.
// 좌표는 HTML판 값의 z에 -1을 곱한 Unity 좌표. L.KX -0.6, L.KZ -3.82 기준.
// 배치: kiosk = PH_Kiosk (KioskController)
// 배치: nunchi = PH_Kiosk 쪽 NunchiSystem
// 배치: stand = Anchor_KioskStand (-0.6, 0, 3.08) 키오스크 앞 자리
// 배치: queueFront = Anchor_QueueFront (-0.6, 0, 1.77) 줄 맨 앞, 뒷사람은 stand 반대쪽으로 간격만큼 뒤에 선다
// 배치: kioskLook = Anchor_KioskLook (-0.6, 1.32, 3.82) 키오스크 화면
// 배치: doorIn = Anchor_DoorIn (1.4, 0, -3.1) 문 안쪽
// 배치: doorOut = Anchor_DoorOut (1.4, 0, -4.7) 문 바깥
// 배치: doorPivot = PH_Door_Glass 안의 DoorPivot (Store 씬은 시작할 때 열려 있다가 닫힘)
// 배치: yoExit = Anchor_YoExit (-0.15, 0, -1.55) 끼어든 사람이 물러나는 자리
// 배치: yoRoute = Anchor_QueueSide0 (-1.25, 0, 2.6), Anchor_QueueSide1 (-1.2, 0, -0.75) 줄 왼쪽으로 돌아 나가는 길
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
    [SerializeField] Transform yoExit;
    [SerializeField] List<Transform> yoRoute = new List<Transform>();
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
    public bool Blowing { get; private set; }
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

    void OnEnable()
    {
        kiosk.Blowup += OnBlowup;
        nunchi.Sorried += Sorry;
    }

    void OnDisable()
    {
        kiosk.Blowup -= OnBlowup;
        nunchi.Sorried -= Sorry;
    }

    void Update()
    {
        float dt = Time.deltaTime;

        if (doorWant != 0f && Time.time > doorUntil) doorWant = 0f;
        doorA = StoreFlow.Damp(doorA, doorWant, doorWant != 0f ? 5f : 3f, dt);
        doorPivot.localRotation = doorBase * Quaternion.Euler(0f, doorA * Mathf.Rad2Deg, 0f);

        if (KioskOn && !Blowing)
        {
            nextArrive -= dt;
            if (nextArrive <= 0f && queue.Count < Bal.I("Queue_Max", 4) && pool.Count > 0)
            {
                nextArrive = Random.Range(Bal.G("Queue_ArriveMin", 17f), Bal.G("Queue_ArriveMax", 25f));
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

    /// <summary>사과: 앞사람은 고개를 까딱, 뒷사람은 고개를 살짝 돌림.</summary>
    public void Sorry()
    {
        for (int i = 0; i < queue.Count; i++)
            queue[i].React(i == 0);
    }

    void OnBlowup()
    {
        if (Blowing) return;
        StartCoroutine(BlowupRun());
    }

    /// <summary>눈치 폭발: 맨 앞 사람이 밀고 들어와 10초 만에 끝내는 걸 줄 맨 뒤에서 본다.</summary>
    IEnumerator BlowupRun()
    {
        Blowing = true;
        var player = PlayerController.I;

        if (queue.Count == 0)
        {
            NpcMover p = TakeFromPool();
            if (p)
            {
                p.Place(Slot(0));
                p.Show();
                queue.Add(p);
            }
        }
        NpcMover yo = null;
        if (queue.Count > 0)
        {
            yo = queue[0];
            queue.RemoveAt(0);
        }
        player.AddShake(0.7f);
        nunchi.Value = Bal.G("Nunchi_BlowupWatch", 62f); // 눈앞은 맑아지고 민망함만 남는다

        bool yoDone = yo == null;
        if (yo) StartCoroutine(YoRun(yo, () => yoDone = true));

        // 옆으로 밀려나 맨 뒤로
        Vector3 tail = Slot(queue.Count);
        CloseUp();
        Coroutine aside = StartCoroutine(player.WalkTo(stand.position + Vector3.right * 1.15f + Back * 0.5f, Bal.F("PushedAsideSpeed", 1.5f)));
        yield return new WaitForSeconds(0.5f);
        StopCoroutine(aside);
        yield return StoreFlow.Race(this, player.WalkTo(tail + Vector3.right * 1.2f + Back * 0.3f, Bal.F("PushedBackSpeed", 1.7f)), 3.2f);
        yield return StoreFlow.Race(this, player.LookAt(kioskLook.position, 0.8f), 0.9f);
        while (!yoDone) yield return null;
        yield return Hud.I.Fade(1f, 0.45f);

        // 그사이 앞사람들도 끝냈다
        if (yo)
        {
            yo.Hide();
            pool.Add(yo);
        }
        foreach (NpcMover n in queue)
        {
            n.Hide();
            pool.Add(n);
        }
        queue.Clear();
        nextArrive = Bal.G("Queue_ArriveAfterBlowup", 2.5f);
        Blowing = false;
    }

    IEnumerator YoRun(NpcMover yo, System.Action done)
    {
        Vector3 kioskFloor = kioskLook.position;
        yield return StoreFlow.Race(this, yo.WalkTo(stand.position, Bal.G("Queue_YoSpeed", 2.3f)), 3.4f);
        yo.Place(stand.position);
        yo.Face(kioskFloor);
        yield return new WaitForSeconds(Bal.G("Queue_YoTapSec", 4.2f));
        AudioManager.I.Play("card_insert", kioskFloor, 0.6f);
        yield return new WaitForSeconds(Bal.G("Queue_YoCardSec", 1f));
        AudioManager.I.Play("receipt_print", kioskFloor, 0.6f);
        yield return new WaitForSeconds(Bal.G("Queue_YoPrintSec", 1.3f));
        AudioManager.I.Play("paper_tear", kioskFloor, 0.6f);
        Hud.I.Say(null, "{y:10초}", null, 2.2f);
        yo.GoVia(yoRoute, yoExit.position, Bal.G("Queue_YoLeaveSpeed", 1.5f));
        yield return new WaitForSeconds(2.2f);
        done();
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
        int nag = 0;
        while (queue.Count > 0 && PlayerAtStand)
        {
            wait -= Time.deltaTime;
            if (wait <= 0f)
            {
                NpcMover front = queue[0];
                front.Face(PlayerController.I.transform.position);
                Vector3 head = front.transform.position + Vector3.up * 1.5f;
                if (nag++ == 0) Hud.I.Say("yM", "할아버지 뭐 해요.", "y_move1", -1f, head);
                else Hud.I.Say("yM", "비키세요.", "y_move2", -1f, head);
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
