// IC 틈을 가린 포스터. 클릭하면 경첩으로 들춰지고 콜라이더가 꺼져 뒤의 틈이 눌린다.
// 배치: hinge = 회전 축 오브젝트, hit = 포스터 콜라이더
using UnityEngine;

public class PosterFlap : MonoBehaviour
{
    [SerializeField] Transform hinge;
    [SerializeField] Collider hit;

    float target, value;
    public bool Opened => target > 0f;

    public void Open() { target = 1f; if (hit) hit.enabled = false; }
    public void Close() { target = 0f; if (hit) hit.enabled = true; }

    void Update()
    {
        value = Mathf.MoveTowards(value, target, Time.deltaTime * Bal.G("Kiosk_PosterSpeed", 4f));
        if (hinge) hinge.localRotation = Quaternion.Euler(0f, value * Bal.G("Kiosk_PosterAngle", 146.1f), 0f);
    }
}
