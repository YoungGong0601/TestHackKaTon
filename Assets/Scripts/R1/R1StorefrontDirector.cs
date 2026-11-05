// 1-4 버거집 앞. 당기기 하나만 활성, 한 번에 열린다(T20). 4회차와 같은 문, 같은 스티커.
// 배치: doorHandle = Anchor_DoorHandle, doorPivot = PH_Door_Glass 안 DoorPivot, doorBlock = Door_Block
// 배치: pullStand, insideLook, insidePoint = 기존 앵커
// 배치: pullDoor = Interact_DoorPull (label 당기기, key E), pushDoor = Interact_DoorPush (이 씬에서는 쓰지 않음)
// 배치: bus = PH_Bus 떠나는 버스, 없어도 동작
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
    [SerializeField] Interactable pullDoor;
    [SerializeField] Interactable pushDoor;
    [SerializeField] Transform bus;

    bool leaving, busGo;
    float busV = 0.5f, doorA, doorWant;
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
        if (bus)
        {
            AudioManager.I.Play("bus_leave", bus.position + Vector3.up, 0.7f);
            busGo = true;
        }
        yield return Round.Open();
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
        AudioManager.I.Play("door_handle", handle, 0.8f);
        Coroutine step = StartCoroutine(player.WalkTo(pullStand.position, Bal.F("MoveSpeed", 2.2f)));
        yield return new WaitForSeconds(0.25f);
        AudioManager.I.Play("door_glass_open", handle, 0.8f);
        AudioManager.I.Play("door_chime", handle, 0.75f);
        doorWant = Bal.G("Door_OpenAngle", 1.45f);
        yield return new WaitForSeconds(0.55f);
        StopCoroutine(step);
        doorBlock.enabled = false;
        yield return StoreFlow.Race(this, player.LookAt(insideLook.position, 0.4f), 0.45f);
        yield return StoreFlow.Race(this, player.WalkTo(insidePoint.position, Bal.F("MoveSpeed", 2.2f)), 1.6f);
        GameState.I.CompleteChapter();
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
        doorA = StoreFlow.Damp(doorA, doorWant, 5f, dt);
        doorPivot.localRotation = doorBase * Quaternion.Euler(0f, doorA * Mathf.Rad2Deg, 0f);
    }
}
