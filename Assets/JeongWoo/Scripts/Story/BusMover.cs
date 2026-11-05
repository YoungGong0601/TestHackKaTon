// 버스 한 대의 이동과 문. 진행 판단은 StreetDirector가 한다.
// 배치: BusMover는 씬의 PH_Bus 인스턴스 루트(Bus1, Bus2)에 붙인다.
// 배치: doorLeafA = 앞문 왼쪽 문짝 (열리면 로컬 -X로 밀림)
// 배치: doorLeafB = 앞문 오른쪽 문짝 (열리면 로컬 +X로 밀림)
using System.Collections;
using UnityEngine;

public class BusMover : MonoBehaviour
{
    const float DoorSlide = 0.5f;
    const float DoorDamp = 5f;

    [SerializeField] Transform doorLeafA;
    [SerializeField] Transform doorLeafB;

    Vector3 closedA, closedB;
    float doorT, doorWant;

    void Awake()
    {
        closedA = doorLeafA.localPosition;
        closedB = doorLeafB.localPosition;
    }

    void Update()
    {
        doorT = Mathf.Lerp(doorT, doorWant, 1f - Mathf.Exp(-DoorDamp * Time.deltaTime));
        doorLeafA.localPosition = closedA + Vector3.left * (doorT * DoorSlide);
        doorLeafB.localPosition = closedB + Vector3.right * (doorT * DoorSlide);
    }

    public void Doors(bool open) => doorWant = open ? 1f : 0f;

    // 도착은 끝에서 감속, 출발은 처음에 천천히. power는 HTML판 곡선 지수.
    public IEnumerator Drive(Vector3 from, Vector3 to, float sec, float power, bool braking)
    {
        for (float t = 0f; t < 1f; t += Time.deltaTime / sec)
        {
            float k = braking ? 1f - Mathf.Pow(1f - t, power) : Mathf.Pow(t, power);
            transform.position = Vector3.LerpUnclamped(from, to, k);
            yield return null;
        }
        transform.position = to;
    }
}
