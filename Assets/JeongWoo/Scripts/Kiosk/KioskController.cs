// 키오스크 본편. Enter로 시작해 영수증을 뜯으면 끝난다. 원본 index.js.
// 배치: screens = KioskScreens (KioskCanvas 위)
// 배치: screenQuad = 화면 쿼드 Transform (Unity Quad, 보이는 면이 손님 쪽, Collider 있음, 크기 0.42 x 0.7467)
// 배치: screenRenderer = 화면 쿼드 MeshRenderer (재질 Graybox/LensScreen)
// 배치: baseCamera = RT_Base를 찍는 카메라 (KioskReveal 제외)
// 배치: cover = IC 틈을 가린 PosterFlap
// 배치: slots = CardSlot 3개 (ic, receipt, barcode)
// 배치: card = KioskCard
// 배치: receipt = KioskReceipt
// 배치: nunchi = 같은 프리팹의 NunchiSystem
// 배치: queue = Store 씬 QueueManager
// 배치: staffAnchor = 알바생 머리 높이 Transform (Anchor_Staff)
// 배치: touchMask = 본체와 화면 콜라이더가 있는 레이어
// 키오스크의 콜라이더(화면, 틈, 포스터, 스팟, 본체)는 전부 이 오브젝트의 자식이어야 한다.
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
    [SerializeField] PosterFlap cover;
    [SerializeField] CardSlot[] slots = new CardSlot[0];
    [SerializeField] KioskCard card;
    [SerializeField] KioskReceipt receipt;
    [SerializeField] NunchiSystem nunchi;
    [SerializeField] QueueManager queue;
    [SerializeField] Transform staffAnchor;
    [SerializeField] LayerMask touchMask = ~0;

    /// <summary>눈치 폭발. 구독자(QueueManager)가 연출을 돌리고 Blowing이 꺼지면 처음 화면으로 복귀한다.</summary>
    public event Action Blowup;

    public KioskFlow Flow { get; private set; }
    public KioskScreens Screens => screens;
    public NunchiSystem Nunchi => nunchi;
    public bool Active { get; private set; }
    public bool Busy { get; private set; }
    public bool CoverOpened => cover && cover.Opened;

    public string Speaker => GameState.I.Profile.speakerKey;
    /// <summary>화면 쿼드 아래 바닥점</summary>
    public Vector3 Floor { get { var p = screenQuad.position; p.y = transform.position.y; return p; } }
    /// <summary>화면에서 손님 쪽으로 나오는 방향</summary>
    public Vector3 Out { get { var f = -screenQuad.forward; f.y = 0f; return f.normalized; } }

    KioskState K => Flow.K;
    KioskView view;
    KioskLens lens;
    bool ctrl, staffBusy;
    int staffTalk, lastSec = -1;
    float slideT, playerY;
    string promptShown = "";

    PlayerController Pc => PlayerController.I;
    Camera Eye => PlayerController.I.Eye;
    Vector3 QueuePos => queue ? queue.QueuePos : Floor + Out * 3f + Vector3.up * 1.5f;
    Vector3 StaffPos => staffAnchor ? staffAnchor.position : Floor + Vector3.up * 1.2f;

    void Awake()
    {
        Flow = new KioskFlow(this, screens);
        view = new KioskView(this);
        lens = new KioskLens(screenRenderer);
        if (!nunchi) return;
        nunchi.CanBlow = () => !Busy && Flow.Safe;
        nunchi.BlowupRequested += OnBlowup;
        if (queue) nunchi.QueueCount = () => queue.Count;
    }

    void OnDestroy()
    {
        if (nunchi) nunchi.BlowupRequested -= OnBlowup;
        if (Active && Pc) view.Restore(Eye);   // 시연자 키로 빠져나가면 ReleaseControl 이 안 불린다. 카메라는 씬을 건너간다
    }

    void Start()
    {
        K.timer = Bal.G("Kiosk_Timer", 90f);
        Flow.Redraw();
        screens.SetTimer(0, false);
        lens.Apply(0);
    }

    // ---- 진입과 종료 ----

    /// <summary>키오스크 모드. 영수증을 뜯고 조작이 돌아오면 끝난다.</summary>
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
        Flow.ResetAll();
        Pc.SetMode(PlayerController.Mode.Cursor);
        Pc.SetCursor01(new Vector2(0.5f, CursorY(0.56f)));
        HandRig.I.SetEnabled(true);
        HandRig.I.SetPointer(true);
        HandRig.I.memoSide = true;
        if (profile.Has(ItemId.Memo)) HandRig.I.Equip(ItemId.Memo);
        view.Begin(Eye);
        K.view = "kiosk"; K.lookingBack = false;
        if (nunchi) { nunchi.Begin(); nunchi.LookingBack = false; }
        RefreshViews();
        ctrl = true; Busy = false;
        Say("kiosk", "화면을 터치하여 주문을 시작해 주세요.", "k_touch");
        while (Active) yield return null;
    }

    /// <summary>처음 화면으로. 에디터가 컴포넌트를 붙일 때도 불리므로 준비 전이면 무시한다.</summary>
    public void Reset()
    {
        if (Flow != null) Flow.ResetAll();
    }

    void ResumeControl()
    {
        Pc.SetMode(PlayerController.Mode.Cursor);
        HandRig.I.SetEnabled(true);
        HandRig.I.SetPointer(true);
        HandRig.I.memoSide = true;
        view.Save(Eye);
        view.Begin(Eye);
        K.view = "kiosk"; K.lookingBack = false;
        if (nunchi) nunchi.LookingBack = false;
        RefreshViews();
        ctrl = true;
        view.Apply(Eye, Pc, "kiosk", Vector2.zero, Vector3.zero, 0f, true);
    }

    void ReleaseControl()
    {
        ctrl = false;
        HandRig.I.SetPointer(false);
        HandRig.I.memoSide = false;
        HandRig.I.pointerDist = null;
        HandRig.I.Equip(ItemId.None);
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
        PlacePlayer(Bal.G("Kiosk_LeaveDist", 1.1f));
        Pc.SetMode(PlayerController.Mode.Fps);
        Pc.Freeze(false);
        Active = false; Busy = false;
    }

    void PlacePlayer(float dist)
    {
        Vector3 p = Floor + Out * dist;
        p.y = playerY;
        Pc.Teleport(p, Mathf.Atan2(-Out.x, -Out.z) * Mathf.Rad2Deg);
    }

    // ---- 눈치 폭발 ----

    void OnBlowup()
    {
        if (Busy || !Flow.Safe) return;
        Busy = true;
        StartCoroutine(BlowupRun());
    }

    IEnumerator BlowupRun()
    {
        var st = GameState.I.Stats;
        st.blowups++; st.resets++;
        K.run++;
        nunchi.HoldForBlowup();
        PlacePlayer(Bal.G("Kiosk_Dist", 0.76f));
        ReleaseControl();
        Pc.SetMode(PlayerController.Mode.Hidden);
        yield return StartCoroutine(Pc.LookAt(QueuePos, Bal.G("Kiosk_BlowupTurnSec", 0.7f)));
        yield return Say(Speaker, "죄송합니다... 먼저 하세요.", Speaker + "_sorry3");
        yield return Say("yM", "비켜보세요, 제가 먼저 할게요.", "y_takeover", QueuePos);
        StartCoroutine(Flow.Demo());
        Blowup?.Invoke();
        float wait = Bal.G(queue ? "Kiosk_BlowupMaxSec" : "Kiosk_BlowupAloneSec", queue ? 45f : 3f), t = 0f;
        yield return null;
        while (t < wait && (!queue || queue.Blowing)) { t += Time.deltaTime; yield return null; }
        yield return Hud.I.Fade(1f, 0.5f);
        Flow.ResetAll();
        nunchi.ResumeAfterBlowup();
        PlacePlayer(Bal.G("Kiosk_Dist", 0.76f));
        ResumeControl();
        Pc.Freeze(true);
        Busy = false;
        K.timer = Bal.G("Kiosk_Timer", 90f);
        yield return Hud.I.Fade(0f, 0.5f);
    }

    // ---- 시선 ----

    void SetView(string v)
    {
        if (K.view == v) return;
        K.view = v; K.lookingBack = v == "back";
        if (nunchi) nunchi.LookingBack = K.lookingBack;
        HandRig.I.SetPointer(v == "kiosk");
        var held = HandRig.I.Held;
        if (v != "kiosk" && (held == ItemId.Card || held == ItemId.Memo)) HandRig.I.Equip(ItemId.None); // 고개를 돌리면 손을 내려 시야를 비운다
    }

    void RefreshViews() => Hud.I.Views($"A 알바생  S 뒤  D 키오스크  W {(view.Down ? "위" : "아래")}");

    IEnumerator CallStaff()
    {
        staffBusy = true; staffTalk++;
        int n = staffTalk % 3;
        yield return n == 2 ? Say(Speaker, "저기요...", Speaker + "_staff2") : Say(Speaker, "저기요, 학생. 이거 좀...", Speaker + "_staff1");
        if (n == 0) yield return Say("staff", "거기 화면 누르시면 돼요.", "staff_3", StaffPos);
        else yield return Say("staff", "네?", "staff_2", StaffPos);
        staffBusy = false;
    }

    // ---- 입력 ----

    /// <summary>화면 아래로 갈수록 커지는 값(0 위, 1 아래). PlayerController.Cursor01은 뷰포트 기준(0 아래, 1 위).</summary>
    static float CursorY(float down) => 1f - down;
    float CursorDown => CursorY(Pc.Cursor01.y);

    bool Pick(out RaycastHit hit)
    {
        return Physics.Raycast(HandRig.I.PointerRay(), out hit, Bal.G("Kiosk_TouchRange", 3f), touchMask, QueryTriggerInteraction.Collide)
            && hit.collider.transform.IsChildOf(transform);
    }

    Vector2 ScreenUv(Vector3 world)
    {
        Vector3 l = screenQuad.InverseTransformPoint(world);
        return new Vector2(l.x + 0.5f, l.y + 0.5f);
    }

    void Click()
    {
        HandRig.I.Tap();
        if (!Pick(out var hit)) return;
        var col = hit.collider;
        if (col.transform == screenQuad) { Flow.Touch(ScreenUv(hit.point)); return; }
        var slot = col.GetComponentInParent<CardSlot>();
        if (slot) { Flow.Slot(slot.id); return; }
        var spot = col.GetComponentInParent<KioskSpot>();
        if (spot) { Flow.Spot(spot.id); return; }
        Flow.Spot(col.GetComponentInParent<PosterFlap>() ? "cover" : "body");
    }

    void HandleKeys()
    {
        var kb = Keyboard.current;
        if (kb != null)
        {
            if (kb.aKey.wasPressedThisFrame) SetView("staff");
            else if (kb.sKey.wasPressedThisFrame) SetView("back");
            else if (kb.dKey.wasPressedThisFrame) SetView("kiosk");
            else if (kb.wKey.wasPressedThisFrame) { if (K.view == "kiosk") { view.ToggleDown(); RefreshViews(); } }
            else if (kb.eKey.wasPressedThisFrame)
            {
                if (K.view == "staff") { if (!staffBusy) StartCoroutine(CallStaff()); }
                else if (K.view == "back" && nunchi) nunchi.Sorry();
            }
        }
        var mouse = Mouse.current;
        if (mouse != null && mouse.leftButton.wasPressedThisFrame && K.view == "kiosk") Click();
    }

    void Update()
    {
        if (!Active) return;
        Flow.Tick();
        // 대기 화면 광고 넘김
        if (K.screen == "idle")
        {
            slideT += Time.deltaTime;
            if (slideT > Bal.G("Kiosk_SlideSec", 3.6f)) { slideT = 0f; K.slide++; Flow.Redraw(); }
        }
        if (!ctrl) return;
        ApplyView();
        if (K.view == "kiosk" && view.EdgeTick(CursorDown, Time.deltaTime)) RefreshViews();
        if (Busy) return;
        HandleKeys();
        if (Busy || !ctrl) return;

        // 시간 제한
        if (Flow.Timed)
        {
            K.timer -= Time.deltaTime;
            int s = Mathf.Max(0, Mathf.CeilToInt(K.timer));
            if (s != lastSec) { lastSec = s; screens.SetTimer(s, true); }
            if (K.timer <= 0f) Flow.TimedOut();
        }
        else if (lastSec != -1) { lastSec = -1; screens.SetTimer(0, false); }

        // 프롬프트
        string label = K.view == "staff" ? (staffBusy ? "" : "E 저기요")
            : K.view == "back" ? (nunchi && nunchi.Running && nunchi.Cooldown <= 0f ? "E 죄송합니다" : "") : "";
        if (label != promptShown) { promptShown = label; Hud.I.Prompt(label == "" ? null : label); }
    }

    void ApplyView()
    {
        var c = Pc.Cursor01;
        view.Apply(Eye, Pc, K.view, new Vector2(c.x - 0.5f, CursorDown - 0.5f), K.view == "staff" ? StaffPos : QueuePos, Time.deltaTime);

        // 손가락 거리
        if (K.view == "kiosk")
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

    public void AddNunchi(float n) { if (nunchi) nunchi.Add(n); }

    public void Mutter() { if (nunchi && nunchi.Running) nunchi.Mutter(); }

    public void OpenCover() { if (cover) cover.Open(); }

    public void HardwareReset()
    {
        if (cover) cover.Close();
        if (card) card.Hide();
        if (receipt) receipt.Clear();
    }

    public void CardAt(string slotId, KioskCard.Move move)
    {
        if (!card) return;
        foreach (var s in slots) if (s.id == slotId) { card.At(s.transform, Out, move); return; }
    }

    public void PrintReceipt(string lines, string total, int number, float sec) { if (receipt) receipt.Print(lines, total, number, sec); }
    public void ReceiptReady() { if (receipt) receipt.CanTear(true); }
    public void TearReceipt() { if (receipt) receipt.Tear(); }
}
