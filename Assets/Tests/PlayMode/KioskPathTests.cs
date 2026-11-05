// 네 경로: 메모대로, 틀린 주문, 눈치 폭발 후 재개, 시간 초과.
using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.TestTools;

public class KioskPathTests : KioskBotFixture
{
    const int Limit = 300000;

    [UnityTest, Timeout(Limit)]
    public IEnumerator MemoOrder()
    {
        yield return EnterKiosk();
        yield return OrderMemo();
        yield return PayWithCard();
        AssertMemoOrder();
        yield return PickupAndFinish();
        AssertMemoOrder();
        Assert.AreEqual(0, Stats.wrong);
        Assert.AreEqual(0, Stats.blowups);
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator WrongOrder()
    {
        yield return EnterKiosk();
        yield return PressAll("start", "dine", "skip", "tab_CLASSIC", "item_mushroom", "opt_large",
            "next", "next", "up_yes", "checkout", "pay_card");

        HandRig.I.Equip(ItemId.Card);
        bot.Slot("barcode");
        yield return new WaitForSeconds(0.7f);
        bot.Slot("receipt");
        yield return new WaitForSeconds(0.7f);
        Assert.GreaterOrEqual(Stats.wrong, 2, "틀린 틈 집계");
        Assert.AreEqual("card", bot.Screen);

        yield return PayWithCard();
        yield return PickupAndFinish();

        Assert.AreEqual("dine", Order.place);
        Assert.AreEqual("mushroom", Order.item);
        Assert.AreEqual("large", Order.combo);
        Assert.AreEqual("cola", Order.drink);
        Assert.IsTrue(Order.sizeUp);
        Assert.IsTrue(Order.paid);
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator BlowupThenResume()
    {
        yield return EnterKiosk();
        yield return PressAll("start", "takeout", "skip", "tab_SIDE", "item_nugget");

        // 뒤돌아 사과: 12 내려가고 쿨타임 동안 다시 안 된다
        bot.SetNunchi(70f);
        yield return new WaitForSeconds(0.3f);
        yield return Key(UnityEngine.InputSystem.Key.S);
        yield return Until(() => nunchi.LookingBack, 3f, "뒤돌아보기");
        float before = nunchi.Value;
        yield return Key(UnityEngine.InputSystem.Key.E);
        Assert.AreEqual(1, Stats.sorry, "사과 집계");
        Assert.Less(nunchi.Value, before - 10f, "사과 감소");
        yield return Key(UnityEngine.InputSystem.Key.E);
        Assert.AreEqual(1, Stats.sorry, "쿨타임");
        yield return Key(UnityEngine.InputSystem.Key.D);
        yield return Until(() => !nunchi.LookingBack, 3f, "키오스크로 돌아옴");

        // 폭발
        bot.SetNunchi(99.9f);
        yield return Until(() => Stats.blowups == 1, 5f, "폭발 시작");
        Assert.IsTrue(nunchi.Hold);
        Time.timeScale = 3f;
        yield return Until(() => !nunchi.Hold, 40f, "폭발 끝");
        Time.timeScale = 1f;

        Assert.AreEqual("idle", bot.Screen);
        Assert.AreEqual(0, bot.CartCount, "장바구니 삭제");
        Assert.IsTrue(string.IsNullOrEmpty(Order.item), "주문 삭제");
        Assert.GreaterOrEqual(nunchi.Value, 45f);
        Assert.Less(nunchi.Value, 50f);
        Assert.AreEqual(0.7f, nunchi.RateMul, 1e-4f);
        Assert.GreaterOrEqual(Stats.resets, 1);

        // 처음부터 다시 주문해 끝까지
        yield return new WaitForSeconds(0.7f);
        yield return OrderMemo();
        yield return PayWithCard();
        yield return PickupAndFinish();
        AssertMemoOrder();
        Assert.AreEqual(1, Stats.blowups);
    }

    [UnityTest, Timeout(Limit)]
    public IEnumerator TimeOut()
    {
        yield return EnterKiosk();
        yield return PressAll("start", "takeout", "skip", "tab_SIDE", "item_fries_r");
        Assert.AreEqual(0, Stats.resets);

        // 터치 없이 제한 시간이 거의 다 된 상태
        bot.SetNunchi(0f);
        bot.SetTimer(1.2f);
        yield return Until(() => bot.Screen == "idle", 5f, "시간 초과 리셋");

        Assert.AreEqual(1, Stats.resets);
        Assert.AreEqual(0, Stats.blowups);
        Assert.AreEqual(0, bot.CartCount, "장바구니 삭제");
        Assert.IsTrue(string.IsNullOrEmpty(Order.item), "주문 삭제");
    }

    // 0번 챕터 진입 때 제목이 뜨고, 닫으면 메모 장면이 걷기를 묶은 채 시작한다
    [UnityTest, Timeout(Limit)]
    public IEnumerator TitleThenMemo()
    {
        Hud.SkipTitle = false;
        GameState.I.JumpChapter(0);
        yield return Until(() => Hud.I.TitleOpen, 20f, "제목 화면");
        Assert.AreEqual(0f, Time.timeScale, "제목 중 시간 멈춤");
        yield return Key(UnityEngine.InputSystem.Key.Enter);
        yield return Until(() => !Hud.I.TitleOpen, 5f, "제목 닫힘");
        Assert.AreEqual(1f, Time.timeScale);
        yield return Until(() => HandRig.I.Held == ItemId.Memo, 10f, "메모 들기");
        Assert.IsTrue(PlayerController.I.HoldStill, "메모 중 걷기 묶임");
        yield return Until(() => !PlayerController.I.Frozen, 10f, "조작 넘어옴");
        yield return Key(UnityEngine.InputSystem.Key.Digit1);
        yield return Until(() => !PlayerController.I.HoldStill, 5f, "메모 내리면 걷기 풀림");
    }
}
