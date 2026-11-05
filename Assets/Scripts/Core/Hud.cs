using System.Collections;
using System.Collections.Generic;
using System.Text.RegularExpressions;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// HUD. GTA 방식 자막(상자 없는 흰 글자와 외곽선, 화자와 핵심어만 색)과 프롬프트, 소지품, 눈치, 암전, 제목, 결과
// 글자는 TextMeshProUGUI(리치 텍스트 켬), Debug만 UnityEngine.UI.Text. 폰트는 Assets/UI/Fonts의 Hud_MalgunOS SDF, 외곽선은 같은 폴더의 Outline 재질로 배치한다
// 그리는 순서: HUD 요소들, Fade, Title, Result (제목과 결과는 암전 위)
// 배치: subs = Subs (아래 중앙, 가운데 정렬, 흰색)
// 배치: prompt = Prompt (화면 60% 높이 중앙)
// 배치: views = Views (왼쪽 아래)
// 배치: itemSlots = Items 자식 Item_0..Item_3 (오른쪽 아래, HorizontalLayoutGroup)
// 배치: cross = Cross (화면 중앙 작은 Image)
// 배치: nunchiGroup = Nunchi (왼쪽 세로 막대 CanvasGroup, 처음 alpha 0, 자식 글자 눈치)
// 배치: nunchiFill = Nunchi 자식 Fill Image (anchorMin 0 0, 오프셋 0, 코드가 anchorMax y로 높이 조절)
// 배치: fade = Fade (화면 전체 검정 Image)
// 배치: titlePanel = Title (전체 화면 크림색, 글자 불고기 세트 하나 / 시작, 처음 꺼짐)
// 배치: debugText = Debug (왼쪽 위 작은 글자, 처음 꺼짐)
public class Hud : MonoBehaviour
{
    public static Hud I { get; private set; }
    public static bool SkipTitle;   // 시험용: ShowTitle을 건너뛴다

    [SerializeField] TMP_Text subs;
    [SerializeField] TMP_Text prompt;
    [SerializeField] TMP_Text views;
    [SerializeField] TMP_Text[] itemSlots;
    [SerializeField] Graphic cross;
    [SerializeField] CanvasGroup nunchiGroup;
    [SerializeField] Image nunchiFill;
    [SerializeField] Image fade;
    [SerializeField] GameObject titlePanel;
    [SerializeField] Text debugText;

    const string PlayerColor = "#f3d24b";
    const string OtherColor = "#c9c1b4";
    const string ItemOn = "#f3d24b";
    const string ItemOff = "#ddd5c6";

    static readonly Dictionary<string, (string name, string color)> Speakers = new()
    {
        { "yM", ("뒤 손님", "#e8584a") },
        { "yF", ("뒤 손님", "#e8584a") },
        { "ajm", ("아주머니", "#e8584a") },
        { "staff", ("알바생", "#7fd08a") },
        { "kiosk", ("키오스크", "#7cc6ee") },
        { "pass", ("행인", "#c9c1b4") },
    };
    static readonly Dictionary<char, string> Marks = new() { { 'y', "#f3d24b" }, { 'r', "#e8584a" }, { 'g', "#7fd08a" }, { 'b', "#7cc6ee" } };
    static readonly Regex MarkRegex = new(@"\{([yrgb]):([^}]*)\}");

    int subToken, fadeToken;
    float nunchiNow, nunchiWant, nunchiAlpha;
    bool titleOpen;

    public bool TitleOpen => titleOpen;

    public string CardName = "카드";   // 소지품 칸의 카드 이름. 1-3은 버스카드

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
    }

    static string Mark(string s) => MarkRegex.Replace(s, m => $"<color={Marks[m.Groups[1].Value[0]]}>{m.Groups[2].Value}</color>");

    static string Name(string speaker)
    {
        if (string.IsNullOrEmpty(speaker)) return "";
        var profile = GameState.I != null ? GameState.I.Profile : null;
        if (profile != null && speaker == profile.speakerKey) return $"<color={PlayerColor}>{profile.displayName}:</color> ";
        if (Speakers.TryGetValue(speaker, out var s)) return $"<color={s.color}>{s.name}:</color> ";
        // 다른 챕터의 조작 인물과 조작하지 않는 화자는 ChapterFlow에서 찾는다
        var flow = GameState.I != null ? GameState.I.flow : null;
        if (flow == null) return "";
        foreach (var c in flow.chapters)
            if (c.profile != null && c.profile.speakerKey == speaker) return $"<color={OtherColor}>{c.profile.displayName}:</color> ";
        foreach (var p in flow.speakers)
            if (p != null && p.speakerKey == speaker) return $"<color={OtherColor}>{p.displayName}:</color> ";
        return "";
    }

    // {y:글자} {r:} {g:} {b:} 색 표기. voKey가 있으면 음성이 끝날 때까지 표시. hold 음수면 글자 수로 정한다
    public Coroutine Say(string speaker, string text, string voKey = null, float hold = -1f, Vector3? pos = null, float vol = 1f, bool clear = false)
    {
        return StartCoroutine(SayRoutine(speaker, text, voKey, hold, pos, vol, clear));
    }

    IEnumerator SayRoutine(string speaker, string text, string voKey, float hold, Vector3? pos, float vol, bool clear)
    {
        int token = ++subToken;
        subs.text = Wrap(Mark(text));   // 임시 T08: 화자 이름 표시 안 함
        float len = hold >= 0f ? hold : Mathf.Max(1.5f, text.Length * 0.1f);
        if (!string.IsNullOrEmpty(voKey))
        {
            float vo = AudioManager.I != null ? AudioManager.I.Vo(voKey, pos, vol, clear) : 0f;
            len = Mathf.Max(vo > 0f ? vo : len, hold >= 0f ? hold : 0.6f);
        }
        yield return new WaitForSeconds(len);
        if (token == subToken) subs.text = "";
    }

    // 왼쪽 위 작은 글자. null이면 지움
    public void SideNote(string text)
    {
        if (RoundUi.I != null) RoundUi.I.SideNote(text);
    }

    public void ClearSubs()
    {
        subToken++;
        subs.text = "";
    }

    // TMP는 한글을 글자 단위로 끊어 끝 글자만 다음 줄로 밀린다. 넘치는 글은 줄 길이가 고른 띄어쓰기에서 직접 끊는다
    string Wrap(string rich)
    {
        int lines = Mathf.CeilToInt(subs.GetPreferredValues(rich, Mathf.Infinity, Mathf.Infinity).x / (subs.rectTransform.rect.width * 0.95f));
        if (lines < 2) return rich;
        var spaces = new List<(int at, int seen)>();
        int seen = 0;
        bool tag = false;
        for (int i = 0; i < rich.Length; i++)
        {
            char c = rich[i];
            if (c == '<') tag = true;
            else if (c == '>') tag = false;
            else if (!tag && c == ' ') spaces.Add((i, ++seen));
            else if (!tag) seen++;
        }
        var chars = rich.ToCharArray();
        for (int k = 1; k < lines; k++)
        {
            int best = -1;
            float bestCost = float.MaxValue;
            foreach (var s in spaces)
            {
                // 문장 부호 뒤라면 조금 멀어도 그곳에서 끊는다
                float cost = Mathf.Abs(s.seen - (float)seen * k / lines) - (".,?!".IndexOf(rich[s.at - 1]) >= 0 ? 4f : 0f);
                if (cost < bestCost) { bestCost = cost; best = s.at; }
            }
            if (best >= 0) chars[best] = '\n';
        }
        return new string(chars);
    }

    // 예: "E 문 열기". null이면 지움
    public void Prompt(string text)
    {
        string t = text ?? "";
        if (prompt.text != t) prompt.text = t;
    }

    public void Cross(bool on)
    {
        if (cross != null) cross.enabled = on;
    }

    // 현재 인물의 소지품과 든 물건을 표시한다. 키는 ItemId 값과 같다
    public void Items()
    {
        var profile = GameState.I != null ? GameState.I.Profile : null;
        var hands = HandRig.I;
        int n = 0;
        if (profile != null && profile.items != null && hands != null && hands.ItemsEnabled)
        {
            if (Note.Available && n < itemSlots.Length)
            {
                var slot = itemSlots[n++];
                slot.gameObject.SetActive(true);
                slot.text = $"<color={(Note.Opened ? ItemOn : ItemOff)}><b>1</b> 쪽지</color>";
            }
            foreach (var id in profile.items)
            {
                // 지갑 속 물건은 칸에 나오지 않는다
                if (id == ItemId.Memo || id == ItemId.Cash || (id == ItemId.Card && profile.Has(ItemId.Wallet))) continue;
                if (n >= itemSlots.Length) break;
                var slot = itemSlots[n++];
                slot.gameObject.SetActive(true);
                slot.text = $"<color={(hands.Held == id || (id == ItemId.Wallet && hands.walletOut) ? ItemOn : ItemOff)}><b>{(id == ItemId.Wallet ? 3 : (int)id)}</b> {ItemName(id)}</color>";
            }
        }
        for (; n < itemSlots.Length; n++) itemSlots[n].gameObject.SetActive(false);
    }

    string ItemName(ItemId id) => id switch
    {
        ItemId.Lens => "돋보기",
        ItemId.Card => CardName,
        ItemId.Wallet => "지갑",
        _ => "",
    };

    // 예: "A 알바생   S 뒤   D 키오스크   W 아래". null이면 지움
    public void Views(string text) => views.text = text ?? "";

    public void Nunchi(float v, bool visible)
    {
        nunchiWant = Mathf.Clamp(v, 0f, 100f);
        nunchiAlpha = visible ? 1f : 0f;
        nunchiFill.color = v >= Bal.G("Nunchi_RingAt", 80f) ? new Color32(0xe8, 0x58, 0x4a, 255) : v >= Bal.G("Nunchi_HeartAt", 40f) ? new Color32(0xe6, 0xb2, 0x4c, 255) : new Color32(0xe6, 0xdc, 0xcb, 255);
    }

    // 1 가림, 0 보임
    public Coroutine Fade(float to, float sec) => StartCoroutine(FadeRoutine(to, sec));

    IEnumerator FadeRoutine(float to, float sec)
    {
        int token = ++fadeToken;
        float from = fade.color.a, t = 0f;
        while (t < sec)
        {
            t += Time.unscaledDeltaTime;
            if (token == fadeToken) SetFade(Mathf.Lerp(from, to, Mathf.Clamp01(t / Mathf.Max(sec, 1e-3f))));
            yield return null;
        }
        if (token == fadeToken) SetFade(to);
    }

    void SetFade(float a)
    {
        var c = fade.color;
        c.a = a;
        fade.color = c;
    }

    // 시간을 멈추고 클릭을 기다린다. 끝나면 기록 시작. GameState가 0번 챕터 진입 때 부른다
    public Coroutine ShowTitle()
    {
        if (SkipTitle || titleOpen || titlePanel == null) return null;
        return StartCoroutine(TitleRoutine());
    }

    IEnumerator TitleRoutine()
    {
        titleOpen = true;
        titlePanel.SetActive(true);
        Time.timeScale = 0f;
        AudioListener.pause = true;
        if (PlayerController.I != null) PlayerController.I.SetMode(PlayerController.Mode.Locked);
        yield return null;
        while (!Clicked()) yield return null;
        titlePanel.SetActive(false);
        Time.timeScale = 1f;
        AudioListener.pause = false;
        titleOpen = false;
        if (PlayerController.I != null) PlayerController.I.SetMode(PlayerController.Mode.Fps);
        if (GameState.I != null) GameState.I.Stats.startTime = Time.time;
    }

    static bool Clicked()
    {
        var mouse = Mouse.current;
        var kb = Keyboard.current;
        return (mouse != null && mouse.leftButton.wasPressedThisFrame) || (kb != null && (kb.enterKey.wasPressedThisFrame || kb.spaceKey.wasPressedThisFrame));
    }

    static string Clock(float sec)
    {
        int s = Mathf.Max(0, Mathf.RoundToInt(sec)), m = s / 60;
        return m > 0 ? $"{m}분 {s % 60}초" : $"{s}초";
    }

    public void ToggleDebug()
    {
        if (debugText != null) debugText.gameObject.SetActive(!debugText.gameObject.activeSelf);
    }

    void Update()
    {
        float dt = Time.unscaledDeltaTime;
        if (nunchiGroup != null)
        {
            nunchiGroup.alpha = Mathf.MoveTowards(nunchiGroup.alpha, nunchiAlpha, dt / 0.5f);
            nunchiNow = Mathf.Lerp(nunchiNow, nunchiWant, 1f - Mathf.Exp(-12f * dt));
            var r = nunchiFill.rectTransform;
            r.anchorMax = new Vector2(r.anchorMax.x, nunchiNow / 100f);
        }

        if (debugText != null && debugText.gameObject.activeSelf)
        {
            var g = GameState.I;
            string profile = g != null && g.Profile != null ? g.Profile.id : "";
            float run = g != null ? Time.time - g.Stats.startTime : 0f;
            debugText.text = $"chapter {(g != null ? g.chapterIndex : -1)} {profile}  {Clock(run)} / {Clock(Bal.G("Run_TotalTargetSec", 600f))}  nunchi {Mathf.RoundToInt(nunchiWant)}  config {(ConfigTableLoader.IsLoaded ? "loaded" : "fallback")}  fps {Mathf.RoundToInt(1f / Mathf.Max(dt, 1e-4f))}";
        }
    }
}
