// 버스 안 진행: 승차 암전에서 내부로 밝아짐, 출발 소리, 안내방송, 다음 챕터.
// 배치: outside = Env_Outside (창밖 거리. 버스 대신 거리를 뒤로 민다)
using System.Collections;
using UnityEngine;

public class BusDirector : MonoBehaviour
{
    static Hud Ui => Hud.I;
    static AudioManager Sound => AudioManager.I;

    [SerializeField] Transform outside;

    IEnumerator Scroll()
    {
        for (float v = 0f; ; v = Mathf.Min(8f, v + 2f * Time.deltaTime))
        {
            outside.position += Vector3.left * (v * Time.deltaTime);
            yield return null;
        }
    }

    IEnumerator Start()
    {
        var player = PlayerController.I;
        player.SetMode(PlayerController.Mode.Fps);
        player.Freeze(true);
        yield return Ui.Fade(1f, 0f);
        Sound.Ambience(("bus_idle", 0.7f));
        Sound.Play("bus_door_close", null, 0.7f);
        yield return Ui.Fade(0f, Bal.G("Bus_InsideFadeSec", 1f));
        player.Freeze(false);

        yield return new WaitForSeconds(Bal.G("Bus_RideDoorSec", 1.6f));
        Sound.Play("bus_leave", null, 0.5f);
        StartCoroutine(Scroll());
        yield return new WaitForSeconds(Bal.G("Bus_RideEngineSec", 2.4f));

        float t0 = Time.time;
        yield return Ui.Say(null, "이번 정류장은, 시장 입구입니다.", "bus_ann");
        float rest = Bal.G("Bus_AnnounceHoldSec", 2.4f) - (Time.time - t0);
        if (rest > 0f) yield return new WaitForSeconds(rest);
        Sound.Play("bus_arrive", null, 0.5f);
        yield return new WaitForSeconds(Bal.G("Bus_AfterAnnounceSec", 1.2f));
        GameState.I.CompleteChapter();
    }
}
