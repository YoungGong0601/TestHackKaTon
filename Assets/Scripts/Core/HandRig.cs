using System;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.InputSystem;

// 카메라에 붙은 손과 소지품. 1 메모 2 돋보기 3 카드, Q 메모. 영수증은 돋보기와 같이 써서 StoreDirector가 따로 다룬다
// 위치는 코드가 매 프레임 로컬로 정한다. 부착: Player의 HandRoot
// 배치: lens = HandRoot 자식 Hand_Lens (원점이 렌즈 중심)
// 배치: lensEye = Eye 자식 LensEye (targetTexture RT_Lens, 꺼 둠, 돋보기 들 때만 그린다)
// 배치: card = HandRoot 자식 Hand_Card
// 배치: pointer = HandRoot 자식 Hand_Pointer (+Y가 손가락 방향)
// 배치: pointerTip = Hand_Pointer 자식 Tip (손끝 위치)
// 배치: wallet = HandRoot 자식 Hand_Wallet (펼친 지갑, 자식에 카드, 지폐, 쪽지. 왼손 자리)
// 배치: bill = HandRoot 자식 Hand_Bill (지폐 한 장, Hand_Card와 같은 축)
// 배치: watch = HandRoot 자식 Hand_Watch (왼 손목과 시계판), watchHour = 그 자식 HourHand (시계판 중심, +Y가 12시)
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
    [SerializeField] Transform watch;
    [SerializeField] Transform watchHour;
    [SerializeField] HandSkin[] skins = new HandSkin[0];

    public float tremble;           // 눈치가 쓰는 떨림
    public bool walletOut;          // Held와 따로 든다. 돋보기와 같이 쓰기 때문
    public float? pointerDist;      // 포인터가 닿는 거리. 없으면 0.6

    public ItemId Held { get; private set; }
    public bool Pointer { get; private set; }
    public bool ItemsEnabled { get; private set; } = true;
    public Readable LensHit { get; private set; }

    float Shake => Mathf.Max(tremble, Debuff.Tremble);

    static readonly Vector3 Shoulder = new(0.24f, -1f, 0.22f);
    static readonly int LensViewId = Shader.PropertyToID("_LensView");

    readonly Ray[] rim = new Ray[6];

    float tap, kick, tLens, tCard, tBill, tWallet, tWatch, tPoint;
    bool watchUp;
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
        int step = Mathf.RoundToInt(Debuff.LensBlur01 * lensSmall.Length);
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
        Vector3 edge = cam.WorldToViewportPoint(lens.position + cam.transform.up * Bal.G("Lens_Radius", 0.06f));
        float radius = Mathf.Abs(edge.y - at.y);
        PostState.Lens = new Vector3(at.x, at.y, radius);
        PostState.LensTexture = lensEye.targetTexture;

        Ray center = cam.ViewportPointToRay(at);
        float tan = radius * 2f * Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad);
        lensEye.transform.SetPositionAndRotation(cam.transform.position, Quaternion.LookRotation(center.direction, cam.transform.up));
        lensEye.fieldOfView = 2f * Mathf.Atan(tan / Mathf.Max(Bal.G("Lens_Zoom", 1.45f), 0.01f)) * Mathf.Rad2Deg;
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
        if (AudioManager.I != null) AudioManager.I.Play("pocket_rummage", null, 0.55f);
        RefreshHud();
    }

    // 소리 없이 내려놓음(챕터 전환)
    public void Clear()
    {
        Held = ItemId.None;
        Pointer = false;
        pointerDist = null;
        tremble = 0f;
        walletOut = false;
        ItemsEnabled = true;
        RefreshHud();
    }

    public void SetEnabled(bool on)
    {
        ItemsEnabled = on;
        if (!on) Held = ItemId.None;
        RefreshHud();
    }

    public void SetPointer(bool on) => Pointer = on;

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

    public void ShowWatch(int hour)
    {
        watchUp = true;
        if (watchHour != null) watchHour.localRotation = Quaternion.Euler(0f, 0f, -hour * 30f);
    }

    public void HideWatch() => watchUp = false;

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
    }

    // 떨림이 들어간 포인터(뷰포트 좌표)
    public Vector2 Ptr01()
    {
        float t = Time.time, j = Shake * Bal.G("Hand_TrembleScale", 0.012f);
        return PlayerController.I.Cursor01 + new Vector2(Mathf.Sin(t * 31f) * j * 0.6f, Mathf.Cos(t * 27f) * j);
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
        if (kb == null || !ItemsEnabled || mode == PlayerController.Mode.Locked || mode == PlayerController.Mode.Hidden) return;
        if (kb.ctrlKey.isPressed) return;   // 시연자 키
        if (kb.digit2Key.wasPressedThisFrame) Toggle(ItemId.Lens);
        else if (kb.digit3Key.wasPressedThisFrame)
        {
            var profile = GameState.I != null ? GameState.I.Profile : null;
            if (profile != null && profile.Has(ItemId.Wallet) && Wallet.I != null) Wallet.I.SetOpen(!Wallet.I.Open);
            else Toggle(ItemId.Card);
        }
    }

    void Update()
    {
        var player = PlayerController.I;
        if (player == null) return;
        Keys();

        float dt = Mathf.Min(Time.deltaTime, 0.05f), t = Time.time;
        var cam = player.Eye;
        tap = Damp(tap, 0f, 14f, dt);
        kick = Damp(kick, 0f, 7f, dt);
        tLens = Damp(tLens, Held == ItemId.Lens ? 1f : 0f, 9f, dt);
        tCard = Damp(tCard, Held == ItemId.Card ? 1f : 0f, 9f, dt);
        tBill = Damp(tBill, Held == ItemId.Cash ? 1f : 0f, 9f, dt);
        tWallet = Damp(tWallet, walletOut ? 1f : 0f, 9f, dt);
        tWatch = Damp(tWatch, watchUp ? 1f : 0f, 9f, dt);
        tPoint = Damp(tPoint, Pointer && Held == ItemId.None ? 1f : 0f, 9f, dt);

        float sway = Mathf.Sin(t * 1.2f) * 0.003f;
        float jx = Mathf.Sin(t * 29f) * Shake * 0.0035f, jy = Mathf.Cos(t * 23f) * Shake * 0.0035f;

        // 포인터를 따르는 것들: 화면 위치에서 카메라 앞 평면으로
        Vector2 ndc = Pointer ? Ptr01() * 2f - Vector2.one : Vector2.zero;
        const float d = 0.34f;
        float half = Mathf.Tan(cam.fieldOfView * 0.5f * Mathf.Deg2Rad) * d;
        float tx = ndc.x * half * cam.aspect, ty = ndc.y * half;
        float hit = Pointer ? pointerDist ?? 0.6f : 0.6f;
        Vector3 dir = new Vector3(tx, ty, d).normalized;

        if (Show(lens, tLens))
        {
            lens.localPosition = new Vector3(tx, ty - (1f - tLens) * 0.35f, d + tap * 0.02f);
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

        if (Show(watch, tWatch))
        {
            watch.localPosition = new Vector3(-0.05f + jx, -0.34f + tWatch * 0.26f + jy, 0.3f);
            watch.localRotation = Rad(-0.5f, 0f, 0f);
        }

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
