using UnityEngine;

// 조작 인물. 수치는 여기 두지 않고 ConfigTable에서 keyPrefix+이름으로 읽는다
[CreateAssetMenu(menuName = "Kiosk/Character Profile")]
public class CharacterProfile : ScriptableObject
{
    public string id;
    public string displayName;
    public string keyPrefix;
    public string speakerKey;
    public int handLook;        // 손 단계 0~3. 3은 소매, 반지, 손목시계. Bal.Age의 fallback 칸이기도 하다
    public ItemId[] items;
    public bool limp;
    public bool visionBlur;
    public bool kioskBlur;
    public bool kioskNunchi;
    public bool kioskHideMeaning;
    public bool kioskTouchFail;
    public bool muffle;
    public bool tremble;
    public bool cursorLag;
    public bool lensFocus;
    public bool kioskTimeout;

    public bool Has(ItemId item) => items != null && System.Array.IndexOf(items, item) >= 0;
}
