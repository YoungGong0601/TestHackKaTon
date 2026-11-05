// 키오스크 품목 그림 목록. 파일 이름으로 찾는다. 부착: PH_Kiosk_R4 루트
// 배치: sprites = Assets/UI/Kiosk/Art/food 전부와 combo_ 그림
using System.Collections.Generic;
using UnityEngine;

public class KioskFood : MonoBehaviour
{
    [SerializeField] Sprite[] sprites = new Sprite[0];

    Dictionary<string, Sprite> byName;

    public Sprite Get(string file)
    {
        if (byName == null)
        {
            byName = new Dictionary<string, Sprite>();
            foreach (var s in sprites) if (s) byName[s.name] = s;
        }
        return byName.TryGetValue(file, out var found) ? found : null;
    }
}
