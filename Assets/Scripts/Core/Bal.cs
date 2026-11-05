// 모든 튜닝 수치의 입구. 시트가 다시 로드될 수 있으니 값을 캐시하지 말고 쓸 때마다 읽는다
public static class Bal
{
    static string Prefix => GameState.I != null && GameState.I.Profile != null ? GameState.I.Profile.keyPrefix : "";

    public static float F(string name, float fb) => ConfigTableLoader.Get(Prefix + name, fb);
    public static float G(string fullKey, float fb) => ConfigTableLoader.Get(fullKey, fb);
    public static int I(string fullKey, int fb) => ConfigTableLoader.Get(fullKey, fb);

    // 인물 키. fallback은 Age20, Age40, Age60, Age80 순서이고 프로필 handLook으로 고른다
    public static float Age(string name, float a20, float a40, float a60, float a80)
    {
        int look = GameState.I != null && GameState.I.Profile != null ? GameState.I.Profile.handLook : 3;
        return F(name, look <= 0 ? a20 : look == 1 ? a40 : look == 2 ? a60 : a80);
    }
}
