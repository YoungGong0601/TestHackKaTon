// 내용이 바뀌는 칸(메뉴, 사이드, 음료, 구성, 장바구니 줄). 켜고 끄며 글자와 버튼 id만 바꾼다.
// 배치: button = 칸의 KioskButton(장바구니 줄은 삭제 버튼), 자식 글자는 KioskField
using UnityEngine;

public class KioskCell : KioskFields
{
    public KioskButton button;

    public void Bind(string buttonId)
    {
        gameObject.SetActive(true);
        if (button) button.id = buttonId;
    }

    public override void Collect()
    {
        base.Collect();
        if (!button) button = GetComponentInChildren<KioskButton>(true);
    }
}
