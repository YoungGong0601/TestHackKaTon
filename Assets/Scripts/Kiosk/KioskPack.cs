using UnityEngine;

// 회차별 키오스크 화면 묶음. Pack 프리팹 루트, 같은 오브젝트에 KioskScreens. 씬의 PH_Kiosk KioskCanvas 아래에 하나만 둔다
public abstract class KioskPack : MonoBehaviour
{
    public KioskController Ctl { get; internal set; }
    public abstract string FirstScreen { get; }
    public virtual bool Timed => false;         // 시간 초과를 세는 화면에서 true. 프로필 kioskTimeout이 켜져야 돈다
    public virtual bool CanGiveUp => true;      // 눈치 버튼 허용
    public abstract void OnPress(string id);    // 터치 판정 뒤 확정된 버튼
    public virtual void OnEnter() { }
    public virtual void OnTimeout() { }         // 시간 초과
    public virtual void OnTick(float dt) { }
    public virtual bool Hit(Collider col) => false;   // 화면 밖 본체 클릭을 Pack이 받으면 true
}
