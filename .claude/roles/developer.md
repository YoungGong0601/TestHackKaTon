# 역할: 개발자

이 세션의 사용자는 개발자다. Unity 코드와 에셋을 만든다.

## 작업 범위

- 고치는 곳: `Assets/`, `ProjectSettings/`, `Packages/`
- `docs/`는 읽기만 한다. 전체 기획은 `docs/Hackton.md`. 기획서와 구현이 다르면 코드를 기획서에 맞추고, 기획서가 틀려 보이면 사용자에게 알린다(기획서를 직접 고치지 않는다).
- 구글 시트(ConfigTable)는 기획자 영역이다. 새 키가 필요하면 코드에 기본값을 넣어 먼저 동작하게 하고, 시트에 추가할 줄(ConfigKey, ValueType, 기본값)을 사용자에게 알려 준다.

## 브랜치

- 작업은 `dev`에서 딴 `feat/<기능>` 브랜치에서 한다. 시작 전에 현재 브랜치를 확인한다.
- `main`과 `dev`에 직접 커밋하지 않는다.

## 코드 규칙

- 밸런스 수치(속도, 체력, 시간, 확률 등)는 상수로 박지 않고 `ConfigTableLoader.Get("Key", 기본값)`으로 읽는다. 기본값은 시트 값과 같게 둔다.
- 로드가 끝난 뒤 값이 필요한 초기화는 `ConfigTableLoader.IsLoaded`를 확인하거나 `ConfigTableLoader.Loaded` 이벤트를 쓴다.
- 기존 코드 스타일을 따른다: 한글 주석, 여는 중괄호는 같은 줄, 클래스 위에 역할을 설명하는 주석 몇 줄.
- 입력은 Input System(`InputSystem_Actions`)만 쓴다. 옛 `Input.GetKey`는 쓰지 않는다.

## Unity 에디터

- 에디터가 열려 있으면 `unity command`로 직접 조작하고, `.unity`, `.prefab`, `.asset` YAML을 손으로 고치지 않는다.
- 스크립트 변경 후 새로고침이나 에셋 변경 전에 `EditorApplication.isPlaying`을 확인한다. 플레이 중이면 멈추고 사용자에게 알린다.
- 빌드는 사용자가 요청할 때만 한다.

## 충돌 줄이기

- 씬 하나는 한 사람만 고친다. 다른 사람 씬에 넣을 것은 프리팹으로 만들어 전달한다.
- 커밋 전에 `git status`로 의도하지 않은 씬, 에셋 변경이 섞였는지 확인한다.
