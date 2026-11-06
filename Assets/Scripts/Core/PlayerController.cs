using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

// 1인칭 이동. 느린 걸음, 고개 흔들림, 다리 절기(프로필 limp), 연출용 시선과 걷기
// 위치 기준은 발. Y는 Teleport 높이에 고정(중력 없음, HTML판과 같음)
// 배치: body = Player의 CharacterController (radius 0.28, height 1.7, center 0 0.85 0)
// 배치: eye = Player 자식 Camera (AudioListener 포함, FOV 66, near 0.03)
// 배치: handRoot = Eye 자식 HandRoot (로컬 원점, HandRig 부착)
[DefaultExecutionOrder(-50)]
public class PlayerController : MonoBehaviour
{
    public enum Mode { Fps, Cursor, Locked, Hidden }   // Locked 커서 보임(제목, 결과), Hidden 시점 고정 연출

    public static PlayerController I { get; private set; }

    [SerializeField] CharacterController body;
    [SerializeField] Camera eye;
    [SerializeField] Transform handRoot;

    public Camera Eye => eye;
    public Transform HandRoot => handRoot;
    public Mode CurrentMode { get; private set; } = Mode.Fps;
    public bool Frozen { get; private set; } = true;
    public string Ground { get; set; } = "concrete";
    public float Yaw { get; private set; }      // 도, Unity 기준
    public float Pitch { get; private set; }    // 도, 위가 +
    public bool HoldStill { get; set; }         // 시선은 돌되 걷지 않음(메모 읽기)
    public float EyeHeight => Bal.Age("EyeHeight", 1.68f, 1.66f, 1.62f, 1.56f);
    float MoveSpeed => Bal.Age("MoveSpeed", 2.2f, 1.9f, 1.5f, 1.15f);
    public Vector3 EyePos => transform.position + Vector3.up * EyeHeight;
    public float Bob => bob;
    public float Walk01 => Mathf.Clamp01(moving / 1.15f);
    public Vector2 Cursor01 => cursor01;        // 뷰포트 좌표, 왼쪽 아래가 (0,0)

    class Turn { public float t, sec, y0, y1, p0, p1, back, arc; }
    class Walk { public Vector3 target; public float speed, stuck; public Vector3 from, bend; public float sec, t; }

    Turn turn;
    Walk walk;
    Vector3? gaze;
    float idle;
    Vector2 cursor01 = new(0.5f, 0.5f), cursorWant = new(0.5f, 0.5f);
    float groundY, moving, stepAcc, bob, shake;
    int stepsTaken;

    // 컷 전환: 지금 시점에서 새 시점으로 천천히 옮겨 간다
    Vector3 blendPos;
    Quaternion blendRot;
    float blendT = -1f, blendSec, blendFov, blendFovTo = -1f;
    float limitYaw, limitHalf = -1f, limitDown, limitUp;

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
        groundY = transform.position.y;
        Yaw = transform.eulerAngles.y;
    }

    void Start() => SetMode(CurrentMode);

    public void SetMode(Mode m)
    {
        CurrentMode = m;
        Cursor.lockState = m == Mode.Fps || m == Mode.Hidden ? CursorLockMode.Locked : m == Mode.Cursor ? CursorLockMode.Confined : CursorLockMode.None;
        Cursor.visible = m == Mode.Locked;
        if (m == Mode.Cursor) cursor01 = cursorWant = new Vector2(0.5f, 0.5f);
        if (Hud.I != null) Hud.I.Cross(m == Mode.Fps);
    }

    public void Freeze(bool on)
    {
        Frozen = on;
        if (on) return;
        gaze = null;
        idle = 0f;
    }

    /// <summary>조작이 잠긴 동안 시선을 천천히 옮겨 줄 곳. 말하는 사람이나 관심 대상.</summary>
    public void Gaze(Vector3 world)
    {
        if (Frozen) gaze = world;
    }

    // 잠겨 있는 동안 정해진 곳으로 시선이 천천히 간다. 정해진 곳이 없으면 잠시 뒤 가까운 목표로
    void Follow(float dt)
    {
        idle += dt;
        if (gaze == null && !HoldStill && idle > Bal.G("Look_IdleSec", 2f)) gaze = Interactable.Nearest(EyePos, Bal.G("Look_IdleDist", 6f));
        if (gaze == null) return;
        Vector3 d = gaze.Value - EyePos;
        float k = 1f - Mathf.Exp(-dt * 3f / Mathf.Max(Bal.G("Look_FollowSec", 0.6f), 0.01f));
        Yaw += Mathf.DeltaAngle(Yaw, Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg) * k;
        Pitch = Mathf.Lerp(Pitch, Mathf.Atan2(d.y, new Vector2(d.x, d.z).magnitude) * Mathf.Rad2Deg, k);
    }

    /// <summary>순간이동 직전에 부른다. 지금 보이는 시점에서 Cine_BlendSec 동안 새 시점으로 옮겨 간다. 암전 컷에는 쓰지 않는다.</summary>
    public void BlendCamera()
    {
        blendPos = eye.transform.position;
        blendRot = eye.transform.rotation;
        blendFov = eye.fieldOfView;
        blendFovTo = -1f;
        blendSec = Mathf.Max(Bal.G("Cine_BlendSec", 1f), 0.01f);
        blendT = 0f;
    }

    /// <summary>앉은 자리처럼 고개 돌리는 범위를 묶는다. 각도는 도. FreeLook으로 푼다.</summary>
    public void LimitLook(float centerYaw, float halfYaw, float down, float up)
    {
        limitYaw = centerYaw;
        limitHalf = halfYaw;
        limitDown = down;
        limitUp = up;
    }

    public void FreeLook() => limitHalf = -1f;

    public void SetCursor01(Vector2 v) => cursor01 = cursorWant = v;

    public void AddShake(float a) => shake = Mathf.Min(1f, shake + a);

    // 시선은 두고 자리만 옮긴다(계단)
    public void MoveTo(Vector3 pos)
    {
        groundY = pos.y;
        if (body != null) body.enabled = false;
        transform.position = pos;
        Physics.SyncTransforms();
        if (body != null) body.enabled = true;
    }

    // yaw는 도, Unity 기준. HTML판 라디안 yaw는 -yaw * Mathf.Rad2Deg
    public void Teleport(Vector3 pos, float yaw)
    {
        turn = null;
        walk = null;
        gaze = null;
        moving = 0f;
        groundY = pos.y;
        Yaw = yaw;
        Pitch = 0f;
        if (body != null) body.enabled = false;
        transform.SetPositionAndRotation(pos, Quaternion.Euler(0f, yaw, 0f));
        Physics.SyncTransforms();
        if (body != null) body.enabled = true;
    }

    public IEnumerator LookAt(Vector3 world, float sec = 1f)
    {
        Gaze(world);
        Vector3 d = world - EyePos;
        float yaw = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
        float pitch = Mathf.Atan2(d.y, new Vector2(d.x, d.z).magnitude) * Mathf.Rad2Deg;
        return TurnTo(yaw, pitch, sec);
    }

    public IEnumerator TurnTo(float yaw, float pitch, float sec = 1f)
    {
        var w = new Turn { sec = sec, y0 = Yaw, y1 = Yaw + Mathf.DeltaAngle(Yaw, yaw), p0 = Pitch, p1 = pitch };
        turn = w;
        while (turn == w) yield return null;
    }

    // speed 생략하면 현재 인물의 걸음 속도
    public IEnumerator WalkTo(Vector3 world, float speed = -1f)
    {
        var w = new Walk { target = world, speed = speed > 0f ? speed : MoveSpeed };
        walk = w;
        while (walk == w) yield return null;
    }

    // 자동 연출 공통. sec 동안 서서히 출발해 서서히 멈춘다. bend 쪽으로 살짝 휘어 간다
    public IEnumerator WalkCurve(Vector3 world, Vector3 bend, float sec)
    {
        var w = new Walk { target = world, from = transform.position, bend = bend, sec = Mathf.Max(sec, 0.01f) };
        walk = w;
        while (walk == w) yield return null;
    }

    // 자동 연출 공통. 시선이 호를 그리며 가서 살짝 지나쳤다가 되돌아온다
    public IEnumerator LookArc(Vector3 world, float sec)
    {
        Gaze(world);
        Vector3 d = world - EyePos;
        float yaw = Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg;
        var w = new Turn
        {
            sec = sec, y0 = Yaw, y1 = Yaw + Mathf.DeltaAngle(Yaw, yaw), p0 = Pitch, p1 = Mathf.Atan2(d.y, new Vector2(d.x, d.z).magnitude) * Mathf.Rad2Deg,
            back = Bal.G("Cam_LookBack", 1.2f), arc = Bal.G("Cam_LookArcDeg", 2f),
        };
        turn = w;
        while (turn == w) yield return null;
    }

    void Update()
    {
        if (PauseMenu.On) return;
        float dt = Mathf.Min(Time.deltaTime, 0.05f);
        var mouse = Mouse.current;
        Look(dt, mouse);
        Move(dt);
        ApplyCamera(dt);

        if (CurrentMode == Mode.Cursor)
        {
            if (mouse != null && mouse.delta.ReadValue().sqrMagnitude > 0f)
            {
                Vector2 p = mouse.position.ReadValue();
                cursorWant = new Vector2(Mathf.Clamp01(p.x / Screen.width), Mathf.Clamp01(p.y / Screen.height));
            }
            float lag = Debuff.CursorLagSec;
            cursor01 = lag > 0.001f ? Vector2.Lerp(cursor01, cursorWant, 1f - Mathf.Exp(-dt / lag)) : cursorWant;
        }
        else if (CurrentMode == Mode.Fps && !Frozen && walk == null && turn == null)
            Interactable.Tick(eye.transform.position, eye.transform.forward);
        else
            Interactable.Clear();
    }

    void Look(float dt, Mouse mouse)
    {
        if (turn != null)
        {
            var w = turn;
            w.t = Mathf.Min(1f, w.t + dt / Mathf.Max(w.sec, 1e-3f));
            float e = w.t * w.t * (3f - 2f * w.t);
            if (w.back > 0f)
            {
                float u = e - 1f;
                e = 1f + (w.back + 1f) * u * u * u + w.back * u * u;   // 지나쳤다가 되돌아온다
            }
            Yaw = Mathf.LerpUnclamped(w.y0, w.y1, e);
            Pitch = Mathf.LerpUnclamped(w.p0, w.p1, e) + Mathf.Sin(w.t * Mathf.PI) * w.arc;
            if (w.t >= 1f) turn = null;
        }
        else if (CurrentMode == Mode.Fps && Frozen && walk == null) Follow(dt);
        else if (CurrentMode == Mode.Fps && !Frozen && mouse != null)
        {
            Vector2 d = mouse.delta.ReadValue();
            float sens = Bal.G("Player_MouseSens", 0.0019f) * Mathf.Rad2Deg * Bal.Age("LookScale", 1f, 1f, 1f, 0.5f);
            Yaw += d.x * sens;
            Pitch = Mathf.Clamp(Pitch + d.y * sens, Bal.G("Player_PitchDown", -1.1f) * Mathf.Rad2Deg, Bal.G("Player_PitchUp", 1.05f) * Mathf.Rad2Deg);
            if (limitHalf >= 0f)
            {
                Yaw = limitYaw + Mathf.Clamp(Mathf.DeltaAngle(limitYaw, Yaw), -limitHalf, limitHalf);
                Pitch = Mathf.Clamp(Pitch, limitDown, limitUp);
            }
        }
        transform.rotation = Quaternion.Euler(0f, Yaw, 0f);
    }

    void Move(float dt)
    {
        float speed = MoveSpeed;
        Vector3 dir = Vector3.zero;
        float want = 0f;
        if (walk != null && walk.sec > 0f)
        {
            walk.t = Mathf.Min(1f, walk.t + dt / walk.sec);
            float e = walk.t * walk.t * (3f - 2f * walk.t);
            Vector3 d = Vector3.Lerp(Vector3.Lerp(walk.from, walk.bend, e), Vector3.Lerp(walk.bend, walk.target, e), e) - transform.position;
            d.y = 0f;
            float dist = d.magnitude;
            if (dist > 0.0001f) { dir = d / dist; want = dist / Mathf.Max(dt, 0.001f); }
            if (walk.t >= 1f) walk = null;
        }
        else if (walk != null)
        {
            Vector3 d = walk.target - transform.position;
            d.y = 0f;
            float dist = d.magnitude;
            if (dist < 0.06f) walk = null;
            else { dir = d / dist; want = walk.speed; }
        }
        else if (!Frozen && !HoldStill && CurrentMode == Mode.Fps && Keyboard.current != null)
        {
            var kb = Keyboard.current;
            int f = (kb.wKey.isPressed || kb.upArrowKey.isPressed ? 1 : 0) - (kb.sKey.isPressed || kb.downArrowKey.isPressed ? 1 : 0);
            int s = (kb.dKey.isPressed || kb.rightArrowKey.isPressed ? 1 : 0) - (kb.aKey.isPressed || kb.leftArrowKey.isPressed ? 1 : 0);
            if (f != 0 || s != 0)
            {
                dir = (transform.forward * f + transform.right * s).normalized;
                bool run = f >= 0 && CanRun && kb.shiftKey.isPressed;
                want = run ? RunSpeed : speed * (f < 0 ? Bal.F("BackSpeedMul", 0.7f) : 1f);
            }
        }

        moving = Damp(moving, want, 8f, dt);
        if (moving > 0.02f)
        {
            Vector3 before = transform.position;
            Vector3 motion = dir * (moving * dt);
            if (body != null && body.enabled) body.Move(motion); else transform.position += motion;
            Vector3 p = transform.position;
            if (p.y != groundY) { p.y = groundY; transform.position = p; }

            // 연출 걷기가 벽에 막혀 끝나지 않는 일을 막는다
            if (walk != null)
            {
                bool blocked = (transform.position - before).magnitude < motion.magnitude * 0.2f;
                walk.stuck = blocked ? walk.stuck + dt : 0f;
                if (walk.stuck > 1.5f) walk = null;
            }

            stepAcc += moving * dt;
            if (stepAcc > Mathf.Lerp(Bal.Age("StepStride", 0.85f, 0.75f, 0.68f, 0.62f), CanRun ? Bal.F("RunStepStride", 0.95f) : 0f, Run01)) { stepAcc = 0f; Step(); }
        }
        bob += moving * dt * Mathf.Lerp(Bal.Age("BobRate", 3.7f, 4.2f, 4.6f, 5.1f), CanRun ? Bal.F("RunBobRate", 3.3f) : 0f, Run01);
    }

    static bool CanRun => GameState.I != null && GameState.I.Profile != null && GameState.I.Profile.canRun;
    static float RunSpeed => Bal.F("RunSpeed", 3.96f);

    // 0 걷기, 1 달리기. 빨라지는 동안 걸음과 고개 흔들림이 따라간다
    float Run01 => CanRun ? Mathf.Clamp01((moving - MoveSpeed) / Mathf.Max(RunSpeed - MoveSpeed, 0.01f)) : 0f;

    void ApplyCamera(float dt)
    {
        float t = Time.time;
        var profile = GameState.I != null ? GameState.I.Profile : null;
        float limp = profile != null && profile.limp ? 1f : 0f;
        float s = Mathf.Sin(bob), c = Mathf.Cos(bob * 0.5f);
        float amp = Mathf.Clamp01(moving / Mathf.Max(MoveSpeed, 0.01f));

        // 왼다리가 불편한 걸음: 위아래가 좌우 비대칭
        float h = Mathf.Lerp(Bal.Age("BobHeight", 0.018f, 0.026f, 0.034f, 0.042f), CanRun ? Bal.F("RunBobHeight", 0.06f) : 0f, Run01);
        float by = (Mathf.Abs(s) * h - h * 0.476f) * amp + Mathf.Sin(t * 1.3f) * (0.0035f + (Frozen ? Bal.G("Cam_BreathAmp", 0.005f) : 0f));
        float roll = c * Bal.F("LimpRoll", 0.016f) * amp * limp + Mathf.Sin(t * 0.7f) * 0.0022f;
        float sway = c * Bal.F("LimpSway", 0.018f) * amp * limp;

        shake = Damp(shake, 0f, 5f, dt);
        float sh = shake;
        eye.transform.localPosition = new Vector3(
            sway + Random.Range(-1f, 1f) * sh * 0.012f,
            EyeHeight + by + Random.Range(-1f, 1f) * sh * 0.012f,
            0f);
        float calm = Frozen ? Bal.G("Look_BreathDeg", 0.3f) : 0f;   // 잠겨 있어도 시선이 굳지 않게 숨 쉬듯 흔든다
        float pitch = Pitch + (Random.Range(-1f, 1f) * sh * 0.006f + Mathf.Sin(t * 0.9f) * 0.0016f) * Mathf.Rad2Deg + Mathf.Sin(t * 1.1f) * calm;
        eye.transform.localRotation = Quaternion.Euler(-pitch, Mathf.Sin(t * 0.73f) * calm * 0.7f, roll * Mathf.Rad2Deg);

        if (blendT < 0f) return;
        if (blendFovTo < 0f) blendFovTo = eye.fieldOfView;
        blendT += dt / blendSec;
        if (blendT >= 1f)
        {
            eye.fieldOfView = blendFovTo;
            blendT = -1f;
            return;
        }
        float e = blendT * blendT * (3f - 2f * blendT);
        eye.transform.SetPositionAndRotation(Vector3.Lerp(blendPos, eye.transform.position, e), Quaternion.Slerp(blendRot, eye.transform.rotation, e));
        eye.fieldOfView = Mathf.Lerp(blendFov, blendFovTo, e);
    }

    void Step()
    {
        stepsTaken++;
        var audio = AudioManager.I;
        if (audio == null) return;
        // 자기 몸 소리는 먹먹함을 받지 않는다
        audio.Play(Ground == "tile" ? "step_tile" : "step_concrete", null, 0.42f, Random.Range(0.92f, 1.04f), true);
        var profile = GameState.I != null ? GameState.I.Profile : null;
        if (profile == null || !profile.limp) return;
        int cane = Mathf.RoundToInt(Bal.Age("CaneEverySteps", 0f, 0f, 0f, 2f));
        if (cane > 0 && stepsTaken % cane == 0) audio.Play("cane_tap", null, 0.26f, Random.Range(0.95f, 1.05f), true);
        if (stepsTaken % Mathf.Max(1, Mathf.RoundToInt(Bal.F("BreathEverySteps", 19f))) == 0) audio.Play("breath_old", null, 0.32f, 1f, true);
    }

    static float Damp(float a, float b, float k, float dt) => Mathf.Lerp(a, b, 1f - Mathf.Exp(-k * dt));
}
