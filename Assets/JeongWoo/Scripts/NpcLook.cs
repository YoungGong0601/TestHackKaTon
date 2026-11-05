using UnityEngine;

// PH_NPC 는 14명이 한 프리팹을 쓴다. Visual 아래 리깅 모습 중 하나만 남기고, 서 있으면 pose, 걸으면 Walk 상태를 튼다.
// look 이 -1 이면 이름으로 고른다. 직원처럼 정해진 사람은 인스펙터에서 번호를 넣는다 (순서는 PH_Map.json).
public class NpcLook : MonoBehaviour
{
    public Transform[] visuals; // ReactPivot/Visual, HeadPivot/Visual
    public int look = -1;
    public string pose = "Idle";

    Animator anim;
    NpcMover mover;
    StreetNpc street;
    string now;

    void Awake()
    {
        if (visuals == null || visuals.Length == 0 || visuals[0].childCount == 0) return;
        int n = visuals[0].childCount;
        int pick = look >= 0 ? look % n : (Animator.StringToHash(name + transform.GetSiblingIndex()) & int.MaxValue) % n;
        var model = visuals[0].GetChild(pick);
        foreach (var v in visuals)
            for (int i = 0; i < v.childCount; i++)
            {
                var child = v.GetChild(i).gameObject;
                child.SetActive(i == pick);
                if (i != pick) Destroy(child);
            }
        anim = model.GetComponent<Animator>();
        mover = GetComponent<NpcMover>();
        street = GetComponent<StreetNpc>();
        foreach (var t in model.GetComponentsInChildren<Transform>(true))
            if (t.name.EndsWith("_Phone")) t.gameObject.SetActive(pose.Contains("Phone"));
    }

    void OnEnable() => now = null;   // SetActive 로 켜면 Animator 가 기본 상태로 돌아간다

    void Update()
    {
        if (!anim) return;
        string want = mover.Walking || street.Walking ? "Walk" : pose;
        if (want == now) return;
        if (now == null) anim.Play(want, 0, Random.value);   // 같은 자세 손님이 같이 움직이지 않게
        else anim.CrossFadeInFixedTime(want, 0.25f);
        now = want;
    }
}
