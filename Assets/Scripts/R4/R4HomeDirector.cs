// 80대 집. 긴 암전과 소리 끊김 뒤 검은 바탕의 두 손에서 시선이 올라오고, 쪽지를 들어 읽고 내린 뒤, 신발을 신고 문을 열고 나간다. 프로토타입 HomeDirector 진행.
// R1_Home 씬 Director 오브젝트에 부착.
// 배치: shoesUse = ShoesUse (label 신발 신기), doorUse = PH_Door_Home 의 DoorUse (label 문 열기)
// 배치: shoes = Env/HomeShoes, leanCane = LeanCane, shoeLook = ShoeLook, shoeStand = ShoeStand, doorLook = DoorLook
// 배치: doorHinge = Hinge, doorBlock = DoorBlock, exitPoint = Anchor_Exit (문 밖)
using System.Collections;
using System.Collections.Generic;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

public class R4HomeDirector : MonoBehaviour
{
    const float DoorOpenDeg = -85.9f;
    const float DoorDamp = 2.2f;

    [SerializeField] Interactable shoesUse;
    [SerializeField] Interactable doorUse;
    [SerializeField] GameObject shoes;
    [SerializeField] GameObject leanCane;
    [SerializeField] Transform shoeLook;
    [SerializeField] Transform shoeStand;
    [SerializeField] Transform doorLook;
    [SerializeField] Transform doorHinge;
    [SerializeField] Collider doorBlock;
    [SerializeField] Transform exitPoint;

    bool ready, noteUp, canLower, lowered, muttering, shoesOn, leaving;
    float doorT, doorWant;
    Quaternion doorClosed;

    static string Me => GameState.I.Profile.speakerKey;
    static PlayerController Player => PlayerController.I;
    static AudioManager Sound => AudioManager.I;

    void Awake()
    {
        doorClosed = doorHinge.localRotation;
        shoesUse.active = false;
        doorUse.active = false;
    }

    void OnEnable()
    {
        shoesUse.onUse.AddListener(OnShoes);
        doorUse.onUse.AddListener(OnDoor);
    }

    void OnDisable()
    {
        shoesUse.onUse.RemoveListener(OnShoes);
        doorUse.onUse.RemoveListener(OnDoor);
        IntroEnd();
        if (Player) Player.HoldStill = false;
    }

    IEnumerator Start()
    {
        if (GameState.I.Booting) yield break;   // 이 씬은 부팅 씬이기도 하다. 80대 챕터로 온 게 아니면 연출을 시작하지 않는다
        Player.HoldStill = true;
        // 앞 장면과 갈라지는 자리. 소리를 끊고 평소보다 길게 어둠을 둔다. 손은 시작 연출이 보여 준다
        Sound.Ambience();
        Round.ProfileChanged = false;
        IntroBegin();
        yield return new WaitForSeconds(Bal.G("R4_HomeBlackSec", 3f));
        Sound.Ambience(("amb_hallway", 0.5f));
        yield return Round.Open();
        yield return Intro();
        ready = true;
        Mutter();
    }

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
        eyeMask = Player.Eye.cullingMask;
        Player.Eye.cullingMask = eyeMask & ~LayerMask.GetMask("LensBlurred");
        IntroShade(0f);
        StartCoroutine(Player.TurnTo(Player.Yaw, Bal.G("R4_IntroPitch", -38f), 0.01f));
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
        if (Player) Player.Eye.cullingMask = eyeMask;
        eyeMask = -1;
    }

    IEnumerator Intro()
    {
        var hands = HandRig.I;
        Player.Freeze(true);
        hands.SetEnabled(false);
        hands.SetPose("Pose_Open");
        yield return new WaitForSeconds(Bal.G("R4_IntroHandSec", 2.5f));
        hands.SetPose("Pose_Default");
        hands.SetEnabled(true);

        float sec = Mathf.Max(Bal.G("R4_IntroLiftSec", 2.5f), 0.01f);
        StartCoroutine(Player.TurnTo(Player.Yaw, 0f, sec));
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            IntroShade(t * t * t);
            yield return null;
        }
        IntroShade(1f);
        RenderSettings.fog = fogOn;
        RenderSettings.fogMode = fogMode;
        IntroEnd();
        Player.Freeze(false);
    }

    // ---- 쪽지 ----

    void Mutter()
    {
        if (!muttering) StartCoroutine(MutterRun());
    }

    IEnumerator MutterRun()
    {
        muttering = true;
        yield return Hud.I.Say(Me, "뭐라고 썼더라.", Me + "_note");
        muttering = false;
    }

    IEnumerator ReadNote()
    {
        yield return new WaitForSeconds(Bal.G("R4_NoteReadDelaySec", 0.6f));
        yield return Hud.I.Say(Me, "우리 손주가 좋아하는 거... 불고기 버거 세트, 사이다로. 그래, 그거.", Me + "_grandson");
        yield return Hud.I.Say(Me, "시장 입구 쪽이랬지.", Me + "_market");
        canLower = true;
    }

    void Lowered()
    {
        lowered = true;
        Hud.I.Prompt(null);
        Note.Close();
        Player.HoldStill = false;
        shoesUse.active = true;
    }

    void Update()
    {
        doorT = Mathf.Lerp(doorT, doorWant, 1f - Mathf.Exp(-DoorDamp * Time.deltaTime));
        doorHinge.localRotation = doorClosed * Quaternion.Euler(0f, doorT * DoorOpenDeg, 0f);
        if (!ready || lowered) return;

        var kb = Keyboard.current;
        if (!noteUp)
        {
            Hud.I.Prompt($"<b>{ItemKeys.Of(ItemId.Memo)}</b> 쪽지");
            // 걸으려 하면 멈춘 이유를 낸다
            if (kb != null && (kb.wKey.wasPressedThisFrame || kb.aKey.wasPressedThisFrame || kb.sKey.wasPressedThisFrame || kb.dKey.wasPressedThisFrame))
                Mutter();
            if (!Note.Opened) return;
            noteUp = true;
            StartCoroutine(ReadNote());
            return;
        }
        if (!canLower) { Hud.I.Prompt(null); return; }
        if (!Note.Opened) { Lowered(); return; }
        Hud.I.Prompt("<b>E</b> 쪽지 내리기");
        if (kb != null && kb.eKey.wasPressedThisFrame) Lowered();
    }

    // ---- 신발 ----

    void OnShoes()
    {
        if (shoesOn) return;
        shoesOn = true;
        shoesUse.active = false;
        StartCoroutine(ShoesRoutine());
    }

    IEnumerator ShoesRoutine()
    {
        Player.Freeze(true);
        yield return Player.LookAt(shoeLook.position, 0.6f);
        yield return Hud.I.Fade(1f, Bal.G("Home_ShoeFadeOutSec", 0.4f));
        Sound.Play("step_tile", null, 0.5f);
        Sound.Play("bag_rustle", null, 0.2f);
        yield return new WaitForSeconds(0.45f);
        Sound.Play("breath_old", null, 0.4f);
        Sound.Play("step_tile", null, 0.5f);
        shoes.SetActive(false);
        leanCane.SetActive(false);
        Sound.Play("cane_tap", null, 0.4f);
        yield return new WaitForSeconds(0.45f);
        Vector3 stand = shoeStand.position;
        stand.z = Mathf.Max(Player.transform.position.z, stand.z);
        Player.Teleport(stand, 0f);
        yield return Player.TurnTo(0f, 0f, 0.01f);
        yield return Hud.I.Fade(0f, Bal.G("Home_ShoeFadeInSec", 0.5f));
        Player.Freeze(false);
        doorUse.active = true;
    }

    // ---- 문 ----

    void OnDoor()
    {
        if (leaving) return;
        leaving = true;
        doorUse.active = false;
        StartCoroutine(Leave());
    }

    IEnumerator Leave()
    {
        Player.Freeze(true);
        yield return Player.LookAt(doorLook.position, 0.5f);
        yield return Hud.I.Say(Me, "자, 나가볼까.", Me + "_go");
        Sound.Play("door_key", null, 0.55f);
        yield return new WaitForSeconds(0.5f);
        Sound.Play("door_handle", null, 0.6f);
        yield return new WaitForSeconds(0.35f);
        Sound.Play("door_open_metal", null, 0.8f);
        doorWant = 1f;
        yield return new WaitForSeconds(0.9f);
        doorBlock.enabled = false;
        StartCoroutine(Player.LookArc(exitPoint.position + Vector3.up * 1.5f, Bal.G("Door_LookInSec", 0.9f)));
        StartCoroutine(Player.WalkTo(exitPoint.position, Bal.F("ExitWalkSpeed", 0.9f)));
        yield return new WaitForSeconds(0.6f);
        GameState.I.CompleteChapter();
    }
}
