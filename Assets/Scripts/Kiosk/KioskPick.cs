// 1회차 신메뉴. 게임을 켤 때 메뉴판 첫 탭에서 하나를 뽑고, 재도전과 처음 복귀에도 그대로 둔다. 4회차 목표는 불고기 버거 세트 그대로다.
// 첫 탭 첫 칸은 불고기 버거 세트 자리라 뽑지 않는다. 시험은 Reseed로 고정한다.
using UnityEngine;
using UnityEngine.SceneManagement;
using static KioskData;

public static class KioskPick
{
    static MenuItem item;
    static System.Random rng;

    public static MenuItem Item
    {
        get
        {
            if (item != null) return item;
            var list = Menu[Tabs[0]];
            rng ??= new System.Random();
            return item = list[1 + rng.Next(list.Length - 1)];
        }
    }

    public static string Id => Item.id;
    public static string SetName => Item.name + " 세트";
    public static int SetPrice => Item.price + Combo("combo").add;
    public static string NoteText => "신메뉴\n" + SetName;

    /// <summary>시험에서 뽑기를 고정한다.</summary>
    public static void Reseed(int seed)
    {
        rng = new System.Random(seed);
        item = null;
        Apply(SceneManager.GetActiveScene());
    }

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void Clear()
    {
        item = null;
        rng = null;
    }

    // Note가 씬을 넘기며 내용을 지운 뒤에 넣어야 한다. Note.Awake보다 늦게 구독한다
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Hook()
    {
        SceneManager.sceneLoaded -= Loaded;
        SceneManager.sceneLoaded += Loaded;
        Apply(SceneManager.GetActiveScene());
    }

    static void Loaded(Scene scene, LoadSceneMode mode)
    {
        if (mode == LoadSceneMode.Single) Apply(scene);
    }

    static void Apply(Scene scene)
    {
        if (scene.name == "R1_Storefront" || scene.name == "R1_Store") Note.Set(NoteText);   // R1_Home은 80대 챕터다
    }
}
