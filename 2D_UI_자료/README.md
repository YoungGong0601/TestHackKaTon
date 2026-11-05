먼저 `UI_작업팩/명세서.md` 를 보세요.

# 2D UI 자료

이 프로젝트의 2D UI 전부를 플레이어가 보는 순서로 모았습니다. 캡처는 `캡처/`, 화면별 요소표는 `요소/`에 번호와 이름이 같은 파일로 있습니다. UI 재작업 커밋 12c21ca 기준의 Pack_R1에서 R4와 HUD로 뽑았습니다. 월드 면은 아직 그레이박스입니다.

## 전체 목록

위쪽이 플레이어가 먼저 보는 순서입니다. 074번 이후는 지금 플레이에 나오지 않는 참고, 미사용, 프로토타입 기준 참고(Screen_ 원본)입니다.

| 번호 | 이름 | 분류 | 회차 | 프리팹 또는 씬 경로 | 해상도나 크기 | 캡처 파일 | 쓰는 장면 |
|---|---|---|---|---|---|---|---|
| 001 | 시작 화면 | HUD | 공통 | Assets/UI/HUD.prefab Title | 1920 x 1080 | 001 시작 화면.png | 게임 시작 |
| 002 | 페이드 | HUD | 공통 | Assets/UI/HUD.prefab Fade | 1920 x 1080 | 002 페이드.png | 장면 전환 암전(캡처는 알파 0.6) |
| 003 | 눈꺼풀 | HUD | 공통 | Assets/UI/HUD.prefab Lid_Top, Lid_Bottom | 1920 x 1080 | 003 눈꺼풀.png | 회차 사이 눈 감고 뜨기 |
| 004 | 자막 목표 | HUD | 1 2 3 | Assets/UI/HUD.prefab Subs | 1920 x 1080 | 004 자막 목표.png | 회차 시작 목표 한 줄 |
| 005 | 십자선 | HUD | 공통 | Assets/UI/HUD.prefab Cross | 1920 x 1080 | 005 십자선.png | 걷는 동안 화면 중앙 |
| 006 | 프롬프트 | HUD | 공통 | Assets/UI/HUD.prefab Prompt | 1920 x 1080 | 006 프롬프트.png | 상호작용 대상 앞 |
| 007 | 소지품 | HUD | 공통 | Assets/UI/HUD.prefab Items | 1920 x 1080 | 007 소지품.png | 오른쪽 아래. 캡처는 4회차 조합(1회차는 3 카드) |
| 008 | BIS 전광판 첫 버스 전 | 월드 2D | 1 4 | Assets/Graybox/PH/PH_BIS.prefab RowsBefore | 1400 x 630 (실물 1.60 x 0.72 m) | 008 BIS 전광판 첫 버스 전.png | 1-1, 4-11 R1_Stop R4_Stop |
| 009 | BIS 전광판 첫 버스 뒤 | 월드 2D | 1 4 | Assets/Graybox/PH/PH_BIS.prefab RowsAfter | 1400 x 630 (실물 1.60 x 0.72 m) | 009 BIS 전광판 첫 버스 뒤.png | 1-1, 4-12 R1_Stop R4_Stop |
| 010 | 현금 없는 버스 안내문 | 월드 2D | 1 | Assets/Graybox/PH/PH_Notice_Cashless.prefab | 1400 x 1000 (실물 0.42 x 0.30 m) | 010 현금 없는 버스 안내문.png | 1-1 R1_Stop 구석 |
| 011 | 버스 번호판 | 월드 2D | 1 4 | Assets/Graybox/PH/PH_Bus.prefab Plate_112 | 1400 x 280 (실물 2.00 x 0.40 m) | 011 버스 번호판.png | 1-3, 4-15 R1_Stop R1_Storefront R4_Storefront R4_Stop. R4_Stop Bus3만 글자가 112 |
| 012 | 마싱 | HUD | 1 4 | Assets/UI/HUD.prefab Mash | 1920 x 1080 | 012 마싱.png | 1-3, 4-15 버스 계단 |
| 013 | 단말기 안내문 | 월드 2D | 1 | Assets/Graybox/PH/PH_BusTerminal.prefab Notice_Cashless | 635 x 1400 (실물 0.22 x 0.49 m) | 013 단말기 안내문.png | 1-3 버스 안 |
| 014 | 버거대왕 간판 | 월드 2D | 1 4 | Assets/Graybox/PH/PH_Storefront.prefab Sign | 1400 x 280 (실물 4.00 x 0.80 m) | 014 버거대왕 간판.png | 1-4 R1_Storefront R4_Storefront, 실내 씬에도 있음 |
| 015 | 당기세요 스티커 | 월드 2D | 1 4 | Assets/Graybox/PH/PH_Door_Glass.prefab Sticker_Pull | 1400 x 700 (실물 0.24 x 0.12 m) | 015 당기세요 스티커.png | 1-4, 4-1, 4-2 |
| 016 | 자막 화자 | HUD | 공통 | Assets/UI/HUD.prefab Subs | 1920 x 1080 | 016 자막 화자.png | 대사 자막. 화자와 핵심어만 색 |
| 017 | 포스터 누구나 쉽고 빠르게 | 월드 2D | 1 4 | Assets/Graybox/PH/PH_Poster.prefab | 980 x 1400 (실물 0.70 x 1.00 m) | 017 포스터 누구나 쉽고 빠르게.png | 1-7 R1_Store 벽 |
| 018 | 점검 중 표시 | 월드 2D | 1 2 3 4 | Assets/Graybox/PH/PH_Kiosk_Broken.prefab Notice | 1400 x 1042 (실물 0.36 x 0.27 m) | 018 점검 중 표시.png | 옆 키오스크. R2 R3 씬은 꺼짐 |
| 019 | 키오스크 아래판 | 월드 2D | 1 2 3 | Assets/Graybox/PH/PH_Kiosk.prefab Plate | 2285 x 2400 (실물 0.56 x 0.58 m) | 019 키오스크 아래판.png | 키오스크 몸체 SCAN PRINT CARD |
| 020 | 카드 전용 스티커 | 월드 2D | 1 4 | Assets/Graybox/PH/PH_Kiosk.prefab Sticker_CardOnly | 1400 x 525 (실물 0.16 x 0.06 m) | 020 카드 전용 스티커.png | 1-7 키오스크 몸체 |
| 021 | 시선 라벨 | HUD | 공통 | Assets/UI/HUD.prefab Views | 1920 x 1080 | 021 시선 라벨.png | 키오스크 앞 왼쪽 아래 |
| 022 | 눈치 | HUD | 공통 | Assets/UI/HUD.prefab Nunchi | 1920 x 1080 | 022 눈치.png | 키오스크 앞 왼쪽 세로 막대 |
| 023 | 1회차 메뉴 | 키오스크 | 1 | Assets/UI/Kiosk/R1/Pack_R1.prefab Screen_menu | 1080 x 1920 | 023 1회차 메뉴.png | 1-7 |
| 024 | 키오스크 토스트 | 키오스크 | 공통 | Assets/Graybox/PH/PH_Kiosk.prefab Overlay_Toast | 1080 x 1920 | 024 키오스크 토스트.png | 거절 문구. 캡처는 품절 |
| 025 | 1회차 결제 | 키오스크 | 1 | Assets/UI/Kiosk/R1/Pack_R1.prefab Screen_pay | 1080 x 1920 | 025 1회차 결제.png | 1-8 |
| 026 | 1회차 주문 완료 | 키오스크 | 1 | Assets/UI/Kiosk/R1/Pack_R1.prefab Screen_done | 1080 x 1920 | 026 1회차 주문 완료.png | 1-8 내 번호 274 |
| 027 | 호출판 | 월드 2D | 1 2 | Assets/Graybox/PH/PH_PickupBoard.prefab | 1400 x 663 (실물 1.31 x 0.62 m) | 027 호출판.png | 1-10, 2-7. 숫자는 코드가 넣음 |
| 028 | 컵 라벨 | 월드 2D | 1 2 4 | 씬 Pickup_Shelf/Cup/Label, Carried_Bag/Cup/Label | 747 x 1400 (실물 0.08 x 0.15 m) | 028 컵 라벨.png | 1-10, 2-8 픽업 대. R2는 아메리카노 |
| 029 | 2회차 메뉴 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_menu | 1080 x 1920 | 029 2회차 메뉴.png (뜻풀이 끔), 029 2회차 메뉴 뜻풀이 켬.png | 2-3 |
| 030 | 2회차 메뉴 선택됨 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_menu on_americano | 1080 x 1920 | 030 2회차 메뉴 선택됨.png | 2-3 아메리카노 선택 뒤 |
| 031 | 2회차 샷 추가 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_shot | 1080 x 1920 | 031 2회차 샷 추가.png | 2-4 |
| 032 | 2회차 얼음 양 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_ice | 1080 x 1920 | 032 2회차 얼음 양.png | 2-4 |
| 033 | 2회차 쿠폰 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_coupon | 1080 x 1920 | 033 2회차 쿠폰.png | 2-4 |
| 034 | 2회차 적립 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_point | 1080 x 1920 | 034 2회차 적립.png | 2-4 |
| 035 | 2회차 결제 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_pay | 1080 x 1920 | 035 2회차 결제.png | 2-6 |
| 036 | 2회차 주문 완료 | 키오스크 | 2 | Assets/UI/Kiosk/R2/Pack_R2.prefab Screen_done | 1080 x 1920 | 036 2회차 주문 완료.png | 2-7 번호 275 |
| 037 | 3회차 영화 선택 | 키오스크 | 3 | Assets/UI/Kiosk/R3/Pack_R3.prefab Screen_movie | 1080 x 1920 | 037 3회차 영화 선택.png | 3-3 |
| 038 | 3회차 상영관 | 키오스크 | 3 | Assets/UI/Kiosk/R3/Pack_R3.prefab Screen_hall | 1080 x 1920 | 038 3회차 상영관.png (뜻풀이 끔), 038 3회차 상영관 뜻풀이 켬.png | 3-2, 3-3 뜻 풀이 |
| 039 | 3회차 좌석 | 키오스크 | 3 | Assets/UI/Kiosk/R3/Pack_R3.prefab Screen_seat | 1080 x 1920 | 039 3회차 좌석.png (뜻풀이 끔), 039 3회차 좌석 뜻풀이 켬.png | 3-4 |
| 040 | 3회차 좌석 선택됨 | 키오스크 | 3 | Assets/UI/Kiosk/R3/Pack_R3.prefab Screen_seat on_1_2 | 1080 x 1920 | 040 3회차 좌석 선택됨.png | 3-4 B3 선택 뒤 |
| 041 | 옆 글자 문자 번호 | HUD | 3 | Assets/UI/HUD.prefab SideNote | 1920 x 1080 | 041 옆 글자 문자 번호.png | 3-8 문자 번호 임시 표시 T17 |
| 042 | 3회차 문자 번호 | 키오스크 | 3 | Assets/UI/Kiosk/R3/Pack_R3.prefab Screen_sms | 1080 x 1920 | 042 3회차 문자 번호.png | 3-8 |
| 043 | 그만두기 | HUD | 3 4 | Assets/UI/HUD.prefab GiveUp | 1920 x 1080 | 043 그만두기.png | 게이지가 차면 오른쪽 아래 |
| 044 | 선택지 3회차 | HUD | 3 | Assets/UI/HUD.prefab Choice | 1920 x 1080 | 044 선택지 3회차.png | 3회차 실패 선택지. 문구는 코드가 넣음 |
| 045 | 3회차 결제 | 키오스크 | 3 | Assets/UI/Kiosk/R3/Pack_R3.prefab Screen_pay | 1080 x 1920 | 045 3회차 결제.png | 3-9 |
| 046 | 3회차 발권 완료 | 키오스크 | 3 | Assets/UI/Kiosk/R3/Pack_R3.prefab Screen_done | 1080 x 1920 | 046 3회차 발권 완료.png | 3-9 |
| 047 | 쪽지 흐림 | 소지품 2D | 4 | Assets/Graybox/PH/PH_Hand.prefab Hand_Wallet/Note | 875 x 1400 (실물 0.05 x 0.08 m) | 047 쪽지 흐림.png | 4-0 돋보기 없이 |
| 048 | 쪽지 | 소지품 2D | 4 | Assets/Graybox/PH/PH_Hand.prefab Hand_Wallet/Note | 875 x 1400 (실물 0.05 x 0.08 m) | 048 쪽지.png | 4-0 돋보기로 |
| 049 | 지갑 안 | 소지품 2D | 2 4 | Assets/Graybox/PH/PH_Hand.prefab Hand_Wallet | 1400 x 824 (실물 0.17 x 0.10 m) | 049 지갑 안.png | 4-0, 4-0a 지갑 열기 |
| 050 | 당기세요 스티커 흐림 | 월드 2D | 4 | Assets/Graybox/PH/PH_Door_Glass.prefab Sticker_Pull/Blurred | 1400 x 700 (실물 0.24 x 0.12 m) | 050 당기세요 스티커 흐림.png | 4-1 돋보기 없이 |
| 051 | 포스터 흐림 | 월드 2D | 4 | Assets/Graybox/PH/PH_Poster.prefab Blurred | 980 x 1400 (실물 0.70 x 1.00 m) | 051 포스터 흐림.png | 4-3 돋보기 없이 |
| 052 | 카드 전용 스티커 흐림 | 월드 2D | 4 | Assets/Graybox/PH/PH_Kiosk.prefab Sticker_CardOnly | 1400 x 525 (실물 0.16 x 0.06 m) | 052 카드 전용 스티커 흐림.png | 4-3 돋보기 없이 |
| 053 | 키오스크 아래판 흐림 | 월드 2D | 3 4 | Assets/Graybox/PH/PH_Kiosk.prefab Plate/Blurred | 2215 x 2400 (실물 0.54 x 0.58 m) | 053 키오스크 아래판 흐림.png | 돋보기 없이 |
| 054 | 4회차 첫 화면 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_idle | 1080 x 1920 | 054 4회차 첫 화면.png | 4-4 |
| 055 | 4회차 메뉴 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_menu | 1080 x 1920 | 055 4회차 메뉴.png | 4-5 |
| 056 | 남은 시간 표시 | 키오스크 | 4 | Assets/Graybox/PH/PH_Kiosk.prefab Overlay_Timer | 1080 x 1920 | 056 남은 시간 표시.png | 4-9 오른쪽 위 |
| 057 | 4회차 메뉴 목록 열림 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_menu list | 1080 x 1920 | 057 4회차 메뉴 목록 열림.png | 4-5 숨은 메뉴 버튼 |
| 058 | 4회차 큰 글씨 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Content 배율 1.6 | 1080 x 1920 | 058 4회차 큰 글씨.png | 4-5a 임시 T21 |
| 059 | 4회차 팝업 코드 등록 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_pop_code | 1080 x 1920 | 059 4회차 팝업 코드 등록.png | 4-8 |
| 060 | 4회차 로봇 인증 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_pop_robot | 1080 x 1920 | 060 4회차 로봇 인증.png (뜻풀이 끔), 060 4회차 로봇 인증 뜻풀이 켬.png | 4-8 |
| 061 | 4회차 로봇 인증 체크됨 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_pop_robot check_on | 1080 x 1920 | 061 4회차 로봇 인증 체크됨.png | 4-8 |
| 062 | 4회차 팝업 앱 가입 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_pop_app | 1080 x 1920 | 062 4회차 팝업 앱 가입.png | 4-8 |
| 063 | 4회차 팝업 포인트 적립 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_pop_point | 1080 x 1920 | 063 4회차 팝업 포인트 적립.png | 4-8 작은 건너뛰기 |
| 064 | 4회차 결제 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_pay | 1080 x 1920 | 064 4회차 결제.png (뜻풀이 끔), 064 4회차 결제 뜻풀이 켬.png | 4-10 |
| 065 | 4회차 결제 카드 전용 깜빡임 | 키오스크 | 4 | Assets/UI/Kiosk/R4/Pack_R4.prefab Screen_pay card_on | 1080 x 1920 | 065 4회차 결제 카드 전용 깜빡임.png | 4-10 지폐 튕김 |
| 066 | BIS 전광판 흐림 | 월드 2D | 4 | Assets/Graybox/PH/PH_BIS.prefab Blurred | 1400 x 630 (실물 1.60 x 0.72 m) | 066 BIS 전광판 흐림.png | 4-11 돋보기 없이 |
| 067 | 현금 없는 버스 안내문 흐림 | 월드 2D | 4 | Assets/Graybox/PH/PH_Notice_Cashless.prefab Blurred | 1400 x 1000 (실물 0.42 x 0.30 m) | 067 현금 없는 버스 안내문 흐림.png | 4-13 돋보기 없이 |
| 068 | 버스 번호판 흐림 | 월드 2D | 4 | Assets/Graybox/PH/PH_Bus.prefab Plate_Blur | 1400 x 280 (실물 2.00 x 0.40 m) | 068 버스 번호판 흐림.png | 4-15 돋보기 없이 |
| 069 | 손목시계 | 소지품 2D | 4 | Assets/Graybox/PH/PH_Hand.prefab Hand_Watch | 350 x 1400 (실물 0.06 x 0.24 m) | 069 손목시계.png | 4-16 숫자 없는 바늘 |
| 070 | 단말기 안내문 흐림 | 월드 2D | 4 | Assets/Graybox/PH/PH_BusTerminal.prefab Notice_Cashless | 635 x 1400 (실물 0.22 x 0.49 m) | 070 단말기 안내문 흐림.png | 4-20 돋보기 없이 |
| 071 | 선택지 4회차 | HUD | 4 | Assets/UI/HUD.prefab Choice | 1920 x 1080 | 071 선택지 4회차.png | 4-21 단말기 앞 |
| 072 | 엔딩 문구 | HUD | 엔딩 | Assets/UI/HUD.prefab End Stat, Source | 1920 x 1080 | 072 엔딩 문구.png | E-2 |
| 073 | 엔딩 제목 | HUD | 엔딩 | Assets/UI/HUD.prefab End EndTitle | 1920 x 1080 | 073 엔딩 제목.png | E-2 |
| 074 | HUD 전체 겹침 확인 | 참고 | 공통 | Assets/UI/HUD.prefab | 1920 x 1080 | 074 HUD 전체 겹침 확인.png | 요소를 한꺼번에 켠 배치 확인용. 게임에서 이 조합은 안 나옴 |
| 075 | 영수증 들고 보기 | 미사용 | 없음 | 씬 Receipt_View(R1_Store R2_Cafe R3_Cinema R4_Store 등) | 735 x 1400 (실물 0.11 x 0.20 m) | 075 영수증 들고 보기.png | 회차 코드 안 씀. 씬에 꺼진 채 남음 |
| 076 | 영수증 인쇄면 | 미사용 | 없음 | Assets/Graybox/PH/PH_Kiosk.prefab KioskRig/ReceiptCanvas | 592 x 2000 (캔버스 296 x 1000의 2배) | 076 영수증 인쇄면.png | 회차 코드 안 씀 |
| 077 | 호출판 흐림 | 미사용 | 없음 | Assets/Graybox/PH/PH_PickupBoard.prefab Blurred | 1400 x 663 (실물 1.31 x 0.62 m) | 077 호출판 흐림.png | 호출판이 나오는 1, 2회차는 흐림 없음 |
| 078 | 원본 첫 화면 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_idle.prefab) | 1080 x 1920 | 078 원본 첫 화면.png (뜻풀이 끔), 078 원본 첫 화면 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 079 | 원본 매장 포장 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_place.prefab) | 1080 x 1920 | 079 원본 매장 포장.png (뜻풀이 끔), 079 원본 매장 포장 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 080 | 원본 회원 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_member.prefab) | 1080 x 1920 | 080 원본 회원.png (뜻풀이 끔), 080 원본 회원 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 081 | 원본 메뉴 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_menu.prefab) | 1080 x 1920 | 081 원본 메뉴.png (뜻풀이 끔), 081 원본 메뉴 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 082 | 원본 구성 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_option.prefab) | 1080 x 1920 | 082 원본 구성.png (뜻풀이 끔), 082 원본 구성 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 083 | 원본 사이드 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_side.prefab) | 1080 x 1920 | 083 원본 사이드.png (뜻풀이 끔), 083 원본 사이드 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 084 | 원본 음료 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_drink.prefab) | 1080 x 1920 | 084 원본 음료.png (뜻풀이 끔), 084 원본 음료 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 085 | 원본 추가 권유 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_upsell.prefab) | 1080 x 1920 | 085 원본 추가 권유.png (뜻풀이 끔), 085 원본 추가 권유 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 086 | 원본 장바구니 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_cart.prefab) | 1080 x 1920 | 086 원본 장바구니.png (뜻풀이 끔), 086 원본 장바구니 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 087 | 원본 결제 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_pay.prefab) | 1080 x 1920 | 087 원본 결제.png (뜻풀이 끔), 087 원본 결제 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 088 | 원본 카드 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_card.prefab) | 1080 x 1920 | 088 원본 카드.png (뜻풀이 끔), 088 원본 카드 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 089 | 원본 결제 중 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_paying.prefab) | 1080 x 1920 | 089 원본 결제 중.png (뜻풀이 끔), 089 원본 결제 중 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 090 | 원본 카드 빼기 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_cardout.prefab) | 1080 x 1920 | 090 원본 카드 빼기.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 091 | 원본 완료 | 프로토타입 기준 참고 | 없음 | 삭제됨(이전 Assets/UI/Kiosk/Screen_done.prefab) | 1080 x 1920 | 091 원본 완료.png (뜻풀이 끔), 091 원본 완료 뜻풀이 켬.png | 프로토타입 기준 참고. 프리팹이 main에서 삭제되어 삭제 전 캡처를 남김 |
| 092 | 원본 안내창 | 프로토타입 기준 참고 | 없음 | Assets/Graybox/PH/PH_Kiosk.prefab Overlay_Info | 1080 x 1920 | 092 원본 안내창.png (뜻풀이 끔), 092 원본 안내창 뜻풀이 켬.png | 프로토타입 기준 참고. 회차 Pack은 안 씀. 삭제 전 캡처 |

제작 중으로 남은 항목은 없습니다. Pack_R1, Pack_R2, Pack_R3, Pack_R4 모두 있고 각각 R1_Store, R2_Cafe, R3_Cinema, R4_Store 씬에 들어가 있습니다.

찾았지만 없는 것: 메뉴판(벽 메뉴판은 어느 씬에도 없음).

Screen_ 원본 14개는 main에서 프리팹이 삭제됐습니다. 그 항목의 캡처와 요소표는 삭제 전 것을 프로토타입 기준 참고로 남겼습니다.

캡처 읽는 법
- 키오스크 뜻 풀이는 끈 것이 기본 파일이고 켠 것은 `뜻풀이 켬`이 붙습니다. `뜻풀이 켬` 파일이 없는 화면은 KioskReveal 요소가 없어 켜도 같은 그림이라 한 장만 두었습니다. 회차 Pack에서 뜻 풀이가 있는 화면은 3회차 상영관뿐입니다.
- 게임 안 키오스크는 이 그림이 쿼드에 번져 나옵니다(3, 4회차 등). 캡처는 번짐 전 원본입니다.
- HUD의 회색 배경과 월드의 어두운 배경은 캡처용입니다. 코드가 넣는 글자와 값(자막, 프롬프트, 선택지, 번호, 금액, 눈치 60%, 마싱 6 / 10)은 코드에 있는 문구로 넣은 샘플입니다.
- 요소표의 위치는 왼쪽 위가 0,0인 캔버스 px입니다. 월드 면은 부모 기준 로컬 좌표입니다.

## 고치는 방법

1. 프리팹을 Prefab Mode로 열고 해당 화면 오브젝트를 켜서 작업한 뒤 원래 켜짐 상태로 되돌려 저장합니다(Pack의 Screen_는 꺼진 채, HUD의 Title, End도 꺼진 채).
2. 오브젝트 이름, 버튼 id(KioskButton), 키(KioskField)는 코드가 씁니다. 요소표의 코드 참조가 아니오가 아닌 요소는 지우거나 이름을 바꾸지 않습니다.
3. 글자는 요소표의 글자 교체가 `교체 가능`이면 프리팹에서 바로 바꿉니다. `코드가 씀`은 프리팹에서 바꿔도 덮이므로 해당 담당에게 문구 변경을 요청합니다.
4. 버튼은 RectTransform 사각형이 곧 터치 판정입니다. 크기를 바꾸면 판정도 같이 바뀌니 의도한 크기로 둡니다.
5. 월드 글자는 Sharp와 Blurred 두 벌이 짝이고, 뜻 풀이는 레이어 KioskReveal의 자식 Canvas 안에 둡니다.

## 공통 색과 폰트

| 구분 | 값 |
|---|---|
| 시작 화면 | 배경 #E8E0CF, 제목 #2D2822, 보조 글자 #6D6456 |
| 자막과 HUD 글자 | 흰색 + 외곽선 재질 Hud_MalgunOS SDF Outline |
| 자막 강조색 | 플레이어와 노랑 #F3D24B, 다른 인물 #C9C1B4, 뒤 손님과 빨강 #E8584A, 알바생과 초록 #7FD08A, 키오스크와 파랑 #7CC6EE |
| 소지품 | 든 것 #F3D24B, 안 든 것 #DDD5C6 |
| HUD 판 | 선택지와 그만두기 #000000 알파 72%, 마싱 판 알파 50%, 막대 #E6DBCC |
| 엔딩 | 배경 검정, 글자 흰색 |
| 1, 4회차 버거대왕 Pack | 빨강 #C8291F, 크림 #FFFDF8, #FFF6E6, 진한 갈색 #3A2416, 글자 #6B4A30, #8D7A64 |
| 2회차 숲길 커피 Pack | 초록 #1F5A45, #2F7A5D, 크림 #FFFDF8, #F3EAD6, 글자 #8F8270, #B0A58F |
| 3회차 별빛 시네마 Pack | 와인 #2E0E1D, #3F1529, #6E1733, 금색 #E0B252, 좌석 #A8567A, 글자 #FBF1E3, #C8A9B3, #9C7F8A |
| 프로토타입 기준 참고(Screen_ 원본) | 빨강 #CB4139, 노랑 #FFF3B4, 크림 #FFFDF8, 글자 #2A1A10 |

| 폰트 | 어디에 |
|---|---|
| Assets/UI/Fonts/Hud_MalgunOS SDF (TMP 동적) | HUD 전체, Pack의 보통 굵기 글자 |
| Assets/UI/Kiosk/Art/Kiosk_MalgunBold SDF (TMP) | Pack의 굵은 글자 |
| Assets/UI/Fonts/Store_KoreanSDF (TMP 정적) | 포스터, 안내문, 스티커, 영수증 등 3D 글자. 정적이라 없는 글자가 빠지니 문구를 바꾸면 확인 필요 |
| Assets/Fonts BusanDandiHandwriting SDF | 쪽지 손글씨 |
| LiberationSans SDF | 호출판 숫자(Ready, Call) |
| LegacyRuntime (uGUI Text) | Screen_ 원본 14개, BIS, 번호판, 간판, 당기세요, 호출판 제목, 키오스크 오버레이 |

글자 크기는 요소표에 화면별로 있습니다. 가장 작은 글자는 1회차 15, 2회차 14, 3회차 13, 4회차 11입니다. HUD는 자막 28, 프롬프트 26, 선택지 32입니다. 키오스크 그림은 Assets/UI/Kiosk/Art 의 PNG 70장이고, 요소표 글자 내용 칸에 `그림:` 으로 파일 이름을 적었습니다.

## 현재 해상도 기준

| 대상 | 기준 |
|---|---|
| HUD | Screen Space Overlay, CanvasScaler Scale With Screen Size, 기준 1920 x 1080, 높이 맞춤(Match 1). 캡처는 1920 x 1080 |
| 키오스크 화면 | World Space 캔버스 1080 x 1920, RT_Base와 RT_Sharp 1080 x 1920, 화면 쿼드 실물 0.42 x 0.75 m |
| 영수증 인쇄면 | 캔버스 296 x 1000, RT_Receipt 592 x 2000 |
| 월드 면 | 목록의 실물 크기. 캔버스 글자 면은 BIS 1500 x 660, 번호판과 간판 2000 x 400, 호출판 1250 x 560, 당기세요 480 x 240 |

## 금지 사항

- 실제 상표와 실제 서비스 이름 금지.
- 화면과 문서에 가운데점, 긴 줄표, 화살표 기호, 원문자, 곱하기표 금지(치수는 x).
- 나이 숫자, 성별, 호칭 금지.
- UI에 사용법 문장 금지. 조작 안내는 키와 명사 라벨만.
- 외부 텍스처와 모델은 그레이박스 규칙을 따릅니다. 씬과 UI를 코드로 생성하지 않습니다.

## 고칠 때 확인할 것

지금 자료에서 찾은 것입니다. 판단이 필요한 것은 사용자에게 묻습니다.

| 번호 | 내용 |
|---|---|
| 072 | 출처 글자에 나이 숫자 `만 55세 이상`. 시트 문구 그대로(임시 T32, 근거는 Docs/STAT_CHECK.md) |
| 023, 057 | 불고기 버거 세트 가격이 1회차 8,900원, 4회차 코드 7,900원으로 다름 |
| 014, 015 | R2_Cafe, R3_Cinema 씬에도 버거대왕 간판과 당기세요가 켜져 있음. 카페와 영화관 간판이 없음 |
| 029, 037 | Pack은 숲길 커피, 별빛 시네마인데 씬 간판은 버거대왕 |
| 055 | 4회차 프로필은 뜻 풀이 숨김이 켜져 있지만 Pack_R4에는 KioskReveal 요소가 없음. 1, 2회차 Pack도 없음 |
| 075 | 씬 영수증 내용이 K-BBQ 스모키 비프로 지금 주문과 다르고, 회차 코드가 쓰지 않음 |
| 064, 087 | 결제 화면 작은 글자에 `K-Pay` 표기. 실제 서비스 이름일 수 있어 교체 필요 |
| 041 | 문자 번호는 임시 표시(T17). 휴대폰 UI로 바뀔 수 있음 |
| 058 | 큰 글씨는 임시 연출(T21). 레퍼런스가 오면 교체 |
| 폴더 | Assets/UI/Kiosk/R1 1 은 빈 폴더 |
