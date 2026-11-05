# 라운드 구현 계획 (ROUND_PLAN)

네 담당(Core, R1, R2R3, R4)은 이 문서만 보고 구현한다. 작성일 2026-11-05.

우선순위: 사용자 지시, 이 문서, 플레이 시트, 나머지 노션, CONTRACT.md 순. CONTRACT.md 중 이 문서 3절에서 버린다고 적은 부분은 따르지 않는다. 공통 작업 규칙은 Docs/AGENT_RULES.md.

범위: 3D만(2D 제외). 그레이박스 유지, 모델링 제외, Assets/Art3D 사용 안 함. 「남은 결정」은 새로 설계하지 않고 1절의 임시 동작만 쓴다.

변경 불가 규칙:
- 4회차 버거 구매와 4회차 버스 탑승의 성공 경로를 만들지 않는다. 4회차에 도움을 받는 분기를 만들지 않는다.
- 막혀도 자동으로 넘기지 않는다. 예외는 4-10a. 입력 없는 연출(1-6, 4-10a, 손목시계, 엔딩)은 조작을 잠근다.
- 아무 반응 없는 입력을 남기지 않는다. 안 되면 소리와 문구를 같이 낸다.
- 나이 숫자, 성별, 실제 서비스 이름을 화면에 쓰지 않는다. UI에 사용법 문장을 쓰지 않는다. 라벨은 키와 명사만.
- 임시 처리한 코드에는 주석 `// 임시 T번호`를 단다(예 `// 임시 T17`). 나중에 grep으로 찾는다. 화면에는 표시하지 않는다.

## 1. 임시 처리 표

| 번호 | 항목 | 임시 동작 |
|---|---|---|
| T01 | 3D 입력 | 현재 동작. WASD 걷기, 마우스 시점, E 또는 좌클릭 사용. 키오스크 Interactable을 쓰면 포인터 모드, 좌클릭 터치 |
| T02 | 고개 돌리기 | 키오스크 앞은 현재 동작인 전환식. A 알바생, S 뒤, D 키오스크, W 아래. A와 S 동안 터치 안 됨, 시간과 게이지는 흐름. 키오스크 밖은 마우스 자유 시점 |
| T03 | 돋보기 | 현재 동작. 2 키 토글. Age60, Age80만 시작부터 소지. 문, 전광판 같은 바깥 글씨도 같은 Readable. 렌즈 안 클릭은 보정 없이 커서 위치 그대로 판정 |
| T04 | 결제 입력 | 3 키. 지갑 없는 인물은 카드를 바로 듦. 지갑 있는 인물은 지갑이 열리고, 카드나 지폐를 클릭해 듦. 든 채 결제 지점을 클릭. 지폐 클릭 입력 1번이 튕김 1번 |
| T05 | 마싱 | 좌클릭 또는 E 연타. 횟수만 다름. 멈춰도 내려가지 않음. 누를 때마다 발소리와 눈높이 상승 |
| T06 | 눈치 표시 | 현재 Hud.Nunchi 막대 그대로. 다 차면 HUD 오른쪽 아래에 버튼 "그만두기". 시선과 무관하게 보임 |
| T07 | 4회차 대사 경계 | 낮음 0 이상 40 미만, 중간 40 이상 80 미만, 높음 80 이상 |
| T08 | 대사 | 자막. 화자 이름은 표시하지 않음(Say의 speaker null). 기존 음성 파일이 있는 문구만 음성 재생 |
| T09 | 디버그 | 챕터 단위 이동. 키는 6절 |
| T10 | 1-2, 4-14 정류장 | 같은 곳. R1_Stop을 복제한 R4_Stop. 방향 표시 없음 |
| T11 | 장소 이동 | 1-3 뒤, 4-10b 뒤는 암전 컷(챕터 전환). 2-1은 R2_Cafe 안에서 키오스크까지 직접 걷기 |
| T12 | 1-5, 1-6 | 줄 위치에서 걷기만 막음(HoldStill), 시선은 자유. 1-6 시작 때 Freeze, 키오스크 쪽 LookAt 고정 |
| T13 | 슬픈 얼굴 | 얼굴을 보여 주지 않음. 1-6은 NPC의 HeadPivot을 숙이고 돌아서서 나감. 4-10a와 4회차 선택지는 카메라 시선을 아래로 내리고 돌아섬 |
| T14 | 1-10, 2-7 호출 | 내 번호는 주문 완료 화면에 표시. 1회차 274, 2회차 275. 호출 뒤 픽업 대 Interactable 활성, 호출 전 쓰면 소리와 "아직입니다". 2회차는 호출 뒤 R2_CallRepeatSec 안에 안 받으면 다시 부름 |
| T15 | 1-11 | 먹는 모습 없음. 받은 뒤 문 Interactable "나가기", 회차 전환 |
| T16 | 3-2 | 돋보기 없이 안 보이는 UI는 외래어 뜻풀이뿐. 현재 KioskReveal 레이어 그대로 |
| T17 | 3-8 | 6자리 번호는 HUD 왼쪽 위 작은 글자로 표시(Hud.SideNote). 틀리거나 30초를 넘기면 입력을 비우고 새 번호, phone_notify 소리와 "다시 입력하세요" |
| T18 | "조금만요" 뒤 | 게이지를 Nunchi_ResumeValue(45)로 내림, 버튼 사라짐. 다시 100이면 다시 뜸. 재촉 간격 0.7배, 한숨 음량 1.3배 |
| T19 | 4-0, 4-0a | 4회차 시작 때 지갑이 열린 채 시작. 3 키로 닫고 열기. 돋보기 없이 쪽지에 E나 클릭이면 "뭐라고 썼더라." |
| T20 | 4-1, 4-2 | 현재 동작. E 밀기, 스티커를 돋보기로 읽은 뒤 R 당기기 표시. 현재 Push 안의 자동 RevealPull은 뺌. 1회차는 당기기 하나만 활성, 키 E |
| T21 | 4-5a 큰 글씨 | 임시 연출. KioskScreens 캔버스 내용 루트 scale 1.6, 왼쪽 위 고정으로 결제 버튼이 화면 밖으로 밀림. 다시 누르면 1.0. 레퍼런스 받으면 교체 |
| T22 | 4-8 팝업 | 순서: 코드 등록, 로봇 인증(체크 칸 클릭 1번), 앱 가입, 포인트 적립. 앞 셋은 x로 다음 팝업. 마지막은 x면 처음 화면, 아주 작은 "건너뛰기"면 결제 창 |
| T23 | 4-9 시간 초과 | 현재 Overlay_Timer(오른쪽 위 초 표시). 현재 동작대로 터치마다 40초로 복귀, 결제 창에 들어가면 멈춤. 초과하면 처음 화면, 장바구니 비움, 큰 글씨 해제. 게이지, 줄, 튕김 횟수는 유지 |
| T24 | 4-10b | 사람들을 문까지 가는 길 양옆 앞쪽에 세운다. HeadPivot이 플레이어를 따라 돈다. 걷기는 플레이어 입력. 멈추면 그대로 기다림. 문 Interactable "나가기" |
| T25 | 4회차 버스 필수 행동 | 4-11, 4-12, 4-13, 4-14는 필수 아님. 1번째 버스는 챕터 시작 뒤 R4_Bus1ArriveSec에 옴 |
| T26 | 4-15~4-19 | 앞 두 대 번호판은 돋보기로 봐도 "112"(판 글자를 112로 둠). 타지 않으면 문 연 채 기다림. 마싱 뒤 "묻기" Interactable만 활성, 묻기 필수. 다음 버스는 앞 버스가 떠나고 R4_NextBusSec 뒤 |
| T27 | 재촉 연출 4-16, 4-18 | 문구 없음. tsk와 bus_door 소리, 문이 먼저 닫히기 시작 |
| T28 | 엔딩 | E-1은 PH_NPC 회색 몸 뒷모습 컷(Cine.BackShot). 제목 뒤 클릭하면 처음으로 |
| T29 | 키오스크 문구 | 버거는 현재 KioskData 메뉴 재사용. 카페, 영화, 팝업은 2절 처리안의 문구만 씀 |
| T30 | 아트 톤 | 회색 그대로. 회차별 키오스크 차이는 글자 크기와 배치만 |
| T31 | 삼성페이 | 게임에 안 나옴. 뒷사람은 카드 |
| T32 | 엔딩 통계 문구 | 시트 문구 그대로. 상수 한 곳(R4 엔딩)에 두고 STAT_CHECK.md 결론은 사용자 판단으로 남김 |
| T33 | 호칭 문구 | 2절 C1 처리안 |

## 2. 시트 안의 모순과 문서에 없는 것

### 모순

| 번호 | 내용 | 처리안 |
|---|---|---|
| C1 | "호칭을 쓰지 않는다"와 대화표 "어르신, 그거 아니에요." | 자막을 "그거 아니에요."로 쓰고 음성 없음(y_hurry5 안 씀). 시트의 "어르신:" 화자 표기는 T08로 화면에 안 나옴. 사용자 판단 필요 |
| C2 | 공통 규칙 "조작은 클릭이다"와 현재 WASD, E, R, 숫자 키 | 사용자 지시로 현재 입력 유지(T01). 터치, 마싱, 선택지만 클릭 |
| C3 | 4-8 "마지막 x는 처음으로"와 4-10 "결제 창까지 간다" | x만 있으면 결제 창에 못 간다. T22의 "건너뛰기" 추가 |
| C4 | "실패해도 넘어갈 수 있는 곳"에 버스가 있으나 버스에 실패 분기가 없음 | 버스는 순서 자체가 실패 진행. 눈치 게이지와 버튼 없음(공통 규칙의 "3회차와 4회차 버거집에만"을 따름) |
| C5 | 4-19 표는 기사 대사가 자동처럼 보이고, 대화표는 "탑승 후 질문" | 세 대 모두 "묻기" 필수(T26) |
| C6 | 게이지 "화면에 보인다"와 1회차 "거의 차지 않는다", 수치표에 1회차 값 없음 | 1회차도 표시. Age20_NunchiFillSec 900 |
| C7 | 2회차 게이지 120초가 다 찬 뒤가 없음(버튼은 3회차와 4회차 버거집만) | 100에서 멈추고 한숨만 계속. 1회차도 같음 |
| C8 | "돋보기 필요 없음"(1, 2회차)과 공통 조작 | 소지 안 함. 2 키는 라벨도 없음. Hud.Items는 소지품만 표시 |
| C9 | 개요 "젊은 사람들은 삼성페이"와 시트 "뒷사람이 카드로", 실제 서비스 이름 금지 | 시트 우선(T31) |
| C10 | 엔딩 문구와 출처 표기 | STAT_CHECK.md: 근거 확인 못 함, 서울 조사 수치일 가능성. 문구 유지(T32), 사용자 판단 필요 |
| C11 | AI 작업 안내 "임의로 정하지 말고 묻는다"와 이번 지시 | 사용자 지시 우선. 이 문서의 T 표가 답. 4-5a도 지시대로 임시 연출 |

### 문서에 없는 것

| 번호 | 없는 것 | 처리안 |
|---|---|---|
| N1 | 시작 화면 | 현재 ShowTitle 유지, 제목 글자만 「불고기버거 세트 하나」 |
| N2 | 1회차에 불고기 세트를 고를 이유, 다른 메뉴를 누르면 | 메뉴 3칸, 불고기 버거 세트가 맨 앞. 나머지는 kiosk_error와 "품절" |
| N3 | 카페 메뉴 | 아메리카노, 카페라떼(글자), 나머지 4칸 아이콘만. 아메리카노는 글자 유지 |
| N4 | 영화 이름, 좌석 구성 | "영화 A", "영화 B", "영화 C". 상영관 3개는 시트의 리클라이너, 스위트박스, 프리미엄. 좌석 6 x 4 격자, 아무 좌석이나 통과 |
| N5 | 2-4 선택 창 내용 | 샷 추가(0, 1), 얼음 양(적게, 보통, 많이), 쿠폰(없음), 적립(건너뛰기) 각 한 화면 |
| N6 | 4-5 숨겨진 메뉴 버튼 | 구석의 작은 세 줄 버튼을 눌러야 메뉴 목록이 열림 |
| N7 | 4-21 기사 답 문구 | "카드 찍으세요." "앱에서 하세요." |
| N8 | 4-20 기사 반복 간격 | R4_DriverRepeatSec 6 |
| N9 | 눈치 버튼 라벨 | "그만두기" |
| N10 | 1회차 게이지 이후 뒷사람 대사, 2회차 뒷사람 대사 | 없음. 한숨만 |
| N11 | 호출 번호 2회차 값 | 275(T14) |
| N12 | 품절, 아직입니다, 다시 입력하세요 같은 거절 문구 | 이 표와 T 표의 문구만 쓴다. 추가가 필요하면 보고서에 적는다 |
| N13 | 버스 탄 뒤 1회차 이동 | 암전 동안 bus_leave 소리, 안내방송 없음 |
| N14 | 1-5 한숨과 4-6 한숨이 같은 소리라는 지정 | 둘 다 sigh_m_1 고정. 4회차 뒷사람은 1회차 캐릭터이고 NunchiLines의 무작위 한숨을 쓰지 않는다 |

## 3. 버릴 것과 재사용할 것

| 대상 | 처리 |
|---|---|
| CONTRACT 씬과 진행, 데이터, ItemId, 키오스크 화면 id, 디버그 키, 챕터 추가 절차, 인물 전제의 범위, 폴더 담당 | 버림. 이 문서 4, 5, 6절이 대신함 |
| CONTRACT PH 프리팹 규칙, 모델 교체 규격, 화면 후처리, 돋보기, 폰트, 좌표 | 재사용 |
| CONTRACT_NOTES | Core, 시작 지점, Say, Nunchi 관련 내용은 참고용. 폭발 관련 줄은 버림 |
| Elder.asset, 노인 챕터 ChapterFlow | 버림. Age20, Age40, Age60, Age80으로 교체. Elder_ 키는 Age80_로 옮김 |
| CharacterProfile, ChapterFlow, ChapterEntry | 재사용, 필드 추가(4절). hasKiosk와 F5는 뺌 |
| GameState, Bal, PlayerController, PlayerSpawn, Interactable, Readable, HandRig, Hud, AudioManager, PostState, PlainChapter, KioskPostFeature | 재사용, Core가 확장 |
| Home.unity, HomeDirector, Bus.unity, BusDirector | 버림(1-1이 정류장에서 시작). PH_BusInterior는 정류장 씬에서 재사용 |
| Street.unity | R1_Stop, R4_Stop의 복제 원본 |
| Storefront.unity | R1_Storefront, R4_Storefront의 복제 원본 |
| Store.unity | R1_Store, R4_Store, R2_Cafe, R3_Cinema의 복제 원본 |
| StreetDirector, StorefrontDirector, StoreDirector | 복사해서 각 담당 Director의 재료로 쓰고 원본은 마감 때 삭제 |
| BusMover, StreetNpc, TrafficMover, CrosswalkBeep, NpcMover, QueueManager, PickupBoard | 재사용. Core 소유. QueueManager의 폭발 끼어들기는 뺌 |
| KioskController, KioskScreens, KioskScreen, KioskButton, KioskField, KioskFields, KioskCell, KioskView, KioskLens, KioskCard, CardSlot | 재사용. 입력, 시선, 번짐, 판정만 남김 |
| KioskFlow, KioskPresenter, KioskData, KioskState, KioskReceipt, PosterFlap, KioskSpot | 복사 재료. 영수증, 포스터 들춤, IC 틈 찾기, 광고, 회원 화면은 기획에 없어 안 씀. 원본은 마감 때 삭제 |
| Screen_*.prefab 14개 | 원본 수정 금지. 각 담당이 자기 Pack 폴더로 복사해 씀 |
| NunchiSystem, NunchiLines | 재사용. 상승률을 100 / NunchiFillSec로 교체, 폭발을 버튼과 선택지로 교체 |
| Assets/Tests/PlayMode | 마감 때 KioskBot 의존 시험 삭제. VideoRun.cs는 git 미추적이라 지우지 말고 사용자에게 묻는다 |
| Hud.ShowResult, RunStats 표시 | 버림. 엔딩이 대신함 |
| Assets/Art3D, Assets/Editor/Art3DTools.cs, tools, Prototype | 건드리지 않음 |

## 4. 챕터 목록

ChapterFlow.chapters 순서. 씬은 Assets/Scenes. spawnId는 씬 이름의 소문자.

| 번호 | 씬 | 프로필 | 복제 원본 | 담당 | 시트 행 | 끝 |
|---|---|---|---|---|---|---|
| 0 | R1_Stop | Age20 | Street | R1 | 1-1~1-3 | 카드 찍은 뒤 암전 컷 |
| 1 | R1_Storefront | Age20 | Storefront | R1 | 1-4 | 문 열고 입장 |
| 2 | R1_Store | Age20 | Store | R1 | 1-5~1-11, 1-9 | 회차 전환 |
| 3 | R2_Cafe | Age40 | Store | R2R3 | 2-1~2-8, 2-5 | 회차 전환 |
| 4 | R3_Cinema | Age60 | Store | R2R3 | 3-1~3-9, 언제든, 실패 | 회차 전환 |
| 5 | R4_Storefront | Age80 | Storefront | R4 | 4-0~4-2 | 문 열고 입장 |
| 6 | R4_Store | Age80 | Store | R4 | 4-3~4-10b, 언제든, 실패 | 암전 컷 |
| 7 | R4_Stop | Age80 | Street | R4 | 4-11~4-21, E-1 | E-1 뒤 CompleteChapter, 이어서 Core가 E-2 |

버스 내부: R1_Stop, R4_Stop에 PH_BusInterior 하나를 땅 밖 Anchor_BusInside 자리에 둔다. 마싱이 끝나면 Teleport로 들어간다(R4는 3대 모두 같은 내부를 쓴다). 내부에 Driver, PH_BusTerminal이 있다.

프로필 필드와 값. 기존 필드는 유지, 새 필드는 Core가 추가. 세기는 7절 키가 정한다.

| 필드 | Age20 | Age40 | Age60 | Age80 | 뜻 |
|---|---|---|---|---|---|
| keyPrefix | Age20_ | Age40_ | Age60_ | Age80_ | |
| speakerKey | a20 | a40 | a60 | gp | 음성 파일은 gp만 있음 |
| displayName | 빈 값 | 빈 값 | 빈 값 | 빈 값 | 호칭 금지 |
| items | Card | Wallet, Card | Lens, Card | Lens, Wallet, Cash, Memo | Memo는 지갑 속 쪽지 |
| handLook(새) | 0 | 1 | 2 | 3 | 손 단계. 3은 소매, 반지, 손목시계 |
| limp | 끔 | 끔 | 끔 | 켬 | 느린 걸음 흔들림 |
| visionBlur | 끔 | 끔 | 켬 | 켬 | 월드 글은 돋보기로만 읽힘 |
| kioskBlur | 끔 | 켬 | 켬 | 켬 | 키오스크 글씨 흐림 |
| kioskHideMeaning | 끔 | 끔 | 켬 | 켬 | 뜻풀이는 돋보기로만 |
| kioskNunchi | 켬 | 켬 | 켬 | 켬 | R4_Stop은 키오스크가 없어 게이지 없음 |
| kioskTouchFail | 끔 | 끔 | 켬 | 켬 | 옆 버튼 눌림과 터치 실패 |
| muffle(새) | 끔 | 켬 | 켬 | 켬 | 먹먹한 소리 |
| tremble(새) | 끔 | 끔 | 켬 | 켬 | 손떨림 |
| cursorLag(새) | 끔 | 끔 | 켬 | 켬 | 커서 지연 |
| lensFocus(새) | 끔 | 끔 | 끔 | 켬 | 돋보기 초점 흐려짐 |
| kioskTimeout(새) | 끔 | 끔 | 끔 | 켬 | 시간 초과 |

글자 크기, 아이콘만, 팝업, 숨겨진 버튼은 스위치가 아니라 각 회차 Pack이 만든다.

## 5. 파일 소유표

자기 소유 밖 파일은 수정하지 않고 보고서에 적는다. 공통 프리팹 변경은 Core만 한다. 씬 안 인스턴스의 오버라이드와 자식 추가는 그 씬 담당이 한다.

| 담당 | 소유 |
|---|---|
| Core | Assets/Scripts/Core, Kiosk(Pack 폴더 제외), Kiosk/Nunchi, Store, Story, Config(읽기만), Assets/Graybox 전체(PH, Data, Materials, Post, Shaders), Assets/UI/HUD.prefab, Assets/UI/Fonts, Assets/Tests, Build Settings, 원본 씬 5개와 SampleScene, Docs/keys_Core.csv 및 기존 keys_ 파일 |
| R1 | Assets/Scripts/R1, Assets/UI/Kiosk/R1, 씬 R1_Stop, R1_Storefront, R1_Store, Docs/keys_R1.csv |
| R2R3 | Assets/Scripts/R2R3, Assets/UI/Kiosk/R2, Assets/UI/Kiosk/R3, 씬 R2_Cafe, R3_Cinema, Docs/keys_R2R3.csv |
| R4 | Assets/Scripts/R4, Assets/UI/Kiosk/R4, 씬 R4_Storefront, R4_Store, R4_Stop, Docs/keys_R4.csv |

Core가 복제 전에 원본 씬과 프리팹에 넣어 같은 자리를 보장할 것: "카드 전용" 스티커(PH_Kiosk 자식 Sticker_CardOnly, Readable), "누구나 쉽고 빠르게!" 포스터(PH_Poster, Store 벽), "현금 없는 버스 운행 안내"(PH_Notice_Cashless, Street 구석), PH_BusTerminal(단말기, 같은 안내문 포함), PH_Sign_Pull은 기존 Sticker_Pull. R1과 R4는 이 넷의 위치를 옮기지 않는다. 카페, 영화관은 스티커와 포스터를 꺼도 된다.

## 6. Core API

시그니처는 고정이다. Core는 먼저 빈 몸체로 올린다. 기존 Hud.Say, Hud.Fade, Hud.Prompt, PlayerController, Interactable, Readable, AudioManager.Play, NpcMover, QueueManager는 그대로 쓴다.

```csharp
// 회차 전환. GameState.CompleteChapter가 다음 프로필이 다르면 눈 감기(위아래 눈꺼풀 Image)로, 같으면 암전으로 닫는다
public static class Round {
  IEnumerator Open(string goal = null);   // 씬 Director 시작에서 yield. 눈 뜨기, 프로필이 바뀌었으면 손을 들어 보여 줌, 목표, Freeze 해제
  void Goal(string text);                 // 목표 한 줄 교체. null이면 지움. 4회차는 안 부른다
}
// Hud.Objective(text, keep): keep 0이면 지울 때까지 표시. Round.Goal이 이것을 쓴다

// 디버프. 챕터 진입 때 프로필로 Core가 자동 적용. 라운드 코드는 읽기만 한다
public static class Debuff {
  float KioskBlur;      // 화면 쿼드 번짐 반지름, Bal.F("KioskBlur"). Kiosk_BlurBase를 대신함. 눈치 BlurStep 가산은 유지
  float Muffle01;       // 0 또렷, 1 최대. 키오스크 안내음, 주변음에 적용
  float Tremble;        // HandRig.tremble과 커서, 돋보기에 적용
  float CursorLagSec;   // 포인터 지연
  bool  LensFocused;    // lensFocus 켜진 인물이 흐려진 구간이면 false. Readable이 이때 onRead를 안 냄
}
// AudioManager.Play(key, pos, vol, rate, clear: true), Vo(.., clear: true): 먹먹함 제외. 뒷사람 한숨, 재촉은 Core가 clear로 낸다
// 터치 실패는 KioskController.Click 안에서 처리: 옆 버튼 눌림, 터치 안 먹음, 빗나가는 손(HandRig.TapMiss), 소리. Pack은 결과만 받는다

// 눈치. PH_Kiosk의 NunchiSystem, Enter에서 Begin, 끝날 때 End (기존)
public class NunchiRule {
  string[] low, mid, high;     // 게이지 구간 대사. null이면 한숨만. 구간 경계 T07
  string[] choices;            // null이면 100에서 멈추고 버튼 없음. [0] 떠남, [1] "조금만요"
  Action onLeave;              // [0]을 고르면 호출
}
void NunchiSystem.Configure(NunchiRule r);   // Enter 전 호출. 상승률은 100 / Bal.F("NunchiFillSec")와 줄 길이
Func<bool> NunchiSystem.CanBlow;             // 기존. false면 버튼이 안 뜬다. Pack.CanGiveUp이 연결됨
// 줄이 길어지는 것은 QueueManager가 게이지에 맞춰 자동. 최대 인원은 기존 키 Queue_Max

// 고개 돌리기. KioskController
string View;                       // "kiosk" "staff" "back"
event Action<string> ViewChanged;
event Action StaffCalled;          // A 시선에서 E. Director가 받아 알바생 대사를 말한다. 고정 문구는 Core에서 뺌

// 지갑. 왼손, 돋보기와 동시 사용
public class Wallet : MonoBehaviour {
  static Wallet I; bool Open;
  void SetOpen(bool on);
  event Action NoteRead;           // 쪽지 Readable을 돋보기로 처음 읽을 때
  event Action NoteMissed;         // 돋보기 없이 쪽지를 눌렀을 때. 대사는 Director가 낸다
}
// ItemId { None, Memo, Lens, Card, Wallet, Cash }. Memo, Wallet은 Held가 아니다. 키 2 Lens, 3 지갑 또는 카드

// 결제 입력. Fps 모드와 키오스크 모두 클릭으로 들어온다. 키오스크는 CardSlot ic에 붙인다
public class PayPoint : MonoBehaviour {
  event Action Approved;           // 카드를 든 채 클릭, card_insert와 kiosk_ok
  event Action<int> CashRejected;  // 지폐를 든 채 클릭, 튕김 소리와 애니, 인수는 이 지점의 누적 횟수
  event Action Empty;              // 빈손 클릭, Core가 kiosk_error
  void ResetCount();
}

// 계단 마싱
public static class Mash {
  IEnumerator Climb(Transform bottom, Transform top);       // 횟수 Bal.F("MashCount")
  IEnumerator Descend(Transform top, Transform bottom);     // 입력 없음
}

// 손목시계. 입력 잠금, 왼손 시계 들기, 바늘 표시, Watch_LookSec 뒤 내림
public static class Watch { IEnumerator Look(int hour); }

// 대화 선택지. HUD 버튼, 커서 모드로 바꾸고 고른 뒤 이전 모드로
public static class Choice { IEnumerator Ask(string[] labels, Action<int> picked); }

// 컷과 엔딩
public static class Cine {
  IEnumerator BackShot(NpcMover walker, Vector3 walkTo, float sec); // 1-6과 E-1이 같은 구도로 쓴다. Shot_ 키
}
// 마지막 챕터의 CompleteChapter는 결과 대신 Ending.Play: 암막, 통계 문구, 작은 출처, 제목, 클릭 대기, Restart
// Hud.SideNote(string text): 왼쪽 위 작은 글자. null이면 지움
```

시연자 키. 빌드 포함, `#if` 제거. 모두 Ctrl+Shift 조합이라 단독으로는 동작하지 않는다. 기존 F 단독 키는 삭제.

| 키 | 동작 |
|---|---|
| Ctrl+Shift+F1 | 디버그 표시(챕터, 경과 시간, 게이지) |
| Ctrl+Shift+F2 | 다음 챕터 |
| Ctrl+Shift+F3 | 이전 챕터 |
| Ctrl+Shift+1~8 | 4절 번호 0~7 챕터로(1이 번호 0) |
| Ctrl+Shift+F6 | 눈치 100 |
| Ctrl+Shift+F7 | 시트 다시 읽기 |
| Ctrl+Shift+Home | 처음으로 |

키오스크 화면 묶음(Pack). PH_Kiosk 프리팹에서 Screen 14개를 빼고, 씬의 PH_Kiosk 인스턴스 KioskCanvas 아래에 담당이 Pack 프리팹 하나를 넣는다. KioskController는 Awake에서 자식의 KioskPack을 찾는다.

```csharp
// Pack 프리팹 루트. 같은 오브젝트에 KioskScreens. 프리팹은 Assets/UI/Kiosk/<R1|R2|R3|R4>/Pack_<회차>.prefab
// 스크립트는 자기 폴더: R1BurgerPack, R2CafePack, R3CinemaPack, R4BurgerPack
public abstract class KioskPack : MonoBehaviour {
  public KioskController Ctl { get; internal set; }
  public abstract string FirstScreen { get; }
  public virtual bool Timed => false;         // 시간 초과를 세는 화면에서 true. 프로필 kioskTimeout이 켜져야 돈다
  public virtual bool CanGiveUp => true;      // 눈치 버튼 허용
  public abstract void OnPress(string id);    // 터치 판정 뒤 확정된 버튼
  public virtual void OnEnter() {}
  public virtual void OnTimeout() {}          // 시간 초과. T23을 여기서 처리
  public virtual void OnTick(float dt) {}
}
// KioskController: void Go(string screenId), void Toast(string), void ResetTimer(), void Finish(), IEnumerator Enter()
// Enter가 끝나면 Director가 이어간다. 화면 id, 버튼 id는 Pack 안에서만 쓰는 이름이다
```

새 Pack의 TMP 폰트는 Assets/UI/Fonts/Hud_MalgunOS SDF.asset을 쓴다(Store_KoreanSDF는 정적이라 새 글자가 빠진다). 기계와 인쇄물 폰트를 바꾸지 않는다는 CONTRACT 규칙은 새 Pack에 적용하지 않는다.

## 7. 수치 (ConfigTable 키)

코드 fallback은 아래 값. 라운드 전용 키는 R1_, R2_, R3_, R4_ 접두어로 각자 keys_ 파일에 적는다. Elder_ 키 중 아래 표에 없는 것(BackSpeedMul, StepStride, BobRate, BobHeight, KioskEyeDown, DoorStepSpeed, PushedAsideSpeed, PushedBackSpeed, ExitWalkSpeed)은 네 접두어에 Elder 값을 복사한다. Age20, Age40, Age60의 LimpRoll, LimpSway, CaneEverySteps, BreathEverySteps는 0이고, 코드는 0이면 소리와 흔들림을 끈다. Age80_CaneEverySteps도 0(기획에 지팡이 없음).

시트 값:

| 키 | 값 | 시트 항목 |
|---|---|---|
| Run_RoundTargetSec | 120 | 회차당 시간(디버그 표시 기준) |
| Run_TotalTargetSec | 600 | 전체 시간(디버그 표시 기준) |
| R1_ElderSceneSec | 15 | 1회차 어르신 장면 |
| Age20_MashCount | 10 | 쉬운 계단 마싱 |
| Age80_MashCount | 40 | 어려운 계단 마싱, 버스마다 |
| Age40_NunchiFillSec | 120 | 2회차 게이지 |
| Age60_NunchiFillSec | 80 | 3회차 게이지 |
| Age80_NunchiFillSec | 60 | 4회차 게이지 |
| Age80_KioskTimeoutSec | 40 | 4회차 시간 초과 |
| Lens_FocusPeriodSec | 8 | 초점 흐려짐 주기 |
| Lens_FocusBlurSec | 2 | 초점 흐려짐 길이 |
| Watch_LookSec | 2 | 손목시계 보는 시간 |
| R4_WatchHour1, R4_WatchHour2, R4_WatchHour3 | 2, 4, 6 | 바늘 |
| Cash_BounceCount | 3 | 지폐 튕김 |
| R3_SmsLimitSec | 30 | 문자 번호 제한 시간 |

재량 값(시트 표에 없음, 플레이 후 조정):

| 키 뒷부분 | Age20 | Age40 | Age60 | Age80 |
|---|---|---|---|---|
| NunchiFillSec | 900 | 시트 | 시트 | 시트 |
| MoveSpeed | 2.2 | 1.9 | 1.5 | 0.9 |
| EyeHeight | 1.68 | 1.66 | 1.62 | 1.56 |
| KioskEye | 1.58 | 1.56 | 1.52 | 1.47 |
| KioskBlur | 0 | 3 | 7 | 12 |
| PostBlurMul | 0 | 0.4 | 0.8 | 1 |
| MuffleCutoff | 22000 | 6000 | 2500 | 1000 |
| Tremble | 0 | 0 | 0.6 | 1 |
| CursorLagSec | 0 | 0 | 0.12 | 0.2 |
| TouchMissChance | 0 | 0 | 0.2 | 0.3 |
| TouchFailChance | 0 | 0 | 0.08 | 0.12 |

공통 재량 값:

| 키 | 값 | 뜻 |
|---|---|---|
| Round_BlinkCloseSec | 0.6 | 눈 감기 |
| Round_BlinkOpenSec | 0.9 | 눈 뜨기 |
| Round_HandShowSec | 1.5 | 손 보여 주기 |
| Round_GoalKeepSec | 0 | 목표 표시 시간, 0은 계속 |
| Shot_BackDist | 4 | 뒷모습 컷 거리 |
| Shot_BackHeight | 1.5 | 뒷모습 컷 높이 |
| Queue_Max | 4 | 줄 최대 인원, 기존 키 |
| Nunchi_LowMax | 40 | T07 |
| Nunchi_MidMax | 80 | T07 |
| Nunchi_ResumeValue | 45 | T18, 기존 키 |
| Nunchi_StayHurryMul | 0.7 | T18 |
| Nunchi_StaySighMul | 1.3 | T18 |
| Kiosk_TimerLow | 10 | 남은 시간 강조, 기존 키 값 변경 |
| R2_CallShowSec | 3 | 화면 번호 표시 |
| R2_CallRepeatSec | 12 | 다시 부름 |
| R4_BigTextScale | 1.6 | T21 |
| R4_Bus1ArriveSec | 8 | T25 |
| R4_NextBusSec | 6 | T26 |
| R4_DriverRepeatSec | 6 | N8 |

## 8. 완성도 점검표

| 항목 | 이번 | 담당 |
|---|---|---|
| 터치 실패 빗나가는 손과 소리 | 넣음 | Core |
| 문이 안 열릴 때 덜컹 소리와 대사 | 넣음 | R4 |
| 지폐 튕김에 소리와 "카드 전용" 안내 | 넣음 | Core 소리, R4 안내 |
| 1회차를 가장 매끄럽게 | 넣음 | R1 |
| 반응 없는 입력 제거 | 넣음 | 모두 |
| 자정까지 1회차부터 엔딩까지 연결 | 넣음(회색 화면 허용). 2026-11-05 자정 기준 | 모두 |
| 2026-11-06 기능 동결 | 따름 | 모두 |
| 버튼 눌림 효과와 효과음 | 넣음 | Core |
| 회차 전환 연출 | 넣음 | Core |
| 키오스크 스타일을 회차별로 | 넣음(T30 범위) | 각 회차 |
| 목표 한 줄, 4회차는 쪽지 | 넣음 | 각 회차 |
| 처음으로 키 | 넣음 | Core |
| 임시 문구와 오타 제거 | 마감 때 | 검증 담당 |
| 처음 보는 사람 시험, 제출 빌드 완주, 헤드폰 준비 | 이번 구현 밖 | 사용자 |

시간이 모자라면 이 순서로 뺀다(점검표 순서 그대로). 다른 것은 임의로 빼지 않는다.

1. 음성 안내(2-7. 화면 번호만 남김)
2. 아이콘만(2-3. 전부 글자로)
3. 음성 AI 상담(3-5)
4. 좁은 버튼(4-5의 옆 버튼 눌림. 터치 실패는 유지)

## 9. 진행 순서

1. Core: 6절 시그니처를 빈 몸체로 올리고 컴파일 에러 0. 기존 코드는 지우지 않는다(ItemId는 뒤에 추가만). 5절 공통 물건을 원본 씬과 프리팹에 넣고, 4절 씬 8개 복제, Age 에셋 4개, ChapterFlow, Build Settings, 기존 Director 제거를 끝낸 뒤 Docs/CORE_READY.txt를 만든다.
2. R1, R2R3, R4: CORE_READY.txt를 본 뒤 자기 폴더에서 시작. 각 씬에 Director(R1StopDirector처럼 씬 이름 + Director)를 만든다. 씬 끝은 GameState.I.CompleteChapter()만 부른다.
3. Core: 몸체 구현. 먼저 Round, Choice, PayPoint, Mash, 그다음 나머지.
4. 모두: 회색 화면이라도 먼저 끝까지 잇고, 그 뒤 연출을 채운다.
5. Core 마감: 구 Director, 구 씬, 구 시험, Elder, Memo 경로 삭제.
