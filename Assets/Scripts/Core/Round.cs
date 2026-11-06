using System.Collections;
using UnityEngine;

// 회차 전환. GameState가 다음 프로필이 다르면 CloseEyes로, 같으면 암전으로 닫는다. 씬 Director는 시작에서 Open을 yield한다
public static class Round
{
    public static bool ProfileChanged;   // GameState가 챕터를 넘길 때 정한다

    static bool eyesShut;

    /// <summary>눈 뜨기, 프로필이 바뀌었으면 손을 들어 보여 줌, Freeze 해제. goal은 쓰지 않는다(쪽지가 대신한다).</summary>
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
            var who = GameState.I.Profile;
            bool bag = who != null && who.briefcase;   // 서류가방을 든 나이대는 가방을 올려 손과 함께 보여 준다
            HandRig.I.caseLift = bag ? Bal.G("Round_CaseLift", 0.12f) : 0f;
            HandRig.I.SetPointer(true);
            yield return new WaitForSeconds(bag ? Bal.G("Round_CaseShowSec", 2.2f) : Bal.G("Round_HandShowSec", 1.5f));
            HandRig.I.SetPointer(false);
            HandRig.I.caseLift = 0f;
        }

        pc.Freeze(false);
    }

    /// <summary>쓰지 않는다. 목표 문구는 쪽지로 바뀌었다. 부르는 곳이 없어지면 지운다.</summary>
    public static void Goal(string text) { }

    // GameState 전용. 소리를 끊고 sec 동안 검은 화면으로 둔다. 소리는 GameState가 씬을 다 불러온 뒤 되돌린다
    public static IEnumerator Silence(float sec)
    {
        if (AudioManager.I != null) AudioManager.I.CutAll();
        AudioListener.volume = 0f;   // 앞 씬에 남은 소리가 암전 중에 새로 나지 않게
        yield return new WaitForSecondsRealtime(sec);
    }

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
        for (float t = 0f; t < sec; t += PauseMenu.Dt)
        {
            float k = t / Mathf.Max(sec, 0.001f);
            ui.Lids(Mathf.Lerp(from, to, k * k * (3f - 2f * k)));
            yield return null;
        }
        ui.Lids(to);
    }
}
