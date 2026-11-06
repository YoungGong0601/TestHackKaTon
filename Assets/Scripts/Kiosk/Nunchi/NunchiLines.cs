// 눈치 시스템의 소리 키와 대사. 문구는 HTML판 kiosk/nunchi.js 그대로.
public static class NunchiLines
{
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
        { "y_hurry8", "yM", "아, 좀 빨리요." },
        { "y_hurry9", "yM", "시간 없는데..." },
    };

    public const string Sigh = "(한숨 소리)", Crowd = "(웅성거림)";
    public const string ElderOnly = "어르신, 그거 아니에요.";   // 어르신이 조작할 때만

    // 뒷사람 반응. 답답함 점수가 오를수록 뒤 칸으로 간다
    public static readonly string[][] Back =
    {
        new[] { Sigh, Crowd, "뭐 하시는 거야...", "왜 저렇게 오래 걸려.", "시간 없는데..." },
        new[] { Sigh, "아, 진짜.", "아, 늦었는데.", "뒤에 사람 기다려요." },
        new[] { "저기요, 빨리 좀 해요.", "아, 좀 빨리요.", "뒤에 사람 기다려요.", ElderOnly },
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

    // 새 목소리로 녹음하지 않은 혼잣말. 한 사람 목소리가 섞이지 않게 고르지 않는다
    public static readonly string[] OldVoice = { "a20_why1", "a20_what1", "a40_why1", "a40_what1" };

    public static readonly string[,] Sorry =
    {
        { "sorry1", "아이고, 죄송합니다." },
        { "sorry2", "미안합니다, 금방 해요." },
    };

}
