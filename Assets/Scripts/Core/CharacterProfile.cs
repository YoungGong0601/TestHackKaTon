using UnityEngine;

// 조작 인물. 수치는 여기 두지 않고 ConfigTable에서 keyPrefix+이름으로 읽는다
[CreateAssetMenu(menuName = "Kiosk/Character Profile")]
public class CharacterProfile : ScriptableObject
{
    public string id;
    public string displayName;
    public string keyPrefix;
    public string speakerKey;
    public ItemId[] items;
    public bool limp;
    public bool visionBlur;
    public bool kioskBlur;
    public bool kioskNunchi;
    public bool kioskHideMeaning;
    public bool kioskTouchFail;

    public bool Has(ItemId item) => items != null && System.Array.IndexOf(items, item) >= 0;
}
