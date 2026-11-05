using System.Linq;
using TMPro;
using UnityEditor;
using UnityEngine;
using UnityEngine.UI;

// 키오스크 화면을 게임 색으로 입힌다. 앞쪽 화면은 회색이고 뒤쪽(장바구니, 결제)만 색이 있어서 뒤쪽 색으로 맞춘다.
// 음식 칸은 KioskPresenter 가 실행 중에 채우고, 여기서는 고정된 자리만 넣는다.
static class JWKiosk
{
    const string Dir = "Assets/JeongWoo/UI/Kiosk/Screen_";
    const string Food = "Assets/JeongWoo/Resources/JW/Food/";

    // 회색 값 → 색. 가장 가까운 회색을 찾는다
    static readonly (int gray, string color)[] Text =
    {
        (0x14, "#2a1a10"), (0x33, "#2a1a10"), (0x40, "#2a1a10"), (0x5c, "#6b4a30"), (0x8c, "#8d7a64"), (0xad, "#b3a288"), (0xcc, "#ffd9c8"), (0xe6, "#fffdf8"), (0xfa, "#fffdf8"),
    };
    static readonly (int gray, string color)[] Image =
    {
        (0x38, "#3a2416"), (0x3d, "#c8291f"), (0x47, "#a32019"), (0x4c, "#c8291f"), (0x57, "#6b4a30"), (0x5c, "#cb4139"), (0x6b, "#a32019"), (0x80, "#c8291f"), (0x85, "#ad251e"),
        (0x9e, "#f0c63a"), (0xa8, "#f0c63a"), (0xcc, "#faefdd"), (0xd9, "#fff0da"), (0xdb, "#f4e6cb"), (0xe6, "#fff0da"), (0xed, "#fff6e6"), (0xfa, "#fffdf8"),
    };

    static Color Warm((int gray, string color)[] table, float gray, float alpha)
    {
        int g = Mathf.RoundToInt(gray * 255f);
        var best = table.OrderBy(t => Mathf.Abs(t.gray - g)).First();
        ColorUtility.TryParseHtmlString(best.color, out var c);
        c.a = alpha;
        return c;
    }

    static void Recolor(GameObject root)
    {
        foreach (var g in root.GetComponentsInChildren<Graphic>(true))
        {
            var c = g.color;
            if (c.a <= 0f || Mathf.Abs(c.r - c.g) > 0.004f || Mathf.Abs(c.g - c.b) > 0.004f) continue;
            if (c.r > 0.99f) continue;   // 음식 그림 자리는 흰색이다
            g.color = Warm(g is TMP_Text || g is UnityEngine.UI.Text ? Text : Image, c.r, c.a);
        }
    }

    static void Picture(Transform root, string path, string file)
    {
        var t = root.Find(path);
        if (t == null) { JWBuild.Warn($"{root.name} 에 {path} 없음"); return; }
        var image = t.GetComponent<Image>();
        image.sprite = AssetDatabase.LoadAllAssetsAtPath(Food + file).OfType<Sprite>().First();
        image.color = Color.white;
        image.preserveAspect = true;
    }

    static void Edit(string screen, System.Action<GameObject> change)
    {
        var path = Dir + screen + ".prefab";
        var root = PrefabUtility.LoadPrefabContents(path);
        try
        {
            change(root);
            PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally { PrefabUtility.UnloadPrefabContents(root); }
    }

    static void Logo(GameObject root)
    {
        foreach (var t in root.GetComponentsInChildren<Transform>(true))
        {
            if (!t.TryGetComponent(out Image image)) continue;
            if (t.name == "Btn_lang0") image.color = new Color32(0xad, 0x25, 0x1e, 255);   // 고른 언어. 글자가 흰색이다
            if (t.name is "Logo" or "Crown") Picture(t.parent, t.name, "logo.png");
            if (t.name is "QR" or "ArtIn" or "QrIn") Picture(t.parent, t.name, "qr.png");
            if (t.name.StartsWith("Thumb")) Picture(t.parent, t.name, "burger_bulgogi.png");
        }
    }

    public static void All()
    {
        foreach (var s in new[] { "idle", "place", "member", "menu", "option", "side", "drink" }) Edit(s, Recolor);
        foreach (var s in new[] { "place", "member", "menu", "option", "side", "drink", "cart", "pay", "card", "paying", "cardout", "done" }) Edit(s, Logo);

        Edit("idle", root =>
        {
            // 대기 화면은 완성된 포스터 한 장이다. 뜻 풀이(Reveal)만 그 위에 남긴다
            var old = root.transform.Find("Attract");
            if (old != null) Object.DestroyImmediate(old.gameObject);
            var go = new GameObject("Attract", typeof(RectTransform), typeof(CanvasRenderer), typeof(RawImage)) { layer = root.layer };
            go.transform.SetParent(root.transform, false);
            var rect = (RectTransform)go.transform;
            rect.anchorMin = Vector2.zero;
            rect.anchorMax = Vector2.one;
            rect.offsetMin = rect.offsetMax = Vector2.zero;
            var raw = go.GetComponent<RawImage>();
            raw.texture = AssetDatabase.LoadAssetAtPath<Texture>("Assets/Art3D/Textures/Kiosk/T_Kiosk_Screen_Attract.png");
            raw.raycastTarget = false;
            var reveal = root.transform.Find("Reveal");
            if (reveal != null) go.transform.SetSiblingIndex(reveal.GetSiblingIndex());
        });
        Edit("place", root =>
        {
            Picture(root.transform, "Btn_dine/Img", "burger_double.png");
            Picture(root.transform, "Btn_takeout/Img", "burger_cheese.png");
            Picture(root.transform, "Btn_promo/Img", "softcone.png");
            Picture(root.transform, "Img", "cola.png");
        });
        Edit("menu", root =>
        {
            Picture(root.transform, "Btn_hero/Img", "burger_bulgogi.png");
            Picture(root.transform, "Ad/Btn_ad/Img", "burger_double.png");
        });
        Edit("upsell", root => Picture(root.transform, "Art", "fries.jpg"));
        Edit("cart", root =>
        {
            Picture(root.transform, "Btn_promo/Art", "burger_double.png");
            Picture(root.transform, "Btn_rec0/Art", "fries.jpg");
            Picture(root.transform, "Btn_rec1/Art", "nuggets.png");
            Picture(root.transform, "Btn_rec2/Art", "cola.png");
            Picture(root.transform, "Btn_rec3/Art", "softcone.png");
        });
        Edit("paying", root => Picture(root.transform, "Panel/Art", "burger_cheese.png"));

        // 안내 창과 타이머는 화면 프리팹이 아니라 PH_Kiosk 안에 있다
        const string kiosk = "Assets/JeongWoo/Graybox/PH/PH_Kiosk.prefab";
        var body = PrefabUtility.LoadPrefabContents(kiosk);
        try
        {
            foreach (var t in body.GetComponentsInChildren<Transform>(true).Where(t => t.name.StartsWith("Overlay_"))) Recolor(t.gameObject);
            foreach (var f in body.GetComponentsInChildren<KioskField>(true).Where(f => f.key == "qr")) Picture(f.transform.parent, f.name, "qr.png");
            PrefabUtility.SaveAsPrefabAsset(body, kiosk);
        }
        finally { PrefabUtility.UnloadPrefabContents(body); }
    }
}
