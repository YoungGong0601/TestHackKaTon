# Assets/JeongWoo

3D 모델과 사운드를 입힌 제출용 사본입니다. 친구 그레이박스(`Assets/Scripts`, `Assets/Graybox`, `Assets/UI`, `Assets/Scenes`)와 파일이 겹치지 않고, 그쪽이 바뀌어도 이 사본은 깨지지 않습니다.

## 쓰는 법

| 할 일 | 방법 |
|---|---|
| 에디터에서 시험 | `Scenes/JW_Home.unity` 를 열고 Play |
| 빌드 | `Tools/JeongWoo/빌드 (Windows)`, `Tools/JeongWoo/빌드 (Mac)`. 결과는 `Builds/` |
| 씬 다시 만들기 | `Tools/JeongWoo/사본 다시 만들기`. 씬을 손으로 고쳤다면 `Env`, `Lights` 쪽 수정은 사라집니다 |

## 시연 키

Ctrl+Shift 를 같이 누릅니다. 빌드에서도 동작합니다.

| 키 | 동작 |
|---|---|
| N | 다음 챕터 |
| B | 이전 챕터 |
| K | 키오스크로 |
| R | 처음으로 |
| Q | 끝내기 |

## 구조

- 코드는 asmdef `JeongWoo.Game` 이라 친구 코드와 클래스 이름이 같아도 충돌하지 않습니다.
- 씬 꾸미기는 `Editor/JWDress.cs`, 배치 데이터는 `Layouts/*.json` 입니다. 움직이는 물체와 콜라이더는 씬의 것을 그대로 쓰고 모델은 보이기만 합니다.
- 공유하는 것은 `Assets/Art3D`, `Assets/TextMesh Pro`, 레이어 설정(ProjectSettings), Packages 뿐입니다.
- 공용 구글 시트는 받지 않습니다. 수치는 코드 기본값입니다.
- 소리 출처는 `Resources/JW/Audio/SFX_CREDITS.csv` 입니다. CC BY 소리가 있어 빌드 폴더에 같이 복사되고, 제출 README 에도 적어야 합니다.
