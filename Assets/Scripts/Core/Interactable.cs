using System;
using System.Collections.Generic;
using System.Text;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.InputSystem;

// 바라보는 물체의 프롬프트. 기준점은 이 오브젝트의 위치. 키별로 시선에 가장 맞는 하나만 잡는다
public class Interactable : MonoBehaviour
{
    public string label;
    public string key = "E";
    public float radius = 2f;
    public float cone = 0.82f;
    public bool active = true;
    public UnityEvent onUse = new();

    static readonly List<Interactable> all = new();
    static readonly List<(Interactable it, float score)> hits = new();
    static readonly List<Interactable> current = new();
    static readonly StringBuilder text = new();

    void OnEnable() => all.Add(this);
    void OnDisable() => all.Remove(this);

    /// <summary>켜진 것 중 가장 가까운 자리. 시선을 줄 곳이 없을 때 쓴다.</summary>
    public static Vector3? Nearest(Vector3 from, float within)
    {
        Vector3? best = null;
        float dist = within * within;
        foreach (var it in all)
        {
            if (!it.active) continue;
            float d = (it.transform.position - from).sqrMagnitude;
            if (d < dist) { dist = d; best = it.transform.position; }
        }
        return best;
    }

    // PlayerController가 FPS 모드에서 매 프레임 부른다
    public static void Tick(Vector3 eye, Vector3 forward)
    {
        hits.Clear();
        foreach (var it in all)
        {
            if (!it.active) continue;
            Vector3 d = it.transform.position - eye;
            float dist = d.magnitude;
            if (dist > it.radius) continue;
            float dot = dist > 1e-4f ? Vector3.Dot(d / dist, forward) : 1f;
            if (dot > it.cone) hits.Add((it, dot - dist * 0.05f));
        }
        hits.Sort((a, b) => b.score.CompareTo(a.score));

        current.Clear();
        text.Clear();
        foreach (var (it, _) in hits)
        {
            if (current.Exists(c => c.key == it.key)) continue;
            current.Add(it);
            if (text.Length > 0) text.Append("     ");
            text.Append("<b>").Append(it.key).Append("</b> ").Append(it.label);
        }
        if (Hud.I != null) Hud.I.Prompt(text.Length > 0 ? text.ToString() : null);

        var kb = Keyboard.current;
        var mouse = Mouse.current;
        foreach (var it in current)
        {
            bool pressed = kb != null && Enum.TryParse(it.key, true, out Key k) && kb[k].wasPressedThisFrame;
            if (it.key == "E" && mouse != null && mouse.leftButton.wasPressedThisFrame) pressed = true;
            if (pressed) { it.onUse.Invoke(); break; }
        }
    }

    public static void Clear()
    {
        current.Clear();
        if (Hud.I != null) Hud.I.Prompt(null);
    }
}
