using System;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

// 코드로 만드는 UI. 상단 안내 문구, 가운데 패널(문구 + 버튼), 오른쪽 아래 완료 버튼
// 패널, 버튼 배경은 Art.Get("Panel"), Art.Get("Button")을 쓰므로 아트 파일만 넣으면 바뀐다
public static class Hud
{
    public static int Picked { get; private set; } = -1; // 패널에서 누른 버튼 번호, 누르기 전 -1
    public static bool PointerOverUi => EventSystem.current != null && EventSystem.current.IsPointerOverGameObject();

    static Text info, panelText;
    static Image panel;
    static RectTransform buttonRow;
    static GameObject doneButton;
    static Action onDone;

    public static void Init()
    {
        var es = new GameObject("EventSystem", typeof(EventSystem));
        es.AddComponent<InputSystemUIInputModule>().AssignDefaultActions();

        var root = new GameObject("Hud");
        var canvas = root.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        var scaler = root.AddComponent<CanvasScaler>();
        scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        scaler.referenceResolution = new Vector2(1920, 1080);
        scaler.matchWidthOrHeight = 0.5f;
        root.AddComponent<GraphicRaycaster>();

        info = MakeText(root.transform, 36, TextAnchor.UpperLeft);
        Place(info.rectTransform, Vector2.zero, Vector2.one, new Vector2(40, 30), new Vector2(-40, -30));

        panel = MakeImage(root.transform, "Panel", new Color(0.08f, 0.1f, 0.14f));
        Place(panel.rectTransform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
        panelText = MakeText(panel.transform, 56, TextAnchor.MiddleCenter);
        Place(panelText.rectTransform, new Vector2(0, 0.35f), Vector2.one, new Vector2(80, 0), new Vector2(-80, -60));

        buttonRow = new GameObject("Buttons", typeof(RectTransform)).GetComponent<RectTransform>();
        buttonRow.SetParent(panel.transform, false);
        Place(buttonRow, Vector2.zero, new Vector2(1, 0.35f), new Vector2(0, 60), Vector2.zero);
        var layout = buttonRow.gameObject.AddComponent<HorizontalLayoutGroup>();
        layout.spacing = 40;
        layout.childAlignment = TextAnchor.MiddleCenter;
        layout.childControlWidth = layout.childControlHeight = false;
        layout.childForceExpandWidth = layout.childForceExpandHeight = false;

        doneButton = MakeButton(root.transform, "완료", () => onDone?.Invoke());
        var rt = doneButton.GetComponent<RectTransform>();
        rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(1, 0);
        rt.anchoredPosition = new Vector2(-40, 40);

        HidePanel();
        Done(null);
    }

    public static void Info(string text) => info.text = text;

    // opaque면 화면을 완전히 가린다 (차례 전환, 블라인드용)
    public static void Panel(string text, bool opaque, params string[] buttons)
    {
        Picked = -1;
        panelText.text = text;
        var c = panel.color;
        c.a = opaque ? 1f : 0.6f;
        panel.color = c;
        foreach (Transform child in buttonRow) UnityEngine.Object.Destroy(child.gameObject);
        for (int i = 0; i < buttons.Length; i++) {
            int index = i;
            MakeButton(buttonRow, buttons[i], () => Picked = index);
        }
        panel.gameObject.SetActive(true);
    }

    public static void PanelText(string text) => panelText.text = text;

    public static void HidePanel() => panel.gameObject.SetActive(false);

    // 완료 버튼. null이면 숨긴다
    public static void Done(Action action)
    {
        onDone = action;
        doneButton.SetActive(action != null);
    }

    static Text MakeText(Transform parent, int size, TextAnchor anchor)
    {
        var go = new GameObject("Text", typeof(RectTransform));
        go.transform.SetParent(parent, false);
        var t = go.AddComponent<Text>();
        t.font = Art.Font;
        t.fontSize = size;
        t.alignment = anchor;
        t.color = Color.white;
        t.horizontalOverflow = HorizontalWrapMode.Wrap;
        t.verticalOverflow = VerticalWrapMode.Overflow;
        t.raycastTarget = false;
        go.AddComponent<Outline>().effectColor = Color.black;
        return t;
    }

    static Image MakeImage(Transform parent, string art, Color placeholder)
    {
        var go = new GameObject(art, typeof(RectTransform));
        go.transform.SetParent(parent, false);
        var img = go.AddComponent<Image>();
        img.sprite = Art.Get(art);
        img.color = Art.Has(art) ? Color.white : placeholder;
        return img;
    }

    static GameObject MakeButton(Transform parent, string label, Action onClick)
    {
        var img = MakeImage(parent, "Button", new Color(0.25f, 0.45f, 0.8f));
        img.rectTransform.sizeDelta = new Vector2(380, 140);
        img.gameObject.AddComponent<Button>().onClick.AddListener(() => onClick());
        var t = MakeText(img.transform, 44, TextAnchor.MiddleCenter);
        t.text = label;
        Place(t.rectTransform, Vector2.zero, Vector2.one, Vector2.zero, Vector2.zero);
        return img.gameObject;
    }

    static void Place(RectTransform rt, Vector2 anchorMin, Vector2 anchorMax, Vector2 offsetMin, Vector2 offsetMax)
    {
        rt.anchorMin = anchorMin;
        rt.anchorMax = anchorMax;
        rt.offsetMin = offsetMin;
        rt.offsetMax = offsetMax;
    }
}
