using System;

// 회차별 눈치 규칙. NunchiSystem.Configure로 넘긴다
public class NunchiRule
{
    public string[] low, mid, high;   // 게이지 구간 대사. null이면 한숨만. 경계 Nunchi_LowMax, Nunchi_MidMax
    public string[] choices;          // null이면 100에서 멈추고 버튼 없음. [0] 떠남, [1] 조금만요
    public Action onFull;        // 다 찼을 때 버튼 없이 바로 부른다
    public float start;          // Begin 때 게이지 시작값
    public Action onLeave;            // [0]을 고르면 호출
}
