// 시트 경로 시험: 전체 완주, 3회차와 4회차 실패 선택지, 지폐 3번 튕김, 시간 초과, 버스 3대, 시연자 키, 반응 없는 상호작용.
using System.Collections;
using System.Linq;
using System.Reflection;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.InputSystem;
using UnityEngine.TestTools;

public class RoundPathTests : RoundFixture
{
    const int R3 = 4, R4Front = 5, R4Store = 6, R4Stop = 7;

    [UnityTest, Timeout(Limit)]
    public IEnumerator FullRun()
    {
        SteadyHands();
        Time.timeScale = Fast;
        yield return PlayR1Stop();
        yield return PlayR1Storefront();
        yield return PlayR1Store();
        yield return PlayR2();
        yield return PlayR3();
        yield return PlayR4Storefront();
        yield return EnterKiosk();
        yield return R4ToPay();
        yield return Bounce(3);
        yield return R4Leave();
        yield return PlayR4Stop();
        yield return PlayEnding();

        AssertSaw("112번 버스를 타고 버거집에 가세요.", "112번 버스를 타세요.", "왜 안 되지?", "그거 지폐 안 받아요.", "그려? 어쩔 수 없구만...",
            "어서 오세요!", "274번 고객님, 주문하신 메뉴 나왔습니다.", "아메리카노를 주문하세요.", "영화표를 사세요.",
            "이건 또 뭐야.", "돈을 어디다 넣으라는 거야.", "117번이요.", "아이고, 아니구먼.", "벌써 이렇게 됐구먼.", "172번이요.");
        Assert.AreEqual(new[] { 2, 4, 6 }, rec.Hours.ToArray(), "손목시계 바늘");
        AssertCleanText();
    }

    // ---- 1-8 카드: 포인터와 좌클릭만으로 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R1_KioskCard_HumanClick()
    {
        yield return Chapter(2);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Screen("menu");
        yield return Touch("burger");
        yield return Screen("pay");
        Time.timeScale = 1f;
        Assert.AreEqual(ItemId.Card, HandRig.I.Held, "결제 창에서 카드를 듦");
        yield return ClickPay();
        yield return Screen("done", 3f);
        Time.timeScale = Fast;
        yield return Free(30f);
        Assert.AreEqual(274, Game.Order.number);
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R1_Whole()
    {
        Time.timeScale = Fast;
        yield return PlayR1Stop();
        yield return PlayR1Storefront();
        yield return PlayR1Store();
        AssertSaw("112번 버스를 타고 버거집에 가세요.", "112번 버스를 타세요.", "왜 안 되지?", "그거 지폐 안 받아요.", "그려? 어쩔 수 없구만...",
            "어서 오세요!", "274번 고객님, 주문하신 메뉴 나왔습니다.");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_Storefront_Note_Door()
    {
        SteadyHands();
        yield return Chapter(R4Front);
        Time.timeScale = Fast;
        yield return PlayR4Storefront();
    }

    // ---- 3회차 실패 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R3_GiveUp_Leave()
    {
        SteadyHands();
        yield return Chapter(R3);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Screen("movie");
        yield return Chord(Key.F6);
        yield return PressGiveUp();
        yield return Pick("다음에 볼게요");
        yield return InChapter(R4Front, 40f);
        Assert.IsFalse(RoundUi.I.GiveUpShown, "버튼이 다음 챕터에 남음");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R3_GiveUp_Stay()
    {
        SteadyHands();
        yield return Chapter(R3);
        Time.timeScale = Fast;
        yield return R3ToSms();
        var nunchi = Kiosk.Nunchi;
        yield return Chord(Key.F6);
        yield return PressGiveUp();
        yield return Pick("조금만요");
        Assert.Less(nunchi.Value, 60f, "조금만요 뒤 게이지");
        Assert.IsTrue(Kiosk.Active, "조금만요 뒤 키오스크");
        Assert.AreEqual("sms", Kiosk.Screen, "화면 유지");
        yield return R3Finish();
        yield return InChapter(R4Front, 40f);
    }

    // ---- 4회차 버거집 실패 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_GiveUp_Leave()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Screen("idle");
        yield return Touch("start");
        yield return Chord(Key.F6);
        yield return PressGiveUp();
        yield return Pick("먼저 하세요");
        yield return Until(() => !Kiosk.Active, 20f, "키오스크 떠남");
        yield return R4Leave();
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_GiveUp_Stay()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Screen("idle");
        yield return Touch("start");
        yield return Screen("menu");
        var nunchi = Kiosk.Nunchi;
        yield return Chord(Key.F6);
        yield return PressGiveUp();
        yield return Pick("조금만요");
        Assert.Less(nunchi.Value, 60f, "조금만요 뒤 게이지");
        Assert.AreEqual("menu", Kiosk.Screen);
        yield return Real(0.3f);
        Assert.IsFalse(RoundUi.I.GiveUpShown, "버튼 사라짐");

        // 다시 100이면 다시 뜬다
        yield return Chord(Key.F6);
        yield return Until(() => RoundUi.I.GiveUpShown, 3f, "다시 버튼");
        Assert.IsTrue(Kiosk.Active);
    }

    // ---- 4회차 지폐 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_CashBounce3()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();

        // 결제 창 밖에서는 세지 않는다
        yield return WalletTake("cashPart", ItemId.Cash);
        yield return ClickPay();
        yield return ClickPay();
        yield return ClickPay();
        Assert.IsTrue(Kiosk.Active, "결제 창 밖 지폐로 끝남");
        yield return Tap(Key.Digit3);
        Assert.IsFalse(Wallet.I.Open, "지갑 닫기");

        yield return R4ToPay();
        Assert.IsFalse(RoundUi.I.GiveUpShown, "결제 창에서는 버튼 없음");
        yield return Bounce(2);
        Assert.IsTrue(Kiosk.Active && !Kiosk.Busy, "두 번까지는 남음");
        var pay = PackScreens.Get("pay");
        yield return ClickPay();
        yield return Until(() => !Kiosk.Active, 20f, "세 번째에 떠남");
        yield return Until(() => rec.Saw("그거 지폐 안 받아요."), 15f, "뒷사람 말");
        yield return Until(() => rec.Saw("그려? 어쩔 수 없구만..."), 15f, "캐릭터 대답");
        AssertSaw("돈을 어디다 넣으라는 거야.");
        yield return R4Leave();
    }

    // ---- 4회차 시간 초과 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_Timeout()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        yield return EnterKiosk();
        yield return Touch("start");
        yield return Touch("list");
        yield return Touch("item_0");
        Assert.AreEqual(1, Field<System.Collections.Generic.List<int>>(Kiosk.Pack, "cart").Count, "담김");

        Time.timeScale = 8f;
        yield return Until(() => Kiosk.Screen == "idle", 12f, "40초 뒤 처음 화면");
        Time.timeScale = 1f;
        yield return Real(0.1f);
        AssertSaw("시간이 초과되어 처음 화면으로 돌아갑니다.");
        Assert.AreEqual(0, Field<System.Collections.Generic.List<int>>(Kiosk.Pack, "cart").Count, "장바구니 비움");
        Assert.Greater(Kiosk.Nunchi.Value, 0f, "게이지 유지");
        Assert.IsTrue(Kiosk.Active, "키오스크 유지");

        // 처음 화면에서는 시간이 안 흐르고 다시 시작할 수 있다
        yield return Touch("start");
        yield return Screen("menu");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_LastPopupGoesHome()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Touch("start");
        yield return Touch("list");
        yield return Touch("item_0");
        yield return Touch("next");
        yield return Touch("x");
        yield return Touch("check");
        yield return Touch("x");
        yield return Touch("x");
        yield return Screen("pop_point");
        yield return Touch("x");
        yield return Screen("idle");
        AssertSaw("처음 화면으로 돌아갑니다.");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_BigText_PushesNextAway()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Touch("start");
        yield return Screen("menu");
        var content = Field<RectTransform>(Kiosk.Pack, "content");
        Assert.IsNotNull(content, "내용 루트 없음");
        Vector2 before = PackScreens.Uv(PackScreens.Find("next"));
        yield return Touch("big");
        Assert.Greater(content.localScale.x, 1.2f, "큰 글씨");
        Vector2 after = PackScreens.Uv(PackScreens.Find("next"));
        Assert.IsTrue(after.x > 1f || after.x < 0f || after.y > 1f || after.y < 0f, $"다음 버튼이 화면 안 {before} {after}");
        yield return Touch("big");
        Assert.AreEqual(1f, content.localScale.x, 0.001f, "되돌림");
    }

    // ---- 도움 없음: 알바생과 터치 확률 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_StaffDoesNotHelp()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return Use("말 걸기", 30f);
        yield return Until(() => rec.Saw("주문은 키오스크에서 해주세요."), 15f, "알바생 답");
        yield return EnterKiosk();
        yield return Touch("start");
        yield return Tap(Key.A);
        Assert.AreEqual("staff", Kiosk.View);
        yield return Real(0.4f);
        yield return Tap(Key.E);
        yield return Real(1f);
        yield return Tap(Key.D);
        Assert.AreEqual("kiosk", Kiosk.View);
        Assert.AreEqual("menu", Kiosk.Screen, "알바생이 화면을 바꾸지 않음");
        var pack = Kiosk.Pack.GetType();
        Assert.IsFalse(pack.GetMethods(BindingFlags.Public | BindingFlags.Instance).Any(m => m.Name == "Hint"), "4회차에 도움 경로");
    }

    /// <summary>시트 재량 값 그대로(터치 실패, 옆 버튼, 떨림)로 결제 창까지 갈 수 있는가.</summary>
    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_RealTouchNoise_ReachesPay()
    {
        yield return Chapter(R4Store);
        Time.timeScale = 2f;
        yield return EnterKiosk();
        float end = Time.realtimeSinceStartup + 150f;
        while (Kiosk.Screen != "pay")
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail("결제 창까지 못 감, 화면 " + Kiosk.Screen);
            if (RoundUi.I.GiveUpShown) { yield return PressGiveUp(); yield return Pick("조금만요"); continue; }
            string now = Kiosk.Screen;
            var cart = Field<System.Collections.Generic.List<int>>(Kiosk.Pack, "cart");
            string id = now switch
            {
                "idle" => "start",
                "menu" => cart.Count > 0 ? "next" : PackScreens.Find("item_0") ? "item_0" : "list",
                "pop_code" or "pop_app" => "x",
                "pop_robot" => Field<bool>(Kiosk.Pack, "robot") ? "x" : "check",
                "pop_point" => "skip",
                _ => null,
            };
            if (id == null || !PackScreens.Find(id)) { yield return null; continue; }
            yield return Touch(id);
            yield return Real(0.1f);
        }
    }

    // ---- 버스 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_Bus3()
    {
        SteadyHands();
        yield return Chapter(R4Stop);
        Time.timeScale = Fast;
        var d = Object.FindAnyObjectByType<R4StopDirector>();
        var sun = Field<Light>(d, "sun");
        float noon = sun.intensity;
        yield return PlayR4Stop();
        yield return PlayEnding();
        Assert.AreEqual(new[] { 2, 4, 6 }, rec.Hours.ToArray(), "손목시계 바늘");
        AssertSaw("117번이요.", "172번이요.", "112번이요.", "아이고, 아니구먼.", "벌써 이렇게 됐구먼.");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_Bus_DuskAndLamps()
    {
        SteadyHands();
        yield return Chapter(R4Stop);
        Time.timeScale = Fast;
        var d = Object.FindAnyObjectByType<R4StopDirector>();
        var sun = Field<Light>(d, "sun");
        var lamps = Field<GameObject[]>(d, "lamps");
        float noon = sun.intensity;
        Assert.IsFalse(lamps.Any(l => l.activeSelf), "낮에 가로등");
        yield return PlayR4Stop();
        yield return Until(() => lamps.All(l => l.activeSelf), 60f, "가로등 켜짐");
        yield return Real(1.5f);
        Assert.Less(sun.intensity, noon * 0.5f, "해 질 녘");
    }

    // ---- 시연자 키 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator DemoKeys()
    {
        yield return Real(0.5f);

        // 단독 키는 듣지 않는다
        yield return Tap(Key.F2);
        yield return Tap(Key.Home);
        yield return Real(1.2f);
        Assert.AreEqual(0, Game.chapterIndex, "단독 F2");

        var debug = Field<Component>(Hud.I, "debugText");
        bool was = debug.gameObject.activeSelf;
        yield return Chord(Key.F1);
        Assert.AreNotEqual(was, debug.gameObject.activeSelf, "F1 디버그");
        yield return Chord(Key.F1);

        yield return Chord(Key.F2);
        yield return InChapter(1);
        yield return Chord(Key.F3);
        yield return InChapter(0);
        for (int i = 7; i >= 1; i -= 3)
        {
            yield return Chord(Key.Digit1 + i);
            yield return InChapter(i);
        }

        // 처음으로. 회차 안, 키오스크 안, 엔딩에서
        yield return Chord(Key.Digit5);
        yield return InChapter(R3);
        yield return EnterKiosk();
        yield return Chord(Key.Home);
        yield return InChapter(0);
        yield return Real(1f);
        Assert.AreEqual(PlayerController.Mode.Fps, Pc.CurrentMode, "처음으로 뒤 모드");

        yield return Chord(Key.Digit8);
        yield return InChapter(R4Stop);
        yield return Chord(Key.Home);
        yield return InChapter(0);
        yield return Until(() => !Pc.Frozen, 20f, "처음 조작");

        // 엔딩 안에서 처음으로
        yield return Chord(Key.Digit8);
        yield return InChapter(R4Stop);
        yield return Real(2f);
        yield return Chord(Key.F2);
        var end = Field<CanvasGroup>(RoundUi.I, "endGroup");
        yield return Until(() => end.gameObject.activeSelf, 10f, "엔딩 시작");
        yield return Chord(Key.Home);
        yield return InChapter(0);
        Assert.IsFalse(end.gameObject.activeSelf, "처음으로 뒤 엔딩 화면이 남음");
        yield return Until(() => !Pc.Frozen, 20f, "엔딩 뒤 조작");
        Assert.AreEqual(PlayerController.Mode.Fps, Pc.CurrentMode, "엔딩 뒤 모드");
    }

    // ---- 반응 없는 입력 ----

    static int Listeners(UnityEventBase e)
    {
        var calls = typeof(UnityEventBase).GetField("m_Calls", BindingFlags.Instance | BindingFlags.NonPublic).GetValue(e);
        int runtime = (int)calls.GetType().GetProperty("Count", BindingFlags.Instance | BindingFlags.Public).GetValue(calls);
        return runtime + e.GetPersistentEventCount();
    }

    /// <summary>켜진 Interactable은 모두 듣는 쪽이 있어야 한다. 눌러도 아무 일 없는 물체를 찾는다.</summary>
    [UnityTest, Timeout(Limit)]
    public IEnumerator NoDeadInteractable()
    {
        var dead = new System.Collections.Generic.List<string>();
        for (int i = 0; i < Game.flow.chapters.Count; i++)
        {
            yield return Chapter(i);
            yield return Real(1f);
            foreach (var it in Object.FindObjectsByType<Interactable>(FindObjectsInactive.Include, FindObjectsSortMode.None))
                if (it.active && Listeners(it.onUse) == 0)
                    dead.Add($"{Scene}/{it.name}({it.label}, active {it.active})");
        }
        Assert.IsEmpty(dead, string.Join(" | ", dead));
    }
}
