// 게임이 화면 후처리에 넘기는 값. 계산은 Assets/Graybox/Post의 렌더러 기능이 한다
using UnityEngine;

public static class PostState
{
    public static float Nunchi;             // 시야가 따라갈 눈치 값, 평소 0
    public static float HeartTime = -1f;    // 심장 소리 재생 위치(초), 소리가 없으면 음수
    public static Vector3 Lens;             // 돋보기 원: xy 뷰포트 좌표, z 화면 높이 기준 반지름, 0이면 없음
    public static Vector4 NoteRect;         // 들고 있는 쪽지 자리: 뷰포트 xMin yMin xMax yMax, 번짐 제외. 없으면 0
    public static Texture LensTexture;      // 돋보기 카메라가 그린 원 안 그림
}
