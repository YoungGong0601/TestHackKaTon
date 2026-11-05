# 에이전트 공통 규칙 (노션 기획 반영)

프로젝트 C:/Users/lovel/Documents/GitHub/TestHackKaTon, Unity 6000.3.13f1, 사용자가 에디터를 열어 두고 직접 플레이한다. Docs/CONTRACT.md, Docs/CONTRACT_NOTES.md 를 먼저 읽는다. HTML판 원본은 ../kiosk-game (읽기만, 큰 파일은 grep으로 필요한 부분만).

- 그레이박스: 회색 상자와 PH_ 프리팹(Visual 안 메시, 콜라이더와 앵커는 Visual 밖). 텍스처, 외부 모델 금지. 사용자가 뒤에 모델을 넣는다.
- 씬과 UI는 코드로 생성하지 않는다. Unity CLI로 열린 에디터에 직접 배치, 저장, 인스펙터 직접 연결. 빌더 스크립트 금지.
- 수치는 ConfigTableLoader 키로, HTML판 또는 합리적 fallback, 사용 시점에 읽음. 새 키는 Docs/keys_<담당>.csv에만 적는다(Docs/ConfigTable.csv는 검증 담당이 합침). 키 값 변경은 코드 fallback과 해당 keys_ 파일을 함께.
- 인물 하드코딩 금지. 대사 음성 키는 Speaker + "_xxx" 방식 유지. 씬 끝은 GameState.I.CompleteChapter().
- 글자: 화면과 문서에 가운데점, 긴 줄표, 화살표 기호, 원문자, 곱하기표 금지. UI에 사용법 문장 금지, 조작 안내는 키와 명사 라벨.
- 사용자 화면, 마우스, 창 포커스 조작 금지. 에디터 종료 금지. 프로세스 명령줄 출력 금지(토큰 노출). 커밋, push, 빌드 금지.
- 제어: unity command ... --project-path "C:/Users/lovel/Documents/GitHub/TestHackKaTon" --caller plugin --skill unity-cli 와 eval. Skill 도구로 unity:unity-cli 로드.
- 사용자가 플레이 중일 수 있다. 저장, 재컴파일, 씬 수정 전마다 EditorApplication.isPlaying 확인, true면 아무것도 바꾸지 말고 2분 간격 대기, 30분 넘으면 보고하고 끝낸다. 파일 편집도 플레이가 꺼진 것을 본 뒤 시작한다.
- 여러 담당이 한 에디터를 공유한다. 파일은 모아서 저장해 재컴파일을 줄인다. 다른 담당 작업으로 컴파일 에러가 잠깐 있으면 2분 뒤 다시 본다. 자기 담당 씬만 Additive로 열어 저장하고 닫는다. 활성 씬을 바꾸지 않는다. 담당 밖 파일 수정이 꼭 필요하면 고치지 말고 보고서에 적는다.
- 기획 정본은 Docs/Notion 의 플레이 시트이고, 결정은 Docs/ROUND_PLAN.md 를 따른다. 노션 파일은 수정하지 않는다. git 커밋, push 금지.
- 스크래치 파일은 자기 이름의 전용 폴더에 둔다.
- PlayMode 시험을 돌리지 않는다(검증 담당만 돌린다). 컴파일 에러 0까지만 확인. 캡처는 플레이 모드 없이 에디터에서 RenderTexture로 Screenshots/<담당>-*.png 저장 후 Read로 확인.
- eval이 시간 초과되면 재시도하지 말고 보고한다(저장 창이 떴을 수 있음).
- 보고는 바꾼 것, 해석한 것, 안 된 것, 사용자가 판단할 것만 짧게. 들어보지 못한 소리와 플레이 못 한 것은 미확인으로 적는다.
