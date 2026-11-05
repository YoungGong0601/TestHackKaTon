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

    public ChapterFlow flow;
    public int chapterIndex;

    public CharacterProfile Profile { get; private set; }
    public OrderData Order { get; private set; } = new();
    public RunStats Stats { get; private set; } = new();
    public bool DebugToKiosk;   // F5. 키오스크가 있는 씬의 Director가 보고 끈다

    bool loading;

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
        DontDestroyOnLoad(root);

        // 어느 씬에서 시작해도 그 씬의 챕터로 맞춘다
        int i = flow != null ? flow.chapters.FindIndex(c => c.sceneName == SceneManager.GetActiveScene().name) : -1;
        if (i < 0) Debug.LogWarning($"ChapterFlow에 씬 {SceneManager.GetActiveScene().name} 없음, 0번 챕터로 시작");
        chapterIndex = Mathf.Max(i, 0);
        Profile = Current?.profile;
    }

    void Start()
    {
        Stats.startTime = Time.time;
        EnterChapter();
        SceneManager.sceneLoaded += OnSceneLoaded;
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
        if (HandRig.I != null) HandRig.I.Clear();
        // 제목은 챕터 순서의 맨 앞에서만. 씬 코드는 Hud.TitleOpen이 꺼질 때까지 기다린다
        if (chapterIndex == 0 && Hud.I != null) Hud.I.ShowTitle();
    }

    // 다음 챕터 로드, 마지막이면 결과
    public void CompleteChapter()
    {
        if (loading) return;
        if (flow == null || chapterIndex + 1 >= flow.chapters.Count) StartCoroutine(Finish());
        else JumpChapter(chapterIndex + 1);
    }

    public void JumpChapter(int index)
    {
        if (loading || flow == null || index < 0 || index >= flow.chapters.Count) return;
        StartCoroutine(Load(index));
    }

    // 결과 화면을 닫을 때. 첫 챕터로
    public void Restart()
    {
        Order = new OrderData();
        Stats = new RunStats { startTime = Time.time };
        JumpChapter(0);
    }

    IEnumerator Load(int index)
    {
        loading = true;
        if (PlayerController.I != null) PlayerController.I.Freeze(true);
        if (Hud.I != null)
        {
            Hud.I.Prompt(null);
            Hud.I.ClearSubs();
            Hud.I.Views(null);
            yield return Hud.I.Fade(1f, 0.7f);
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
        if (Hud.I != null)
        {
            yield return Hud.I.Fade(1f, 0.7f);
            Hud.I.ShowResult();
        }
        loading = false;
    }

#if UNITY_EDITOR || DEVELOPMENT_BUILD
    // F1 표시, F2 다음 챕터, F3 이전 챕터, F5 키오스크로, F7 시트 다시 읽기. F6은 NunchiSystem
    void Update()
    {
        var kb = Keyboard.current;
        if (kb == null) return;
        if (kb.f1Key.wasPressedThisFrame && Hud.I != null) Hud.I.ToggleDebug();
        if (kb.f2Key.wasPressedThisFrame) CompleteChapter();
        if (kb.f3Key.wasPressedThisFrame) JumpChapter(chapterIndex - 1);
        if (kb.f5Key.wasPressedThisFrame && flow != null)
        {
            int i = flow.chapters.FindIndex(c => c.hasKiosk);
            if (i >= 0)
            {
                DebugToKiosk = true;
                if (i != chapterIndex) JumpChapter(i);
            }
        }
        if (kb.f7Key.wasPressedThisFrame) ConfigTableLoader.Load();
    }
#endif
}
