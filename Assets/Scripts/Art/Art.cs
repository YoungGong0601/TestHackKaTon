using System.Collections.Generic;
using UnityEngine;

// 아트 교체 지점. Resources/Art/<이름> 스프라이트가 있으면 쓰고, 없으면 단색 도형을 만든다
// 아트 담당은 코드 수정 없이 docs/ArtList.md의 이름대로 파일만 넣으면 된다
public static class Art
{
    static readonly Dictionary<string, Sprite> cache = new();
    static Sprite square, circle;
    static Font font;
    static Material lineMaterial;

    public static Sprite Get(string name, bool round = false)
    {
        var sprite = Load(name);
        return sprite != null ? sprite : round ? Circle : Square;
    }

    public static bool Has(string name) => Load(name) != null;

    // 없는 파일도 null로 캐시해서 매번 다시 찾지 않는다
    static Sprite Load(string name)
    {
        if (!cache.TryGetValue(name, out var sprite)) cache[name] = sprite = Resources.Load<Sprite>("Art/" + name);
        return sprite;
    }

    // parent 아래에 size 크기로 맞춘 그림을 붙인다. 진짜 아트가 있으면 color는 무시한다
    public static SpriteRenderer Visual(Transform parent, string name, Vector2 size, Color color, bool round = false, int order = 0)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = Get(name, round);
        sr.color = Has(name) ? Color.white : color;
        sr.sortingOrder = order;
        Vector2 b = sr.sprite.bounds.size;
        go.transform.localScale = new Vector3(size.x / b.x, size.y / b.y, 1);
        return sr;
    }

    public static Sprite Square => square != null ? square : square = Make(false);
    public static Sprite Circle => circle != null ? circle : circle = Make(true);

    // 1유닛 크기 흰 도형
    static Sprite Make(bool round)
    {
        const int n = 64;
        var tex = new Texture2D(n, n) { filterMode = FilterMode.Bilinear };
        var px = new Color[n * n];
        for (int y = 0; y < n; y++)
            for (int x = 0; x < n; x++) {
                float dx = x - n / 2f + 0.5f, dy = y - n / 2f + 0.5f;
                px[y * n + x] = !round || dx * dx + dy * dy <= n * n / 4f ? Color.white : Color.clear;
            }
        tex.SetPixels(px);
        tex.Apply();
        return Sprite.Create(tex, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), n);
    }

    public static Font Font => font != null ? font
        : font = Font.CreateDynamicFontFromOSFont(new[] { "Malgun Gothic", "Apple SD Gothic Neo", "AppleGothic", "Arial" }, 32);

    // 길, 지형 선용
    public static LineRenderer Line(GameObject go, Color color, float width, int order = 0)
    {
        if (lineMaterial == null) lineMaterial = new Material(Shader.Find("Sprites/Default"));
        var lr = go.AddComponent<LineRenderer>();
        lr.sharedMaterial = lineMaterial;
        lr.startColor = lr.endColor = color;
        lr.startWidth = lr.endWidth = width;
        lr.numCapVertices = 2;
        lr.numCornerVertices = 2;
        lr.sortingOrder = order;
        lr.useWorldSpace = true;
        return lr;
    }
}

// 소리 교체 지점. Resources/Sfx/<이름>이 없으면 무음
public static class Sfx
{
    static AudioSource source;

    public static void Play(string name)
    {
        var clip = Resources.Load<AudioClip>("Sfx/" + name);
        if (clip == null) return;
        if (source == null) source = new GameObject("Sfx").AddComponent<AudioSource>();
        source.PlayOneShot(clip);
    }
}
