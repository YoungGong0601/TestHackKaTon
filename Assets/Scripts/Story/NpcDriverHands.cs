// 앉은 기사의 두 팔을 운전대 쪽으로 든다. 앉기 자세 위에 뼈 회전을 더한다.
// 배치: 기사 NPC 루트(NpcPose 와 같은 오브젝트)에 부착
using System.Collections.Generic;
using UnityEngine;

public class NpcDriverHands : MonoBehaviour
{
    readonly List<Transform> upper = new(), lower = new();

    void Start()
    {
        foreach (var t in GetComponentsInChildren<Transform>())
        {
            if (t.name == "UpperArm.L" || t.name == "UpperArm.R") upper.Add(t);
            if (t.name == "LowerArm.L" || t.name == "LowerArm.R") lower.Add(t);
        }
    }

    void LateUpdate()
    {
        float up = Bal.G("Bus_DriverArmUpper", 40f), low = Bal.G("Bus_DriverArmLower", 32f);
        foreach (var t in upper) t.Rotate(transform.right, -up, Space.World);
        foreach (var t in lower) t.Rotate(transform.right, -low, Space.World);
    }
}
