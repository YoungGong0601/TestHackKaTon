// E-1a, E-1b, E-1c. 늦은 밤 집 앞 골목을 플레이어가 아주 느리게 걷고, 현관에서 쪽지를 구겨 바닥에 두고, 크게 한숨을 쉰 뒤 벽을 짚고 숨을 고르다 암막으로 끝난다.
// 끝은 CompleteChapter, 이어서 Ending.Play가 E-2를 보여 준다.
// 손은 HandRig 대신 씬에 둔 회색 손을 시선에 붙여 그린다. 씬 이름 Ending_Home, 부착: Director
// 배치: doorHinge = PH_Door_Home 의 Hinge, doorBlock = DoorBlock
// 배치: doorReach = 문 밖에서 E-1b가 시작되는 자리, foyerStand = 현관 안 서는 자리
// 배치: noteSpot = 쪽지를 놓을 때 손 자리, wallStand = 벽 앞 서는 자리, wallPalm = 벽 짚는 왼손 자리(회전 그대로 쓴다)
// 배치: handR, handL = 회색 손 묶음. noteFlat, noteBall = handR 자식(손에 쥔 쪽지, 구겨진 쪽지)
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

public class EndingHomeDirector : MonoBehaviour
{
    const float DoorOpenDeg = -85.9f;

    [SerializeField] Transform doorHinge;
    [SerializeField] Collider doorBlock;
    [SerializeField] Transform doorReach;
    [SerializeField] Transform foyerStand;
    [SerializeField] Transform noteSpot;
    [SerializeField] Transform wallStand;
    [SerializeField] Transform wallPalm;
    [SerializeField] Transform handR;
    [SerializeField] Transform handL;
    [SerializeField] GameObject noteFlat;
    [SerializeField] GameObject noteBall;

    // 시선 기준 손 자리. onFloor가 1이면 target 자리(바닥, 벽)로 옮겨 간다
    class Hold
    {
        public Transform hand, target;
        public Vector3 pos;
        public Quaternion rot;
        public float onFloor, shake;
    }

    static readonly Vector3 CarryPos = new(0.15f, -0.19f, 0.4f);
    static readonly Quaternion CarryRot = Quaternion.Euler(50f, 0f, -12f);
    static readonly Vector3 SqueezePos = new(0.03f, -0.13f, 0.33f);
    static readonly Quaternion SqueezeRot = Quaternion.Euler(40f, 0f, 0f);
    static readonly Vector3 HiddenLeft = new(-0.2f, -0.6f, 0.3f);

    Hold right, left;
    PlayerController player;
    AudioManager sound;
    Coroutine walking;
    bool walkHeld;
    float nextStrain;
    int strainAt;
    float roll, breathe;   // 벽을 짚은 뒤 시선 기울기(도)와 숨 고르는 눈 높이 흔들림(m)

    void Awake()
    {
        right = new Hold { hand = handR, pos = CarryPos, rot = CarryRot };
        left = new Hold { hand = handL, pos = HiddenLeft, rot = CarryRot };
        noteFlat.SetActive(true);
        noteBall.SetActive(false);
    }

    IEnumerator Start()
    {
        player = PlayerController.I;
        sound = AudioManager.I;
        HandRig.I.SetEnabled(false);          // 소지품 칸과 2, 3 키를 끈다
        player.HoldStill = true;              // 걸음은 Walk가 낸다. 속도가 인물 값보다 느려서다
        player.Ground = "concrete";
        sound.Ambience(("amb_hallway", Bal.G("End_AmbVol", 0.18f)));

        yield return Round.Open();
        Hud.I.Cross(false);
        yield return Walk();
        yield return EnterHome();
        yield return Lean();
        GameState.I.CompleteChapter();
    }

    // E-1a. 멈추면 그대로 기다린다(남은 결정, 재촉 없음)
    IEnumerator Walk()
    {
        nextStrain = Time.time + Bal.G("End_StrainFirstSec", 1.5f);
        float reach = Bal.G("End_DoorReach", 1.1f);
        while (Flat(player.transform.position, doorReach.position) > reach)
        {
            Step();
            yield return null;
        }
        StopWalk();
    }

    void Step()
    {
        var kb = Keyboard.current;
        int f = 0, s = 0;
        if (kb != null)
        {
            f = (kb.wKey.isPressed || kb.upArrowKey.isPressed ? 1 : 0) - (kb.sKey.isPressed || kb.downArrowKey.isPressed ? 1 : 0);
            s = (kb.dKey.isPressed || kb.rightArrowKey.isPressed ? 1 : 0) - (kb.aKey.isPressed || kb.leftArrowKey.isPressed ? 1 : 0);
        }
        if (f == 0 && s == 0)
        {
            if (walkHeld) StopWalk();
            return;
        }
        walkHeld = true;
        var t = player.transform;
        Vector3 dir = (t.forward * f + t.right * s).normalized;
        walking = StartCoroutine(player.WalkTo(t.position + dir * 0.5f, Bal.G("End_WalkSpeed", 0.35f)));
        if (Time.time >= nextStrain) Strain(Bal.G("End_StrainEverySec", 4.5f));
    }

    void StopWalk()
    {
        walkHeld = false;
        if (walking == null) return;
        walking = StartCoroutine(player.WalkTo(player.transform.position, 0.01f));
    }

    // 음성과 숨을 번갈아 낸다
    void Strain(float wait)
    {
        strainAt++;
        float len = strainAt % 3 == 0
            ? PlayBreath()
            : sound.Vo("gp_strain" + (1 + strainAt * 2 % 5), null, Bal.G("End_StrainVol", 0.8f), clear: true);
        nextStrain = Time.time + len + wait * Random.Range(0.8f, 1.2f);
    }

    float PlayBreath()
    {
        sound.Play("breath_old", null, Bal.G("End_BreathVol", 0.6f), Random.Range(0.92f, 1f), clear: true);
        return 2f;
    }

    // E-1b
    IEnumerator EnterHome()
    {
        player.Freeze(true);
        player.SetMode(PlayerController.Mode.Hidden);
        sound.Play("door_key", doorHinge.position, 0.6f);
        yield return new WaitForSeconds(Bal.G("End_KeySec", 1.2f));
        sound.Play("door_handle", doorHinge.position, 0.7f);
        doorBlock.enabled = false;
        StartCoroutine(OpenDoor());
        yield return new WaitForSeconds(0.8f);

        float speed = Bal.G("End_WalkSpeed", 0.35f);
        StartCoroutine(player.TurnTo(Yaw(foyerStand.position), -12f, 1.2f));
        Strain(0f);
        yield return player.WalkTo(doorReach.position, speed);
        yield return player.WalkTo(foyerStand.position, speed);
        player.Ground = "tile";

        // 쥐어 구긴다
        yield return Move(right, SqueezePos, SqueezeRot, 0.9f);
        right.shake = 1f;
        sound.Play("paper_rustle", null, 0.8f);
        yield return Squeeze(Bal.G("End_CrushSec", 1.4f));
        noteFlat.SetActive(false);
        noteBall.SetActive(true);
        sound.Play("paper_rustle", null, 1f, 0.8f);
        Strain(0f);
        yield return new WaitForSeconds(Bal.G("End_CrushHoldSec", 1.6f));
        right.shake = 0.4f;

        // 허리를 숙여 바닥에 둔다
        StartCoroutine(player.TurnTo(player.Yaw, -62f, 1.8f));
        yield return Sink(Bal.G("End_BendEye", 0.85f), 1.8f);
        yield return Reach(right, noteSpot, 1.2f);
        noteBall.transform.SetParent(null, true);
        Vector3 rest = noteBall.transform.position;
        rest.y = foyerStand.position.y + Bal.G("End_NoteRestY", 0.025f);
        noteBall.transform.position = rest;
        sound.Play("paper_rustle", noteSpot.position, 0.5f, 1.15f);
        yield return new WaitForSeconds(Bal.G("End_NoteRestSec", 0.8f));
    }

    // E-1c. 몸을 일으키며 크게 한숨, 벽으로 가서 왼손을 짚고 고개를 약간 숙인 채 숨을 고른다
    IEnumerator Lean()
    {
        float sec = Bal.G("End_RiseSec", 2f);
        sound.Play("sigh_m_1", null, Bal.G("End_SighVol", 1f), Bal.G("End_SighRate", 0.8f), clear: true);
        StartCoroutine(player.TurnTo(Yaw(wallStand.position), -6f, sec));
        StartCoroutine(Drop(right, sec));
        yield return Sink(player.EyeHeight, sec);
        yield return new WaitForSeconds(Bal.G("End_SighSec", 1.8f));
        yield return player.WalkTo(wallStand.position, Bal.G("End_WalkSpeed", 0.35f));

        sec = Bal.G("End_LeanSec", 1.3f);
        StartCoroutine(player.TurnTo(Yaw(wallPalm.position) + Bal.G("End_LeanYawOff", 22f), Bal.G("End_LeanPitch", -14f), sec));
        StartCoroutine(Sink(Bal.G("End_LeanEye", 1.42f), sec));
        StartCoroutine(Tilt(Bal.G("End_LeanRoll", 4f), sec));
        yield return Reach(left, wallPalm, sec);
        sound.Play("step_tile", wallPalm.position, 0.35f, 1.3f);
        left.shake = 0.4f;
        breathe = Bal.G("End_LeanBreath", 0.012f);
        yield return new WaitForSeconds(0.6f);
        float len = sound.Vo("gp_strain4", null, Bal.G("End_StrainVol", 0.8f), clear: true);
        yield return new WaitForSeconds(len + Bal.G("End_LeanHoldSec", 1.2f));
        PlayBreath();
        yield return Hud.I.Fade(1f, Bal.G("End_FadeOutSec", 4f));
        sound.Ambience();
        yield return new WaitForSeconds(Bal.G("End_BlackSec", 1f));
    }

    IEnumerator Tilt(float deg, float sec)
    {
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            roll = deg * t * t * (3f - 2f * t);
            yield return null;
        }
        roll = deg;
    }

    // 쥔 손을 내린다. 화면 밖으로 빠진다
    IEnumerator Drop(Hold h, float sec)
    {
        var eye = player.Eye.transform;
        h.pos = eye.InverseTransformPoint(h.hand.position);
        h.rot = Quaternion.Inverse(eye.rotation) * h.hand.rotation;
        h.target = null;
        h.onFloor = 0f;
        yield return Move(h, new Vector3(0.2f, -0.6f, 0.3f), CarryRot, sec);
    }

    IEnumerator OpenDoor()
    {
        Quaternion from = doorHinge.localRotation, to = from * Quaternion.Euler(0f, DoorOpenDeg, 0f);
        for (float t = 0f, sec = Bal.G("End_DoorSec", 1.6f); t < 1f; t += Time.deltaTime / sec)
        {
            doorHinge.localRotation = Quaternion.Slerp(from, to, t * t * (3f - 2f * t));
            yield return null;
        }
        doorHinge.localRotation = to;
    }

    // 눈 높이까지 몸을 내린다. PlayerController는 눈을 몸 기준 EyeHeight에 두므로 몸을 내려서 맞춘다
    IEnumerator Sink(float eyeAboveFloor, float sec)
    {
        float floor = foyerStand.position.y, from = player.transform.position.y;
        float to = floor + eyeAboveFloor - player.EyeHeight;
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            Vector3 p = player.transform.position;
            p.y = Mathf.Lerp(from, to, t * t * (3f - 2f * t));
            player.MoveTo(p);
            yield return null;
        }
    }

    IEnumerator Squeeze(float sec)
    {
        Vector3 from = noteFlat.transform.localScale;
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            noteFlat.transform.localScale = Vector3.Lerp(from, from * 0.45f, t);
            yield return null;
        }
    }

    IEnumerator Move(Hold h, Vector3 pos, Quaternion rot, float sec)
    {
        Vector3 p0 = h.pos;
        Quaternion r0 = h.rot;
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            float e = t * t * (3f - 2f * t);
            h.pos = Vector3.Lerp(p0, pos, e);
            h.rot = Quaternion.Slerp(r0, rot, e);
            yield return null;
        }
        h.pos = pos;
        h.rot = rot;
    }

    IEnumerator Reach(Hold h, Transform target, float sec)
    {
        // 지금 손 자리에서 출발한다
        var eye = player.Eye.transform;
        h.pos = eye.InverseTransformPoint(h.hand.position);
        h.rot = Quaternion.Inverse(eye.rotation) * h.hand.rotation;
        h.target = target;
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            h.onFloor = t * t * (3f - 2f * t);
            yield return null;
        }
        h.onFloor = 1f;
    }

    void LateUpdate()
    {
        if (player == null) return;
        // PlayerController가 Update마다 눈을 다시 놓으므로 그 위에 더한다
        var eye = player.Eye.transform;
        if (roll != 0f) eye.localRotation *= Quaternion.Euler(0f, 0f, roll);
        if (breathe != 0f) eye.localPosition += Vector3.up * (Mathf.Sin(Time.time * 1.5f) * breathe);
        Place(right);
        Place(left);
    }

    void Place(Hold h)
    {
        var eye = player.Eye.transform;
        float t = Time.time, j = (Debuff.Tremble + h.shake) * Bal.G("End_HandTremble", 0.003f);
        Vector3 at = eye.TransformPoint(h.pos);
        Quaternion rot = eye.rotation * h.rot;
        if (h.target != null)
        {
            at = Vector3.Lerp(at, h.target.position, h.onFloor);
            rot = Quaternion.Slerp(rot, h.target.rotation, h.onFloor);
        }
        h.hand.SetPositionAndRotation(at + new Vector3(Mathf.Sin(t * 29f), Mathf.Cos(t * 23f), Mathf.Sin(t * 17f)) * j, rot);
    }

    float Yaw(Vector3 world)
    {
        Vector3 d = world - player.transform.position;
        return Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
    }

    static float Flat(Vector3 a, Vector3 b)
    {
        a.y = b.y = 0f;
        return Vector3.Distance(a, b);
    }
}
