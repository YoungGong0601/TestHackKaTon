using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;

// 길 담당: 마우스 드래그로 길을 그린다. 잉크(총 길이)가 떨어지면 더 못 그린다
public class RoadPainter : MonoBehaviour
{
    public float InkLeft { get; private set; }

    readonly List<(int seg, GameObject go)> roads = new();
    PhysicsMaterial2D material;
    List<Vector2> points;
    LineRenderer line;
    EdgeCollider2D edge;
    float minX, maxX;
    bool active;

    static readonly Color color = new(0.45f, 0.3f, 0.2f);

    void Awake()
    {
        material = new PhysicsMaterial2D("Road") {
            friction = Env.Cfg("Road.Friction", 0.8f), bounciness = 0f, frictionCombine = PhysicsMaterialCombine2D.Minimum,
        };
    }

    // 설정 범위 안의 이전 길은 지우고 새로 그린다
    public void Begin(int from, int to)
    {
        Clear(from, to);
        InkLeft = Env.Cfg("Road.Ink", 12f);
        minX = from * Track.SegW;
        maxX = to * Track.SegW;
        active = true;
    }

    public void End()
    {
        active = false;
        line = null;
    }

    public void Clear(int from, int to)
    {
        roads.RemoveAll(r => {
            if (r.seg < from || r.seg >= to) return false;
            Destroy(r.go);
            return true;
        });
    }

    public void SetVisible(bool show)
    {
        foreach (var r in roads) r.go.SetActive(show);
    }

    void Update()
    {
        var mouse = Mouse.current;
        if (!active || mouse == null) return;

        if (mouse.leftButton.wasPressedThisFrame && !Hud.PointerOverUi) StartStroke(MouseWorld(mouse));
        else if (mouse.leftButton.isPressed && line != null) Extend(MouseWorld(mouse));
        if (mouse.leftButton.wasReleasedThisFrame) line = null;
    }

    Vector2 MouseWorld(Mouse mouse)
    {
        Vector2 p = Camera.main.ScreenToWorldPoint(mouse.position.ReadValue());
        p.x = Mathf.Clamp(p.x, minX, maxX);
        return p;
    }

    void StartStroke(Vector2 p)
    {
        if (InkLeft <= 0f) return;
        var go = new GameObject("Road");
        go.transform.SetParent(transform);
        roads.Add((Track.SegAt(p.x), go));
        points = new List<Vector2> { p };
        line = Art.Line(go, color, 0.2f, 3);
        edge = null;
        Refresh();
    }

    void Extend(Vector2 p)
    {
        var last = points[^1];
        float d = Vector2.Distance(last, p);
        if (d < 0.15f) return;
        if (d > InkLeft) {
            p = Vector2.MoveTowards(last, p, InkLeft);
            d = InkLeft;
        }
        points.Add(p);
        InkLeft -= d;
        Refresh();
        if (InkLeft <= 0.01f) line = null;
    }

    void Refresh()
    {
        line.positionCount = points.Count;
        for (int i = 0; i < points.Count; i++) line.SetPosition(i, points[i]);
        if (points.Count < 2) return;
        // 점이 2개 이상일 때만 충돌선을 붙인다 (기본 충돌선이 원점에 생기는 것 방지)
        if (edge == null) {
            edge = line.gameObject.AddComponent<EdgeCollider2D>();
            edge.edgeRadius = 0.1f;
            edge.sharedMaterial = material;
        }
        edge.SetPoints(points);
    }
}
