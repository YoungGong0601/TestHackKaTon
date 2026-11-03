using UnityEngine;

// 자동차, 길은 매 회차 작업. 나머지 6개가 회차마다 뽑히는 요소. 순서가 곧 작업 순서
public enum Role { Car, Road, Weather, Wheel, Terrain, Trap, Weight, Gravity }

public enum Weather { Clear, Rain, Headwind, Tailwind }
public enum Wheel { Round, Big, Square, Star }
public enum Surface { Normal, Mud, Ice }

// 카드형 요소(날씨, 바퀴, 무게, 중력)의 현재 값. 지형과 함정 값은 Track이 들고 있다
public static class Env
{
    public static readonly string[] RoleNames = { "자동차", "길", "날씨", "바퀴", "지형", "함정", "차체 무게", "중력" };
    public static readonly string[] SurfaceNames = { "일반", "진흙", "얼음" };

    static readonly string[][] cards = {
        null, null,
        new[] { "맑음", "비", "맞바람", "뒷바람" },
        new[] { "원형", "대형", "사각", "별" },
        null, null,
        new[] { "가벼움", "보통", "무거움" },
        new[] { "낮음", "보통", "높음" },
    };

    static readonly int[] values = new int[8];

    public static Weather Weather => (Weather)values[(int)Role.Weather];
    public static Wheel Wheel => (Wheel)values[(int)Role.Wheel];
    public static int Weight => values[(int)Role.Weight]; // 0 가벼움, 1 보통, 2 무거움
    public static int Gravity => values[(int)Role.Gravity]; // 0 낮음, 1 보통, 2 높음

    public static bool IsCard(Role r) => cards[(int)r] != null;
    public static string[] Cards(Role r) => cards[(int)r];
    public static void Set(Role r, int v) => values[(int)r] = v;
    public static string ValueName(Role r) => cards[(int)r][values[(int)r]];

    // 첫 회차: 맑음, 원형, 보통, 보통
    public static void Reset()
    {
        Set(Role.Weather, 0);
        Set(Role.Wheel, 0);
        Set(Role.Weight, 1);
        Set(Role.Gravity, 1);
    }

    // 서로 다른 카드 2장
    public static int[] DrawTwo(Role r)
    {
        int n = cards[(int)r].Length, a = Random.Range(0, n), b = Random.Range(0, n - 1);
        if (b >= a) b++;
        return new[] { a, b };
    }

    public static void Randomize(Role r) => Set(r, Random.Range(0, cards[(int)r].Length));

    public static float WeightMul => Weight switch { 0 => Cfg("Weight.Light", 0.6f), 2 => Cfg("Weight.Heavy", 1.8f), _ => 1f };
    public static float GravityMul => Gravity switch { 0 => Cfg("Gravity.Low", 0.5f), 2 => Cfg("Gravity.High", 1.6f), _ => 1f };

    public static float Wind => Weather switch {
        Weather.Headwind => -Cfg("Weather.Wind", 4f),
        Weather.Tailwind => Cfg("Weather.Wind", 4f),
        _ => 0f,
    };

    public static float Cfg(string key, float fallback) => ConfigTableLoader.Get(key, fallback);
    public static int Cfg(string key, int fallback) => ConfigTableLoader.Get(key, fallback);
}
