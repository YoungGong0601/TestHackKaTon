# 카페 두 대 분담 (정우맥, 정우컴)

정우컴 시작 문구: `너는 정우컴이야 CAFE_SPLIT.md를 읽고 작업시작해줘`

MODELING_SPLIT.md 8절의 카페를 4번(령기컴) 대신 정우맥과 정우컴이 나눕니다. 이 문서가 MODELING_SPLIT.md 보다 우선합니다. 규격과 도구 설명은 Docs/MODELING_PREP.md 의 5절(카페), 7.1, 7.2 를 같이 읽습니다.

CLAUDE.md 와 메모리는 정우컴에 없습니다. 답변은 존댓말로 하고 `~입니다` 말투를 씁니다. 급한 작업입니다. 다듬기보다 끝내는 것이 먼저입니다.

## 1. 분담

Unity 는 정우맥만 씁니다. 정우컴은 Blender 만 씁니다. 두 대가 각자 임포트하면 같은 FBX 의 .meta GUID 가 갈라지기 때문입니다.

| 순서 | 에셋 | 모델 이름 | 스크립트 | 담당 |
|---|---|---|---|---|
| 1 | 카페 키오스크 | PH_KioskCafe__Body, __WingL, __WingR | PH/kiosk_cafe.py | 정우맥 |
| 2 | 커피 2잔과 캐리어 | PH_CoffeeCups__Set | PH/cafe_cups.py | 정우맥 |
| 3 | 바 카운터 | PH_BarCounter__Body | PH/cafe_bar.py | 정우맥 |
| 4 | 카페 앞면 | PH_CafeFront__Body | PH/cafe_front.py | 정우맥 |
| 5 | 벽, 바닥, 천장, 길, Unity 넣기 전부 | Env_Cafe, DressCafe.cs, PH_Map_Cafe.json | PH/cafe_room.py | 정우맥 |
| 6 | 뒤 선반 | PH_BackShelf__Body | PH/cafe_shelf.py | 정우컴 |
| 7 | 커피 머신 | PH_BackShelf__Machine | PH/cafe_machine.py | 정우컴 |
| 8 | 진열장 | PH_Showcase__Body | PH/cafe_showcase.py | 정우컴 |
| 9 | 둥근 탁자 | PH_CafeTable__Body | PH/cafe_table.py | 정우컴 |
| 10 | 가로수 | PH_StreetTree__Body | PH/cafe_tree.py | 정우컴 |
| 11 | 사무 빌딩 | PH_OfficeBlock__Body | PH/cafe_office.py | 정우컴 |

정우맥이 자기 일을 끝내면 정우컴 목록의 뒤에서부터 가져갑니다. 가져갈 때 이 표의 담당을 정우맥으로 고쳐 main 에 올립니다. 정우컴은 다음 에셋을 시작하기 전에 `git fetch origin` 뒤 `git show origin/main:CAFE_SPLIT.md` 로 이 표를 봅니다. 담당이 바뀐 에셋은 건너뜁니다.

## 2. 정우컴 시작 순서

1. MODELING_SPLIT.md 0절의 환경 확인을 합니다. 번호는 2번입니다.
2. 저장소 루트에서 `git status` 를 보고 `git fetch origin` 뒤 `git switch -c cafe-win origin/main` 입니다. 이미 있으면 `git switch cafe-win` 입니다.
3. `git push origin HEAD:cafe-win` 으로 push 권한을 봅니다. 거부되면 사용자에게 알립니다.
4. Blender 5.2.x 를 찾습니다(PREP 7.1). 없으면 사용자에게 설치를 요청합니다.
5. `blender -b --factory-startup --python-exit-code 1 --python ArtSource/Blender/scripts/setup.py` 를 돌리고 `k3d:` 줄의 베이크 장치가 GPU 인지 봅니다. CPU 면 사용자에게 알리고 CPU 로 계속합니다.
6. 저장소 밖에 시험합니다.
   `K3D_ROOT=<임시폴더> K3D_CACHE=<저장소>/ArtSource/_cache blender -b --factory-startup --python-exit-code 1 --python ArtSource/Blender/scripts/Items/Memo.py`
7. k3d.py, setup.py 는 Windows 실행을 검증한 적이 없습니다. 실패하면 가장 작게 고칩니다. 10분 안에 안 되면 멈추고 사용자에게 보고합니다. 정우맥이 전부 가져갑니다.
8. 사용자에게 한 줄로 보고하고 표의 6번부터 차례로 합니다.

## 3. 정우컴 규칙

MODELING_SPLIT.md 와 다른 점입니다.

1. Unity 를 쓰지 않습니다. 이 프로젝트를 열지 않습니다. 맵 파일, 프리팹, 씬, Dress 스크립트를 고치지 않습니다. 정우맥이 합니다.
2. main 에 push 하지 않습니다. `cafe-win` 브랜치에만 올립니다. .meta 없는 FBX 가 main 에 가면 다른 사람의 임포트가 .meta 를 따로 만듭니다.
3. .meta 를 커밋하지 않습니다. MODELING_SPLIT 11절의 "FBX 만 있고 .meta 가 없는 커밋" 규칙은 여기에 적용하지 않습니다. 정우맥이 임포트해서 올립니다.
4. 커밋할 것은 경로를 지정해 씁니다. `git add -A`, `git add .` 를 쓰지 않습니다.
   - `ArtSource/Blender/scripts/PH/cafe_*.py`
   - `Assets/Art3D/Models/PH/<모델>.fbx`, `<모델>.json`
   - `Assets/Art3D/Textures/<모델>/`
5. 에셋 하나가 끝날 때마다 `git push origin HEAD:cafe-win` 입니다. 커밋 메시지는 `add: 뒤 선반 모델 [2번]` 처럼 씁니다. Co-Authored-By 를 넣지 않습니다. 마지막 커밋에 `[2번 카페 끝]` 을 씁니다.
6. Blender 는 한 번에 1개만 돌립니다. 서브에이전트로 스크립트 초안을 동시에 쓰는 것은 괜찮습니다.
7. 기존 스크립트(table.py, store_kitchen.py 등)는 고치지 않고 복사합니다. 복사한 뒤 export, finish 이름을 전부 바꿉니다. 안 바꾸면 버거집 모델을 덮어씁니다. 남의 스크립트를 돌리지 않습니다.
8. 재질 이름은 자기 모델 이름으로 시작합니다. 유리는 `M_Glass_<프리팹>` 입니다. M_Glass 로 시작하지 않으면 불투명으로 구워집니다. M_Tile_* 는 만들지 않습니다.
9. 글자를 텍스처에 넣지 않습니다. 폰트 문제가 생깁니다. 상표나 실제 브랜드도 넣지 않습니다.

## 4. 정우컴 에셋 규격

공통입니다. 단위는 미터, 정적 메시, 원점은 프리팹 원점입니다. 스크립트 기본형은 PREP 7.2 이고 앞면은 Unity -Z 이므로 `ph.part(A, parts, ph.turn(180))` 입니다. 아래 좌표는 Unity 프리팹 좌표이고 회색 자리의 실측입니다. 회색 Cylinder 는 Y 스케일의 2배가 높이입니다.

매번 미리보기 PNG(ArtSource/Previews)를 실제로 열어 크기, 앞면, 원점을 봅니다. 그리고 `blender -b --factory-startup --python ArtSource/Blender/scripts/k3d.py -- validate Assets/Art3D/Models/PH/<모델>.fbx <높이>` 를 돌립니다. 시점은 1인칭 눈높이 약 1.6 m 입니다. 베이크는 1024 면 충분합니다.

### 6. 뒤 선반 PH_BackShelf__Body

전체 4.4 x 2.36 x 0.33. 바 뒤 벽에 붙는 원목 선반입니다. 플레이어는 바 앞에서 1.5 m 이상 떨어져 봅니다.

| 부품 | 위치 x, y, z | 크기 x, y, z |
|---|---|---|
| Base 하부장 | 0, 0.45, 0 | 4.4, 0.9, 0.32 |
| Back 뒤판 | 0, 1.2, 0.14 | 4.4, 1.6, 0.04 |
| Board0, 1, 2 선반 판 | 0, 1.2 / 1.65 / 2.1, 0 | 4.4, 0.04, 0.3 |
| 소품 21개 | x -1.9, -1.27, -0.64, -0.01, 0.62, 1.25, 1.88, y 각 판 위 | 폭 0.14, 높이 0.12 또는 0.24 |

- 소품은 커피 원두 봉지, 유리병, 시럽병, 머그, 종이컵 묶음을 섞습니다. 글자 없는 무지 라벨입니다.
- Board0 은 x -1.25 ~ -0.55 를 비웁니다. 커피 머신이 들어갈 자리입니다. 그 자리 소품 Item0_1(x -1.27), Item0_2(x -0.64)도 뺍니다.
- 위가 2.36 을 넘지 않습니다. 뒷면은 z +0.165 를 넘지 않습니다. 벽 앞에 붙습니다.

### 7. 커피 머신 PH_BackShelf__Machine

회색 자리 Machine 은 위치 (-0.9, 1.03, -0.02), 크기 0.62 x 0.36 x 0.3 입니다. FillMap 이 Visual 을 통째로 비우고 두 FBX 를 같은 자리에 넣으므로 **선반 좌표 그대로 내보냅니다.** 원점을 옮기지 않습니다.

- 폭 0.62, 깊이 0.3 안, Base 윗면 y 0.9 에서 시작해 y 1.3 까지 씁니다.
- 스테인리스 2그룹 에스프레소 머신입니다. 그룹헤드 2개, 포터필터 2개, 스팀봉, 드립 트레이, 위쪽 컵 받침, 압력계 원판(글자 없음)입니다.

### 8. 진열장 PH_Showcase__Body

전체 1.54 x 0.585 x 0.6. 바 위(y 1.06)에 놓입니다. 원점은 바닥 중앙이고 앞면이 플레이어 쪽입니다.

| 부품 | 위치 x, y, z | 크기 x, y, z |
|---|---|---|
| Base 받침 | 0, 0.04, 0 | 1.5, 0.08, 0.56 |
| Glass 유리 | 0, 0.32, 0 | 1.5, 0.48, 0.56 |
| Shelf 중간판 | 0, 0.3, 0 | 1.44, 0.02, 0.5 |
| Roof 지붕 | 0, 0.57, 0 | 1.54, 0.03, 0.6 |
| Cake0~3 | x -0.54, -0.18, 0.18, 0.54, y 0.13 | 0.22, 0.1, 0.22 |
| Bread0~3 | x 같음, y 0.36 | 0.24, 0.08, 0.16 |

- 케이크 4종과 빵 4종은 서로 다르게 만듭니다. 조각 케이크 접시, 치즈케이크, 초코 케이크, 크루아상, 스콘, 식빵 같은 것입니다.
- 유리는 재질 `M_Glass_PH_Showcase` 입니다. 안쪽 윗면에 얇은 흰 조명 띠를 둡니다.

### 9. 둥근 탁자 PH_CafeTable__Body

전체 0.64 x 0.735 x 0.64. PH/table.py 를 복사해 새 파일로 씁니다. 원판 지름 0.64, **상판 윗면은 y 0.735** 입니다. 씬 소품(냅킨, 빨대)이 이 높이에 놓여 있습니다. 기둥 지름 약 0.06, 바닥 받침 지름 0.4 입니다.

### 10. 가로수 PH_StreetTree__Body

전체 2.95 x 5.1 x 2.6. 줄기 지름 약 0.2, 높이 약 3, 수관은 (0, 3.9, 0) 지름 2.6 에 작은 덩어리 둘(0.7, 3.3, 0.2), (-0.6, 3.4, -0.4)입니다. 밑동 철제 보호판은 1.1 x 0.04 x 1.1 입니다. 투명 잎 카드 없이 울퉁불퉁한 덩어리로 만듭니다. 10 m 밖에서 봅니다.

### 11. 사무 빌딩 PH_OfficeBlock__Body

전체 16 x 30 x 12.85. 몸통 (0, 15, 0) 크기 16 x 30 x 12 입니다. 앞면 z -6 에 1층 로비(높이 3.2), 차양(0, 3.5, -6.4) 크기 16 x 0.2 x 0.9, 위층 유리 띠입니다. 씬에서 스케일 0.52~1.2 로 늘려 쓰니 글자나 동그란 모양이 없는 격자 입면으로 만듭니다. 바닥에서 시작합니다. BuildingBackdrop.py 패턴이고 굽기 없이 재질 몇 개면 됩니다. 멀리서만 봅니다.

## 5. 정우맥이 받는 방법

`git fetch origin cafe-win` 뒤 `git merge --no-edit origin/cafe-win` 로 받습니다. 새 파일뿐이라 충돌이 없습니다. Unity 로 임포트하고 맵 행을 쓴 뒤 .meta 와 재질까지 main 에 같이 올립니다. 맵 행은 FBX 가 있을 때만 씁니다. 모델이 없는 행도 회색 메시를 지웁니다.
