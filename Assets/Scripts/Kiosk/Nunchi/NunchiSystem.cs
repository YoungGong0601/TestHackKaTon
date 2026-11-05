// 눈치: 게이지 증감, 한숨과 재촉 스케줄, 실수 직후 혼잣말, 뒤돌아 사과, 폭발 트리거, 단계 효과.
// 수치는 전부 Bal에서 사용 시점에 읽는다. 인물 정보는 GameState.I.Profile만 본다.
// 배치: queue = Store 씬 Director의 QueueManager (뒤 사람 소리가 나는 곳)
// 배치: heartbeat = 자식 AudioSource Nunchi_Heartbeat (loop, playOnAwake 끔, 볼륨 0, clip heartbeat)
// 배치: tinnitus = 자식 AudioSource Nunchi_Tinnitus (loop, playOnAwake 끔, 볼륨 0, clip tinnitus)
// 배치: crowd = 자식 AudioSource Nunchi_Crowd (loop, playOnAwake 끔, 볼륨 0, clip crowd_murmur_tense)
using System;
using UnityEngine;

public class NunchiSystem : MonoBehaviour
{
    [SerializeField] QueueManager queue;
    [SerializeField] AudioSource heartbeat;
    [SerializeField] AudioSource tinnitus;
    [SerializeField] AudioSource crowd;

    // KioskController가 채운다
    public bool LookingBack;
    public Func<bool> CanBlow;
    public Func<int> QueueCount;

    public event Action BlowupRequested;
    public event Action Sorried;

    public bool Running { get; private set; }
    public bool Hold { get; private set; }
    public float RateMul { get; private set; } = 1f;
    public float Cooldown { get; private set; }
    public int BlurStep { get; private set; }

    float gauge;
    public float Value
    {
        get => gauge;
        set => gauge = Mathf.Clamp(value, 0f, Max);
    }

    static float Max => Bal.G("Nunchi_Max", 100f);
    string Speaker => GameState.I.Profile.speakerKey;
    Vector3? QueuePos => queue != null ? queue.QueuePos : (Vector3?)null;

    float nextHurry, nextSigh, hurryWait, sayUntil, mutterWant, mutterReady;
    int hurryIdx;
    float heartTarget, ringTarget, crowdTarget;

    // ---- 진입과 종료 ----

    /// <summary>키오스크 앞에 섰을 때. 프로필이 눈치를 안 쓰면 아무것도 안 한다.</summary>
    public void Begin()
    {
        if (!GameState.I.Profile.kioskNunchi) return;
        gauge = 0f; RateMul = 1f; Cooldown = 0f; Hold = false; LookingBack = false;
        hurryWait = 0f; hurryIdx = 0; sayUntil = 0f; mutterWant = 0f; mutterReady = 0f; BlurStep = 0;
        nextHurry = Range("Nunchi_HurryFirstMin", 16f, "Nunchi_HurryFirstMax", 26f);
        nextSigh = Range("Nunchi_SighFirstMin", 4f, "Nunchi_SighFirstMax", 8f);
        Running = true;
    }

    /// <summary>키오스크를 떠날 때. 효과를 전부 거둔다.</summary>
    public void End()
    {
        if (!Running) return;
        Running = false; Hold = false;
        heartTarget = 0f; ringTarget = 0f; crowdTarget = 0f;
        SetBlurStep(0);
        HandRig.I.tremble = 0f;
        Hud.I.Nunchi(gauge, false);
        ClearPost();
    }

    void OnDisable() => ClearPost();

    static void ClearPost()
    {
        PostState.Nunchi = 0f;
        PostState.HeartTime = -1f;
    }

    // ---- 게이지 ----

    public void Add(float a)
    {
        if (Running && !Hold) Value = gauge + a;
    }

    /// <summary>뒤돌아 사과. 쿨타임이면 false.</summary>
    public bool Sorry()
    {
        if (!Running || Hold || Cooldown > 0f) return false;
        int i = UnityEngine.Random.Range(0, NunchiLines.Sorry.GetLength(0));
        Say(Speaker, NunchiLines.Sorry[i, 1], Speaker + "_" + NunchiLines.Sorry[i, 0]);
        Value = gauge - Bal.G("Nunchi_Sorry", 12f);
        Cooldown = Bal.G("Nunchi_SorryCooldown", 8f);
        hurryWait = 0f;
        GameState.I.Stats.sorry++;
        Sorried?.Invoke();
        return true;
    }

    /// <summary>실수 직후 혼잣말을 청한다. 쿨타임이면 무시하고, 다른 말이 나오는 중이면 끝난 뒤에 한다.</summary>
    public void Mutter()
    {
        if (Time.time < mutterReady) return;
        mutterWant = Time.time + Bal.G("Nunchi_MutterWait", 3f);
    }

    void SayMutter()
    {
        mutterWant = 0f;
        mutterReady = Time.time + Bal.G("Nunchi_MutterCooldown", 9f);
        int i = UnityEngine.Random.Range(0, NunchiLines.Mutter.GetLength(0));
        Say(Speaker, NunchiLines.Mutter[i, 1], Speaker + "_" + NunchiLines.Mutter[i, 0], null, Bal.G("Nunchi_MutterVolume", 0.9f));
    }

    /// <summary>다른 말과 겹치지 않게 시간을 기록하며 자막을 띄운다. pos가 있으면 음성은 그 자리에서 난다.</summary>
    public Coroutine Say(string who, string text, string vo = null, Vector3? pos = null, float vol = 1f)
    {
        sayUntil = Time.time + Mathf.Max(1.6f, text.Length * 0.1f);
        return Hud.I.Say(who, text, vo, -1f, pos, vol);
    }

    void Murmur(string text, float sec)
    {
        if (Time.time <= sayUntil) return;
        Hud.I.Say(null, text, null, sec);
        sayUntil = Time.time + sec;
    }

    // ---- 폭발 ----

    /// <summary>폭발 장면 동안 게이지를 멈추고 지켜볼 수 있는 시야로 바꾼다.</summary>
    public void HoldForBlowup()
    {
        if (Hold) return;
        Hold = true;
        Hud.I.Nunchi(Max, true);
        HandRig.I.tremble = 0f;
    }

    /// <summary>폭발 장면이 끝나고 키오스크로 돌아왔을 때.</summary>
    public void ResumeAfterBlowup()
    {
        gauge = Bal.G("Nunchi_ResumeValue", 45f);
        RateMul *= Bal.G("Nunchi_ResumeRateMul", 0.7f);
        hurryWait = 0f;
        nextHurry = Bal.G("Nunchi_ResumeHurry", 20f);
        Hold = false;
    }

    void TryBlow()
    {
        bool can = BlowupRequested != null && (CanBlow == null || CanBlow());
        if (!can) { gauge = Mathf.Min(gauge, Max - 1f); return; }
        HoldForBlowup();
        BlowupRequested.Invoke();
    }

    // ---- 매 프레임 ----

    void Update()
    {
#if UNITY_EDITOR || DEVELOPMENT_BUILD
        var kb = UnityEngine.InputSystem.Keyboard.current;
        if (kb != null && kb.f6Key.wasPressedThisFrame) Add(100f);
#endif
        FadeLoop(heartbeat, heartTarget);
        FadeLoop(tinnitus, ringTarget);
        FadeLoop(crowd, crowdTarget);
        if (Running && !Hold) Tick(Time.deltaTime);
        if (Running)
        {
            // 폭발 장면은 지켜볼 수 있는 시야로 둔다
            PostState.Nunchi = Hold ? Bal.G("Post_WatchNunchi", 50f) : gauge;
            PostState.HeartTime = heartbeat != null && heartbeat.isPlaying ? heartbeat.time : -1f;
        }
    }

    void Tick(float dt)
    {
        Cooldown = Mathf.Max(0f, Cooldown - dt);
        int q = QueueCount != null ? QueueCount() : Bal.I("Nunchi_DefaultQueue", 3);
        Value = gauge + (Bal.G("Nunchi_PerSecond", 0.6f) + Bal.G("Nunchi_PerQueue", 0.2f) * q) * RateMul * dt;
        Hud.I.Nunchi(gauge, true);
        ApplyStage();

        // 한숨, 혀 차는 소리, 발끝
        nextSigh -= dt;
        if (nextSigh <= 0f)
        {
            nextSigh = Range("Nunchi_SighMin", 5f, "Nunchi_SighMax", 10f) * (1f - gauge / (Max * 2f));
            string s = NunchiLines.Sighs[UnityEngine.Random.Range(0, NunchiLines.Sighs.Length)];
            AudioManager.I.Play(s, QueuePos, Bal.G("Nunchi_SighVolume", 0.8f), UnityEngine.Random.Range(0.95f, 1.05f));
            if (!LookingBack) Murmur(NunchiLines.SighText(s), 1.3f);
        }

        // 실수 직후 혼잣말
        if (mutterWant > 0f)
        {
            if (Time.time > mutterWant) mutterWant = 0f;
            else if (Time.time >= sayUntil) SayMutter();
        }

        // 재촉
        nextHurry -= dt;
        if (nextHurry <= 0f)
        {
            nextHurry = Range("Nunchi_HurryMin", 25f, "Nunchi_HurryMax", 40f);
            int i = hurryIdx++ % NunchiLines.Hurry.GetLength(0);
            Say(NunchiLines.Hurry[i, 1], NunchiLines.Hurry[i, 2], NunchiLines.Hurry[i, 0], QueuePos);
            PlayerController.I.AddShake(Bal.G("Nunchi_HurryShake", 0.12f));
            if (!LookingBack) hurryWait = Bal.G("Nunchi_HurryIgnoreWindow", 7f);
        }
        if (hurryWait > 0f)
        {
            if (LookingBack) hurryWait = 0f;
            else
            {
                hurryWait -= dt;
                if (hurryWait <= 0f) Add(Bal.G("Nunchi_HurryIgnored", 8f));
            }
        }

        if (gauge >= Max) TryBlow();
    }

    // ---- 단계 효과 ----

    void ApplyStage()
    {
        float heartAt = Bal.G("Nunchi_HeartAt", 40f), trembleAt = Bal.G("Nunchi_TrembleAt", 60f), ringAt = Bal.G("Nunchi_RingAt", 80f);
        float a = Mathf.Clamp01((gauge - heartAt) / (ringAt - heartAt));

        HandRig.I.tremble = Mathf.Clamp01((gauge - trembleAt) / (Max - trembleAt));

        heartTarget = gauge >= heartAt ? Bal.G("Nunchi_HeartVolMin", 0.35f) + a * Bal.G("Nunchi_HeartVolAdd", 0.5f) : 0f;
        ringTarget = gauge >= ringAt ? Bal.G("Nunchi_RingVolume", 0.22f) : 0f;

        // 뒤 사람들의 웅성임은 심장 소리와 같은 단계에서 시작해 게이지 끝까지 커진다
        float crowdAt = Bal.G("Nunchi_CrowdAt", heartAt);
        crowdTarget = gauge >= crowdAt ? Bal.G("Nunchi_CrowdVolMin", 0.3f) + Mathf.Clamp01((gauge - crowdAt) / (Max - crowdAt)) * Bal.G("Nunchi_CrowdVolAdd", 0.6f) : 0f;

        SetBlurStep(gauge >= Bal.G("Nunchi_BlurStep2At", 92f) ? 2 : gauge >= ringAt ? 1 : 0);
    }

    void SetBlurStep(int step)
    {
        if (step == BlurStep) return;
        BlurStep = step;
    }

    void FadeLoop(AudioSource src, float target)
    {
        if (src == null) return;
        if (target > 0f && !src.isPlaying)
        {
            src.loop = true;
            src.Play();
        }
        src.volume = Mathf.MoveTowards(src.volume, target, Time.deltaTime / Mathf.Max(0.01f, Bal.G("Nunchi_AudioFade", 1f)));
        if (target <= 0f && src.volume <= 0f && src.isPlaying) src.Stop();
    }

    static float Range(string minKey, float min, string maxKey, float max)
    {
        return UnityEngine.Random.Range(Bal.G(minKey, min), Bal.G(maxKey, max));
    }
}
