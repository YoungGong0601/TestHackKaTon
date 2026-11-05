// 후처리 검수용 촬영. Screenshots/post-*.png 로 저장한다. 평소 시험에서는 돌지 않는다.
using System.Collections;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

public class PostCapture : KioskBotFixture
{
    static string Dir => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Screenshots"));

    static IEnumerator Shot(string name)
    {
        yield return new WaitForEndOfFrame();
        int w = Screen.width, h = Screen.height;
        var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
        ScreenCapture.CaptureScreenshotIntoRenderTexture(rt);
        var flip = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
        Graphics.Blit(rt, flip, new Vector2(1f, -1f), new Vector2(0f, 1f));
        var prev = RenderTexture.active;
        RenderTexture.active = flip;
        var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
        tex.Apply();
        RenderTexture.active = prev;
        RenderTexture.ReleaseTemporary(rt);
        RenderTexture.ReleaseTemporary(flip);
        Directory.CreateDirectory(Dir);
        File.WriteAllBytes(Path.Combine(Dir, "post-" + name + ".png"), tex.EncodeToPNG());
        Object.Destroy(tex);
    }

    IEnumerator Pin(float v, float sec, Vector2? cursor = null)
    {
        for (float end = Time.realtimeSinceStartup + sec; Time.realtimeSinceStartup < end; )
        {
            bot.SetNunchi(v);
            if (cursor.HasValue) PlayerController.I.SetCursor01(cursor.Value);
            yield return null;
        }
        bot.SetNunchi(v);
    }

    static IEnumerator Face(Vector3 stand, Vector3 look)
    {
        var p = PlayerController.I;
        stand.y = p.transform.position.y;
        Vector3 d = look - stand;
        p.Teleport(stand, Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg);
        yield return null;
        yield return p.LookAt(look, 0.2f);
    }

    static IEnumerator Jump(int chapter, string scene)
    {
        GameState.I.JumpChapter(chapter);
        yield return Until(() => SceneManager.GetActiveScene().name == scene, 30f, scene);
        yield return new WaitForSeconds(1.2f);
        yield return Hud.I.Fade(0f, 0f);
    }

    [UnityTest, Explicit, Timeout(600000)]
    public IEnumerator Capture()
    {
        Vector2 menu = new Vector2(0.56f, 0.5f);

        yield return EnterKiosk();
        yield return PressAll("start", "takeout", "skip", "tab_CLASSIC");
        yield return new WaitForSeconds(0.5f);

        foreach (int v in new[] { 0, 40, 60, 80, 98 })
        {
            yield return Pin(v, 2.2f);
            yield return Shot("kiosk-n" + v);
        }

        // 번짐 수치 측정용: 같은 화면에서 글자 번짐만 끈 것
        var profile = GameState.I.Profile;
        yield return Pin(0f, 2.2f);
        yield return Shot("kiosk-a");
        try
        {
            profile.kioskBlur = false;
            yield return Pin(0f, 0.4f);
            yield return Shot("kiosk-noblur");
        }
        finally { profile.kioskBlur = true; }

        HandRig.I.Equip(ItemId.Lens);
        yield return Pin(0f, 2f, menu);
        yield return Shot("kiosk-lens-n0");
        yield return Pin(98f, 2f, menu);
        yield return Shot("kiosk-lens-n98");
        yield return Pin(98f, 1f, new Vector2(0.56f, 0.13f));
        yield return Shot("kiosk-lens-checkout-n98");
        HandRig.I.Equip(ItemId.None);
        yield return Pin(0f, 0.3f);

        yield return PressAll("item_bulgogi", "opt_combo", "next", "drink_cider", "next", "up_no", "checkout", "pay_card");
        yield return PayWithCard();

        // 픽업과 영수증
        Time.timeScale = 6f;
        yield return Until(() => Object.FindObjectsByType<Interactable>(FindObjectsSortMode.None).Any(i => i.active && i.label == "받기"), 40f, "번호 호출");
        Time.timeScale = 1f;
        var board = Object.FindAnyObjectByType<PickupBoard>();
        Vector3 at = board.transform.position;
        yield return Face(at + board.transform.right * 3f, at);
        yield return new WaitForSeconds(0.6f);
        yield return Shot("receipt");
        HandRig.I.Equip(ItemId.Lens);
        yield return new WaitForSeconds(0.8f);
        yield return Shot("receipt-lens");
        HandRig.I.Equip(ItemId.None);
        yield return Key(UnityEngine.InputSystem.Key.Digit4);
        yield return new WaitForSeconds(0.9f);
        yield return Shot("board");
        HandRig.I.Equip(ItemId.Lens);
        yield return new WaitForSeconds(0.8f);
        yield return Shot("board-lens");
        HandRig.I.Equip(ItemId.None);
        yield return Key(UnityEngine.InputSystem.Key.Digit4);

        // 씬마다 밝기와 번진 글
        yield return Jump(0, "Home");
        yield return new WaitForSeconds(0.6f);
        yield return Shot("scene-home");

        yield return Jump(1, "Street");
        Vector3 bis = GameObject.Find("BisLook").transform.position;
        yield return Face(new Vector3(26.2f, 0f, 33f), bis);
        yield return new WaitForSeconds(0.8f);
        yield return Shot("scene-street");
        try
        {
            GameState.I.Profile.visionBlur = false;
            yield return new WaitForSeconds(0.3f);
            yield return Shot("scene-street-novision");
        }
        finally { GameState.I.Profile.visionBlur = true; }
        yield return new WaitForSeconds(0.3f);
        HandRig.I.Equip(ItemId.Lens);
        yield return new WaitForSeconds(0.8f);
        yield return Shot("scene-street-lens");
        HandRig.I.Equip(ItemId.None);

        yield return Jump(2, "Storefront");
        var sticker = Object.FindObjectsByType<Readable>(FindObjectsSortMode.None).FirstOrDefault(r => r.name == "Sticker_Pull");
        if (sticker != null)
        {
            Vector3 s = sticker.transform.position;
            yield return Face(s - sticker.transform.forward * 1.2f, s);
            yield return new WaitForSeconds(0.8f);
            yield return Shot("scene-sticker");
            HandRig.I.Equip(ItemId.Lens);
            yield return new WaitForSeconds(0.8f);
            yield return Shot("scene-sticker-lens");
            HandRig.I.Equip(ItemId.None);
        }

        yield return Jump(3, "Store");
        yield return new WaitForSeconds(0.6f);
        yield return Shot("scene-store");
    }
}
