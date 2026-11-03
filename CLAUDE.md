# TestHackKaTon

해커톤용 Unity 2D 게임. 서로의 작업을 모른 채 자동차, 길, 날씨, 바퀴, 지형, 함정, 차체 무게, 중력을 정하고, 합쳐진 결과로 차를 결승선까지 보내는 사이드뷰 로컬 협동 게임이다. 전체 기획은 `docs/Hackton.md`.

기획자와 개발자가 같은 저장소를 쓰고, 역할별 지침은 따로 불러온다.

## 역할 확인 (작업 시작 전 필수)

역할 지침은 이 파일에 없다. 각자 커밋하지 않는 `CLAUDE.local.md`가 둘 중 하나를 불러온다.

- 개발자: `.claude/roles/developer.md`
- 기획자: `.claude/roles/planner.md`

이 대화에 역할 지침이 로드되지 않았다면(위 두 파일 내용이 보이지 않으면) 다른 작업보다 먼저 사용자에게 역할을 묻고, 아래 두 파일을 만든 뒤 Claude Code를 다시 시작하라고 안내한다.

1. `CLAUDE.local.md` (프로젝트 루트)

   ```
   @.claude/roles/developer.md
   ```
   기획자는 `@.claude/roles/planner.md`.

2. `.claude/settings.local.json` (이미 있으면 `permissions.deny`에 합친다)

   개발자:
   ```json
   { "permissions": { "deny": ["Edit(/docs/**)"] } }
   ```
   기획자:
   ```json
   { "permissions": { "deny": ["Edit(/Assets/**)", "Edit(/ProjectSettings/**)", "Edit(/Packages/**)"] } }
   ```

두 파일은 `.gitignore`에 들어 있다. 커밋하지 않는다.

## 프로젝트

- Unity 6000.3.13f1, URP 2D, 입력은 Input System만 사용
- 해상도 1920x1080
- 원격: https://github.com/YoungGong0601/TestHackKaTon

## 폴더

| 경로 | 내용 | 담당 |
|---|---|---|
| `docs/` | 기획 문서 | 기획자 |
| `Assets/` | 게임 코드와 에셋 | 개발자 |
| `Assets/Scripts/Config/` | 밸런스 시트 로더 | 개발자 |
| `.claude/roles/` | 역할별 지침 | 공통 (고칠 때는 팀에 알림) |

## 브랜치

| 브랜치 | 용도 |
|---|---|
| `main` | 빌드되는 상태만. 직접 커밋하지 않고 `dev`에서 병합 |
| `dev` | 통합 브랜치. 기획자는 `docs/` 변경을 여기에 바로 커밋 |
| `feat/<기능>` | 개발자 작업. `dev`에서 따고, 짧게 쓰고 `dev`로 병합 |

- push와 병합은 사용자가 시킬 때만 한다.
- 커밋 하나에는 한 역할의 변경만 담는다. `docs/`와 `Assets/`를 한 커밋에 섞지 않는다.

## 밸런스 값: ConfigTable 시트

게임 수치는 코드나 문서에 직접 쓰지 않고 구글 시트에서 관리한다.

- 시트: https://docs.google.com/spreadsheets/d/1Rakb-IC_AwaCy93-ioBw9UIesSYxOdWwIFE4Kwc_UB8/edit
- 탭 `ConfigTable` (gid=0), 한 줄이 값 하나

| 열 | 코드가 읽나 | 내용 |
|---|---|---|
| ConfigKey | 읽음 | 코드에서 꺼낼 이름. 대소문자까지 일치해야 함 |
| Description | 안 읽음 | 값 설명 |
| ValueType | 읽음 | Int, Float, Bool, String |
| Value | 읽음 | 실제 값 |
| Unit | 안 읽음 | 단위 |
| BalanceIntent | 안 읽음 | 이 값을 고른 이유 |

- 게임 시작 시 `ConfigTableLoader`가 시트를 CSV로 받는다. 실패하면 마지막 캐시를 쓴다.
- 코드에서는 `ConfigTableLoader.Get("Key", 기본값)`으로 꺼낸다. 키가 없거나 타입이 맞지 않으면 기본값이 나온다.
- 헤더 이름을 바꾸면 로더가 열을 못 찾는다. 열 순서는 바꿔도 된다.
