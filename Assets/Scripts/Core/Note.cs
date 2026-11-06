using System;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;

// 쪽지. 모든 회차의 목표 표시를 대신한다. ItemKeys 번호로 손에 들고 내린다. 보는 동안 시간은 흐르고 걸을 수 있다
// 내용 찾는 순서: Note.Set, entries의 씬 이름, entries의 프로필 id
// 배치: Assets/Graybox/PH/NotePanel.prefab, Systems 프리팹의 자식. 내용만 들고 있고 보이는 종이는 HandRig의 Hand_Note다
public class Note : MonoBehaviour
{
    [Serializable]
    public class Entry
    {
        public string key;   // 씬 이름 또는 프로필 id
        [TextArea] public string text;
        [Range(0f, 1f)] public float soft;   // 0 또렷, 클수록 번진다
        public int kind;                     // 0 구겨진 쪽지, 1 포스트잇
    }

    public static Note I { get; private set; }

    [SerializeField] Entry[] entries = new Entry[0];

    string setText;
    float setSoft, closeAt;
    int setKind;
    bool open;

    /// <summary>지금 인물이 1 키로 볼 쪽지가 있을 때.</summary>
    public static bool Available
    {
        get
        {
            var p = GameState.I != null ? GameState.I.Profile : null;
            return I != null && p != null && I.Find(p, out _, out _, out _);
        }
    }

    public static bool Opened => I != null && I.open;

    /// <summary>이 씬의 쪽지 내용을 정한다. 다음 씬에서 풀린다. soft 0 또렷, 클수록 번진다.</summary>
    public static void Set(string text, float soft = 0f, int kind = 0)
    {
        if (I == null) return;
        I.setText = text;
        I.setSoft = soft;
        I.setKind = kind;
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

    /// <summary>접힐 때까지 든다.</summary>
    public static void Hold()
    {
        if (I != null && Available) I.Show(true);
    }

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
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
    }

    bool Find(CharacterProfile profile, out string body, out float soft, out int kind)
    {
        body = setText;
        soft = setSoft;
        kind = setKind;
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
        kind = hit.kind;
        return !string.IsNullOrEmpty(body);
    }

    void Show(bool on)
    {
        closeAt = 0f;
        string body = null;
        float soft = 0f;
        int kind = 0;
        on = on && Find(GameState.I.Profile, out body, out soft, out kind);
        if (on && Wallet.I != null) Wallet.I.SetOpen(false);   // 쪽지와 지갑은 한 번에 하나만 든다
        if (HandRig.I != null) HandRig.I.SetPaper(on, body, soft, kind);
        if (open == on) return;
        open = on;
        if (AudioManager.I != null)
        {
            if (on) AudioManager.I.Play("paper_rustle_1", null, 0.4f);
            else AudioManager.I.PlayShort("paper_rustle_2", Bal.G("Note_PutSec", 0.3f), null, 0.4f);
        }
        if (Hud.I != null) Hud.I.Items();
    }

    void Update()
    {
        if (PauseMenu.On)
        {
            if (closeAt > 0f) closeAt += Time.unscaledDeltaTime;   // 쉬는 동안 접히는 시간도 멈춘다
            return;
        }
        if (closeAt > 0f && Time.unscaledTime >= closeAt) Show(false);

        var kb = Keyboard.current;
        var pc = PlayerController.I;
        if (kb == null || pc == null || kb.ctrlKey.isPressed) return;
        if (pc.CurrentMode == PlayerController.Mode.Locked || pc.CurrentMode == PlayerController.Mode.Hidden || !ItemKeys.Pressed(kb, ItemId.Memo)) return;
        Show(!open);
    }
}
