# 아트 / 소리 넣는 법

코드 수정 없이 아래 이름 그대로 파일을 넣으면 플레이스홀더(단색 도형)가 바뀐다.

- 그림: `Assets/Resources/Art/<이름>.png` (임포트 설정 Texture Type = **Sprite (2D and UI)**)
- 소리: `Assets/Resources/Sfx/<이름>.wav` (mp3, ogg도 됨)
- 그림은 아래 "게임 속 크기"에 맞춰 자동으로 늘리거나 줄인다. 비율만 맞추면 해상도는 자유.

## 그림

| 이름 | 무엇 | 게임 속 크기 (가로 x 세로, 유닛) |
| --- | --- | --- |
| `CarBody` | 차체 | 2 x 0.5 |
| `Wheel_Round` | 원형 바퀴 | 0.7 x 0.7 |
| `Wheel_Big` | 대형 바퀴 | 1.1 x 1.1 |
| `Wheel_Square` | 사각 바퀴 | 0.65 x 0.65 |
| `Wheel_Star` | 별 바퀴 | 0.9 x 0.9 |
| `Trap` | 함정 (폭탄) | 0.6 x 0.5 |
| `Finish` | 결승선 깃발 | 0.3 x 6 |
| `Panel` | UI 패널 배경 | 화면 전체로 늘어남 |
| `Button` | UI 버튼 배경 | 380 x 140 (1920x1080 기준) |

지형과 길은 지금 선(LineRenderer)으로 그린다. 지형 아트가 필요하면 그때 SpriteShape로 바꾼다.

## 소리

| 이름 | 언제 |
| --- | --- |
| `Trap` | 함정에 닿음 |
| `Fall` | 추락 |
| `RoundEnd` | 재생 끝 (추락 아닐 때) |
| `Win` | 승리 |
| `Lose` | 패배 |
