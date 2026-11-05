Nunchi: NunchiSystem은 PH_Kiosk 오브젝트(또는 그 자식)에 붙고 Update로 스스로 돈다. KioskController는 Enter에서 Begin(), 끝날 때 End()만 부른다. 프로필 kioskNunchi가 false면 Begin은 아무것도 안 한다.
Nunchi: KioskController가 NunchiSystem에 넣어 주는 값은 public 필드 LookingBack(S 뒤 시선일 때 true), Func<bool> CanBlow(폭발 가능 여부, HTML flow.safe()와 !busy), Func<int> QueueCount(없으면 Nunchi_DefaultQueue 3).
Nunchi: 폭발 흐름은 NunchiSystem이 100 도달 시 event Action BlowupRequested를 낸다. KioskController는 이를 받아 HoldForBlowup(), 자기 event Blowup 발생, 연출 후 ResumeAfterBlowup()을 부른다(게이지 45, 상승률 0.7배 누적, 재촉 20초 뒤).
Nunchi: 화면 글자 추가 번짐은 int BlurStep(0,1,2). 키오스크 쿼드 번짐 반지름은 Kiosk_BlurBase + step x Nunchi_ScreenBlurPerStep으로 Kiosk가 적용한다.
Nunchi: 사과 반응은 event Action Sorried(KioskController가 QueueManager.Sorry를 구독). E 키는 KioskController가 시선이 뒤일 때 Sorry()를 부른다. 프롬프트 라벨 판단용 float Cooldown 공개.
Nunchi: 씬 배치 필수: Player 카메라 Post Processing 켬. NunchiSystem 필드 queue = Store 씬 QueueManager, heartbeat, tinnitus = 루프 AudioSource(playOnAwake 끔, 볼륨 0).
Nunchi: PlayMode 시험 asmdef가 게임 코드를 참조하려면 Assembly-CSharp로는 안 되어 Assets/Scripts/KioskGame.asmdef를 둔다. 런타임 코드는 전부 Assets/Scripts 아래에 두고, Assets/Scripts 아래 UnityEditor 코드는 #if UNITY_EDITOR로 감싼다.
Nunchi: 키오스크 진입은 label 주문하기 Interactable.onUse.Invoke(), 받기는 label 받기 Interactable. 주문 판정은 GameState.Order(place takeout, item bulgogi, combo combo, drink cider)로 HTML 값과 같은 id 문자열을 쓴다.
Store: QueueManager(Store 씬 Director 오브젝트)는 Kiosk용 공개 멤버 int Count, Vector3 QueuePos, bool Blowing, void Sorry()를 제공한다. KioskController는 SerializeField로 QueueManager를 받아 눈치 계산과 사과 반응에 쓴다.
Store: 폭발 대기 방식. QueueManager가 KioskController.Blowup 이벤트를 구독해 연출 코루틴을 돌린다. Kiosk는 Blowup?.Invoke() 뒤 QueueManager.Blowing이 false가 될 때까지(최대 45초) 기다린 다음 HTML판처럼 암전, 리셋, 플레이어 복귀를 한다.
Store: 연출 중 눈치 값은 QueueManager가 NunchiSystem.Value = Bal.G("Nunchi_BlowupWatch",62)로 직접 쓴다. Value는 public set이어야 한다.
Store: Interactable.onUse, Readable.onRead는 Director가 OnEnable에서 코드로 구독한다. 씬 배치에서 UnityEvent를 연결하지 않는다(중복 호출 방지). Interactable 참조 필드만 연결한다.
Story: 추가 스크립트 BusMover(PH_Bus 인스턴스 루트 Bus1, Bus2), StreetNpc(PH_NPC 인스턴스 루트 Student, Worker). 필드와 좌표는 각 파일과 HomeDirector, StreetDirector 맨 위 배치 주석대로.
Story: 씬이 HTML판처럼 암전에서 시작하도록 Director Start가 Hud.Fade(1,0) 뒤 Fade(0,초)를 부른다. 타이틀은 GameState가 띄우고 HomeDirector는 Hud.TitleOpen이 꺼질 때까지 기다린다.
Story: 메모를 든 동안은 PlayerController.HoldStill로 걷기만 막는다(HTML speed 0.001). 시선과 E는 그대로 된다.
Story: 손에 든 지팡이는 계약에 없어 Story가 다루지 않는다. 현관의 LeanCane만 끄고 cane_tap 소리만 낸다. 연출 중 손 끄기는 HandRig.SetEnabled(false)이고 챕터 진입 때 Clear가 되살린다.
Story: Say에 pos가 없어 pass_1, pass_2는 위치 없이 재생한다. hold는 Say 뒤 남은 시간을 기다려 맞춘다. Objective의 keep은 HTML 값을 넘긴다.
Story: 버스 대기 소리 bus_idle은 Ambience(amb_city_morning, bus_idle)로 바꿔 켜고 도시 소리만으로 되돌려 끈다.
Story: 그레이박스 범위라 배경 행인, 아주머니, 전구 떨림, 시계 초침, 후처리 값 변경은 넣지 않았다.
Story: 지나가는 차 5대와 오토바이 1대는 Street 씬 Traffic 아래 PH_Car, PH_Scooter 인스턴스이고 TrafficMover가 HTML판 traffic처럼 움직인다. 버스 도착 전 정류장 쪽 차선이 빌 때까지 Traffic_BusWaitMaxSec까지 기다린다.
Story: crosswalk_beep, crowd_murmur_tense, tray_put은 HTML판 코드에서 쓰지 않았다. 시점을 새로 정했다. 횡단보도 신호음은 Anchors/Crosswalk_Sound의 CrosswalkBeep, 웅성임은 NunchiSystem의 Nunchi_Crowd, 음식 놓는 소리는 StoreDirector가 받는 곳 선반이 나타날 때이다.
Store: 사과 반응은 QueueManager가 OnEnable에서 NunchiSystem.Sorried를 코드로 구독한다. NunchiSystem.onSorry UnityEvent는 씬에서 연결하지 않아도 된다.
Store: KioskController는 nunchi.QueueCount = () => queue.Count를 넣는다. 폭발은 BlowupRequested를 받아 자기 Blowup 이벤트를 내고 QueueManager.Blowing이 false가 된 뒤 ResumeAfterBlowup을 부른다.
Store: 추가 스크립트 PickupBoard(PH_PickupBoard). 필드와 좌표는 StorefrontDirector, StoreDirector, QueueManager, NpcMover, PickupBoard 맨 위 배치 주석대로. PH_NPC에 NpcMover를 붙이고 자식 Visual, 꺼 둔 Bag을 둔다. 물리 없이 transform으로 움직이므로 줄 손님 콜라이더는 플레이어를 막지 않게 둔다.
Store: 영수증은 돋보기와 같이 써야 해서 HandRig 소지품(ItemId.Receipt)이 아니라 Store 씬의 Receipt_View(Readable)를 HandRoot 아래로 옮겨 쓴다. 들고 가는 Carried_Bag도 같고, StoreDirector.OnDestroy가 지운다. 4번 키는 StoreDirector가 읽는다. HandRoot는 카메라 자식이어야 하고 전방 +Z 기준으로 위치를 준다.
Store: PlayerController.WalkTo, LookAt은 내부 플래그 없이 코루틴 진행만으로 움직여야 한다. 시간 초과 때 StopCoroutine으로 끊고 다음 WalkTo를 시작한다(Freeze 중에도 동작).
Store: 문 미는 손은 계약에 없어 HandRig.SetPointer(true)와 Tap()으로 대신한다. Say의 hold, pos, rate 인자가 없어 글자 길이 기준으로 표시되고 위치 없이 재생한다. 후처리 값 변경, 형광등 떨림, 앉은 자세와 폰 보기 포즈, 테이블 음식은 그레이박스 범위 밖이라 넣지 않았다.
Store: 수치 차이 주의. SPEC은 폭발 뒤 게이지 45, HTML은 연출 중 62로 두고 끝나면 45로 바꾼다. Store는 62, 45는 Nunchi 쪽 값.
Core: HUD 글자는 TextMeshProUGUI(리치 텍스트 켬)이고 Debug만 Legacy Text이다. 폰트 배치는 CONTRACT의 폰트를 따른다. 필드와 오브젝트 이름은 Hud.cs 맨 위 배치 주석 기준.
Core: PlayerSpawn(id, ground: concrete 또는 tile) 컴포넌트를 씬의 PlayerSpawn 오브젝트에 붙인다. GameState가 씬 로드 때 Director의 Start보다 먼저 플레이어를 옮기고 Freeze(true), Fps 모드, 손 비움을 한다. 씬에 다른 Camera, AudioListener를 두지 않는다.
Core: 챕터 전환은 암전(Fade 1)인 채로 끝난다. Director가 시작 때 Hud.I.Fade(0, 초)와 PlayerController.I.Freeze(false)를 부른다(HTML판 onEnter와 같음).
Core: 제목 화면은 GameState.EnterChapter가 chapterIndex 0일 때 부른다(맨 앞 챕터가 바뀌어도 맞다). 씬 코드는 Hud.TitleOpen을 기다린다. 열린 동안 timeScale 0, 소리 멈춤. 시험은 Hud.SkipTitle = true. 결과 화면 클릭은 GameState.Restart()로 첫 챕터.
Core: Teleport의 yaw와 TurnTo, Yaw, Pitch는 도(Unity 기준, Pitch는 위가 +). HTML판 라디안 yaw는 -yaw * Rad2Deg. LookAt, WalkTo의 sec, speed는 생략 가능.
Core: Cursor01과 SetCursor01은 뷰포트 좌표(왼쪽 아래 0,0)라 Eye.ViewportPointToRay에 바로 넣는다. 떨림 포함 값은 HandRig.I.Ptr01(), 광선은 HandRig.I.PointerRay(). Cursor 모드는 OS 커서 숨김, Confined.
Core: 계약에 더한 선택 인자와 멤버: Say(.., hold, pos, vol), Objective(text, keep=6), Play(.., rate), Vo(.., vol), Loop, SetLoop, StopLoop, Hud.Cross, Hud.TitleOpen, Hud.ToggleDebug, PlayerController.CurrentMode, Frozen, Ground, Yaw, Pitch, HoldStill, EyeHeight, EyePos, TurnTo, HandRig.SetEnabled, Clear, ItemsEnabled, Pointer, LensHit, memoSide, memoScale, pointerDist, RunStats.endTime, GameState.Restart, DebugToKiosk.
Core: Interactable에 cone(0.82) 필드 추가. 좌클릭은 E와 같다. Readable은 area에 조준용 Collider를 연결하고, 돋보기 원이 닿기 시작할 때 onRead를 한 번 부른다. 프로필 visionBlur가 false면 늘 sharp이고 조준만으로 onRead가 온다.
Core: 영수증은 소지품이 아니고 StoreDirector가 4번 키로 다룬다. 화면 라벨은 Hud.I.Views("4 영수증").
Core: 디버그 키 F1, F2, F3, F5, F7은 GameState, F6은 NunchiSystem에 있다. F5는 ChapterEntry.hasKiosk 챕터로 가서 GameState.DebugToKiosk를 켜고 StoreDirector가 주문 단계에서 받는다.
Core: AudioManager 소스는 프리팹 배치(Sfx 12, Vo 2, Loop 6). 소리 크레딧은 Assets/Resources/Audio/SFX_CREDITS.csv, VO_LINES.csv.
Nunchi: 시험은 SceneManager.LoadSceneAsync("Store")로 시작하므로 Store 씬이 Build Settings에 있어야 한다. KioskBot은 PH_Kiosk에 배치되어 있어야 하고, 시험 Timeout은 경로당 300초다.
Kiosk: UI 배치 명세(화면별 KioskField 키, 버튼 id, 칸 개수, 오버레이)는 Assets/Scripts/Kiosk/KioskScreens.cs 맨 위 주석이 기준이다. PH_Kiosk 필드는 KioskController.cs 맨 위 주석대로 연결한다.
Kiosk: 계약에 없던 컴포넌트 추가. KioskField(값 바꿀 글자나 켜고 끌 요소), KioskFields(묶음, Overlay_Toast, Overlay_Info, Overlay_Timer에 부착), KioskCell(내용이 바뀌는 칸), KioskSpot(poster, call, paper), KioskCard, KioskReceipt.
Kiosk: KioskScreen과 KioskCell의 fields, buttons, cells 배열은 OnValidate가 채운다. 프리팹을 코드로 저장할 때는 저장 직전에 Collect()를 불러 값이 저장되게 한다.
Kiosk: 캔버스는 World Space 1080 x 1920, 레이어 KioskUI. 뜻 풀이는 레이어 KioskReveal의 자식 Canvas 아래에 둔다(uGUI 레이어는 Canvas 단위로 걸러진다). 광고와 팝업은 뜻 풀이보다 뒤 자식이라 위에 그려져야 한다.
Kiosk: 메뉴 칸 id는 코드가 넣는다(item_<id>). 프리팹에는 칸 메뉴 9개, 구성 3개, 사이드 6개, 음료 8개, 장바구니 줄 4개만 배치하면 된다. 칸 안 KioskButton id는 비워도 된다.
Kiosk: 화면 판정은 EventSystem을 쓰지 않는다. 화면 쿼드는 Unity Quad(보이는 면이 local -Z, 손님 쪽), 콜라이더 필수, 판정은 맞은 점을 쿼드 local로 바꿔 쓴다. 키오스크 콜라이더는 전부 KioskController 오브젝트의 자식이어야 한다.
Kiosk: 셰이더 Graybox/LensScreen 속성은 _BlurRadius(_BaseTex 픽셀 번짐 반지름)뿐이다. MaterialPropertyBlock으로 넣는다. 원과 확대는 CONTRACT의 돋보기를 따른다. RT_Base, RT_Sharp는 mip 생성 켬.
Kiosk: 번짐은 캔버스 픽셀 반지름(Kiosk_BlurBase + BlurStep x Nunchi_ScreenBlurPerStep)이다. 셰이더가 RT의 mip 위에서 16점 나선으로 읽는다. 추가 RT는 없다.
Kiosk: KioskController는 실행 순서 -40으로 PlayerController(-50) 다음, HandRig(0) 앞에서 Eye를 직접 놓는다. PlayerController의 흔들림 위치만 이어 받고 회전 흔들림은 키오스크 조작 중 없다.
Kiosk: 눈높이는 인물별 키 <접두어>KioskEye, KioskEyeDown. 그 외 키오스크 수치는 Kiosk_ 공통. 목록은 Docs/keys_Kiosk.csv.
Kiosk: 사과 반응은 QueueManager가 Sorried를 구독하므로 Kiosk는 연결하지 않는다. 폭발은 Store 노트대로 Blowup 뒤 Blowing을 기다리고 ResumeAfterBlowup을 부른다.
Kiosk: 시험 API KioskBot은 PH_Kiosk에 부착, kiosk 필드 연결. 계약 외 추가로 View, Timer, CartCount, Ad, CanTear, Active, Busy, SetTimer가 있다.
Kiosk: 그레이박스라 HTML의 터치 물결과 음식 그림은 빼고 눌림은 Button targetGraphic의 짧은 색 변화로 표시한다. 지문, 글레어, 본체 흔들림(nudge)도 없다.
통합: 재질은 Assets/Graybox/Materials에 Gray_Light(0.72), Gray_Mid(0.5), Gray_Dark(0.28), Gray_Interact(0.82). URP Lit, 텍스처 없음.
통합: 데이터는 Assets/Graybox/Data에 Elder.asset, ChapterFlow.asset(Home, Street, Storefront, Store). 씬의 PlayerSpawn.id는 각각 home, street, storefront, store로 둔다.
통합: 후처리는 Assets/Graybox/Data/PostProfile.asset 하나를 모든 씬 Global Volume이 쓴다. 켜진 override는 Bloom뿐이고 나머지는 CONTRACT의 화면 후처리가 대신한다.
통합: PH_Hand의 Hand_Receipt, HandRig 영수증 경로, PlayerController.EyeLift와 Roll, NunchiSystem.BlurStepChanged는 쓰는 곳이 없어 지웠다. 소리 클립은 계약대로 Resources.Load를 쓴다. GameState의 FindObjectsByType<PlayerSpawn>은 DontDestroyOnLoad 오브젝트가 씬 참조를 못 가져 남긴다.
통합: Store 씬 NPC_Eater는 유리 너머 손님과 이어지게 둔 한 명이다. 벽 메뉴판, 포스터, 나머지 손님은 기능에 필요하지 않아 넣지 않았다.

메인: Bus 챕터는 Street와 Storefront 사이, 시작 지점 id bus. 내부 공간만 있고 이동 연출은 보류.
