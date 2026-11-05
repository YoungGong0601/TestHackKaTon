// 큰길을 지나가는 차와 오토바이 한 대. 한쪽 끝에서 나와 반대쪽 끝으로 지나가고 틈을 두고 다시 나온다.
// 차선 z와 높이는 씬에 놓은 위치를 그대로 쓴다. 움직임은 HTML판 street.js의 traffic과 같다.
// 배치: PH_Car, PH_Scooter 인스턴스 루트에 붙인다. 진행 방향 회전은 씬에서 준다(앞이 +X, 반대 차선은 Y 180).
// 배치: visual = 자식 Visual
// 배치: dir = 1이면 +X로 달리는 정류장 쪽 차선, -1이면 건너편 차선
// 배치: order = 시작 순서 (0부터, 뒤일수록 늦게 나온다)
// 배치: scooter = 오토바이면 켬 (소리, 속도, 시작 시간이 달라진다)
using System.Collections.Generic;
using UnityEngine;

public class TrafficMover : MonoBehaviour
{
    public static bool BusBusy;

    static readonly List<TrafficMover> All = new();

    [SerializeField] GameObject visual;
    [SerializeField] int dir = 1;
    [SerializeField] int order;
    [SerializeField] bool scooter;

    float wait, speed;
    bool moving, heard;

    float X => transform.position.x;

    void Awake()
    {
        visual.SetActive(false);
        BusBusy = false;
        wait = scooter
            ? Bal.G("Traffic_ScooterFirstSec", 5f)
            : Bal.G("Traffic_FirstSec", 1f) + order * Random.Range(Bal.G("Traffic_FirstGapMin", 2f), Bal.G("Traffic_FirstGapMax", 5f));
    }

    void OnEnable() => All.Add(this);

    void OnDisable() => All.Remove(this);

    // 정류장 쪽 차선에 버스 길을 막는 차가 없으면 true
    public static bool LaneClear(float stopX)
    {
        float from = -Bal.G("Traffic_LaneCheckX", 110f), to = stopX + Bal.G("Traffic_LaneCheckPast", 8f);
        foreach (var c in All)
            if (c.dir > 0 && c.moving && c.X > from && c.X < to) return false;
        return true;
    }

    void Update()
    {
        if (!moving)
        {
            wait -= Time.deltaTime;
            if (wait > 0f) return;
            if (dir > 0 && BusBusy) { wait = Bal.G("Traffic_BusRetrySec", 3f); return; }
            Launch();
            return;
        }

        var p = transform.position;
        p.x += dir * speed * Time.deltaTime;
        transform.position = p;
        Listen();
        if (Mathf.Abs(p.x) > Bal.G("Traffic_EndX", 130f))
        {
            moving = false;
            visual.SetActive(false);
            wait = Random.Range(Bal.G("Traffic_GapMin", 2f), Bal.G("Traffic_GapMax", 11f));
        }
    }

    void Launch()
    {
        speed = scooter ? Bal.G("Traffic_ScooterSpeed", 12f) : Random.Range(Bal.G("Traffic_CarSpeedMin", 8.8f), Bal.G("Traffic_CarSpeedMax", 11f));
        var p = transform.position;
        p.x = -dir * Bal.G("Traffic_StartX", 125f);
        transform.position = p;
        moving = true;
        heard = false;
        visual.SetActive(true);
    }

    // 플레이어 곁을 지날 때 한 번, 진행 방향 앞쪽에서 소리를 낸다
    void Listen()
    {
        if (heard || PlayerController.I == null) return;
        Vector3 me = PlayerController.I.transform.position;
        if (Mathf.Abs(X - me.x) >= Bal.G("Traffic_HearDist", 26f) || me.z <= Bal.G("Traffic_HearMinZ", 24f)) return;
        heard = true;
        var pos = new Vector3(X + dir * Bal.G("Traffic_SoundLead", 14f), 0.6f, transform.position.z);
        if (scooter) AudioManager.I.Play("scooter_pass", pos, Bal.G("Traffic_ScooterVolume", 0.5f));
        else AudioManager.I.Play("car_pass", pos, Bal.G("Traffic_CarVolume", 0.55f));
    }
}
