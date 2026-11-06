# 불고기 버거 세트 하나

> 같은 키오스크, 같은 버거. 달라진 것은 내 나이뿐입니다.

20대에는 10초면 끝나던 주문이 80대에는 하루 일이 됩니다. **불고기 버거 세트 하나**는 한 사람이 20대, 40대, 80대를 차례로 살아 보며 키오스크 앞에 서는 1인칭 3D 스토리 게임입니다.

화면에는 나이 숫자가 나오지 않습니다. 손이 늙어 가고, 글씨가 흐려지고, 손이 떨리고, 뒷사람의 한숨이 커지는 것으로 나이를 느낍니다. 1회차에 뒤에서 답답하게 지켜보던 그 어르신이, 마지막에는 플레이어 자신이 됩니다.

- 장르: 1인칭 3D 스토리 체험
- 플레이 시간: 약 10분
- 엔진: Unity 6000.3.13f1 (URP)

## 이야기 흐름

| 장면 | 나이 | 겪는 일 |
|---|---|---|
| 버거집 | 20대 | 앞의 어르신이 카드 넣는 곳에 지폐를 넣다가 세 번 튕기고 돌아섭니다. 내 차례의 주문은 쉽게 끝납니다 |
| 카페 | 40대 | 부탁받은 쪽지의 "뽀샤티"가 무슨 메뉴인지 알 수 없습니다. 직원에게 물어봐야 결제로 넘어갑니다 |
| 집과 정류장 | 80대 | 전광판이 보이지 않고, 길을 물어도 다들 바쁩니다. 첫 버스를 놓친 뒤 돋보기로 번호를 읽어 다음 버스에 오릅니다 |
| 버거집 앞 | 80대 | 문을 밀어도 열리지 않습니다. 돋보기로 "당기세요"를 읽어야 들어갑니다 |
| 버거집 | 80대 | 떨리는 손으로 키오스크와 씨름합니다. 그때 그 어르신처럼 지폐가 튕기고, 뒷사람의 카드로 겨우 주문을 마칩니다 |
| 결과 | | 80~84세 노인 중 키오스크로 주문할 수 있는 사람의 비율을 보여 줍니다 |

## 해커톤 주제

**[게임 안에, 모두를 담다]** 세부 주제 중 다음을 다룹니다.

- **④ 현실을 게임으로 풀기**: 세대 간 디지털 격차라는 일상의 문제를 버거 한 세트를 사는 이야기로 풀었습니다.
- **③ 다른 시선 플레이하기**: 같은 장면을 뒷사람의 자리에서 한 번, 어르신의 자리에서 한 번 플레이합니다. 처음에 답답했던 사람이 나중에는 내가 됩니다.
- **① 고정관념과 장벽 깨기**: 접근성이 없는 화면이 어떤 벽이 되는지 플레이로 겪게 합니다. 주인공의 성별은 정하지 않았고 손만 보입니다.

## 실행 방법

**빌드로 실행 (권장)**

1. ZIP을 풀고 Windows 빌드 폴더의 실행 파일을 엽니다.
2. 시작 화면을 클릭하면 게임이 시작됩니다.

Windows 64비트를 권장합니다. 화면 글자 일부가 Windows의 맑은 고딕을 사용합니다. 인터넷 연결은 없어도 됩니다.

**Unity 에디터로 실행**

1. Unity 6000.3.13f1로 프로젝트를 엽니다.
2. `Assets/Scenes/R1_Home.unity`를 열고 Play를 누릅니다. 첫 장면부터 시작됩니다.

## 조작 방법

| 입력 | 동작 |
|---|---|
| W A S D, 방향키 | 걷기 |
| 마우스 | 둘러보기 |
| Shift | 달리기 (20대만 가능합니다) |
| E, 왼쪽 클릭 | 상호작용 |
| 숫자 키 | 소지품 사용. 번호는 화면의 소지품 칸에 표시됩니다 |
| 왼쪽 클릭 | 키오스크 화면 누르기 |
| A / S / D | 키오스크 앞에서 알바생 보기 / 뒷줄 보기 / 키오스크 보기 |

그 밖의 키는 화면 안내를 따릅니다.

## 시연자 키

심사 중 막히거나 시간이 모자랄 때 씁니다. 모두 `Ctrl + Shift`를 함께 누르며, 빌드에서도 동작합니다.

| 키 | 동작 |
|---|---|
| F2 | 다음 장면 |
| F3 | 이전 장면 |
| 1 ~ 7 | 해당 순번의 장면으로 이동 |
| F6 | 눈치 게이지 가득 채우기 |
| Home | 처음으로 |
| F1 | 디버그 표시 |

## 주요 기능

- **나이 디버프**: 글씨 번짐, 손떨림, 커서 지연, 걸음 속도가 나이에 따라 달라집니다.
- **눈치 게이지**: 오래 걸리면 뒷사람의 한숨과 재촉이 이어지고, 게이지가 다 차면 줄 맨 뒤로 밀려납니다.
- **돋보기**: 80대에는 안내문과 전광판을 돋보기로 비춰야 읽힙니다. 돋보기도 손과 함께 떨립니다.
- **세대별 키오스크**: 회차마다 화면 구성과 결제 수단이 달라집니다. 80대에는 시간 초과로 처음 화면으로 돌아가기도 합니다.
- **같은 자리, 다른 대접**: 같은 질문과 같은 장소라도 나이에 따라 사람들의 반응이 달라집니다.
- **자막과 음성**: 대사에 자막이 함께 나옵니다.

## AI 활용 내역

이 게임은 AI 없이는 나올 수 없었습니다. 코드도 모델도 사람 손으로 만든 것보다 말로 시켜서 만든 것이 훨씬 많습니다. 팀은 기획과 연출 방향을 정하고, 플레이해 보고, 이상한 곳을 지적했습니다.

| 도구 | 사용 범위 |
|---|---|
| Claude Code | Blender Python 스크립트로 만든 3D 모델 전반(건물, 거리, 매장, 카페, 인물, 손, 음식), Unity 코드와 씬 작업, 작업 문서, 여러 컴퓨터 분담 작업과 Git 관리 |
| GPT | 예시 일러스트 |
| 클로바더빙 + 보이스 체인저 | 캐릭터 목소리 |
| Edge TTS | 일부 대사와 안내 음성 생성 (`tools/make_vo.py`) |

게임 실행 중에 AI가 동작하지는 않습니다. 작업 과정은 Git 커밋 기록, `ArtSource/Blender/scripts`, `Docs`에서 확인할 수 있습니다. AI가 만든 결과물은 팀이 직접 플레이하며 확인했고, 외부 소리와 글꼴은 아래에 출처를 밝혔습니다.

## 폴더 구조

| 경로 | 내용 |
|---|---|
| `Assets/Scenes` | 게임 씬. 실제 순서는 `Assets/Graybox/Data/ChapterFlow.asset`에 있습니다 |
| `Assets/Scripts` | 게임 코드 |
| `Assets/Art3D` | 3D 모델과 재질 |
| `Assets/Resources/Audio` | 효과음과 음성, 출처 목록 |
| `ArtSource/Blender` | 3D 모델을 만드는 Blender 스크립트와 원본 |
| `Docs` | 개발 문서 |
| `Prototype` | 초기 프로토타입 |
| `Assets/JeongWoo` | 개발 중 만든 이전 사본 |

## 출처

**통계**: 2023년도 노인실태조사(보건복지부, 한국보건사회연구원), 김세진, 「노인의 여가 및 정보화 현황」, 보건복지포럼 2024년 11월호

**글꼴**

- 부산단디손글씨: 부산광역시 (판매와 대가 수령 금지)
- 서울알림체: 서울특별시 (이미지로만 사용)
- Pretendard: Kil Hyung-jin, SIL OFL 1.1
- Black Han Sans, Do Hyeon, Gothic A1, Jua: Google Fonts, SIL OFL 1.1
- Nanum Pen Script: NAVER Corporation, SIL OFL 1.1
- NanumSquare: NAVER Corporation, 네이버 나눔글꼴 라이선스
- 맑은 고딕: Microsoft

**효과음**: [Freesound](https://freesound.org)에서 받았습니다. CC0 소리 50개를 포함한 전체 목록은 `Assets/Resources/Audio/SFX_CREDITS.csv`에 있습니다. 표기가 필요한 CC BY 소리는 다음과 같습니다.

| 제목 | 작성자 | 라이선스 |
|---|---|---|
| [260601_075521_FR_Public_garden_Spring_urban_atmosphere](https://freesound.org/s/859168/) | kevp888 | CC BY 4.0 |
| [Room-tone hallway apartment 191013_0076.wav](https://freesound.org/s/492810/) | klankbeeld | CC BY 4.0 |
| [Cane_Hitting_Pavement_2.wav](https://freesound.org/s/138296/) | Tdude9000 | CC BY 3.0 |
| [Cane_Hitting_Pavement_3.wav](https://freesound.org/s/138295/) | Tdude9000 | CC BY 3.0 |
| [Cane_Hit_on_Gravel_1.wav](https://freesound.org/s/138292/) | Tdude9000 | CC BY 3.0 |
| [car passing 40km 001.wav](https://freesound.org/s/504968/) | klankbeeld | CC BY 4.0 |
| [car passing 40km 002.wav](https://freesound.org/s/503615/) | klankbeeld | CC BY 4.0 |
| [Card-swipe.wav](https://freesound.org/s/669228/) | soundfridgepr@gmail.com | CC BY 4.0 |
| [Sliding Glass Door-002.wav](https://freesound.org/s/259977/) | heyim89yearsold | CC BY 3.0 |
| [timer.flac](https://freesound.org/s/22627/) | tim.kahn | CC BY 4.0 |
| [26.07.21- Real Human Heartbeat - Contact Mic Recording 4](https://freesound.org/s/863689/) | Valerie-Vivegnis | CC BY 4.0 |
| [moped passing.wav](https://freesound.org/s/198611/) | extrafonia | CC BY 4.0 |
| [Short Female Sigh](https://freesound.org/s/441508/) | guinefurrie | CC BY 4.0 |
| [Long Female Sigh](https://freesound.org/s/441509/) | guinefurrie | CC BY 4.0 |
| [Double Sigh Female](https://freesound.org/s/441511/) | guinefurrie | CC BY 4.0 |
| [tinnitus.wav](https://freesound.org/s/456627/) | bumpelsnake | CC BY 4.0 |
| [Tsk Tsk Mouth Tongue Click](https://freesound.org/s/679316/) | DeqstersLab | CC BY 4.0 |
