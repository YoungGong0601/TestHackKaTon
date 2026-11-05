# 계약 문서 (코드 담당과 배치 담당의 공통 기준)

기획과 문구 원본: `../kiosk-game/SPEC.md`, `src/kiosk/data.js`(메뉴), `src/kiosk/screens.js`(화면 문구), `src/kiosk/flow.js`, `src/kiosk/nunchi.js`, `src/scenes/*.js`. 큰 파일은 전체를 읽지 말고 필요한 부분만 grep으로 읽는다.

## 폴더 담당
| 폴더 | 담당 |
|---|---|
| Assets/Scripts/Config | 복사본, 수정 금지 |
| Assets/Scripts/Core | Core |
| Assets/Scripts/Story | Story |
| Assets/Scripts/Store | Store |
| Assets/Scripts/Kiosk | Kiosk |
| Assets/Scripts/Kiosk/Nunchi, Assets/Tests/PlayMode | Nunchi |
| Assets/Graybox/PH, Materials, Data, Shaders | 프리팹 배치, 통합 |
| Assets/UI | UI 배치(키오스크와 HUD의 TMP 폰트는 Assets/UI/Fonts) |
| Assets/Fonts | 메모 손글씨 폰트 원본과 TMP 폰트 에셋, 수정 금지 |
| Assets/Scenes | 씬 배치 |

## 씬과 진행
Home, Street, Bus, Storefront, Store 순서. 모든 씬에 `Systems.prefab`(Assets/Graybox/PH) 인스턴스 하나를 배치한다. 자식: GameState, AudioManager, Player, HUD. 중복이면 나중 것이 스스로 파괴, 먼저 것은 DontDestroyOnLoad. 씬 어디서 시작해도 동작한다.
씬마다 `PlayerSpawn`(id 문자열) 오브젝트, `Director`(씬 진행 스크립트), `Bounds`(경계 콜라이더 묶음), `Global Volume`, 조명을 직접 배치한다.
좌표: +Z가 플레이어 진행 방향의 기준이 아니라 HTML판 좌표를 그대로 쓴다(three.js도 Y 위, 미터). HTML은 오른손, Unity는 왼손이므로 z에 -1을 곱한다.

## 데이터 (Assets/Graybox/Data)
```csharp
[CreateAssetMenu] class CharacterProfile : ScriptableObject {
  string id; string displayName; string keyPrefix;      // "Elder_"
  string speakerKey;                                     // 자막 화자 "gp"
  ItemId[] items;                                        // Memo, Lens, Card
  bool limp; bool visionBlur;
  bool kioskBlur; bool kioskNunchi; bool kioskHideMeaning; bool kioskTouchFail;
}
[Serializable] class ChapterEntry { string sceneName; CharacterProfile profile; string spawnId; bool hasKiosk; }
[CreateAssetMenu] class ChapterFlow : ScriptableObject { List<ChapterEntry> chapters; List<CharacterProfile> speakers; }
```
에셋: Elder.asset, ChapterFlow.asset(노인 챕터 4개).

## Core API
```csharp
enum ItemId { None, Memo, Lens, Card }
class OrderData { string place,item,combo,side,drink; bool sizeUp,paid; int number=274; }
class RunStats { float startTime; int touches,wrong,sorry,resets,blowups; }
class GameState : MonoBehaviour {
  static GameState I; ChapterFlow flow; int chapterIndex;
  CharacterProfile Profile; OrderData Order; RunStats Stats;
  void CompleteChapter();       // 다음 챕터 로드, 마지막이면 결과
  void JumpChapter(int index);
}
static class Bal {                                       // 모든 수치는 여기로 읽고 Awake에 캐시 금지
  float F(string name, float fb);                        // ConfigTableLoader.Get(Profile.keyPrefix+name, fb)
  float G(string fullKey, float fb);                     // 인물 공통 키, 예 Nunchi_PerSecond
  int I(string fullKey, int fb);
}
class PlayerController : MonoBehaviour {
  static PlayerController I; Camera Eye; Transform HandRoot;
  enum Mode { Fps, Cursor, Locked, Hidden } void SetMode(Mode m); void Freeze(bool on);
  void Teleport(Vector3 pos, float yaw);
  IEnumerator LookAt(Vector3 world, float sec); IEnumerator WalkTo(Vector3 world, float speed);
  void AddShake(float a); Vector2 Cursor01 { get; }      // 시험용 SetCursor01(Vector2) 제공
}
class Interactable : MonoBehaviour {
  string label; KeyCode-like string key="E"; float radius=2f; UnityEvent onUse; bool active=true;
}
class Readable : MonoBehaviour { GameObject blurred; GameObject sharp; UnityEvent onRead; }  // 렌즈로 조준할 때만 sharp 표시
class HandRig : MonoBehaviour {
  static HandRig I; ItemId Held; void Equip(ItemId id); void SetPointer(bool on); void Tap(); float tremble;
}
class Hud : MonoBehaviour {
  static Hud I;
  Coroutine Say(string speaker, string text, string voKey=null);   // {y:글자} {r:} {g:} {b:} 색 표기
  void Objective(string text); void ClearSubs();
  void Prompt(string text); void Items(); void Views(string text);
  void Nunchi(float v, bool visible); Coroutine Fade(float to, float sec);
  void ShowTitle(); void ShowResult();
}
class AudioManager : MonoBehaviour {
  static AudioManager I; void Play(string key, Vector3? pos=null, float vol=1f);  // key_1.. 변형 자동
  float Vo(string key, Vector3? pos=null); void Ambience(params (string key,float vol)[] loops);
}
```
소리 경로 Resources/Audio/sfx, Resources/Audio/vo. 씬 간 참조는 `I` 싱글턴으로, 씬 안 참조는 SerializeField로.

## 씬 스크립트 (씬의 Director 오브젝트에 부착)
HomeDirector, StreetDirector, BusDirector(Story) / StorefrontDirector, StoreDirector, QueueManager, NpcMover(Store). 필드 이름은 담당이 정하고 파일 맨 위 주석에 `// 배치: 필드 = 오브젝트 이름`을 필드마다 적는다. 씬 배치 담당은 이 주석대로 연결한다. 씬 끝에는 GameState.I.CompleteChapter()만 호출, 씬 이름을 직접 쓰지 않는다.
모든 Director는 `public IEnumerator`로 시험이 부를 수 있는 진입점 없이, Interactable.onUse를 통해 진행한다. 시험은 `Interactable.onUse.Invoke()`와 PlayerController.Teleport로 진행한다.

## 키오스크
`KioskController`(Store 씬 PH_Kiosk 위): `IEnumerator Enter()`, `Reset()`, `event Action Blowup`. `KioskScreens` : id로 `KioskScreen` 켜고 끔. `KioskButton`(id, Button). `CardSlot`(id: ic, receipt, barcode; Collider). `PosterFlap`(들춤). `NunchiSystem`(`float Value; void Add(float); void Sorry();`). 시험 API `KioskBot`: `Press(id)`, `string[] Ids()`, `Slot(id)`, `LiftPoster()`, `TakeReceipt()`, `string Screen`, `SetNunchi(v)`.
화면 id: idle place member menu option side drink upsell cart pay card paying cardout done. 프리팹: Assets/UI/Kiosk/Screen_<id>.prefab. 버튼 id는 HTML판과 같음(start, skip, tab_CLASSIC, item_bulgogi, opt_combo, up_no, checkout, pay_card 등, screens.js 기준).
화면 표시: 레이어 KioskUI 캔버스를 카메라 2대가 RenderTexture 2장으로 찍는다. `RT_Base`는 뜻 풀이 레이어(KioskReveal) 제외, `RT_Sharp`는 포함. PH_Kiosk 화면 쿼드는 셰이더 `Graybox/LensScreen`: 본 카메라에는 RT_Base를 번지게(_BlurRadius), 돋보기 카메라에는 RT_Sharp. 둘 다 씬에 직접 배치한다. 터치는 쿼드 UV를 캔버스 좌표로 바꿔 버튼 판정.
시선: A 알바생, S 뒤, D 키오스크, W 아래. 시간 제한, 재촉, 폭발은 SPEC 수치.

## PH 프리팹 규칙
구조: 루트(로직, 콜라이더, 앵커) / `Visual`(회색 메시만). `Visual`은 스케일 1이고 메시는 그 자식에 둔다. 코드가 움직이거나 참조하는 것은 Visual 밖 앵커이다(HeadPivot, ReactPivot, BagAnchor, PlateAnchor, Card 루트). 재질 Assets/Graybox/Materials: Gray_Light, Gray_Mid, Gray_Dark, 상호작용 물체는 Gray_Interact(약간 밝은 회색). 색 금지. 필요한 목록은 프리팹 담당이 SPEC과 씬 코드에서 뽑되 기능에 필요한 것만: PH_Door_Home, PH_ShoeRack, PH_BusShelter, PH_BIS, PH_Bus, PH_NPC, PH_Storefront, PH_Door_Glass, PH_Counter, PH_Kiosk, PH_Kiosk_Broken, PH_PickupBoard, PH_Table, PH_Hand, PH_Wall, PH_Floor 등.

## ConfigTable 키
수치는 코드에 fallback으로 HTML판 값을 넣는다. 인물 수치: Bal.F("MoveSpeed",1.15f) = Elder_MoveSpeed. 공통: Nunchi_, Kiosk_, Bus_, Queue_ 접두어. 각 개발 담당은 쓴 키를 `Docs/keys_<담당>.csv`에 시트 헤더 순서(ConfigKey,Description,ValueType,Value,Unit,BalanceIntent)로 적는다. 문서 담당이 `Docs/ConfigTable.csv`로 합친다.

## 디버그 키 (에디터, 개발 빌드만)
F1 표시, F2 다음 챕터, F3 이전 챕터, F5 키오스크로(hasKiosk 챕터), F6 눈치 100, F7 ConfigTableLoader.Load().

## 챕터 추가 절차
맨 앞이나 중간에 아들 챕터를 넣을 때 하는 일.
| 일 | 어디 |
|---|---|
| Son.asset 만들기 | Assets/Graybox/Data, keyPrefix Son_, speakerKey son |
| 목록 항목 추가 | ChapterFlow.chapters (씬 이름, 프로필, 시작 지점 id) |
| 씬 파일 | Systems 인스턴스, PlayerSpawn, Global Volume, 조명 |
| Build Settings 등록 | 빠지면 ChapterFlow가 경고하고 로드가 실패한다 |
| 진행 | 전용 Director, 또는 PlainChapter(암전 풀기, 조작 넘기기, exit Interactable로 CompleteChapter) |
| 시트 키 | Son_MoveSpeed, Son_BackSpeedMul, Son_EyeHeight, Son_StepStride, Son_BobRate, Son_BobHeight, Son_LimpRoll, Son_LimpSway, Son_KioskEye, Son_KioskEyeDown, Son_DoorStepSpeed, Son_PushedAsideSpeed, Son_PushedBackSpeed, Son_ExitWalkSpeed, Son_CaneEverySteps, Son_BreathEverySteps. 없으면 노인 fallback으로 조용히 동작한다 |
| 음성 | Resources/Audio/vo의 son_ 접두어 파일. 코드는 speakerKey + "_이름"으로 부른다 |
| 조작하지 않는 화자 | CharacterProfile(id, displayName, speakerKey만)을 ChapterFlow.speakers에 넣는다 |

제목 화면은 chapterIndex 0 진입 때 GameState가 띄우므로 맨 앞이 무엇이든 맞다. 씬 코드는 시작 때 Hud.TitleOpen이 꺼질 때까지 기다린다.

## 인물 전제의 범위
- Home, Street, Storefront, Store의 Director는 노인 전용 씬이다. 음성 키는 speakerKey를 따르지만 대사 문구는 노인 말투 상수이다. 아들이 이 씬을 재사용하면 대사는 Director 수정이 필요하다. 키오스크의 CallStaff, 카드 대사, NunchiLines도 같다.
- 소지품은 ItemId 3종의 부분집합까지만 데이터이다. Memo, Lens, Card가 없는 인물은 Home 메모 장면, Street 돋보기 단계, 키오스크 카드 들기를 건너뛴다. 휴대폰 같은 새 물건은 enum, Hud.ItemName, HandRig 코드가 필요하다. HUD 칸은 4개이고 표시 숫자는 ItemId 값이다.
- 영수증은 소지품이 아니다. 돋보기와 같이 써야 하므로 StoreDirector의 4번 키로 따로 다룬다.
- 같은 씬을 두 챕터가 쓰면 그 씬에서 바로 시작할 때 앞 챕터로 잡힌다(ChapterFlow 경고).
- 결과 화면은 노인 주문 목표와 문구를 고정으로 쓴다. RunStats는 인물 구분 없이 합산되고 걸린 시간은 제목 뒤부터 StoreDirector의 받기까지이다. Store 뒤에 챕터를 붙이면 그 구간은 시간에서 빠진다.
- 시험 코드 KioskBotFixture는 씬 이름 Store와 kioskNunchi true를 전제한다.

## 시야 번짐
프로필 visionBlur는 두 가지를 켠다. Readable이 렌즈 없이 번진 글을 보여 주는 것과 자체 후처리의 평온 단계 번짐(Post_BlurCenterCalm, Post_BlurEdgeCalm)이다. 눈치로 늘어나는 번짐은 그 위에 더해지고 프로필과 무관하다. visionBlur가 false인 인물은 글이 늘 또렷하고, 조준만으로 onRead가 온다.

## 화면 후처리
Assets/Graybox/Post의 KioskPostFeature(ScriptableRendererFeature, Render Graph)를 PC_Renderer와 Mobile_Renderer에 등록해 쓴다. URP 기본 Vignette, Film Grain, Depth Of Field, Color Adjustments override는 꺼 두고 Bloom만 쓴다.
게임 코드는 PostState로만 값을 넘긴다: Nunchi(시야가 따라갈 눈치 값), HeartTime(심장 소리 재생 위치), Lens(돋보기 뷰포트 위치와 반지름). 수치는 전부 Post_ 키이고 목록은 Docs/keys_Post.csv이다.
패스는 번짐이 필요할 때 1/2, 1/4, 1/8, 1/16로 내리고 1/4까지 올리는 Dual Kawase 6회와 전체 해상도 합성 1회, 필요 없으면 합성 1회뿐이다. 합성이 번짐, 색수차, 탈색, 딤, 테두리 쉐도우, 그레인을 한 번에 그린다. 카메라 Post Processing이 꺼진 카메라(키오스크 RT 카메라)는 지나간다.
테두리 쉐도우는 둥근 사각형 거리장이다. 두께와 세기는 눈치 단계별 키(Calm, Heart, Tremble, Ring, Max)로 시트에서 고치고 단계 경계는 Nunchi_HeartAt, TrembleAt, RingAt, Max를 따른다. Nunchi_HeartAt 위로는 heartbeat.mp3 박동에 맞춰 수축한다.
Readable의 번진 쪽 줄은 Graybox/SmudgeText 재질(Post/Smudge_Dark, Smudge_Light)의 얇은 Cube이다. 글자 정보가 없어 어떤 거리에서도 읽히지 않는다. 호출 전광판은 번진 쪽 글자를 끄고 얼룩 줄만 둔다.

## 돋보기
Player/Eye/LensEye 카메라가 돋보기를 든 동안만 RT_Lens(512)로 원 방향을 Lens_Zoom배 확대해 그리고, 후처리 합성이 손 모델 원(Hand_Lens Rim, Lens_Radius) 자리에 그 그림을 넣는다. 키오스크와 월드 글이 같은 길을 쓴다.
레이어: LensSharp(본 카메라에서 제외), LensBlurred(LensEye에서 제외), HandModel(LensEye에서 제외). Readable은 시작 때 sharp와 blurred 자식을 이 레이어로 옮기므로 배치할 일이 없다. sharp와 blurred는 켜 둔 채 두고, 읽기 판정은 sharp 표시 대신 Readable.Seen을 본다.
판정은 원 가운데 광선이 먼저이고 없으면 원 안쪽 6점을 본다. onRead는 조준 시작 때 한 번 온다. 화면 쿼드는 _LensView 전역값이 1인 카메라에 RT_Sharp를, 그 밖에는 RT_Base 번짐을 그린다.

## 폰트
손글씨는 메모에만 쓴다. Assets/Fonts에 부산단디 ttf 원본과 TMP 폰트 에셋 BusanDandiHandwriting SDF가 있고, Atlas Population Mode Dynamic, Multi Atlas, Clear Dynamic Data On Build이다.
HUD 글자는 Assets/UI/Fonts/Hud_MalgunOS SDF.asset을 쓴다. Atlas Population Mode Dynamic OS라 프로젝트에 폰트 파일 없이 실행 중 OS의 Malgun Gothic에서 글자를 그린다. 같은 방식으로 Multi Atlas, Clear Dynamic Data On Build이다.
| 글자 | 폰트 |
|---|---|
| 메모: Hand_Memo | 부산단디 손글씨 |
| HUD: Subs, Prompt, Views, Items, 눈치 라벨, Title, Result | 맑은 고딕 (Hud_MalgunOS SDF) |
| 기계와 인쇄물: 키오스크 화면, BIS, 호출판, 영수증, 간판, 스티커 | 바꾸지 않는다 |

자막 외곽선은 Hud_MalgunOS SDF Outline 재질이다. 대사와 목표는 같은 Subs 글자를 쓴다. TMP는 한글을 글자 단위로 끊으므로 넘치는 자막은 Hud가 줄 길이가 고른 띄어쓰기에서 직접 끊는다.
키오스크 쪽 TMP 글자는 Assets/UI/Fonts/Store_KoreanSDF.asset(정적 아틀라스, 맑은 고딕에서 구움, 스크립트에 쓰인 한글 전체와 ASCII)을 쓴다. 정적이라 실행 중 OS 폰트를 찾지 않는다. 새 문구에 없는 글자가 있으면 아틀라스를 다시 구워야 한다. 키오스크 화면 Legacy Text, BIS, 호출판 외 인쇄물과 HUD Debug는 OS 폰트 대체에 기댄다.

## 모델 교체 규격
모델은 각 프리팹의 Visual 아래에 넣는다. 크기는 미터, 앞면은 표에 적은 방향이다.
| 프리팹 | 피벗 | 앞면 | 치수 x y z | 맞춰야 할 기능 오브젝트 |
|---|---|---|---|---|
| PH_NPC | 바닥 중앙 | +Z | 0.46 x 1.71 x 0.34 | HeadPivot y 1.58, BagAnchor (0.32, 0.72, 0), 모델은 ReactPivot 아래 Visual |
| PH_Bus | 바닥 중앙 | 진행 +X, 문 -Z | 10.9 x 3.05 x 2.5 | DoorLeafA, B z -1.29, PlateAnchor (0, 2.75, -1.27)가 측면 바로 앞이어야 함 |
| PH_Kiosk | 바닥 중앙 | -Z | 0.6 x 1.9 x 0.11 | ScreenQuad z -0.057 (0.42 x 0.7467), Plate z -0.0586, Slot 콜라이더 z -0.065, 앞면 기준 z -0.055, Cover 경첩 x 0.326은 본체 밖 |
| PH_Kiosk_Broken | 바닥 중앙 | -Z | 0.6 x 1.9 x 0.11 | Notice z -0.0605 |
| PH_BIS | 바닥 중앙 | 양면 X | 0.14 x 3.1 x 1.6 | BisFaceA x -0.075, BisFaceB x 0.075 (Panel 두께 0.14 기준). Blurred의 Row 메시는 번진 글자라 Visual 밖에 둔다 |
| PH_PickupBoard | 판 중심 | +X | 0.08 x 0.62 x 1.31 | Blurred, Sharp x 0.05 |
| PH_Counter | 앞면 | +X | 0.76 x 1.0 x 5.94 | Bound_Counter |
| PH_Door_Glass | 경첩 | -Z | 0.93 x 2.28 x 0.05 | DoorPivot, Sticker_Pull |
| PH_Door_Home | 문 아래 중앙 | -Z | 1.08 x 2.12 x 0.12 | Hinge x -0.46 |
| PH_Car | 바닥 중앙 | 진행 +X | 4.4 x 1.45 x 1.8 | 씬 인스턴스 루트에 TrafficMover, Visual이 켜고 꺼짐 |
| PH_Scooter | 바닥 중앙 | 진행 +X | 1.8 x 1.72 x 0.6 (탄 사람 포함) | 씬 인스턴스 루트에 TrafficMover, Visual이 켜고 꺼짐 |
| PH_Floor | 윗면 중앙, 루트 스케일로 크기 | | | 건물 구조 전용, 소품에 쓰지 않음 |
| PH_Wall | 바닥 중앙, 루트 스케일로 크기 | | | 건물 구조 전용, 소품에 쓰지 않음 |
| PH_Seat, PH_Booth, PH_KitchenBench, PH_Fryer, PH_Hood, PH_Bulkhead, PH_PickupStand, PH_ShoeCabinet, PH_Cane, PH_Bulb, PH_Rail, PH_Curb, PH_BusStopSign | 바닥 중앙, 루트 스케일 1 | | BoxCollider size가 크기 | PH_Rail은 Rail_E만 길이 오버라이드 |
| Hand_Card, Card | 카드 중심 | | 0.085 x 0.054 x 0.002 | 두 곳 축이 같다. Card/Visual 회전이 틈 방향을 맞춘다 |

물체에 속한 Bound와 앵커는 그 물체의 자식이다(Bound_Kiosk, Bound_KioskBroken, Bound_Counter, Bound_Booth, Bound_Table, Anchor_KioskStand, Anchor_KioskLook, Anchor_PickupLook, Anchor_Board, Anchor_DoorHandle, Anchor_DoorLook, Interact_DoorPush, Interact_DoorPull). 씬의 Bounds에는 방 경계만 남는다. PH_Kiosk 프리팹 단독에서 비는 참조는 씬에서 연결하는 세 개뿐이다(KioskController.queue, staffAnchor, NunchiSystem.queue).
