using System.Collections.Generic;
using UnityEngine;

// 3화면 길이 고정 지형 1종. 화면 하나를 구간 3개로 나눠 구간마다 재질을 갖는다
// 함정도 여기서 관리한다. 녹화용 빈 평지는 멀리 아래쪽에 따로 둔다
public class Track : MonoBehaviour
{
    // ponytail: 화면 폭과 지형이 상수. 맵 무작위 생성을 하게 되면 Height를 데이터로 바꾼다
    public const float ScreenW = 18f, SegW = ScreenW / 3f, Length = ScreenW * 3f;
    public const int SegCount = 9;
    public const float StartX = 2f, FinishX = Length - 2f, FallY = -6f;
    public static readonly Vector2 RecordStart = new(0f, -200f);

    public static PhysicsMaterial2D[] Materials;

    static readonly Color hidden = new(0.6f, 0.6f, 0.6f);
    static readonly Color[] surfaceColors = { new(0.35f, 0.75f, 0.35f), new(0.5f, 0.32f, 0.15f), new(0.6f, 0.9f, 1f) };

    readonly Surface[] surfaces = new Surface[SegCount];
    readonly List<EdgeCollider2D>[] colliders = new List<EdgeCollider2D>[SegCount];
    readonly List<LineRenderer>[] lines = new List<LineRenderer>[SegCount];
    readonly List<(int seg, GameObject go)> traps = new();
    bool showSurfaces = true;

    // 지형 높이. 구덩이는 NaN
    public static float Height(float x)
    {
        if ((x > 19f && x < 22f) || (x > 38f && x < 41f)) return float.NaN;
        // 최대 경사 = 높이 * π / (2 * 반폭). 0.7 안쪽으로 둬야 길 없이도 오를 수 있다
        return 1.5f * Bump(x, 13f, 4f) + 0.6f * Bump(x, 25.5f, 1.5f) + 2f * Bump(x, 33f, 4.5f) + 1.2f * Bump(x, 47f, 4f);
    }

    static float Bump(float x, float center, float halfWidth)
    {
        float d = Mathf.Abs(x - center);
        return d < halfWidth ? 0.5f * (1f + Mathf.Cos(Mathf.PI * d / halfWidth)) : 0f;
    }

    public static int SegAt(float x) => Mathf.Clamp(Mathf.FloorToInt(x / SegW), 0, SegCount - 1);

    // 설정 범위: 차가 있는 구간부터 한 화면 (구간 3개). to는 포함하지 않음
    // ponytail: 범위를 고정 구간에 맞춘다. 차 위치 기준 정확한 한 화면이 필요하면 구간을 잘게 나눈다
    public static (int from, int to) Range(float carX)
    {
        int from = SegAt(carX);
        return (from, Mathf.Min(from + 3, SegCount));
    }

    void Awake()
    {
        Materials = new[] {
            Mat("Normal", Env.Cfg("Surface.NormalFriction", 0.8f)),
            Mat("Mud", Env.Cfg("Surface.MudFriction", 0.8f)),
            Mat("Ice", Env.Cfg("Surface.IceFriction", 0.05f)),
        };

        for (int s = 0; s < SegCount; s++) BuildSegment(s);

        Art.Visual(transform, "Finish", new Vector2(0.3f, 6f), Color.yellow, false, 1)
            .transform.position = new Vector3(FinishX, Height(FinishX) + 3f);

        var floor = new GameObject("RecordFloor");
        floor.transform.SetParent(transform);
        var pts = new List<Vector2> { RecordStart + new Vector2(-20f, 0f), RecordStart + new Vector2(600f, 0f) };
        var edge = floor.AddComponent<EdgeCollider2D>();
        edge.SetPoints(pts);
        edge.sharedMaterial = Materials[0];
        var lr = Art.Line(floor, hidden, 0.15f);
        lr.positionCount = 2;
        lr.SetPosition(0, pts[0]);
        lr.SetPosition(1, pts[1]);
    }

    static PhysicsMaterial2D Mat(string name, float friction) =>
        new(name) { friction = friction, bounciness = 0f, frictionCombine = PhysicsMaterialCombine2D.Minimum };

    // 구간을 0.25 간격으로 찍고, 구덩이에서 끊어 조각마다 충돌선과 그림선을 만든다
    void BuildSegment(int s)
    {
        colliders[s] = new List<EdgeCollider2D>();
        lines[s] = new List<LineRenderer>();
        var piece = new List<Vector2>();
        const int steps = 24;
        float x0 = s * SegW;

        for (int k = 0; k <= steps; k++) {
            float x = x0 + k * SegW / steps, y = Height(x);
            if (float.IsNaN(y)) {
                if (piece.Count > 0) {
                    piece.Add(new Vector2(piece[^1].x, -10f)); // 구덩이 벽
                    AddPiece(s, piece);
                    piece = new List<Vector2>();
                }
                continue;
            }
            if (piece.Count == 0) {
                if (k > 0 && float.IsNaN(Height(x - SegW / steps))) piece.Add(new Vector2(x, -10f)); // 구덩이 반대편 벽
                if (x <= 0f) piece.Add(new Vector2(x, 10f)); // 출발점 뒤 벽
            }
            piece.Add(new Vector2(x, y));
        }
        if (s == SegCount - 1) piece.Add(new Vector2(Length, 10f)); // 끝 벽
        if (piece.Count >= 2) AddPiece(s, piece);
    }

    void AddPiece(int s, List<Vector2> pts)
    {
        var go = new GameObject($"Seg{s}");
        go.transform.SetParent(transform);
        var edge = go.AddComponent<EdgeCollider2D>();
        edge.SetPoints(pts);
        edge.sharedMaterial = Materials[0];
        colliders[s].Add(edge);

        var lr = Art.Line(go, surfaceColors[0], 0.15f);
        lr.positionCount = pts.Count;
        for (int i = 0; i < pts.Count; i++) lr.SetPosition(i, pts[i]);
        lines[s].Add(lr);
    }

    public Surface SurfaceOf(int s) => surfaces[s];

    public void SetSurface(int s, Surface surface)
    {
        surfaces[s] = surface;
        foreach (var c in colliders[s]) c.sharedMaterial = Materials[(int)surface];
        Paint(s);
    }

    // 길 담당, 함정 담당은 재질을 보지 못하게 회색으로 그린다
    public void ShowSurfaces(bool show)
    {
        showSurfaces = show;
        for (int s = 0; s < SegCount; s++) Paint(s);
    }

    void Paint(int s)
    {
        var color = showSurfaces ? surfaceColors[(int)surfaces[s]] : hidden;
        foreach (var lr in lines[s]) lr.startColor = lr.endColor = color;
    }

    // 함정은 지형 표면에 붙는다. 구덩이면 실패
    public bool PlaceTrap(float x)
    {
        float y = Height(x);
        if (float.IsNaN(y)) return false;
        traps.Add((SegAt(x), Trap.Create(new Vector2(x, y), transform)));
        return true;
    }

    public void PlaceRandomTraps(int count, int from, int to)
    {
        for (int tries = 0; count > 0 && tries < 100; tries++)
            if (PlaceTrap(Random.Range(from * SegW + 0.5f, to * SegW - 0.5f))) count--;
    }

    public void ClearTraps(int from, int to)
    {
        traps.RemoveAll(t => {
            if (t.go != null && (t.seg < from || t.seg >= to)) return false;
            if (t.go != null) Destroy(t.go);
            return true;
        });
    }

    public void ShowTraps(bool show)
    {
        foreach (var t in traps) if (t.go != null) t.go.SetActive(show);
    }

    public void ResetAll()
    {
        for (int s = 0; s < SegCount; s++) SetSurface(s, Surface.Normal);
        ClearTraps(0, SegCount);
    }
}
