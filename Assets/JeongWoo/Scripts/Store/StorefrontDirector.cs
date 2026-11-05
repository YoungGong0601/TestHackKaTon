// 매장 앞: 간판을 올려다보고, 유리문을 밀다가 당긴다. Storefront 씬 Director 오브젝트에 부착.
// 좌표는 HTML판 값의 z에 -1을 곱한 Unity 좌표.
// 배치: signLook = Anchor_SignLook (-0.1, 3.72, -3.8) 간판 로고
// 배치: doorLook = Anchor_DoorLook (1.475, 1.32, -3.8) 문 스티커 높이
// 배치: doorHandle = Anchor_DoorHandle (1.775, 1.1, -3.86) 손잡이, 소리 위치
// 배치: doorPivot = PH_Door_Glass 안의 DoorPivot (경첩, x 0.935, z -3.8) 자식으로 문짝
// 배치: doorBlock = Door_Block 문을 막는 콜라이더, 당겨서 열리면 꺼짐
// 배치: pullStand = Anchor_PullStand (1.78, 0, -5.15) 문이 열릴 때 비켜 서는 자리
// 배치: insideLook = Anchor_InsideLook (1.4, 1.4, -1.8) 들어가며 보는 곳
// 배치: insidePoint = Anchor_InsidePoint (1.52, 0, -3.4) 문 안쪽 도착점
// 배치: pushDoor = Interact_DoorPush (Interactable, label 밀기, key E, radius 2.1, cone 0.72)
// 배치: pullDoor = Interact_DoorPull (Interactable, label 당기기, key R, radius 2.1, cone 0.72, active 끔)
// 배치: sticker = Sticker_Pull (Readable, 문짝 자식, 글자 당기세요)
// 배치: eater = NPC_Eater (NpcMover, 유리 너머 손님 (2.75, 0, -2.3))
// 배치: bus = PH_Bus (-6, 0, -11.4, 회전 Y 180, 문이 인도 쪽), 떠나는 버스. 없어도 동작
// 배치: doorRoot = PH_Door_Glass (안으로 들어서면 다음 씬의 문으로 바뀜)
// 배치: stayOut = Interior Light, PH_Table, NPC_Eater (다음 씬을 미리 불러오면 그쪽 것으로 대신함)
// 다음 챕터가 같은 인물의 매장이면 시작할 때 Additive로 미리 불러 같은 좌표에 둔다. 유리 너머로 보이고 암전 없이 이어 들어간다.
// 이 씬의 바닥, 벽, 천장, 정면과 거리는 들어간 뒤에도 남아 유리 밖 풍경이 된다. 못 불러오면 예전처럼 암전 후 CompleteChapter.
using System.Collections;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

public class StorefrontDirector : MonoBehaviour
{
    [SerializeField] Transform signLook;
    [SerializeField] Transform doorLook;
    [SerializeField] Transform doorHandle;
    [SerializeField] Transform doorPivot;
    [SerializeField] Collider doorBlock;
    [SerializeField] Transform pullStand;
    [SerializeField] Transform insideLook;
    [SerializeField] Transform insidePoint;
    [SerializeField] Interactable pushDoor;
    [SerializeField] Interactable pullDoor;
    [SerializeField] Readable sticker;
    [SerializeField] NpcMover eater;
    [SerializeField] Transform bus;
    [SerializeField] GameObject doorRoot;
    [SerializeField] GameObject[] stayOut;

    StoreDirector store;
    int tries;
    bool pushing, leaving, busGo;
    float busV = 0.5f;

    // 문 각도는 HTML판 부호(안쪽으로 밀리면 +, 당기면 -), 라디안
    float doorA, doorV;
    bool doorHeld;
    float doorHold;
    Quaternion doorBase;

    string Me => GameState.I.Profile.speakerKey;
    Vector3 Handle => doorHandle.position;

    void Awake()
    {
        doorBase = doorPivot.localRotation;
    }

    void OnEnable()
    {
        pushDoor.onUse.AddListener(OnPush);
        pullDoor.onUse.AddListener(OnPull);
        if (sticker) sticker.onRead.AddListener(RevealPull);
    }

    void OnDisable()
    {
        pushDoor.onUse.RemoveListener(OnPush);
        pullDoor.onUse.RemoveListener(OnPull);
        if (sticker) sticker.onRead.RemoveListener(RevealPull);
    }

    void Start()
    {
        pullDoor.active = false;
        StartCoroutine(Intro());
    }

    IEnumerator Preload()
    {
        var game = GameState.I;
        int next = game.chapterIndex + 1;
        if (game.flow == null || next >= game.flow.chapters.Count) yield break;
        ChapterEntry entry = game.flow.chapters[next];
        if (entry.profile != game.Profile) yield break;

        StoreDirector.PreviewNext = true;
        AsyncOperation op = JWScenes.Load(entry.sceneName, LoadSceneMode.Additive);
        while (op != null && !op.isDone) yield return null;
        StoreDirector.PreviewNext = false;

        store = StoreDirector.Waiting;
        if (!store)
        {
            if (op != null) SceneManager.UnloadSceneAsync(entry.sceneName);
            yield break;
        }
        foreach (GameObject g in stayOut) g.SetActive(false);
        if (store.Eater) eater = store.Eater;
    }

    IEnumerator Intro()
    {
        var player = PlayerController.I;
        yield return Preload();
        AudioManager.I.Ambience(("amb_city_morning", 0.5f));
        player.SetMode(PlayerController.Mode.Fps);
        player.Freeze(true);
        HandRig.I.SetEnabled(false);
        if (bus)
        {
            AudioManager.I.Play("bus_leave", bus.position + Vector3.up, 0.7f);
            busGo = true;
        }
        Hud.I.Fade(0f, 1.2f);
        yield return new WaitForSeconds(0.9f);
        yield return player.LookAt(signLook.position, Bal.G("Door_SignLookSec", 3.2f));
        yield return new WaitForSeconds(Bal.G("Door_SignHoldSec", 1.1f));
        yield return player.LookAt(doorLook.position, 1.8f);
        Hud.I.Objective("{y:유리문}", 5f);
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
            if (tries == 3) StartCoroutine(EaterLook());   // 겹치면 돌아간 각도를 원래 각도로 잡는다
            yield return Shove(Bal.I("Door_Shove3Count", 5), Bal.G("Door_Shove3Power", 1.3f));
            RevealPull();
        }
        pushing = false;
    }

    IEnumerator Shove(int count, float strength)
    {
        HandRig.I.SetPointer(true);
        for (int i = 0; i < count; i++)
        {
            yield return new WaitForSeconds(0.13f);
            AudioManager.I.Play("door_rattle", Handle, 0.9f);
            HandRig.I.Tap();
            doorV += Bal.G("Door_Kick", 0.55f) * strength;
            PlayerController.I.AddShake(Bal.G("Door_Shake", 0.5f) * strength);
            yield return new WaitForSeconds(0.2f);
        }
        yield return new WaitForSeconds(0.12f);
        HandRig.I.SetPointer(false);
    }

    IEnumerator EaterLook()
    {
        if (!eater) yield break;
        float y0 = eater.transform.eulerAngles.y;
        eater.FaceYaw(y0 - 60f, 4f);   // 앉은 채로 고개만 돌아보는 정도. 문까지 다 돌면 다리가 의자를 뚫는다
        yield return new WaitForSeconds(2.6f);
        eater.FaceYaw(y0, 4f);
    }

    void RevealPull()
    {
        if (leaving || pullDoor.active) return;
        pullDoor.active = true;
        Hud.I.Say(Me, "이건 또 뭐야.", Me + "_why3");
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
        HandRig.I.Equip(ItemId.None);
        AudioManager.I.Play("door_handle", Handle, 0.8f);
        Coroutine say = Hud.I.Say(Me, "아, 당기는 거구먼.", Me + "_door3");
        Coroutine step = StartCoroutine(player.WalkTo(pullStand.position, Bal.F("DoorStepSpeed", 0.9f)));
        yield return new WaitForSeconds(0.45f);
        AudioManager.I.Play("door_glass_open", Handle, 0.8f);
        AudioManager.I.Play("door_chime", Handle, 0.75f);
        doorHeld = true;
        doorHold = -Bal.G("Door_OpenAngle", 1.45f);
        yield return say;
        StopCoroutine(step);
        doorBlock.enabled = false;
        if (store) StartCoroutine(BlendAmbient(Bal.G("Door_AmbientBlendSec", 1.6f)));
        yield return StoreFlow.Race(this, player.LookAt(insideLook.position, 0.7f), 0.8f);
        yield return StoreFlow.Race(this, player.WalkTo(insidePoint.position, Bal.F("MoveSpeed", 1.15f)), 3f);
        if (store)
        {
            GameState.I.chapterIndex++;
            doorRoot.SetActive(false);
            store.EnterFromDoor(-doorA);
            yield break;
        }
        yield return Hud.I.Fade(1f, 0.7f);
        GameState.I.CompleteChapter();
    }

    // 매장 씬의 앰비언트는 위아래 없이 한 색이다. 활성 씬이 바뀔 때 밝기가 튀지 않게 걸어 들어가는 동안 맞춘다
    IEnumerator BlendAmbient(float sec)
    {
        Color equator = RenderSettings.ambientEquatorColor, ground = RenderSettings.ambientGroundColor;
        Color sky = RenderSettings.ambientSkyColor;
        for (float t = 0f; t < sec && RenderSettings.ambientMode == AmbientMode.Trilight; t += Time.deltaTime)
        {
            float u = t / sec;
            RenderSettings.ambientEquatorColor = Color.Lerp(equator, sky, u);
            RenderSettings.ambientGroundColor = Color.Lerp(ground, sky, u);
            yield return null;
        }
    }

    void Update()
    {
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
