using System.Collections;
using UnityEngine;

// 회차 전환. GameState가 다음 프로필이 다르면 CloseEyes로, 같으면 암전으로 닫는다. 씬 Director는 시작에서 Open을 yield한다
public static class Round
{
    public static bool ProfileChanged;   // GameState가 챕터를 넘길 때 정한다

    static bool eyesShut;

    /// <summary>눈 뜨기, 프로필이 바뀌었으면 손을 들어 보여 줌, 목표, Freeze 해제.</summary>
    public static IEnumerator Open(string goal = null)
    {
        var pc = PlayerController.I;
        pc.Freeze(true);
        while (Hud.I.TitleOpen) yield return null;

        if (eyesShut)
        {
            eyesShut = false;
            Hud.I.Fade(0f, 0f);
            yield return Lids(1f, 0f, Bal.G("Round_BlinkOpenSec", 0.9f));
        }
        else
        {
            if (RoundUi.I != null) RoundUi.I.Lids(0f);
            yield return Hud.I.Fade(0f, Bal.G("Chapter_FadeInSec", 1f));
        }

        if (ProfileChanged)
        {
            ProfileChanged = false;
            HandRig.I.SetPointer(true);
            yield return new WaitForSeconds(Bal.G("Round_HandShowSec", 1.5f));
            HandRig.I.SetPointer(false);
        }

        if (goal != null) Goal(goal);
        pc.Freeze(false);
    }

    /// <summary>목표 한 줄 교체. null이면 지움. 4회차는 안 부른다.</summary>
    public static void Goal(string text) => Hud.I.Objective(text, Bal.G("Round_GoalKeepSec", 0f));

    // GameState 전용
    public static IEnumerator CloseEyes()
    {
        if (RoundUi.I == null)
        {
            yield return Hud.I.Fade(1f, Bal.G("Round_BlinkCloseSec", 0.6f));
            yield break;
        }
        yield return Lids(0f, 1f, Bal.G("Round_BlinkCloseSec", 0.6f));
        Hud.I.Fade(1f, 0f);
        eyesShut = true;
    }

    static IEnumerator Lids(float from, float to, float sec)
    {
        var ui = RoundUi.I;
        if (ui == null) yield break;
        for (float t = 0f; t < sec; t += Time.unscaledDeltaTime)
        {
            float k = t / Mathf.Max(sec, 0.001f);
            ui.Lids(Mathf.Lerp(from, to, k * k * (3f - 2f * k)));
            yield return null;
        }
        ui.Lids(to);
    }
}
