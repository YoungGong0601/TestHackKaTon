// 코드로 연결한 효과음 다섯 개가 실제로 재생되는지 본다. 소리 내용은 사람이 들어야 한다. 평소 시험에서는 돌지 않는다(Explicit).
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

public class SoundWiringTests : KioskBotFixture
{
    static void Listen(HashSet<string> heard)
    {
        foreach (var s in AudioManager.I.GetComponentsInChildren<AudioSource>(true))
            if (s.isPlaying && s.clip != null) heard.Add(s.clip.name);
    }

    static bool Any(HashSet<string> heard, string key) => heard.Any(n => n.StartsWith(key));

    static IEnumerator ShotStreet()
    {
        yield return new WaitForEndOfFrame();
        int w = Screen.width, h = Screen.height;
        var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
        var rt = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
        ScreenCapture.CaptureScreenshotIntoRenderTexture(rt);
        var flip = RenderTexture.GetTemporary(w, h, 0, RenderTextureFormat.ARGB32);
        Graphics.Blit(rt, flip, new Vector2(1f, -1f), new Vector2(0f, 1f));
        var prev = RenderTexture.active;
        RenderTexture.active = flip;
        tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
        tex.Apply();
        RenderTexture.active = prev;
        RenderTexture.ReleaseTemporary(rt);
        RenderTexture.ReleaseTemporary(flip);
        string dir = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "Screenshots"));
        File.WriteAllBytes(Path.Combine(dir, "font-street-traffic.png"), tex.EncodeToPNG());
        Object.Destroy(tex);
    }

    [UnityTest, Explicit, Timeout(280000)]
    public IEnumerator StreetTraffic()
    {
        GameState.I.JumpChapter(1);
        yield return Until(() => SceneManager.GetActiveScene().name == "Street" && !PlayerController.I.Frozen, 40f, "골목 도착");
        var cars = Object.FindObjectsByType<TrafficMover>(FindObjectsSortMode.None);
        Assert.AreEqual(6, cars.Length, "차 5대와 오토바이 1대");

        var p = PlayerController.I;
        p.Teleport(new Vector3(26f, 0f, 33f), 0f);
        var heard = new HashSet<string>();
        bool shot = false;
        float end = Time.realtimeSinceStartup + 120f;
        Time.timeScale = 2f;
        while (Time.realtimeSinceStartup < end && !(Any(heard, "car_pass") && Any(heard, "scooter_pass") && Any(heard, "crosswalk_beep") && shot))
        {
            Listen(heard);
            if (!shot)
            {
                var near = cars.FirstOrDefault(c => c.transform.Find("Visual").gameObject.activeSelf && Mathf.Abs(c.transform.position.x - 26f) < 12f);
                if (near != null)
                {
                    Time.timeScale = 1f;
                    yield return p.LookAt(near.transform.position + Vector3.up, 0.1f);
                    yield return ShotStreet();
                    shot = true;
                    Time.timeScale = 2f;
                }
            }
            yield return null;
        }
        Time.timeScale = 1f;
        Assert.IsTrue(Any(heard, "car_pass"), "car_pass");
        Assert.IsTrue(Any(heard, "scooter_pass"), "scooter_pass");
        Assert.IsTrue(Any(heard, "crosswalk_beep"), "crosswalk_beep");
    }

    [UnityTest, Explicit, Timeout(280000)]
    public IEnumerator StoreSounds()
    {
        yield return EnterKiosk();
        var crowd = nunchi.transform.Find("Nunchi_Crowd").GetComponent<AudioSource>();
        Assert.IsFalse(crowd.isPlaying, "시작에는 조용함");
        bot.SetNunchi(70f);
        yield return new WaitForSeconds(1.5f);
        Assert.IsTrue(crowd.isPlaying, "눈치 단계에서 웅성임 재생");
        Assert.Greater(crowd.volume, 0.2f);
        float low = crowd.volume;
        bot.SetNunchi(95f);
        yield return new WaitForSeconds(1.5f);
        Assert.Greater(crowd.volume, low, "눈치가 오르면 커짐");
        bot.SetNunchi(10f);

        yield return OrderMemo();
        yield return PayWithCard();
        var heard = new HashSet<string>();
        Time.timeScale = 4f;
        float end = Time.realtimeSinceStartup + 60f;
        while (Time.realtimeSinceStartup < end && !Any(heard, "tray_put"))
        {
            Listen(heard);
            yield return null;
        }
        Time.timeScale = 1f;
        Assert.IsTrue(Any(heard, "tray_put"), "tray_put");
        yield return new WaitForSeconds(2.5f);
        Assert.IsFalse(crowd.isPlaying, "키오스크를 떠나면 그침");
    }
}
