# 네 대 모델링 분담

시작 문구: `너는 n번 컴퓨터야 MODELING_SPLIT.md를 읽고 작업시작해줘`

이 문구를 받은 Claude 는 이 문서를 위에서 아래로 따릅니다. 0절만 끝나면 사용자에게 묻지 않고 진행합니다. 자세한 규격과 재활용 표는 `Docs/MODELING_PREP.md` 에 있습니다. 시작할 때 같이 읽습니다.

CLAUDE.md 와 메모리는 이 저장소에 없습니다. 이 두 문서가 규칙입니다. 답변은 존댓말로 하고 `~입니다` 말투를 씁니다.

Docs/AGENT_RULES.md, Docs/ROUND_PLAN.md, Docs/CONTRACT.md 는 친구의 그레이박스 작업 규칙입니다. 거기 적힌 커밋과 push 금지, 빌더 스크립트 금지, Assets/Art3D 사용 금지, 모델링 제외는 이 작업에 적용하지 않습니다. 이 문서가 우선합니다. 이 컴퓨터에 로컬 CLAUDE.md 가 있어 이 문서와 다르면 시작 보고에 적고 사용자의 말을 따릅니다.

## 0. 가장 먼저: 실행 환경 경고

아래를 확인합니다. 하나라도 아니면 아무 작업도 하기 전에 사용자에게 경고하고 답을 기다립니다. 사용자가 그대로 하라고 하면 진행합니다.

1. 모델이 Opus 5.5(claude-opus-5-5)입니다.
2. 울트라코드가 켜져 있습니다. 세션에 "Ultracode is on" 알림이 없으면 꺼진 것입니다.
3. 추론 강도(effort)가 max 입니다. 직접 확인할 수 없으면 경고가 아니라 시작 보고에 "effort 가 max 인지 확인해 주세요" 를 한 줄 씁니다.
4. 번호와 운영체제가 맞습니다. 1번과 3번은 Mac, 2번과 4번은 Windows 입니다.

## 1. 분담

| 번호 | 컴퓨터 | 맡는 일 | 씬 | 이유 |
|---|---|---|---|---|
| 1번 | 맥북 프로 16 M4 Max 64GB(정우맥) | 버거집, 사람, 마지막 점검(묶음 D) | R1_Storefront, R4_Storefront, R1_Store, R4_Store | 원본 폰트가 전부 있습니다. 씬이 가장 많고 사람 모델을 다시 만드는 일은 Apple 폰트가 필요합니다 |
| 2번 | AERO 15 KD RTX 3060 32GB(정우컴) | 손과 소지품, 엔딩(묶음 A) | Ending_Home | 새 소품 위주라 폰트 제약이 없습니다. 엔딩 손과 씬을 한 대가 맡아 넘겨주는 일을 줄입니다 |
| 3번 | 맥북프로 14 M5 16GB(세민맥) | 버스와 정류장(묶음 B) | R1_Stop, R4_Stop | 버스 텍스처에 Apple 폰트가 필요해 Mac 입니다. 이 결과를 기다리는 컴퓨터가 없어 다른 작업으로 끊겨도 전체가 멈추지 않습니다 |
| 4번 | HP OMEN MAX 16 RTX 5070 Ti 32GB(령기컴) | 카페(묶음 C) | R2_Cafe | 새 모델이 가장 많습니다. GPU 가 가장 강합니다 |

0단계(기존 모델 57개를 PH 프리팹 31개에 넣기)는 이미 끝나서 main 에 있습니다. 메뉴 `Tools/키오스크/PH 프리팹에 모델 넣기` 는 다시 누르지 않습니다. 모든 프리팹을 저장해서 다른 컴퓨터와 충돌합니다.

## 2. 공통 시작 순서

1. 저장소 루트에서 `git status` 를 봅니다. `git fetch origin` 뒤 main 으로 받습니다(`git pull --rebase origin main`). 받기가 막히면 3절 규칙 7 을 따릅니다.
2. `git push --dry-run origin main` 으로 push 권한을 봅니다. 거부되면 사용자에게 알립니다.
3. Unity 6000.3.13f1 과 Blender 5.2.x 를 찾습니다. 경로는 PREP 7.1 입니다. 다른 버전만 있거나 없으면 사용자에게 설치를 요청합니다. 다른 버전으로 프로젝트를 열지 않습니다.
4. `blender -b --factory-startup --python-exit-code 1 --python ArtSource/Blender/scripts/setup.py` 를 돌립니다. `k3d:` 줄을 봅니다. Windows 에서는 베이크 장치가 GPU 여야 합니다. CPU 로 나오면 드라이버를 확인하고 사용자에게 알린 뒤 CPU 로 계속합니다.
5. Library 폴더가 없으면 첫 임포트를 백그라운드로 돌립니다. 끝나기 전에도 Blender 작업은 진행합니다.
   `Unity -batchmode -quit -projectPath . -logFile <임시폴더>/first.log`
   에디터가 열려 있으면 배치가 실패합니다. 사용자에게 닫아 달라고 합니다. 라이선스 오류면 Unity Hub 로그인을 요청합니다. 로그는 커밋하지 않습니다(토큰이 찍힙니다). 3번은 메모리가 작아 첫 임포트가 끝날 때까지 Blender 를 돌리지 않습니다.
6. Windows 는 저장소 밖에 시험합니다. 실패하면 11절입니다.
   `K3D_ROOT=<임시폴더> K3D_CACHE=<저장소>/ArtSource/_cache blender -b --factory-startup --python-exit-code 1 --python ArtSource/Blender/scripts/Items/Memo.py`
   이 문서의 명령은 Git Bash 문법입니다. PowerShell 이면 `$env:K3D_ROOT='...'` 로 쓰고 `& '<전체 경로>\blender.exe' ...` 로 부릅니다. `blender`, `Unity` 는 PREP 7.1 의 전체 경로로 바꿔 씁니다.
7. 사용자에게 한 줄로 보고하고 자기 절의 일을 시작합니다.

## 3. 공통 규칙

PREP 9절이 전체 규칙입니다. 자주 틀리는 것입니다.

1. 내 소유 파일만 저장하고 커밋합니다. 소유는 5~8절에 있습니다. 소유 밖을 고쳐야 하면 고치지 말고 끝날 때 보고합니다.
2. `git add -A`, `git add .` 를 쓰지 않습니다. 경로를 지정하고 `git status`, `git diff --cached --stat` 로 확인합니다.
3. 남의 에셋 스크립트를 돌리지 않습니다. FBX 는 내용이 같아도 항상 바뀝니다.
4. 같은 이름으로 다시 내보낸 FBX 는 그 FBX 를 쓰는 모든 곳이 자동으로 따라갑니다. 사본 Assets/JeongWoo 도 바뀝니다. 다른 자리와 달라야 하면 새 이름으로 내보냅니다. FillMap 은 새 행이 있을 때만 씁니다.
5. 공용 파일은 고치지 않습니다: k3d.py, PH/ph.py, Assets/Editor/Art3DTools.cs, Assets/Editor/DressKit.cs, Assets/Art3D/PH_Map.json, Systems.prefab, Assets/Scripts, Assets/UI, ProjectSettings, Packages, Assets/JeongWoo. 예외는 11절입니다.
6. 새 재질은 자기 에셋 이름으로 시작합니다(M_<에셋>). 유리는 M_Glass_<에셋>, 타일은 M_Tile_<묶음>_<이름>, 런타임 텍스처는 M_Dyn_<에셋> 입니다. 이 접두사가 아니면 굽기에서 불투명으로 합쳐집니다. 공유 타일을 고치지 않고 새 이름의 사본을 만듭니다.
7. 받기가 막히면 내 것이 아닌 파일을 `git stash push -- <파일>` 로 치우고 받습니다. stash 를 pop 하지 않습니다. force push, `--autostash`, git-lfs 를 쓰지 않습니다.
8. 커밋 메시지는 짧은 한글에 `add:`, `edit:`, `fix:`, `remove:` 를 붙이고 끝에 번호를 적습니다. 예: `add: 지폐 모델 [2번]`. Co-Authored-By 를 넣지 않습니다.
9. 플레이 시험은 사람이 합니다. Unity 는 임포트, 모델 넣기, 씬 저장, 캡처에만 씁니다. 빌드하지 않습니다.
10. 기획의 「남은 결정」은 묻지 않고 PREP 2절 기본값으로 진행합니다. 끝날 때 기본값을 쓴 곳을 보고합니다.
11. 서브에이전트나 워크플로를 쓸 때 같은 파일을 동시에 고치지 않습니다. Blender 동시 실행은 1번 3개, 4번 2개, 2번과 3번은 1개까지입니다. 3번은 `K3D_BAKE_SLOTS=2` 로 돌립니다. Unity 와 Blender 를 3번에서 동시에 돌리지 않습니다.

## 4. 일하는 방법

한 묶음(에셋 몇 개)마다 아래를 돕니다. 급이 높은 것부터 합니다. 핵심을 다 끝내고 보통으로 갑니다.

1. 스크립트를 쓰고 돌립니다(PREP 7.2). 미리보기 PNG 를 실제로 열어 봅니다. 크기, 앞면, 원점을 PREP 5절과 맞춥니다.
2. 자기 맵 파일(`Assets/Art3D/PH_Map_<묶음>.json`)에 행을 씁니다(PREP 7.3).
3. Unity 를 돌립니다. `Unity -batchmode -quit -projectPath . -executeMethod Art3DTools.FillMap -phmap PH_Map_<묶음>.json -logFile <임시폴더>/fill.log`. 로그의 `키오스크:` 줄을 전부 읽습니다.
4. 씬 일은 자기 파일 `Assets/Editor/Dress<이름>.cs` 에 씁니다. DressKit 을 부릅니다. 같은 방식으로 `-executeMethod Dress<이름>.All` 을 돌립니다. 로그의 `꾸미기:` 줄을 전부 읽습니다. 경로가 틀리면 경고만 내고 넘어갑니다. 하나라도 있으면 고치고 다시 돌립니다. 경로는 씬 루트부터 끝까지 씁니다.
5. `DressKit.Shot` 으로 씬을 찍어 눈으로 봅니다. 분홍 재질, 남은 회색, 공중에 뜬 물체를 찾습니다. 사람은 플레이 전에는 모두 첫 모습으로 보입니다. 정상입니다.
6. `git status` 를 보고 내 것만 커밋합니다. 같이 넣을 것입니다: 스크립트, FBX, JSON, Textures/<에셋>, Materials 의 내 재질(M_<에셋>*, M_Glass_*, M_Tile_* 중 내가 만든 것), Textures/Tile 의 내 타일, 전부의 .meta, Textures/<에셋>.meta, 원본이면 .blend, 맵 파일, 내 프리팹과 씬, Env 프리팹.
7. `git pull --rebase origin main` 뒤 `git push origin main` 입니다. 끝날 때마다 올립니다. 올리지 않은 일은 다른 컴퓨터가 쓸 수 없습니다.

```csharp
using UnityEngine;
using static DressKit;

public static class DressStop
{
    public static void All()
    {
        var env = Root("Env_Street");
        foreach (var it in Read("Street").items) Place(it, env, Pos(it), Yaw(it));   // 건너뛸 항목은 JWDress.StreetItems 를 봅니다
        SaveEnv(env);
        foreach (var name in new[] { "R1_Stop", "R4_Stop" })
        {
            var s = Open(name);
            PutEnv(s, "Env_Street");
            Off(s, "Bounds/Facade_E", "World/Floor_Road");
            Save(s);
        }
    }
}
```

DressKit 함수는 Read, Open, Save, Find, Off, Move, Look, Model, Root, Place, Pos, Yaw, SaveEnv, PutEnv, Solid, Pole, Blocker, LayoutLights, Sky, Fence, Shot 입니다. 씬 전용 자리에는 `Model(s, 경로, "Models/...fbx")` 를 씁니다. 프리팹 인스턴스 안의 자식은 지울 수 없으니 Off 로 끕니다.

참고 코드는 Assets/JeongWoo/Editor/JWDress.cs 입니다(Street 318-406행, Storefront 440-490행, Store 492-579행, Home 266-313행). 사본 전제가 있으니 복사할 때 각 절의 주의를 지킵니다. 안개, 반사 프로브, Director 호출은 옮기지 않습니다.

씬의 PH_NPC 인스턴스는 전부 look 을 정합니다. 비워 두면 이름 해시로 골라 손님이 직원이나 어르신 모습이 됩니다. 0~8 은 OfficeMan, Ajumma, StudentWoman, StudentMan, YoungWoman, OldMan, SuitMan, Youth, Staff 이고 9 는 어르신, 10 은 카페 직원입니다.

## 5. 1번 정우맥: 버거집, 사람, 마지막 점검

소유: Assets/Art3D/PH_Map_Store.json, 프리팹 PH_Kiosk_R4, PH_Kiosk_Broken, PH_Poster, PH_NPC, 씬 R1_Storefront, R4_Storefront, R1_Store, R4_Store, Env_Storefront, Env_StoreInterior, Assets/Editor/DressStore.cs, 스크립트 PH/npc.py, PH/ph_spec.py, Characters/, 새 PH/kiosk_r4.py, PH/poster.py.

1. 어르신 몸을 먼저 올립니다. 3번이 기다립니다. Characters/NpcOldMan.py 를 복사해 NpcElder.py 를 만듭니다. 소매는 갈색 뜨개, 시계는 스틸 케이스에 가죽 줄로 GrandpaHand 와 맞춥니다. ph_spec.LOOKS 에 "Elder" 를 더하고 PH/npc.py 의 NECK 에 OldMan 값을 복사해 넣은 뒤 `PH/npc.py -- Elder` 만 돌립니다. 양팔이 있는 몸 PH_NPC__Elder_BodyArm(Walker 용)과 오른팔을 지운 몸 PH_NPC__Elder_Body(Arm_Pivot 과 겹치지 않게, look 9 행), 머리 PH_NPC__Elder_Head 를 내보냅니다. 팔을 지우면 목 색 기준이 달라질 수 있으니 미리보기를 봅니다.
2. 카페 직원을 올립니다. 4번이 기다립니다. Characters/NpcStaff.py 를 복사해 NpcCafeStaff.py 로 색과 로고를 바꾸고, LOOKS 에 "CafeStaff", NECK 에 Staff 값을 넣습니다. look 10 입니다.
3. 키오스크입니다. PH/kiosk.py 는 고치지 않습니다(사본이 씁니다). 복사해 PH/kiosk_r4.py 를 만들고 edit_labels 의 sticker 조건을 빼서 PH_KioskR4__Body, PH_KioskR4__Broken 으로 내보냅니다. 맵에는 PH_Kiosk 행(Wing_L/Visual, Wing_R/Visual, 빈 행들)을 복사하고, Visual 은 PH_KioskR4__Body, Cover/Hinge/Visual 은 PH_Kiosk__Cover 입니다. PH_Kiosk_Broken 은 Visual 빈 행 뒤에 새 모델 행을 씁니다.
4. Sticker_CardOnly/Visual 판과 PH_Poster/Visual 판을 넣습니다. store_tex.py 의 poster_kiosk 는 고치지 않습니다(StorePosters 를 사본이 씁니다). 글자 없는 인쇄면을 새로 그려 Textures/PH_Poster 에 둡니다.
5. Env_StoreInterior 와 Env_Storefront 를 DressStore.cs 로 만듭니다. Storefront 씬에도 Env_StoreInterior 를 넣습니다. R 씬은 Single 로드라 유리 너머가 비어 보입니다.
6. 네 씬에 적용합니다. JWDress 와 다른 점입니다: StoreDirector.sharedRoom, 영수증, 안개, 반사 프로브는 뺍니다. 두 Store 씬의 Lights 는 코드가 참조하지 않으니 지우고 Store.json 의 lights 로 바꿉니다(LayoutLights). PH_Bus, BusStop, PlayerSpawn, Bound_Road 이동은 R1, R4 두 Storefront 에 똑같이 합니다. 포스터 자리는 두 Store 씬 모두 (0.75, 2.28) 입니다(D12).
7. 씬 전용 자리입니다. R4_Store: NPCs/Watcher0~4 의 ReactPivot/Visual 과 ReactPivot/HeadPivot/Visual, Counter/Tray_Pass/Visual, NPCs/NPC_Staff 휴대폰. R1_Store: NPCs/NPC_Elder 의 look 9, NPCs/NPC_Elder/ReactPivot/Arm_Pivot/Visual 과 Arm_Pivot/Bill/Visual(2번 결과), PH_Cane.
8. 흐린 사본입니다(D16, PREP 3.7).
9. `git log --oneline --grep "끝\]"` 로 2, 3, 4번의 끝 표시를 보고 마지막 점검을 합니다. pull, Unity 한 번 실행, 씬 8개 캡처, 경고 확인 뒤 사용자에게 보고합니다.

## 6. 2번 정우컴: 손, 소지품, 엔딩

소유: Assets/Art3D/PH_Map_Hand.json, 프리팹 PH_Hand, 씬 Ending_Home, Env_Home, Assets/Editor/DressEnding.cs, 스크립트 PH/hand.py, Hands/, 새 Items/ 파일.

기존 PH_Hand__Card, PH_Hand__Lens, PH_Hand__Memo 는 다시 내보내지 않습니다. 사본과 다른 자리가 같이 바뀝니다. 변형은 아래 새 이름으로 만듭니다.

1. 지폐 PH_Hand__Bill(손 없음)을 먼저 올립니다. 1번이 기다립니다.
2. 어르신 팔 PH_Elder__Arm 을 올립니다. 1번이 기다립니다. 소매, 손, 반지, 시계가 80대 손과 같아야 하므로 바로 아래 항목의 80 손을 먼저 만들고 그것으로 팔을 만듭니다.
3. 나이별 손 PH_Hand__Pointer20, 40, 80 입니다. GrandpaHand.py 에 K3D_HAND_AGE 를 더합니다. 소매 끝은 y -0.8 까지입니다. 80 에는 반지와 시계를 넣습니다. 맵 파일에 Hand_Pointer/Visual 빈 행을 먼저 쓰고 Look_0, 1, 3 행을 씁니다.
4. 지갑 PH_Hand__Wallet, 칸의 카드 PH_Hand__WalletCard, 칸의 지폐 PH_Hand__WalletCash, 쪽지 PH_Hand__WalletNote 입니다. target 규칙은 PREP 5절입니다.
5. 시계 팔 PH_Hand__Watch 와 시침 PH_Hand__WatchHour 입니다. 바늘을 메시에 합치지 않습니다. 문자판은 숫자와 요일창이 없습니다. 이렇게 하면 Apple 폰트가 필요 없습니다.
6. D4 입니다. 80대 손을 같이 구운 PH_Hand__LensHeld, PH_Hand__BillHeld 를 만듭니다. 렌즈 원 안에 손이 들어가지 않게 합니다. 맵 파일에 Hand_Lens/Visual 빈 행을 먼저 쓰고 LensHeld 행을 씁니다. Hand_Bill/Visual 은 BillHeld 입니다.
7. `FillMap -phmap PH_Map_Hand.json` 으로 PH_Hand 를 넣습니다.
8. 엔딩 손 PH_End__HandR(HoldMemo), PH_End__HandL(펼친 손)과 구겨진 쪽지 PH_End__NoteBall 입니다. 소매, 반지, 시계를 모델에 넣습니다.
9. Env_Home 을 DressEnding.cs 로 만듭니다.
   - Home.json 은 HomeEntry, HomeUmbrella, HomeUmbrellaRed, HomeMedicineBag 만 놓습니다. 좌표는 Pos, Yaw 가 아니라 JWDress.Home() 의 식(274-278행)을 복사합니다.
   - Street.json 은 이름이 StreetRoadAlley, StreetDrain, StreetManhole, BuildingVilla, BuildingRealEstate, BuildingSalon, BuildingShopRow 이고 pos 의 y 가 -5~31 인 항목만 오프셋 (0, -0.13, 8.5) 로 놓습니다. 현관과 겹치는 y -8 모듈과 CarHatch 는 빠집니다.
   - StreetLight 는 (-2.3, -0.13, 8.5), (2.3, -0.13, 16) 에 놓습니다. Lamp_Mid, Lamp_Far 는 y 3.8 의 빛이라 Model 을 쓰지 않습니다.
   - Off 는 Room/ 쪽 Ceiling, Wall_Left, Wall_Right, Wall_Back, Wall_Door_L, Wall_Door_R, Wall_Door_Top, Floor_Lino, Floor_Tile 과 Alley/Floor_Alley, Alley/Wall_Alley_W, Alley/Wall_Alley_E, Lamps/Lamp_Mid_Pole, Lamps/Lamp_Far_Pole 입니다.
   - 조명, 안개, 하늘은 바꾸지 않습니다. 씬에 밤 값이 있습니다. 바닥 높이 -0.13 은 코드가 씁니다.
10. 손은 EndHands/End_HandR/Visual, EndHands/End_HandL/Visual, 구겨진 쪽지는 EndHands/End_HandR/Note_Ball 에 Model 로 넣습니다. End_HandR, End_HandL 자체에 넣으면 코드가 쓰는 Note_Flat, Note_Ball 이 지워져 실행 중 오류가 납니다. 회색이 남지 않게 두 손의 Look_3 오브젝트는 끕니다. EndHands/End_HandR/Note_Flat 은 재질만 입힙니다.
11. 지팡이 쥔 오른손 PH_Hand__Cane 은 모델만 만듭니다(D15). 자리가 없으니 맵에 넣지 않습니다.

## 7. 3번 세민맥: 버스와 정류장

소유: Assets/Art3D/PH_Map_Bus.json, 프리팹 PH_Bus, PH_BusInterior, PH_BusTerminal, PH_Notice_Cashless, 씬 R1_Stop, R4_Stop, Env_Street, Assets/Editor/DressStop.cs, 스크립트 PH/bus.py, PH/bus_tex.py, PH/bus_interior.py, 새 PH/ 파일.

이 컴퓨터는 다른 작업에도 쓰입니다. 사용자가 다른 일을 시키면 커밋할 수 있는 지점까지 마치고 push 한 뒤 멈춥니다. 작게 자주 올립니다. 시간이 모자라면 1번이 이어받을 수 있게 보고합니다.

1. PH/bus.py 에 앞문 계단을 더합니다(D6). 같은 이름이라 FillMap 이 필요 없습니다. 사본 버스에도 계단이 생기는 것은 괜찮습니다.
2. PH_BusTerminal 모델, PH_Notice_Cashless 빈 판을 만들고 맵 파일에 씁니다. bus_interior.py 의 x 3.5 단말기를 뺍니다. PH_BusTerminal 안 안내문 중첩 z 를 0.03 에서 0.02 로 당깁니다. FillMap 을 돌립니다.
3. Env_Street 를 만듭니다. JWDress.StreetItems 의 건너뛰기를 지킵니다. 충돌체 Solid, Pole, Blocker 도 같이 넣습니다.
4. R1_Stop, R4_Stop 에 적용합니다. Off 12개, Fence 재질, World/Rail_E 루트 X 스케일 0.94145 와 BoxCollider 길이 85.4 입니다. 하늘은 두 씬 모두 `RenderSettings.skybox = Sky()` 입니다. R1_Stop 에만 StreetSun 값을 씁니다. R4_Stop 은 R4StopDirector 의 배열이 조명을 덮습니다. 씬에 직렬화된 값이라 고쳐도 됩니다. 코드는 고치지 않습니다.
5. 씬 전용 자리입니다: Buses/Bus3/Visual, Buses/Bus3/DoorLeafA/Visual, Buses/Bus3/DoorLeafB/Visual. Npcs/Student, Npcs/Worker, PH_BusInterior/Driver 의 look. BusStop_Area/Notice_Pole 재질. R1_Stop 의 BuildingSalon 을 x 쪽으로 약 0.52 옮깁니다(Env_Street 인스턴스 값으로).
6. 가로등입니다. Street/street_light.py 는 고치지 않습니다. 복사해 PH/street_light_r4.py 로 렌즈를 나눈 PH_StreetLightR4 와 렌즈판을 만듭니다. Lamps/Lamp0~2/Visual 에 넣고, Lamps/LampN/Light 는 지우지 않고 모델 높이에 맞게 옮깁니다. 렌즈판은 Light 아래에 두면 같이 켜집니다.
7. Npcs/Walker/ReactPivot/Visual 에 PH_NPC__Elder_BodyArm, Npcs/Walker/ReactPivot/HeadPivot/Visual 에 PH_NPC__Elder_Head 를 넣고 PH_Cane 을 Walker 자식으로 더합니다. 1번 결과가 없으면 다른 일을 먼저 합니다.
8. 흐린 사본입니다(D16, PREP 3.8). 나중입니다.

## 8. 4번 령기컴: 카페

소유: Assets/Art3D/PH_Map_Cafe.json, 프리팹 PH_Kiosk, PH_BarCounter, PH_Showcase, PH_BackShelf, PH_CafeTable, PH_CafeFront, PH_OfficeBlock, PH_StreetTree, PH_Crosswalk, PH_Road, PH_CoffeeCups, 씬 R2_Cafe, Env_Cafe, Assets/Editor/DressCafe.cs, 스크립트 새 PH/cafe_*.py, PH/kiosk_cafe.py, 새 Food/ 파일.

기존 스크립트를 고치지 말고 복사해서 새 파일로 씁니다(store_counter.py, table.py, FoodDrinkCup.py, kiosk.py). 복사한 스크립트의 export, finish 이름을 반드시 바꿉니다. 기존 모델을 덮으면 버거집과 사본이 바뀝니다.

1. 핵심: 커피 2잔과 캐리어(PH_CoffeeCups), 바 카운터, 카페 키오스크.
   - 키오스크는 PH/kiosk_cafe.py 로 PH_KioskCafe__Body, __WingL, __WingR 을 내보냅니다. edit_labels 의 sticker 조건을 뺍니다. kiosk_tex.py 는 실행하지 않습니다. Textures/Kiosk 를 Windows 대체 글꼴로 덮습니다. 간판과 포스터는 저장소 폰트로 새로 그려 Textures/PH_KioskCafe 에 둡니다. 이름은 숲길 커피입니다.
   - PH_Map_Cafe.json 에 PH_Kiosk 의 Visual, Wing_L/Visual, Wing_R/Visual 빈 행을 먼저 쓰고 새 모델 행을 씁니다. Sticker_CardOnly 는 R2_Cafe 가 꺼 두었으니 판이 필요 없습니다.
2. 보통: 방 벽과 바닥과 천장(Env_Cafe), 카페 앞면, 뒤 선반, 커피 머신, 진열장. 카페 방은 PH_Wall, PH_Floor 를 Off 하고 Env_Cafe 로 덮습니다. 타일은 PREP 7.2 입니다.
3. 나중: 둥근 탁자, 사무 빌딩, 가로수, 길(PH_Road, PH_Crosswalk 는 Off 하고 Env_Cafe 에 Street 모델을 놓습니다).
4. R2_Cafe 의 NPC look 을 정합니다. NPCs/NPC_Staff 는 10(1번 결과), 나머지는 0~7 입니다.

스케일로 크기를 만든 인스턴스(Curb, Rail, Office)는 모델을 넣으면 찌그러집니다. PREP 3.6 을 봅니다.

## 9. 서로 넘겨주는 것

이름을 지켜야 받는 쪽이 찾습니다. 받는 쪽은 pull 뒤 파일이 있으면 씁니다. 없으면 기다리지 말고 다른 일을 합니다. 다른 일이 다 떨어지면 5분마다 `git pull --rebase origin main` 을 최대 6번 합니다. 그래도 없으면 기다리는 파일을 사용자에게 보고하고 멈춥니다.

| 만드는 쪽 | 파일 | 받는 쪽 | 자리 |
|---|---|---|---|
| 2번 | Models/PH/PH_Hand__Bill.fbx | 1번 | R1_Store NPCs/NPC_Elder/ReactPivot/Arm_Pivot/Bill/Visual |
| 2번 | Models/PH/PH_Elder__Arm.fbx | 1번 | R1_Store NPCs/NPC_Elder/ReactPivot/Arm_Pivot/Visual |
| 1번 | Models/PH/PH_NPC__Elder_BodyArm.fbx, PH_NPC__Elder_Head.fbx | 3번 | R4_Stop Npcs/Walker |
| 1번 | PH_NPC look 10 | 4번 | R2_Cafe NPCs/NPC_Staff |

## 10. 끝내는 기준

1. 자기 절의 핵심과 보통 항목이 씬에 들어갔습니다. 나중은 시간이 남으면 합니다.
2. FillMap 로그 경고는 사본용 3행(Hand_Memo, Cover, Card)뿐입니다. Dress 로그에 `꾸미기:` 경고가 없습니다.
3. 캡처에 분홍 재질과 남은 회색 덩어리가 없습니다.
4. `git status` 가 비어 있고 push 가 끝났습니다. 마지막 커밋 메시지 끝에 `[n번 끝]` 을 씁니다. 1번이 이것으로 마지막 점검 시점을 압니다.
5. 사용자에게 보고합니다: 끝낸 것, 못 한 것, 기본값으로 정한 것, 소유 밖이라 고치지 못한 것.

## 11. 막혔을 때

| 상황 | 할 일 |
|---|---|
| Windows 에서 k3d.py, setup.py 가 실패 | 이 두 파일은 Windows 실행을 한 번도 못 했습니다. 이식 문제면 먼저 발견한 컴퓨터가 가장 작게 고쳐 바로 push 합니다. 다른 컴퓨터는 pull 합니다 |
| Blender 가 종료 코드 134, 137 로 죽음 | Mac 베이크 크래시입니다. 같은 명령을 다시 돌립니다. 반복되면 `K3D_DEVICE=CPU` 입니다 |
| FBX 만 있고 .meta 가 없는 커밋을 받음 | 만든 컴퓨터에 넘기라고 보고합니다. 내가 만들어 올리지 않습니다 |
| 내 것이 아닌 .mat, .meta, 폰트, Settings 가 바뀜 | 커밋하지 않습니다. 3절 규칙 7 입니다 |
| push 충돌 | 다시 pull 합니다. 프리팹이나 씬 충돌이면 멈추고 사용자에게 알립니다. 폴더 .meta 충돌만 이미 올라간 GUID 로 풉니다 |
| 친구(YoungGong0601)가 내 프리팹이나 씬을 고쳐 올림 | 내 변경을 덮어쓰지 말고 멈춘 뒤 사용자에게 알립니다. Dress 스크립트를 다시 돌리면 씬을 복구할 수 있는지 먼저 봅니다 |
| 기획이나 문서가 코드와 다름 | 플레이 시트가 우선입니다. 문서를 고치지 말고 끝날 때 보고합니다 |
| 씬 저장이 안 되거나 Unity 가 멈춤 | 로그를 읽고 재시도는 한 번만 합니다. 에디터를 강제로 끄지 않습니다 |
