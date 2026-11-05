using System;
using UnityEngine;

// 지갑. 왼손, 돋보기와 동시 사용. 임시 T04, T19. 부착: HandRoot (늘 켜져 있는 쪽)
// 배치: note = Hand_Wallet 자식 Note (Readable)
// 배치: cardPart, cashPart, notePart = Hand_Wallet 자식 클릭 자리. 화면에 투영해 Wallet_PartRadius로 판정한다(콜라이더 없음)
public class Wallet : MonoBehaviour
{
    public static Wallet I { get; private set; }

    [SerializeField] Readable note;
    [SerializeField] Transform cardPart;
    [SerializeField] Transform cashPart;
    [SerializeField] Transform notePart;

    public bool Open { get; private set; }

    public event Action NoteRead;     // 쪽지 Readable을 돋보기로 처음 읽을 때
    public event Action NoteMissed;   // 돋보기 없이 쪽지를 눌렀을 때. 대사는 Director가 낸다

    bool noteDone, ownCursor;
    PlayerController.Mode before;
    bool frozenBefore, pointerBefore;

    /// <summary>지갑 위 클릭이라 키오스크가 받으면 안 될 때.</summary>
    public bool Over => Open && (Hit(cardPart) || Hit(cashPart) || Hit(notePart));

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
        if (note != null) note.onRead.AddListener(OnNoteSeen);
    }

    void OnNoteSeen()
    {
        if (noteDone || HandRig.I.Held != ItemId.Lens) return;
        noteDone = true;
        NoteRead?.Invoke();
    }

    public void SetOpen(bool on)
    {
        if (Open == on) return;
        var hands = HandRig.I;
        var pc = PlayerController.I;
        Open = on;
        hands.walletOut = on;
        if (AudioManager.I != null) AudioManager.I.Play("pocket_rummage", null, 0.55f);
        if (Hud.I != null) Hud.I.Items();

        if (on)
        {
            ShowParts();
            // 걷는 중에는 조작을 멈추고 포인터를 낸다. 키오스크 앞은 이미 포인터 모드
            ownCursor = pc.CurrentMode != PlayerController.Mode.Cursor;
            if (!ownCursor) return;
            before = pc.CurrentMode;
            frozenBefore = pc.Frozen;
            pointerBefore = hands.Pointer;
            pc.Freeze(true);
            pc.SetMode(PlayerController.Mode.Cursor);
            hands.SetPointer(true);
        }
        else if (ownCursor)
        {
            ownCursor = false;
            hands.SetPointer(pointerBefore);
            pc.SetMode(before);
            pc.Freeze(frozenBefore);
        }
    }

    // 챕터가 바뀔 때. 모드는 GameState가 정한다
    public void Clear()
    {
        Open = false;
        ownCursor = false;
    }

    public void ResetRun() => noteDone = false;

    void ShowParts()
    {
        var p = GameState.I.Profile;
        if (cardPart != null) cardPart.gameObject.SetActive(p.Has(ItemId.Card));
        if (cashPart != null) cashPart.gameObject.SetActive(p.Has(ItemId.Cash));
        if (notePart != null) notePart.gameObject.SetActive(p.Has(ItemId.Memo));
    }

    bool Hit(Transform part)
    {
        if (part == null || !part.gameObject.activeInHierarchy) return false;
        var eye = PlayerController.I.Eye;
        Vector3 v = eye.WorldToViewportPoint(part.position);
        Vector2 p = HandRig.I.Ptr01();
        float dx = (v.x - p.x) * eye.aspect, dy = v.y - p.y, r = Bal.G("Wallet_PartRadius", 0.07f);
        return dx * dx + dy * dy < r * r;
    }

    void Take(ItemId id)
    {
        var hands = HandRig.I;
        hands.Equip(hands.Held == id ? ItemId.None : id);
        SetOpen(false);   // 집으면 닫는다. 키오스크에서는 지갑이 투입구를 가려 클릭을 먹는다
    }

    void Update()
    {
        if (!Open || !RoundUi.Clicked || PlayerController.I.CurrentMode != PlayerController.Mode.Cursor) return;
        if (Hit(cardPart)) Take(ItemId.Card);
        else if (Hit(cashPart)) Take(ItemId.Cash);
        else if (Hit(notePart) && HandRig.I.Held != ItemId.Lens) NoteMissed?.Invoke();
    }
}
