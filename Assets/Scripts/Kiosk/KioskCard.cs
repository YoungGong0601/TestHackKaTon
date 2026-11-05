// 틈으로 들어가는 카드 모습.
// 배치: visual = Card 자식 Visual(평소 꺼짐, 스케일 1). 움직이는 것은 이 오브젝트이고 Visual은 켜고 끄기만 한다
using UnityEngine;

public class KioskCard : MonoBehaviour
{
    public enum Move { In, Out, Bounce }

    [SerializeField] GameObject visual;

    Move move;
    Vector3 slotPos, outward;
    float t;
    bool on;

    public void At(Transform slot, Vector3 outDir, Move m)
    {
        slotPos = slot.position; outward = outDir; move = m; t = 0f; on = true;
        transform.rotation = slot.rotation;
        if (visual) visual.SetActive(true);
    }

    public void Hide()
    {
        on = false;
        if (visual) visual.SetActive(false);
    }

    void Update()
    {
        if (!on || !visual) return;
        t += Time.deltaTime;
        float d;
        float depth = Bal.G("Kiosk_CardDepth", -0.02f);   // 틈 앞면 기준 카드 중심 자리. 음수면 틈 안쪽
        if (move == Move.In) d = Mathf.Lerp(0.075f, depth, Mathf.Clamp01(t / 0.35f));
        else if (move == Move.Out)
        {
            d = Mathf.Lerp(depth, 0.135f, Mathf.Clamp01(t / 0.42f));
            if (t > 0.42f) Hide();
        }
        else
        {
            d = 0.08f - Mathf.Sin(Mathf.Clamp01(t / 0.5f) * Mathf.PI) * 0.042f;
            if (t > 0.5f) Hide();
        }
        transform.position = slotPos + outward * d;
    }
}
