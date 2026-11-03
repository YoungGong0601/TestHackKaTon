using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using Random = UnityEngine.Random;

// 게임 전체 흐름. 씬에 아무것도 놓지 않아도 스스로 생겨서 지형, 차, UI를 만든다
// 인원 설정 → [요소 뽑기 → 역할 배정 → 차례별 작업 → 재생 → 현황 공개] x 회차 → 승패
public class GameFlow : MonoBehaviour
{
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    static void Boot()
    {
        if (FindAnyObjectByType<GameFlow>() == null) new GameObject("GameFlow").AddComponent<GameFlow>();
    }

    Track track;
    RoadPainter road;
    Car car;
    Camera cam;
    Vector2 baseGravity, roundStart;
    int players = 4;
    bool follow;
    string lastResult = "";

    static float TaskTime => Env.Cfg("Time.Task", 15f);

    void Start()
    {
        cam = Camera.main;
        baseGravity = Physics2D.gravity;
        StartCoroutine(Run());
    }

    void LateUpdate()
    {
        if (follow) cam.transform.position = new Vector3(car.Position.x + 3f, car.Position.y + 1f, -10f);
    }

    IEnumerator Run()
    {
        Hud.Init();
        Hud.Panel("설정을 불러오는 중입니다", true);
        for (float t = 0; !ConfigTableLoader.IsLoaded && t < 5f; t += Time.deltaTime) yield return null;

        // 수치를 읽은 뒤에 만든다
        track = new GameObject("Track").AddComponent<Track>();
        road = new GameObject("Roads").AddComponent<RoadPainter>();
        car = Car.Create();

        while (true) {
            yield return Setup();
            yield return PlayGame();
        }
    }

    IEnumerator Setup()
    {
        Focus(0f, Track.ScreenW);
        while (true) {
            Hud.Info("");
            Hud.Panel($"블라인드 협동 레이싱\n\n인원: {players}명", true, "-", "+", "시작");
            yield return new WaitUntil(() => Hud.Picked >= 0);
            if (Hud.Picked == 0) players = Mathf.Max(2, players - 1);
            else if (Hud.Picked == 1) players = Mathf.Min(6, players + 1);
            else yield break;
        }
    }

    IEnumerator PlayGame()
    {
        Env.Reset();
        track.ResetAll();
        road.Clear(0, Track.SegCount);
        roundStart = new Vector2(Track.StartX, Track.Height(Track.StartX) + 1f);
        car.Teleport(roundStart);
        car.Freeze();

        int rounds = Env.Cfg("Round.Count", 5);
        bool win = false;
        for (int round = 1; round <= rounds && !win; round++) {
            var (from, to) = Track.Range(roundStart.x);
            var tasks = DrawRound(from, to);
            var owners = Assign(tasks.Count);
            for (int i = 0; i < tasks.Count; i++) yield return Turn(round, tasks[i], owners[i], from, to);
            yield return Playback(r => win = r);
            if (!win && round < rounds) yield return Reveal(round, rounds);
        }
        yield return Result(win);
    }

    // 6개 중 2개는 플레이어 몫, 2개는 게임이 몰래 바꾸고, 나머지 2개는 유지
    List<Role> DrawRound(int from, int to)
    {
        var pool = new List<Role> { Role.Weather, Role.Wheel, Role.Terrain, Role.Trap, Role.Weight, Role.Gravity };
        Shuffle(pool);
        for (int i = 2; i < 4; i++) GameChange(pool[i], from, to);
        var tasks = new List<Role> { Role.Car, Role.Road, pool[0], pool[1] };
        tasks.Sort(); // 자동차 → 길 → 기획서 표 순서
        return tasks;
    }

    void GameChange(Role r, int from, int to)
    {
        if (Env.IsCard(r)) Env.Randomize(r);
        else if (r == Role.Terrain) {
            for (int s = from; s < to; s++) track.SetSurface(s, (Surface)Random.Range(0, 3));
        }
        else {
            track.ClearTraps(from, to);
            track.PlaceRandomTraps(Env.Cfg("Trap.Count", 2), from, to);
        }
    }

    // 작업마다 담당 플레이어 번호. 인원이 적으면 돌아가며 여러 개, 많으면 남는 사람은 쉰다
    List<int> Assign(int taskCount)
    {
        var order = new List<int>();
        for (int i = 0; i < players; i++) order.Add(i);
        Shuffle(order);
        var owners = new List<int>();
        for (int i = 0; i < taskCount; i++) owners.Add(order[i % players]);
        return owners;
    }

    IEnumerator Turn(int round, Role role, int owner, int from, int to)
    {
        Hud.Info("");
        Hud.Panel($"{round}회차\n\n플레이어 {owner + 1}님 차례입니다\n담당: {Env.RoleNames[(int)role]}\n\n다른 사람은 화면을 보지 마세요", true, "확인");
        yield return new WaitUntil(() => Hud.Picked >= 0);
        Hud.HidePanel();

        switch (role) {
            case Role.Car: yield return RecordCar(); break;
            case Role.Road: yield return DrawRoad(from, to); break;
            case Role.Terrain: yield return EditTerrain(from, to); break;
            case Role.Trap: yield return PlaceTraps(from, to); break;
            default: yield return PickCard(role); break;
        }
        Hud.Info("");
    }

    // 자동차: 빈 평지에서 기본 환경으로 녹화. 게임이 바꾼 요소를 느끼지 못하게 한다
    IEnumerator RecordCar()
    {
        car.Configure(Wheel.Round, 1f, 1f, 0f);
        Physics2D.gravity = baseGravity;
        car.Teleport(Track.RecordStart + Vector2.up);
        follow = true;
        cam.orthographicSize = 6f;

        for (int n = 3; n > 0; n--) {
            Hud.Info($"자동차: ←→ 가속/후진, ↑↓ 기울기\n{n}초 뒤 녹화를 시작합니다");
            yield return new WaitForSeconds(1f);
        }
        car.Record();
        yield return Timed(Env.Cfg("Time.Record", 10f), () => "녹화 중  ←→ 가속/후진, ↑↓ 기울기", canSkip: false);
        car.Freeze();
        follow = false;
        car.Teleport(roundStart);
    }

    IEnumerator DrawRoad(int from, int to)
    {
        View(surfaces: false, roads: true, traps: false);
        Focus(from * Track.SegW, to * Track.SegW);
        road.Begin(from, to);
        yield return Timed(TaskTime, () => $"길: 마우스로 드래그해 길을 그리세요. 결승선은 → 방향입니다\n남은 잉크 {road.InkLeft:0.0}");
        road.End();
    }

    IEnumerator EditTerrain(int from, int to)
    {
        View(surfaces: true, roads: false, traps: false);
        Focus(from * Track.SegW, to * Track.SegW);
        yield return Timed(TaskTime, () => {
            var names = new List<string>();
            for (int s = from; s < to; s++) names.Add($"구간{s - from + 1} {Env.SurfaceNames[(int)track.SurfaceOf(s)]}");
            return "지형: 구간을 클릭해 재질을 바꾸세요 (일반 → 진흙 → 얼음)\n" + string.Join("   ", names);
        }, tick: () => {
            if (!Clicked(out var p)) return;
            int s = Track.SegAt(p.x);
            if (s >= from && s < to) track.SetSurface(s, (Surface)(((int)track.SurfaceOf(s) + 1) % 3));
        });
    }

    IEnumerator PlaceTraps(int from, int to)
    {
        View(surfaces: false, roads: false, traps: true);
        Focus(from * Track.SegW, to * Track.SegW);
        track.ClearTraps(from, to);
        int need = Env.Cfg("Trap.Count", 2), placed = 0;
        yield return Timed(TaskTime, () => $"함정: 차가 지나가지 않을 곳을 클릭하세요. 남은 함정 {need - placed}개",
            tick: () => {
                if (placed < need && Clicked(out var p) && p.x >= from * Track.SegW && p.x < to * Track.SegW && track.PlaceTrap(p.x)) placed++;
            },
            canFinish: () => placed >= need);
        if (placed < need) track.PlaceRandomTraps(need - placed, from, to); // 시간 초과 시 남은 개수는 무작위
    }

    // 카드 2장 중 택 1. 시간 초과면 첫 장
    IEnumerator PickCard(Role role)
    {
        var two = Env.DrawTwo(role);
        var names = Env.Cards(role);
        string title = $"{Env.RoleNames[(int)role]}: 하나를 고르세요";
        Hud.Panel(title, true, names[two[0]], names[two[1]]);
        for (float t = TaskTime; t > 0 && Hud.Picked < 0; t -= Time.deltaTime) {
            Hud.PanelText($"{title}\n\n남은 시간 {Mathf.CeilToInt(t)}초");
            yield return null;
        }
        Env.Set(role, two[Mathf.Max(0, Hud.Picked)]);
        Hud.HidePanel();
    }

    IEnumerator Playback(Action<bool> onWin)
    {
        Hud.Panel("모두 모여 화면을 보세요", true, "재생");
        yield return new WaitUntil(() => Hud.Picked >= 0);
        Hud.HidePanel();

        View(surfaces: true, roads: true, traps: true);
        car.Configure(Env.Wheel, Env.WeightMul, Env.Weather == Weather.Rain ? Env.Cfg("Weather.RainFriction", 0.3f) : 1f, Env.Wind);
        Physics2D.gravity = baseGravity * Env.GravityMul;
        car.Teleport(roundStart);
        car.Play();
        follow = true;
        cam.orthographicSize = 6f;

        float limit = car.TapeSeconds + Env.Cfg("Time.PlayExtra", 8f);
        bool fell = false;
        for (float t = 0; ; t += Time.deltaTime) {
            Hud.Info($"재생 중  결승까지 {Mathf.Max(0f, Track.FinishX - car.Position.x):0}m");
            if (car.Position.x >= Track.FinishX) { onWin(true); lastResult = "결승선 통과"; break; }
            if (car.Position.y < Track.FallY) { fell = true; lastResult = "추락해서 회차 시작 위치로 돌아갑니다"; break; }
            if (car.FlipTime > 0.5f) { lastResult = "뒤집혀서 그 자리에 세웁니다"; break; }
            if (car.TapeDone && car.StillTime > 1f) { lastResult = "멈췄습니다"; break; }
            if (t > limit) { lastResult = "시간이 끝났습니다"; break; }
            yield return null;
        }

        car.Freeze();
        follow = false;
        Physics2D.gravity = baseGravity;
        if (fell) car.Teleport(roundStart);
        else {
            if (car.FlipTime > 0.5f) car.Upright();
            roundStart = car.Position + Vector2.up * 0.3f;
            // 구덩이 위 길에서 멈추면 다음 회차 길 담당이 그 길을 지울 수 있으므로 구덩이 앞 땅으로 옮긴다
            while (float.IsNaN(Track.Height(roundStart.x))) roundStart.x -= 0.25f;
            roundStart.y = Mathf.Max(roundStart.y, Track.Height(roundStart.x) + 1f);
        }
        Sfx.Play(fell ? "Fall" : "RoundEnd");
    }

    // 현황 공개. 이때만 대화할 수 있다
    IEnumerator Reveal(int round, int rounds)
    {
        View(surfaces: true, roads: true, traps: true);
        Focus(0f, Track.Length);
        yield return Timed(Env.Cfg("Time.Reveal", 15f), () =>
            $"현황 공개 ({round}/{rounds}회차 끝)  지금만 대화할 수 있습니다\n" +
            $"{lastResult}  결승까지 {Mathf.Max(0f, Track.FinishX - car.Position.x):0}m\n" +
            $"날씨 {Env.ValueName(Role.Weather)}  바퀴 {Env.ValueName(Role.Wheel)}  무게 {Env.ValueName(Role.Weight)}  중력 {Env.ValueName(Role.Gravity)}");
    }

    IEnumerator Result(bool win)
    {
        Sfx.Play(win ? "Win" : "Lose");
        Hud.Info("");
        Hud.Panel(win ? "결승선 통과!\n전원 승리" : "회차를 모두 썼습니다\n전원 패배", false, "다시 하기");
        yield return new WaitUntil(() => Hud.Picked >= 0);
        Hud.HidePanel();
    }

    // seconds 동안 매 프레임 tick을 돌리고 안내 문구를 갱신한다. 완료 버튼으로 일찍 끝낼 수 있다
    IEnumerator Timed(float seconds, Func<string> text, Action tick = null, Func<bool> canFinish = null, bool canSkip = true)
    {
        bool done = false;
        Hud.Done(canSkip ? (Action)(() => done = canFinish == null || canFinish()) : null);
        for (float t = seconds; t > 0 && !done; t -= Time.deltaTime) {
            tick?.Invoke();
            Hud.Info($"{text()}\n남은 시간 {Mathf.CeilToInt(t)}초");
            yield return null;
        }
        Hud.Done(null);
    }

    void View(bool surfaces, bool roads, bool traps)
    {
        track.ShowSurfaces(surfaces);
        road.SetVisible(roads);
        track.ShowTraps(traps);
    }

    // x0~x1이 화면 가로에 꽉 차게
    void Focus(float x0, float x1)
    {
        cam.orthographicSize = Mathf.Max(5f, (x1 - x0) / 2f / cam.aspect + 0.5f);
        cam.transform.position = new Vector3((x0 + x1) / 2f, 1.5f, -10f);
    }

    bool Clicked(out Vector2 world)
    {
        world = default;
        var mouse = Mouse.current;
        if (mouse == null || !mouse.leftButton.wasPressedThisFrame || Hud.PointerOverUi) return false;
        world = cam.ScreenToWorldPoint(mouse.position.ReadValue());
        return true;
    }

    static void Shuffle<T>(IList<T> list)
    {
        for (int i = list.Count - 1; i > 0; i--) {
            int j = Random.Range(0, i + 1);
            (list[i], list[j]) = (list[j], list[i]);
        }
    }
}
