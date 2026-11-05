using UnityEngine;

// 시안. 어르신 손끝을 키오스크 화면 같은 목표점에 대는 두 뼈 IK. 기본은 꺼 둔다.
// Animation Rigging 패키지 없이 Animator 뒤(LateUpdate)에서 어깨 아래 두 뼈만 돌린다.
// 뼈 이름은 Art3D 인물 Quaternius 리그 기준 UpperArm.R, LowerArm.R, Palm.R.
public class NpcHandIK : MonoBehaviour
{
    public Transform target;
    public string upperName = "UpperArm.R";
    public string lowerName = "LowerArm.R";
    public string handName = "Palm.R";
    public Vector3 bendHint = new Vector3(0.4f, -1f, -0.2f);   // 팔꿈치가 향할 쪽, 몸 기준
    public float handLength = 0.14f;                           // 손목에서 손끝까지
    [Range(0f, 1f)] public float weight = 1f;

    Transform upper, lower, hand;

    void Awake() => FindBones();

    public void FindBones()
    {
        upper = lower = hand = null;
        foreach (var t in GetComponentsInChildren<Transform>())
        {
            if (!upper && t.name == upperName) upper = t;
            if (!lower && t.name == lowerName) lower = t;
            if (!hand && t.name == handName) hand = t;
        }
    }

    void LateUpdate()
    {
        if (target) Solve(target.position, weight);
    }

    // 에디터 캡처에서도 부른다
    public void Solve(Vector3 tip, float w)
    {
        if (!upper) FindBones();
        if (!upper || !lower || !hand || w <= 0f) return;

        var a = upper.position;
        float la = Vector3.Distance(a, lower.position);
        float lb = Vector3.Distance(lower.position, hand.position);

        // 손끝이 목표에 닿도록 손목 목표는 어깨 쪽으로 손 길이만큼 물린다
        var toTip = tip - a;
        var wrist = tip - toTip.normalized * handLength;
        var to = wrist - a;
        float dist = Mathf.Clamp(to.magnitude, Mathf.Abs(la - lb) + 0.001f, la + lb - 0.001f);
        var dir = to.normalized;

        var hint = transform.TransformDirection(bendHint);
        var side = Vector3.ProjectOnPlane(hint, dir).normalized;
        float cosA = (la * la + dist * dist - lb * lb) / (2f * la * dist);
        float angA = Mathf.Acos(Mathf.Clamp(cosA, -1f, 1f));
        var elbow = a + (dir * Mathf.Cos(angA) + side * Mathf.Sin(angA)) * la;

        var upperTurn = Quaternion.FromToRotation(lower.position - a, elbow - a);
        upper.rotation = Quaternion.Slerp(Quaternion.identity, upperTurn, w) * upper.rotation;

        var lowerTurn = Quaternion.FromToRotation(hand.position - lower.position, a + dir * dist - lower.position);
        lower.rotation = Quaternion.Slerp(Quaternion.identity, lowerTurn, w) * lower.rotation;

        var handTurn = Quaternion.FromToRotation(hand.up, (tip - hand.position).normalized);
        hand.rotation = Quaternion.Slerp(Quaternion.identity, handTurn, w) * hand.rotation;
    }
}
