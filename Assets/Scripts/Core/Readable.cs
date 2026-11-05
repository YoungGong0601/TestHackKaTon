using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Events;

// 돋보기 원 안에서만 또렷한 글. 시야 번짐을 쓰지 않는 인물에게는 늘 또렷하다
// 번진 쪽은 레이어 LensBlurred(본 카메라만), 또렷한 쪽은 LensSharp(돋보기 카메라만)로 시작 때 옮긴다. 원은 후처리 합성이 그린다
// 배치: area = 조준용 Collider, blurred = 번진 글 오브젝트, sharp = 또렷한 글 오브젝트
public class Readable : MonoBehaviour
{
    public GameObject blurred;
    public GameObject sharp;
    public bool wide;      // 넓은 판. 한 줄이 읽히게 돋보기 배율을 낮춘다
    public bool postBlur;  // 글이 SignBlur 레이어에 있어 후처리가 번지게 한다. 판독 판정만 쓰고 층은 옮기지 않는다
    public UnityEvent onRead = new();

    [SerializeField] Collider area;

    static readonly List<Readable> all = new();
    bool aimed;
    bool? plainNow;

    /// <summary>지금 읽을 수 있는 상태인가. 돋보기 원이 글에 닿았거나 시야 번짐이 없는 인물이 보는 중.</summary>
    public bool Seen => aimed || Plain;

    static bool Plain
    {
        get
        {
            var profile = GameState.I != null ? GameState.I.Profile : null;
            return profile != null && !profile.visionBlur;
        }
    }

    void OnEnable() { all.Add(this); plainNow = null; Refresh(); }
    void OnDisable() { all.Remove(this); aimed = false; }

    // HTML판처럼 다른 물체에 가려도 글 면만 본다. 원 가운데를 먼저 보고 없으면 rim을 본다. 맞은 글을 돌려준다
    public static Readable Aim(Ray ray, bool lensOn, Ray[] rim = null)
    {
        Readable best = null;
        float bestDist = float.MaxValue;
        var profile = GameState.I != null ? GameState.I.Profile : null;
        if (lensOn || (profile != null && !profile.visionBlur))   // 시야 번짐이 없는 인물은 보는 것만으로 읽는다
        {
            Nearest(ray, ref best, ref bestDist);
            if (best == null && lensOn && rim != null)
                foreach (var r in rim) Nearest(r, ref best, ref bestDist);
        }
        for (int i = all.Count - 1; i >= 0; i--) all[i].SetAimed(all[i] == best);
        return best;
    }

    static void Nearest(Ray ray, ref Readable best, ref float bestDist)
    {
        foreach (var r in all)
            if (r.area != null && r.area.Raycast(ray, out var hit, 1000f) && hit.distance < bestDist)
            {
                best = r;
                bestDist = hit.distance;
            }
    }

    void SetAimed(bool on)
    {
        Refresh();
        if (on == aimed) return;
        aimed = on;
        if (on) onRead.Invoke();
    }

    // 인물이 바뀌면 다시 나눈다. 씬 시작 뒤에 프로필이 정해지므로 조준 판정 때마다 본다
    void Refresh()
    {
        bool plain = Plain;
        if (plainNow == plain) return;
        plainNow = plain;
        if (postBlur)
        {
            if (blurred != null) blurred.SetActive(false);
            return;
        }
        if (sharp != null)
        {
            sharp.SetActive(true);
            SetLayer(sharp.transform, plain ? 0 : LayerMask.NameToLayer("LensSharp"));
        }
        if (blurred != null)
        {
            blurred.SetActive(!plain);
            SetLayer(blurred.transform, LayerMask.NameToLayer("LensBlurred"));
        }
    }

    static void SetLayer(Transform t, int layer)
    {
        t.gameObject.layer = layer;
        foreach (Transform c in t) SetLayer(c, layer);
    }
}
