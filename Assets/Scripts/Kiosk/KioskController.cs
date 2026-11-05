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

    public void ResetTimer() => timer = Bal.F("KioskTimeoutSec", 40f);

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
    }

    void Start()
    {
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
            baseCamera.cullingMask = profile.kioskHideMeaning ? baseCamera.cullingMask & ~reveal : baseCamera.cullingMask | reveal;
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

    public void Finish()
    {
        if (!Active) return;
        Busy = true;
        StartCoroutine(FinishRun());
    }

    IEnumerator FinishRun()
    {
        yield return new WaitForSeconds(Bal.G("Kiosk_FinishDelay", 0.9f));
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
    void PackTouch(Vector2 uv)
    {
        var profile = GameState.I.Profile;
        ResetTimer();
        Sfx("kiosk_tap", 0.8f, UnityEngine.Random.Range(0.95f, 1.08f));
        if (profile.kioskTouchFail && UnityEngine.Random.value < Bal.Age("TouchFailChance", 0f, 0f, 0.08f, 0.12f))
        {
            HandRig.I.TapMiss();
            Mutter();
            return;
        }
        var b = packScreens.At(uv);
        if (b && profile.kioskTouchFail && UnityEngine.Random.value < Bal.Age("TouchMissChance", 0f, 0f, 0.2f, 0.3f))
        {
            var side = Neighbor(b);
            if (side) { b = side; HandRig.I.TapMiss(); }
        }
        if (!b)
        {
            Sfx("kiosk_error", 0.6f);
            Mutter();
            return;
        }
        b.Flash();
        Pack.OnPress(b.id);
    }

    KioskButton Neighbor(KioskButton b)
    {
        KioskButton best = null;
        float dist = float.MaxValue;
        foreach (var o in packScreens.Buttons())
        {
            if (o == b) continue;
            float d = (o.CenterWorld - b.CenterWorld).sqrMagnitude;
            if (d < dist) { dist = d; best = o; }
        }
        return best;
    }

    void Click()
    {
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
            else if (kb.eKey.wasPressedThisFrame && View == "staff") StaffCalled?.Invoke();
        }
        var mouse = Mouse.current;
        if (mouse != null && mouse.leftButton.wasPressedThisFrame && View == "kiosk") Click();
    }

    void Update()
    {
        if (!Active) return;
        Pack.OnTick(Time.deltaTime);
        if (toastUntil > 0f && Time.time > toastUntil) Toast(null);
        if (!ctrl) return;
        ApplyView();
        if (View == "kiosk" && view.EdgeTick(CursorDown, Time.deltaTime)) RefreshViews();
        if (Busy) return;
        HandleKeys();
        if (Busy || !ctrl) return;

        // 시간 제한
        if (Pack.Timed && GameState.I.Profile.kioskTimeout)
        {
            timer -= Time.deltaTime;
            int s = Mathf.Max(0, Mathf.CeilToInt(timer));
            if (s != lastSec) { lastSec = s; screens.SetTimer(s, true); }
            if (timer <= 0f) { ResetTimer(); Pack.OnTimeout(); }
        }
        else if (lastSec != -1) { lastSec = -1; screens.SetTimer(0, false); }

        // 프롬프트
        string label = View == "staff" ? "E 저기요" : "";
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

    public void Sfx(string key, float vol, float rate = 1f) => AudioManager.I.Play(key, null, vol, rate);

    public Coroutine Say(string who, string text, string vo = null, Vector3? pos = null)
    {
        if (nunchi && nunchi.Running) return nunchi.Say(who, text, vo, pos);
        if (pos != null && vo != null) { AudioManager.I.Vo(vo, pos); return Hud.I.Say(who, text); }
        return Hud.I.Say(who, text, vo);
    }

    public void Mutter() { if (nunchi && nunchi.Running) nunchi.Mutter(); }
}
