// 1-5, 1-6 앞 어르신 장면. 1-6 길이는 R1_ElderSceneSec. 아래 시각은 15초 기준이고 비율로 늘고 준다.
// 얼굴을 보이지 않고 고개를 숙여 돌아서는 것으로 슬픔을 보인다(T13). 뒷모습은 Cine.BackShot, E-1과 같은 구도.
// 배치: elder = NPC_Elder (NpcMover), head = 그 HeadPivot
// 배치: arm = NPC_Elder 의 Arm_Pivot (Visual 안 소매, 손, 반지, 손목시계), restArm, reachArm = 팔 로컬 회전
// 배치: bill = 지폐 상자(팔 손 끝 자식), slot = PH_Kiosk 의 Slot_ic
// 배치: door = Anchor_DoorIn, doorOut = Anchor_DoorOut, queue = QueueManager (문 열기)
// 배치: watchers = 함께 바라보는 NPC들
using System.Collections;
using UnityEngine;

public class R1ElderScene : MonoBehaviour
{
    [SerializeField] NpcMover elder;
    [SerializeField] Transform head;
    [SerializeField] Transform arm;
    [SerializeField] Vector3 restArm;
    [SerializeField] Vector3 reachArm;
    [SerializeField] Transform bill;
    [SerializeField] Transform slot;
    [SerializeField] Transform door;
    [SerializeField] Transform doorOut;
    [SerializeField] QueueManager queue;
    [SerializeField] NpcMover[] watchers = new NpcMover[0];

    float k;
    bool watching, following;
    float[] watcherYaw;
    Vector3 billHome;
    Quaternion headRest;

    static PlayerController Player => PlayerController.I;
    Vector3 ElderHead => head.position;

    void Awake()
    {
        billHome = bill.localPosition;
        headRest = head.localRotation;
        arm.localRotation = Quaternion.Euler(restArm);
        watcherYaw = new float[watchers.Length];
    }

    WaitForSeconds Wait(float sec) => new WaitForSeconds(sec * k);

    public IEnumerator Play()
    {
        float total = Bal.G("R1_ElderSceneSec", 15f);
        k = total / 15f;

        // 1-5 줄. 걷기만 막고 시선은 자유다(T12). 장면 길이에 넣지 않는다
        Player.HoldStill = true;
        yield return new WaitForSeconds(0.6f);
        Hud.I.Say(null, "왜 안 되지?", "gp_why1", -1f, ElderHead);
        yield return new WaitForSeconds(2f);
        AudioManager.I.Play("sigh_m_1", null, 0.8f, 1f, clear: true);   // N14
        yield return new WaitForSeconds(0.8f);

        // 1-6 입력 없음. 여기서부터 R1_ElderSceneSec
        float t0 = Time.time;
        Player.Freeze(true);
        Player.HoldStill = false;
        yield return Player.LookAt(slot.position, 0.6f * k);
        int bounces = Bal.I("Cash_BounceCount", 3);
        for (int i = 0; i < bounces; i++) yield return Bounce();

        yield return Hud.I.Say(null, "그거 지폐 안 받아요.", GameState.I.Profile.speakerKey + "_nobill", 1.5f * k);
        elder.Face(Player.transform.position, 5f);
        yield return Player.LookAt(ElderHead, 0.3f * k);
        yield return Hud.I.Say(null, "그려? 어쩔 수 없구만...", "gp_giveup", 1.6f * k, ElderHead);

        // 고개를 숙이고 돌아선다
        bill.gameObject.SetActive(false);
        StartCoroutine(Droop(0.55f * k));
        elder.Face(door.position, 4f);
        yield return Wait(0.55f);

        // 사람들과 함께 바라본다
        Watch(true);
        StartCoroutine(Follow());
        float speed = Bal.G("R1_ElderWalkSpeed", 1.1f);
        elder.Go(door.position, speed);
        float shot = Bal.G("R1_ElderShotDist", 2.7f);
        while (elder.Walking && Flat(elder.transform.position, door.position) > shot) yield return null;
        following = false;
        yield return new WaitForSeconds(0.16f);

        // BackShot은 대상 뒤 Shot_BackDist에 카메라를 둔다. 벽을 뚫지 않게 문 가까이 와서 찍는다
        yield return Cine.BackShot(elder, door.position, Mathf.Max(1.5f, total - (Time.time - t0)));
        Exit();
    }

    static float Flat(Vector3 a, Vector3 b)
    {
        a.y = b.y;
        return Vector3.Distance(a, b);
    }

    // 사람들과 같이 나가는 어르신을 눈으로 좇는다
    IEnumerator Follow()
    {
        following = true;
        while (following) yield return Player.LookAt(ElderHead, 0.15f);
    }

    IEnumerator Bounce()
    {
        Vector3 from = bill.parent.TransformPoint(billHome);
        Vector3 to = slot.position;
        yield return Reach(from, to, 0.42f * k);
        AudioManager.I.Play("card_reject", to, 0.8f);
        AudioManager.I.Play("kiosk_error", to, 0.5f);
        yield return Spit(to, 0.4f * k);
        yield return Wait(0.43f);
    }

    IEnumerator Reach(Vector3 from, Vector3 to, float sec)
    {
        Quaternion a = Quaternion.Euler(restArm), b = Quaternion.Euler(reachArm);
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            float s = Mathf.SmoothStep(0f, 1f, t);
            arm.localRotation = Quaternion.Slerp(a, b, s);
            bill.position = Vector3.Lerp(from, to, s);
            yield return null;
        }
        arm.localRotation = b;
        bill.position = to;
    }

    // 지폐가 틈에서 튀어나와 손으로 돌아온다
    IEnumerator Spit(Vector3 at, float sec)
    {
        Quaternion a = Quaternion.Euler(reachArm), b = Quaternion.Euler(restArm);
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            float s = Mathf.SmoothStep(0f, 1f, t);
            arm.localRotation = Quaternion.Slerp(a, b, s);
            Vector3 home = bill.parent.TransformPoint(billHome);
            bill.position = Vector3.Lerp(at, home, s) + Vector3.up * (Mathf.Sin(t * Mathf.PI) * 0.09f);
            yield return null;
        }
        arm.localRotation = b;
        bill.localPosition = billHome;
    }

    IEnumerator Droop(float sec)
    {
        // StreetNpc.Update가 머리 회전을 매 프레임 덮어쓴다
        var look = elder.GetComponent<StreetNpc>();
        if (look) look.enabled = false;
        Quaternion down = headRest * Quaternion.Euler(Bal.G("R1_ElderHeadDownDeg", 28f), 0f, 0f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            head.localRotation = Quaternion.Slerp(headRest, down, Mathf.SmoothStep(0f, 1f, t));
            yield return null;
        }
        head.localRotation = down;
    }

    void Watch(bool on)
    {
        watching = on;
        for (int i = 0; i < watchers.Length; i++)
        {
            if (!watchers[i]) continue;
            if (on) watcherYaw[i] = watchers[i].transform.eulerAngles.y;
            else watchers[i].FaceYaw(watcherYaw[i], 3f);
        }
    }

    void Update()
    {
        if (!watching) return;
        foreach (NpcMover w in watchers)
            if (w && !w.Walking) w.Face(elder.transform.position, 5f);
    }

    void Exit()
    {
        queue.OpenDoor();
        elder.Go(doorOut.position, Bal.G("R1_ElderWalkSpeed", 1.1f), () =>
        {
            Watch(false);
            elder.Hide();
        });
    }
}
