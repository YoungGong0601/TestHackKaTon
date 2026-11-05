using System;

public enum ItemId { None, Memo, Lens, Card }

// 인물별 챕터를 건너가는 진행 데이터. 값은 HTML판과 같은 id 문자열
[Serializable]
public class OrderData
{
    public string place, item, combo, side, drink;
    public bool sizeUp, paid;
    public int number = 274;
}

[Serializable]
public class RunStats
{
    public float startTime, endTime = -1f;
    public int touches, wrong, sorry, resets, blowups;
}
