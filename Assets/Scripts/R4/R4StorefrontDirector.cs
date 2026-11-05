// 4-0~4-2: 지갑 속 쪽지를 돋보기로 읽어야 걷는다. 문은 E로 밀고, 스티커를 돋보기로 읽으면 R 당기기가 생긴다.
// R4_Storefront 씬 Director 오브젝트에 부착. 문 물리는 StorefrontDirector를 복사했다.
// 배치: doorHandle = Anchor_DoorHandle, doorPivot = PH_Door_Glass 안 DoorPivot
// 배치: doorBlock = Door_Block, pullStand = Anchor_PullStand, insideLook = Anchor_InsideLook, insidePoint = Anchor_InsidePoint
// 배치: pushDoor = Interact_DoorPush (label 밀기, key E), pullDoor = Interact_DoorPull (label 당기기, key R)
// 배치: sticker = Sticker_Pull (Readable)
using System.Collections;
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
    bool opened, noteRead, pushing, leaving, muttering;

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
        yield return Round.Open();
        Wallet.I.NoteRead += OnNoteRead;
        Wallet.I.NoteMissed += Mutter;
        Wallet.I.SetOpen(true);   // 임시 T19
        opened = true;
    }

    void OnNoteRead()
    {
        if (noteRead) return;
        noteRead = true;
        AudioManager.I.Play("paper_rustle", null, 0.5f);
        StartCoroutine(StartWalking());
    }

    // 쪽지를 볼 틈을 준 뒤 지갑을 닫고 걷기 시작한다
    IEnumerator StartWalking()
    {
        yield return new WaitForSeconds(Bal.G("R4_NoteHoldSec", 2f));
        Wallet.I.SetOpen(false);
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
        yield return Hud.I.Say(null, "뭐라고 썼더라.", Me + "_note");
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
        else
        {
            yield return Shove(Bal.I("Door_Shove2Count", 3), Bal.G("Door_Shove2Power", 1.1f));
            yield return Hud.I.Say(null, "잠겼나?", Me + "_door2");
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
        yield return StoreFlow.Race(this, player.WalkTo(insidePoint.position, Bal.F("MoveSpeed", 0.9f)), 3f);
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
        if (noteRead && !leaving && !pullDoor.active && sticker && sticker.Seen) pullDoor.active = true;

        float dt = Time.deltaTime;
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
