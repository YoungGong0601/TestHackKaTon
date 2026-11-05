// 4-10b: 키오스크 앞 사람들의 고개가 플레이어를 따라 돈다. 임시 T24
using System.Collections.Generic;
using UnityEngine;

public class R4Gaze : MonoBehaviour
{
    readonly List<Transform> heads = new List<Transform>();
    readonly List<NpcMover> bodies = new List<NpcMover>();

    public void Add(NpcMover npc)
    {
        Transform head = FindHead(npc.transform);
        if (!head) return;
        heads.Add(head);
        bodies.Add(npc);
    }

    static Transform FindHead(Transform t)
    {
        if (t.name == "HeadPivot") return t;
        foreach (Transform c in t)
        {
            Transform hit = FindHead(c);
            if (hit) return hit;
        }
        return null;
    }

    void LateUpdate()
    {
        if (heads.Count == 0 || !PlayerController.I) return;
        Vector3 eye = PlayerController.I.EyePos;
        float k = 1f - Mathf.Exp(-Bal.G("R4_GazeTurn", 5f) * Time.deltaTime);
        for (int i = 0; i < heads.Count; i++)
        {
            if (!bodies[i] || !bodies[i].isActiveAndEnabled) continue;
            if (!bodies[i].Walking) bodies[i].Face(PlayerController.I.transform.position, Bal.G("R4_GazeBodyTurn", 1.2f));
            Vector3 d = eye - heads[i].position;
            if (d.sqrMagnitude > 0.01f) heads[i].rotation = Quaternion.Slerp(heads[i].rotation, Quaternion.LookRotation(d), k);
        }
    }
}
