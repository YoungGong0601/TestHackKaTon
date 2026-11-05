// 1-7, 1-8 쉬운 키오스크. 메뉴 3칸, 카드 결제, 번호. 화면은 menu, pay, done.
// 버튼 id: burger, soldout, back. 결제는 PH_Kiosk 의 Slot_ic 에 붙은 PayPoint.
// 배치: numberTexts = done 화면의 번호 TMP
using System.Collections;
using TMPro;
using UnityEngine;

public class R1BurgerPack : KioskPack
{
    [SerializeField] TMP_Text[] numberTexts = new TMP_Text[0];

    PayPoint pay;
    string screen;

    public override string FirstScreen => "menu";
    public override bool CanGiveUp => false;

    public override void OnEnter()
    {
        screen = FirstScreen;
        pay = Ctl.Pay;
        pay.Approved += OnPaid;
        pay.Empty += OnEmpty;
        AudioManager.I.Vo("k_menu");
    }

    void OnDestroy()
    {
        if (!pay) return;
        pay.Approved -= OnPaid;
        pay.Empty -= OnEmpty;
    }

    void Show(string id)
    {
        screen = id;
        Ctl.Go(id);
    }

    public override void OnPress(string id)
    {
        switch (id)
        {
            case "burger":
                GameState.I.Order.item = KioskPick.SetName;
                Show("pay");
                HandRig.I.Equip(ItemId.Card);
                AudioManager.I.Vo("k_card");
                break;
            case "soldout":
                AudioManager.I.Play("kiosk_error", null, 0.5f);
                Ctl.Toast("품절");
                break;
            case "back":
                HandRig.I.Equip(ItemId.None);
                Show("menu");
                break;
        }
    }

    void OnEmpty()
    {
        Ctl.Toast(screen == "pay" ? $"{ItemKeys.Of(ItemId.Card)} 카드" : "메뉴");
    }

    void OnPaid()
    {
        if (screen == "done") return;
        if (screen != "pay")
        {
            AudioManager.I.Play("kiosk_error", null, 0.5f);
            Ctl.Toast("메뉴");
            return;
        }
        int number = Bal.I("R1_OrderNumber", 274);
        GameState.I.Order.number = number;
        foreach (TMP_Text t in numberTexts) t.text = number.ToString();
        HandRig.I.Equip(ItemId.None);
        Show("done");
        StartCoroutine(Close());
    }

    IEnumerator Close()
    {
        yield return new WaitForSeconds(Bal.G("R1_DoneShowSec", 1.6f));
        Ctl.Finish();
    }

    // 1-9 알바생이 도와줄 때 다음에 누를 곳을 번쩍여 보여 준다
    public void Hint()
    {
        if (screen == "menu") GetComponent<KioskScreens>().Find("burger")?.Flash();
        else if (screen == "pay") Ctl.Toast("카드");
    }
}
