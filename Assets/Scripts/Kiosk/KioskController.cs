// 키오스크 본편. Enter로 시작해 Finish까지. 화면과 판정은 Pack이, 포인터, 시선, 터치 실패, 시간 초과는 여기서 맡는다.
// 배치: screens = KioskScreens (KioskCanvas 위, 알림과 타이머)
// 배치: screenQuad = 화면 쿼드 Transform (Unity Quad, 보이는 면이 손님 쪽, Collider 있음, 크기 0.42 x 0.7467)
// 배치: screenRenderer = 화면 쿼드 MeshRenderer (재질 Graybox/LensScreen)
// 배치: baseCamera = RT_Base를 찍는 카메라 (KioskReveal 제외)
// 배치: nunchi = 같은 프리팹의 NunchiSystem
// 배치: queue = Store 씬 QueueManager
// 배치: staffAnchor = 알바생 머리 높이 Transform (Anchor_Staff)
// 배치: touchMask = 본체와 화면 콜라이더가 있는 레이어
// 키오스크의 콜라이더(화면, 투입구, 본체)는 전부 이 오브젝트의 자식이어야 한다.
using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

// PlayerController(-50)가 카메라를 놓은 뒤, HandRig(0)가 포인터를 쓰기 전에 돈다
[DefaultExecutionOrder(-40)]
public class KioskController : MonoBehaviour
{
    [SerializeField] KioskScreens screens;
    [SerializeField] Transform screenQuad;
    [SerializeField] Renderer screenRenderer;
    [SerializeField] Camera baseCamera;
    [SerializeField] NunchiSystem nunchi;
    [SerializeField] QueueManager queue;
    [SerializeField] Transform staffAnchor;
    [SerializeField] LayerMask touchMask = ~0;

    /// <summary>시선이 바뀔 때. "kiosk" "staff" "back"</summary>
    public event Action<string> ViewChanged;
    /// <summary>A 시선에서 E. Director가 알바생 대사를 말한다.</summary>
    public event Action StaffCalled;

    public KioskPack Pack { get; private set; }
    public string View { get; private set; } = "kiosk";
    public PayPoint Pay => pay;
    public string Screen => packScreens && packScreens.Current ? packScreens.Current.id : "";
    public NunchiSystem Nunchi => nunchi;
    public bool Active { get; private set; }
    public bool Busy { get; private set; }

    /// <summary>화면 쿼드 아래 바닥점</summary>
    public Vector3 Floor { get { var p = screenQuad.position; p.y = transform.position.y; return p; } }
    /// <summary>화면에서 손님 쪽으로 나오는 방향</summary>
    public Vector3 Out { get { var f = -screenQuad.forward; f.y = 0f; return f.normalized; } }

    /// <summary>화면 전환. id는 Pack 안의 이름.</summary>
    public void Go(string screenId)
    {
        packScreens.Show(screenId);
        Toast(null);
        // 결제 창이면 투입구가 보이게 고개를 숙인다. 투입구는 기본 시선의 화면 아래 경계 밖이다
        view.SetDown(screenId == "pay");
        RefreshViews();
    }

    /// <summary>화면 위 짧은 알림. null이면 지움.</summary>
    public void Toast(string text)
    {
        screens.SetToast(text);
        toastUntil = text != null ? Time.time + Bal.G("Kiosk_ToastSec", 1.8f) : 0f;
    }

    /// <summary>고개를 투입구 쪽으로. 화면을 직접 그리는 Pack이 부른다.</summary>
    public void SetDown(bool on)
    {
        view.SetDown(on);
        RefreshViews();
    }

    public bool IsScreen(Collider col) => col.transform == screenQuad;

    public void ResetTimer() => timer = IdleSec + CountSec;

    // 입력 없이 IdleSec이 지나면 CountSec 동안 화면에 안내가 뜨고, 끝까지 없으면 처음 화면으로
    static float IdleSec => Bal.G("Kiosk_IdleSec", 20f);
    static float CountSec => Bal.G("Kiosk_IdleCountSec", 10f);

    KioskView view;
    KioskLens lens;
    KioskScreens packScreens;
    PayPoint pay;
    float toastUntil, timer, playerY;
    bool ctrl;
    int lastSec = -1;
    string promptShown = "";

    PlayerController Pc => PlayerController.I;
    Camera Eye => PlayerController.I.Eye;
    Vector3 QueuePos => queue ? queue.QueuePos : Floor + Out * 3f + Vector3.up * 1.5f;
    Vector3 StaffPos => staffAnchor ? staffAnchor.position : Floor + Vector3.up * 1.2f;

    void Awake()
    {
        Pack = GetComponentInChildren<KioskPack>(true);
        view = new KioskView(this);
        lens = new KioskLens(screenRenderer);
        if (!Pack) { enabled = false; return; }
        Pack.Ctl = this;
        packScreens = Pack.GetComponent<KioskScreens>();
        packScreens.Bind(screens.Canvas);
        Pack.transform.SetAsFirstSibling();   // 알림과 타이머가 위에 그려진다
        pay = GetComponentInChildren<PayPoint>(true);
        if (!nunchi) return;
        nunchi.CanBlow = () => !Busy && Pack.CanGiveUp;
        if (queue) nunchi.QueueCount = () => queue.Count;
        nunchi.ScreenId = () => Screen;
        if (pay) pay.CashRejected += _ => nunchi.Miss();
    }

    // 시연자 키로 빠져나가면 ReleaseControl이 안 불린다. 카메라 화각을 돌려놓는다
    void OnDestroy()
    {
        if (Active && Pc) view.Restore(Eye);
    }

    // 틈을 맞추려면 커서가 아래로 가기 쉽다. 판정만 아래로 넓힌다. 위와 좌우는 그대로이고, 틈끼리의 세로 간격보다 작아야 한다
    void WidenSlots()
    {
        float below = Bal.G("Kiosk_SlotHitBelow", 0.035f);
        foreach (var box in GetComponentsInChildren<BoxCollider>(true))
        {
            if (!box.name.StartsWith("Slot_")) continue;
            float local = below / Mathf.Max(box.transform.lossyScale.y, 0.0001f);
            box.size += Vector3.up * local;
            box.center -= Vector3.up * (local * 0.5f);
        }
    }

    void Start()
    {
        WidenSlots();
        screens.SetTimer(0, false);
        screens.SetToast(null);
        packScreens.Show(Pack.FirstScreen);
        lens.Apply(0);
    }

    // ---- 진입과 종료 ----

    /// <summary>키오스크 모드. Pack이 Finish를 부르고 조작이 돌아오면 끝난다.</summary>
    public IEnumerator Enter()
    {
        if (Active) yield break;
        Active = true;
        var profile = GameState.I.Profile;
        playerY = Pc.transform.position.y;
        if (baseCamera)
        {
            int reveal = LayerMask.GetMask("KioskReveal");
            baseCamera.cullingMask = profile.kioskHideMeaning || !Pack.ShowMeaning ? baseCamera.cullingMask & ~reveal : baseCamera.cullingMask | reveal;
        }
        Pc.Freeze(true);
        view.Save(Eye);
        Pc.SetMode(PlayerController.Mode.Cursor);
        Pc.SetCursor01(new Vector2(0.5f, CursorY(0.56f)));
        HandRig.I.SetEnabled(true);
        HandRig.I.SetPointer(true);
        view.Begin(Eye);
        View = "kiosk";
        if (nunchi) { nunchi.Begin(); nunchi.LookingBack = false; }
        RefreshViews();
        ctrl = true; Busy = false;
        ResetTimer();
        Go(Pack.FirstScreen);
        Pack.OnEnter();
        while (Active) yield return null;
    }

    void ReleaseControl()
    {
        ctrl = false;
        HandRig.I.SetPointer(false);
        HandRig.I.pointerDist = null;
        HandRig.I.Equip(ItemId.None);
        if (Wallet.I != null) Wallet.I.SetOpen(false);
        Hud.I.Views(null);
        Hud.I.Prompt(null);
        promptShown = "";
        screens.SetTimer(0, false);
        lastSec = -1;
        view.Restore(Eye);
        lens.Apply(0);
    }

    // delay를 안 주면 결제 끝난 뒤의 Kiosk_FinishDelay
    public void Finish(float delay = -1f)
    {
        if (!Active) return;
        Busy = true;
        StartCoroutine(FinishRun(delay >= 0f ? delay : Bal.G("Kiosk_FinishDelay", 0.9f)));
    }

    IEnumerator FinishRun(float delay)
    {
        yield return new WaitForSeconds(delay);
        Pc.BlendCamera();
        ReleaseControl();
        if (nunchi) nunchi.End();
        Vector3 p = Floor + Out * Bal.G("Kiosk_LeaveDist", 1.1f);
        p.y = playerY;
        Pc.Teleport(p, Mathf.Atan2(-Out.x, -Out.z) * Mathf.Rad2Deg);
        Pc.SetMode(PlayerController.Mode.Fps);
        Pc.Freeze(false);
        Active = false; Busy = false;
    }

    // ---- 시선 ----

    void SetView(string v)
    {
        if (View == v) return;
        View = v;
        ViewChanged?.Invoke(v);
        if (nunchi) nunchi.LookingBack = v == "back";
        HandRig.I.SetPointer(v == "kiosk");
        if (v != "kiosk" && HandRig.I.Held == ItemId.Card) HandRig.I.Equip(ItemId.None); // 고개를 돌리면 손을 내려 시야를 비운다
    }

    // 사과 문구와 음성은 노인 것이다. 4회차 인물만
    bool CanSorry => nunchi && GameState.I.Profile.limp;

    void RefreshViews() => Hud.I.Views($"A 알바생  S 뒤  D 키오스크  W {(view.Down ? "위" : "아래")}");

    // ---- 입력 ----

    /// <summary>화면 아래로 갈수록 커지는 값(0 위, 1 아래). PlayerController.Cursor01은 뷰포트 기준(0 아래, 1 위).</summary>
    static float CursorY(float down) => 1f - down;
    float CursorDown => CursorY(Pc.Cursor01.y);

    // 시선 카메라가 플레이어 몸보다 뒤에 있을 때가 있어 키오스크 밖 콜라이더는 건너뛴다
    bool Pick(out RaycastHit hit)
    {
        hit = default;
        bool found = false;
        foreach (var h in Physics.RaycastAll(HandRig.I.PointerRay(), Bal.G("Kiosk_TouchRange", 3f), touchMask, QueryTriggerInteraction.Collide))
        {
            if (h.collider.gameObject.layer == 2 || !h.collider.transform.IsChildOf(transform) || (found && h.distance >= hit.distance)) continue;   // 2 = Ignore Raycast, 몸을 막는 경계
            hit = h;
            found = true;
        }
        return found;
    }

    Vector2 ScreenUv(Vector3 world)
    {
        Vector3 l = screenQuad.InverseTransformPoint(world);
        return new Vector2(l.x + 0.5f, l.y + 0.5f);
    }

    // 터치 판정. 터치 안 먹음, 옆 버튼 눌림은 여기서 끝내고 Pack은 확정된 버튼만 받는다
    // 둘 다 버튼 가장자리를 눌렀을 때만 일어난다. 가운데를 누르면 항상 그 버튼이 눌린다
    void PackTouch(Vector2 uv)
    {
        var profile = GameState.I.Profile;
        var b = packScreens.At(uv);
        Vector3 at = packScreens.World(uv);
        bool edge = b && profile.kioskTouchFail && b.EdgeRatio(at) > 1f - Bal.G("Kiosk_TouchEdgeFrac", 0.25f);
        if (edge && UnityEngine.Random.value < Bal.Age("TouchFailChance", 0f, 0f, 0.07f, 0.07f))
        {
            Sfx("kiosk_tap", 0.3f, 0.6f);   // 낮고 둔한 소리로 빗나갔음을 알린다
            HandRig.I.TapMiss();
            Mutter();
            return;
        }
        Sfx("kiosk_tap", 0.8f, UnityEngine.Random.Range(0.95f, 1.08f));
        if (edge && UnityEngine.Random.value < Bal.Age("TouchMissChance", 0f, 0f, 0.1f, 0.15f))
        {
            var side = Neighbor(b, at);
            if (side) { b = side; HandRig.I.TapMiss(); }
        }
        if (!b)
        {
            Sfx("kiosk_error", 0.6f);
            Mutter();
            return;
        }
        b.Flash();
        GameState.I.Stats.touches++;
        Pack.OnPress(b.id);
    }

    // 누른 자리에 가장 가까운 옆 버튼. 화면 전체를 덮는 뒷판 버튼은 옆 버튼이 아니다
    KioskButton Neighbor(KioskButton b, Vector3 at)
    {
        KioskButton best = null;
        float dist = float.MaxValue;
        foreach (var o in packScreens.Buttons())
        {
            if (o == b || o.Contains(at)) continue;
            float d = (o.CenterWorld - at).sqrMagnitude;
            if (d < dist) { dist = d; best = o; }
        }
        return best;
    }

    void Click()
    {
        ResetTimer();
        if ((RoundUi.I != null && RoundUi.I.Blocks) || (Wallet.I != null && Wallet.I.Over)) return;
        HandRig.I.Tap();
        if (Pick(out var hit))
        {
            if (Pack.Hit(hit.collider)) return;
            if (hit.collider.transform == screenQuad) { PackTouch(ScreenUv(hit.point)); return; }
            var point = hit.collider.GetComponentInParent<PayPoint>();
            if (point) { point.Click(); return; }
        }
        Sfx("kiosk_error", 0.5f);
    }

    void HandleKeys()
    {
        var kb = Keyboard.current;
        if (kb != null)
        {
            if (kb.aKey.wasPressedThisFrame) SetView("staff");
            else if (kb.sKey.wasPressedThisFrame) SetView("back");
            else if (kb.dKey.wasPressedThisFrame) SetView("kiosk");
            else if (kb.wKey.wasPressedThisFrame) { if (View == "kiosk") { view.ToggleDown(); RefreshViews(); } }
            else if (kb.eKey.wasPressedThisFrame)
            {
                if (View == "staff") StaffCalled?.Invoke();
                else if (View == "back" && CanSorry) nunchi.Sorry();
            }
        }
        var mouse = Mouse.current;
        if (mouse != null && mouse.leftButton.wasPressedThisFrame && View == "kiosk") Click();
    }

    void Update()
    {
        if (!Active || PauseMenu.On) return;
        Pack.OnTick(Time.deltaTime);
        if (toastUntil > 0f && Time.time > toastUntil) Toast(null);
        if (!ctrl) return;
        ApplyView();
        if (View == "kiosk" && view.EdgeTick(CursorDown, Time.deltaTime)) RefreshViews();
        if (Busy) return;
        HandleKeys();
        if (Busy || !ctrl) return;

        // 무입력
        if (Pack.Timed)
        {
            timer -= Time.deltaTime;
            if (timer <= CountSec)
            {
                int s = Mathf.Max(0, Mathf.CeilToInt(timer));
                if (s != lastSec)
                {
                    if (lastSec == -1) Sfx("kiosk_popup", 0.7f);
                    lastSec = s;
                    screens.SetTimer(s, true);
                }
            }
            else if (lastSec != -1) { lastSec = -1; screens.SetTimer(0, false); }
            if (timer <= 0f) { ResetTimer(); lastSec = -1; screens.SetTimer(0, false); GameState.I.Stats.resets++; Pack.OnTimeout(); }
        }
        else if (lastSec != -1) { lastSec = -1; screens.SetTimer(0, false); }

        // 프롬프트
        string label = View == "staff" ? "E 저기요" : View == "back" && CanSorry && nunchi.Running && nunchi.Cooldown <= 0f ? "E 죄송합니다" : "";
        if (label != promptShown) { promptShown = label; Hud.I.Prompt(label == "" ? null : label); }
    }

    void ApplyView()
    {
        var c = Pc.Cursor01;
        view.Apply(Eye, Pc, View, new Vector2(c.x - 0.5f, CursorDown - 0.5f), View == "staff" ? StaffPos : QueuePos, Time.deltaTime);

        // 손가락 거리
        if (View == "kiosk")
        {
            bool picked = Pick(out var hit);
            HandRig.I.pointerDist = picked ? hit.distance : 0.6f;
        }
        lens.Apply(nunchi ? nunchi.BlurStep : 0);
    }

    // ---- 흐름이 부르는 것 ----

    public void Sfx(string key, float vol, float rate = 1f)
    {
        AudioManager.I.Play(key, null, vol, rate, true);   // 내 손이 낸 소리는 먹먹함을 받지 않는다
        if (nunchi && (key == "kiosk_error" || key == "card_slide_wrong")) nunchi.Miss();
    }

    public Coroutine Say(string who, string text, string vo = null, Vector3? pos = null)
    {
        if (nunchi && nunchi.Running) return nunchi.Say(who, text, vo, pos);
        if (pos != null && vo != null) { AudioManager.I.Vo(vo, pos); return Hud.I.Say(who, text); }
        return Hud.I.Say(who, text, vo);
    }

    public void Mutter()
    {
        if (!nunchi || !nunchi.Running) return;
        nunchi.Miss();
        nunchi.Mutter();
    }

    // ---- 다음 손님 ----

    /// <summary>플레이어 다음 손님이 실제 화면을 넘기며 쓴다. 플레이어는 이때 조작하지 못한다.</summary>
    public IEnumerator CustomerUse()
    {
        Vector3 at = screenQuad.position;
        float step = Bal.G("Kiosk_DemoStepSec", 0.85f);
        foreach (string id in Pack.CustomerScreens)
        {
            AudioManager.I.Play("kiosk_tap", at, 0.6f);
            Pack.ShowCustomer(id);
            yield return new WaitForSeconds(step);
        }
        yield return new WaitForSeconds(Bal.G("Kiosk_CustomerUseSec", 4f));
        AudioManager.I.Play("card_insert", at, 0.8f);
        yield return new WaitForSeconds(step);
        AudioManager.I.Play("kiosk_ok", at, 0.8f);
    }
}
