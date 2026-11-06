// 1-0 현관 안. Ending_Home과 같은 공간의 낮. 쪽지를 잠깐 펴고, 문을 열고 나가면 R1_Stop 골목으로 이어진다.
// 배치: doorUse = PH_Door_Home 의 DoorUse (label 문 열기), doorHinge = Hinge, doorBlock = DoorBlock, exitPoint = Anchor_Exit (문 밖)
// Interactable.onUse는 코드에서 구독한다.
using System.Collections;
using UnityEngine;

public class R1HomeDirector : MonoBehaviour
{
    const float DoorOpenDeg = -85.9f;

    [SerializeField] Interactable doorUse;
    [SerializeField] Transform doorHinge;
    [SerializeField] Collider doorBlock;
    [SerializeField] Transform exitPoint;

    bool leaving;

    void Awake() => doorUse.active = false;
    void OnEnable() => doorUse.onUse.AddListener(OnDoor);
    void OnDisable() => doorUse.onUse.RemoveListener(OnDoor);

    IEnumerator Start()
    {
        AudioManager.I.Ambience(("amb_city_morning", 0.22f));
        yield return Round.Open();
        Note.Peek();
        doorUse.active = true;
    }

    void OnDoor()
    {
        if (leaving) return;
        leaving = true;
        doorUse.active = false;
        StartCoroutine(Leave());
    }

    IEnumerator Leave()
    {
        var player = PlayerController.I;
        player.Freeze(true);
        AudioManager.I.Play("door_handle", doorHinge.position, 0.8f);
        AudioManager.I.Play("door_open_metal", doorHinge.position, 0.8f);
        Quaternion from = doorHinge.localRotation, to = from * Quaternion.Euler(0f, DoorOpenDeg, 0f);
        float sec = Bal.G("R1_DoorOpenSec", 0.45f);
        for (float t = 0f; t < sec; t += Time.deltaTime)
        {
            doorHinge.localRotation = Quaternion.Slerp(from, to, t / sec);
            yield return null;
        }
        doorHinge.localRotation = to;
        doorBlock.enabled = false;
        StartCoroutine(player.LookArc(exitPoint.position + Vector3.up * 1.5f, Bal.G("Door_LookInSec", 0.9f)));
        yield return StoreFlow.Race(this, player.WalkTo(exitPoint.position, Bal.F("MoveSpeed", 2.2f)), 1.6f);
        GameState.I.CompleteChapter();
    }
}
