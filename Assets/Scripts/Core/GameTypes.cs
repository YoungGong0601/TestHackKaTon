using System;

// 값은 저장된 에셋과 HUD 숫자로 쓰이니 뒤에만 붙인다. Memo와 Wallet은 Held가 아니다
public enum ItemId { None, Memo, Lens, Card, Wallet, Cash, Receipt }

// 인물별 챕터를 건너가는 진행 데이터. 값은 HTML판과 같은 id 문자열
[Serializable]
public class OrderData
{
    public string item;
    public int number = 274;
}

[Serializable]
public class RunStats
{
    public float startTime, endTime = -1f;
    public int touches, wrong, sorry, resets;
    public bool memoOk;   // 쪽지대로 주문했는가. 4회차 주문이 끝날 때 적는다
}
