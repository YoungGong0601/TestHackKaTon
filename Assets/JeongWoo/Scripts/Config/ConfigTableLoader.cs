// 제출 빌드는 공용 시트를 받지 않고 코드의 fallback 값만 쓴다. 시연 날 시트가 바뀌어도 수치가 흔들리지 않는다
public static class ConfigTableLoader
{
    public static T Get<T>(string key, T fallback) => fallback;
}
