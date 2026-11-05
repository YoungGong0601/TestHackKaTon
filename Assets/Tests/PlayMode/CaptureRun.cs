// 처음부터 끝까지 한 판을 진행하며 장면을 Screenshots/play-*.png 로 저장한다. 평소 시험에서는 돌지 않는다(Explicit).
using System.Collections;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

public class CaptureRun : KioskBotFixture
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
        File.WriteAllBytes(Path.Combine(Dir, "play-" + name + ".png"), tex.EncodeToPNG());
        Object.Destroy(tex);
        Debug.Log("촬영 " + name + " " + w + "x" + h);
    }

    static Interactable Find(string label) =>
        Object.FindObjectsByType<Interactable>(FindObjectsInactive.Exclude, FindObjectsSortMode.None)
            .FirstOrDefault(i => i.active && i.label == label);

    static IEnumerator Scene(string name, float sec) =>
        Until(() => SceneManager.GetActiveScene().name == name && !PlayerController.I.Frozen, sec, "씬 " + name);

    static IEnumerator Face(Vector3 stand, Vector3 look)
    {
        var p = PlayerController.I;
        stand.y = p.transform.position.y;
        Vector3 d = look - stand;
        p.Teleport(stand, Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg);
        yield return null;
        yield return p.LookAt(look, 0.2f);
    }

    [UnityTest, Explicit, Timeout(900000)]
    public IEnumerator Capture()
    {
        // 현관
        GameState.I.JumpChapter(0);
        yield return Scene(GameState.I.flow.chapters[0].sceneName, 30f);
        yield return new WaitForSeconds(0.6f);
        yield return Shot("01-home");
        yield return Use("메모 내리기", 10f);
        yield return Use("신발 신기", 10f);
        yield return Until(() => Find("문 열기") != null, 15f, "문 열기 준비");
        yield return Use("문 열기", 5f);

        // 골목과 정류장
        yield return Scene("Street", 60f);
        yield return new WaitForSeconds(0.4f);
        yield return Shot("02-alley");

        Vector3 bis = GameObject.Find("BisLook").transform.position;
        Vector3 stand = new Vector3(26.2f, 0f, 33f);
        yield return Face(stand, bis);
        yield return new WaitForSeconds(1.2f);
        yield return Shot("03-busstop");
        Time.timeScale = 3f;
        yield return Use("말 걸기", 40f);
        yield return Until(() => !PlayerController.I.Frozen, 30f, "학생 대화 끝");
        yield return Use("말 걸기", 40f);
        yield return Until(() => !PlayerController.I.Frozen, 30f, "행인 대화 끝");
        Time.timeScale = 1f;

        yield return Face(stand, bis);
        HandRig.I.Equip(ItemId.Lens);
        yield return Until(() => HandRig.I.LensHit != null, 5f, "돋보기 조준");
        yield return new WaitForSeconds(0.6f);
        yield return Shot("04-lens-bis");

        Time.timeScale = 3f;
        yield return Use("버스 타기", 60f);
        yield return Until(() => SceneManager.GetActiveScene().name == "Storefront", 40f, "매장 앞 도착");
        Time.timeScale = 1f;

        // 매장 앞
        yield return Scene("Storefront", 30f);
        yield return new WaitForSeconds(0.3f);
        yield return Shot("05-storefront");
        while (Find("당기기") == null)
        {
            yield return Use("밀기", 5f);
            yield return new WaitForSeconds(2.2f);
        }
        yield return Use("당기기", 5f);

        // 매장
        yield return Scene("Store", 40f);
        yield return new WaitForSeconds(0.4f);
        yield return Shot("06-store");

        bot = Object.FindAnyObjectByType<KioskBot>();
        nunchi = Object.FindAnyObjectByType<NunchiSystem>();
        yield return EnterKiosk();
        yield return new WaitForSeconds(1f);
        yield return Shot("07-kiosk-idle");
        yield return PressAll("start", "takeout", "skip", "tab_CLASSIC");
        yield return new WaitForSeconds(0.4f);
        yield return Shot("08-kiosk-menu");

        HandRig.I.Equip(ItemId.Lens);
        // 실제 마우스가 끼어들지 않게 매 프레임 메뉴 칸 위에 둔다
        for (float end = Time.time + 1f; Time.time < end; )
        {
            PlayerController.I.SetCursor01(new Vector2(0.56f, 0.5f));
            yield return null;
        }
        PlayerController.I.SetCursor01(new Vector2(0.56f, 0.5f));
        yield return Shot("09-lens");
        HandRig.I.Equip(ItemId.None);

        yield return Key(UnityEngine.InputSystem.Key.S);
        yield return Until(() => nunchi.LookingBack, 3f, "뒤보기");
        yield return new WaitForSeconds(1f);
        yield return Shot("10-back");
        yield return Key(UnityEngine.InputSystem.Key.A);
        yield return new WaitForSeconds(1f);
        yield return Shot("11-staff");
        yield return Key(UnityEngine.InputSystem.Key.D);
        yield return new WaitForSeconds(0.8f);

        // 폭발
        bot.SetNunchi(99.9f);
        yield return Until(() => Stats.blowups == 1, 5f, "폭발 시작");
        yield return new WaitForSeconds(1.2f);
        yield return Shot("12-blowup-turn");
        yield return Until(() => bot.Screen == "cart", 40f, "끼어든 사람 주문");
        yield return Shot("13-blowup-demo");
        Time.timeScale = 3f;
        yield return Until(() => !nunchi.Hold, 40f, "폭발 끝");
        Time.timeScale = 1f;
        yield return new WaitForSeconds(0.7f);

        yield return OrderMemo();
        HandRig.I.Equip(ItemId.Card);
        bot.LiftPoster();
        yield return Key(UnityEngine.InputSystem.Key.W);
        yield return new WaitForSeconds(0.9f);
        yield return Shot("14-card-slot");
        yield return Key(UnityEngine.InputSystem.Key.W);
        yield return PayWithCard();

        // 픽업
        Time.timeScale = 6f;
        yield return Until(() => Find("받기") != null, 40f, "번호 호출");
        Time.timeScale = 1f;
        yield return new WaitForSeconds(0.3f);
        Vector3 bag = Find("받기").transform.position;
        Vector3 from = PlayerController.I.transform.position - bag;
        from.y = 0f;
        yield return Face(bag + from.normalized * 1.6f, bag);
        yield return new WaitForSeconds(0.4f);
        yield return Shot("15-pickup");

        yield return PickupAndFinish();
        yield return new WaitForSecondsRealtime(2f);
        yield return Shot("16-result");

        AssertMemoOrder();
        Assert.AreEqual(1, Stats.blowups);
    }
}
