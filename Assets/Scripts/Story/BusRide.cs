// 카드를 찍은 뒤 빈자리까지 걸어가 앉아 창밖을 보며 가고, 안내방송 뒤 페이드로 내린다. 1, 4회차 공통.
// 끝나면 화면이 닫힌 채 돌아온다. 부른 쪽이 CompleteChapter를 부른다.
// 이름으로 찾는다: Anchor_BusSeatAisle = 좌석 옆 통로, Anchor_BusSeat = 앉는 자리(+Z가 앉아서 보는 쪽)
// BusOutside = 창밖 묶음. 없으면 그 연출만 건너뛴다
using System.Collections;
using UnityEngine;

public static class BusRide
{
    static bool riding;

    static PlayerController Player => PlayerController.I;
    static AudioManager Sound => AudioManager.I;

    public static IEnumerator Run(MonoBehaviour host)
    {
        Transform aisle = Named("Anchor_BusSeatAisle"), seat = Named("Anchor_BusSeat"), outside = Named("BusOutside");
        float end = Time.time + Bal.G("Bus_RideSec", 12f);

        Player.Freeze(true);
        Player.HoldStill = true;
        Sound.Play("bus_door_close", null, 0.8f);
        Sound.Play("bus_leave", null, 0.5f);
        Sound.Ambience(("bus_idle", Bal.G("Bus_RideEngineVol", 0.7f)));
        riding = true;
        host.StartCoroutine(Rumble());
        if (outside) host.StartCoroutine(Scroll(outside, seat ? -seat.forward : Vector3.left));

        if (aisle) yield return Go(host, aisle.position);
        if (seat) yield return Sit(host, seat);
        float yaw = seat ? seat.eulerAngles.y : Player.Yaw;
        Player.LimitLook(yaw, Bal.G("Bus_RideYawDeg", 100f), Bal.G("Bus_RidePitchDown", -25f), Bal.G("Bus_RidePitchUp", 20f));
        Player.Freeze(false);

        while (Time.time < end - Bal.G("Bus_AnnounceLeadSec", 4f)) yield return null;
        yield return Hud.I.Say(null, "이번 정류장은, 시장 입구입니다.", "bus_ann");
        while (Time.time < end) yield return null;

        Sound.Play("bus_arrive", null, 0.5f);
        yield return Hud.I.Fade(1f, Bal.G("Bus_RideFadeSec", 0.8f));
        riding = false;
        Player.Freeze(true);
        Player.FreeLook();
        Player.HoldStill = false;
        Sound.Play("bus_door_open", null, 0.8f);
    }

    static IEnumerator Go(MonoBehaviour host, Vector3 to)
    {
        host.StartCoroutine(Player.LookAt(to + Vector3.up * Player.EyeHeight, Bal.G("Bus_SeatTurnSec", 0.5f)));
        yield return StoreFlow.Race(host, Player.WalkTo(to), Bal.G("Bus_SeatWalkMaxSec", 4f));
    }

    // 좌석 콜라이더 안으로 들어가므로 걷지 않고 몸을 옮긴다. 눈은 몸 기준이라 몸을 내려 앉은 높이를 맞춘다
    static IEnumerator Sit(MonoBehaviour host, Transform seat)
    {
        float sec = Mathf.Max(Bal.G("Bus_SitSec", 0.9f), 0.01f);
        Vector3 from = Player.transform.position, to = seat.position;
        to.y += Bal.G("Bus_SitEye", 1.3f) - Player.EyeHeight;
        host.StartCoroutine(Player.TurnTo(seat.eulerAngles.y, 0f, sec));
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            Player.MoveTo(Vector3.Lerp(from, to, t * t * (3f - 2f * t)));
            yield return null;
        }
        Player.MoveTo(to);
    }

    static IEnumerator Rumble()
    {
        while (riding)
        {
            Player.AddShake(Bal.G("Bus_RideShake", 0.6f) * Time.deltaTime);
            yield return null;
        }
    }

    // 버스 대신 거리를 뒤로 민다
    static IEnumerator Scroll(Transform outside, Vector3 dir)
    {
        float top = Bal.G("Bus_RideSpeed", 8f), accel = Bal.G("Bus_RideAccel", 2f);
        for (float v = 0f; riding; v = Mathf.Min(top, v + accel * Time.deltaTime))
        {
            outside.position += dir * (v * Time.deltaTime);
            yield return null;
        }
    }

    static Transform Named(string name)
    {
        GameObject g = GameObject.Find(name);
        return g ? g.transform : null;
    }
}
