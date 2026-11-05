using System;
using UnityEngine;

// 결제 지점. Fps 모드는 같은 오브젝트의 Interactable.onUse로, 키오스크는 Slot_ic에 붙어 KioskController.Click으로 들어온다
public class PayPoint : MonoBehaviour
{
    public bool DeferOk;                     // 승인음을 듣는 쪽이 결제가 끝날 때 낸다
    public event Action Approved;            // 카드를 든 채 클릭
    public event Action<int> CashRejected;   // 지폐를 든 채 클릭, 인수는 이 지점의 누적 횟수
    public event Action Empty;               // 빈손 클릭

    int count;

    void Awake()
    {
        var use = GetComponent<Interactable>();
        if (use != null) use.onUse.AddListener(Click);
    }

    public void ResetCount() => count = 0;

    public void Click()
    {
        var hands = HandRig.I;
        hands.Tap();
        if (hands.Held == ItemId.Card)
        {
            AudioManager.I.Play("card_insert", null, 0.8f);
            if (!DeferOk) AudioManager.I.Play("kiosk_ok", null, 0.7f);
            Approved?.Invoke();
        }
        else if (hands.Held == ItemId.Cash)
        {
            hands.Kick();
            AudioManager.I.Play("card_reject", null, 0.9f);
            CashRejected?.Invoke(++count);
        }
        else
        {
            AudioManager.I.Play("kiosk_error", null, 0.7f);
            Empty?.Invoke();
        }
    }
}
