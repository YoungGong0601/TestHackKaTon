// 현관 진행: 메모를 내리고, 신발을 신고, 문을 열고 나간다.
// 좌표는 HTML판 home.js의 z에 -1을 곱한 값이다.
// 배치: memoUse = MemoUse (Interactable, label 메모 내리기, radius 99, cone -2, 위치 0,1,0)
// 배치: shoesUse = PH_ShoeRack 의 ShoesUse (Interactable, label 신발 신기, radius 2.4, cone 0.78, 위치 0.18,-0.08,1.28)
// 배치: doorUse = PH_Door_Home 의 DoorUse (Interactable, label 문 열기, radius 1.9, cone 0.6, 위치 0,1.0,2.33)
// 배치: shoes = PH_ShoeRack 의 Shoes (바닥의 신발 회색 상자, 신으면 꺼짐)
// 배치: leanCane = LeanCane (벽에 기댄 지팡이 회색 상자, 신으면 꺼짐)
// 배치: shoeLook = ShoeLook (위치 0.18,-0.13,1.25)
// 배치: shoeStand = ShoeStand (위치 0,-0.13,1.2, 신발을 신은 뒤 서는 자리)
// 배치: doorLook = DoorLook (위치 0.1,1.1,2.35)
// 배치: exitPoint = ExitPoint (위치 0,0,2.7, 문 밖)
// 배치: doorHinge = PH_Door_Home 의 Hinge (문짝 부모, 위치 -0.46,-0.13,2.4, 문짝은 +X로 뻗음)
// 배치: doorBlock = PH_Door_Home 의 DoorBlock (문을 막는 콜라이더, 문이 열리면 꺼짐)
// 배치: doorGlow = DoorGlow (문 밖에서 들어오는 Light, 처음엔 컴포넌트 꺼 둠)
// Interactable.onUse는 코드에서 구독한다. 씬에서 UnityEvent를 연결하지 않는다.
using System.Collections;
using UnityEngine;

public class HomeDirector : MonoBehaviour
{
    const float DoorOpenDeg = -85.9f;   // HTML 1.5 rad, 왼손 좌표라 부호 반대
    const float DoorDamp = 2.2f;

    [SerializeField] Interactable memoUse;
    [SerializeField] Interactable shoesUse;
    [SerializeField] Interactable doorUse;
    [SerializeField] GameObject shoes;
    [SerializeField] GameObject leanCane;
    [SerializeField] Transform shoeLook;
    [SerializeField] Transform shoeStand;
    [SerializeField] Transform doorLook;
    [SerializeField] Transform exitPoint;
    [SerializeField] Transform doorHinge;
    [SerializeField] Collider doorBlock;
    [SerializeField] Light doorGlow;

    bool ready, memoUp = true, shoesOn, opened;
    float doorT, doorWant;
    Quaternion doorClosed;

    static string Speaker => GameState.I.Profile.speakerKey;

    void Awake()
    {
        doorClosed = doorHinge.localRotation;
        shoesUse.active = false;
        doorUse.active = false;
    }

    void OnEnable()
    {
        memoUse.onUse.AddListener(LowerMemo);
        shoesUse.onUse.AddListener(PutOnShoes);
        doorUse.onUse.AddListener(OpenDoor);
    }

    void OnDisable()
    {
        memoUse.onUse.RemoveListener(LowerMemo);
        shoesUse.onUse.RemoveListener(PutOnShoes);
        doorUse.onUse.RemoveListener(OpenDoor);
    }

    IEnumerator Start()
    {
        while (Hud.I.TitleOpen) yield return null;
        var player = PlayerController.I;
        var profile = GameState.I.Profile;
        player.SetMode(PlayerController.Mode.Fps);
        player.Freeze(true);
        yield return Hud.I.Fade(1f, 0f);
        AudioManager.I.Ambience(("amb_hallway", 0.5f));
        if (profile.Has(ItemId.Memo))
        {
            HandRig.I.memoScale = Bal.G("Home_MemoScale", 1.34f);
            HandRig.I.Equip(ItemId.Memo);
            player.HoldStill = true;
        }
        yield return new WaitForSeconds(0.1f);
        yield return Hud.I.Fade(0f, Bal.G("Home_FadeInSec", 1.4f));
        player.Freeze(false);
        ready = true;
        if (profile.Has(ItemId.Memo)) yield return Hud.I.Say(Speaker, "불고기 버거 세트... 사이다로. 그래, 그거.", Speaker + "_memo");
    }

    void Update()
    {
        // 숫자 키로 내려도 같은 진행이 되도록 손에 든 물건을 본다.
        if (ready && memoUp && HandRig.I.Held != ItemId.Memo)
        {
            memoUp = false;
            memoUse.active = false;
            shoesUse.active = true;
            PlayerController.I.HoldStill = false;
            HandRig.I.memoScale = 1f;
            Hud.I.Objective("{y:신발}을 신는다", 8f);
        }
        doorT = Mathf.Lerp(doorT, doorWant, 1f - Mathf.Exp(-DoorDamp * Time.deltaTime));
        doorHinge.localRotation = doorClosed * Quaternion.Euler(0f, doorT * DoorOpenDeg, 0f);
    }

    void LowerMemo()
    {
        if (memoUp) HandRig.I.Equip(ItemId.None);
    }

    void PutOnShoes()
    {
        if (memoUp || shoesOn) return;
        shoesOn = true;
        shoesUse.active = false;
        StartCoroutine(ShoesRoutine());
    }

    IEnumerator ShoesRoutine()
    {
        var player = PlayerController.I;
        var audio = AudioManager.I;
        player.Freeze(true);
        yield return player.LookAt(shoeLook.position, 0.6f);
        yield return Hud.I.Fade(1f, Bal.G("Home_ShoeFadeOutSec", 0.4f));
        audio.Play("step_tile", null, 0.5f);
        audio.Play("bag_rustle", null, 0.2f);
        yield return new WaitForSeconds(0.45f);
        bool limp = GameState.I.Profile.limp;
        if (limp) audio.Play("breath_old", null, 0.4f);
        audio.Play("step_tile", null, 0.5f);
        shoes.SetActive(false);
        if (limp)
        {
            leanCane.SetActive(false);
            audio.Play("cane_tap", null, 0.4f);
        }
        yield return new WaitForSeconds(0.45f);
        Vector3 stand = shoeStand.position;
        stand.z = Mathf.Max(player.transform.position.z, stand.z);
        player.Teleport(stand, 0f);
        yield return Hud.I.Fade(0f, Bal.G("Home_ShoeFadeInSec", 0.5f));
        player.Freeze(false);
        doorUse.active = true;
        Hud.I.Objective("{y:문}을 열고 나간다", 8f);
    }

    void OpenDoor()
    {
        if (!shoesOn || opened) return;
        opened = true;
        doorUse.active = false;
        StartCoroutine(LeaveRoutine());
    }

    IEnumerator LeaveRoutine()
    {
        var player = PlayerController.I;
        var audio = AudioManager.I;
        player.Freeze(true);
        yield return player.LookAt(doorLook.position, 0.5f);
        yield return Hud.I.Say(Speaker, "자, 나가볼까.", Speaker + "_go");
        audio.Play("door_key", null, 0.55f);
        yield return new WaitForSeconds(0.5f);
        audio.Play("door_handle", null, 0.6f);
        yield return new WaitForSeconds(0.35f);
        audio.Play("door_open_metal", null, 0.8f);
        doorWant = 1f;
        doorGlow.enabled = true;
        yield return new WaitForSeconds(0.9f);
        doorBlock.enabled = false;
        StartCoroutine(player.WalkTo(exitPoint.position, Bal.F("ExitWalkSpeed", 0.9f)));
        yield return new WaitForSeconds(0.6f);
        GameState.I.CompleteChapter();
    }
}
