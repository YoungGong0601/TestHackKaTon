// KioskField 묶음. 저장된 배열만 쓰고, 에디터에서 Collect로 채운다(OnValidate 자동, 프리팹 저장 전 호출 권장).
using System.Linq;
using UnityEngine;

public class KioskFields : MonoBehaviour
{
    [SerializeField] protected KioskField[] fields = new KioskField[0];

    public void Text(string key, string value)
    {
        foreach (var f in fields) if (f.key == key) f.SetText(value);
    }

    public void Show(string key, bool on)
    {
        foreach (var f in fields) if (f.key == key) f.gameObject.SetActive(on);
    }

    public void Fill(string key, float p)
    {
        foreach (var f in fields) if (f.key == key) f.SetFill(p);
    }

    /// <summary>자식에서 자기 소속 표시를 모은다. 다른 묶음(칸) 아래 것은 뺀다.</summary>
    public virtual void Collect()
    {
        fields = GetComponentsInChildren<KioskField>(true).Where(f => f.GetComponentInParent<KioskFields>(true) == this).ToArray();
    }

#if UNITY_EDITOR
    protected virtual void OnValidate() => Collect();
#endif
}
