using System;
using TMPro;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.InputSystem;

// 카메라에 붙은 손과 소지품. 번호는 ItemKeys가 정한다. 영수증은 돋보기와 같이 써서 StoreDirector가 따로 다룬다
// 위치는 코드가 매 프레임 로컬로 정한다. 부착: Player의 HandRoot
// 배치: lens = HandRoot 자식 Hand_Lens (원점이 렌즈 중심)
// 배치: lensEye = Eye 자식 LensEye (targetTexture RT_Lens, 꺼 둠, 돋보기 들 때만 그린다)
// 배치: card = HandRoot 자식 Hand_Card
// 배치: pointer = HandRoot 자식 Hand_Pointer (+Y가 손가락 방향)
// 배치: pointerTip = Hand_Pointer 자식 Tip (손끝 위치)
// 배치: wallet = HandRoot 자식 Hand_Wallet (펼친 지갑, 자식에 카드, 지폐, 쪽지. 왼손 자리)
// 배치: bill = HandRoot 자식 Hand_Bill (지폐 한 장, Hand_Card와 같은 축)
// 배치: paper = HandRoot 자식 Hand_Note (손에 든 쪽지, 왼손 자리), paperKinds = 그 자식 종이들(0 구겨진 쪽지, 1 포스트잇), paperTexts = 각 종이의 글자. 내용은 Note가 넣는다
// 배치: cane = HandRoot 자식 Hand_Cane (원점이 손잡이, 자식에 PH_Cane). 다리를 저는 인물만 든다
// 배치: briefcase = HandRoot 자식 Hand_Briefcase (원점이 손잡이, 모델은 자식 Visual에 넣는다). 프로필 briefcase 인물만 든다
// 배치: skins = 손 단계별 묶음(look은 프로필 handLook, parts는 소매와 반지까지 그 단계에서 켤 오브젝트)
[Serializable]
public class HandSkin
{
    public int look;
    public GameObject[] parts;
}

public class HandRig : MonoBehaviour
{
    public static HandRig I { get; private set; }

    [SerializeField] Transform lens;
    [SerializeField] Camera lensEye;
    [SerializeField] Transform card;
    [SerializeField] Transform pointer;
    [SerializeField] Transform pointerTip;
    [SerializeField] Transform wallet;
    [SerializeField] Transform bill;
    [SerializeField] Transform paper;
    [SerializeField] GameObject[] paperKinds = new GameObject[0];
    [SerializeField] TMP_Text[] paperTexts = new TMP_Text[0];
    [SerializeField] Transform cane;
    [SerializeField] Transform briefcase;
    [SerializeField] HandSkin[] skins = new HandSkin[0];

    public float tremble;           // 눈치가 쓰는 떨림
    public float paperRate = 9f;    // 쪽지가 올라오는 빠르기
    public bool walletOut;          // Held와 따로 든다. 돋보기와 같이 쓰기 때문
    public float? pointerDist;      // 포인터가 닿는 거리. 없으면 0.6
    public float caseLift;          // 0보다 크면 포인터를 든 동안에도 서류가방을 이만큼 올려 보여 준다

    public ItemId Held { get; private set; }
    // 영수증은 돋보기와 같이 보므로 Held가 아니다. 씬의 Receipt_View를 손에 붙여 오른쪽에서 들어 올린다
    public bool HasReceipt { get; private set; }
    public bool ReceiptOn { get; private set; }
    public bool Pointer { get; private set; }
    public bool ItemsEnabled { get; private set; } = true;
    public Readable LensHit { get; private set; }

    // 인물과 눈치 단계가 더해진다. 시작은 손이나 돋보기가 멈출 때, 물건을 꺼낼 때
    float Shake => Debuff.TrembleAmp(tremble + Debuff.Tremble, Time.time - trembleFrom);
    static float TrembleRad => Bal.G("Tremble_Freq", 1.8f) * Mathf.PI * 2f;

    Transform receiptView;
    float tReceipt, tReceiptLens;
    float trembleFrom = -100f, lastMove;
    bool handMoving;

    static readonly Vector3 Shoulder = new(0.24f, -1f, 0.22f);
    static readonly int LensViewId = Shader.PropertyToID("_LensView");
    static readonly int BaseColorId = Shader.PropertyToID("_BaseColor");

    readonly Ray[] rim = new Ray[6];

    float tap, kick, tLens, tCard, tBill, tWallet, tPaper, tPoint, tCane, tCase, tLift;
    bool paperUp;
    float paperSoft, paperSoftNow = -1f;
    int paperKind;
    RenderTexture lensFull;
    RenderTexture[] lensSmall;

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
    }

    void Start() => RefreshHud();

    void OnEnable() => RenderPipelineManager.beginCameraRendering += MarkLensView;

    void OnDisable()
    {
        RenderPipelineManager.beginCameraRendering -= MarkLensView;
        PostState.Lens = Vector3.zero;
    }

    void OnDestroy()
    {
        if (lensSmall == null) return;
        foreach (var rt in lensSmall) if (rt != null) rt.Release();
    }

    // 초점 흐림: 돋보기 카메라를 더 작은 그림에 찍어 원 안에서 늘린다. 후처리는 PostState.LensTexture를 그대로 그린다
    void FocusLens()
    {
        if (lensFull == null) lensFull = lensEye.targetTexture;
        if (lensFull == null) return;
        if (lensSmall == null)
        {
            lensSmall = new RenderTexture[4];
            for (int i = 0; i < lensSmall.Length; i++)
            {
                int size = Mathf.Max(8, lensFull.width >> (i + 1));
                lensSmall[i] = new RenderTexture(size, size, lensFull.depth, lensFull.format) { filterMode = FilterMode.Bilinear };
            }
        }
        int step = ReceiptOn ? 0 : Mathf.RoundToInt(Debuff.LensBlur01 * lensSmall.Length);   // 영수증은 번지지 않고 읽힌다
        var want = step == 0 ? lensFull : lensSmall[step - 1];
        if (lensEye.targetTexture != want) lensEye.targetTexture = want;
    }

    void MarkLensView(ScriptableRenderContext context, Camera camera) =>
        Shader.SetGlobalFloat(LensViewId, camera == lensEye ? 1f : 0f);

    // 손 모델의 원을 화면으로 옮겨 돋보기 카메라를 그 방향으로 맞춘다. 원 가운데 광선을 돌려주고 rim을 채운다
    Ray LensView(Camera cam)
    {
        FocusLens();
        Vector3 at = cam.WorldToViewportPoint(lens.position);
        Vector3 edge = cam.WorldToViewportPoint(lens.position + cam.transform.up * (Bal.G("Lens_Radius", 0.06f) * lens.localScale.x));
        float radius = Mathf.Abs(edge.y - at.y);
        PostState.Lens = new Vector3(at.x, at.y, radius);
        PostState.LensTexture = lensEye.targetTexture;

        Ray center = cam.ViewportPointToRay(at);
        float tan = radius * 2f * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
        lensEye.transform.SetPositionAndRotation(cam.transform.position, Quaternion.LookRotation(center.direction, cam.transform.up));
        // 영수증을 볼 때는 배율을 낮춘다. 1.45면 렌즈가 겹쳐 보여도 원 안 시야가 종이에 닿지 않는다
        float zoom = ReceiptOn ? Bal.G("Lens_ReceiptZoom", 1.05f) : LensHit != null && LensHit.wide ? Bal.G("Lens_BoardZoom", 1.15f) : Bal.G("Lens_Zoom", 1.45f);
        lensEye.fieldOfView = 2f * Mathf.Atan(tan / Mathf.Max(zoom, 0.01f)) * Mathf.Rad2Deg;
        lensEye.clearFlags = cam.clearFlags;
        lensEye.backgroundColor = cam.backgroundColor;

        for (int i = 0; i < rim.Length; i++)
        {
            float a = i * Mathf.PI * 2f / rim.Length;
            rim[i] = cam.ViewportPointToRay(new Vector3(at.x + Mathf.Cos(a) * radius * 0.75f / cam.aspect, at.y + Mathf.Sin(a) * radius * 0.75f, 0f));
        }
        return center;
    }

    public void Equip(ItemId id)
    {
        if (Held == id) return;
        Held = id;
        if (id != ItemId.None) trembleFrom = Time.time;
        if (AudioManager.I != null) AudioManager.I.Play("pocket_rummage", null, 0.55f);
        RefreshHud();
    }

    // 소리 없이 내려놓음(챕터 전환)
    public void Clear()
    {
        Held = ItemId.None;
        Pointer = false;
        pointerDist = null;
        caseLift = 0f;
        tremble = 0f;
        paperRate = 9f;
        walletOut = false;
        ItemsEnabled = true;
        receiptView = null;
        HasReceipt = false;
        ReceiptOn = false;
        tReceipt = 0f;
        RefreshHud();
    }

    public void SetEnabled(bool on)
    {
        ItemsEnabled = on;
        if (!on) Held = ItemId.None;
        RefreshHud();
    }

    public void SetPointer(bool on) => Pointer = on;

    /// <summary>씬의 영수증 그림을 손에 붙인다. 씬이 끝날 때 부른 쪽이 치운다.</summary>
    public void SetReceiptView(Transform view)
    {
        receiptView = view;
        view.gameObject.SetActive(false);
        view.SetParent(transform, false);
    }

    /// <summary>또렷한 쪽 번호와 메뉴 글자를 넣는다.</summary>
    public void FillReceipt(int number, string lines)
    {
        if (!receiptView) return;
        Transform n = receiptView.Find("Sharp/Number"), l = receiptView.Find("Sharp/Lines");
        if (n && n.TryGetComponent(out TMP_Text nt)) nt.text = number.ToString();
        if (l && l.TryGetComponent(out TMP_Text lt)) lt.text = lines;
    }

    /// <summary>영수증을 얻어 든다. 소지품 줄 끝에 붙는다.</summary>
    public void GiveReceipt()
    {
        HasReceipt = true;
        ReceiptOn = true;
        if (AudioManager.I != null) AudioManager.I.Play("paper_rustle", null, 0.5f);
        RefreshHud();
    }

    public void TakeReceipt()
    {
        HasReceipt = false;
        ReceiptOn = false;
        RefreshHud();
    }

    void MoveReceipt(float dt)
    {
        if (!receiptView) return;
        tReceipt = Damp(tReceipt, ReceiptOn ? 1f : 0f, 9f, dt);
        bool show = tReceipt > 0.01f;
        if (receiptView.gameObject.activeSelf != show) receiptView.gameObject.SetActive(show);
        // 돋보기를 들면 종이를 렌즈 아래로 가져온다. 돋보기는 평소 화면 가운데에 있다
        tReceiptLens = Damp(tReceiptLens, Held == ItemId.Lens ? 1f : 0f, 9f, dt);
        float x = Mathf.Lerp(Bal.G("Hand_ReceiptX", 0.13f), Bal.G("Hand_ReceiptLensX", 0f), tReceiptLens);
        float y = Mathf.Lerp(Bal.G("Hand_ReceiptY", -0.06f), Bal.G("Hand_ReceiptLensY", 0f), tReceiptLens);
        receiptView.localPosition = new Vector3(x, y - (1f - tReceipt) * 0.34f, 0.4f);
    }

    /// <summary>손 자세 자리를 켠다. Pose_ 로 시작하는 자식 중 이름이 맞는 것만 켠다. Pose_Open은 반전 짝(Pose_Open_Mirror)도 같이 켠다.</summary>
    public void SetPose(string pose)
    {
        foreach (Transform c in transform)
            if (c.name.StartsWith("Pose_"))
            {
                c.gameObject.SetActive(c.name.StartsWith(pose));
                var open = c.Find("Visual/Hand_Open");   // 어깨가 아니라 손 자리에서 키워야 화면에서 커진다
                if (open) open.localScale = Vector3.one * Bal.G("Hand_OpenScale", 1.3f);
            }
    }

    public void Tap() => tap = 1f;

    // 지폐가 튕겨 손 쪽으로 밀려난다
    public void Kick() => kick = 1f;

    // 터치가 빗나갈 때 손이 옆으로 빠진다
    public void TapMiss()
    {
        tap = 1f;
        kick = 1f;
        if (AudioManager.I != null) AudioManager.I.Play("card_slide_wrong", null, 0.5f);
    }

    /// <summary>쪽지를 들거나 내린다. body가 있으면 글을 바꾼다. soft 0 또렷, 클수록 번진다.</summary>
    public void SetPaper(bool up, string body = null, float soft = 0f, int kind = 0)
    {
        paperUp = up;
        if (body == null) return;
        paperSoft = soft;
        paperKind = kind;
        for (int i = 0; i < paperKinds.Length; i++) if (paperKinds[i]) paperKinds[i].SetActive(i == kind);
        if (kind < paperTexts.Length && paperTexts[kind]) paperTexts[kind].text = body;
        paperSoftNow = -1f;
    }

    // 들고 있는 쪽지가 화면에서 차지하는 자리. 후처리가 이 자리를 번지지 않게 둔다
    void NoteRect(Camera cam)
    {
        if (paperKind >= paperKinds.Length || !paperKinds[paperKind]) return;
        Vector2 lo = Vector2.one, hi = Vector2.zero;
        foreach (var r in paperKinds[paperKind].GetComponentsInChildren<Renderer>())
        {
            Bounds b = r.bounds;
            for (int i = 0; i < 8; i++)
            {
                Vector3 p = cam.WorldToViewportPoint(b.center + Vector3.Scale(b.extents, new Vector3(i & 1, i >> 1 & 1, i >> 2 & 1) * 2f - Vector3.one));
                lo = Vector2.Min(lo, p);
                hi = Vector2.Max(hi, p);
            }
        }
        PostState.NoteRect = new Vector4(lo.x, lo.y, hi.x, hi.y);
    }

    // 시야가 번지는 인물은 돋보기를 들어야 또렷하다
    void PaperFocus()
    {
        if (paperKind >= paperTexts.Length || !paperTexts[paperKind]) return;
        float want = Held == ItemId.Lens ? 0f : paperSoft;
        if (Mathf.Approximately(want, paperSoftNow)) return;
        paperSoftNow = want;
        paperTexts[paperKind].fontMaterial.SetFloat(ShaderUtilities.ID_OutlineSoftness, want);
    }

    public void ApplyLook(int look)
    {
        foreach (var skin in skins)
            foreach (var part in skin.parts)
                if (part != null) part.SetActive(false);
        foreach (var skin in skins)
        {
            if (skin.look != look) continue;
            foreach (var part in skin.parts)
                if (part != null) part.SetActive(true);
        }
        TintSkin();
    }

    // 나이별 손 색. 재질 이름에 Skin이 든 칸이면 어느 자세, 어느 모델이든 같은 색을 곱한다
    void TintSkin()
    {
        var tint = new Color(Bal.Age("HandTintR", 1.16f, 0.96f, 0.84f, 0.72f), Bal.Age("HandTintG", 1.08f, 0.86f, 0.73f, 0.62f), Bal.Age("HandTintB", 1f, 0.78f, 0.66f, 0.58f));
        var block = new MaterialPropertyBlock();
        foreach (var r in GetComponentsInChildren<Renderer>(true))
        {
            var mats = r.sharedMaterials;
            for (int i = 0; i < mats.Length; i++)
            {
                if (mats[i] == null || !mats[i].name.Contains("Skin") || !mats[i].HasProperty(BaseColorId)) continue;
                r.GetPropertyBlock(block, i);
                block.SetColor(BaseColorId, tint);
                r.SetPropertyBlock(block, i);
            }
        }
    }

    // 떨림이 들어간 포인터(뷰포트 좌표)
    public Vector2 Ptr01()
    {
        float t = Time.time * TrembleRad, j = Shake * Bal.G("Hand_TrembleScale", 0.012f);
        return PlayerController.I.Cursor01 + new Vector2(Mathf.Sin(t * 1.07f) * j * 0.6f, Mathf.Cos(t * 0.93f) * j);
    }

    public Ray PointerRay()
    {
        return PlayerController.I.Eye.ViewportPointToRay(Pointer ? Ptr01() : new Vector2(0.5f, 0.5f));
    }

    void RefreshHud()
    {
        if (Hud.I != null) Hud.I.Items();
    }

    void Toggle(ItemId id)
    {
        var profile = GameState.I != null ? GameState.I.Profile : null;
        if (profile != null && profile.Has(id)) Equip(Held == id ? ItemId.None : id);
    }

    void Keys()
    {
        var kb = Keyboard.current;
        var mode = PlayerController.I.CurrentMode;
        if (kb == null || PauseMenu.On || !ItemsEnabled || mode == PlayerController.Mode.Locked || mode == PlayerController.Mode.Hidden) return;
        if (HasReceipt && ItemKeys.Pressed(kb, ItemId.Receipt))
        {
            ReceiptOn = !ReceiptOn;
            if (AudioManager.I != null) AudioManager.I.Play("paper_rustle", null, 0.5f);
            RefreshHud();
        }
        if (kb.ctrlKey.isPressed) return;   // 시연자 키
        if (ItemKeys.Pressed(kb, ItemId.Lens)) Toggle(ItemId.Lens);
        else if (ItemKeys.Pressed(kb, ItemId.Card)) Toggle(ItemId.Card);
        else if (ItemKeys.Pressed(kb, ItemId.Wallet) && Wallet.I != null)
        {
            Wallet.I.SetOpen(!Wallet.I.Open);
            if (Wallet.I.Open) trembleFrom = Time.time;
        }
    }

    // 움직이던 손이 Tremble_StillSec 동안 멈추면 떨림을 다시 큰 폭에서 시작한다
    void WatchStill()
    {
        var mouse = Mouse.current;
        if (mouse != null && mouse.delta.ReadValue().sqrMagnitude > Bal.G("Tremble_MoveDelta", 4f))
        {
            lastMove = Time.time;
            handMoving = true;
        }
        else if (handMoving && Time.time - lastMove > Bal.G("Tremble_StillSec", 0.12f))
        {
            handMoving = false;
            trembleFrom = Time.time;
        }
    }

    void Update()
    {
        var player = PlayerController.I;
        if (player == null) return;
        Keys();
        WatchStill();

        float dt = Mathf.Min(Time.deltaTime, 0.05f), t = Time.time;
        var cam = player.Eye;
        tap = Damp(tap, 0f, 14f, dt);
        kick = Damp(kick, 0f, 7f, dt);
        tLens = Damp(tLens, Held == ItemId.Lens ? 1f : 0f, 9f, dt);
        tCard = Damp(tCard, Held == ItemId.Card ? 1f : 0f, 9f, dt);
        tBill = Damp(tBill, Held == ItemId.Cash ? 1f : 0f, 9f, dt);
        MoveReceipt(dt);
        tWallet = Damp(tWallet, walletOut ? 1f : 0f, 9f, dt);
        tPaper = Damp(tPaper, paperUp && player.CurrentMode != PlayerController.Mode.Hidden ? 1f : 0f, paperRate, dt);
        tPoint = Damp(tPoint, Pointer && Held == ItemId.None ? 1f : 0f, 9f, dt);

        float sway = Mathf.Sin(t * 1.2f) * 0.003f;
        float jx = Mathf.Sin(t * TrembleRad) * Shake * 0.0035f, jy = Mathf.Cos(t * TrembleRad * 0.8f) * Shake * 0.0035f;

        // 포인터를 따르는 것들: 화면 위치에서 카메라 앞 평면으로
        Vector2 ndc = Pointer ? Ptr01() * 2f - Vector2.one : Vector2.zero;
        const float d = 0.34f;
        float half = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad) * d;
        float tx = ndc.x * half * cam.aspect, ty = ndc.y * half;
        float hit = Pointer ? pointerDist ?? 0.6f : 0.6f;
        // 지갑이 펴지면 손과 돋보기는 지갑보다 앞으로 온다. 화면 자리와 크기는 그대로 둔다
        float front = Bal.G("Hand_WalletFrontDist", 0.26f);
        hit = Mathf.Lerp(hit, Mathf.Min(hit, front), tWallet);
        float near = Mathf.Lerp(1f, front / d, tWallet);
        Vector3 dir = new Vector3(tx, ty, d).normalized;

        if (Show(lens, tLens))
        {
            lens.localPosition = new Vector3(tx, ty - (1f - tLens) * 0.35f, d + tap * 0.02f) * near;
            lens.localScale = Vector3.one * near;
            lens.localRotation = Rad(0f, 0f, -0.12f);
        }

        if (Show(card, tCard))
        {
            if (Pointer)
            {
                Vector3 p = dir * (hit - 0.05f + (tap > 0.1f ? 0.02f * tap : 0f));
                p.y -= (1f - tCard) * 0.35f;
                card.localPosition = p;
            }
            else card.localPosition = new Vector3(tx + 0.1f, ty - 0.11f - (1f - tCard) * 0.35f, d);
            card.localRotation = Rad(0.2f, 0f, -0.1f);
        }

        // 지팡이: 빈손일 때 오른쪽 아래에 들고, 걸음에 맞춰 약하게 흔든다. 원본 street.js makeCane
        var who = GameState.I != null ? GameState.I.Profile : null;
        bool handFree = who != null && ItemsEnabled && Held == ItemId.None && !Pointer && !walletOut
            && player.CurrentMode != PlayerController.Mode.Hidden;
        bool caneOn = handFree && who.limp;
        tCane = Damp(tCane, caneOn ? 1f : 0f, 8f, dt);
        if (Show(cane, tCane))
        {
            float amp = player.Walk01, ph = player.Bob * 0.5f;
            cane.localPosition = new Vector3(0.3f + Mathf.Sin(ph) * 0.008f * amp, Bal.G("Hand_CaneY", -0.13f) - (1f - tCane) * 0.4f + Mathf.Abs(Mathf.Sin(ph)) * 0.022f * amp, 0.5f);
            cane.localRotation = Rad(-0.32f - Mathf.Cos(ph) * 0.11f * amp, 0f, 0.13f);
        }

        // 서류가방: 지팡이와 같은 자리에서 빈손일 때만 윗부분이 보인다. 쪽지와 영수증을 볼 때도 내린다
        tCase = Damp(tCase, who != null && who.briefcase && (handFree || caseLift > 0f) && !paperUp && !ReceiptOn ? 1f : 0f, 8f, dt);
        tLift = Damp(tLift, caseLift, 6f, dt);
        if (Show(briefcase, tCase))
        {
            float amp = player.Walk01, ph = player.Bob * 0.5f, swing = Bal.G("Hand_BriefcaseSway", 0.012f);
            briefcase.localPosition = new Vector3(Bal.G("Hand_BriefcaseX", 0.42f) + Mathf.Sin(ph) * swing * amp,
                Bal.G("Hand_BriefcaseY", -0.27f) + tLift - (1f - tCase) * 0.4f + Mathf.Abs(Mathf.Sin(ph)) * swing * amp, Bal.G("Hand_BriefcaseZ", 0.5f));
            briefcase.localRotation = Rad(-0.05f, Bal.G("Hand_BriefcaseYaw", 1.25f), Mathf.Sin(ph) * swing * 3f * amp);
        }

        if (Show(bill, tBill))
        {
            if (Pointer)
            {
                Vector3 p = dir * (hit - 0.05f - kick * 0.14f + (tap > 0.1f ? 0.02f * tap : 0f));
                p.y -= (1f - tBill) * 0.35f;
                bill.localPosition = p;
            }
            else bill.localPosition = new Vector3(tx + 0.1f, ty - 0.11f - (1f - tBill) * 0.35f, d);
            bill.localRotation = Rad(0.2f, 0f, -0.1f);
        }

        // 지갑: 왼손 자리. 돋보기와 지폐를 든 손은 오른쪽에서 온다
        if (Show(wallet, tWallet))
        {
            wallet.localPosition = new Vector3(-0.1f * cam.aspect / 1.78f + jx, -0.34f + tWallet * 0.24f + sway + jy, 0.34f);
            wallet.localRotation = Rad(0.25f, -0.12f, 0.03f);
        }

        // 쪽지: 왼손 자리. 흔들림은 지갑과 같은 만큼만
        if (Show(paper, tPaper))
        {
            PaperFocus();
            paper.localPosition = new Vector3(Bal.G("Note_HandX", -0.09f) * cam.aspect / 1.78f + jx, Bal.G("Note_HandY", -0.06f) - (1f - tPaper) * 0.3f + sway + jy, Bal.G("Note_HandZ", 0.34f));
            paper.localRotation = Rad(0.14f, -0.1f, 0.07f);
            NoteRect(cam);
        }
        else PostState.NoteRect = Vector4.zero;

        if (Show(pointer, tPoint))
        {
            // 손끝이 포인터가 맞은 지점에 닿도록 어깨에서 뻗은 팔
            Vector3 tip = dir * (hit - 0.0102f - 0.03f * (1f - tap));
            Vector3 armY = (tip - Shoulder).normalized;
            pointer.localRotation = Quaternion.LookRotation(new Vector3(0.1f, 0.25f, 1f), armY);
            Vector3 toTip = pointerTip != null ? transform.InverseTransformVector(pointerTip.position - pointer.position) : Vector3.zero;
            Vector3 p = tip - toTip;
            p.y -= (1f - tPoint) * 0.35f;
            pointer.localPosition = p;
        }

        bool lensOn = Held == ItemId.Lens && lens != null && lensEye != null;
        Ray aim = lensOn ? LensView(cam) : PointerRay();
        if (!lensOn) PostState.Lens = Vector3.zero;
        if (lensEye != null && lensEye.enabled != lensOn) lensEye.enabled = lensOn;
        // 지갑과 쪽지 종이는 HandModel이라 돋보기 그림에 넣어야 뒤 풍경이 비치지 않는다
        if (lensEye != null)
        {
            int handMask = LayerMask.GetMask("HandModel");
            bool handInLens = walletOut || tPaper > 0.01f || tReceipt > 0.01f;
            lensEye.cullingMask = handInLens ? lensEye.cullingMask | handMask : lensEye.cullingMask & ~handMask;
        }
        // 초점이 나간 동안에는 글이 읽히지 않는다
        bool focused = Debuff.LensFocused;
        LensHit = Readable.Aim(aim, Held == ItemId.Lens && focused, lensOn && focused ? rim : null);
    }

    static bool Show(Transform item, float k)
    {
        if (item == null) return false;
        bool on = k > 0.01f;
        if (item.gameObject.activeSelf != on) item.gameObject.SetActive(on);
        return on;
    }

    static Quaternion Rad(float x, float y, float z) => Quaternion.Euler(x * Mathf.Rad2Deg, y * Mathf.Rad2Deg, z * Mathf.Rad2Deg);

    static float Damp(float a, float b, float k, float dt) => Mathf.Lerp(a, b, 1f - Mathf.Exp(-k * dt));
}
