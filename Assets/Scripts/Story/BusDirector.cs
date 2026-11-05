// 버스 안 진행: 승차 암전에서 내부로 밝아짐, 출발 소리, 안내방송, 다음 챕터.
// 씬에서 연결할 필드는 없다. Bus 씬의 Director 오브젝트에 붙인다.
using System.Collections;
using UnityEngine;

public class BusDirector : MonoBehaviour
{
    static Hud Ui => Hud.I;
    static AudioManager Sound => AudioManager.I;

    IEnumerator Start()
    {
        var player = PlayerController.I;
        player.SetMode(PlayerController.Mode.Fps);
        player.Freeze(true);
        yield return Ui.Fade(1f, 0f);
        Sound.Ambience(("bus_idle", 0.7f));
        Sound.Play("bus_door", null, 0.7f);
        yield return Ui.Fade(0f, Bal.G("Bus_InsideFadeSec", 1f));
        player.Freeze(false);

        yield return new WaitForSeconds(Bal.G("Bus_RideDoorSec", 1.6f));
        Sound.Play("bus_leave", null, 0.5f);
        yield return new WaitForSeconds(Bal.G("Bus_RideEngineSec", 2.4f));

        float t0 = Time.time;
        yield return Ui.Say(null, "이번 정류장은, 시장 입구입니다.", "bus_ann");
        float rest = Bal.G("Bus_AnnounceHoldSec", 2.4f) - (Time.time - t0);
        if (rest > 0f) yield return new WaitForSeconds(rest);
        yield return new WaitForSeconds(Bal.G("Bus_AfterAnnounceSec", 1.2f));
        GameState.I.CompleteChapter();
    }
}
