# 표지 번짐 대상 (레이어 후처리 방식)

방식: SignBlur 레이어(13번)가 보이는 자리를 KioskPostFeature가 마스크로 그리고(깊이 비교로 앞 물체 제외), 그 자리만 Dual Kawase 피라미드로 섞는다. 돋보기 LensEye는 후처리가 없어 선명하다.
세기: Post_SignBlur 0.5 x 프로필 배율 PostSignBlurMul(Age20 0, Age40 0, Age60 0.8, Age80 1). 1회차는 0이다.
블러 이미지는 따로 만들지 않는다. Readable.postBlur를 켠 글은 판독 판정만 쓰고 Blurred 쪽은 꺼진다.

| 씬 또는 프리팹 | 대상 | 처리 |
|---|---|---|
| R1_Stop, R4_Stop | Route_Board | 이미지 한 장(RouteMap.png), Sharp를 SignBlur 레이어로, Blurred 끔, wide |
| R1_Stop, R4_Stop | Notice_Cashless(버스 안) | NoticeImage 쿼드를 SignBlur 레이어로, Blurred 끔 |
| R4_Stop | BisFaceA, BisFaceB | Sharp를 SignBlur 레이어로, Blurred 끔 |
| R4_Stop | 간판 영역 36개(옛 Sign_Blur 판) | M_SignZone(투명)으로 바꾸고 SignBlur 레이어. 뒤의 실제 간판이 번진다 |
| R4_Storefront | 간판 영역 13개 | 같음 |
| PH_Door_Glass | Sticker_Pull(당기세요) | Plate를 SignBlur 레이어로, Blurred 끔 |

## 아직 옛 방식인 것
| 대상 | 이유 |
|---|---|
| R1_Stop, R1_Storefront, R2_Cafe의 Readable | 그 씬 인물은 번짐이 없어 Readable이 선명한 쪽만 쓴다 |
| R4_Store의 표지, 스티커 | 아직 Readable 방식. SignBlur 레이어로 옮기면 같은 방식이 된다 |

## 과거 값과 지금 값
| 항목 | 과거(backup/before-single) | 지금 |
|---|---|---|
| 간판 판 | Sign_Blur.mat 월드 반경 0.3m, 지시 0.8배면 0.24m | 후처리 Post_SignBlur 1, 나란히 캡처로 맞춘 뒤 가독성 기준으로 올림 |
| 근접 글자 | 기준 없음 | Post_SignNear 4m 안은 넓은 번짐 단계 전부 사용 |
| 시야 번짐 Post_BlurCenterCalm, Post_BlurEdgeCalm, Post_BlurSpread | 0.1, 0.55, 1.4 | 같음. 표지 번짐과 따로 작동 |
| Readable 번진 쪽 Post_SmudgeSoft, Post_SmudgeContrast | 0.5, 0.55 | 같음. R4_Store 표지만 아직 쓴다 |

우선 기준: 4회차 글자는 맨눈으로 못 읽고 돋보기로 읽는다. 쪽지는 예외다. 이 기준이 0.8배 수치보다 우선이다.

## 키오스크 화면
키오스크 화면 글자는 후처리 표지 번짐 대상이 아니다. 기존 KioskReveal 레이어와 Readable 방식 그대로다.
화면 쿼드 번짐은 Age80_KioskBlur 44px(이전 12px). 4회차 큰 글자와 가격도 맨눈으로 못 읽고 그림과 버튼 자리만 보인다. 돋보기는 RT_Sharp라 또렷하다.

## 쪽지
쪽지는 번짐 대상이 아니다. R2_NoteSoft 0, NotePanel의 age20, age40, age80 soft 0. 들고 있는 동안 HandRig가 쪽지 자리를 PostState.NoteRect로 넘기고 후처리가 그 자리의 시야 번짐과 표지 번짐을 뺀다. 종이 재질은 렌더 큐 3950, 글자 M_Note_Text는 3960으로 유리보다 뒤에 그린다.

## 버스 번호판
R4_Stop Bus1 2413 은행골, Bus2와 Bus3 112 시장입구. 측면 띠 자리, 글자는 SignBlur 레이어로 돋보기로 읽는다.
