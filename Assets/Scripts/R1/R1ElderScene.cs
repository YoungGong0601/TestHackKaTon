// 1-5, 1-6 앞 어르신 장면. 1-6 길이는 R1_ElderSceneSec. 아래 시각은 15초 기준이고 비율로 늘고 준다.
// 얼굴을 보이지 않고 고개를 숙여 돌아서는 것으로 슬픔을 보인다(T13). 뒷모습은 Cine.BackShot, E-1과 같은 구도.
// 배치: elder = NPC_Elder (NpcMover), head = 그 HeadPivot
// 배치: arm = NPC_Elder 의 Arm_Pivot (Visual 안 소매, 손, 반지, 손목시계), restArm = 팔 로컬 회전
// 배치: slot = PH_Kiosk 의 Slot_ic
// 배치: door = Anchor_DoorIn, doorOut = Anchor_DoorOut, queue = QueueManager (문 열기)
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

    float k;
    bool following;
    Quaternion headRest;

    static PlayerController Player => PlayerController.I;
    Vector3 ElderHead => head.position;

    void Awake()
    {
        headRest = head.localRotation;
        arm.localRotation = Quaternion.Euler(restArm);
    }

    WaitForSeconds Wait(float sec) => new WaitForSeconds(sec * k);

    public IEnumerator Play()
    {
        float total = Bal.G("R1_ElderSceneSec", 15f);
        k = total / 15f;

        // 1-5 줄. 걷기만 막고 시선은 자유다(T12). 장면 길이에 넣지 않는다
        Player.HoldStill = true;
        yield return new WaitForSeconds(0.6f);
        // 기다리는 동안 어르신 혼잣말. 음성이 없는 줄은 자막만 나온다
        float mutter = Bal.G("R1_ElderMutterSec", 2.5f);
        yield return Hud.I.Say(null, "이게 어디를 누르는 거여...", "gp_where_press", -1f, ElderHead);
        yield return new WaitForSeconds(mutter);
        yield return Hud.I.Say(null, "왜 안 되지?", "gp_why1", -1f, ElderHead);
        yield return new WaitForSeconds(mutter);
        yield return Hud.I.Say(null, "글씨가 왜 이렇게 작아.", "gp_read1", -1f, ElderHead);
        yield return new WaitForSeconds(mutter);
        AudioManager.I.Play("sigh_m_1", null, 0.8f, 1f, clear: true);   // N14
        yield return new WaitForSeconds(0.8f);

        // 1-6 입력 없음. 여기서부터 R1_ElderSceneSec
        float t0 = Time.time;
        Player.Freeze(true);
        Player.HoldStill = false;
        yield return Player.LookAt(slot.position, Bal.G("Cine_BlendSec", 1f));
        int bounces = Bal.I("Cash_BounceCount", 3);
        for (int i = 0; i < bounces; i++) yield return Bounce();
        yield return Hud.I.Say(null, "왜 기계가 돈을 안먹지? 이상하네", "gp_no_eat", -1f, ElderHead);

        int said = 0;
        yield return Choice.Ask(KioskData.CashLines, i => said = i);
        Player.Freeze(true);
        GameState.I.CashLine = said;
        yield return Hud.I.Say(null, KioskData.CashLines[said], KioskData.CashVo(GameState.I.Profile.speakerKey, said), 1.5f * k);
        elder.Face(Player.transform.position, 5f);
        yield return Player.LookAt(ElderHead, Bal.G("Cine_BlendSec", 1f));
        // R4ProtoPack.CashTalk과 같은 순서, 같은 문구. 시점만 다르다
        yield return Hud.I.Say(null, "아, 그려?", "gp_really", -1f, ElderHead);
        yield return Hud.I.Say(null, "그러면 방법이 없는겨?", "gp_nomore", -1f, ElderHead);
        yield return Hud.I.Say(null, "일단 현금은 안된다네요.", GameState.I.Profile.speakerKey + "_nocash");
        yield return Hud.I.Say(null, "그려? 어쩔 수 없구만...", "gp_giveup", 1.6f * k, ElderHead);

        // 고개를 숙이고 돌아선다
        StartCoroutine(Droop(0.55f * k));
        elder.Face(door.position, 4f);
        yield return Wait(0.55f);

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

    // 나가는 어르신을 눈으로 좇는다
    IEnumerator Follow()
    {
        following = true;
        while (following) yield return Player.LookAt(ElderHead, 0.15f);
    }

    // 팔은 움직이지 않는다. 머뭇거리는 시간과 거부 소리만 남긴다
    IEnumerator Bounce()
    {
        yield return Wait(0.42f);
        AudioManager.I.Play("card_reject", slot.position, 0.8f);
        AudioManager.I.Play("kiosk_error", slot.position, 0.5f);
        yield return Wait(0.83f);
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

    void Exit()
    {
        queue.OpenDoor();
        elder.Go(doorOut.position, Bal.G("R1_ElderWalkSpeed", 1.1f), () =>
        {
            elder.Hide();
        });
    }
}
