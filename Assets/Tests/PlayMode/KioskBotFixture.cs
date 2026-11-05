// 네 경로 봇 시험의 공통 부분. Store 씬에서 시작해 게임이 쓰는 경로(Interactable.onUse, KioskBot, 키 입력)로만 진행한다.
using System;
using System.Collections;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

public abstract class KioskBotFixture
{
    protected KioskBot bot;
    protected NunchiSystem nunchi;

    float savedVolume;
    InputSettings.BackgroundBehavior savedBackground;
    InputSettings.EditorInputBehaviorInPlayMode savedEditorInput;

    protected static OrderData Order => GameState.I.Order;
    protected static RunStats Stats => GameState.I.Stats;

    [UnitySetUp]
    public IEnumerator SetUp()
    {
        savedVolume = AudioListener.volume;
        AudioListener.volume = 0f;
        Time.timeScale = 1f;
        Hud.SkipTitle = true;

        // 창에 초점이 없어도 시험 키 입력이 들어가게 한다
        savedBackground = InputSystem.settings.backgroundBehavior;
        savedEditorInput = InputSystem.settings.editorInputBehaviorInPlayMode;
        InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
        InputSystem.settings.editorInputBehaviorInPlayMode = InputSettings.EditorInputBehaviorInPlayMode.AllDeviceInputAlwaysGoesToGameView;

        yield return SceneManager.LoadSceneAsync("Store", LoadSceneMode.Single);
        yield return null;
        yield return null;

        bot = UnityEngine.Object.FindAnyObjectByType<KioskBot>();
        nunchi = UnityEngine.Object.FindAnyObjectByType<NunchiSystem>();
        Assert.IsNotNull(GameState.I, "GameState 없음");
        Assert.IsNotNull(bot, "KioskBot 없음");
        Assert.IsNotNull(nunchi, "NunchiSystem 없음");
        Assert.IsTrue(GameState.I.Profile.kioskNunchi, "프로필 눈치 꺼짐");
    }

    [UnityTearDown]
    public IEnumerator TearDown()
    {
        Time.timeScale = 1f;
        Hud.SkipTitle = false;
        AudioListener.volume = savedVolume;
        InputSystem.settings.backgroundBehavior = savedBackground;
        InputSystem.settings.editorInputBehaviorInPlayMode = savedEditorInput;

        // 씬을 먼저 내린다. Systems만 없애면 남은 씬의 Update가 없어진 참조를 건드린다
        var blank = SceneManager.CreateScene("TestBlank" + Time.frameCount);
        SceneManager.SetActiveScene(blank);
        for (int i = SceneManager.sceneCount - 1; i >= 0; i--)
        {
            var scene = SceneManager.GetSceneAt(i);
            if (scene != blank) yield return SceneManager.UnloadSceneAsync(scene);
        }

        // 다음 시험이 새 상태로 시작하도록 Systems를 없앤다
        if (GameState.I != null) UnityEngine.Object.Destroy(GameState.I.transform.root.gameObject);
        yield return null;
    }

    // ---- 기다리기 ----

    protected static IEnumerator Until(Func<bool> cond, float realSec, string what)
    {
        float end = Time.realtimeSinceStartup + realSec;
        while (!cond())
        {
            if (Time.realtimeSinceStartup > end) Assert.Fail("시간 초과: " + what);
            yield return null;
        }
    }

    static Interactable Usable(string label)
    {
        return UnityEngine.Object.FindObjectsByType<Interactable>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
            .FirstOrDefault(i => i.active && i.label == label);
    }

    /// <summary>플레이어를 물체 앞으로 옮기고 그 물체를 쓴다.</summary>
    protected static IEnumerator Use(string label, float realSec)
    {
        Interactable it = null;
        yield return Until(() => (it = Usable(label)) != null, realSec, "상호작용 " + label);
        var player = PlayerController.I;
        Vector3 from = player.transform.position - it.transform.position;
        from.y = 0f;
        Vector3 at = it.transform.position + from.normalized * Mathf.Min(1f, it.radius * 0.5f);
        at.y = player.transform.position.y;
        player.Teleport(at, Quaternion.LookRotation(-from).eulerAngles.y);
        yield return null;
        it.onUse.Invoke();
    }

    // ---- 키 입력 ----

    protected static IEnumerator Key(Key key)
    {
        var kb = Keyboard.current ?? InputSystem.AddDevice<Keyboard>();
        InputSystem.QueueStateEvent(kb, new KeyboardState(key));
        yield return null;
        yield return null;
        InputSystem.QueueStateEvent(kb, new KeyboardState());
        yield return null;
    }

    // ---- 키오스크 ----

    protected IEnumerator EnterKiosk()
    {
        yield return Use("주문하기", 40f);
        // 대기 화면은 진입 전에도 보인다. 걸어가서 Enter가 돌아야 진입이다
        yield return Until(() => bot.Active && !bot.Busy && bot.Ids().Contains("start"), 20f, "키오스크 진입");
        yield return new WaitForSeconds(0.2f);
    }

    protected IEnumerator Press(string id)
    {
        yield return Until(() => bot.Ids().Contains(id), 6f, "버튼 " + id + ", 화면 " + bot.Screen);
        if (id != "ad_close" && bot.Ids().Contains("ad_close"))
        {
            bot.Press("ad_close");
            yield return new WaitForSeconds(0.12f);
        }
        Assert.IsTrue(bot.Press(id), "누름 실패 " + id);
        yield return new WaitForSeconds(0.12f);
    }

    protected IEnumerator PressAll(params string[] ids)
    {
        foreach (string id in ids) yield return Press(id);
    }

    /// <summary>불고기 버거 세트, 사이다, 포장.</summary>
    protected IEnumerator OrderMemo()
    {
        yield return PressAll("start", "takeout", "skip", "tab_CLASSIC", "item_bulgogi", "opt_combo",
            "next", "drink_cider", "next", "up_no", "checkout", "pay_card");
    }

    protected IEnumerator PayWithCard()
    {
        HandRig.I.Equip(ItemId.Card);
        bot.LiftPoster();
        yield return new WaitForSeconds(0.2f);
        bot.Slot("ic");                                       // 처음은 칩 방향 거부
        yield return new WaitForSeconds(0.7f);
        bot.Slot("ic");
        yield return Until(() => bot.Screen == "cardout", 15f, "결제 진행");
        bot.Slot("ic");
        yield return Until(() => bot.Screen == "done", 10f, "카드 회수");
        yield return Until(() => bot.TakeReceipt(), 8f, "영수증 뜯기");
    }

    /// <summary>번호가 불리면 받고 마지막 챕터가 끝날 때까지.</summary>
    protected IEnumerator PickupAndFinish()
    {
        Time.timeScale = 6f;
        yield return Use("받기", 40f);
        yield return Until(() => PlayerController.I.CurrentMode == PlayerController.Mode.Locked, 30f, "받기 뒤 결과 화면");
        Time.timeScale = 1f;
    }

    protected static void AssertMemoOrder()
    {
        Assert.AreEqual("takeout", Order.place);
        Assert.AreEqual("bulgogi", Order.item);
        Assert.AreEqual("combo", Order.combo);
        Assert.AreEqual("fries_r", Order.side);
        Assert.AreEqual("cider", Order.drink);
        Assert.IsFalse(Order.sizeUp);
        Assert.IsTrue(Order.paid);
        Assert.AreEqual(274, Order.number);
    }
}
