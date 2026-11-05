using UnityEngine;

// 회차별 키오스크 화면 묶음. Pack 프리팹 루트, 같은 오브젝트에 KioskScreens. 씬의 PH_Kiosk KioskCanvas 아래에 하나만 둔다
public abstract class KioskPack : MonoBehaviour
{
    public KioskController Ctl { get; internal set; }
    public abstract string FirstScreen { get; }
    public virtual bool Timed => false;         // 무입력 시간을 세는 화면에서 true
    public virtual bool ShowMeaning => true;    // false면 뜻 풀이를 아예 안 그린다
    public virtual bool CanGiveUp => true;      // 눈치 버튼 허용
    public abstract void OnPress(string id);    // 터치 판정 뒤 확정된 버튼
    public virtual void OnEnter() { }
    public virtual void OnTimeout() { }         // 시간 초과
    public virtual void OnTick(float dt) { }
    public virtual bool Hit(Collider col) => false;   // 화면 밖 본체 클릭을 Pack이 받으면 true
    public virtual string[] CustomerScreens => new[] { FirstScreen };   // 다음 손님이 차례로 넘기는 화면
    public virtual void ShowCustomer(string id) => GetComponent<KioskScreens>().Show(id);
}
