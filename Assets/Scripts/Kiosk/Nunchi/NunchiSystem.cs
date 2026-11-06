// 눈치: 게이지 증감, 답답함 점수로 나오는 뒷사람 반응, 실수 직후 혼잣말, 그만두기 버튼, 단계 효과.
// 수치는 전부 Bal에서 사용 시점에 읽는다. 인물 정보는 GameState.I.Profile만 본다.
// 배치: queue = Store 씬 Director의 QueueManager (뒤 사람 소리가 나는 곳)
// 배치: heartbeat = 자식 AudioSource Nunchi_Heartbeat (loop, playOnAwake 끔, 볼륨 0, clip heartbeat)
// 배치: tinnitus = 자식 AudioSource Nunchi_Tinnitus (loop, playOnAwake 끔, 볼륨 0, clip tinnitus)
// 배치: crowd = 자식 AudioSource Nunchi_Crowd (loop, playOnAwake 끔, 볼륨 0, clip crowd_murmur_tense)
using System;
using System.Collections.Generic;
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
    public Func<string> ScreenId;

    NunchiRule rule;
    float hurryMul = 1f, sighMul = 1f;
    bool asking;

    /// <summary>회차 규칙. Enter 전에 부른다.</summary>
    public void Configure(NunchiRule r) => rule = r;
    public event Action Sorried;

    public bool Running { get; private set; }
    public float RateMul { get; private set; } = 1f;
    public float Cooldown { get; private set; }
    public int BlurStep { get; private set; }

    float gauge, calmUntil;
    public float Value
    {
        get => gauge;
        set => gauge = Mathf.Clamp(value, 0f, Max);
    }

    static float Max => Bal.G("Nunchi_Max", 100f);
    string Speaker => GameState.I.Profile.speakerKey;
    Vector3? QueuePos => queue != null ? queue.QueuePos : (Vector3?)null;

    float hurryWait, sayUntil, mutterWant, mutterReady;
    // 답답함 점수. 실수와 한 화면에 머문 시간으로 오르고, 처음 보는 화면으로 넘어가면 내린다
    float sighScore, sighElapsed, sighReady, sameScreenSec, missAt;
    string lastScreen;
    readonly HashSet<string> seenScreens = new HashSet<string>();
    string lastBack;
    float heartTarget, ringTarget, crowdTarget;

    // ---- 진입과 종료 ----

    /// <summary>키오스크 앞에 섰을 때. 프로필이 눈치를 안 쓰면 아무것도 안 한다.</summary>
    public void Begin()
    {
        if (!GameState.I.Profile.kioskNunchi) return;
        gauge = rule != null ? rule.start : 0f; RateMul = 1f; Cooldown = 0f; LookingBack = false;
        hurryMul = 1f; sighMul = 1f; asking = false;
        hurryWait = 0f; lastBack = null; sayUntil = 0f; mutterWant = 0f; mutterReady = 0f; BlurStep = 0;
        sighScore = 0f; sighElapsed = 0f; sighReady = 0f; sameScreenSec = 0f; missAt = -1f;
        lastScreen = null;
        seenScreens.Clear();
        Running = true;
    }

    /// <summary>키오스크를 떠날 때. 효과를 전부 거둔다.</summary>
    public void End()
    {
        if (!Running) return;
        Running = false;
        heartTarget = 0f; ringTarget = 0f; crowdTarget = 0f;
        if (RoundUi.I != null) RoundUi.I.GiveUp(null);
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

    /// <summary>오터치, 잘못된 버튼, 튕김. 한 번의 실수에 여러 곳이 불러도 한 번만 친다.</summary>
    public void Miss()
    {
        if (!Running || Time.time - missAt < 0.3f) return;
        missAt = Time.time;
        sighScore += Bal.G("Nunchi_SighMissScore", 6f);
    }

    // ---- 게이지 ----

    public void Add(float a)
    {
        if (Running) Value = gauge + a;
    }

    /// <summary>뒤돌아 사과. 쿨타임이면 false.</summary>
    public bool Sorry()
    {
        if (!Running || Cooldown > 0f) return false;
        int i = UnityEngine.Random.Range(0, NunchiLines.Sorry.GetLength(0));
        Say(Speaker, NunchiLines.Sorry[i, 1], Speaker + "_" + NunchiLines.Sorry[i, 0]);
        Value = gauge - Bal.G("Nunchi_Sorry", 25f);
        Cooldown = Bal.G("Nunchi_SorryCooldown", 5f);
        calmUntil = Time.time + Bal.G("Nunchi_SorryHoldSec", 2f);
        hurryWait = 0f;
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
        int i;
        do i = UnityEngine.Random.Range(0, NunchiLines.Mutter.GetLength(0));
        while (Array.IndexOf(NunchiLines.OldVoice, Speaker + "_" + NunchiLines.Mutter[i, 0]) >= 0);
        Say(Speaker, NunchiLines.Mutter[i, 1], Speaker + "_" + NunchiLines.Mutter[i, 0], null, Bal.G("Nunchi_MutterVolume", 0.9f));
    }

    /// <summary>다른 말과 겹치지 않게 시간을 기록하며 자막을 띄운다. pos가 있으면 음성은 그 자리에서 난다.</summary>
    public Coroutine Say(string who, string text, string vo = null, Vector3? pos = null, float vol = 1f, bool clear = false)
    {
        sayUntil = Time.time + Mathf.Max(1.6f, text.Length * 0.1f, vo != null ? AudioManager.I.VoLength(vo) : 0f);
        return Hud.I.Say(who, text, vo, -1f, pos, vol, clear);
    }

    void Murmur(string text, float sec)
    {
        if (Time.time <= sayUntil) return;
        Hud.I.Say("back", text, null, sec);
        sayUntil = Time.time + sec;
    }

    // ---- 매 프레임 ----

    void Update()
    {
        FadeLoop(heartbeat, heartTarget);
        FadeLoop(tinnitus, ringTarget);
        FadeLoop(crowd, crowdTarget);
        if (Running)
        {
            Tick(Time.deltaTime);
            PostState.Nunchi = gauge;
            PostState.HeartTime = heartbeat != null && heartbeat.isPlaying ? heartbeat.time : -1f;
        }
    }

    void Tick(float dt)
    {
        Cooldown = Mathf.Max(0f, Cooldown - dt);
        int q = QueueCount != null ? QueueCount() : 1;
        float fill = Mathf.Max(Bal.Age("NunchiFillSec", 900f, 120f, 80f, 60f), 1f);
        if (Time.time >= calmUntil) Value = gauge + Max / fill * (1f + Bal.G("Nunchi_PerQueueMul", 0.03f) * Mathf.Max(q - 1, 0)) * RateMul * dt;
        Hud.I.Nunchi(gauge, true);
        ApplyStage();

        // 뒷사람 반응. 첫 시간에는 아무 반응이 없다
        TickSighScore(dt);
        float limit = Bal.G("Nunchi_SighScore", 20f);
        if (sighElapsed >= Bal.G("Nunchi_SighMinSec", 30f) && sighScore >= limit && Time.time >= sighReady)
        {
            sighReady = Time.time + Bal.G("Nunchi_SighGapSec", 12f) * hurryMul * (1f - gauge / (Max * 2f));
            BackReact(limit);
        }

        // 실수 직후 혼잣말
        if (mutterWant > 0f)
        {
            if (Time.time > mutterWant) mutterWant = 0f;
            else if (Time.time >= sayUntil) SayMutter();
        }

        // 재촉을 못 들은 척하면 눈치가 오른다
        if (hurryWait > 0f)
        {
            if (LookingBack) hurryWait = 0f;
            else
            {
                hurryWait -= dt;
                if (hurryWait <= 0f) Add(Bal.G("Nunchi_HurryIgnored", 8f));
            }
        }

        // 버튼 없이 줄 맨 뒤로 가는 규칙
        if (gauge >= Max && rule != null && rule.onFull != null && (CanBlow == null || CanBlow()))
        {
            rule.onFull();
            return;
        }

        // 다 차면 버튼. 규칙에 선택지가 없으면 100에서 멈추고 한숨만 계속된다
        bool can = gauge >= Max && rule != null && rule.choices != null && !asking && (CanBlow == null || CanBlow());
        if (RoundUi.I != null)
        {
            RoundUi.I.GiveUp(can ? "그만두기" : null);   // 임시 T06
            if (can && RoundUi.I.GiveUpClicked()) StartCoroutine(GiveUpRun());
        }
    }

    void TickSighScore(float dt)
    {
        sighElapsed += dt;
        string screen = ScreenId != null ? ScreenId() : null;
        if (screen != lastScreen)
        {
            lastScreen = screen;
            sameScreenSec = 0f;
            if (screen != null && seenScreens.Add(screen) && seenScreens.Count > 1)
                sighScore = Mathf.Max(0f, sighScore - Bal.G("Nunchi_SighStepDown", 8f));
        }
        sameScreenSec += dt;
        if (sameScreenSec > Bal.G("Nunchi_SighStallFreeSec", 10f)) sighScore += Bal.G("Nunchi_SighStallRate", 1f) * dt;
    }

    // 점수가 높을수록 센 칸에서 고른다. 같은 줄은 연속으로 나오지 않는다. 화자와 같은 성별이 줄에 없으면 그 문구는 뺀다
    void BackReact(float limit)
    {
        int tier = sighScore >= limit * Bal.G("Nunchi_BackHighMul", 2f) ? 2 : sighScore >= limit * Bal.G("Nunchi_BackMidMul", 1.5f) ? 1 : 0;
        var pool = new List<string>(NunchiLines.Back[tier]);
        if (!GameState.I.Profile.limp) pool.Remove(NunchiLines.ElderOnly);
        pool.RemoveAll(t => VoicePos(t) == null);
        if (pool.Count == 0) return;
        if (pool.Count > 1) pool.Remove(lastBack);
        string text = pool[UnityEngine.Random.Range(0, pool.Count)];
        lastBack = text;

        if (text == NunchiLines.Sigh)
        {
            // 1회차에 들은 그 소리를 끝까지 쓴다
            AudioManager.I.Play("sigh_m_1", QueuePos, Bal.G("Nunchi_SighVolume", 0.8f) * sighMul, 1f, true);
            if (!LookingBack) Murmur(text, 1.3f);
            return;
        }
        if (text == NunchiLines.Crowd)
        {
            AudioManager.I.PlayShort("crowd_murmur_tense", 2f, QueuePos, Bal.G("Nunchi_CrowdVolume", 0.5f));
            if (!LookingBack) Murmur(text, 1.3f);
            return;
        }
        Say("back", text, VoFor(text), VoicePos(text), 1f, true);
        if (tier == 0) return;
        PlayerController.I.AddShake(Bal.G("Nunchi_HurryShake", 0.12f));
        if (!LookingBack) hurryWait = Bal.G("Nunchi_HurryIgnoreWindow", 7f);
    }

    // 음성은 기존 파일이 있는 문구만
    static string VoFor(string text)
    {
        for (int i = 0; i < NunchiLines.Hurry.GetLength(0); i++)
            if (NunchiLines.Hurry[i, 2] == text) return NunchiLines.Hurry[i, 0];
        return null;
    }

    // 문구가 나는 자리. 표의 화자와 성별이 같은 줄 손님에게서 나고, 그런 사람이 없으면 null. 한숨과 웅성거림은 줄 맨 앞
    Vector3? VoicePos(string text)
    {
        for (int i = 0; i < NunchiLines.Hurry.GetLength(0); i++)
            if (NunchiLines.Hurry[i, 2] == text)
                return queue != null ? queue.VoicePos(NunchiLines.Hurry[i, 1] != "yM") : (Vector3?)null;
        return QueuePos;
    }

    System.Collections.IEnumerator GiveUpRun()
    {
        asking = true;
        RoundUi.I.GiveUp(null);
        int picked = 1;
        yield return Choice.Ask(rule.choices, i => picked = i);
        asking = false;
        if (picked == 0) { rule.onLeave?.Invoke(); yield break; }
        // 임시 T18
        gauge = Bal.G("Nunchi_ResumeValue", 45f);
        hurryMul *= Bal.G("Nunchi_StayHurryMul", 0.7f);
        sighMul *= Bal.G("Nunchi_StaySighMul", 1.3f);
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

}
