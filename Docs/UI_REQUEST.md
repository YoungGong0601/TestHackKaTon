# UI 요청 (R2, Pack_R2.prefab)

코드는 아래 키가 없어도 돌아간다. 프리팹에 넣으면 바로 표시된다. KioskField 추가 뒤 Collect.

| 화면 | 필요 | id 또는 key | 지금 상태 |
|---|---|---|---|
| menu | 라떼 선택 표시 | KioskField on_latte (Btn_latte 아래, Btn_americano/Field_on과 같은 모양) | 없음. 아메리카노만 표시됨 |
| menu | 담은 잔 수 글자 | KioskField cart_count (Deco_Back/Cart_Count, Deco_CartPicked/Cart_Count) | 고정 글자 "0 ITEM", "1 ITEM" |
| shot, ice | 지금 옵션을 고르는 잔 이름 | KioskField cup_name (Deco_Back/Summary_Name) | 고정 글자 "아메리카노". 지금은 토스트로 표시 |
| shot, ice, pay, done | 2잔 기준 합계와 개수 | 고정 글자 Summary_Sub "1개", Total_Count "1 ITEM", Total_Value "4,500원" 을 2잔으로 수정(9,500원, 라떼 5,000원 기준) | 1잔 글자 |

버튼 id는 추가가 필요 없다(americano, latte, icon0~3, next, shot0, shot1, ice0~2 모두 있음).
