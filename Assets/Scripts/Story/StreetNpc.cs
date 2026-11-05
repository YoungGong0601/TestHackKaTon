// 정류장 행인 한 명의 걷기와 고개 동작.
// 배치: StreetNpc는 씬의 PH_NPC 인스턴스 루트(Student, Worker)에 붙인다.
// 배치: head = PH_NPC 의 HeadPivot (Visual 밖 앵커, 머리 모델은 그 아래 Visual에 넣는다)
using System.Collections;
using UnityEngine;

public class StreetNpc : MonoBehaviour
{
    const float NodDamp = 2.6f, GlanceDamp = 1.6f;
    const float NodDeg = 22.9f, GlanceDeg = 28.6f;   // HTML 0.4 rad, 0.5 rad

    [SerializeField] Transform head;

    Quaternion headRest;
    float nod, glance, stepAcc, pace;
    Transform bone;

    public Vector3 HeadPos => head.position;
    public bool Walking { get; private set; }

    void Awake() => headRest = head.localRotation;

    void Start()
    {
        foreach (var t in GetComponentsInChildren<Transform>())   // 켜진 모델만 돈다
            if (t.name == "Head") { bone = t; break; }
    }

    // Animator 가 뼈를 놓은 뒤에 HeadPivot 회전을 머리뼈에 얹는다. 뼈 축이 모델마다 달라 루트 기준으로 곱한다
    void LateUpdate()
    {
        if (bone) bone.rotation = head.rotation * Quaternion.Inverse(transform.rotation) * bone.rotation;
    }

    void Update()
    {
        nod = Mathf.Lerp(nod, 0f, 1f - Mathf.Exp(-NodDamp * Time.deltaTime));
        glance = Mathf.Lerp(glance, 0f, 1f - Mathf.Exp(-GlanceDamp * Time.deltaTime));
        head.localRotation = headRest * Quaternion.Euler(
            Mathf.Sin(nod * Mathf.PI) * NodDeg, Mathf.Sin(glance * Mathf.PI) * GlanceDeg, 0f);
    }

    public void Nod() => nod = 1f;
    public void Glance() => glance = 1f;

    public void Face(Vector3 world)
    {
        Vector3 d = world - transform.position;
        d.y = 0f;
        if (d.sqrMagnitude > 0.0001f) transform.rotation = Quaternion.LookRotation(d);
    }

    public IEnumerator WalkTo(Vector3 world, float speed)
    {
        world.y = transform.position.y;
        Walking = true;
        float blend = Mathf.Max(Bal.G("Npc_BlendSec", 0.25f), 0.01f);
        while (transform.position != world)
        {
            float dt = Time.deltaTime;
            Vector3 d = world - transform.position;
            // 출발은 서서히, 도착 앞에서는 줄이고, 방향은 돌면서 맞춘다
            pace = Mathf.MoveTowards(pace, Mathf.Min(speed, Mathf.Max(0.2f, d.magnitude / blend)), speed / blend * dt);
            if (d.sqrMagnitude > 0.0001f) transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(d), 1f - Mathf.Exp(-8f * dt));
            transform.position = Vector3.MoveTowards(transform.position, world, pace * dt);
            AudioManager.I.Footstep(transform.position, pace * dt, ref stepAcc);
            yield return null;
        }
        Walking = false;
    }
}
