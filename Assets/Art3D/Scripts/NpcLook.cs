using UnityEngine;

// PH_NPC 는 14명이 한 프리팹을 쓴다. Visual 아래 모습 중 하나만 켜서 서로 다르게 보이게 한다.
// look 이 -1 이면 이름으로 고른다. 직원처럼 정해진 사람은 인스펙터에서 번호를 넣는다 (순서는 PH_Map.json).
public class NpcLook : MonoBehaviour
{
    public Transform[] visuals; // ReactPivot/Visual, HeadPivot/Visual
    public int look = -1;

    void Awake()
    {
        if (visuals == null || visuals.Length == 0 || visuals[0].childCount == 0) return;
        int n = visuals[0].childCount;
        int pick = look >= 0 ? look % n : (Animator.StringToHash(name + transform.GetSiblingIndex()) & int.MaxValue) % n;
        foreach (var v in visuals)
            for (int i = 0; i < v.childCount; i++)
                v.GetChild(i).gameObject.SetActive(i == pick);
    }
}
