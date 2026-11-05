// 4-1~4-2: 내린 자리에서 버스가 떠나고 간판을 올려다본다. 문은 E로 밀고, 스티커를 돋보기로 읽으면 R 당기기가 생긴다.
// R4_Storefront 씬 Director 오브젝트에 부착. 문 물리는 StorefrontDirector를 복사했다.
// 배치: doorHandle = Anchor_DoorHandle, doorPivot = PH_Door_Glass 안 DoorPivot
// 배치: doorBlock = Door_Block, pullStand = Anchor_PullStand, insideLook = Anchor_InsideLook, insidePoint = Anchor_InsidePoint
// 배치: pushDoor = Interact_DoorPush (label 밀기, key E), pullDoor = Interact_DoorPull (label 당기기, key R)
// 배치: sticker = Sticker_Pull (Readable)
using System.Collections;
using UnityEngine;

public class R4StorefrontDirector : MonoBehaviour
{
    [SerializeField] Transform doorHandle;
    [SerializeField] Transform doorPivot;
    [SerializeField] Collider doorBlock;
    [SerializeField] Transform pullStand;
    [SerializeField] Transform insideLook;
    [SerializeField] Transform insidePoint;
    [SerializeField] Interactable pushDoor;
    [SerializeField] Interactable pullDoor;
    [SerializeField] Readable sticker;

    int tries;
    bool pushing, leaving, busGo;
    float busV = 0.5f;
    Transform signLook, doorLook, bus;
    NpcMover eater;

    // 문 각도는 HTML판 부호(안쪽으로 밀리면 +, 당기면 -), 라디안
    float doorA, doorV, doorHold;
    bool doorHeld;
    Quaternion doorBase;

    static string Me => GameState.I.Profile.speakerKey;
    Vector3 Handle => doorHandle.position;

    void Awake()
    {
        doorBase = doorPivot.localRotation;
        pushDoor.active = false;
        pullDoor.active = false;
        // 씬 필드를 늘리지 않고 이름으로 찾는다. 없으면 그 연출만 건너뛴다
        signLook = Named("Anchor_SignLook");
        doorLook = Named("Anchor_DoorLook");
        bus = Named("PH_Bus");
        Transform e = Named("NPC_Eater");
        if (e) eater = e.GetComponent<NpcMover>();
    }

    static Transform Named(string name)
    {
        GameObject g = GameObject.Find(name);
        return g ? g.transform : null;
    }

    void OnEnable()
    {
        pushDoor.onUse.AddListener(OnPush);
        pullDoor.onUse.AddListener(OnPull);
    }

    void OnDisable()
    {
        pushDoor.onUse.RemoveListener(OnPush);
        pullDoor.onUse.RemoveListener(OnPull);
        if (PlayerController.I) PlayerController.I.HoldStill = false;
    }

    IEnumerator Start()
    {
        PlayerController.I.HoldStill = true;
        AudioManager.I.Ambience(("amb_city_morning", 0.5f));
        if (bus)
        {
            AudioManager.I.Play("bus_leave", bus.position + Vector3.up, 0.7f);
            busGo = true;
        }
        yield return Round.Open();
        yield return LookUp();
        PlayerController.I.HoldStill = false;
        pushDoor.active = true;
    }

    // 간판을 천천히 올려다보고 문으로 시선을 내린다. 입력 없음
    IEnumerator LookUp()
    {
        if (!signLook || !doorLook) yield break;
        var player = PlayerController.I;
        player.Freeze(true);
        HandRig.I.SetEnabled(false);
        yield return player.LookAt(signLook.position, Bal.G("R4_SignLookSec", 1.2f));
        yield return new WaitForSeconds(Bal.G("R4_SignHoldSec", 2f));
        yield return player.LookAt(doorLook.position, 1.8f);
        HandRig.I.SetEnabled(true);
        player.Freeze(false);
    }

    void OnPush()
    {
        if (pushing || leaving) return;
        StartCoroutine(Push());
    }

    IEnumerator Push()
    {
        pushing = true;
        tries++;
        if (tries == 1)
        {
            yield return Shove(Bal.I("Door_Shove1Count", 2), Bal.G("Door_Shove1Power", 0.9f));
            yield return Hud.I.Say(Me, "어? 왜 안 열려.", Me + "_door1");
        }
        else if (tries == 2)
        {
            yield return Shove(Bal.I("Door_Shove2Count", 3), Bal.G("Door_Shove2Power", 1.1f));
            yield return Hud.I.Say(Me, "잠겼나?", Me + "_door2");
        }
        else
        {
            if (tries == 3) StartCoroutine(EaterLook());
            yield return Shove(Bal.I("Door_Shove3Count", 5), Bal.G("Door_Shove3Power", 1.3f));
        }
        pushing = false;
    }

    // 유리 너머 손님이 앉은 채로 돌아본다
    // 몸통을 조금 틀고 고개를 크게 돌려 플레이어를 본다. 머리뼈는 애니메이션 뒤 LateUpdate에서 돌린다
    Transform eaterHead;
    float eaterLook;

    IEnumerator EaterLook()
    {
        if (!eater) yield break;
        foreach (var t in eater.GetComponentsInChildren<Transform>())
            if (t.name.EndsWith("Head") && t.GetComponent<SkinnedMeshRenderer>() == null) { eaterHead = t; break; }
        float y0 = eater.transform.eulerAngles.y;
        Vector3 to = PlayerController.I.transform.position - eater.transform.position;
        float delta = Mathf.DeltaAngle(y0, Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg);
        float body = Bal.G("Door_SeatBodyDeg", 35f);
        eater.FaceYaw(y0 + Mathf.Clamp(delta, -body, body), 4f);
        for (float t = 0f; t < 1f; t += Time.deltaTime / 0.5f) { eaterLook = t; yield return null; }
        eaterLook = 1f;
        yield return new WaitForSeconds(Bal.G("Door_SeatLookSec", 2.6f));
        eater.FaceYaw(y0, 4f);
        for (float t = 1f; t > 0f; t -= Time.deltaTime / 0.5f) { eaterLook = t; yield return null; }
        eaterLook = 0f;
    }

    void LateUpdate()
    {
        if (eaterLook <= 0f || !eaterHead || !eater) return;
        Vector3 to = PlayerController.I.transform.position - eater.transform.position;
        float delta = Mathf.DeltaAngle(eater.transform.eulerAngles.y, Mathf.Atan2(to.x, to.z) * Mathf.Rad2Deg);
        float max = Bal.G("Door_SeatHeadDeg", 70f);
        eaterHead.Rotate(Vector3.up, Mathf.Clamp(delta, -max, max) * eaterLook, Space.World);
    }

    IEnumerator Shove(int count, float strength)
    {
        for (int i = 0; i < count; i++)
        {
            yield return new WaitForSeconds(0.13f);
            AudioManager.I.Play("door_rattle", Handle, 0.9f);
            doorV += Bal.G("Door_Kick", 0.55f) * strength;
            PlayerController.I.AddShake(Bal.G("Door_Shake", 0.5f) * strength);
            yield return new WaitForSeconds(0.2f);
        }
        yield return new WaitForSeconds(0.12f);
    }

    void OnPull()
    {
        if (leaving) return;
        leaving = true;
        pushDoor.active = false;
        pullDoor.active = false;
        StartCoroutine(Pull());
    }

    IEnumerator Pull()
    {
        var player = PlayerController.I;
        player.Freeze(true);
        Wallet.I.SetOpen(false);
        HandRig.I.Equip(ItemId.None);
        StartCoroutine(player.LookArc(Handle, Bal.G("Door_LookSec", 0.5f)));
        AudioManager.I.Play("door_handle", Handle, 0.8f);
        Coroutine say = Hud.I.Say(Me, "아, 당기는 거구먼.", Me + "_door3");
        Coroutine step = StartCoroutine(player.WalkTo(pullStand.position, Bal.F("DoorStepSpeed", 0.9f)));
        yield return new WaitForSeconds(0.45f);
        AudioManager.I.Play("door_chime", Handle, 0.75f);
        doorHeld = true;
        doorHold = -Bal.G("Door_OpenAngle", 1.45f);
        yield return say;
        StopCoroutine(step);
        doorBlock.enabled = false;
        StartCoroutine(player.LookArc(insideLook.position, Bal.G("Door_LookInSec", 0.9f)));
        yield return StoreFlow.Race(this, player.WalkTo(insidePoint.position, Bal.F("MoveSpeed", 1.15f)), 3f);
        GameState.I.CompleteChapter();
    }

    void Update()
    {
        // onRead는 조준 시작 때 한 번만 오므로 지금 보이는지를 본다. 임시 T20
        if (pushDoor.active && !leaving && !pullDoor.active && sticker && sticker.Seen)
        {
            pullDoor.active = true;
            Hud.I.Say(Me, "이건 또 뭐야.", Me + "_why3");
        }

        float dt = Time.deltaTime;
        if (busGo)
        {
            busV = Mathf.Min(Bal.G("Bus_LeaveMaxSpeed", 9f), busV + dt * Bal.G("Bus_LeaveAccel", 1.7f));
            bus.position += bus.right * (busV * dt);   // PH_Bus의 앞은 로컬 +X
            if (Mathf.Abs(bus.position.x) > 46f)
            {
                bus.gameObject.SetActive(false);
                busGo = false;
            }
        }
        if (doorHeld)
        {
            doorA = StoreFlow.Damp(doorA, doorHold, 2.6f, dt);
        }
        else
        {
            float k = Bal.G("Door_SpringK", 620f), c = Bal.G("Door_SpringD", 24f);
            int n = Mathf.Min(40, Mathf.CeilToInt(dt / 0.008f));
            float h = n > 0 ? dt / n : 0f;
            for (int i = 0; i < n; i++)
            {
                doorV += (-doorA * k - doorV * c) * h;
                doorA += doorV * h;
                if (doorA > 0.05f) { doorA = 0.05f; doorV *= -0.45f; }
                if (doorA < -0.012f) { doorA = -0.012f; doorV *= -0.4f; }
            }
        }
        // z를 뒤집었으므로 y 회전 부호도 뒤집힌다
        doorPivot.localRotation = doorBase * Quaternion.Euler(0f, -doorA * Mathf.Rad2Deg, 0f);
    }
}
