using UnityEngine;

// 시안. 같은 자세 NPC가 같은 속도로 움직이지 않게 Animator 속도를 사람마다 조금 다르게 준다. 기본은 꺼 둔다.
// 시작 시점은 NpcPose가 이미 무작위로 잡으므로 여기서는 속도와 가끔 생기는 멈칫만 맡는다.
public class IdleVariation : MonoBehaviour
{
    public Vector2 speed = new Vector2(0.85f, 1.15f);
    public Vector2 driftEverySec = new Vector2(6f, 14f);

    Animator anim;
    float nextDrift;

    void OnEnable()
    {
        anim = GetComponentInChildren<Animator>();
        Pick();
    }

    void OnDisable()
    {
        if (anim) anim.speed = 1f;
    }

    void Update()
    {
        if (anim && Time.time >= nextDrift) Pick();
    }

    void Pick()
    {
        if (anim) anim.speed = Random.Range(speed.x, speed.y);
        nextDrift = Time.time + Random.Range(driftEverySec.x, driftEverySec.y);
    }
}
