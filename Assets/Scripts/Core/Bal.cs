// 모든 튜닝 수치의 입구. 시트가 다시 로드될 수 있으니 값을 캐시하지 말고 쓸 때마다 읽는다
public static class Bal
{
    static string Prefix => GameState.I != null && GameState.I.Profile != null ? GameState.I.Profile.keyPrefix : "";

    public static float F(string name, float fb) => ConfigTableLoader.Get(Prefix + name, fb);
    public static float G(string fullKey, float fb) => ConfigTableLoader.Get(fullKey, fb);
    public static int I(string fullKey, int fb) => ConfigTableLoader.Get(fullKey, fb);
}
