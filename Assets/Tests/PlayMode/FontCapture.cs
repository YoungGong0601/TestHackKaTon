// HUD 고딕과 메모 손글씨 검수용 장면을 Screenshots/font2-*.png 로 저장한다. 평소 시험에서는 돌지 않는다(Explicit).
using System.Collections;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

public class FontCapture : KioskBotFixture
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
        File.WriteAllBytes(Path.Combine(Dir, "font2-" + name + ".png"), tex.EncodeToPNG());
        Object.Destroy(tex);
    }

    // 키오스크 화면 그대로(번지기 전)
    static IEnumerator SaveSharp()
    {
        yield return new WaitForEndOfFrame();
        foreach (var rt in Resources.FindObjectsOfTypeAll<RenderTexture>())
        {
            if (rt.name != "RT_Sharp") continue;
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            File.WriteAllBytes(Path.Combine(Dir, "font2-kiosk-sharp.png"), tex.EncodeToPNG());
            Object.Destroy(tex);
            break;
        }
    }

    // 대본과 스크립트의 대사, 목표 문구 전부를 자막에 넣어 끝 글자만 남는 줄이 없는지 본다
    [UnityTest, Explicit, Timeout(120000)]
    public IEnumerator SubsWrap()
    {
        var hud = Hud.I;
        var subs = hud.GetComponentsInChildren<TMPro.TMP_Text>(true).First(t => t.name == "Subs");
        var lit = new Regex(@"\.(Say\([^""\n]*|Objective\()""([^""]+)""");
        var all = Directory.GetFiles(Path.Combine(Application.dataPath, "Scripts"), "*.cs", SearchOption.AllDirectories)
            .SelectMany(f => lit.Matches(File.ReadAllText(f)).Cast<Match>().Select(m => m.Groups[2].Value))
            .Concat(File.ReadAllLines(Path.Combine(Application.dataPath, "Resources/Audio/VO_LINES.csv")).Skip(1)
                .Select(l => Regex.Match(l, "^[^,]*,[^,]*,\"?(.*?)\"?,[^,]*$").Groups[1].Value).Where(l => l.Length > 0))
            .Distinct().ToList();
        var log = new System.Text.StringBuilder();
        int multi = 0, bad = 0;
        float width = subs.rectTransform.rect.width;
        foreach (var line in all)
        {
            hud.Say("yM", line, null, 0f);
            subs.ForceMeshUpdate();
            var info = subs.textInfo;
            int n = info.lineCount;
            if (n < 2) continue;
            multi++;
            var last = info.lineInfo[n - 1];
            bool odd = last.visibleCharacterCount < 4 || info.lineInfo.Take(n).Any(l => l.lineExtents.max.x - l.lineExtents.min.x > width);
            if (odd) bad++;
            log.AppendLine((odd ? "BAD " : "") + n + " lines: " + subs.text.Replace("\n", " / "));
        }
        // 실제 대사는 지금 크기에서 한 줄에 들어가므로 넘치는 경우는 긴 문장으로 따로 본다
        hud.Say("yM", "할아버지, 뒤에 사람들 기다리잖아요. 모르시면 저기 직원한테 물어보시든가, 저희 먼저 하면 안 될까요?", null, 3f);
        subs.ForceMeshUpdate();
        var longInfo = subs.textInfo;
        log.AppendLine("long " + longInfo.lineCount + " lines: " + subs.text.Replace("\n", " / "));
        if (longInfo.lineCount != 2 || longInfo.lineInfo[1].visibleCharacterCount < 4) bad++;
        yield return new WaitForSeconds(0.3f);
        yield return Shot("speech-long");
        hud.ClearSubs();
        var font = subs.font;
        string missing = new string(string.Concat(all).Where(c => !char.IsWhiteSpace(c) && !font.HasCharacter(c, false, true)).Distinct().ToArray());
        log.Insert(0, "lines " + all.Count + " wrapped " + multi + " bad " + bad + " missing '" + missing + "'\n");
        File.WriteAllText(Path.Combine(Dir, "font2-wrap.txt"), log.ToString());
        yield return null;
        Assert.AreEqual(0, bad, log.ToString());
        Assert.IsEmpty(missing);
    }

    [UnityTest, Explicit, Timeout(600000)]
    public IEnumerator Capture()
    {
        var hud = Hud.I;
        // 시작 화면
        var title = hud.transform.Find("Title").gameObject;
        title.SetActive(true);
        yield return new WaitForSecondsRealtime(0.5f);
        yield return Shot("title");
        title.SetActive(false);

        // 키오스크
        yield return EnterKiosk();
        yield return new WaitForSeconds(1f);
        yield return Shot("kiosk");
        yield return PressAll("start", "takeout", "skip", "tab_CLASSIC");
        yield return new WaitForSeconds(0.4f);
        yield return Shot("kiosk-menu");
        yield return SaveSharp();

        // 메모
        HandRig.I.Equip(ItemId.Memo);
        yield return new WaitForSeconds(1f);
        yield return Shot("memo");
        HandRig.I.Equip(ItemId.None);

        // 대사 자막과 목표 자막, 프롬프트, 소지품, 눈치 라벨
        hud.Say(GameState.I.Profile.speakerKey, "이게 왜 안 돼. 글씨가 왜 이렇게 작아, {y:사이다}는 어디 있는 거야.", null, 3f);
        yield return new WaitForSeconds(0.3f);
        yield return Shot("speech");
        hud.Objective("{y:버스 정류장}으로 간다. 옆 {y:사람}에게 묻는다", 3f);
        hud.Prompt("E 문 열기");
        yield return new WaitForSeconds(0.3f);
        yield return Shot("objective");
        hud.Prompt(null);

        // 결과 화면
        yield return Key(UnityEngine.InputSystem.Key.D);
        hud.ShowResult();
        yield return new WaitForSecondsRealtime(1.6f);
        yield return Shot("result");
    }
}
