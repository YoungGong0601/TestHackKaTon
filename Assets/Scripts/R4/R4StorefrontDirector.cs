// 4-0~4-2: 지갑 속 쪽지를 돋보기로 읽어야 걷는다. 문은 E로 밀고, 스티커를 돋보기로 읽으면 R 당기기가 생긴다.
// R4_Storefront 씬 Director 오브젝트에 부착. 문 물리는 StorefrontDirector를 복사했다.
// 배치: doorHandle = Anchor_DoorHandle, doorPivot = PH_Door_Glass 안 DoorPivot
// 배치: doorBlock = Door_Block, pullStand = Anchor_PullStand, insideLook = Anchor_InsideLook, insidePoint = Anchor_InsidePoint
// 배치: pushDoor = Interact_DoorPush (label 밀기, key E), pullDoor = Interact_DoorPull (label 당기기, key R)
// 배치: sticker = Sticker_Pull (Readable)
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

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
    bool opened, noteRead, pushing, leaving, muttering, busGo;
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
        IntroEnd();
        if (PlayerController.I) PlayerController.I.HoldStill = false;
        if (Wallet.I)
        {
            Wallet.I.NoteRead -= OnNoteRead;
            Wallet.I.NoteMissed -= Mutter;
        }
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
        IntroBegin();
        yield return Round.Open();
        yield return Intro();
        yield return LookUp();
        Wallet.I.NoteRead += OnNoteRead;
        Wallet.I.NoteMissed += Mutter;
        Wallet.I.SetOpen(true);   // 임시 T19
        opened = true;
        Hud.I.Hint(ItemId.Lens);
        Mutter();
    }

    // 간판을 천천히 올려다보고 문으로 시선을 내린다. 입력 없음
    // ---- 시작 연출: 검은 바탕에 두 손, 시선이 올라오며 배경이 걷힌다 ----
    // 손은 눈앞 0.7m 안에 있으므로 검은 안개로 그 뒤만 가린다. 안개를 안 받는 글자는 잠시 끄고, 하늘은 색을 내린다

    readonly List<Renderer> introHidden = new List<Renderer>();
    Material introSky;
    Color skyTint, fogColor;
    float skyExposure, fogStart, fogEnd;
    int eyeMask = -1;
    bool fogOn;
    FogMode fogMode;

    void IntroBegin()
    {
        var player = PlayerController.I;
        fogOn = RenderSettings.fog;
        fogMode = RenderSettings.fogMode;
        fogColor = RenderSettings.fogColor;
        fogStart = RenderSettings.fogStartDistance;
        fogEnd = RenderSettings.fogEndDistance;
        RenderSettings.fog = true;
        RenderSettings.fogMode = FogMode.Linear;
        if (RenderSettings.skybox)
        {
            introSky = RenderSettings.skybox = new Material(RenderSettings.skybox);
            if (introSky.HasProperty("_Tint")) skyTint = introSky.GetColor("_Tint");
            if (introSky.HasProperty("_Exposure")) skyExposure = introSky.GetFloat("_Exposure");
        }
        foreach (var t in FindObjectsByType<TextMeshPro>(FindObjectsSortMode.None))
        {
            var r = t.GetComponent<Renderer>();
            if (!r || !r.enabled) continue;
            r.enabled = false;
            introHidden.Add(r);
        }
        eyeMask = player.Eye.cullingMask;
        player.Eye.cullingMask = eyeMask & ~LayerMask.GetMask("LensBlurred");
        IntroShade(0f);
        StartCoroutine(player.TurnTo(player.Yaw, Bal.G("R4_IntroPitch", -38f), 0.01f));
    }

    // 0 검정, 1 원래
    void IntroShade(float k)
    {
        RenderSettings.fogColor = Color.Lerp(Color.black, fogColor, k);
        RenderSettings.fogStartDistance = Mathf.Lerp(Bal.G("R4_IntroFogStart", 0.7f), fogStart, k);
        RenderSettings.fogEndDistance = Mathf.Lerp(Bal.G("R4_IntroFogEnd", 1f), fogEnd, k);
        if (!introSky) return;
        if (introSky.HasProperty("_Tint")) introSky.SetColor("_Tint", Color.Lerp(Color.black, skyTint, k));
        if (introSky.HasProperty("_Exposure")) introSky.SetFloat("_Exposure", skyExposure * k);
    }

    void IntroEnd()
    {
        if (eyeMask == -1) return;
        foreach (var r in introHidden) if (r) r.enabled = true;
        introHidden.Clear();
        if (PlayerController.I) PlayerController.I.Eye.cullingMask = eyeMask;
        eyeMask = -1;
    }

    IEnumerator Intro()
    {
        var player = PlayerController.I;
        var hands = HandRig.I;
        player.Freeze(true);
        hands.SetPointer(true);
        hands.ShowWatch(Bal.I("R4_IntroWatchHour", 10));
        yield return new WaitForSeconds(Bal.G("R4_IntroHandSec", 2.5f));
        hands.HideWatch();
        hands.SetPointer(false);

        float sec = Mathf.Max(Bal.G("R4_IntroLiftSec", 2.5f), 0.01f);
        StartCoroutine(player.TurnTo(player.Yaw, 0f, sec));
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            IntroShade(t * t * t);
            yield return null;
        }
        IntroShade(1f);
        RenderSettings.fog = fogOn;
        RenderSettings.fogMode = fogMode;
        IntroEnd();
        player.Freeze(false);
    }

    IEnumerator LookUp()
    {
        if (!signLook || !doorLook) yield break;
        var player = PlayerController.I;
        player.Freeze(true);
        HandRig.I.SetEnabled(false);
        yield return player.LookAt(signLook.position, Bal.G("Door_SignLookSec", 3.2f));
        yield return new WaitForSeconds(Bal.G("Door_SignHoldSec", 1.1f));
        yield return player.LookAt(doorLook.position, 1.8f);
        HandRig.I.SetEnabled(true);
        player.Freeze(false);
    }

    void OnNoteRead()
    {
        if (noteRead) return;
        noteRead = true;
        Hud.I.Hint(ItemId.None);
        AudioManager.I.Play("paper_rustle", null, 0.5f);
        StartCoroutine(StartWalking());
    }

    // 쪽지를 볼 틈을 준 뒤 지갑을 닫고 걷기 시작한다
    IEnumerator StartWalking()
    {
        yield return new WaitForSeconds(Bal.G("R4_NoteHoldSec", 2f));
        Wallet.I.SetOpen(false);
        HandRig.I.Equip(ItemId.None);   // 돋보기를 내린다. 4-1은 못 보고 미는 장면이다
        PlayerController.I.HoldStill = false;
        pushDoor.active = true;
    }

    void Mutter()
    {
        if (muttering) return;
        StartCoroutine(MutterRun());
    }

    IEnumerator MutterRun()
    {
        muttering = true;
        AudioManager.I.Play("paper_rustle", null, 0.4f);
        yield return Hud.I.Say(null, "지갑에 뭐라 썼더라...", Me + "_wallet");
        muttering = false;
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
            yield return Hud.I.Say(null, "어? 왜 안 열려.", Me + "_door1");
        }
        else if (tries == 2)
        {
            yield return Shove(Bal.I("Door_Shove2Count", 3), Bal.G("Door_Shove2Power", 1.1f));
            yield return Hud.I.Say(null, "잠겼나?", Me + "_door2");
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
        AudioManager.I.Play("door_handle", Handle, 0.8f);
        Coroutine say = Hud.I.Say(null, "아, 당기는 거구먼.", Me + "_door3");
        Coroutine step = StartCoroutine(player.WalkTo(pullStand.position, Bal.F("DoorStepSpeed", 0.9f)));
        yield return new WaitForSeconds(0.45f);
        AudioManager.I.Play("door_glass_open", Handle, 0.8f);
        AudioManager.I.Play("door_chime", Handle, 0.75f);
        doorHeld = true;
        doorHold = -Bal.G("Door_OpenAngle", 1.45f);
        yield return say;
        StopCoroutine(step);
        doorBlock.enabled = false;
        yield return StoreFlow.Race(this, player.LookAt(insideLook.position, 0.7f), 0.8f);
        yield return StoreFlow.Race(this, player.WalkTo(insidePoint.position, Bal.F("MoveSpeed", 1.15f)), 3f);
        GameState.I.CompleteChapter();
    }

    void Update()
    {
        // 쪽지를 읽기 전 걸으려 하면 멈춘 이유를 낸다
        var kb = Keyboard.current;
        if (opened && !noteRead && kb != null
            && (kb.wKey.wasPressedThisFrame || kb.aKey.wasPressedThisFrame || kb.sKey.wasPressedThisFrame || kb.dKey.wasPressedThisFrame))
            Mutter();

        // onRead는 조준 시작 때 한 번만 오므로 지금 보이는지를 본다. 임시 T20
        if (noteRead && !leaving && !pullDoor.active && sticker && sticker.Seen)
        {
            pullDoor.active = true;
            Hud.I.Say(null, "이건 또 뭐야.", Me + "_why3");
        }

        float dt = Time.deltaTime;
        if (busGo)
        {
            busV = Mathf.Min(Bal.G("Bus_LeaveMaxSpeed", 9f), busV + dt * Bal.G("Bus_LeaveAccel", 1.7f));
            bus.position += bus.right * (busV * dt);   // PH_Bus의 앞은 로컬 +X
            if (Mathf.Abs(bus.position.x) > 125f)   // 안개 끝(플레이어에서 110m) 너머, 도로는 140까지 있다
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
