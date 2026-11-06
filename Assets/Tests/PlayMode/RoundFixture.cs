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
        int tick;

        static string Clean(string s) => Regex.Replace(Regex.Replace(s, "<[^>]+>", ""), @"\s+", "");

        void LateUpdate()
        {
            if (Hud.I != null)
                foreach (var t in Hud.I.GetComponentsInChildren<TMP_Text>(false))
                    if (!string.IsNullOrEmpty(t.text)) Lines.Add(Clean(t.text));
            if (++tick % 20 == 0)
                foreach (var t in FindObjectsByType<TMP_Text>(FindObjectsSortMode.None))
                    if (!string.IsNullOrEmpty(t.text)) Lines.Add(Clean(t.text));
        }

        /// <summary>앞 회차에서 나온 같은 대사를 지운다. 다시 나오기를 기다릴 때 쓴다.</summary>
        public void Forget(params string[] lines)
        {
            foreach (string line in lines)
            {
                string want = Clean(line);
                Lines.RemoveWhere(l => l.Contains(want));
            }
        }

        public bool Saw(string line)
        {
            string want = Clean(line);
            return Lines.Any(l => l.Contains(want));
        }
    }

    protected Recorder rec;

    /// <summary>이 소지품의 숫자 키. 표시 번호와 같다.</summary>
    protected static Key ItemKey(ItemId id)
    {
        int n = ItemKeys.Of(id);
        Assert.Greater(n, 0, id + " 칸 없음");
        return Key.Digit1 + (n - 1);
    }

    float savedVolume;
    InputSettings.BackgroundBehavior savedBackground;
    InputSettings.EditorInputBehaviorInPlayMode savedEditorInput;
    readonly List<string> overrides = new();
    InputDevice realMouse, realKeyboard, testMouse, testKeyboard;

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
        Hud.AutoTitle = true;
        savedBackground = InputSystem.settings.backgroundBehavior;
        savedEditorInput = InputSystem.settings.editorInputBehaviorInPlayMode;
        InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
        InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;

        // 실제 장치가 움직이면 게임 커서가 그 자리로 튀므로 시험 동안 끄고 가상 장치만 쓴다
        realMouse = Mouse.current;
        realKeyboard = Keyboard.current;
        if (realMouse != null) InputSystem.DisableDevice(realMouse);
        if (realKeyboard != null) InputSystem.DisableDevice(realKeyboard);
        testMouse = InputSystem.AddDevice<Mouse>("TestMouse");
        testKeyboard = InputSystem.AddDevice<Keyboard>("TestKeyboard");
        testMouse.MakeCurrent();
        testKeyboard.MakeCurrent();

        yield return Until(() => ConfigTableLoader.IsLoaded, 20f, "설정 로드");
        yield return SceneManager.LoadSceneAsync("R1_Home", LoadSceneMode.Single);
        yield return null;
        yield return null;
        Assert.IsNotNull(GameState.I, "GameState 없음");
        yield return Until(() => !GameState.I.Booting, 20f, "부팅 씬에서 첫 챕터로");
        yield return null;
        yield return null;
        yield return Until(() => !Hud.I.TitleOpen, 20f, "시작 화면과 오류 페이지");
        var host = new GameObject("TestRecorder");
        Object.DontDestroyOnLoad(host);
        rec = host.AddComponent<Recorder>();
    }

    [UnityTearDown]
    public IEnumerator TearDown()
    {
        Time.timeScale = 1f;
        Hud.AutoTitle = false;
        AudioListener.volume = savedVolume;
        InputSystem.settings.backgroundBehavior = savedBackground;
        InputSystem.settings.editorInputBehaviorInPlayMode = savedEditorInput;
        if (testMouse != null) InputSystem.RemoveDevice(testMouse);
        if (testKeyboard != null) InputSystem.RemoveDevice(testKeyboard);
        if (realMouse != null) { InputSystem.EnableDevice(realMouse); realMouse.MakeCurrent(); }
        if (realKeyboard != null) { InputSystem.EnableDevice(realKeyboard); realKeyboard.MakeCurrent(); }
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

    /// <summary>게이지를 거의 멈춘다. 시험 배속에서 줄 복귀로 빠지지 않게 하는 완주 전용. 줄 복귀 자체는 GaugeFull 시험이 본다.</summary>
    protected void CalmLine()
    {
        Override("Age40_NunchiFillSec", 6000f);
        Override("Age80_NunchiFillSec", 6000f);
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

    /// <summary>대사가 이 순서로 나올 때까지 기다린다. 한 줄마다 sec초까지.</summary>
    protected IEnumerator Lines(float sec, params string[] lines)
    {
        foreach (string line in lines) yield return Until(() => rec.Saw(line), sec, "대사 " + line);
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
        float end = Time.realtimeSinceStartup + 6f, again = Time.realtimeSinceStartup + 0.5f;
        while (!prompt.text.Contains(label))
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail($"프롬프트 {label} 안 뜸, 지금 '{prompt.text}' (씬 {Scene}, 멈춤 {Pc.Frozen}, 모드 {Pc.CurrentMode})");
            // 입력 없는 연출이 시선을 돌렸으면 사람처럼 다시 본다
            if (!Pc.Frozen && Time.realtimeSinceStartup > again)
            {
                again = Time.realtimeSinceStartup + 0.5f;
                yield return Pc.LookAt(it.transform.position, 0.02f);
            }
            yield return null;
        }
        Debug.Log($"사용 {label} 프롬프트 '{prompt.text}' 멈춤 {Pc.Frozen} 모드 {Pc.CurrentMode} 키보드 {Keyboard.current?.deviceId} 시각 {Time.time:F2}");
        yield return Tap((Key)Enum.Parse(typeof(Key), it.key, true));
        Debug.Log($"사용 뒤 자막 '{Field<TMP_Text>(Hud.I, "subs").text}' 프롬프트 '{prompt.text}' 시각 {Time.time:F2}");
    }

    // ---- 계단 ----

    // ---- 키오스크 ----

    protected static KioskController Kiosk => Object.FindObjectsByType<KioskController>(FindObjectsSortMode.None).First(k => k.Pack != null);

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
        var ad = id != "ad_close" ? PackScreens.Find("ad_close") : null;
        if (ad != null)
        {
            yield return Point(() => ButtonWorld(ad));
            yield return Click();
            yield return Real(0.1f);
            b = PackScreens.Find(id);
            Assert.IsNotNull(b, "광고 닫은 뒤 버튼 " + id);
        }
        yield return Point(() => ButtonWorld(b));
        var names = Physics.RaycastAll(HandRig.I.PointerRay(), 3f, ~0, QueryTriggerInteraction.Collide).OrderBy(h => h.distance).Select(h => h.collider.name);
        if (id == "start") Debug.Log($"터치 {id} 화면 {Kiosk.Screen} 포인터 {Pc.Cursor01} uv {PackScreens.Uv(b)} 버튼들 [{string.Join(",", PackScreens.Buttons().Select(x => x.id))}] 맞은 순서 {string.Join(",", names)}");
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
        var flap = Object.FindAnyObjectByType<PosterFlap>();
        if (flap != null && !flap.Opened)
        {
            var hit = Field<Collider>(flap, "hit");
            yield return Point(() => hit.bounds.center);
            yield return Click();
            yield return Until(() => flap.Opened, 3f, "포스터 들춤");
            yield return Real(0.5f);
        }
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
        if (!w.Open) yield return Tap(ItemKey(ItemId.Wallet));
        Assert.IsTrue(w.Open, "지갑 키로 지갑이 안 열림");
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
        if (HandRig.I.Held != ItemId.Lens) yield return Tap(ItemKey(ItemId.Lens));
        Assert.AreEqual(ItemId.Lens, HandRig.I.Held, "돋보기 키로 돋보기를 못 듦");
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
        var bad = new Regex(@"^:|손님:|알바생:|키오스크:|할아버지|할머니|[2468]0대|·|—|→|×|[①-⑳]");
        // Hud가 붙이는 화자 라벨은 빼고 본다. 시트의 말머리가 대사 본문에 새는 것을 막는 판정이다
        var label = new Regex("^(알바생|키오스크):");
        var hits = rec.Lines.Where(l => bad.IsMatch(label.Replace(l, ""))).ToArray();
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

    /// <summary>W를 누른 채 목표로 걷는다. 곧장 못 가면 경고를 남기고 옮긴다(직선만 시험하므로 길 막힘은 사람 확인 몫).</summary>
    protected static IEnumerator WalkW(Func<Vector3> target, Func<bool> arrived, float sec, string what)
    {
        var kb = Keyboard.current ?? InputSystem.AddDevice<Keyboard>();
        yield return Pc.LookAt(target(), 0.02f);
        yield return Pc.TurnTo(Pc.Yaw, 0f, 0.02f);
        InputSystem.QueueStateEvent(kb, new KeyboardState(Key.W));
        float end = Time.realtimeSinceStartup + sec, check = Time.realtimeSinceStartup + 2f;
        Vector3 last = Pc.transform.position;
        bool stuck = false;
        while (!arrived() && Time.realtimeSinceStartup < end && !stuck)
        {
            if (Time.realtimeSinceStartup > check)
            {
                check = Time.realtimeSinceStartup + 2f;
                if ((Pc.transform.position - last).magnitude < 0.05f) stuck = true;
                last = Pc.transform.position;
            }
            yield return null;
        }
        InputSystem.QueueStateEvent(kb, new KeyboardState());
        yield return null;
        if (!arrived())
        {
            Debug.LogWarning($"걷기 경로 막힘 {what}: {Pc.transform.position} 에서 멈춤");
            Vector3 p = target();
            p.y = Pc.transform.position.y;
            Pc.Teleport(p, Pc.Yaw);
            yield return null;
        }
    }

    protected IEnumerator PlayR1Storefront()
    {
        yield return InChapter(0);
        yield return Use("당기기", 30f);
        yield return InChapter(1);
    }

    /// <summary>1-7, 1-8. 포인터와 좌클릭만으로 결제까지.</summary>
    protected IEnumerator R1Kiosk()
    {
        KioskPick.Reseed(7);   // 뽑힌 칸만 item_set, 첫 칸 불고기는 눌러도 담기지 않는다
        yield return EnterKiosk();
        yield return Screen("idle");
        yield return Touch("start");
        yield return Screen("place");
        yield return Touch("dine");
        yield return Screen("menu");
        yield return Touch("item_bulgogi");
        Assert.AreEqual("menu", Kiosk.Screen, "쪽지에 없는 메뉴는 넘어가지 않음");
        Assert.AreEqual(0, Field<KioskState>(Kiosk.Pack, "K").cart.Count, "쪽지에 없는 메뉴는 담기지 않음");
        yield return Until(() => rec.Saw("이거 아니잖아"), 5f, "쪽지에 없는 메뉴 혼잣말");
        yield return Touch("item_set");
        yield return Screen("cart");
        Assert.AreEqual(KioskPick.SetName, Game.Order.item, "쪽지의 신메뉴");
        Assert.AreEqual(KioskPick.SetPrice, Field<KioskState>(Kiosk.Pack, "K").Total, "신메뉴 세트 가격");
        yield return Touch("checkout");
        yield return Screen("pay");
        yield return Touch("pay_card");
        yield return Screen("card");
        Assert.AreEqual(ItemId.Card, HandRig.I.Held, "카드 화면에서 카드를 듦");
        // 종이를 넘기고 틈에 꽂는다. 넘기기 전 틈은 가려져 있다
        var flap = Object.FindAnyObjectByType<PosterFlap>();
        Assert.IsFalse(flap.Opened, "종이가 틈을 가리고 시작");
        yield return Real(0.6f);
        yield return Shot("r1-poster");
        yield return ClickPay();
        Assert.IsTrue(flap.Opened, "종이 넘김");
        yield return Screen("paying", 3f);
        Assert.AreEqual(ItemId.None, HandRig.I.Held, "카드가 틈으로 들어감");
        yield return Real(0.4f);
        yield return Shot("r1-card-in");

        // 기다렸다가 카드를 뺀다
        yield return Screen("cardout", 15f);
        yield return ClickPay();
        yield return Screen("done", 5f);

        yield return TearReceipt("r1-receipt");
    }

    /// <summary>영수증이 다 나오면 뜯는다.</summary>
    protected IEnumerator TearReceipt(string shot = null)
    {
        var hit = Field<Collider>(Object.FindAnyObjectByType<KioskReceipt>(FindObjectsInactive.Include), "hit");
        yield return Until(() => hit.enabled, 15f, "영수증 다 나옴");
        Assert.IsTrue(Kiosk.Active, "뜯기 전에는 안 끝남");
        if (shot != null) yield return Shot(shot);
        yield return Point(() => hit.bounds.center);
        yield return Click();
    }


    protected IEnumerator PlayR1Store()
    {
        yield return Lines(60f, "어르신, 이거 돈 안 들어가요.", "아, 그려?", "그러면 방법이 없는겨?", "제 카드로 결제해 드릴게요.", "아이고, 고맙구먼.");
        var staff = Field<Interactable>(Object.FindAnyObjectByType<R1StoreDirector>(), "talkStaff");
        yield return Until(() => staff.active && !Pc.Frozen && rec.Saw("어서 오세요!"), 90f, "알바생 인사");
        yield return Real(0.5f);
        yield return Use(staff);
        yield return Until(() => rec.Saw("여기 누르시면 돼요. 제가 도와드릴게요."), 15f, "알바생 친절");
        yield return R1Kiosk();
        yield return Free(30f);
        Assert.AreEqual(274, Game.Order.number);
        var d = Object.FindAnyObjectByType<R1StoreDirector>();
        var take = Field<Interactable>(d, "takeBag");
        yield return Until(() => take.active && rec.Saw("274번 고객님, 주문하신 메뉴 나왔습니다."), 40f, "호출");
        yield return Use(take);
        var exit = Field<Interactable>(d, "exitDoor");
        yield return Until(() => exit.active, 10f, "나가기 켜짐");
        yield return Use(exit);
        yield return InChapter(2);
    }

    /// <summary>2-3, 2-4. 쪽지대로 2잔을 담고 잔마다 옵션을 고른다.</summary>
    protected IEnumerator R2Order()
    {
        yield return Screen("menu");
        yield return Touch("next");
        Assert.AreEqual("menu", Kiosk.Screen, "메뉴 없이 다음");
        yield return Touch("item_americano");
        yield return Touch("next");
        Assert.AreEqual("menu", Kiosk.Screen, "1잔으로 다음");
        yield return Touch("tab_2");
        yield return Touch("item_icetea");
        yield return Touch("next");
        yield return Screen("shot");
        yield return Touch("shot1");
        yield return Screen("ice");
        yield return Touch("ice1");
        yield return Screen("shot");
        yield return Touch("shot1");
        yield return Screen("ice");
        yield return Touch("ice1");
        yield return Screen("coupon");
        StringAssert.Contains("아메리카노 샷 추가", Game.Order.item);
        StringAssert.Contains("아이스티 샷 추가", Game.Order.item);
        yield return Touch("coupon_none");
        yield return Screen("point");
        yield return Touch("point_skip");
        yield return Screen("pay");
    }

    protected IEnumerator PlayR2()
    {
        yield return Until(() => !Pc.Frozen, 30f, "카페 시작");
        yield return Until(() => Note.Opened, 5f, "2회차 쪽지");
        // 주문하기가 막힌 뒤에야 직원에게 물을 수 있다
        yield return EnterKiosk();
        yield return Touch("next");
        yield return Until(() => rec.Saw("누구 물어볼 사람 없나?"), 15f, "주문하기가 막히고 혼잣말");
        var cafe = Object.FindAnyObjectByType<R2CafeDirector>();
        yield return Until(() => Field<bool>(cafe, "wondered"), 15f, "혼잣말이 끝나야 말을 걸 수 있음");
        yield return Tap(Key.A);
        yield return Real(0.4f);
        yield return Tap(Key.E);
        yield return Until(() => rec.Saw("아이스티에... 커피를 넣는다고?"), 20f, "직원 대답");
        yield return Tap(Key.D);
        yield return R2Order();
        yield return WalletTake("cardPart", ItemId.Card);
        yield return ClickPay();
        yield return Screen("cardout", 10f);
        yield return ClickPay();
        yield return Screen("done");
        yield return Free(30f);
        Assert.IsFalse(Wallet.I.Open, "키오스크 뒤 지갑이 열린 채");
        var cup = Field<Interactable>(Object.FindAnyObjectByType<R2CafeDirector>(), "takeCup");
        yield return Until(() => Object.FindAnyObjectByType<R2CafeDirector>() != null && rec.Saw("...번 고객..."), 40f, "카페 호출");
        yield return Use(cup);
        yield return InChapter(3);
    }

    /// <summary>80대 집. 시작 연출 뒤 쪽지를 들어 맨눈으로 읽고 내리고, 신발을 신고 문을 연다.</summary>
    protected IEnumerator PlayR4Home()
    {
        yield return InChapter(3);
        yield return Until(() => rec.Saw("뭐라고 썼더라."), 30f, "시작 연출 뒤 혼잣말");
        yield return Tap(ItemKey(ItemId.Memo));
        Assert.IsTrue(Note.Opened, "쪽지 듦");
        yield return Until(() => rec.Saw("불고기 버거 세트... 사이다로. 그래, 그거."), 15f, "쪽지 읽음");
        var prompt = Field<TMP_Text>(Hud.I, "prompt");
        yield return Until(() => prompt.text.Contains("쪽지 내리기"), 20f, "쪽지 내리기 프롬프트");
        yield return Tap(Key.E);
        Assert.IsFalse(Note.Opened, "쪽지 내림");
        yield return Use("신발 신기", 15f);
        yield return Use("문 열기", 20f);
        yield return Until(() => rec.Saw("자, 나가볼까."), 15f, "문 앞 대사");
        yield return InChapter(4);
    }

    protected IEnumerator PlayR4Storefront()
    {
        yield return InChapter(5, 90f);
        var d = Object.FindAnyObjectByType<R4StorefrontDirector>();
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

    protected static KioskState K => ((R4ProtoPack)Kiosk.Pack).Flow.K;

    /// <summary>지금 눌러야 할 버튼. 처음 화면으로 돌아가도 여기서 다시 잇는다.</summary>
    static string R4Next()
    {
        var k = K;
        if (k.info != null) return PackScreens.Find("pop_skip") ? "pop_skip" : "info_close";
        return Kiosk.Screen switch
        {
            "idle" => "start",
            "place" => "takeout",
            "member" => "skip",
            "menu" => k.cart.Count > 0 ? "cart" : k.tab != "CLASSIC" ? "tab_CLASSIC" : "item_bulgogi",
            "option" => "opt_combo",
            "side" or "drink" => "next",
            "upsell" => "up_no",
            "cart" => k.cart.Count > 0 ? "checkout" : "add_more",
            "pay" => "pay_card",
            _ => null,
        };
    }

    /// <summary>불고기 세트를 담고 팝업을 지나 카드 화면까지 간다. 시간 초과나 줄 복귀로 처음이 되면 차례를 기다려 다시 누른다.</summary>
    protected IEnumerator R4ToPay(float sec = 150f)
    {
        float end = Time.realtimeSinceStartup + sec;
        while (!Kiosk.Active || Kiosk.Busy || Kiosk.Screen != "card")
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail($"카드 화면까지 못 감: 화면 {Kiosk.Screen}, 키오스크 {Kiosk.Active}, 눈치 {Kiosk.Nunchi.Value:F0}");
            if (!Kiosk.Active || Kiosk.Busy || RoundUi.I.ChoiceOpen) { yield return null; continue; }
            string id = R4Next();
            if (id == null || !PackScreens.Find(id)) { yield return null; continue; }
            if (id == "checkout") Assert.AreEqual(8900, K.Total, "불고기 세트 가격");
            yield return Touch(id);
            yield return Real(0.1f);
        }
    }

    /// <summary>지폐를 count번 넣는다.</summary>
    protected IEnumerator Bounce(int count)
    {
        // 1회차 어르신 장면과 같은 대사라 지워 두어야 R4Finish가 이번 대화를 기다린다
        rec.Forget("어르신, 이거 돈 안 들어가요.", "아, 그려?", "그러면 방법이 없는겨?", "제 카드로 결제해 드릴게요.", "아이고, 고맙구먼.");
        if (HandRig.I.Held != ItemId.Cash)
        {
            yield return WalletTake("cashPart", ItemId.Cash);
            Assert.IsFalse(Field<Transform>(Wallet.I, "cardPart").gameObject.activeSelf, "지갑에 카드 없음");
        }
        for (int i = 0; i < count; i++) yield return ClickPay();
    }

    /// <summary>지폐 3번 뒤 뒷사람 결제, 호출, 수령, 대사까지.</summary>
    protected IEnumerator R4Finish()
    {
        yield return Lines(30f, "어르신, 이거 돈 안 들어가요.", "아, 그려?", "그러면 방법이 없는겨?", "제 카드로 결제해 드릴게요.");
        yield return Until(() => rec.Saw("아이고, 고맙구먼."), 60f, "뒷사람 결제 뒤 인사");
        yield return Free(20f);
        var take = Field<Interactable>(Object.FindAnyObjectByType<R4StoreDirector>(), "takeBag");
        yield return Until(() => take.active, 120f, "호출");
        Assert.AreEqual(273, Game.Order.number, "주문 번호");
        yield return Use(take);
        yield return Until(() => rec.Saw("됐다... 됐어."), 15f, "받은 뒤 대사");
        yield return Until(() => rec.Saw("이거 하나 사기가 이렇게 힘들어서야."), 20f, "마지막 대사");
    }

    /// <summary>가는 길. 골목을 걸어 전광판을 보고, 행인 둘에게 묻고, 첫 버스를 놓치고, 돋보기로 읽고, 112번에 자동으로 탄다.</summary>
    protected IEnumerator PlayR4Stop()
    {
        yield return InChapter(4);
        var d = Object.FindAnyObjectByType<R4StopDirector>();
        yield return Until(() => !Pc.Frozen, 20f, "정류장 장면 시작");

        var zone = Field<Collider>(d, "stopZone");
        yield return WalkW(() => zone.bounds.center, () => zone.bounds.Contains(Pc.transform.position), 120f, "골목 걷기");
        yield return Until(() => rec.Saw("안 보이네... 몇 번이 온다는 거야."), 20f, "전광판 안 보임");
        var student = Field<Interactable>(d, "askStudent");
        yield return Until(() => student.active, 10f, "학생에게 물을 수 있음");
        yield return Use(student);
        yield return Until(() => rec.Saw("아, 저도 잘 모르겠어요."), 15f, "학생 답");
        var worker = Field<Interactable>(d, "askWorker");
        yield return Until(() => worker.active, 40f, "직장인에게 물을 수 있음");
        yield return Use(worker);
        yield return Until(() => rec.Saw("저 바빠서요."), 15f, "직장인 답");

        yield return Until(() => rec.Saw("아 이보시게 잠시만요!"), 60f, "첫 버스 놓침");
        var faces = Field<Readable[]>(d, "bisFaces");
        var look = Field<Transform>(d, "bisLook");
        var at = look.position;
        at.y = Pc.transform.position.y;
        Pc.Teleport(at + (Pc.transform.position - at).normalized * 4f, Pc.Yaw);
        yield return Free(10f);
        yield return LensOn(faces[0]);
        yield return Until(() => rec.Saw("이번 정류장은, 시장 입구입니다."), 90f, "112번 승차 뒤 안내방송");
        yield return InChapter(5, 30f);
    }

    protected void AssertNotSaw(params string[] lines)
    {
        var hit = lines.Where(l => rec.Saw(l)).ToArray();
        Assert.IsEmpty(hit, "없어진 문구가 나옴: " + string.Join(" / ", hit));
    }

    /// <summary>버거를 받은 뒤 결과. 문구, 제목, 클릭으로 처음으로.</summary>
    protected IEnumerator PlayResult()
    {
        var ui = RoundUi.I;
        var group = Field<CanvasGroup>(ui, "endGroup");
        yield return Until(() => group.gameObject.activeSelf, 30f, "결과 시작");
        yield return Until(() => rec.Saw(Ending.Title), 30f, "결과 제목");
        AssertSaw(Ending.Stat, Ending.Source);
        yield return Real(Bal.G("End_StatSec", 5f) / Time.timeScale + 0.5f);   // 이 시간이 지나야 클릭을 받는다
        yield return Click();
        yield return InChapter(0, 30f);
        Assert.IsFalse(group.gameObject.activeSelf, "처음으로 뒤 결과 화면이 남음");
    }
}
