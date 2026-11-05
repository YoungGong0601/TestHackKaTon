# 프로토타입 대조표 (PROTOTYPE_GAP)

작성 2026-11-06. 기준: 기능과 흐름은 Docs/Notion(남은 결정 제외), 표현(걷기 느낌, 연출, 소리, 모델, 질감)은 Assets/JeongWoo. 둘이 다르면 기능은 노션, 표현은 정우를 따른다. 위치의 JW는 Assets/JeongWoo/Scripts, HTML은 kiosk-game/src.

상태: 같음(이미 동작), 약함(있으나 다르게 들리거나 보임), 없음(빠짐). 인물 칸: R1은 1회차(Age20), R2, R3, R4는 각 회차.

## 원인 요약

- 걷기 코드(고개 흔들림, 다리 절기 공식)는 JW와 같다. 체감이 사라진 이유는 값과 소리다.
- Age80 걸음 속도가 JW 1.15에서 0.9로 내려갔다.
- 지팡이 소리가 CaneEverySteps 0으로 꺼졌다.
- 발소리, 숨소리가 Age80 먹먹함(1000Hz 저역 통과)을 그대로 받아 거의 안 들린다. JW에는 먹먹함이 없다.
- 공용 시트는 머리글뿐이라 값은 모두 코드 fallback이다. keys_ 파일만 고쳐서는 게임이 바뀌지 않는다.
- 연출은 회차 Director를 새로 쓰면서 빠졌다(간판 시선, 혼잣말, 손님 돌아봄, 버스 소리 순서).

## 1인칭 걷기

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 느린 걸음 | JW PlayerController MoveSpeed 1.15 | 약함, Age80 0.9 | R4 1.15. R1 2.2, R2 1.9, R3 1.5 유지 |
| 다리 절기(기울기, 좌우) | JW PlayerController ApplyCamera | 같음, 프로필 limp | R4만 켬 |
| 고개 흔들림 | JW ApplyCamera, 폭 0.042, 보폭 0.62 | 약함, 모든 인물이 같은 폭. R1은 빠른 속도로 잘게 떨림 | R4 JW 값. R1 폭을 줄이고 보폭을 넓혀 가볍게, R2, R3은 그 사이 |
| 지팡이 소리 | JW Step, 2걸음마다 cane_tap | 없음, 값 0 | R4만. ROUND_PLAN 7절의 0은 표현 기준으로 대체. 노션에 지팡이 언급 없음 |
| 지팡이 모델과 손 | HTML, JW 모두 손에 안 듦. PH_Cane은 현관 소품 | 같음(없음) | 해당 없음 |
| 발소리 | JW Step, step_tile, step_concrete 0.42 | 약함, 먹먹함 적용 | 전 회차, 자기 몸 소리는 먹먹함 제외 |
| 재질별 소리 | PlayerSpawn.ground | 같음, 씬마다 tile, concrete | 전 회차 |
| 숨소리 | JW Step, 19걸음마다 breath_old | 약함, 먹먹함 적용 | R4만 |
| 손 흔들림과 떨림 | JW HandRig sway, tremble | 같음, Debuff.Tremble이 더함 | R3, R4 |
| 계단 발소리 | 노션 마싱, JW 없음 | 약함, 먹먹함 적용 | R1, R4 |

## 시점 연출

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 간판 올려다보기, 문으로 시선 내리기 | JW StorefrontDirector.Intro(3.2초, 1.1초, 1.8초) | 없음 | R4 쪽지 앞에 그대로. R1은 끔(1-4 가볍게) |
| 시선 트윈 LookAt, TurnTo | JW PlayerController | 같음 | 전 회차 |
| 연출 중 손 숨김 | JW Intro SetEnabled(false) | 없음 | R4 |
| 행인 눈으로 좇기 | JW StreetDirector.TrackWorker | 없음 | R4 행인 |
| 고개 숙임과 돌아섬 | 노션 4-10a, T13 | 같음 | R4 |
| 주위 둘러보기 | 노션 4-10b | 같음 | R4 |

## 후처리와 눈치 효과

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 그림자, 번짐, 탈색 패스 | JW Post/KioskPostFeature | 같음, 평온 번짐만 PostBlurMul 비율 | R4 1, R3 0.8, R2 0.4, R1 0 |
| 눈치 단계 시야 | JW NunchiSystem PostState | 같음 | 키오스크 전 회차 |
| 렌더러 등록 | PC_Renderer, Mobile_Renderer | 같음 | 전 회차 |

## 소리

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 환경음 앰비언스 | JW 각 Director | 약함, 주방 0.2(JW 0.5), R4에서 먹먹함이 강함 | 전 회차 |
| 먹먹함 세기 | JW 없음, 노션 기능 | 약함, Age80 1000Hz로 환경음까지 묻힘 | 기능 유지, 값만 완화(R4 1800, R3 3000) |
| 3D 소리 거리 | JW AudioManager minDistance 6 | 없음, 1.5 | 전 회차 |
| 튀김기 소리 | JW StoreDirector fryer_beep 0.8 | R1 0.3, R4 없음 | R1, R4 |
| 알바생 폰 알림음 | JW StoreDirector phone_notify 주기 | R4 없음 | R4, R1 |
| 혼잣말(주문 어디, 이건 또 뭐야) | JW StoreDirector, StorefrontDirector | 없음 | R4 |
| 혼잣말(키오스크 실수) | JW NunchiSystem | 같음 | 키오스크 전 회차 |
| 한숨 | JW 무작위 6종 | 다름, sigh_m_1 고정(N14) | 노션 지정 유지, 혀 차기, 발 구르기, 헛기침 섞기는 남김 |
| 재촉 대사 | JW 순서 재생 | 같음, 구간별 대사로 교체 | R3, R4 |
| 심장, 이명, 수군거림 | JW NunchiSystem | 같음 | 키오스크 전 회차 |
| 키오스크 안내음 끊기 | JW AudioManager k_ | 없음 | 전 회차 |
| 버스 소리 순서 | JW StreetDirector(엔진 서서히, 정차 5초 전 브레이크, 문 열림, 닫힘 구분) | 없음, bus_door 하나 | R1, R4 |
| 횡단보도 음량 | JW CrosswalkBeep 1 | 약함, 0.45 | 정류장 |
| 호출 음성 | JW staff_call_269 등 | 없음 | 호출 차례가 있는 회차 |

## NPC

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 폰 보기, 시계 보기, 초조함, 앉기 자세 | JW NpcLook, JWDress의 pose | 코드 있음, Assets/Scripts/Store/NpcPose.cs. Art3D NpcLook과 이름 충돌을 피한 별도 클래스. NPC에 부착과 pose 값은 모델 담당 | 전 회차 |
| 걷기 애니메이션 | JW NpcLook Walk | 없음, 위와 같음 | 전 회차 |
| 끄덕임, 돌아봄 | JW StreetNpc.Nod, Glance | 같음 | R1 끄덕임, R4 돌아봄 |
| 머리뼈 따라 돌기 | JW StreetNpc.LateUpdate | 없음 | 모델 들어간 NPC |
| NPC 발소리 | JW AudioManager.Footstep | 없음 | 전 회차 |
| 이동 회피 | JW NpcMover | 같음 | 전 회차 |
| 봉투 높이 손에 맞춤 | JW NpcMover.LateUpdate | 없음 | 픽업 손님 |
| 줄 늘어남 | JW 시간 기준 | 다름, 게이지 기준(ROUND_PLAN 6절) | 노션 유지 |
| 비키라는 재촉 | JW QueueManager.NextUp | 없음 | R4 등 픽업 대기. "할아버지" 호칭 문구는 노션 호칭 금지로 뺌 |
| 손님 키오스크 터치 자세 | JW NextUp pose Tap | 없음 | NpcLook 뒤 |
| 뒤돌아 사과 | JW NunchiSystem.Sorry | 같음, 키오스크 담당이 복구 | R4 |
| 눈치 폭발 끼어들기 | JW BlowupRun | 버림, Requeue와 Takeover가 대신 | 없음 |

## 유리문 개그

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 밀기 1, 2회 흔들림과 대사 | JW StorefrontDirector.Push | 같음 | R4 |
| 3회째 5번 밀기 | JW Push | 없음, 3회째도 3번 | R4 |
| 유리 너머 손님 돌아봄 | JW EaterLook(60도) | 없음 | R4 |
| 당기기 표시 때 혼잣말 | JW RevealPull "이건 또 뭐야." | 없음 | R4 |
| 자동 RevealPull | JW Push | 뺌(T20) | 노션 유지 |
| 문 닫힘 소리 | JW QueueManager | 없음 | R1, R4 |
| 매장 미리 불러오기 | JW Preload | 없음(T11 암전) | 노션 유지 |
| 떠나는 버스 | JW Intro | R1 있음, R4 없음 | R4 |

## 정류장 연출

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 버스 도착, 떠남 | JW StreetDirector | 약함, 소리 순서 위 표 | R1, R4 |
| 놓친 버스 혼잣말 | JW "어어, 잠깐만" | 없음, 노션 흐름이 달라 뺌 | 노션 유지 |
| 전광판 못 읽음 혼잣말 | JW _toofar | 같음 | R4 |
| 행인 두 명 | JW Student, Worker | 다름, 행인 하나 | 노션 유지 |
| 저무는 하늘 | 노션 | 있음 | R4 |

## 픽업

| 항목 | 프로토타입 위치 | 지금 상태 | 인물별 |
|---|---|---|---|
| 호출 차례 3번 뒤 내 번호 | JW StoreDirector.Pickup | 다름, R1은 대기 후 바로(T14) | 노션 유지, 1회차 가볍게 |
| 요리사 이동 | JW Pickup cook.Go | 없음 | R1 |
| 받기와 봉투 | JW Take | 같음 | R1 |
| 영수증 | JW Receipt | 버림(3절) | 없음 |

## 씬 소품

씬은 모델 적용 담당 범위. Layouts와 JWDress 기준으로 그쪽에서 맞춘다. 이 표에서는 코드가 이름으로 찾는 Anchor_SignLook, Anchor_DoorLook, NPC_Eater, PH_Bus가 R4_Storefront에 있음만 확인했다.

## 범위 밖이라 안 고침

- Assets/Scripts/Kiosk 아래(NunchiSystem 포함): 검증 담당 범위. 한숨 외 소리 섞기, 재촉 Say의 음성 길이 반영은 그쪽에서 판단.
- 씬 안의 자세 값과 소품: 모델 적용 담당.
