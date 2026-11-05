// 게임의 첫 장면, 버거집 앞. 쪽지를 잠깐 펴고 당기기 하나만 활성, 한 번에 열린다(T20). 4회차와 같은 문, 같은 스티커.
// 배치: doorHandle = Anchor_DoorHandle, doorPivot = PH_Door_Glass 안 DoorPivot, doorBlock = Door_Block
// 배치: pullStand, insideLook, insidePoint = 기존 앵커
// 배치: introStart, introBend, introEnd = Anchor_IntroStart, Anchor_IntroBend, Anchor_IntroEnd (시작 걷기 곡선), signLook = PH_Storefront 안 Anchor_SignLook
// 배치: pullDoor = Interact_DoorPull (label 당기기, key E), pushDoor = Interact_DoorPush (이 씬에서는 쓰지 않음)
using System.Collections;
using UnityEngine;

public class R1StorefrontDirector : MonoBehaviour
{
    [SerializeField] Transform doorHandle;
    [SerializeField] Transform doorPivot;
    [SerializeField] Collider doorBlock;
    [SerializeField] Transform pullStand;
    [SerializeField] Transform insideLook;
    [SerializeField] Transform insidePoint;
    [SerializeField] Transform introStart;
    [SerializeField] Transform introBend;
    [SerializeField] Transform introEnd;
    [SerializeField] Transform signLook;
    [SerializeField] Interactable pullDoor;
    [SerializeField] Interactable pushDoor;

    bool leaving;
    float doorA, doorWant;
    Quaternion doorBase;

    void Awake()
    {
        doorBase = doorPivot.localRotation;
        pullDoor.active = true;
        if (pushDoor) pushDoor.active = false;
    }

    void OnEnable() => pullDoor.onUse.AddListener(OnPull);
    void OnDisable() => pullDoor.onUse.RemoveListener(OnPull);

    IEnumerator Start()
    {
        AudioManager.I.Ambience(("amb_city_morning", 0.5f));
        var player = PlayerController.I;
        if (!introStart || !introBend || !introEnd || !signLook)
        {
            yield return Round.Open();
            Note.Peek();
            yield break;
        }
        Vector3 way = introBend.position - introStart.position;
        player.Teleport(introStart.position, Mathf.Atan2(way.x, way.z) * Mathf.Rad2Deg);
        yield return Round.Open();
        player.Freeze(true);
        // 걷는 도중에 시선이 간판으로 옮겨 가고, 이어서 문으로 간다. 서서 기다리는 구간을 두지 않는다
        float walkSec = Bal.G("R1_IntroWalkSec", 3f), turnSec = Bal.G("R1_IntroTurnSec", 1.1f);
        Coroutine walking = StartCoroutine(player.WalkCurve(introEnd.position, introBend.position, walkSec));
        yield return new WaitForSeconds(walkSec * Bal.G("R1_IntroLookAt", 0.4f));
        yield return player.LookArc(signLook.position, turnSec);
        yield return new WaitForSeconds(Bal.G("R1_IntroSignSec", 0.9f));
        yield return player.LookArc(doorHandle.position, turnSec);
        yield return walking;
        yield return new WaitForSeconds(Bal.G("R1_IntroDoorSec", 0.3f));
        yield return new WaitForSeconds(Bal.G("R1_IntroNoteDelay", 0.2f));
        HandRig.I.paperRate = Bal.G("R1_IntroNoteRate", 2.5f);
        Note.Peek();
        yield return new WaitForSeconds(Bal.G("R1_IntroNoteRiseSec", 1.2f));
        HandRig.I.paperRate = 9f;
        player.Freeze(false);
    }

    void OnPull()
    {
        if (leaving) return;
        leaving = true;
        pullDoor.active = false;
        StartCoroutine(Pull());
    }

    IEnumerator Pull()
    {
        var player = PlayerController.I;
        Vector3 handle = doorHandle.position;
        player.Freeze(true);
        HandRig.I.Equip(ItemId.None);
        StartCoroutine(player.LookArc(handle, Bal.G("Door_LookSec", 0.5f)));
        AudioManager.I.Play("door_handle", handle, 0.8f);
        Coroutine step = StartCoroutine(player.WalkTo(pullStand.position, Bal.F("MoveSpeed", 2.2f)));
        yield return new WaitForSeconds(0.25f);
        AudioManager.I.Play("door_chime", handle, 0.75f);
        doorWant = Bal.G("Door_OpenAngle", 1.45f);
        yield return new WaitForSeconds(0.55f);
        StopCoroutine(step);
        doorBlock.enabled = false;
        StartCoroutine(player.LookArc(insideLook.position, Bal.G("Door_LookInSec", 0.9f)));
        yield return StoreFlow.Race(this, player.WalkTo(insidePoint.position, Bal.F("MoveSpeed", 2.2f)), 1.6f);
        GameState.I.CompleteChapter();
    }

    void Update()
    {
        float dt = Time.deltaTime;
        doorA = StoreFlow.Damp(doorA, doorWant, 5f, dt);
        doorPivot.localRotation = doorBase * Quaternion.Euler(0f, doorA * Mathf.Rad2Deg, 0f);
    }
}
