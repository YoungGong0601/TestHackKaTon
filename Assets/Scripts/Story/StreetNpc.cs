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
    float nod, glance;

    public Vector3 HeadPos => head.position;

    void Awake() => headRest = head.localRotation;

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
        Face(world);
        while (transform.position != world)
        {
            transform.position = Vector3.MoveTowards(transform.position, world, speed * Time.deltaTime);
            yield return null;
        }
    }
}
