// 거리 행인이 두 지점을 왕복한다. 걷는 자세는 NpcPose가 튼다.
// 배치: Dress 프리팹의 Npc_Walk 루트(NpcMover와 같이). a, b = 씬 좌표 왕복 끝. 시작은 a
using UnityEngine;

[RequireComponent(typeof(NpcMover))]
public class NpcPatrol : MonoBehaviour
{
    public Vector3 a, b;

    NpcMover mover;

    void Start()
    {
        mover = GetComponent<NpcMover>();
        Next(b);
    }

    void Next(Vector3 to) => mover.Go(to, Bal.G("Npc_PatrolSpeed", 1.1f), () => Next(to == a ? b : a));
}
