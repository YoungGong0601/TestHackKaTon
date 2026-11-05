// 옛 Store 흐름용. 새 구조에 없는 KioskBot에 기대므로 컴파일에서 뺀다. 보관 여부는 사용자 판단
#if KIOSK_OLD_VIDEO
// 처음부터 끝까지 한 판을 사람처럼 진행하며 주요 순간만 _video/frames 에 프레임으로 저장한다. 평소 시험에서는 돌지 않는다(Explicit).
// 시간은 Time.captureFramerate로 고정한다. stride 1은 실시간, 2는 2배속, 0은 찍지 않고 건너뜀.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using Object = UnityEngine.Object;

public class VideoRun : KioskBotFixture
{
    const int Fps = 30, OutW = 1280, OutH = 720;

    static string Root => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "_video"));
    static string FrameDir => Path.Combine(Root, "frames");

    // 오버레이 HUD와 후처리가 모두 들어간 화면을 그린 뒤 찍는다. CaptureRun.Shot과 같은 방식
    class FrameTaker : MonoBehaviour
    {
        public int stride;
        public int Saved { get; private set; }

        int tick;
        Texture2D tex;

        IEnumerator Start()
        {
            tex = new Texture2D(OutW, OutH, TextureFormat.RGB24, false);
            var end = new WaitForEndOfFrame();
            while (true)
            {
                yield return end;
                if (stride > 0 && ++tick % stride == 0) Take();
            }
        }

        void Take()
        {
            int w = Screen.width, h = Screen.height;
            float aspect = (float)w / h, want = (float)OutW / OutH;
            float sx = Mathf.Min(1f, want / aspect), sy = Mathf.Min(1f, aspect / want);
            var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
            ScreenCapture.CaptureScreenshotIntoRenderTexture(rt);
            var flip = RenderTexture.GetTemporary(OutW, OutH, 0, RenderTextureFormat.ARGB32);
            Graphics.Blit(rt, flip, new Vector2(sx, -sy), new Vector2((1f - sx) * 0.5f, 1f - (1f - sy) * 0.5f));
            var prev = RenderTexture.active;
            RenderTexture.active = flip;
            tex.ReadPixels(new Rect(0, 0, OutW, OutH), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            RenderTexture.ReleaseTemporary(rt);
            RenderTexture.ReleaseTemporary(flip);
            File.WriteAllBytes(Path.Combine(FrameDir, $"f{Saved:D6}.jpg"), tex.EncodeToJPG(95));
            Saved++;
        }

        void OnDestroy()
        {
            if (tex) Destroy(tex);
        }
    }

    FrameTaker rec;
    Keyboard fakeKeys;
    readonly List<InputDevice> realDevices = new();
    KioskController kiosk;
    Transform quad;

    // 진짜 마우스와 키보드가 끼어들지 않게 막고 가상 키보드만 쓴다
    void TakeOverInput()
    {
        foreach (var d in InputSystem.devices.ToArray())
            if (d is Mouse || d is Keyboard)
            {
                InputSystem.DisableDevice(d);
                realDevices.Add(d);
            }
        fakeKeys = InputSystem.AddDevice<Keyboard>("VideoKeyboard");
        fakeKeys.MakeCurrent();
    }

    [UnityTearDown]
    public IEnumerator VideoTearDown()
    {
        Time.captureFramerate = 0;
        if (rec) Object.Destroy(rec.gameObject);
        if (fakeKeys != null) InputSystem.RemoveDevice(fakeKeys);
        fakeKeys = null;
        foreach (var d in realDevices) InputSystem.EnableDevice(d);
        realDevices.Clear();
        yield return null;
    }

    // ---- 도움 ----

    static T F<T>(object o, string name) =>
        (T)o.GetType().GetField(name, BindingFlags.NonPublic | BindingFlags.Instance).GetValue(o);

    static float FadeA()
    {
        var img = F<Component>(Hud.I, "fade");
        return ((Color)img.GetType().GetProperty("color").GetValue(img)).a;
    }

    static Interactable Find(string label) =>
        Object.FindObjectsByType<Interactable>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
            .FirstOrDefault(i => i.active && i.label == label);

    static string Subs => F<TMPro.TMP_Text>(Hud.I, "subs").text;
    static PlayerController P => PlayerController.I;
    static string Active => SceneManager.GetActiveScene().name;

    void Mark(string name)
    {
        string line = $"{rec.Saved} {name}";
        Debug.Log("영상 구간 " + line);
        File.AppendAllText(Path.Combine(Root, "marks.txt"), line + "\n");
    }

    static WaitForSeconds Wait(float sec) => new(sec);

    static IEnumerator SceneIs(string name) => Until(() => Active == name, 240f, "씬 " + name);
    static IEnumerator Unfrozen(string what) => Until(() => !P.Frozen, 120f, what);
    static IEnumerator Visible() => Until(() => FadeA() < 0.97f, 120f, "밝아짐");
    static IEnumerator Black() => Until(() => FadeA() >= 0.995f, 120f, "암전");

    static float YawTo(Vector3 at)
    {
        Vector3 d = at - P.transform.position;
        return Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
    }

    /// <summary>돌아서 걸어간다.</summary>
    static IEnumerator Walk(Vector3 at, float turnSec = 0.4f)
    {
        at.y = P.transform.position.y;
        yield return P.TurnTo(YawTo(at), 0f, turnSec);
        yield return P.WalkTo(at);
    }

    /// <summary>물체 앞까지 걸어가 바라본다. 막혀서 못 가면 그 자리로 옮긴다.</summary>
    static IEnumerator Approach(string label, float dist)
    {
        Interactable it = null;
        yield return Until(() => (it = Find(label)) != null, 120f, "상호작용 " + label);
        Vector3 from = P.transform.position - it.transform.position;
        from.y = 0f;
        Vector3 at = it.transform.position + from.normalized * dist;
        at.y = P.transform.position.y;
        yield return Walk(at);
        if (Vector3.Distance(P.transform.position, at) > 0.4f)
        {
            Debug.LogWarning("영상: 걷기가 막혀 옮김 " + label);
            P.Teleport(at, YawTo(it.transform.position));
            yield return null;
        }
        yield return P.LookAt(it.transform.position, 0.35f);
    }

    static IEnumerator Face(Vector3 stand, Vector3 look)
    {
        stand.y = P.transform.position.y;
        Vector3 d = look - stand;
        P.Teleport(stand, Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg);
        yield return null;
        yield return P.LookAt(look, 0.1f);
    }

    /// <summary>손끝을 월드 지점으로 천천히 옮긴다.</summary>
    static IEnumerator Aim(Func<Vector3> world, float sec)
    {
        Vector2 from = P.Cursor01;
        for (float t = 0f; t < sec; t += Time.deltaTime)
        {
            float u = Mathf.Clamp01(t / sec), e = u * u * (3f - 2f * u);
            P.SetCursor01(Vector2.Lerp(from, P.Eye.WorldToViewportPoint(world()), e));
            yield return null;
        }
        P.SetCursor01(P.Eye.WorldToViewportPoint(world()));
        yield return null;
    }

    Vector3 ButtonWorld(string id)
    {
        Vector2 uv = kiosk.Screens.Uv(kiosk.Screens.Find(id));
        return quad.TransformPoint(new Vector3(uv.x - 0.5f, uv.y - 0.5f, 0f));
    }

    IEnumerator Touch(string id, float glide = 0.42f, float after = 0.25f)
    {
        yield return Until(() => bot.Ids().Contains(id), 60f, "버튼 " + id + ", 화면 " + bot.Screen);
        if (id != "ad_close" && bot.Ids().Contains("ad_close")) yield return Touch("ad_close");
        Vector3 at = ButtonWorld(id);
        yield return Aim(() => at, glide);
        HandRig.I.Tap();
        Assert.IsTrue(bot.Press(id), "누름 실패 " + id);
        yield return Wait(after);
    }

    static Vector3 SlotPos(string id) =>
        Object.FindObjectsByType<CardSlot>(FindObjectsSortMode.None).First(s => s.id == id).transform.position;

    // ---- 본편 ----

    [UnityTest, Explicit, Timeout(3000000)]
    public IEnumerator Record()
    {
        if (Directory.Exists(FrameDir)) Directory.Delete(FrameDir, true);
        Directory.CreateDirectory(FrameDir);
        File.WriteAllText(Path.Combine(Root, "marks.txt"), "");

        TakeOverInput();
        var go = new GameObject("VideoTaker");
        Object.DontDestroyOnLoad(go);
        rec = go.AddComponent<FrameTaker>();
        Time.captureFramerate = Fps;

        // 현관: 메모
        GameState.I.JumpChapter(0);
        yield return Until(() => Active == GameState.I.flow.chapters[0].sceneName, 120f, "현관");
        yield return Visible();
        Mark("현관 메모");
        rec.stride = 1;
        yield return Unfrozen("현관 시작");
        yield return Wait(2.2f);
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Wait(0.9f);

        // 신발은 건너뛰고 문
        rec.stride = 0;
        yield return Use("신발 신기", 30f);
        yield return Until(() => Find("문 열기") != null, 60f, "문 열기 준비");
        yield return Unfrozen("신발 끝");
        yield return P.LookAt(Find("문 열기").transform.position, 0.2f);
        yield return Wait(0.2f);
        Mark("현관 문");
        rec.stride = 1;
        yield return Wait(0.35f);
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Black();
        rec.stride = 0;

        // 골목
        yield return SceneIs("Street");
        yield return Visible();
        Mark("골목");
        rec.stride = 1;
        yield return Unfrozen("골목 시작");
        rec.stride = 2;
        yield return Walk(P.transform.position + P.transform.forward * 6f, 0.05f);
        rec.stride = 0;

        // 정류장: 맨눈으로는 안 보이는 전광판
        var street = Object.FindAnyObjectByType<StreetDirector>();
        Vector3 bis = GameObject.Find("BisLook").transform.position;
        Vector3 stand = new Vector3(23.6f, 0f, 33.4f);
        yield return Face(stand, bis);
        Mark("전광판 맨눈");
        rec.stride = 1;
        yield return Wait(2.4f);
        rec.stride = 0;

        // 물어보기와 첫 버스는 건너뜀
        Time.timeScale = 3f;
        yield return Use("말 걸기", 120f);
        yield return Unfrozen("학생 대화");
        yield return Use("말 걸기", 120f);
        yield return Unfrozen("행인 대화");
        var rowsAfter = F<GameObject[]>(street, "rowsAfter");
        yield return Until(() => rowsAfter[0].activeSelf, 180f, "첫 버스 떠남");
        Time.timeScale = 1f;

        // 돋보기로 전광판
        yield return Face(stand, bis);
        Mark("전광판 돋보기");
        rec.stride = 1;
        yield return Wait(0.7f);
        yield return Key(UnityEngine.InputSystem.Key.Digit2);
        yield return Wait(0.9f);
        yield return P.LookAt(bis + Vector3.up * 0.1f + Vector3.forward * 0.2f, 0.9f);
        yield return Wait(0.8f);
        yield return P.LookAt(bis + Vector3.back * 0.2f, 0.9f);
        yield return Wait(0.4f);
        yield return Key(UnityEngine.InputSystem.Key.Digit2);
        yield return Wait(0.3f);
        rec.stride = 0;

        // 112번 도착과 승차
        Time.timeScale = 3f;
        var bus2 = F<BusMover>(street, "bus2");
        yield return Until(() => bus2.gameObject.activeSelf, 120f, "둘째 버스");
        Time.timeScale = 1f;
        yield return Face(new Vector3(34.6f, 0f, 33.7f), new Vector3(18f, 1.8f, 37f));
        Mark("버스 도착");
        rec.stride = 6;
        yield return Until(() => Find("버스 타기") != null, 120f, "버스 타기");
        rec.stride = 1;
        yield return P.LookAt(Find("버스 타기").transform.position, 0.6f);
        yield return Wait(0.5f);
        yield return Key(UnityEngine.InputSystem.Key.E);
        rec.stride = 2;
        yield return Black();
        rec.stride = 0;

        // 버스 안
        yield return SceneIs("Bus");
        yield return Visible();
        Mark("버스 안");
        rec.stride = 1;
        yield return Unfrozen("버스 안");
        yield return P.TurnTo(P.Yaw + 40f, -4f, 1.2f);
        rec.stride = 0;
        yield return Until(() => Subs != "", 60f, "안내방송");
        rec.stride = 1;
        yield return P.TurnTo(P.Yaw - 40f, 2f, 1.4f);
        yield return Wait(0.9f);
        rec.stride = 0;

        // 매장 앞
        yield return SceneIs("Storefront");
        var front = Object.FindAnyObjectByType<StorefrontDirector>();
        yield return Visible();
        Mark("매장 앞");
        rec.stride = 3;
        yield return Unfrozen("매장 앞 시작");
        yield return Approach("밀기", 1.15f);
        rec.stride = 1;
        yield return Wait(0.3f);

        // 밀기 덜컥
        Mark("밀기");
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Until(() => !F<bool>(front, "pushing"), 60f, "밀기 1");
        yield return Wait(0.2f);
        rec.stride = 0;
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Until(() => !F<bool>(front, "pushing"), 60f, "밀기 2");
        rec.stride = 1;
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Until(() => Find("당기기") != null, 60f, "당기기 준비");
        yield return Until(() => !F<bool>(front, "pushing"), 60f, "밀기 3");
        yield return Wait(0.4f);

        // 당겨서 입장. 끊지 않고 이어 찍는다
        Mark("당기기");
        yield return Key(UnityEngine.InputSystem.Key.R);
        yield return Until(() => Active == "Store", 120f, "입장");
        yield return Wait(0.4f);
        rec.stride = 2;
        yield return Unfrozen("입장 대사");

        // 키오스크로
        Mark("키오스크로");
        bot = Object.FindAnyObjectByType<KioskBot>();
        nunchi = Object.FindAnyObjectByType<NunchiSystem>();
        kiosk = Object.FindAnyObjectByType<KioskController>();
        quad = F<Transform>(kiosk, "screenQuad");
        rec.stride = 3;
        yield return Approach("주문하기", 1.3f);
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Until(() => bot.Active && !bot.Busy && bot.Ids().Contains("start"), 60f, "키오스크 진입");

        // 주문 몇 단계
        Mark("주문");
        rec.stride = 1;
        yield return Wait(0.7f);
        yield return Touch("start");
        yield return Touch("takeout");
        yield return Touch("skip");
        yield return Touch("tab_CLASSIC");

        // 돋보기
        Mark("키오스크 돋보기");
        yield return Key(UnityEngine.InputSystem.Key.Digit2);
        Vector3 item = ButtonWorld("item_bulgogi");
        yield return Aim(() => item, 0.7f);
        yield return Wait(1.1f);
        yield return Key(UnityEngine.InputSystem.Key.Digit2);
        yield return Touch("item_bulgogi");
        yield return Touch("opt_combo");
        rec.stride = 0;

        // 뒤돌아 사과
        bot.SetNunchi(62f);
        yield return Wait(0.4f);
        Mark("사과");
        rec.stride = 1;
        yield return Key(UnityEngine.InputSystem.Key.S);
        yield return Until(() => nunchi.LookingBack, 10f, "뒤보기");
        yield return Wait(1f);
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Wait(1.7f);
        yield return Key(UnityEngine.InputSystem.Key.D);
        yield return Wait(0.4f);
        rec.stride = 0;

        yield return PressAll("next", "drink_cider", "next", "up_no", "checkout", "pay_card");
        yield return Until(() => bot.Screen == "card", 30f, "카드 화면");
        yield return Wait(0.3f);

        // 카드 틈
        Mark("카드");
        rec.stride = 1;
        yield return Key(UnityEngine.InputSystem.Key.Digit3);
        yield return Wait(0.3f);
        yield return Key(UnityEngine.InputSystem.Key.W);
        yield return Wait(0.8f);
        Vector3 cover = Object.FindAnyObjectByType<PosterFlap>().transform.position;
        yield return Aim(() => cover, 0.5f);
        HandRig.I.Tap();
        bot.LiftPoster();
        yield return Wait(0.5f);
        Vector3 ic = SlotPos("ic");
        yield return Aim(() => ic, 0.5f);
        HandRig.I.Tap();
        bot.Slot("ic");                                       // 처음은 칩 방향 거부
        yield return Wait(1f);
        HandRig.I.Tap();
        bot.Slot("ic");
        rec.stride = 5;
        yield return Until(() => bot.Screen == "cardout", 60f, "결제 진행");
        rec.stride = 1;
        yield return Wait(0.4f);
        bot.Slot("ic");
        yield return Until(() => bot.Screen == "done", 60f, "카드 회수");

        // 영수증
        Mark("영수증");
        Vector3 paper = SlotPos("receipt") + Vector3.down * 0.08f;
        rec.stride = 2;
        yield return Aim(() => paper, 0.6f);
        yield return Until(() => bot.CanTear, 60f, "영수증 인쇄");
        rec.stride = 1;
        yield return Wait(0.3f);
        HandRig.I.Tap();
        yield return Until(() => bot.TakeReceipt(), 30f, "영수증 뜯기");
        yield return Until(() => !bot.Active, 30f, "키오스크 끝");
        yield return Wait(1.3f);
        rec.stride = 0;

        // 번호 기다림은 건너뜀
        yield return Key(UnityEngine.InputSystem.Key.Digit4);
        var store = Object.FindAnyObjectByType<StoreDirector>();
        Vector3 take = F<Interactable>(store, "takeBag").transform.position;
        Vector3 back = new Vector3(2.3f, 0f, 3.1f).normalized;
        yield return Face(take + back * 3.2f, take);
        Time.timeScale = 3f;
        yield return Until(() => Find("받기") != null, 180f, "번호 호출");
        Time.timeScale = 1f;

        // 픽업
        Mark("픽업");
        rec.stride = 1;
        yield return Wait(1f);
        rec.stride = 2;
        yield return Approach("받기", 1.25f);
        rec.stride = 1;
        yield return Wait(0.3f);
        yield return Key(UnityEngine.InputSystem.Key.E);
        yield return Wait(2.2f);
        rec.stride = 0;
        yield return Until(() => Subs.Contains("이거 하나"), 60f, "끝 대사");
        rec.stride = 1;
        yield return Until(() => Subs == "", 60f, "끝 대사 끝");
        rec.stride = 3;
        yield return Black();
        rec.stride = 0;

        // 결과
        yield return Until(() => P.CurrentMode == PlayerController.Mode.Locked, 60f, "결과 화면");
        Mark("결과");
        rec.stride = 1;
        yield return Wait(4.2f);
        rec.stride = 0;
        Mark("끝");

        AssertMemoOrder();
        Assert.Greater(rec.Saved, 1000, "프레임 수");
    }
}

#endif
