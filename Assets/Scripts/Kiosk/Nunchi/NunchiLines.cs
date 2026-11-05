// 눈치 시스템의 소리 키와 대사. 문구는 HTML판 kiosk/nunchi.js 그대로.
public static class NunchiLines
{
    public static readonly string[] Sighs = { "sigh_m", "sigh_f", "sigh_m", "tsk", "foot_tap", "throat_clear" };

    public static string SighText(string key)
    {
        switch (key)
        {
            case "tsk": return "(혀 차는 소리)";
            case "foot_tap": return "(발끝 구르는 소리)";
            case "throat_clear": return "(헛기침 소리)";
            default: return "(한숨 소리)";
        }
    }

    // 음성 키, 화자, 문구
    public static readonly string[,] Hurry =
    {
        { "y_hurry1", "yM", "저기요, 빨리 좀 해요." },
        { "y_hurry2", "yM", "아, 진짜." },
        { "y_hurry3", "yF", "뭐 하시는 거야..." },
        { "y_hurry4", "ajm", "뒤에 사람 기다려요." },
        { "y_hurry5", "yM", "어르신, 그거 아니에요." },
        { "y_hurry6", "yF", "왜 저렇게 오래 걸려." },
        { "y_hurry7", "yM", "아, 늦었는데." },
    };

    // 음성 키 뒷부분(앞은 프로필 화자 키), 문구
    public static readonly string[,] Mutter =
    {
        { "why1", "왜 안 되지?" },
        { "why2", "이게 왜 안 돼." },
        { "why3", "이건 또 뭐야." },
        { "what1", "이게 무슨 말이야." },
        { "read1", "글씨가 왜 이렇게 작아." },
    };

    public static readonly string[,] Sorry =
    {
        { "sorry1", "아이고, 죄송합니다." },
        { "sorry2", "미안합니다, 금방 해요." },
    };
}
