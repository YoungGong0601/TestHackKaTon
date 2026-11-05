// 멀리 횡단보도 신호음. 큰길 쪽에 있을 때만 틈을 두고 들린다. HTML판은 파일만 있고 쓰지 않아 새로 정한 시점이다.
// 배치: Street 씬 Crosswalk_Sound 오브젝트에 붙인다. 소리는 그 자리에서 난다.
using UnityEngine;

public class CrosswalkBeep : MonoBehaviour
{
    float wait;

    void Start() => wait = Bal.G("Traffic_CrosswalkFirstSec", 9f);

    void Update()
    {
        wait -= Time.deltaTime;
        if (wait > 0f) return;
        wait = Random.Range(Bal.G("Traffic_CrosswalkGapMin", 22f), Bal.G("Traffic_CrosswalkGapMax", 38f));
        if (PlayerController.I == null || PlayerController.I.transform.position.z <= Bal.G("Traffic_HearMinZ", 24f)) return;
        AudioManager.I.Play("crosswalk_beep", transform.position, Bal.G("Traffic_CrosswalkVolume", 0.45f));
    }
}
