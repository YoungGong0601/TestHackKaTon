// 회차 시험의 공통 부분. 플레이어 입력(E, R, 숫자 키, 마우스 클릭, 포인터)을 넣어 게임이 쓰는 경로로만 진행한다.
// 키오스크 버튼과 결제 지점은 포인터를 옮겨 실제 레이캐스트로 누른다.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.RegularExpressions;
using NUnit.Framework;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

public abstract class RoundFixture
{
    protected const int Limit = 600000;
    protected const float Fast = 3f;

    // 화면에 나온 글자와 손목시계 바늘을 모은다
    protected class Recorder : MonoBehaviour
    {
        public readonly HashSet<string> Lines = new();
        public readonly List<int> Hours = new();
        int tick;
        bool watchWas;

        static string Clean(string s) => Regex.Replace(Regex.Replace(s, "<[^>]+>", ""), @"\s+", "");

        void LateUpdate()
        {
            if (Hud.I != null)
                foreach (var t in Hud.I.GetComponentsInChildren<TMP_Text>(false))
                    if (!string.IsNullOrEmpty(t.text)) Lines.Add(Clean(t.text));
            if (++tick % 20 == 0)
                foreach (var t in FindObjectsByType<TMP_Text>(FindObjectsSortMode.None))
                    if (!string.IsNullOrEmpty(t.text)) Lines.Add(Clean(t.text));
            if (HandRig.I == null) return;
            bool up = Field<bool>(HandRig.I, "watchUp");
            if (up && !watchWas)
            {
                var hand = Field<Transform>(HandRig.I, "watchHour");
                Hours.Add(hand != null ? Mathf.RoundToInt(Mathf.Repeat(-hand.localEulerAngles.z, 360f) / 30f) : -1);
            }
            watchWas = up;
        }

        public bool Saw(string line)
        {
            string want = Clean(line);
            return Lines.Any(l => l.Contains(want));
        }
    }

    protected Recorder rec;

    float savedVolume;
    InputSettings.BackgroundBehavior savedBackground;
    InputSettings.EditorInputBehaviorInPlayMode savedEditorInput;
    readonly List<string> overrides = new();

    protected static PlayerController Pc => PlayerController.I;
    protected static GameState Game => GameState.I;
    protected static string Scene => SceneManager.GetActiveScene().name;

    // ---- 준비와 정리 ----

    [UnitySetUp]
    public IEnumerator SetUp()
    {
        savedVolume = AudioListener.volume;
        AudioListener.volume = 0f;
        Time.timeScale = 1f;
        Hud.SkipTitle = true;
        savedBackground = InputSystem.settings.backgroundBehavior;
        savedEditorInput = InputSystem.settings.editorInputBehaviorInPlayMode;
        InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
        InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;

        yield return Until(() => ConfigTableLoader.IsLoaded, 20f, "설정 로드");
        yield return SceneManager.LoadSceneAsync("R1_Stop", LoadSceneMode.Single);
        yield return null;
        yield return null;
        Assert.IsNotNull(GameState.I, "GameState 없음");
        var host = new GameObject("TestRecorder");
        Object.DontDestroyOnLoad(host);
        rec = host.AddComponent<Recorder>();
    }

    [UnityTearDown]
    public IEnumerator TearDown()
    {
        Time.timeScale = 1f;
        Hud.SkipTitle = false;
        AudioListener.volume = savedVolume;
        InputSystem.settings.backgroundBehavior = savedBackground;
        InputSystem.settings.editorInputBehaviorInPlayMode = savedEditorInput;
        ClearOverrides();
        if (rec != null) Object.Destroy(rec.gameObject);

        var blank = SceneManager.CreateScene("TestBlank" + Time.frameCount);
        SceneManager.SetActiveScene(blank);
        for (int i = SceneManager.sceneCount - 1; i >= 0; i--)
        {
            var scene = SceneManager.GetSceneAt(i);
            if (scene != blank) yield return SceneManager.UnloadSceneAsync(scene);
        }
        if (GameState.I != null) Object.Destroy(GameState.I.transform.root.gameObject);
        yield return null;
    }

    // ---- 값 고치기 ----

    protected static T Field<T>(object o, string name)
    {
        for (var t = o.GetType(); t != null; t = t.BaseType)
        {
            var f = t.GetField(name, BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic);
            if (f != null) return (T)f.GetValue(o);
        }
        throw new MissingFieldException(o.GetType().Name, name);
    }

    static Dictionary<string, object> Configs =>
        (Dictionary<string, object>)typeof(ConfigTableLoader).GetField("configs", BindingFlags.Static | BindingFlags.NonPublic).GetValue(null);

    /// <summary>시험 동안만 시트 값을 넣는다. 정리 때 지운다.</summary>
    protected void Override(string key, float value)
    {
        Configs[key] = value;
        overrides.Add(key);
    }

    void ClearOverrides()
    {
        foreach (string k in overrides) Configs.Remove(k);
        overrides.Clear();
    }

    /// <summary>터치 실패, 옆 버튼, 손떨림을 끈다. 눌러야 할 곳이 정해진 경로 시험용. 확률 자체는 TouchNoise 시험이 본다.</summary>
    protected void SteadyHands()
    {
        foreach (string p in new[] { "Age60_", "Age80_" })
        {
            Override(p + "TouchFailChance", 0f);
            Override(p + "TouchMissChance", 0f);
        }
        Override("Hand_TrembleScale", 0f);
    }

    // ---- 기다리기 ----

    protected static IEnumerator Until(Func<bool> cond, float realSec, string what)
    {
        float end = Time.realtimeSinceStartup + realSec;
        while (!cond())
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail($"시간 초과: {what} (씬 {Scene}, 모드 {(Pc ? Pc.CurrentMode.ToString() : "-")}, 멈춤 {(Pc ? Pc.Frozen : false)})");
            yield return null;
        }
    }

    protected static IEnumerator Real(float sec)
    {
        float end = Time.realtimeSinceStartup + sec;
        while (Time.realtimeSinceStartup < end) yield return null;
    }

    /// <summary>챕터 이동. 시연자 키가 쓰는 경로.</summary>
    protected IEnumerator Chapter(int index)
    {
        if (Game.chapterIndex != index)
        {
            Game.JumpChapter(index);
            yield return InChapter(index);
        }
        yield return Real(0.2f);
    }

    protected IEnumerator InChapter(int index, float sec = 40f)
    {
        string name = Game.flow.chapters[index].sceneName;
        yield return Until(() => Scene == name && Game.chapterIndex == index, sec, "챕터 " + name);
        Assert.AreEqual(Game.flow.chapters[index].profile, Game.Profile, "프로필 " + name);
    }

    protected static IEnumerator Free(float sec = 40f)
    {
        yield return Until(() => !Pc.Frozen && Pc.CurrentMode == PlayerController.Mode.Fps, sec, "조작 복귀");
    }

    // ---- 키보드와 마우스 ----

    protected static IEnumerator Tap(params Key[] keys)
    {
        var kb = Keyboard.current ?? InputSystem.AddDevice<Keyboard>();
        InputSystem.QueueStateEvent(kb, new KeyboardState(keys));
        yield return null;
        yield return null;
        InputSystem.QueueStateEvent(kb, new KeyboardState());
        yield return null;
    }

    protected static IEnumerator Chord(Key key) => Tap(Key.LeftCtrl, Key.LeftShift, key);

    static Mouse MouseDevice => Mouse.current ?? InputSystem.AddDevice<Mouse>();

    protected static IEnumerator Click(Vector2 screen = default)
    {
        InputSystem.QueueStateEvent(MouseDevice, new MouseState { position = screen }.WithButton(MouseButton.Left));
        yield return null;
        yield return null;
        InputSystem.QueueStateEvent(MouseDevice, new MouseState { position = screen });
        yield return null;
    }

    // ---- 상호작용 ----

    protected static Interactable Usable(string label) =>
        Object.FindObjectsByType<Interactable>(FindObjectsInactive.Exclude, FindObjectsSortMode.None).FirstOrDefault(i => i.active && i.label == label);

    protected static IEnumerator Use(string label, float sec = 60f)
    {
        Interactable it = null;
        yield return Until(() => (it = Usable(label)) != null && !Pc.Frozen, sec, "상호작용 " + label);
        yield return Use(it);
    }

    /// <summary>플레이어를 물체 앞으로 옮기고 바라본 뒤 물체의 키를 누른다. onUse를 직접 부르지 않는다.</summary>
    protected static IEnumerator Use(Interactable it)
    {
        yield return Until(() => !Pc.Frozen && Pc.CurrentMode == PlayerController.Mode.Fps, 30f, "조작 복귀 " + it.label);
        Vector3 from = Pc.transform.position - it.transform.position;
        from.y = 0f;
        float near = Mathf.Min(1f, it.radius * 0.5f);
        if (from.magnitude > near)
        {
            Vector3 at = it.transform.position + from.normalized * near;
            at.y = Pc.transform.position.y;
            Pc.Teleport(at, Pc.Yaw);
        }
        yield return Pc.LookAt(it.transform.position, 0.02f);
        // 프롬프트에 이 물체가 떠야 사람도 누를 수 있다
        var prompt = Field<TMP_Text>(Hud.I, "prompt");
        string label = it.label;
        float end = Time.realtimeSinceStartup + 3f;
        while (!prompt.text.Contains(label))
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail($"프롬프트 {label} 안 뜸, 지금 '{prompt.text}' (씬 {Scene}, 멈춤 {Pc.Frozen}, 모드 {Pc.CurrentMode})");
            yield return null;
        }
        Debug.Log($"사용 {label} 프롬프트 '{prompt.text}' 멈춤 {Pc.Frozen} 모드 {Pc.CurrentMode} 키보드 {Keyboard.current?.deviceId} 시각 {Time.time:F2}");
        yield return Tap((Key)Enum.Parse(typeof(Key), it.key, true));
        Debug.Log($"사용 뒤 자막 '{Field<TMP_Text>(Hud.I, "subs").text}' 프롬프트 '{prompt.text}' 시각 {Time.time:F2}");
    }

    // ---- 계단 ----

    /// <summary>마싱 표시가 뜨면 끝날 때까지 E를 눌러 횟수를 돌려준다.</summary>
    protected static IEnumerator Mash(Action<int> count)
    {
        var group = Field<CanvasGroup>(RoundUi.I, "mashGroup");
        yield return Until(() => group.alpha > 0.5f, 40f, "마싱 시작");
        int n = 0;
        float end = Time.realtimeSinceStartup + 60f;
        while (group.alpha > 0.5f)
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail("마싱 끝나지 않음 " + n);
            yield return Tap(Key.E);
            n++;
        }
        count(n);
    }

    // ---- 키오스크 ----

    protected static KioskController Kiosk => Object.FindAnyObjectByType<KioskController>();

    protected static KioskScreens PackScreens => Kiosk.Pack.GetComponent<KioskScreens>();

    protected IEnumerator EnterKiosk()
    {
        // 씬마다 라벨이 달라 Director가 쥔 물체를 쓴다
        Interactable order = null;
        foreach (var m in Object.FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
        {
            var f = m.GetType().GetField("orderKiosk", BindingFlags.Instance | BindingFlags.NonPublic);
            if (f != null) order = (Interactable)f.GetValue(m);
        }
        Assert.IsNotNull(order, "orderKiosk 없음 " + Scene);
        yield return Until(() => order.active && !Pc.Frozen, 90f, "주문 준비 " + order.label);
        yield return Use(order);
        var k = Kiosk;
        yield return Until(() => k.Active && Pc.CurrentMode == PlayerController.Mode.Cursor, 30f, "키오스크 진입");
        yield return Real(0.5f);
    }

    /// <summary>세계 좌표에 포인터를 놓는다. 화면 밖이면 W로 고개를 숙인다.</summary>
    protected static IEnumerator Point(Func<Vector3> world)
    {
        Vector3 v = Pc.Eye.WorldToViewportPoint(world());
        for (int tries = 0; tries < 2 && (v.y < 0.06f || v.y > 0.94f); tries++)
        {
            yield return Tap(Key.W);
            yield return Real(0.4f);
            v = Pc.Eye.WorldToViewportPoint(world());
        }
        // 포인터가 움직이면 시선도 따라 움직이므로 맞을 때까지 다시 놓는다. 사람이 눈으로 맞추는 것과 같다
        float end = Time.realtimeSinceStartup + 4f;
        int good = 0;
        while (good < 4 && Time.realtimeSinceStartup < end)
        {
            v = Pc.Eye.WorldToViewportPoint(world());
            var want = new Vector2(v.x, v.y);
            good = (want - Pc.Cursor01).sqrMagnitude < 2e-6f ? good + 1 : 0;
            Pc.SetCursor01(want);
            yield return null;
        }
    }

    protected static Vector3 ButtonWorld(KioskButton b)
    {
        var quad = Field<Transform>(Kiosk, "screenQuad");
        Vector2 uv = PackScreens.Uv(b);
        return quad.TransformPoint(new Vector3(uv.x - 0.5f, uv.y - 0.5f, 0f));
    }

    /// <summary>화면 버튼을 포인터와 좌클릭으로 누른다.</summary>
    protected static IEnumerator Touch(string id, float sec = 10f)
    {
        KioskButton b = null;
        yield return Until(() => (b = PackScreens.Find(id)) != null, sec, $"버튼 {id}, 화면 {Kiosk.Screen}");
        yield return Until(() => !Kiosk.Busy && !RoundUi.I.ChoiceOpen, 10f, "키오스크 대기 " + id);
        yield return Point(() => ButtonWorld(b));
        var names = Physics.RaycastAll(HandRig.I.PointerRay(), 3f, ~0, QueryTriggerInteraction.Collide).OrderBy(h => h.distance).Select(h => h.collider.name);
        Debug.Log($"터치 {id} 화면 {Kiosk.Screen} 포인터 {Pc.Cursor01} uv {PackScreens.Uv(b)} 버튼들 [{string.Join(",", PackScreens.Buttons().Select(x => x.id))}] 맞은 순서 {string.Join(",", names)}");
        yield return Click();
        yield return Real(0.05f);
    }

    protected static IEnumerator TouchAll(params string[] ids)
    {
        foreach (string id in ids) yield return Touch(id);
    }

    protected static IEnumerator Screen(string id, float sec = 6f)
    {
        yield return Until(() => Kiosk.Screen == id, sec, $"화면 {id}, 지금 {Kiosk.Screen}");
    }

    static Vector3 PayWorld()
    {
        var col = Kiosk.Pay.GetComponentInChildren<Collider>();
        return col != null ? col.bounds.center : Kiosk.Pay.transform.position;
    }

    /// <summary>결제 지점을 포인터로 클릭한다.</summary>
    protected static IEnumerator ClickPay()
    {
        yield return Point(PayWorld);
        var hits = Physics.RaycastAll(HandRig.I.PointerRay(), 3f, ~0, QueryTriggerInteraction.Collide).OrderBy(h => h.distance).Select(h => h.collider.name);
        Debug.Log($"결제 클릭 포인터 {Pc.Cursor01} 맞은 순서: {string.Join(", ", hits)}");
        yield return Click();
        yield return Real(0.1f);
    }

    /// <summary>지갑을 열고 칸을 집는다. 칸 이름은 cardPart, cashPart.</summary>
    protected static IEnumerator WalletTake(string part, ItemId expect)
    {
        var w = Wallet.I;
        if (!w.Open) yield return Tap(Key.Digit3);
        Assert.IsTrue(w.Open, "3 키로 지갑이 안 열림");
        yield return Real(0.7f);
        var t = Field<Transform>(w, part);
        Assert.IsTrue(t.gameObject.activeInHierarchy, part + " 안 보임");
        yield return Point(() => t.position);
        yield return Click();
        yield return Real(0.1f);
        Assert.AreEqual(expect, HandRig.I.Held, "지갑에서 집은 것");
    }

    // ---- HUD 버튼 ----

    static Vector2 ScreenOf(RectTransform rect)
    {
        var canvas = rect.GetComponentInParent<Canvas>();
        var cam = canvas != null && canvas.renderMode != RenderMode.ScreenSpaceOverlay ? canvas.worldCamera : null;
        return RectTransformUtility.WorldToScreenPoint(cam, rect.TransformPoint(rect.rect.center));
    }

    static IEnumerator ClickRect(RectTransform rect)
    {
        Vector2 at = ScreenOf(rect);
        if (Pc.CurrentMode == PlayerController.Mode.Cursor)
            Pc.SetCursor01(new Vector2(at.x / UnityEngine.Screen.width, at.y / UnityEngine.Screen.height));
        // 위치를 먼저 넣고 다음 프레임에 누른다
        InputSystem.QueueStateEvent(MouseDevice, new MouseState { position = at });
        yield return null;
        yield return Click(at);
    }

    protected static IEnumerator PressGiveUp()
    {
        yield return Until(() => RoundUi.I.GiveUpShown, 10f, "그만두기 버튼");
        yield return ClickRect(Field<RectTransform>(RoundUi.I, "giveUp"));
    }

    protected static IEnumerator Pick(string label, float sec = 30f)
    {
        var ui = RoundUi.I;
        var rows = Field<RectTransform[]>(ui, "choiceRows");
        var labels = Field<TMP_Text[]>(ui, "choiceLabels");
        int row = -1;
        yield return Until(() =>
        {
            row = Array.FindIndex(labels, l => l.gameObject.activeInHierarchy && l.text == label);
            return ui.ChoiceOpen && row >= 0;
        }, sec, "선택지 " + label);
        yield return ClickRect(rows[row]);
        yield return Until(() => !ui.ChoiceOpen || labels[row].text != label, 5f, "선택지 닫힘 " + label);
    }

    // ---- 돋보기 ----

    protected static IEnumerator FocusReady()
    {
        yield return Until(() => Debuff.LensFocused, 12f, "돋보기 초점");
    }

    /// <summary>돋보기를 들고 시선을 조금씩 옮겨 글을 찾는다. 사람이 원을 글 위로 가져가는 것과 같다.</summary>
    protected static IEnumerator LensOn(Readable r)
    {
        var area = Field<Collider>(r, "area");
        if (HandRig.I.Held != ItemId.Lens) yield return Tap(Key.Digit2);
        Assert.AreEqual(ItemId.Lens, HandRig.I.Held, "2 키로 돋보기를 못 듦");
        yield return Real(0.4f);
        yield return Pc.LookAt(area.bounds.center, 0.02f);
        float yaw = Pc.Yaw, pitch = Pc.Pitch;
        for (int ring = 0; ring < 16 && !r.Seen; ring++)
            for (int i = 0; i < 8 && !r.Seen; i++)
            {
                float a = i * Mathf.PI / 4f, d = ring * 2.5f;
                yield return FocusReady();
                yield return Pc.TurnTo(yaw + Mathf.Cos(a) * d, pitch + Mathf.Sin(a) * d, 0.01f);
                yield return null;
                yield return null;
            }
        Assert.IsTrue(r.Seen, "돋보기로 못 읽음 " + r.name);
    }

    // ---- 공통 판정 ----

    protected void AssertSaw(params string[] lines)
    {
        var missing = lines.Where(l => !rec.Saw(l)).ToArray();
        Assert.IsEmpty(missing, "화면에 안 나온 문구: " + string.Join(" / ", missing));
    }

    /// <summary>시트 공통 규칙: 호칭, 나이 숫자, 금지 기호.</summary>
    protected void AssertCleanText()
    {
        var bad = new Regex(@"어르신|할아버지|할머니|학생|[2468]0대|·|—|→|×|[①-⑳]");
        var hits = rec.Lines.Where(l => bad.IsMatch(l)).ToArray();
        Assert.IsEmpty(hits, "금지 문구: " + string.Join(" / ", hits));
    }

    // ---- 촬영 ----

    protected static IEnumerator Shot(string name)
    {
        yield return new WaitForEndOfFrame();
        int w = UnityEngine.Screen.width, h = UnityEngine.Screen.height;
        var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
        ScreenCapture.CaptureScreenshotIntoRenderTexture(rt);
        var flip = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
        Graphics.Blit(rt, flip, new Vector2(1f, -1f), new Vector2(0f, 1f));
        var prev = RenderTexture.active;
        RenderTexture.active = flip;
        var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
        tex.Apply();
        RenderTexture.active = prev;
        RenderTexture.ReleaseTemporary(rt);
        RenderTexture.ReleaseTemporary(flip);
        string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Screenshots"));
        Directory.CreateDirectory(dir);
        File.WriteAllBytes(Path.Combine(dir, "rounds-" + name + ".png"), tex.EncodeToPNG());
        Object.Destroy(tex);
    }

    // ---- 회차 조각. 완주와 갈래 시험이 같이 쓴다 ----

    protected IEnumerator PlayR1Stop()
    {
        yield return InChapter(0);
        var d = Object.FindAnyObjectByType<R1StopDirector>();
        yield return Until(() => !Pc.Frozen, 20f, "1회차 시작");
        yield return Use(Field<Interactable>(d, "askPasser"));
        yield return Until(() => rec.Saw("112번 타시면 돼요. 곧 와요."), 10f, "행인 대답");
        yield return Use("버스 타기", 60f);
        int n = 0;
        yield return Mash(c => n = c);
        Assert.AreEqual(10, n, "1회차 마싱 횟수");
        yield return Free();
        Assert.AreEqual(ItemId.Card, HandRig.I.Held, "버스 안 카드");
        yield return Use(Field<PayPoint>(d, "terminal").GetComponent<Interactable>());
        yield return InChapter(1);
    }

    protected IEnumerator PlayR1Storefront()
    {
        yield return Use("당기기", 30f);
        yield return InChapter(2);
    }

    protected IEnumerator PlayR1Store()
    {
        var staff = Field<Interactable>(Object.FindAnyObjectByType<R1StoreDirector>(), "talkStaff");
        yield return Until(() => staff.active && !Pc.Frozen && rec.Saw("어서 오세요!"), 90f, "알바생 인사");
        yield return Real(0.5f);
        yield return Use(staff);
        yield return Until(() => rec.Saw("여기 누르시면 돼요. 제가 도와드릴게요."), 15f, "알바생 친절");
        yield return EnterKiosk();
        yield return Screen("menu");
        yield return Touch("soldout");
        yield return Touch("burger");
        yield return Screen("pay");
        Assert.AreEqual(ItemId.Card, HandRig.I.Held, "결제 창 카드");
        yield return ClickPay();
        yield return Screen("done");
        yield return Free(30f);
        Assert.AreEqual(274, Game.Order.number);
        var d = Object.FindAnyObjectByType<R1StoreDirector>();
        var take = Field<Interactable>(d, "takeBag");
        yield return Until(() => take.active && rec.Saw("274번 고객님, 주문하신 메뉴 나왔습니다."), 40f, "호출");
        yield return Use(take);
        var exit = Field<Interactable>(d, "exitDoor");
        yield return Until(() => exit.active, 10f, "나가기 켜짐");
        yield return Use(exit);
        yield return InChapter(3);
    }

    protected IEnumerator PlayR2()
    {
        var staff = Field<Interactable>(Object.FindAnyObjectByType<R2CafeDirector>(), "talkStaff");
        yield return Until(() => staff.active && !Pc.Frozen, 30f, "카페 알바생 물을 수 있음");
        yield return Use(staff);
        yield return Until(() => rec.Saw("아, 그거 여기 누르시면 돼요."), 15f, "카페 알바생");
        yield return EnterKiosk();
        yield return Screen("menu");
        yield return Touch("latte");
        yield return Touch("next");
        Assert.AreEqual("menu", Kiosk.Screen, "메뉴 없이 다음");
        yield return TouchAll("americano", "next");
        yield return Screen("shot");
        yield return Touch("shot0");
        yield return Screen("ice");
        yield return Touch("ice1");
        yield return Screen("coupon");
        yield return Touch("coupon_none");
        yield return Screen("point");
        yield return Touch("point_skip");
        yield return Screen("pay");
        yield return WalletTake("cardPart", ItemId.Card);
        yield return ClickPay();
        yield return Screen("done");
        yield return Free(30f);
        Assert.IsFalse(Wallet.I.Open, "키오스크 뒤 지갑이 열린 채");
        var cup = Field<Interactable>(Object.FindAnyObjectByType<R2CafeDirector>(), "takeCup");
        yield return Until(() => Object.FindAnyObjectByType<R2CafeDirector>() != null && rec.Saw("...번 고객..."), 40f, "카페 호출");
        yield return Use(cup);
        yield return InChapter(4);
    }

    protected IEnumerator R3ToSms()
    {
        yield return EnterKiosk();
        yield return Screen("movie");
        yield return Touch("movie0");
        yield return Screen("hall");
        yield return Touch("hall0");
        yield return Screen("seat");
        yield return Touch("next");
        yield return Touch("seat_1_2");
        yield return Touch("next");
        yield return Screen("sms");
    }

    protected IEnumerator R3Finish()
    {
        var note = Field<TMP_Text>(RoundUi.I, "sideNote");
        yield return Until(() => Regex.IsMatch(note.text, @"^\d{6}$"), 5f, "문자 번호");
        foreach (char c in note.text.ToCharArray()) yield return Touch("key" + c);
        yield return Screen("pay");
        yield return Tap(Key.Digit3);
        Assert.AreEqual(ItemId.Card, HandRig.I.Held, "3 키 카드");
        yield return ClickPay();
    }

    protected IEnumerator PlayR3()
    {
        var staff = Field<Interactable>(Object.FindAnyObjectByType<R3CinemaDirector>(), "talkStaff");
        yield return Until(() => staff.active && !Pc.Frozen, 30f, "영화관 알바생 물을 수 있음");
        yield return Use(staff);
        yield return Until(() => rec.Saw("거기 다 나와 있어요."), 15f, "영화관 알바생");
        yield return R3ToSms();
        yield return R3Finish();
        yield return InChapter(5);
    }

    protected IEnumerator PlayR4Storefront()
    {
        var d = Object.FindAnyObjectByType<R4StorefrontDirector>();
        yield return Until(() => Wallet.I.Open, 30f, "지갑 열림");
        Assert.AreEqual(PlayerController.Mode.Cursor, Pc.CurrentMode, "4-0 포인터");
        yield return Real(0.8f);

        // 돋보기 없이 쪽지
        var part = Field<Transform>(Wallet.I, "notePart");
        yield return Point(() => part.position);
        yield return Click();
        yield return Until(() => rec.Saw("뭐라고 썼더라."), 6f, "쪽지 혼잣말");

        // 돋보기로 쪽지
        bool read = false;
        Action hit = () => read = true;
        Wallet.I.NoteRead += hit;
        yield return FocusReady();
        yield return Tap(Key.Digit2);
        Assert.AreEqual(ItemId.Lens, HandRig.I.Held, "돋보기");
        yield return Real(0.5f);
        var note = Field<Readable>(Wallet.I, "note");
        var area = Field<Collider>(note, "area");
        // 사람이 돋보기를 쪽지 위로 이리저리 옮기는 것과 같다
        if (!read) yield return Point(() => area.bounds.center);
        Vector2 home = Pc.Cursor01;
        Debug.Log($"쪽지 시작 포인터 {home} 렌즈 시야 {PostState.Lens} 쪽지 화면 {Pc.Eye.WorldToViewportPoint(area.bounds.center)} 크기 {area.bounds.size} 켜짐 {area.enabled}/{area.gameObject.activeInHierarchy}");
        for (int ring = 0; ring < 14 && !read; ring++)
            for (int i = 0; i < 10 && !read; i++)
            {
                float a = i * Mathf.PI / 5f, step = ring * 0.03f;
                yield return FocusReady();
                Pc.SetCursor01(home + new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * step);
                for (int f = 0; f < 6 && !read; f++) yield return null;
                if (read) Debug.Log($"쪽지 읽힘 포인터 {Pc.Cursor01} 렌즈 시야 {PostState.Lens}");
            }
        Wallet.I.NoteRead -= hit;
        Assert.IsTrue(read, "쪽지가 돋보기로 안 읽힘");
        yield return Free(20f);

        // 민다. 안 열린다
        yield return Use("밀기", 20f);
        yield return Until(() => rec.Saw("어? 왜 안 열려."), 10f, "4-1 대사");
        yield return Real(0.6f);
        Assert.AreEqual(5, Game.chapterIndex, "미는 것으로 안 넘어감");
        Assert.IsNull(Usable("당기기"), "읽기 전 당기기");

        // 돋보기로 읽고 당긴다
        yield return LensOn(Field<Readable>(d, "sticker"));
        yield return Until(() => Usable("당기기") != null, 5f, "당기기 생김");
        yield return Use("당기기");
        yield return Until(() => rec.Saw("아, 당기는 거구먼."), 15f, "4-2 대사");
        yield return InChapter(6);
    }

    /// <summary>메뉴를 찾아 담고 팝업을 지나 결제 창까지 간다.</summary>
    protected IEnumerator R4ToPay()
    {
        yield return Screen("idle");
        yield return Touch("start");
        yield return Screen("menu");
        yield return Touch("next");
        Assert.AreEqual("menu", Kiosk.Screen, "빈 장바구니로 다음");
        yield return Touch("list");
        yield return Touch("item_0");
        yield return Touch("next");
        yield return Screen("pop_code");
        yield return Touch("x");
        yield return Screen("pop_robot");
        yield return Touch("x");
        Assert.AreEqual("pop_robot", Kiosk.Screen, "로봇 인증 없이 닫힘");
        yield return Touch("check");
        yield return Touch("x");
        yield return Screen("pop_app");
        yield return Touch("x");
        yield return Screen("pop_point");
        yield return Touch("skip");
        yield return Screen("pay");
    }

    /// <summary>지폐를 count번 넣는다.</summary>
    protected IEnumerator Bounce(int count)
    {
        if (HandRig.I.Held != ItemId.Cash) yield return WalletTake("cashPart", ItemId.Cash);
        for (int i = 0; i < count; i++) yield return ClickPay();
    }

    /// <summary>4-10a 또는 선택지 뒤 문까지 나간다.</summary>
    protected IEnumerator R4Leave()
    {
        yield return Use("나가기", 60f);
        yield return InChapter(7);
    }

    protected IEnumerator PlayR4Stop(bool lastOnly = false)
    {
        var d = Object.FindAnyObjectByType<R4StopDirector>();
        yield return Free(30f);

        // 4-11 돋보기 없이 전광판, 4-13 안내문, 4-14 행인
        var bis = Field<Transform>(d, "bisLook");
        Vector3 toBis = Pc.transform.position - bis.position;
        toBis.y = 0f;
        Vector3 stand = bis.position + toBis.normalized * 4f;
        stand.y = Pc.transform.position.y;
        Pc.Teleport(stand, Pc.Yaw);
        yield return Pc.LookAt(bis.position, 0.02f);
        yield return Until(() => rec.Saw("안 보이네... 몇 번이 온다는 거야."), 6f, "4-11 대사");
        yield return LensOn(Field<Readable>(d, "notice"));
        yield return Until(() => rec.Saw("현금 없는 버스 운행 안내"), 6f, "4-13 안내문");
        yield return Tap(Key.Digit2);
        yield return Use(Field<Interactable>(d, "askPasser"));
        yield return Until(() => rec.Saw("허허... 다들 바쁘구먼."), 20f, "4-14 대사");
        AssertSaw("저 바빠서요.");

        var driver = Field<Interactable>(d, "askDriver");
        var buses = Field<BusMover[]>(d, "buses");
        var doors = new List<int>();
        for (int i = 0; i < 3; i++)
        {
            yield return Use("버스 타기", 90f);
            int n = 0;
            yield return Mash(c => n = c);
            doors.Add(n);
            yield return Until(() => driver.active && !Pc.Frozen, 20f, "기사 묻기 " + i);
            yield return Use(driver);
        }
        Assert.AreEqual(new[] { 40, 40, 40 }, doors.ToArray(), "버스마다 마싱 횟수");

        // 4-20, 4-21
        yield return Until(() => rec.Saw("112번이요."), 10f, "세 번째 번호");
        yield return Until(() => !Pc.Frozen, 10f, "4-20 조작");
        yield return Until(() => rec.Saw("현금은 안 받아요."), 10f, "기사 첫말");
        yield return Until(() => rec.Saw("거기 써 있잖아요."), 20f, "기사 반복");
        yield return LensOn(Field<Readable>(d, "terminalNotice"));
        yield return Pick("현금밖에 없는데요");
        yield return Until(() => rec.Saw("카드 찍으세요."), 8f, "기사 답 1");
        yield return Pick("카드는 어디서 만들어요?");
        yield return Until(() => rec.Saw("앱에서 하세요."), 8f, "기사 답 2");
        yield return Pick("내릴게요");
    }

    protected IEnumerator PlayEnding()
    {
        var ui = RoundUi.I;
        var group = Field<CanvasGroup>(ui, "endGroup");
        yield return Until(() => group.gameObject.activeSelf, 120f, "엔딩 시작");
        yield return Until(() => rec.Saw(Ending.Title), 20f, "엔딩 제목");
        AssertSaw(Ending.Stat, Ending.Source);
        yield return Real(1.2f);
        yield return Click();
        yield return InChapter(0, 30f);
    }
}
