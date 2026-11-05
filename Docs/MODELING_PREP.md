# 모델링 사전 준비

노션 기획서를 기준으로 무엇을 재활용하고 무엇을 새로 만들지, 네 대가 겹치지 않게 어떻게 일할지 정리한 문서입니다.

- 기준: 친구 커밋 a607539 위의 저장소, 2026-11-06 01:38 노션 동기화본입니다.
- 우선순위: 플레이 시트, 실물 프리팹과 코드, 모델링목록.md, Docs/ROUND_PLAN.md 순입니다. ROUND_PLAN 은 기획 갱신 전 문서라서 3회차가 남아 있고, "모델링 제외"는 그레이박스 때의 범위입니다.
- 회차는 1(20대 버스와 버거집), 2(40대 카페), 4(80대 버거집과 버스), 엔딩입니다. 3회차 영화관은 빠졌습니다.
- CLAUDE.md 와 메모리는 다른 컴퓨터에 없습니다. 다른 컴퓨터는 이 문서가 규칙입니다.

## 1. 요약

- 모델 155개가 이미 있습니다. 그런데 Assets/Graybox/PH 프리팹에는 FBX 가 하나도 들어가 있지 않습니다. 지금 R 씬이 회색인 이유는 모델이 없어서가 아니라 넣지 않아서입니다.
- 3절의 78개 항목 중 45개는 모델링 없이 끝납니다. 고치는 것이 19개, 새로 만드는 것이 14개입니다.
- 거리, 정류장, 버거집은 새로 만들 것이 거의 없습니다. 새 모델링은 손과 소지품, 카페, 엔딩 소품에 몰려 있습니다.
- 스크립트 한 번은 수 초에서 1분입니다. 시간은 모델링보다 정확한 자리에 넣는 일에 듭니다.

| 판정 | 뜻 | 항목 수 |
|---|---|---|
| 그대로 | 모델과 PH_Map 행이 있습니다. 메뉴만 돌리면 들어갑니다 | 24 |
| 행 추가 | 모델이 있습니다. 맵 행만 더합니다 | 1 |
| 배치 | 모델이 있습니다. 배경 프리팹이나 씬 오브젝트 아래에 놓습니다 | 15 |
| 색만 | 메시는 두고 재질이나 텍스처만 바꿉니다 | 5 |
| 고침 | 기존 스크립트를 고쳐 다시 내보냅니다 | 19 |
| 새로 | 새 스크립트로 만듭니다. 복사할 재료 코드는 적어 두었습니다 | 14 |

급은 시간이 모자랄 때 뺄 순서입니다. 핵심은 코앞에서 보거나 조작하는 것, 보통은 눈에 띄는 배경, 나중은 빼도 게임이 성립하는 것입니다.

## 2. 먼저 정할 것

기본값대로 진행해도 됩니다. 바꾸려면 작업 시작 전에 정합니다. 플레이 시트 기준 🔴 초안이거나 「남은 결정」에 있는 항목이라 사용자나 기획자가 정합니다.

| 번호 | 결정 | 기본값 | 바꾸면 달라지는 것 |
|---|---|---|---|
| D1 | 어디에 입힐지 | R 씬(Assets/Scenes, Assets/Graybox). 사본 Assets/JeongWoo 는 옛 흐름이라 기획을 담지 못합니다 | 사본에 입히면 이 문서의 씬 작업이 전부 바뀝니다 |
| D2 | 사람 모델 | 정적 메시(PH_NPC__*). 코드가 HeadPivot 을 돌리고 Animator 가 없어 수정이 필요 없습니다. 걸을 때 미끄러집니다 | 리깅으로 가면 NpcLook 과 고개 코드를 새로 짜야 합니다 |
| D3 | 손의 나이 | 피부까지 세 벌(Look_0, 1, 3) | 소매만 바꾸면 손 메시 하나로 끝납니다 |
| D4 | 물건을 든 손 | 80대만 쓰는 Hand_Lens, Hand_Bill 에는 손을 같이 굽습니다. Hand_Card, Hand_Wallet 은 물건만 보입니다 | Hand_Card, Hand_Wallet 에 손을 붙이면 HandRig 의 skins 를 고쳐야 합니다 |
| D5 | 시계 손목 | Look_3, Hand_Watch, 어르신 팔, 엔딩 손에 같은 시계를 씁니다. 한 화면에 같이 나오지 않습니다 | 코드 주석은 왼 손목, Look_3 과 어르신 팔은 오른팔입니다 |
| D6 | 버스 계단 | 앞문 안쪽 3단, 위 높이 0.6 | R1 앵커는 0.6, R4 는 0.9 입니다. 맞추려면 씬 값을 바꿉니다 |
| D7 | 버스 번호 | ROUND_PLAN T26 대로 세 대 모두 112 로 보입니다. 117, 172 는 기사 대사로만 나옵니다 | 표시하려면 CityBus_tex.route_sign 으로 텍스처 3벌을 만듭니다(Mac) |
| D8 | 집 문 자리 | 각 씬 그대로 둡니다(R1 은 골목 옆벽, Ending_Home 은 골목 끝) | 같은 길로 보이게 하려면 씬 구조를 바꿉니다 |
| D9 | E-1c 자세 | 시트는 바닥, 코드는 벽입니다. 펼친 손 모델 하나로 둘 다 됩니다 | 바닥으로 맞추려면 코드와 카메라를 고칩니다(친구 파일) |
| D10 | 1회차 캐릭터 몸(4-3) | 줄 맨 앞 PH_NPC 에 기존 모습을 정해 씁니다 | 성별을 정하지 않는 규칙과 부딪힙니다. 사용자 판단입니다 |
| D11 | 어르신 몸 | NpcOldMan 을 고친 NpcElder. 뒷모습 위주로 보입니다 | 수염과 안경이 앞에서 보입니다. 성별 규칙과 부딪힙니다 |
| D12 | 포스터 자리 | 화장실 문과 겹치므로 두 씬 모두 (0.75, 2.28) 로 옮기고 스케일 0.9 | 그대로 두면 문틀과 겹칩니다 |
| D13 | 친구 파일 수정 | 고치지 않습니다. R4StopDirector.ApplySky 에 안개 색이 없으니 R 씬에는 안개를 켜지 않습니다 | 안개를 쓰려면 ApplySky 와 QualitySettings 를 고칩니다 |
| D14 | 친구와 동시 작업 | 0단계와 씬 저장은 친구 작업이 멈춘 것을 확인하고 합니다. 친구는 Assets/Graybox, Assets/Scenes 를 수시로 크게 고칩니다 | 동시에 저장하면 한쪽 작업이 사라집니다 |
| D15 | 4회차 지팡이(01:38 기획 추가) | 모델만 먼저 만듭니다. PH_Hand 와 HandRig 에 지팡이 자리가 없어 1인칭으로 보이려면 친구 코드가 필요합니다. 어르신 NPC 에는 씬에서 붙입니다 | 「남은 결정」 4회차 지팡이 항목입니다. 지갑, 돋보기, 지폐를 쥐는 손을 어떻게 나눌지에 따라 손 모델이 달라집니다 |

## 3. 재활용 지도

플레이 시트 순서입니다. 묶음은 6절의 A, B, C, D 입니다. 경로는 프리팹 안 경로이고, 씬이라고 쓴 것은 프리팹이 아니라 씬에만 있는 오브젝트입니다.

글씨가 붙는 물건(스티커, 포스터, 안내문, 호출판, 전광판)은 글자를 텍스처에 굽지 않습니다. 코드가 Readable 의 Blurred, Sharp 로 흐림과 또렷함을 바꾸므로, 구우면 80대에도 그대로 읽혀 "같은 글씨, 다른 눈" 규칙이 깨집니다. 모델은 빈 판으로 만듭니다.

### 3.1 손과 소지품 (전 회차, PH_Hand)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 20대 손과 소매 | 1회차 | 고침 | 핵심 | GrandpaHand_R Point 자세, PH/hand.py pointer() | Hand_Pointer/Look_0 | A |
| 40대 손과 소매 | 2회차 | 고침 | 핵심 | 같음 | Hand_Pointer/Look_1 | A |
| 80대 손, 소매, 반지, 시계 | 4-3, 4회차 | 고침 | 핵심 | 같음. 반지는 ik.torus | Hand_Pointer/Look_3 | A |
| 돋보기 | 4-0, 4-2, 4-4, 4-12, 4-21 | 그대로 | 핵심 | PH_Hand__Lens | Hand_Lens/Visual | 0 |
| 카드 | 1-3, 1-8, 2-6 | 그대로 | 핵심 | PH_Hand__Card | Hand_Card/Visual | 0 |
| 펼친 지갑 | 2-6, 4-0, 4-20 | 새로 | 핵심 | Items/_ik.py box, P | Hand_Wallet/Visual | A |
| 지갑 칸의 카드 | 2-6 | 고침 | 핵심 | PH_Hand__Card 를 세워 다시 내보냄 | Hand_Wallet/Card_Part | A |
| 지갑 칸의 지폐 | 4-0, 4-10, 4-20 | 새로 | 핵심 | 지폐 모델 | Hand_Wallet/Cash_Part | A |
| 지갑 속 쪽지 | 4-0, 4-0a | 고침 | 핵심 | PH/hand.py memo() 크기 변경 | Hand_Wallet/Note/Visual | A |
| 지폐 | 1-6, 4-10, 4-21b | 새로 | 핵심 | ik.quad, ik.flat_img, tex2d.paper | Hand_Bill/Visual | A |
| 왼 손목과 시계 | 4-16, 4-18, 4-21b | 고침 | 핵심 | GrandpaHand_L 시계. 바늘과 "토 15" 요일창을 뺌 | Hand_Watch/Visual | A |
| 시침 | 4-16, 4-18, 4-21b | 고침 | 핵심 | GrandpaHand.py:853-867 바늘 하나 | Hand_Watch/HourHand | A |
| 지팡이 쥔 오른손 | 4회차 머리글, 4-3 | 고침 | 보통 | GrandpaHand_R GripCane 자세, Items/Cane | 자리 없음(D15) | A |

1, 2회차 쪽지는 3D 가 아니라 HUD 패널입니다(NotePanel.prefab). 모델이 필요 없습니다.

### 3.2 1-0 골목 (R1_Stop)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 현관문 두 개 | 1-0 | 그대로 | 보통 | PH_Door_Home__Frame, __Leaf | Home_Door, Elder_Door 인스턴스 | 0 |
| 골목 바닥과 양옆 건물 | 1-0, E-1a | 배치 | 보통 | Layouts/Street.json(StreetRoadAlley, BuildingSalon 등) | Env_Street | B |

문은 x 2.54 이고 BuildingSalon 옆벽은 약 x 3.12 라 0.58 m 뜹니다. R1_Stop 에서만 건물을 x 쪽으로 약 0.52 옮깁니다(계산값이라 눈으로 확인합니다).

### 3.3 정류장과 버스 (R1_Stop, R4_Stop 공용)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 쉼터 | 1-1 | 그대로 | 보통 | PH_BusShelter | 프리팹 | 0 |
| 전광판 | 1-1, 4-11 | 그대로 | 핵심 | PH_BIS | 프리팹 | 0 |
| 안내판 빈 판 | 1-1, 4-13 | 새로 | 핵심 | PH/kiosk.py fit_notice 방식 | PH_Notice_Cashless/Visual | B |
| 안내판 기둥 | 1-1 | 색만 | 나중 | M_BusShelter_Frame | 씬 BusStop_Area/Notice_Pole | B |
| 버스 외부와 문 | 1-3, 4-15 | 그대로 | 핵심 | PH_Bus__Body, DoorA, DoorB | 프리팹 | 0 |
| 앞문 계단 | 1-3, 4-15, 4-17, 4-19 | 고침 | 핵심 | PH/bus.py 에 디딤판 추가 | PH_Bus__Body | B |
| 단말기 | 1-3, 4-19, 4-20a, 4-21 | 새로 | 핵심 | PH/bus_interior.py:304-307 | PH_BusTerminal/Visual | B |
| 버스 실내 | 1-3, 4-16 | 고침 | 보통 | x 3.5 기둥 단말기 삭제(누를 수 없는 단말기가 남음) | PH_BusInterior | B |
| 기사 | 4-16, 4-18, 4-19 | 그대로 | 보통 | PH_NPC look 0(OfficeMan). 앉은 자세는 선택 | 씬 Driver 의 look | B |
| 행인 | 1-2, 4-14 | 그대로 | 보통 | PH_NPC. 두 씬이 같은 look | 씬 Student 의 look | B |
| 차와 스쿠터 | 코드만 | 그대로 | 나중 | PH_Car, PH_Scooter | 프리팹 | 0 |
| 난간 | 코드만 | 그대로 | 나중 | PH_Rail. 메뉴 뒤 Rail_E 루트 X 스케일 0.941 | 프리팹 | 0 |
| 차도, 보도, 건너편 건물 | 1-1 | 배치 | 보통 | Layouts/Street.json | Env_Street | B |

### 3.4 버거집 앞 (R1_Storefront, R4_Storefront)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 유리문 | 1-4, 4-1, 4-2 | 그대로 | 핵심 | PH_Door_Glass__Leaf | 프리팹 | 0 |
| 앞면과 간판 | 1-4 | 그대로 | 보통 | PH_Storefront | 프리팹 | 0 |
| 정류장 표지 | 1-3a | 그대로 | 나중 | PH_BusStopSign | 프리팹 | 0 |
| 연석 | 1-4 | 그대로 | 나중 | PH_Curb | 프리팹 | 0 |
| 유리 너머 탁자와 손님 | 1-4 | 그대로 | 나중 | PH_Table, PH_NPC | 프리팹 | 0 |
| 유리 너머 매장 내부 | 1-4 | 배치 | 보통 | Layouts/Store.json | Env_StoreInterior | D |
| 이웃 건물과 길 | 1-4 | 배치 | 보통 | Layouts/Storefront.json | Env_Storefront | D |

"당기세요" 스티커는 프리팹 Sticker_Pull 의 글자라 모델 일이 없습니다. R 씬은 Single 로드라서 사본처럼 매장 씬을 겹쳐 보여 줄 수 없습니다. 그래서 내부 배경을 앞 씬에도 넣습니다.

### 3.5 버거집 안 (R1_Store, R4_Store)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 키오스크 본체, 날개, 덮개 | 1-7, 1-8, 4-3 | 행 추가 | 핵심 | PH_Kiosk__Body, WingL, WingR, Cover | PH_Kiosk_R4 | D |
| 구운 "카드 전용" 띠 제거 | 4-3 | 고침 | 핵심 | PH/kiosk.py:134 의 sticker 조건 삭제 | PH_Kiosk__Body, PH_Kiosk_Broken | D |
| "카드 전용" 스티커 판 | 1-7, 4-3 | 색만 | 핵심 | 회색 판 0.16x0.06 재질 | Sticker_CardOnly/Visual | D |
| 벽 포스터 빈 판 | 1-7, 4-3 | 고침 | 핵심 | store_tex.py 글자 없는 인쇄면, StorePosters 프레임 | PH_Poster/Visual | D |
| 앞 어르신 몸 | 1-5, 1-6 | 고침 | 핵심 | NpcOldMan 복사, 옷과 시계 변경, 팔 삭제 | PH_NPC 새 look | D |
| 어르신 팔과 지폐 | 1-6 | 고침 | 핵심 | GrandpaHand 정적. 지폐는 묶음 A | 씬 Arm_Pivot/Visual, Bill/Visual | D |
| 어르신 지팡이 | 1-5, 4-3 | 배치 | 보통 | PH_Cane | 씬 NPC_Elder 자식, R4_Stop Walker 도 같게 | D |
| 줄 손님, 구경하는 손님 | 1-5, 1-6 | 그대로 | 보통 | PH_NPC look 0~7 | 인스턴스마다 look | D |
| 알바생 | 1-7, 1-9 | 그대로 | 보통 | PH_NPC look 8 | 씬 NPC_Staff 의 look | D |
| 호출판, 받침, 봉투, 컵 | 1-10 | 그대로 | 보통 | PH_PickupBoard, PH_PickupStand, PH_Bag, __Cup | 프리팹 | 0 |
| 카운터, 벽체, 주방 | 1-7 | 그대로 | 보통 | PH_Counter, Bulkhead, KitchenBench, Fryer, Hood | 프리팹 | 0 |
| 탁자, 의자, 부스 | 1-11 | 그대로 | 나중 | PH_Table, PH_Seat, PH_Booth | 프리팹 | 0 |
| 고장 키오스크 | 코드만 | 그대로 | 나중 | PH_Kiosk_Broken | 프리팹 | 0 |
| 벽, 바닥, 천장, 소품 | 1-5 | 배치 | 보통 | Layouts/Store.json | Env_StoreInterior | D |

### 3.6 카페 (R2_Cafe)

R2_Cafe 는 a607539 에서 새 공간이 됐습니다. 방은 안쪽 7.7 x 6.9 m 로 StoreShell(11.5 x 8 m)을 쓸 수 없습니다.

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 키오스크 | 2-2, 2-3, 2-6 | 색만 | 핵심 | 같은 메시, 간판 PNG, 포스터 아틀라스(kiosk_tex.py) | PH_Kiosk | C |
| 커피 2잔과 캐리어 | 2-8 | 새로 | 핵심 | FoodDrinkCup.py:60-81 컵 프로필, M_Glass 몸통 | PH_CoffeeCups | C |
| 바 카운터 | 2-5, 2-8 | 고침 | 핵심 | store_counter.py:11-61 | PH_BarCounter | C |
| 방 벽, 바닥, 천장 | 2-1 | 새로 | 보통 | store_shell.py W(), tint_copy, 7.2절 타일 | Env_Cafe | C |
| 카페 앞면과 차양 | 2-1 | 새로 | 보통 | sf.box2, bld.awning(bld.py:697) | PH_CafeFront | C |
| 뒤 선반 | 코드만 | 새로 | 보통 | store_kitchen.py:170 | PH_BackShelf | C |
| 커피 머신 | 코드만 | 새로 | 보통 | store_kitchen.py:261 디스펜서 | PH_BackShelf 의 Machine 자리 | C |
| 진열장, 케이크, 빵 | 코드만 | 새로 | 보통 | storelib boxz, 유리 재질 | PH_Showcase | C |
| 카페 직원 | 2-5 | 색만 | 보통 | NpcStaff 아틀라스의 빨강과 로고 교체(미시험), 안 되면 스크립트 고침 | PH_NPC 새 look | D |
| 유리문, 호출판, 받침, 의자 | 2-1, 2-7, 2-8 | 그대로 | 보통 | PH_Door_Glass, PH_PickupBoard, PH_PickupStand, PH_Seat | 프리팹 | 0 |
| 줄 손님 | 2회차 | 그대로 | 보통 | PH_NPC | 프리팹 | 0 |
| 작은 둥근 탁자 | 코드만 | 고침 | 나중 | PH/table.py 를 복사해 원판 추가 | PH_CafeTable | C |
| 사무 빌딩 | 2-1 | 새로 | 나중 | BuildingBackdrop.py 패턴, 굽기 없음 | PH_OfficeBlock | C |
| 가로수 | 2-1 | 새로 | 나중 | 재료 없음. 줄기와 잎 덩어리 | PH_StreetTree | C |
| 차도, 횡단보도, 보도, 연석 | 2-1 | 배치 | 나중 | StreetRoad, StreetRoadCrosswalk, StreetSidewalk, StreetCurb | Env_Cafe | C |

PH_Curb, PH_Rail, PH_OfficeBlock 인스턴스는 스케일로 크기를 만들어서 모델을 넣으면 찌그러집니다. 길은 프리팹 교체 대신 Env_Cafe 로 놓고 회색 Visual 을 끕니다.

### 3.7 4회차 버거집 (1회차와 다른 것만)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 바라보는 사람들 | 4-10b | 배치 | 핵심 | PH_NPC 와 같은 모델. HeadPivot 이름 유지 | 씬 Watcher0~4 | D |
| 지나가는 쟁반 | 4-10a, 실패 | 배치 | 보통 | FoodTray, FoodBulgogiBurger, FoodFries, FoodDrinkCup_Cola(소켓 있음) | 씬 Tray_Pass/Visual | D |
| 알바생 휴대폰 | 4-7 | 배치 | 나중 | NpcSmartphone | 씬 NPC_Staff | D |

### 3.8 4회차 정류장 (R1 과 다른 것만)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 세 번째 버스 | 4-19, 4-21b | 배치 | 핵심 | PH_Bus__Body, DoorA, DoorB | 씬 Buses/Bus3 | B |
| 어르신 뒷모습 | E-1 | 배치 | 핵심 | 어르신 몸(묶음 D) | 씬 Npcs/Walker | B |
| 가로등 | 머리글, 4-21b | 고침 | 보통 | Street/street_light.py 렌즈 분리, 꺼진 재질 | 씬 Lamps/Lamp0~2 | B |

저녁 장면은 코드가 조명과 하늘 색을 바꿉니다. 저녁용 모델은 없습니다. 가로등 Light 는 지우면 안 되고 모델 높이(7.2 m)에 맞게 옮깁니다.

### 3.9 엔딩 (Ending_Home)

| 물건 | 시트 | 판정 | 급 | 재료 | 넣을 곳 | 묶음 |
|---|---|---|---|---|---|---|
| 쪽지 쥔 오른손 | E-1a, E-1b | 고침 | 핵심 | GrandpaHand_R HoldMemo 자세 | 씬 End_HandR/Visual | A |
| 짚는 왼손 | E-1c | 고침 | 핵심 | GrandpaHand_L, POSES 에 펼친 자세 추가 | 씬 End_HandL/Visual | A |
| 구겨진 쪽지 | E-1b, E-1c | 새로 | 핵심 | 지름 약 0.06, M_Memo_Sheet 재질 | 씬 Note_Ball | A |
| 펼친 쪽지 | E-1a | 색만 | 보통 | 메시 유지, 재질만. 스케일이 0.085x0.13x0.001 이라 자식을 달면 찌그러집니다 | 씬 Note_Flat | D |
| 현관 안 | E-1b, E-1c | 배치 | 핵심 | HomeEntry, HomeUmbrella, HomeMedicineBag. Room 치수가 일치합니다 | Env_Home | D |
| 현관문, 신발장, 전구, 지팡이 | E-1b | 그대로 | 보통 | PH_Door_Home, PH_ShoeCabinet, PH_Bulb, PH_Cane | 프리팹 | 0 |
| 밤 골목 | E-1a | 배치 | 보통 | Street.json 의 골목 항목. y -8 모듈과 CarHatch 는 뺌 | Env_Home | D |
| 가로등 | E-1a | 배치 | 나중 | StreetLight | 씬 Lamp_Mid, Lamp_Far | D |

HomeCorridor 는 5층 복도라 쓸 수 없습니다. 집 앞 벽 HouseFront 는 해당 모델이 없고 밤에 짧게 보여서 PH_Wall 그대로 둡니다.

### 3.10 만들지 않는 것

영화관과 Look_2, PH_ShoeRack(어느 씬에도 없음), 영수증(코드 참조 없음), FoodPager, 1, 2회차 3D 쪽지, Hand_Memo(자리 없음), HomeCorridor 입니다. R3_Cinema 는 빌드와 흐름에서 빠졌으니 입히지 않습니다.

## 4. 같은 모습이어야 하는 복사본

프리팹 하나를 고쳐도 아래 복사본은 안 바뀝니다. 재질 이름을 공유해 한 벌로 맞춥니다.

| 물건 | 복사본 | 근거 |
|---|---|---|
| 어르신 소매, 반지, 시계, 지팡이 | Look_3, Hand_Watch, R1_Store Arm_Pivot, Ending_Home End_HandR, End_HandL, 어르신 몸 | 1-5 와 4-3 이 같은 사람입니다. 지금 NpcOldMan 은 빨강 소매와 금색 시계, GrandpaHand 는 갈색 뜨개와 스틸 시계라 다릅니다 |
| 어르신 몸 | R1_Store NPC_Elder, R4_Stop Walker | 1-6 과 E-1 이 같은 구도입니다 |
| 지폐 | Hand_Bill, Cash_Part, Arm_Pivot/Bill | 1-6 과 4-10a 가 같은 장면입니다 |
| 쪽지 | Hand_Wallet/Note, Note_Flat, Note_Ball | 같은 쪽지입니다 |
| 버스 | PH_Bus 인스턴스, R4_Stop Bus3 | 같은 차종입니다 |
| 키오스크 | PH_Kiosk(R2), PH_Kiosk_R4(R1, R4), PH_Kiosk_Broken | 스티커 자리가 같습니다 |
| 안내문 | 정류장 PH_Notice_Cashless, PH_BusTerminal 안 중첩 | 1-3 과 4-21 이 같은 안내문입니다 |
| 사람 | PH_NPC 인스턴스, R4_Store Watcher0~4 | 4-10b 입니다 |
| 골목 | R1_Stop, Ending_Home | 1-0 과 E-1a 가 같은 길입니다 |

## 5. 새로 만들거나 고치는 것의 규격

크기는 회색 자리 실측입니다(m). 모두 정적 메시입니다. Assets/Scripts 에 Animator 가 없고 손은 뼈대가 필요 없습니다. 앞면은 특별한 말이 없으면 Unity -Z 입니다.

### 손과 소지품

- Hand_Pointer 는 +Y 가 손가락 방향이고 손끝은 Tip (0, 0.09, 0) 입니다. Tip 은 옮기지 않습니다.
- 소매 끝은 로컬 y -0.8 까지 늘립니다. 지금 모델은 -0.085 에서 잘려 화면 가운데에서 끝이 보입니다. 소매만 단순 원통으로 늘려도 됩니다.
- 나이 인자는 GrandpaHand.py 에 K3D_HAND_AGE 를 더해 넣습니다. 고칠 곳은 14-16행(이름), 229행(마디 변형), 473-548행(피부), 550-590행(손톱), 662-663행(타일 이름)입니다. 기본값 80 이면 기존 결과가 유지됩니다.
- Look_N 행에는 look 필드를 넣지 않습니다. 넣으면 모델이 꺼집니다.
- Card_Part, Cash_Part 는 target 을 부모로 씁니다(Hand_Wallet/Card_Part). 메시가 Visual 자체라서 Visual 을 target 으로 하면 스케일을 물려받습니다.
- 지갑 칸 위치는 x -0.055, 0, 0.055 입니다. 코드가 이 자리를 화면에 투영해 클릭을 판정합니다.

| 모델 | 크기 | 원점과 깊이 |
|---|---|---|
| 지갑 | 0.17 x 0.1 x 0.01 | 앞면 z +0.001. 펼친 모양 한 벌이면 됩니다 |
| 지갑 카드 | 0.05 x 0.075 x 0.003 | 칸 중심, 앞면 z -0.0015 |
| 지갑 지폐 | 0.05 x 0.085 x 0.003 | 칸 중심, 앞면 z -0.0015 |
| 지갑 쪽지 종이 | 0.05 x 0.08 x 0.002 | 앞면 z -0.001. 글자 Text z -0.003 보다 뒤 |
| 지폐 | 0.13 x 0.06 x 0.001 | 중심. 가상 도안 |
| 시계 팔 | Dial 0.05, 팔은 y -0.25 까지 | 원점 문자판 중심. 문자판 앞면 z -0.003, 시침보다 뒤 |
| 시침 | 0.004 x 0.022 x 0.001 | 원점 회전축, +Y 가 12시, z -0.004. 숫자 없는 문자판 |
| 반지 | 0.024 x 0.008 x 0.024 | y 0.03 부근 |
| 어르신 팔 | 어깨부터 손끝 약 0.64 | Arm_Pivot 기준. GrandpaHand 는 0.515 라 소매 상수로 맞춤 |

Hand_Lens 에 손을 구울 때는 렌즈 원 밖에 둡니다. 원 안은 후처리가 덮습니다.

### 버스와 정류장

| 모델 | 크기와 자리 | 주의 |
|---|---|---|
| 앞문 계단 | 버스 로컬 x 4.0~5.0, z -1.19 에서 안쪽 | 저상 바닥이라 지금 계단이 없습니다. bus.py 는 굽기가 없어 단색 재질로 됩니다. x 를 4.0 부터 시작해야 단말기 봉을 피합니다 |
| PH_BusTerminal | 단말 0.16 x 0.22 x 0.07, 봉 지름 0.04 높이 2.32, 카드 면 0.12 x 0.15 위로 35도 | 루트는 안내문 뒤, 봉 x 0.24, 단말 중심 바닥 위 1.2 |
| PH_Notice_Cashless 판 | 0.42 x 0.3 x 0.01 | 앞면 z 0~+0.001, 두께는 +Z. PH_BusTerminal 의 중첩 안내문은 칸막이 면 뒤로 1 mm 묻힙니다. 중첩 z 를 0.03 에서 0.02 로 당깁니다 |

### 버거집

| 모델 | 크기와 자리 | 주의 |
|---|---|---|
| PH_Poster 판 | 0.7 x 1.0 x 0.01, 앞면 z 0~+0.001 | StorePosters_Kiosk 외곽은 0.634 x 0.881 입니다. 빈 인쇄면으로 다시 만듭니다. poster_kiosk 의 "현금 결제 불가" 문구도 뺍니다 |
| Sticker_CardOnly 판 | 0.16 x 0.06 x 0.01 | 재질만 입힙니다 |

PH_Kiosk_R4 행은 PH_Kiosk 행(Visual, Wing_L/Visual, Wing_R/Visual, 빈 행들)을 복사하고 Cover/Hinge/Visual 에 PH_Kiosk__Cover 를 더합니다. Card/Visual 은 자리가 없습니다.

### 카페 (실측 크기, 모델링목록과 다른 값은 실측이 맞습니다)

| 프리팹 | 크기 x, y, z | 주의 |
|---|---|---|
| PH_BarCounter | 5.4 x 1.06 x 0.785 | store_counter.py 는 TOP 1.055 로 높이가 맞습니다. L 5.3, 빨강을 갈색으로, 픽업 구간 삭제 |
| PH_Showcase | 1.54 x 0.585 x 0.6 | 바 위 |
| PH_BackShelf | 4.4 x 2.36 x 0.33 | Machine 자리 0.62 x 0.36 x 0.3 |
| PH_CafeTable | 0.64 x 0.735 x 0.64 | 둥근 탁자 |
| PH_CafeFront | 7.8 x 3.3 x 1.15 | x 0.45~1.38 은 문 자리라 비웁니다. Sign z -0.145 앞에 메시를 두지 않습니다. Col_L, Col_R, Col_Top, Sign 유지 |
| PH_OfficeBlock | 16 x 30 x 12.85 | 인스턴스 스케일 0.52~1.2 |
| PH_StreetTree | 2.95 x 5.1 x 2.6 | StorePlant 는 화분이 한 메시라 못 씁니다 |
| PH_CoffeeCups | 0.26 x 0.26 x 0.14 | 불투명 종이컵이면 얼음과 커피가 안 보여 투명 컵입니다. 코드는 루트를 켜고 끕니다 |

카페 키오스크는 Visual/Sign 을 씬이 끄고 있는데 모델이 간판을 합치면 그 끄기가 사라집니다. 버거대왕 간판과 포스터가 보이지 않게 PH/kiosk_cafe.py 를 새로 만들어 Body 를 카페용으로 내보내고, PH_Map_Cafe.json 에서 PH_Kiosk 의 Visual, Wing_L/Visual, Wing_R/Visual 을 빈 행으로 지운 뒤 새 모델을 넣습니다.

## 6. 작업 묶음

파일이 겹치지 않게 나눈 단위입니다. 네 대에 배정할 때 이 표를 씁니다. 소유 파일 밖은 고치지 않습니다.

| 묶음 | 내용 | 맵 파일 | 프리팹 | 씬 | 주로 고치는 스크립트 |
|---|---|---|---|---|---|
| 0단계 | 기존 모델 넣기. 한 대가 맨 처음 합니다 | PH_Map.json(고치지 않음) | PH 프리팹 31개 | 없음 | 없음 |
| A 손과 소지품 | 3.1, 3.9 의 손과 쪽지, 지폐 | PH_Map_Hand.json | PH_Hand | 없음(엔딩 손 모델은 D 가 씬에 넣음) | PH/hand.py, Hands/, 새 Items/ |
| B 버스와 정류장 | 3.2, 3.3, 3.8 | PH_Map_Bus.json | PH_Bus, PH_BusInterior, PH_BusTerminal, PH_Notice_Cashless | R1_Stop, R4_Stop | PH/bus*.py, Street/street_light.py |
| C 카페 | 3.6 | PH_Map_Cafe.json | PH_Kiosk, 카페 10종 | R2_Cafe | 새 PH/cafe_*.py, PH/kiosk_cafe.py, 새 Food/ |
| D 버거집, 사람, 엔딩 | 3.4, 3.5, 3.7, 3.9 | PH_Map_Store.json | PH_Kiosk_R4, PH_Kiosk_Broken, PH_Poster, PH_NPC | R1_Storefront, R4_Storefront, R1_Store, R4_Store, Ending_Home | PH/kiosk.py, PH/npc.py, Characters/, Store/ |

순서입니다.

1. 0단계를 끝내고 push 합니다. 그동안 다른 컴퓨터는 Unity 첫 임포트를 돌리고 Blender 작업을 시작합니다. 프리팹 저장은 0단계를 pull 한 뒤에 합니다.
2. A, B, C, D 는 동시에 진행합니다. 에셋이 끝날 때마다 작게 push 합니다.
3. 의존은 세 곳입니다. 지폐와 손(A)이 나와야 D 가 어르신 팔과 엔딩 손을 씬에 넣습니다. 어르신 몸(D)이 나와야 B 가 Walker 를 넣습니다. 카페 직원 look 번호(D)가 나와야 C 가 씬에 지정합니다. 사람 모습은 PH_NPC 소유자인 D 만 더합니다. 먼저 끝나는 쪽이 push 하면 pull 합니다.
4. 마지막에 한 대가 씬 8개를 차례로 열어 경고와 분홍 재질이 없는지 봅니다. 플레이 시험은 사람이 합니다.

컴퓨터 배정 때 볼 사실입니다.

| 사실 | 배정에 주는 영향 |
|---|---|
| 정우맥(1번)만 원본 폰트가 전부 있고 Library 가 이미 있습니다 | 0단계와 마지막 점검에 맞습니다. 노션 동기화와 사본 작업도 이 컴퓨터만 합니다 |
| Apple 폰트를 쓰는 텍스처는 Windows 에서 다른 글꼴로 바뀝니다(10절) | Kiosk, CityBus, PH/bus, NpcStaff, GrandpaHand_L 문자판을 다시 만드는 일은 Mac 입니다. 그래서 B 는 Mac 에 둡니다 |
| 카페와 소지품은 새 에셋이라 폰트 제약이 없습니다 | C, A 는 Windows 에 맞습니다 |
| 세민맥(3번)은 메모리 16GB 입니다 | Unity 와 Blender 를 동시에 돌리지 않습니다. K3D_BAKE_SLOTS=2 로 줄입니다 |
| RTX 두 대는 OptiX 로 굽습니다 | 굽기가 많은 C 에 맞습니다. Windows 실행은 아직 검증하지 못했습니다(11절) |

## 7. 작업 방법

### 7.1 새 컴퓨터 준비

1. Unity Hub 로 6000.3.13f1 을 설치합니다. 다른 버전으로 열면 Packages 와 설정 파일이 바뀝니다.
2. Blender 5.2.x 를 설치합니다. .blend 가 5.2 형식입니다. Steam 판은 자동 업데이트를 끕니다.
3. 저장소를 받습니다. 폴더 이름은 TestHackKaTon 으로 둡니다.
4. Unity 로 한 번 열어 첫 임포트를 끝내고 닫습니다. 패키지를 받으므로 네트워크가 필요하고 Library 는 약 3.8 GB 입니다. 배치 모드를 쓰려면 Hub 로그인과 라이선스가 먼저입니다.
5. `blender -b --factory-startup --python ArtSource/Blender/scripts/setup.py` 를 돌립니다. 끝에 나오는 `k3d:` 줄에서 Pillow, 베이크 장치, 폰트 목록, Blender 버전을 봅니다.
6. `git status` 가 비어 있는지 봅니다. 6000.3.13f1 이면 그대로여야 합니다. 뭔가 바뀌어 있으면 9절을 따릅니다.

Blender 실행 파일 위치입니다.

| 설치 | 경로 |
|---|---|
| Mac Steam | ~/Library/Application Support/Steam/steamapps/common/Blender/Blender.app/Contents/MacOS/Blender |
| Mac 일반 | /Applications/Blender.app/Contents/MacOS/Blender |
| Windows 일반 | C:\Program Files\Blender Foundation\Blender 5.2\blender.exe |
| Windows Steam | C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe |

Unity 는 Mac /Applications/Unity/Hub/Editor/6000.3.13f1/Unity.app/Contents/MacOS/Unity, Windows C:\Program Files\Unity\Hub\Editor\6000.3.13f1\Editor\Unity.exe 입니다.

### 7.2 모델 하나 만드는 순서

1. 스크립트를 씁니다. 처음부터 만드는 새 PH 모델의 기본형입니다.

```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ph, bpy
k3d = ph.k3d

k3d.reset()
A = "PH_Showcase"
m = k3d.mat("M_tmp_Wood", (0.2, 0.12, 0.07), 0.5)   # 이름이 M_ 이면 bake 가 한 벌로 합칩니다
...                                                 # 미터, Blender 좌표(Z-up), 정면 -Y, 원점 바닥 중앙
o = ph.part(A, parts, ph.turn(180))                 # 앞 -Z 는 180, 앞 +Z 는 0, 앞 +X 는 -90
k3d.bake(o, size=1024)
ph.finish(A, o, notes="원점, 앞면, 특이사항")
k3d.preview(A, [o])
```

기존 모델에서 파생할 때는 PH/table.py 처럼 `ph.load("Store", "StoreTable")` 로 원본 .blend 를 엽니다. 자세를 굳힐 때는 `ph.posed()` 입니다.

2. 돌립니다. `--python-exit-code 1` 이 없으면 파이썬 오류가 나도 종료 코드가 0 입니다.

```
blender -b --factory-startup --python-exit-code 1 --python ArtSource/Blender/scripts/PH/showcase.py
blender -b --factory-startup --python ArtSource/Blender/scripts/k3d.py -- validate Assets/Art3D/Models/PH/PH_Showcase.fbx 0.585
```

3. 결과를 눈으로 봅니다. 미리보기 PNG 는 ArtSource/Previews 에 생깁니다. 크기, 앞면, 원점을 5절과 맞춥니다. 프리팹이 아직 회색일 때는 `ph_bbox.py` 와 `ph_fit.py` 로 회색 범위와 비교할 수 있습니다(ArtSource/PH_인계.md).

재질 규칙입니다.

- 이름은 M_<이름> 입니다. 접두사 M_Glass(투명), M_Dyn(런타임 텍스처), M_Tile(타일링)은 굽지 않고 그대로 나갑니다. 나머지는 bake 가 오브젝트당 텍스처 1세트로 합칩니다.
- Unity 재질 이름은 전역입니다. 같은 이름은 같은 .mat 으로 갑니다. 새 재질은 자기 에셋 이름으로 시작합니다.
- 공유 타일을 고치지 않습니다. 색을 바꾸려면 새 이름으로 틴트 사본을 만듭니다(store_shell.py:24-33 tint_copy). M_Tile_Store_* 는 버거집과 공유합니다.

바로 쓸 수 있는 공용 함수입니다.

| 모듈 | 함수 |
|---|---|
| k3d | reset, mat, flag, load_image, image_node, uv_world, uv_smart, bake, tile, polyhaven, join, smooth, origin_bottom, export, preview, validate, PY |
| PH/ph | load, turn, at_unity, move_unity, posed, part, finish |
| Items/_ik | box, cyl, lathe, tube, poly_extrude, torus, quad, P, flat_img, glass, socket, join, finish, tex |
| Items/tex2d | paper, fbm, normal_from_height, save_ms |
| Food/_food | Sh, lathe, mats, join, smooth, bevel, solidify, socket, textures |
| Store/storelib | box, boxz, cyl, quad, pbr, img_mat, empty, shot |
| StoreProps/_common | box, cyl, lathe, tube, quad, plastic, stainless, wood, powder_coat, rubber, label_mat, draw_labels |
| Characters/npc_common | run(CFG), cloth, skin, hair, leather, flat, watch, glasses |
| Buildings/bld | awning 외 건물 도구 |
| Vehicles/_vlib | 스플라인, 회전체, 튜브, 절차 재질 |

카페에 쓸 타일입니다. `k3d.tile(name, maps={"diff": 기존경로})` 로 만들면 인터넷 없이 됩니다(Layouts/StreetGround.py:12 참고).

| 면 | 재료 | 타일(m) |
|---|---|---|
| 바닥 | T_Tile_Home_WoodFloor | 1.7 |
| 벽 | T_Tile_Store_Paint | 2.0 |
| 바 뒤 벽 | T_Tile_Buildings_RedBrick 또는 LongTileCream | 1.4, 1.27 |
| 천장 | T_Tile_Home_Ceiling | 1.06 |

### 7.3 Unity 에 넣기

새 행은 자기 묶음 파일 Assets/Art3D/PH_Map_<묶음>.json 에만 씁니다. PH_Map.json 은 사본도 읽으므로 고치지 않고 ph_map.py 도 돌리지 않습니다.

```json
{"rows": [
 {"prefab": "PH_Hand", "target": "Hand_Pointer/Visual", "model": ""},
 {"prefab": "PH_Hand", "target": "Hand_Pointer/Look_0", "model": "Models/PH/PH_Hand__Pointer20.fbx"}
]}
```

- model 이 비어 있는 행은 그 자리의 앞선 행을 지우고 회색 메시만 비웁니다. 위 예는 PH_Map.json 의 공통 손을 지웁니다.
- target 의 자식은 모두 지워지고 모델이 그 아래에 들어갑니다. Visual 밖의 앵커, 콜라이더, 글자는 target 으로 쓰지 않습니다.
- 새 사람 모습은 target 이 ReactPivot/Visual, HeadPivot/Visual 이고 look 번호를 이어 갑니다(지금 0~8). 이 경우 빈 행을 쓰지 않습니다. 인스턴스의 NpcLook.look 에 번호를 넣습니다. 비우면 이름 해시로 고르므로 손님이 직원 모습이 될 수 있습니다.

Unity 를 닫고 돌립니다. 그 맵 파일에 나오는 프리팹만 저장하므로 다른 묶음의 프리팹을 건드리지 않습니다.

```
Unity -batchmode -quit -projectPath . -executeMethod Art3DTools.FillMap -phmap PH_Map_Cafe.json -logFile -
```

로그의 `키오스크: PH 프리팹 N개에 모델 M개를 넣었습니다. 경고 K개` 를 봅니다. 자리나 모델을 못 찾으면 경고만 나고 넘어갑니다. 경고는 전부 읽습니다. PH_Hand__Memo, Cover, Card 3행 경고는 사본용 행이라 정상입니다.

씬에만 있는 자리(3절에 씬이라고 쓴 곳)와 배경은 메뉴가 닿지 않습니다.

- 배경은 프리팹 하나로 묶어 Assets/Art3D/Env 에 둡니다(Env_Street, Env_Storefront, Env_StoreInterior, Env_Cafe, Env_Home). 씬에는 인스턴스 하나와 회색 Visual 끄기, RenderSettings 만 남겨 씬 충돌을 줄입니다.
- 배치 데이터는 Assets/JeongWoo/Layouts/*.json 이고 코드는 Assets/JeongWoo/Editor/JWDress.cs 입니다. JWDress 의 Street, Storefront, Store 가 쓰는 씬 경로는 R 씬에 전부 있습니다(19/19, 27/27, 35/35). 다만 어셈블리와 타입이 달라 그대로는 안 돕니다. 도구 함수(36-262행)를 Assets/Editor 로 복사하고 Root 경로, JWBuild.Warn, Npc(), Group, 영수증, StoreDirector.sharedRoom 부분을 고칩니다. Sky_Overcast, Fence_Construction 은 Assets/Art3D 로 복사해야 R 씬이 사본에 묶이지 않습니다.
- JWDress.Storefront 는 매장 안을 겹쳐 보여 주는 전제입니다. R 씬은 Env_StoreInterior 를 같이 넣습니다.
- 복사본인 Bus3, Walker, Watcher0~4 는 Visual, DoorLeafA, DoorLeafB, HeadPivot/Visual 아래에 FBX 를 직접 넣습니다. 오브젝트 이름과 참조는 유지합니다. 코드가 fileID 로 참조하므로 지우고 다시 만들면 끊어집니다.
- 코드가 이름으로 찾는 것은 HeadPivot 하나입니다. 지우거나 옮기면 안 되는 것은 Interactable, Readable, 앵커, Bounds 콜라이더입니다. Visual 아래 회색 메시는 지워도 됩니다.

씬을 눈으로 볼 때는 플레이하지 않고 에디터 카메라 Camera.Render 로 찍습니다.

## 8. 파일 정책

| 파일 | git | 이유 |
|---|---|---|
| ArtSource/Blender/scripts/**/*.py | 올림 | 모델의 원본입니다 |
| ArtSource/Blender/<카테고리>/*.blend | 올림 | PH 스크립트 13개가 .blend 40개를 입력으로 엽니다. FBX 로 대신할 수 없습니다. 93개 54 MB 입니다 |
| *.blend1 | 안 올림 | Blender 자동 백업입니다 |
| Assets/Art3D/Models, Textures, Materials 와 .meta | 올림 | 게임이 쓰는 결과물입니다 |
| ArtSource/_cache/fonts | 올림 | 텍스처 글자에 필요합니다. 라이선스는 OFL.txt 입니다 |
| ArtSource/_ref/img, _ref/models/npc_*.glb | 올림 | 포스터 그림과 새 인물의 원본입니다. Prototype/3d.html 에 이미 공개된 파일입니다 |
| ArtSource/_cache 나머지 | 안 올림 | venv, 내려받은 텍스처, 중간 산출물입니다. 스크립트가 다시 만듭니다 |
| ArtSource/Previews, _ref 나머지 | 안 올림 | 미리보기와 참고 자료입니다 |

저장소는 공개입니다. 출처가 불분명한 이미지와 폰트, 토큰이 찍힌 Unity 로그를 올리지 않습니다.

스크립트를 돌리면 FBX, JSON, 텍스처, .blend 가 같이 바뀝니다. 이 묶음을 같은 커밋에 넣습니다. FBX 는 내용이 같아도 시각과 UID 가 바뀌어 항상 변경으로 잡힙니다.

## 9. 충돌을 막는 규칙

공통입니다.

1. `git add -A`, `git add .` 를 쓰지 않습니다. 내 경로만 add 하고 `git status`, `git diff --cached --stat` 로 본 뒤 커밋합니다. docs 폴더는 Docs 와 대소문자가 섞여 있어 add 가 조용히 안 될 수 있습니다.
2. 남의 에셋을 다시 내보내지 않습니다. 내 에셋도 내용이 안 바뀌었으면 커밋하지 않습니다.
3. FBX 를 만든 컴퓨터가 Unity 로 임포트해 .meta 와 .mat 까지 같은 커밋에 넣습니다. .meta 없이 FBX 만 올리면 컴퓨터마다 GUID 가 달라져 프리팹 참조가 끊어집니다.
4. 소유 파일 밖은 저장하지 않습니다. 씬 하나는 한 대만 저장합니다. 씬과 프리팹은 병합이 안 됩니다.
5. Systems.prefab, Assets/Scripts, Assets/UI, ProjectSettings, Assets/JeongWoo, Packages, ProjectVersion.txt 는 고치지 않습니다. 태그와 레이어를 만들지 않습니다.
6. 새 폴더를 공용 위치에 만들지 않습니다. 새 모델은 Models/PH, 배경 프리팹은 Assets/Art3D/Env 에 둡니다. 텍스처 폴더는 에셋마다 따로라 겹치지 않습니다.
7. 받을 때는 `git pull --rebase origin main`, 올릴 때는 `git push origin main` 입니다. force push, `--autostash`, `git add --renormalize`, git-lfs 를 쓰지 않습니다. push 가 거부되면 다시 pull 합니다. 충돌이 나면 멈추고 사람에게 알립니다. 폴더 .meta 충돌만 이미 올라간 GUID 로 풉니다.
8. 내 것이 아닌 파일이 바뀌어 pull 이 막히면 `git stash push -- <파일>` 로 치우고 받습니다. stash 를 pop 하지 않습니다. 빌드나 Unity 가 만든 부작용이라 되살리면 다시 충돌합니다.
9. 커밋 메시지는 짧은 한글에 add:, edit:, fix:, remove: 를 붙입니다. Co-Authored-By 를 넣지 않습니다.
10. 플레이 시험은 사람이 합니다. Unity 는 임포트와 모델 넣기, 캡처에만 씁니다. 배치 모드는 에디터가 열려 있으면 못 돕니다.

한 대만 하는 일입니다.

- 0단계 메뉴(`Tools/키오스크/PH 프리팹에 모델 넣기`)입니다. 31개 프리팹을 한꺼번에 저장합니다.
- 노션 동기화입니다. 플러그인 버전에 따라 변환 결과가 달라 번갈아 돌리면 계속 바뀝니다.
- 빌드와 `JWBuild.All` 입니다. 빌드는 PC_RPAsset, UniversalRenderPipelineGlobalSettings 를 바꿉니다. 이 둘은 커밋하지 않고 stash 합니다.

0단계 뒤에 씬 값이 사라지는 곳이 있습니다. 씬 주인이 맞춥니다.

| 곳 | 증상 | 처리 |
|---|---|---|
| R1_Stop, R4_Stop Rail_E | 길이가 80.4 에서 85.4 로 돌아갑니다 | 인스턴스 루트 X 스케일 0.941 |
| R1_Store NPC_Elder | 몸 재질 덮어쓰기가 사라집니다 | NpcLook.look 을 어르신 번호로 |
| R2_Cafe 키오스크 | 버거대왕 간판과 포스터가 보입니다 | 5절 카페 키오스크 |
| 모든 키오스크 | 구운 "카드 전용" 띠가 보입니다 | 3.5 고침 |

## 10. 알려진 문제

| 문제 | 내용 | 대응 |
|---|---|---|
| Mac 베이크 크래시 | Blender 5.2.3 Metal 굽기가 힙 손상으로 죽고 macOS 오류 창이 뜹니다. CPU 와 GPU 를 같이 켜던 설정에서 6회 중 4회 죽어서 GPU 만 쓰게 고쳤습니다. 고친 뒤에는 39회 중 1회입니다. 완전히 없어지지는 않았습니다 | 내보내기 전에 죽으므로 창을 닫고 그 스크립트를 다시 돌립니다. `K3D_DEVICE=CPU` 를 주면 24회 중 0회였고 3~5배 느립니다 |
| Apple 폰트 | Home/tex2d, Kiosk/kiosk_tex, Vehicles/CityBus_tex, PH/bus_tex, Characters/npcb_decals, Hands/GrandpaHand_tex, StoreProps/labels, Buildings/tex2d, Items/tex2d 가 재배포할 수 없는 폰트를 씁니다 | Windows 에서는 setup.py 가 넣은 대체 규칙으로 GothicA1-Bold 가 쓰여 글자 모양이 달라집니다. 기존 인쇄물을 다시 만드는 일은 Mac 에서 합니다. 새 텍스처는 ArtSource/_cache/fonts 의 폰트만 씁니다 |
| 실행 순서 | PH 스크립트는 원본 .blend 를 엽니다. 원본 그룹을 고치면 원본, PH 순서로 돌립니다. PH/bus_interior 는 PH/bus 뒤입니다 | Street 를 병렬로 돌릴 때는 `all_tiles()` 를 먼저 한 번, Vehicles 는 VEH_TEX_DONE=1 입니다 |
| 사본 영향 | Assets/JeongWoo 는 같은 FBX 를 GUID 로 씁니다. 기존 FBX 의 이름과 계층을 바꾸면 사본이 깨질 수 있습니다 | R 전용으로 형태가 달라지면 새 파일로 만듭니다 |
| Layouts 출력 | Layouts/*.py 는 Assets/Art3D/Layouts 에 쓰는데 실제로 쓰는 곳은 Assets/JeongWoo/Layouts 입니다 | 다시 돌렸다면 옮깁니다 |
| 씬 값에 묶인 범위 | 차는 x 125, 130, 버스는 x 46 에서 끝납니다 | 배경이 이 범위를 덮어야 합니다 |
| 버스 창밖 | PH_BusInterior 는 y -40 이라 창밖이 비어 있습니다 | 머무는 시간이 짧아 그대로 둡니다. 필요하면 Env_Street 를 (-31.75, -39.86, -37) 에 하나 더 놓습니다 |
| 저녁 조명 | R4_Stop 의 ambient 값이 Skybox 모드에서 안 먹을 수 있습니다(실행 미확인) | 씬 주인이 눈으로 봅니다 |

## 11. 확인하지 못한 것

- Windows 에서는 아직 한 번도 돌려 보지 않았습니다. 코드와 문서로만 고쳤습니다. 첫 실행이 setup.py 입니다. 실패하면 그 출력으로 판단합니다.
- Unity 를 실행하지 않았습니다. FillMap, 폰트 설정, 메뉴 결과는 코드와 YAML 을 읽어 판단했습니다. PH_Kiosk_R4 처럼 화면 프리팹이 중첩된 프리팹을 저장했을 때의 결과는 미확인입니다.
- Unity 첫 임포트 시간, 다른 컴퓨터의 라이선스와 git 설정은 미확인입니다.
- Windows 에서 Apply 가 .mat 을 다시 쓸 때 값이 달라지는지 미확인입니다. 내 것이 아닌 .mat 이 바뀌면 규칙 8 을 따릅니다.
- JWDress 재사용과 Env 프리팹 구성은 제안이고 아직 돌려 보지 않았습니다.
