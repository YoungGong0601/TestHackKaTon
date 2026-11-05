# PH 프리팹 인계

`Assets/Art3D/Models/PH` 모델을 친구 프리팹(`Assets/Graybox/PH`)에 넣는 방법과 상태다. 표는 `모델링목록.md`, 실물은 프리팹과 코드이며 다르면 실물이 맞다.

## 넣는 방법

`Tools/키오스크/PH 프리팹에 모델 넣기` 를 누른다. 머티리얼을 맞춘 뒤 `Assets/Art3D/PH_Map.json` 대로 `Visual` 아래 회색 메시만 지우고 모델을 넣는다. 앵커, 콜라이더, 글자는 건드리지 않고, 찾지 못한 자리는 경고만 남긴다. 다시 눌러도 된다.

## 상태

- 규격 검사 `ph_check.py` 60행 통과. 실물 비교 `ph_fit.py` 는 나머지가 맞고 아래만 회색 상자보다 크다. 모두 의도한 것이다: 지팡이 손잡이, 문 손잡이, 신발장 소품, 표지판 받침, 버스 문 손잡이 봉, 키오스크 NEW 스티커, 의자 등받이, 부스 등받이, 작업대 그리들, 튀김기 연도, 컵 뚜껑과 빨대, 스쿠터 핸들.
- Unity 확인: `3D 에셋 적용` 은 실제 Unity 에서 경고 0개로 돌았다. 모델 넣기는 사본에서 `JWBuild.FillPrefabs` 로 경고 0개로 돌았다.
- `Assets/Art3D` 와 `Assets/Editor/Art3DTools.cs` 는 커밋했다. `ArtSource` 는 커밋하지 않았다.

## 남은 일

2026-11-05 밤 기준이다. 모델 적용은 `Assets/JeongWoo` 사본에서 끝냈다(`Tools/JeongWoo/사본 다시 만들기`, 설명은 `Assets/JeongWoo/README.md`).

1. `PH_BusInterior` 모델을 만들었다(`scripts/PH/bus_interior.py`, Models/PH, PH_Map 1행 추가).
2. 사람은 사본에서 정적 메시 대신 리깅 모델을 쓴다. `Graybox/Npc/*.controller`, `NpcLook` 의 pose.
3. 예전 메뉴 `PH 프리팹에 모델 넣기` 는 이제 `Assets/Graybox` 프리팹만 고친다. 사본은 건드리지 않는다.
4. 친구가 올린 노션 4회차 그레이박스(`R1_*`, `R2_Cafe`, `R3_Cinema`, `R4_*` 씬)에는 아직 3D 를 입히지 않았다. 사본은 기존 흐름 기준이다.
5. 기획 쪽 미반영: 회차별 손, 지갑, 지폐, 카페, 영화관, "카드 전용" 스티커의 흐림 상태.

## 규칙

- 원본 에셋은 `Assets/Art3D/Models/<카테고리>`, 소스는 `ArtSource/Blender`, 스크립트는 `ArtSource/Blender/scripts/PH`.
- 규격 행은 `ph_spec.py`, 맵은 `python3 ArtSource/Blender/scripts/PH/ph_map.py` 로 만든다.
- 실물 비교: `blender -b --factory-startup --python .../ph_bbox.py -- /tmp/b.json` 후 `python3 .../ph_fit.py Assets/Graybox/PH /tmp/b.json`.
- 영수증 `Receipt/Paper/Visual/Sheet` 는 KioskReceipt.cs 가 메시를 만들므로 교체하지 않는다. 돋보기 원점은 렌즈 중심이고 반지름은 Lens_Radius 0.06 이다. Cover 는 Z 로 180도 돌아 있다.
- Street 씬 `Rail_E` 는 회색 메시 `Visual/Mesh` 의 X 스케일로 길이 80.4 를 만든다. 메시를 바꾸면 이 값이 사라지므로 메뉴를 돌린 뒤 인스턴스 루트 X 스케일을 0.941 로 맞춘다.
- 현관문은 복도 쪽(+Z)으로 음수 각도로 연다. 버스 DoorLeafB 는 0.25~0.3m 만 민다. 유리문 매장 쪽 스티커는 단면이라 Double Sided 를 켜지 않는다.
- 사람 모습 번호: OfficeMan 0, Ajumma 1, StudentWoman 2, StudentMan 3, YoungWoman 4, OldMan 5, SuitMan 6, Youth 7, Staff 8. 직원은 인스턴스 `NpcLook.look` 에 8 을 넣는다.
