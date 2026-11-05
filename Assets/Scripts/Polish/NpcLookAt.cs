using UnityEngine;

// 시안. NPC 고개가 가까이 온 플레이어를 따라 돈다. 기본은 꺼 둔다(enabled 끔). 컨펌 뒤 PH_NPC 인스턴스에서 켠다.
// Animator 뒤(LateUpdate)에서 Head, Neck 뼈만 돌리므로 어떤 클립이든 위에 얹힌다.
// 뼈 이름 Head, Neck 은 Art3D 인물 두 리그(Quaternius HumanArmature, Character 리그) 모두에 있다.
public class NpcLookAt : MonoBehaviour
{
    public Transform target;            // 비우면 Camera.main
    public float range = 4f;
    public float maxYaw = 65f;
    public float maxPitch = 25f;
    public float turnSpeed = 5f;
    [Range(0f, 1f)] public float neckShare = 0.35f;

    Transform head, neck;
    float weight;

    void Awake() => FindBones();

    public void FindBones()
    {
        head = neck = null;
        foreach (var t in GetComponentsInChildren<Transform>())
        {
            if (!head && t.name == "Head") head = t;
            if (!neck && t.name == "Neck") neck = t;
        }
    }

    void LateUpdate()
    {
        var aim = target ? target : (Camera.main ? Camera.main.transform : null);
        if (!aim || !head) return;
        bool near = (aim.position - head.position).sqrMagnitude < range * range;
        weight = Mathf.MoveTowards(weight, near ? 1f : 0f, turnSpeed * 0.3f * Time.deltaTime);
        if (weight > 0f) Apply(aim.position, weight);
    }

    // 에디터 캡처에서도 부른다. 몸 앞 방향 기준으로 좌우, 위아래를 제한해 돌린다
    public void Apply(Vector3 point, float w)
    {
        if (!head) FindBones();
        if (!head) return;
        var body = transform;
        var local = body.InverseTransformDirection(point - head.position);
        float yaw = Mathf.Clamp(Mathf.Atan2(local.x, local.z) * Mathf.Rad2Deg, -maxYaw, maxYaw);
        float pitch = Mathf.Clamp(-Mathf.Atan2(local.y, new Vector2(local.x, local.z).magnitude) * Mathf.Rad2Deg, -maxPitch, maxPitch);
        var turn = body.rotation * Quaternion.Euler(pitch * w, yaw * w, 0f) * Quaternion.Inverse(body.rotation);
        if (neck)
        {
            var part = Quaternion.Slerp(Quaternion.identity, turn, neckShare);
            neck.rotation = part * neck.rotation;
            head.rotation = Quaternion.Slerp(Quaternion.identity, turn, 1f - neckShare) * head.rotation;
        }
        else head.rotation = turn * head.rotation;
    }
}
