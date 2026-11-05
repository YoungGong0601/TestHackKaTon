using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

// 챕터 진행과 챕터를 건너가는 데이터. Systems 프리팹의 자식. 중복은 나중 것이 스스로 사라진다
// 배치: flow = Assets/Graybox/Data/ChapterFlow.asset
[DefaultExecutionOrder(-1000)]
public class GameState : MonoBehaviour
{
    public static GameState I { get; private set; }

    // 에디터에서 열어 두는 씬. 80대 챕터로도 쓰여서, 여기서 플레이를 시작하면 챕터 대신 0번 챕터로 보낸다
    const string BootScene = "R1_Home";

    public ChapterFlow flow;
    public int chapterIndex;

    public CharacterProfile Profile { get; private set; }
    public OrderData Order { get; private set; } = new();
    public RunStats Stats { get; private set; } = new();

    /// <summary>BootScene으로 시작해 0번 챕터 씬을 불러오는 중. 이 동안 BootScene의 Director는 연출을 시작하지 않는다.</summary>
    public bool Booting { get; private set; }

    bool loading;
    Coroutine finish;

    public ChapterEntry CurrentEntry => Current;

    ChapterEntry Current => flow != null && chapterIndex >= 0 && chapterIndex < flow.chapters.Count ? flow.chapters[chapterIndex] : null;

    void Awake()
    {
        var root = transform.root.gameObject;
        if (I != null && I != this)
        {
            root.SetActive(false);  // 형제의 Awake와 Start가 돌지 않게
            Destroy(root);
            return;
        }
        I = this;
        string startScene = root.scene.name;   // 씬을 비동기로 불러올 때는 활성 씬이 아직 앞 씬일 수 있다
        DontDestroyOnLoad(root);
        QualitySettings.realtimeReflectionProbes = true;   // 씬의 반사 프로브가 시작 때 한 번 찍는다. 공용 설정은 꺼져 있다

        // 어느 씬에서 시작해도 그 씬의 챕터로 맞춘다. 단 BootScene은 처음부터. 이 Awake는 게임을 켤 때만 돌고, 진행 중 80대 도착은 아래 OnSceneLoaded가 받는다
        int i = flow != null ? flow.chapters.FindIndex(c => c.sceneName == startScene) : -1;
        if (i < 0) Debug.LogWarning($"ChapterFlow에 씬 {startScene} 없음, 0번 챕터로 시작");
        Booting = i > 0 && startScene == BootScene;
        chapterIndex = Booting ? 0 : Mathf.Max(i, 0);
        Profile = Current?.profile;
    }

    void Start()
    {
        Stats.startTime = Time.time;
        SceneManager.sceneLoaded += OnSceneLoaded;
        if (Booting)
        {
            if (Hud.I != null) Hud.I.Fade(1f, 0f);
            SceneManager.LoadScene(Current.sceneName, LoadSceneMode.Single);   // 제목은 도착한 뒤 EnterChapter가 띄운다
        }
        else EnterChapter();
    }

    void OnDestroy()
    {
        if (I != this) return;
        SceneManager.sceneLoaded -= OnSceneLoaded;
        I = null;
    }

    void OnSceneLoaded(Scene scene, LoadSceneMode mode)
    {
        if (mode != LoadSceneMode.Single) return;
        Booting = false;
        if (Current == null || Current.sceneName != scene.name)
        {
            int i = flow != null ? flow.chapters.FindIndex(c => c.sceneName == scene.name) : -1;
            if (i >= 0) chapterIndex = i;
        }
        EnterChapter();
    }

    // 프로필 적용과 시작 지점 배치. Director의 Start보다 먼저 돈다
    void EnterChapter()
    {
        var entry = Current;
        Profile = entry?.profile;
        var player = PlayerController.I;
        if (player != null)
        {
            PlayerSpawn spawn = null;
            foreach (var s in FindObjectsByType<PlayerSpawn>(FindObjectsSortMode.None))
                if (spawn == null || (entry != null && s.id == entry.spawnId)) spawn = s;
            if (spawn != null && entry != null && spawn.id != entry.spawnId) Debug.LogWarning($"PlayerSpawn id {entry.spawnId} 없음, {spawn.id} 사용");
            if (spawn != null)
            {
                player.Teleport(spawn.transform.position, spawn.transform.eulerAngles.y);
                player.Ground = spawn.ground;
            }
            player.Freeze(true);
            player.HoldStill = false;
            player.SetMode(PlayerController.Mode.Fps);
        }
        if (HandRig.I != null)
        {
            HandRig.I.Clear();
            HandRig.I.ApplyLook(Profile != null ? Profile.handLook : 0);
        }
        if (Wallet.I != null) Wallet.I.Clear();
        // 제목은 챕터 순서의 맨 앞에서만. 씬 코드는 Hud.TitleOpen이 꺼질 때까지 기다린다
        if (chapterIndex == 0 && Hud.I != null) Hud.I.ShowTitle();
    }

    // 다음 챕터 로드, 마지막이면 엔딩
    public void CompleteChapter()
    {
        if (loading) return;
        if (flow == null || chapterIndex + 1 >= flow.chapters.Count) { if (finish == null) finish = StartCoroutine(Finish()); }
        else JumpChapter(chapterIndex + 1, true);
    }

    // eyes: 다음 프로필이 다르면 암전 대신 눈을 감는다. 진행만 쓰고 디버그와 처음으로는 쓰지 않는다
    public void JumpChapter(int index, bool eyes = false)
    {
        if (loading || flow == null || index < 0 || index >= flow.chapters.Count) return;
        StopEnding();
        StartCoroutine(Load(index, eyes));
    }

    // 엔딩 중 시연자 키로 옮길 때 엔딩 화면을 걷는다
    void StopEnding()
    {
        if (finish == null) return;
        StopCoroutine(finish);
        finish = null;
        if (RoundUi.I != null) RoundUi.I.End(false);
    }

    // 엔딩이 끝날 때와 처음으로 키. 첫 챕터로
    public void Restart()
    {
        Order = new OrderData();
        Stats = new RunStats { startTime = Time.time };
        Round.ProfileChanged = false;
        if (Wallet.I != null) Wallet.I.ResetRun();
        JumpChapter(0);
    }

    IEnumerator Load(int index, bool eyes)
    {
        loading = true;
        if (PlayerController.I != null) PlayerController.I.Freeze(true);
        if (Hud.I != null)
        {
            Hud.I.Prompt(null);
            Hud.I.ClearSubs();
            Hud.I.Views(null);
            Round.ProfileChanged = Current != null && flow.chapters[index].profile != Current.profile;
            if (eyes && Round.ProfileChanged) yield return Round.CloseEyes();
            else yield return Hud.I.Fade(1f, 0.7f);
        }
        chapterIndex = index;
        Profile = Current.profile;
        var op = SceneManager.LoadSceneAsync(Current.sceneName, LoadSceneMode.Single);
        if (op == null)
        {
            Debug.LogError($"씬 {Current.sceneName} 로드 실패, Build Settings 확인");
            if (Hud.I != null) Hud.I.Fade(0f, 0.5f);
            if (PlayerController.I != null) PlayerController.I.Freeze(false);
        }
        while (op != null && !op.isDone) yield return null;
        loading = false;
    }

    IEnumerator Finish()
    {
        loading = true;
        if (Stats.endTime < 0f) Stats.endTime = Time.time;
        if (PlayerController.I != null) PlayerController.I.Freeze(true);
        loading = false;
        yield return Ending.Play();
        finish = null;
    }

    // 시연자 키. 빌드에도 들어간다. Ctrl+Shift 없이는 동작하지 않는다
    void Update()
    {
        var kb = Keyboard.current;
        if (kb == null || !kb.ctrlKey.isPressed || !kb.shiftKey.isPressed) return;
        if (kb.f1Key.wasPressedThisFrame && Hud.I != null) Hud.I.ToggleDebug();
        if (kb.f2Key.wasPressedThisFrame) CompleteChapter();
        if (kb.f3Key.wasPressedThisFrame) JumpChapter(chapterIndex - 1);
        if (kb.f6Key.wasPressedThisFrame)
        {
            var nunchi = FindAnyObjectByType<NunchiSystem>();
            if (nunchi != null) nunchi.Add(100f);
        }
        if (kb.f7Key.wasPressedThisFrame) ConfigTableLoader.Load();
        if (kb.homeKey.wasPressedThisFrame) Restart();
        for (int i = 0; i < 9; i++)
            if (kb[Key.Digit1 + i].wasPressedThisFrame) JumpChapter(i);
    }
}
