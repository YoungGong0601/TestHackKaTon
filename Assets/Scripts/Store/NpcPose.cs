using UnityEngine;

// PH_NPC 자세. 서 있으면 pose, 걸으면 Walk 상태를 튼다. 정우 사본 NpcLook과 같은 동작이고, 이름은 Art3D의 NpcLook과 겹치지 않게 다르다.
// 배치: PH_NPC 인스턴스 루트에 부착. pose = Idle, Phone, Watch, Impatient, SitIdle, SitPhone, Tap
// 배치: visuals = ReactPivot/Visual, HeadPivot/Visual. 비워 두면 모습은 고르지 않고 켜져 있는 모델의 Animator를 쓴다(Art3D NpcLook과 같이 쓸 때)
// look 이 -1 이면 이름으로 고른다. 직원처럼 정해진 사람은 인스펙터에서 번호를 넣는다
public class NpcPose : MonoBehaviour
{
    public Transform[] visuals;
    public int look = -1;
    public string pose = "Idle";

    Animator anim;
    NpcMover mover;
    StreetNpc street;
    string now;

    void Awake()
    {
        mover = GetComponent<NpcMover>();
        street = GetComponent<StreetNpc>();
        if (visuals == null || visuals.Length == 0 || visuals[0].childCount == 0) return;
        int n = visuals[0].childCount;
        int pick = look >= 0 ? look % n : (Animator.StringToHash(name + transform.GetSiblingIndex()) & int.MaxValue) % n;
        // 할아버지 모델은 1회차 어르신만 쓴다. 이름으로 고를 때는 건너뛴다
        if (look < 0 && visuals[0].GetChild(pick).name == "NpcOldMan") pick = (pick + 1) % n;
        var model = visuals[0].GetChild(pick);
        foreach (var v in visuals)
            for (int i = 0; i < v.childCount; i++)
            {
                var child = v.GetChild(i).gameObject;
                child.SetActive(i == pick);
                if (i != pick) Destroy(child);
            }
        Bind(model);
    }

    // NpcLook이 모습을 고른 뒤에 켜진 모델을 잡는다
    void Start()
    {
        if (anim) return;
        var found = GetComponentInChildren<Animator>();
        if (found) Bind(found.transform);
    }

    void Bind(Transform model)
    {
        anim = model.GetComponent<Animator>();
        foreach (var t in model.GetComponentsInChildren<Transform>(true))
            if (t.name.EndsWith("_Phone")) t.gameObject.SetActive(pose.Contains("Phone"));
    }

    void OnEnable() => now = null;   // SetActive 로 켜면 Animator 가 기본 상태로 돌아간다

    void Update()
    {
        if (!anim) return;
        bool walking = (mover && mover.Walking) || (street && street.Walking);
        string want = walking ? "Walk" : pose;
        if (want == now) return;
        if (now == null) anim.Play(want, 0, Random.value);   // 같은 자세 손님이 같이 움직이지 않게
        else anim.CrossFadeInFixedTime(want, Bal.G("Npc_BlendSec", 0.25f));
        now = want;
    }
}
