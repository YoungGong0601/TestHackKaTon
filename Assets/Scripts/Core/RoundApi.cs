using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

// ROUND_PLAN 6절의 정적 입구. 화면 쪽 참조는 RoundUi(HUD)에 있다

// 계단 마싱. 임시 T05: 좌클릭 또는 E 연타, 횟수만 다름, 멈춰도 내려가지 않음
public static class Mash
{
    public static IEnumerator Climb(Transform bottom, Transform top)
    {
        var pc = PlayerController.I;
        var mode = pc.CurrentMode;
        bool frozen = pc.Frozen;
        pc.Freeze(true);
        pc.SetMode(PlayerController.Mode.Hidden);
        // 계단 진행 방향을 본다. 앵커 회전에 기대지 않고 아래에서 위로 가는 방향을 쓴다
        Vector3 up = top.position - bottom.position;
        up.y = 0f;
        float yaw = up.sqrMagnitude > 1e-3f ? Mathf.Atan2(up.x, up.z) * Mathf.Rad2Deg : top.eulerAngles.y;
        pc.BlendCamera();
        pc.Teleport(bottom.position, pc.Yaw);
        pc.StartCoroutine(pc.TurnTo(yaw, Bal.G("Mash_LookPitch", 6f), Bal.G("Cine_BlendSec", 1f)));

        int total = Mathf.Max(1, Mathf.RoundToInt(Bal.Age("MashCount", 10f, 10f, 10f, 40f))), done = 0;
        float shown = 0f;
        if (RoundUi.I != null) RoundUi.I.Mash(true, 0, total);
        while (done < total)
        {
            var mouse = Mouse.current;
            var kb = Keyboard.current;
            if ((mouse != null && mouse.leftButton.wasPressedThisFrame) || (kb != null && kb.eKey.wasPressedThisFrame))
            {
                done++;
                AudioManager.I.Play("step_concrete", null, 0.5f, UnityEngine.Random.Range(0.92f, 1.04f), true);
                if (RoundUi.I != null) RoundUi.I.Mash(true, done, total);
            }
            shown = Mathf.MoveTowards(shown, (float)done / total, Time.deltaTime * 4f);
            pc.MoveTo(Vector3.Lerp(bottom.position, top.position, shown));
            yield return null;
        }
        pc.MoveTo(top.position);
        if (RoundUi.I != null) RoundUi.I.Mash(false, 0, 0);
        pc.SetMode(mode);
        pc.Freeze(frozen);
    }

    public static IEnumerator Descend(Transform top, Transform bottom)
    {
        var pc = PlayerController.I;
        bool frozen = pc.Frozen;
        pc.Freeze(true);
        float sec = Mathf.Max(Bal.G("Mash_DescendSec", 1.4f), 0.01f), step = 0f;
        for (float t = 0f; t < sec; t += Time.deltaTime)
        {
            pc.MoveTo(Vector3.Lerp(top.position, bottom.position, t / sec));
            step += Time.deltaTime;
            if (step > 0.45f)
            {
                step = 0f;
                AudioManager.I.Play("step_concrete", null, 0.45f, 1f, true);
            }
            yield return null;
        }
        pc.MoveTo(bottom.position);
        pc.Freeze(frozen);
    }
}

// 손목시계. 입력 잠금, 왼손 시계 들기, 바늘 표시, Watch_LookSec 뒤 내림
public static class Watch
{
    public static IEnumerator Look(int hour)
    {
        var pc = PlayerController.I;
        bool frozen = pc.Frozen;
        pc.Freeze(true);
        HandRig.I.ShowWatch(hour);
        yield return new WaitForSeconds(Bal.G("Watch_LookSec", 2f));
        HandRig.I.HideWatch();
        yield return new WaitForSeconds(0.3f);
        pc.Freeze(frozen);
    }
}

// 대화 선택지. HUD 버튼, 커서 모드로 바꾸고 고른 뒤 이전 모드로
public static class Choice
{
    public static IEnumerator Ask(string[] labels, Action<int> picked)
    {
        var pc = PlayerController.I;
        var ui = RoundUi.I;
        var mode = pc.CurrentMode;
        bool frozen = pc.Frozen;
        pc.Freeze(true);
        // 키오스크 앞은 손 포인터 그대로, 그 밖은 마우스 커서를 보인다
        if (mode != PlayerController.Mode.Cursor) pc.SetMode(PlayerController.Mode.Locked);
        ui.ChoiceShow(labels);
        yield return null;

        int hit = -1;
        while (true)
        {
            hit = ui.ChoiceHover();
            if (hit >= 0 && RoundUi.Clicked) break;
            yield return null;
        }
        AudioManager.I.Play("kiosk_tap", null, 0.7f);
        ui.ChoiceShow(null);
        if (mode != PlayerController.Mode.Cursor) pc.SetMode(mode);
        pc.Freeze(frozen);
        picked?.Invoke(hit);
    }
}

// 컷. 임시 T28: 플레이어 시점을 걷는 사람 뒤로 옮겨 찍고 원래 자리로 돌아온다
public static class Cine
{
    public static IEnumerator BackShot(NpcMover walker, Vector3 walkTo, float sec)
    {
        var pc = PlayerController.I;
        var mode = pc.CurrentMode;
        bool frozen = pc.Frozen;
        Vector3 back = pc.transform.position;
        float yaw = pc.Yaw, pitch = pc.Pitch;

        pc.Freeze(true);
        pc.SetMode(PlayerController.Mode.Hidden);
        HandRig.I.SetEnabled(false);
        Vector3 from = walker.transform.position, dir = walkTo - from;
        dir.y = 0f;
        dir = dir.sqrMagnitude > 1e-4f ? dir.normalized : walker.transform.forward;
        Vector3 cam = from - dir * Bal.G("Shot_BackDist", 4f);
        cam.y = from.y + Bal.G("Shot_BackHeight", 1.5f) - pc.EyeHeight;
        pc.BlendCamera();
        pc.Teleport(cam, Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg);

        float speed = Vector3.Distance(from, walkTo) / Mathf.Max(sec, 0.01f);
        walker.Go(walkTo, speed);
        yield return new WaitForSeconds(sec);

        pc.BlendCamera();
        pc.Teleport(back, yaw);
        yield return pc.TurnTo(yaw, pitch, 0.01f);
        HandRig.I.SetEnabled(true);
        pc.SetMode(mode);
        pc.Freeze(frozen);
    }
}

// 마지막 챕터의 CompleteChapter가 부른다. 암막, 통계 문구, 작은 출처, 제목, 클릭 대기, Restart
public static class Ending
{
    // 임시 T32: 사용자 지시 문구(시트 문구를 대신함)
    public const string Stat = "80~84세 노인 중 키오스크로 주문할 수 있는 사람은 2.3%입니다.";
    public const string Source = "출처: 2023년도 노인실태조사(보건복지부, 한국보건사회연구원),\n김세진, 「노인의 여가 및 정보화 현황」, 보건복지포럼 2024년 11월호";
    public const string Title = "불고기버거 세트 하나";

    public static IEnumerator Play()
    {
        var pc = PlayerController.I;
        var ui = RoundUi.I;
        pc.Freeze(true);
        pc.SetMode(PlayerController.Mode.Hidden);
        Hud.I.Prompt(null);
        Hud.I.ClearSubs();
        Hud.I.Views(null);
        yield return Hud.I.Fade(1f, 0.7f);
        AudioManager.I.Ambience();
        if (ui != null)
        {
            ui.End(true);
            ui.EndStat(Stat, Source);
            yield return new WaitForSeconds(Bal.G("End_StatSec", 5f));
            ui.EndTitle(Title);
            yield return new WaitForSeconds(Bal.G("End_TitleMinSec", 1.5f));
            while (!RoundUi.Clicked) yield return null;
            ui.End(false);
        }
        GameState.I.Restart();
    }
}
