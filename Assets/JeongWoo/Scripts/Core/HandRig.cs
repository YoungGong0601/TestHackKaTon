using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.InputSystem;

// 카메라에 붙은 손과 소지품. 1 메모 2 돋보기 3 카드, Q 메모. 영수증은 돋보기와 같이 써서 StoreDirector가 따로 다룬다
// 위치는 코드가 매 프레임 로컬로 정한다. 부착: Player의 HandRoot
// 배치: memo = HandRoot 자식 Hand_Memo (회색 판, 글자 손자가 부탁한 것 / 시장 입구 버거대왕 / 불고기 버거 세트 / 콜라 말고 사이다로 / 포장 /)
// 배치: lens = HandRoot 자식 Hand_Lens (원점이 렌즈 중심)
// 배치: lensEye = Eye 자식 LensEye (targetTexture RT_Lens, 꺼 둠, 돋보기 들 때만 그린다)
// 배치: card = HandRoot 자식 Hand_Card
// 배치: pointer = HandRoot 자식 Hand_Pointer (+Y가 손가락 방향)
// 배치: pointerTip = Hand_Pointer 자식 Tip (손끝 위치)
public class HandRig : MonoBehaviour
{
    public static HandRig I { get; private set; }

    [SerializeField] Transform memo;
    [SerializeField] Transform lens;
    [SerializeField] Camera lensEye;
    [SerializeField] Transform card;
    [SerializeField] Transform pointer;
    [SerializeField] Transform pointerTip;

    public float tremble;
    public bool memoSide;           // 화면을 가리지 않게 왼쪽으로 비킴
    public float memoScale = 1f;    // 혼자 읽을 때 크게
    public float? pointerDist;      // 포인터가 닿는 거리. 없으면 0.6

    public ItemId Held { get; private set; }
    public bool Pointer { get; private set; }
    public bool ItemsEnabled { get; private set; } = true;
    public Readable LensHit { get; private set; }

    static readonly Vector3 Shoulder = new(0.24f, -1f, 0.22f);
    static readonly int LensViewId = Shader.PropertyToID("_LensView");

    readonly Ray[] rim = new Ray[6];

    float tap, tMemo, tLens, tCard, tPoint;

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

    void MarkLensView(ScriptableRenderContext context, Camera camera) =>
        Shader.SetGlobalFloat(LensViewId, camera == lensEye ? 1f : 0f);

    // 손 모델의 원을 화면으로 옮겨 돋보기 카메라를 그 방향으로 맞춘다. 원 가운데 광선을 돌려주고 rim을 채운다
    Ray LensView(Camera cam)
    {
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
        if (AudioManager.I != null) AudioManager.I.Play(id == ItemId.Memo ? "paper_rustle" : "pocket_rummage", null, 0.55f);
        RefreshHud();
    }

    // 소리 없이 내려놓음(챕터 전환)
    public void Clear()
    {
        Held = ItemId.None;
        Pointer = false;
        memoSide = false;
        memoScale = 1f;
        pointerDist = null;
        tremble = 0f;
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

    // 떨림이 들어간 포인터(뷰포트 좌표)
    public Vector2 Ptr01()
    {
        float t = Time.time, j = tremble * Bal.G("Hand_TrembleScale", 0.012f);
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
        if (kb.digit1Key.wasPressedThisFrame || kb.qKey.wasPressedThisFrame) Toggle(ItemId.Memo);
        else if (kb.digit2Key.wasPressedThisFrame) Toggle(ItemId.Lens);
        else if (kb.digit3Key.wasPressedThisFrame) Toggle(ItemId.Card);
    }

    void Update()
    {
        var player = PlayerController.I;
        if (player == null) return;
        Keys();

        float dt = Mathf.Min(Time.deltaTime, 0.05f), t = Time.time;
        var cam = player.Eye;
        tap = Damp(tap, 0f, 14f, dt);
        tMemo = Damp(tMemo, Held == ItemId.Memo ? 1f : 0f, 9f, dt);
        tLens = Damp(tLens, Held == ItemId.Lens ? 1f : 0f, 9f, dt);
        tCard = Damp(tCard, Held == ItemId.Card ? 1f : 0f, 9f, dt);
        tPoint = Damp(tPoint, Pointer && (Held == ItemId.None || Held == ItemId.Memo) ? 1f : 0f, 9f, dt);

        float sway = Mathf.Sin(t * 1.2f) * 0.003f;
        float jx = Mathf.Sin(t * 29f) * tremble * 0.0035f, jy = Mathf.Cos(t * 23f) * tremble * 0.0035f;

        // 메모: 키오스크에서는 화면을 가리지 않게 왼쪽으로 비킨다
        bool side = Pointer || memoSide;
        Paper(memo, tMemo, side, cam.aspect, jx, jy, sway);
        if (memo != null) memo.localScale = Vector3.one * (side ? 1f : memoScale);

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
        LensHit = Readable.Aim(aim, Held == ItemId.Lens, lensOn ? rim : null);
    }

    static void Paper(Transform paper, float k, bool side, float aspect, float jx, float jy, float sway)
    {
        if (!Show(paper, k)) return;
        float x = side ? -0.25f * aspect / 1.78f : -0.03f;
        paper.localPosition = new Vector3(x + jx, -0.34f + k * (side ? 0.24f : 0.32f) + sway + jy, side ? 0.4f : 0.34f);
        paper.localRotation = Rad(0.12f, side ? -0.22f : -0.05f, 0.03f);
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
