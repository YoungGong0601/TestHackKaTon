# Core API (회차 담당용)

시그니처 정본은 ROUND_PLAN 6절이다. 여기는 쓰는 순서와 주의만 적는다.

## 씬 시작과 끝
```csharp
IEnumerator Start() {
  yield return Round.Open("112번 버스를 타고 버거집에 가세요.");  // 4회차는 인수 없이
  ...
  GameState.I.CompleteChapter();   // 프로필이 바뀌면 눈 감기, 같으면 암전. 마지막 챕터는 엔딩
}
```
Round.Open을 부르지 않으면 화면이 안 열린다. 목표는 대사가 끝나면 자막 자리로 돌아온다. Round.Goal(null)로 지운다.

## 키오스크
PH_Kiosk 인스턴스의 KioskCanvas 아래에 Pack 프리팹 하나. Pack 루트에 KioskPack 파생과 KioskScreens를 같이 붙이고, KioskScreens.screens에 화면을 넣는다. canvas 칸은 비워도 된다(KioskController가 넣음). 화면의 buttons는 KioskScreen.Collect로 모은다.

| 호출 | 뜻 |
|---|---|
| yield return kiosk.Enter() | 포인터 모드 진입. Pack.OnEnter가 불리고 Finish까지 돌아오지 않는다 |
| Ctl.Go(id) | 화면 전환 |
| Ctl.Toast(text) | Kiosk_ToastSec 뒤 사라지는 알림 |
| Ctl.ResetTimer() | 시간 초과 되돌림. 터치마다 Core가 부른다 |
| Ctl.Finish() | 키오스크를 떠남 |
| Ctl.Pay | Slot_ic의 PayPoint. 결제 화면에서 이벤트를 듣는다 |
| Ctl.View, ViewChanged, StaffCalled | 시선과 A 시선의 E |

터치 실패, 옆 버튼 눌림, 빈 곳 터치 소리는 Core가 처리한다. Pack.OnPress는 확정된 버튼만 받는다.

## 눈치
Enter 전에 nunchi.Configure(new NunchiRule { ... }). choices가 null이면 100에서 멈춘다. 다 차면 HUD 오른쪽 아래 그만두기가 뜨고, Pack.CanGiveUp이 false면 안 뜬다. onLeave 안에서 Ctl.Finish를 부른다. 한숨은 sigh_m_1 고정. 대사는 low, mid, high 문구이고 NunchiLines.Hurry와 글자가 같으면 음성이 나온다.

## 결제
| 인물 | 드는 법 |
|---|---|
| 지갑 없음 | 3 키로 카드 |
| 지갑 있음 | 3 키로 지갑을 열고 카드나 지폐를 클릭. 걷는 중이면 들자마자 지갑이 닫힌다 |

PayPoint는 Interactable이 같이 있으면 onUse로 클릭을 받는다(PH_BusTerminal). 소리는 Core가 내고 안내 문구는 Director가 낸다. 튕김 기준은 Bal.I("Cash_BounceCount", 3)와 CashRejected의 인수를 비교한다.

## 지갑과 쪽지
4회차 시작: Round.Open 뒤 Wallet.I.SetOpen(true). 쪽지 문구는 PH_Hand의 Hand_Wallet/Note. NoteRead는 한 판에 한 번.

## 그 밖
| 호출 | 뜻 |
|---|---|
| yield return Mash.Climb(bottom, top) | 시선은 top의 y 회전. 끝나면 이전 모드로 돌아가고 조작 잠금은 부르기 전 상태 |
| yield return Mash.Descend(top, bottom) | 입력 없음 |
| yield return Watch.Look(hour) | R4_WatchHour1 등 |
| yield return Choice.Ask(labels, i => ...) | 최대 4줄 |
| yield return Cine.BackShot(npc, to, sec) | 끝나면 플레이어를 원래 자리로 돌린다 |
| Hud.I.SideNote(text) | 왼쪽 위 작은 글자 |
| AudioManager.I.Play(key, pos, vol, rate, clear: true) | 먹먹함 제외 |
| Bal.Age(name, a20, a40, a60, a80) | 인물 키와 인물별 fallback |

## 공통 물건
Sticker_CardOnly, PH_Poster, PH_Notice_Cashless, PH_BusTerminal은 Readable이다. 4회차에서 카드 전용 깜빡임은 R4가 낸다.
Anchor_BusInside에 Teleport하면 버스 안이다. Driver, PH_BusTerminal이 PH_BusInterior 자식이다.
