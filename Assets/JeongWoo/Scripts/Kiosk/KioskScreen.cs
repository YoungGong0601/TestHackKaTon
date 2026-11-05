// 화면 하나(Assets/UI/Kiosk/Screen_<id>.prefab 루트).
// 배치: id = 화면 id, backdrop = 뒤에 비치는 화면(member는 place, upsell은 drink, 그 외 비움)
using UnityEngine;

public class KioskScreen : KioskFields
{
    public string id;
    public KioskScreen backdrop;
    public KioskButton[] buttons = new KioskButton[0];   // 계층 순서, 뒤가 위
    public KioskCell[] cells = new KioskCell[0];         // 계층 순서

    public override void Collect()
    {
        base.Collect();
        buttons = GetComponentsInChildren<KioskButton>(true);
        cells = GetComponentsInChildren<KioskCell>(true);
    }
}
