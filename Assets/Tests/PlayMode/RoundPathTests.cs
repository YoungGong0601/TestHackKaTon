// 경로 시험: 전체 완주(버거집 앞부터 결과까지), 게이지 복귀, 지폐 3번 뒤 뒷사람 결제, 시간 초과, 가는 길 버스, 시연자 키, 반응 없는 상호작용.
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
    const int R1Store = 1, R2 = 2, R4Home = 3, R4Stop = 4, R4Front = 5, R4Store = 6;

    [UnityTest, Timeout(Limit)]
    public IEnumerator FullRun()
    {
        SteadyHands();
        CalmLine();
        Time.timeScale = Fast;
        yield return PlayR1Storefront();
        yield return PlayR1Store();
        yield return PlayR2();
        yield return PlayR4Home();
        yield return PlayR4Stop();
        yield return PlayR4Storefront();
        yield return EnterKiosk();
        yield return R4ToPay();
        yield return Bounce(1);
        yield return R4Finish();
        yield return PlayResult();

        AssertSaw("왜 안 되지?", "어서 오세요!", "274번 고객님, 주문하신 메뉴 나왔습니다.", "이건 또 뭐야.", "왜 기계가 돈을 안먹지? 이상하네", "아 이보시게 잠시만요!");
        AssertNotSaw("일단 현금은 안된다네요.", "하... 걸어가야겠구만.", "현금은 어디에 넣어요?");
        AssertCleanText();
    }

    // ---- 촬영. 평소 시험에서는 돌지 않는다 ----

    class Shooter : MonoBehaviour
    {
        readonly System.Collections.Generic.HashSet<string> done = new();
        bool busy;

        void Update()
        {
            if (busy || Game == null || Pc == null) return;
            string c = "c" + Game.chapterIndex + "-" + Scene;
            var k = Object.FindAnyObjectByType<KioskController>();
            string want = !Pc.Frozen && Pc.CurrentMode == PlayerController.Mode.Fps ? c + "-start"
                : k != null && k.Active && k.Screen != "" ? c + "-" + k.Screen : null;
            if (want != null && done.Add(want)) StartCoroutine(Take(want));
        }

        System.Collections.IEnumerator Take(string name)
        {
            busy = true;
            float end = Time.realtimeSinceStartup + 0.5f;
            while (Time.realtimeSinceStartup < end) yield return null;
            yield return Shot(name);
            busy = false;
        }
    }

    [UnityTest, Explicit, Timeout(Limit)]
    public IEnumerator Capture()
    {
        SteadyHands();
        rec.gameObject.AddComponent<Shooter>();
        Time.timeScale = 2f;
        yield return PlayR1Storefront();
        yield return PlayR1Store();
        yield return PlayR2();
        yield return PlayR4Home();
        yield return PlayR4Stop();
        yield return PlayR4Storefront();
        yield return EnterKiosk();
        yield return R4ToPay();
        yield return Bounce(1);
        yield return R4Finish();
        var group = Field<CanvasGroup>(RoundUi.I, "endGroup");
        yield return Until(() => group.gameObject.activeSelf, 120f, "엔딩");
        yield return Until(() => rec.Saw(Ending.Stat), 20f, "엔딩 문구");
        yield return Real(0.3f);
        yield return Shot("end-stat");
        yield return Until(() => rec.Saw(Ending.Title), 20f, "엔딩 제목");
        yield return Real(0.3f);
        yield return Shot("end-title");
    }

    // ---- 1회차 신메뉴 ----

    /// <summary>뽑기는 첫 칸 불고기와 겹치지 않고, 씬을 건너도 그대로이며, 쪽지가 따라간다.</summary>
    [UnityTest, Timeout(Limit)]
    public IEnumerator R1_RandomMenu_Stays()
    {
        for (int seed = 0; seed < 20; seed++)
        {
            KioskPick.Reseed(seed);
            Assert.AreNotEqual("crown3", KioskPick.Id, "첫 칸은 불고기 자리");
            Assert.AreNotEqual("bulgogi", KioskPick.Id);
        }
        KioskPick.Reseed(7);
        string name = KioskPick.SetName;
        yield return Chapter(1);
        Assert.AreEqual(name, KioskPick.SetName, "씬을 건너도 유지");
        yield return Chapter(0);
        Assert.AreEqual(name, KioskPick.SetName, "처음 복귀에도 유지");
        StringAssert.Contains(name, KioskPick.NoteText);
    }

    // ---- 1-8 카드: 포인터와 좌클릭만으로 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R1_KioskCard_HumanClick()
    {
        yield return Chapter(R1Store);
        Time.timeScale = Fast;
        yield return Until(() => rec.Saw("아이고, 고맙구먼."), 90f, "어르신 대리 결제");
        yield return R1Kiosk();
        yield return Free(30f);
        Assert.AreEqual(274, Game.Order.number);
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R1_Whole()
    {
        Time.timeScale = Fast;
        yield return PlayR1Storefront();
        yield return PlayR1Store();
        AssertSaw("왜 안 되지?", "어서 오세요!", "274번 고객님, 주문하신 메뉴 나왔습니다.");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_Storefront_Door()
    {
        SteadyHands();
        yield return Chapter(R4Front);
        Time.timeScale = Fast;
        yield return PlayR4Storefront();
    }

    // ---- 4회차 버거집 실패 ----

    /// <summary>게이지가 다 차면 선택지 없이 줄 맨 뒤로 갔다가 다시 시도한다. 횟수 제한 없음, 나가는 길은 4-10a뿐.</summary>
    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_GaugeFull_Requeue()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        for (int round = 0; round < 2; round++)
        {
            yield return Screen("idle");
            yield return Touch("start");
            yield return Screen("place");
            yield return Chord(Key.F6);
            yield return Real(0.1f);
            Assert.IsFalse(RoundUi.I.ChoiceOpen, "선택지가 뜸");
            Assert.IsFalse(RoundUi.I.GiveUpShown, "버튼이 뜸");
            yield return Until(() => !Kiosk.Active, 10f, "키오스크에서 비켜남");
            Assert.AreEqual(R4Store, Game.chapterIndex, "가게를 나가지 않음");
            yield return Until(() => Kiosk.Active && !Kiosk.Busy, 60f, "차례가 다시 옴");
            Assert.Greater(Kiosk.Nunchi.Value, 40f, "게이지 절반쯤");
            Assert.Less(Kiosk.Nunchi.Value, 70f, "게이지 절반쯤");
        }
        yield return Real(0.5f);
        yield return R4ToPay();
        yield return Bounce(1);
        yield return R4Finish();
    }

    // ---- 2회차 줄 맨 뒤 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R2_GaugeFull_Requeue()
    {
        yield return Chapter(R2);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Screen("menu");
        yield return Chord(Key.F6);
        yield return Until(() => !Kiosk.Active, 10f, "키오스크에서 비켜남");
        Assert.IsFalse(RoundUi.I.ChoiceOpen, "선택지가 뜸");
        yield return Until(() => Kiosk.Active && !Kiosk.Busy, 90f, "차례가 다시 옴");
        yield return Real(0.5f);
        yield return Touch("item_americano");
        Assert.IsTrue(Kiosk.Active);
    }

    // ---- 4회차 지폐 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_CashBounce1()
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
        yield return Tap(Key.W);
        yield return Tap(ItemKey(ItemId.Wallet));
        Assert.IsFalse(Wallet.I.Open, "지갑 닫기");

        yield return R4ToPay();
        Assert.IsFalse(RoundUi.I.GiveUpShown, "결제 창에서는 버튼 없음");
        yield return Bounce(1);
        Assert.AreEqual("카드 전용", K.cardMsg, "튕김 안내");
        yield return Until(() => !Kiosk.Active, 40f, "대화 뒤 비켜섬");
        AssertSaw("왜 기계가 돈을 안먹지? 이상하네");
        yield return R4Finish();
        yield return PlayResult();
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_EmptyHandNoPay()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Assert.IsFalse(Game.Profile.Has(ItemId.Card), "4회차 지갑은 현금만");
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return R4ToPay();
        // 빈손으로 틈을 눌러도 결제되지 않는다
        yield return ClickPay();
        Assert.AreEqual("card", Kiosk.Screen);
        Assert.AreEqual("카드 전용", K.cardMsg);
        Assert.IsTrue(Kiosk.Active);
    }

    // ---- 4회차 시간 초과 ----

    protected IEnumerator ToMenu()
    {
        yield return Touch("start");
        yield return Screen("place");
        yield return Touch("takeout");
        yield return Screen("member");
        yield return Touch("skip");
        yield return Screen("menu");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_Timeout()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        yield return EnterKiosk();
        yield return ToMenu();
        yield return Touch("tab_SIDE");
        yield return Touch("item_nugget");
        Assert.AreEqual(1, K.cart.Count, "담김");
        var timer = Field<KioskFields>(Field<KioskScreens>(Kiosk, "screens"), "timer");
        yield return Real(0.2f);
        Assert.IsTrue(timer.gameObject.activeInHierarchy, "남은 시간 표시");

        Time.timeScale = 8f;
        yield return Until(() => Kiosk.Screen == "idle", 12f, "40초 뒤 처음 화면");
        Time.timeScale = 1f;
        yield return Real(0.1f);
        AssertSaw("시간이 초과되어 처음 화면으로 돌아갑니다.");
        Assert.AreEqual(0, K.cart.Count, "장바구니 비움");
        Assert.Greater(Kiosk.Nunchi.Value, 0f, "게이지 유지");
        Assert.IsTrue(Kiosk.Active, "키오스크 유지");

        yield return Touch("start");
        yield return Screen("place");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_LastPopupGoesHome()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return ToMenu();
        yield return Touch("tab_SIDE");
        yield return Touch("item_nugget");
        yield return Touch("cart");
        yield return Screen("cart");
        yield return Touch("checkout");
        yield return Touch("info_close");
        yield return Touch("info_close");
        yield return Until(() => K.info != null && K.info.title == "포인트 적립", 5f, "마지막 팝업");
        yield return Touch("info_close");
        yield return Screen("idle");
        yield return Real(0.1f);
        AssertSaw("처음 화면으로 돌아갑니다.");
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_BigText()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        yield return EnterKiosk();
        yield return Touch("start");
        yield return Screen("place");
        yield return Touch("access");
        var pack = (R4ProtoPack)Kiosk.Pack;
        Assert.IsTrue(pack.Big, "큰 글씨");
        yield return Touch("access");
        Assert.IsFalse(pack.Big, "되돌림");
    }

    // ---- 도움 없음: 알바생과 터치 확률 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_StaffDoesNotHelp()
    {
        SteadyHands();
        yield return Chapter(R4Store);
        Time.timeScale = Fast;
        var staff = Field<Interactable>(Object.FindAnyObjectByType<R4StoreDirector>(), "talkStaff");
        yield return Until(() => staff.active && !Pc.Frozen, 30f, "알바생");
        yield return Use(staff);
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
        Assert.AreEqual("place", Kiosk.Screen, "알바생이 화면을 바꾸지 않음");
    }

    /// <summary>재량 값 그대로(터치 실패, 옆 버튼, 떨림)로 카드 화면까지 갈 수 있는가.</summary>
    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_RealTouchNoise_ReachesPay()
    {
        yield return Chapter(R4Store);
        Time.timeScale = 2f;
        yield return EnterKiosk();
        float end = Time.realtimeSinceStartup + 170f;
        while (Kiosk.Screen != "card")
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail("카드 화면까지 못 감, 화면 " + Kiosk.Screen);
            if (!Kiosk.Active || Kiosk.Busy) { yield return null; continue; }
            var k = K;
            string id = k.info != null ? (PackScreens.Find("pop_skip") ? "pop_skip" : "info_close") : Kiosk.Screen switch
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
            if (id == null || !PackScreens.Find(id)) { yield return null; continue; }
            yield return Touch(id);
            yield return Real(0.1f);
        }
    }

    // ---- 버스 ----

    [UnityTest, Timeout(Limit)]
    public IEnumerator R4_Home_To_Storefront()
    {
        SteadyHands();
        yield return Chapter(R4Home);
        Time.timeScale = Fast;
        yield return PlayR4Home();
        yield return PlayR4Stop();
        AssertNotSaw("벌써 이렇게 됐구먼.", "현금밖에 없는데요.", "저희는 카드밖에 받지 않습니다.");
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
        for (int i = 6; i >= 1; i -= 3)
        {
            yield return Chord(Key.Digit1 + i);
            yield return InChapter(i);
        }

        // 처음으로. 회차 안, 키오스크 안, 엔딩에서
        yield return Chord(Key.Digit3);
        yield return InChapter(R2);
        yield return EnterKiosk();
        yield return Chord(Key.Home);
        yield return InChapter(0);
        yield return Real(1f);
        Assert.AreEqual(PlayerController.Mode.Fps, Pc.CurrentMode, "처음으로 뒤 모드");

        yield return Chord(Key.Digit5);
        yield return InChapter(R4Stop);
        yield return Chord(Key.Home);
        yield return InChapter(0);
        yield return Until(() => !Pc.Frozen, 20f, "처음 조작");

        // 결과 안에서 처음으로
        yield return Chord(Key.Digit7);
        yield return InChapter(R4Store);
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
