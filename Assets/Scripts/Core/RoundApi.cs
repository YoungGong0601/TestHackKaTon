using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

// ROUND_PLAN 6절의 정적 입구. 화면 쪽 참조는 RoundUi(HUD)에 있다

// 버스 계단. 입력 없이 자동으로 오르내린다. 인물마다 시간만 다르다
public static class Steps
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
        pc.MoveTo(bottom.position);   // Teleport는 시선 높이를 0으로 돌려 시점이 튄다
        pc.StartCoroutine(pc.TurnTo(yaw, Bal.G("Steps_LookPitch", 6f), Bal.G("Cine_BlendSec", 1f)));

        float sec = Mathf.Max(Bal.Age("ClimbSec", 1.1f, 1.2f, 1.8f, 3.2f), 0.01f), step = 0f;
        for (float t = 0f; t < sec; t += Time.deltaTime)
        {
            pc.MoveTo(Vector3.Lerp(bottom.position, top.position, Mathf.SmoothStep(0f, 1f, t / sec)));
            step += Time.deltaTime;
            if (step > sec / 3f)
            {
                step = 0f;
                AudioManager.I.Play("step_concrete", null, 0.5f, UnityEngine.Random.Range(0.92f, 1.04f), true);
            }
            yield return null;
        }
        pc.MoveTo(top.position);
        pc.SetMode(mode);
        pc.Freeze(frozen);
    }

    public static IEnumerator Descend(Transform top, Transform bottom)
    {
        var pc = PlayerController.I;
        bool frozen = pc.Frozen;
        pc.Freeze(true);
        float sec = Mathf.Max(Bal.G("Steps_DescendSec", 1.4f), 0.01f), step = 0f;
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
    // 하단 카피는 프로토타입 결과 화면 끝 줄과 같다. 숫자 2.3%는 그림 Txt_End_Number
    public const string Stat = "65세 이상 노인 중 키오스크로\n주문할 수 있는 사람은 약 18%.";
    public const string Source = "출처: 2023년도 노인실태조사(보건복지부, 한국보건사회연구원),\n김세진, 「노인의 여가 및 정보화 현황」, 보건복지포럼 2024년 11월호";
    public const string Title = "불고기 버거 세트 하나";

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
            // 한 화면에 위 제목, 가운데 통계, 아래 카피, 맨 아래 출처
            ui.EndStat(Stat, Source);
            ui.EndTitle(Title);
            yield return ui.EndReveal();
            yield return new WaitForSeconds(Bal.G("End_StatSec", 5f));
            while (!RoundUi.Clicked) yield return null;
            yield return null;
            yield return ui.EndResult();
            while (!RoundUi.Clicked) yield return null;
            ui.End(false);
        }
        GameState.I.Restart();
    }
}
