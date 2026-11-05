using System;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

// 쪽지. 모든 회차의 목표 표시를 대신한다. 1 키로 열고 닫는다. 보는 동안 시간은 흐르고 걸을 수 있다
// 내용 찾는 순서: Note.Set, entries의 씬 이름, entries의 프로필 id
// Memo를 가진 인물(4회차)은 지갑 속 쪽지를 쓰니 여기서는 열리지 않는다
// 배치: Assets/Graybox/PH/NotePanel.prefab, Systems 프리팹의 자식. 켜고 끄기는 group.alpha로 한다
// 배치: group = 루트 CanvasGroup, text = Paper 자식 Text
public class Note : MonoBehaviour
{
    [Serializable]
    public class Entry
    {
        public string key;   // 씬 이름 또는 프로필 id
        [TextArea] public string text;
        [Range(0f, 1f)] public float soft;   // 0 또렷, 클수록 번진다
    }

    public static Note I { get; private set; }

    [SerializeField] CanvasGroup group;
    [SerializeField] TMP_Text text;
    [SerializeField] Entry[] entries = new Entry[0];

    string setText;
    float setSoft, closeAt;
    bool open;

    /// <summary>지금 인물이 1 키로 볼 쪽지가 있을 때.</summary>
    public static bool Available
    {
        get
        {
            var p = GameState.I != null ? GameState.I.Profile : null;
            return I != null && p != null && !p.Has(ItemId.Memo) && I.Find(p, out _, out _);
        }
    }

    public static bool Opened => I != null && I.open;

    /// <summary>이 씬의 쪽지 내용을 정한다. 다음 씬에서 풀린다. soft 0 또렷, 클수록 번진다.</summary>
    public static void Set(string text, float soft = 0f)
    {
        if (I == null) return;
        I.setText = text;
        I.setSoft = soft;
        if (I.open) I.Show(true);
    }

    /// <summary>쪽지를 잠깐 편다. 조작을 막지 않고 sec 뒤에 접힌다. 음수면 Note_PeekSec.</summary>
    public static void Peek(float sec = -1f)
    {
        if (I == null || !Available) return;
        I.Show(true);
        I.closeAt = Time.unscaledTime + (sec >= 0f ? sec : Bal.G("Note_PeekSec", 4f));
    }

    public static void Close()
    {
        if (I != null) I.Show(false);
    }

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
        group.alpha = 0f;
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
        setText = null;
        Show(false);
        group.alpha = 0f;
    }

    bool Find(CharacterProfile profile, out string body, out float soft)
    {
        body = setText;
        soft = setSoft;
        if (!string.IsNullOrEmpty(body)) return true;
        string scene = SceneManager.GetActiveScene().name;
        Entry hit = null;
        foreach (var e in entries)
        {
            if (e.key == scene) { hit = e; break; }
            if (e.key == profile.id) hit = e;
        }
        if (hit == null) return false;
        body = hit.text;
        soft = hit.soft;
        return !string.IsNullOrEmpty(body);
    }

    void Show(bool on)
    {
        closeAt = 0f;
        if (on && Find(GameState.I.Profile, out var body, out var soft))
        {
            text.text = body;
            text.fontMaterial.SetFloat(ShaderUtilities.ID_OutlineSoftness, soft);
        }
        if (open == on) return;
        open = on;
        if (AudioManager.I != null) AudioManager.I.Play(on ? "paper_rustle_1" : "paper_rustle_2", null, 0.4f);
        if (Hud.I != null) Hud.I.Items();
    }

    void Update()
    {
        float dt = Time.unscaledDeltaTime;
        group.alpha = Mathf.MoveTowards(group.alpha, open ? 1f : 0f, dt / 0.15f);
        if (closeAt > 0f && Time.unscaledTime >= closeAt) Show(false);

        var kb = Keyboard.current;
        var pc = PlayerController.I;
        if (kb == null || pc == null || kb.ctrlKey.isPressed || !kb.digit1Key.wasPressedThisFrame) return;
        if (pc.CurrentMode == PlayerController.Mode.Locked || pc.CurrentMode == PlayerController.Mode.Hidden || !Available) return;
        Show(!open);
    }
}
