using System.Collections.Generic;
using UnityEngine;

// 소리. Resources/Audio/sfx, vo. key_1.. 변형은 자동 선택. 소스는 프리팹에 배치된 것만 돌려 쓴다
// 배치: sfx = AudioManager 자식 Sfx_00..Sfx_11 AudioSource 12개 (playOnAwake 끔)
// 배치: voice = AudioManager 자식 Vo_0, Vo_1 AudioSource 2개 (playOnAwake 끔)
// 배치: loops = AudioManager 자식 Loop_0..Loop_5 AudioSource 6개 (playOnAwake 끔)
public class AudioManager : MonoBehaviour
{
    public static AudioManager I { get; private set; }

    [SerializeField] AudioSource[] sfx;
    [SerializeField] AudioSource[] voice;
    [SerializeField] AudioSource[] loops;

    readonly Dictionary<string, AudioClip[]> clips = new();
    string[] loopKey;
    float[] loopTarget, loopRate;
    int nextSfx, nextVoice;
    readonly Dictionary<AudioSource, AudioLowPassFilter> filters = new();

    static float Master => Bal.G("Audio_Master", 0.9f);

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
        loopKey = new string[loops.Length];
        loopTarget = new float[loops.Length];
        loopRate = new float[loops.Length];
        FindFilters(sfx);
        FindFilters(voice);
        FindFilters(loops);
    }

    // 소리 소스별 저역 통과. 필터는 Systems 프리팹의 각 소스에 붙어 있다
    void FindFilters(AudioSource[] list)
    {
        foreach (var s in list)
        {
            var f = s.GetComponent<AudioLowPassFilter>();
            if (f == null) continue;
            f.cutoffFrequency = Debuff.OpenHz;
            filters[s] = f;
        }
    }

    // 소리 하나의 먹먹함을 정한다. clear는 뒷사람의 한숨과 재촉
    void Muffle(AudioSource src, bool clear)
    {
        if (filters.TryGetValue(src, out var f)) f.cutoffFrequency = clear ? Debuff.OpenHz : Debuff.MuffleCutoff;
    }

    AudioClip[] Variants(string key)
    {
        if (clips.TryGetValue(key, out var found)) return found;
        var list = new List<AudioClip>();
        var plain = Resources.Load<AudioClip>("Audio/sfx/" + key);
        if (plain != null) list.Add(plain);
        for (int i = 1; i < 9; i++)
        {
            var c = Resources.Load<AudioClip>($"Audio/sfx/{key}_{i}");
            if (c != null) list.Add(c);
        }
        return clips[key] = list.ToArray();
    }

    static void Place(AudioSource src, Vector3? pos)
    {
        src.spatialBlend = pos.HasValue ? 1f : 0f;
        if (!pos.HasValue) return;
        src.transform.position = pos.Value;
        src.rolloffMode = AudioRolloffMode.Logarithmic;
        src.minDistance = 1.5f;
        src.maxDistance = 80f;
    }

    public void Play(string key, Vector3? pos = null, float vol = 1f, float rate = 1f, bool clear = false)
    {
        var list = Variants(key);
        if (list.Length == 0 || sfx.Length == 0) return;
        AudioSource src = null;
        foreach (var s in sfx) if (!s.isPlaying) { src = s; break; }
        if (src == null) { src = sfx[nextSfx]; nextSfx = (nextSfx + 1) % sfx.Length; }
        Place(src, pos);
        src.clip = list[Random.Range(0, list.Length)];
        Muffle(src, clear);
        src.volume = vol * Master;
        src.pitch = rate;
        src.Play();
    }

    // 음성을 틀고 길이(초)를 돌려준다. 파일이 없으면 0
    public float Vo(string key, Vector3? pos = null, float vol = 1f, bool clear = false)
    {
        var clip = Resources.Load<AudioClip>("Audio/vo/" + key);
        if (clip == null || voice.Length == 0) return 0f;
        AudioSource src = null;
        foreach (var s in voice) if (!s.isPlaying) { src = s; break; }
        if (src == null) { src = voice[nextVoice]; nextVoice = (nextVoice + 1) % voice.Length; }
        Place(src, pos);
        src.clip = clip;
        Muffle(src, clear);
        src.volume = vol * Master;
        src.Play();
        return clip.length;
    }

    int LoopIndex(string key) => System.Array.IndexOf(loopKey, key);

    public void Loop(string key, float vol = 1f, float fade = 1.5f)
    {
        if (LoopIndex(key) >= 0) { SetLoop(key, vol, fade); return; }
        var list = Variants(key);
        int i = System.Array.IndexOf(loopKey, null);
        if (list.Length == 0 || i < 0) return;
        loopKey[i] = key;
        var src = loops[i];
        src.clip = list[0];
        src.loop = true;
        src.spatialBlend = 0f;
        src.volume = 0f;
        src.Play();
        SetLoop(key, vol, fade);
    }

    public void SetLoop(string key, float vol, float fade = 0.6f)
    {
        int i = LoopIndex(key);
        if (i < 0) return;
        loopTarget[i] = vol * Master;
        loopRate[i] = Mathf.Abs(loopTarget[i] - loops[i].volume) / Mathf.Max(fade, 0.01f);
    }

    public void StopLoop(string key, float fade = 1f)
    {
        int i = LoopIndex(key);
        if (i < 0) return;
        loopKey[i] = "";    // 빈 문자열은 페이드아웃 중인 슬롯
        loopTarget[i] = 0f;
        loopRate[i] = loops[i].volume / Mathf.Max(fade, 0.01f);
    }

    // 씬 전환 때: 목록만 남기고 나머지는 페이드아웃
    public void Ambience(params (string key, float vol)[] list)
    {
        foreach (string k in loopKey)
        {
            if (string.IsNullOrEmpty(k)) continue;
            bool keep = false;
            foreach (var l in list) keep |= l.key == k;
            if (!keep) StopLoop(k, 1.5f);
        }
        foreach (var l in list) Loop(l.key, l.vol);
    }

    void Update()
    {
        for (int i = 0; i < loops.Length; i++)
        {
            if (loopKey[i] == null) continue;
            var src = loops[i];
            if (filters.TryGetValue(src, out var f)) f.cutoffFrequency = Debuff.MuffleCutoff;
            src.volume = Mathf.MoveTowards(src.volume, loopTarget[i], loopRate[i] * Time.unscaledDeltaTime);
            if (loopKey[i].Length == 0 && src.volume <= 0f)
            {
                src.Stop();
                loopKey[i] = null;
            }
        }
    }
}
