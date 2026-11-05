// 호출 전광판의 숫자. PH_PickupBoard에 부착. 준비 중, 호출 제목 글자는 프리팹에 직접 둔다.
// 배치: readyTexts = 번진 쪽과 또렷한 쪽의 준비 번호 TMP 둘 다
// 배치: callTexts = 번진 쪽과 또렷한 쪽의 호출 번호 TMP 둘 다
using System.Collections.Generic;
using System.Text;
using TMPro;
using UnityEngine;

public class PickupBoard : MonoBehaviour
{
    [SerializeField] TMP_Text[] readyTexts;
    [SerializeField] TMP_Text[] callTexts;

    public void Show(List<int> ready, int call)
    {
        var sb = new StringBuilder();
        for (int i = 0; i < ready.Count && i < 4; i++)
        {
            if (i > 0) sb.Append(i % 2 == 0 ? "\n" : "   ");
            sb.Append(ready[i]);
        }
        foreach (TMP_Text t in readyTexts) t.text = sb.ToString();
        foreach (TMP_Text t in callTexts) t.text = call.ToString();
    }
}
