using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;

// 챕터 진행과 챕터를 건너가는 데이터. Systems 프리팹의 자식. 중복은 나중 것이 스스로 사라진다
// 배치: flow = Assets/JeongWoo/Graybox/Data/ChapterFlow.asset
// 배치: pipeline = Assets/JeongWoo/Settings/JW_PC_RPAsset.asset (공용 렌더러를 건드리지 않고 사본 후처리를 쓴다)
[DefaultExecutionOrder(-1000)]
public class GameState : MonoBehaviour
{
    public static GameState I { get; private set; }

    public ChapterFlow flow;
    public int chapterIndex;
    [SerializeField] RenderPipelineAsset pipeline;

    public CharacterProfile Profile { get; private set; }
    public OrderData Order { get; private set; } = new();
    public RunStats Stats { get; private set; } = new();
    public bool DebugToKiosk;   // F5. 키오스크가 있는 씬의 Director가 보고 끈다

    bool loading;
    RenderPipelineAsset pipelineBefore;

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
        pipelineBefore = QualitySettings.renderPipeline;
        if (pipeline != null) QualitySettings.renderPipeline = pipeline;
        QualitySettings.realtimeReflectionProbes = true;   // 씬의 반사 프로브가 시작 때 한 번 찍는다. 공용 설정은 꺼져 있다

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
        QualitySettings.renderPipeline = pipelineBefore;
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
        if (Hud.I != null) Hud.I.Nunchi(0f, false);   // 시연자 키로 키오스크 중에 넘어와도 막대가 남지 않게
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
        if (loading) return;
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
            Hud.I.CloseResult();
            Hud.I.Prompt(null);
            Hud.I.ClearSubs();
            Hud.I.Views(null);
            yield return Hud.I.Fade(1f, 0.7f);
        }
        chapterIndex = index;
        Profile = Current.profile;
        var op = JWScenes.Load(Current.sceneName, LoadSceneMode.Single);
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

    // 시연자용. 심사위원이 실수로 누르지 않게 Ctrl+Shift를 같이 누른다. N 다음 챕터, B 이전 챕터, K 키오스크로, R 처음으로, Q 끝내기
    void Update()
    {
        var kb = Keyboard.current;
        if (kb == null) return;
        if (kb.ctrlKey.isPressed && kb.shiftKey.isPressed)
        {
            if (kb.nKey.wasPressedThisFrame) CompleteChapter();
            if (kb.bKey.wasPressedThisFrame) JumpChapter(chapterIndex - 1);
            if (kb.kKey.wasPressedThisFrame) ToKiosk();
            if (kb.rKey.wasPressedThisFrame) Restart();
            if (kb.qKey.wasPressedThisFrame) Application.Quit();
        }
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        // F1 표시, F2 다음 챕터, F3 이전 챕터, F5 키오스크로. F6은 NunchiSystem
        if (kb.f1Key.wasPressedThisFrame && Hud.I != null) Hud.I.ToggleDebug();
        if (kb.f2Key.wasPressedThisFrame) CompleteChapter();
        if (kb.f3Key.wasPressedThisFrame) JumpChapter(chapterIndex - 1);
        if (kb.f5Key.wasPressedThisFrame) ToKiosk();
#endif
    }

    void ToKiosk()
    {
        int i = flow != null ? flow.chapters.FindIndex(c => c.hasKiosk) : -1;
        if (i < 0) return;
        DebugToKiosk = true;
        if (i != chapterIndex) JumpChapter(i);
    }
}
