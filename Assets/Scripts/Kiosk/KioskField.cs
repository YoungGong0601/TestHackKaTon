// 코드가 값을 바꾸는 화면 요소 표시. 글자면 graphic에 TMP_Text 또는 Text, 켜고 끄기만 하면 비워도 된다.
// 배치: key = KioskScreens.cs 맨 위 주석의 키, graphic = 같은 오브젝트의 글자 컴포넌트
using TMPro;
using UnityEngine;
using UnityEngine.UI;

public class KioskField : MonoBehaviour
{
    public string key;
    public Graphic graphic;

    public void SetText(string value)
    {
        if (graphic is TMP_Text t) t.text = value;
        else if (graphic is Text u) u.text = value;
    }

    /// <summary>진행 막대. 왼쪽 피벗의 가로 크기로 표시</summary>
    public void SetFill(float p) => transform.localScale = new Vector3(Mathf.Clamp01(p), 1f, 1f);

    void Reset() => graphic = GetComponent<Graphic>();
}
