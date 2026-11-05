// 캡슐 플레이스홀더용 단순 이동. PH_NPC 루트에 부착한다. 물리 없이 transform만 움직인다.
// 걷는 동안 앞을 막는 다른 손님과 플레이어는 옆으로 돌아 지나간다. 막혀서 못 가면 Npc_StuckSec 뒤 그 자리에서 도착으로 친다.
// 배치: bag = ReactPivot 자식 BagAnchor (꺼진 상태, 봉투 모델은 그 아래 Visual에 넣는다)
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class NpcMover : MonoBehaviour
{
    [SerializeField] GameObject bag;

    static readonly List<NpcMover> everyone = new List<NpcMover>();

    bool walking;
    int token;
    Vector3 target;
    float speed;
    Action onArrive;
    readonly Queue<Vector3> route = new Queue<Vector3>();
    Vector3 heading;
    int side;
    float bestDist, stuck;
    StreetNpc look;

    bool turning;
    float wantYaw, turnRate = 8f;

    public bool Walking => walking;

    void OnEnable() => everyone.Add(this);
    void OnDisable() => everyone.Remove(this);

    /// <summary>새 이동을 시작한다. 이전 이동은 취소되고 그 콜백은 불리지 않는다.</summary>
    public void Go(Vector3 world, float walkSpeed, Action arrive = null)
    {
        token++;
        route.Clear();
        SetTarget(world);
        speed = walkSpeed;
        onArrive = arrive;
        walking = true;
        turning = false;
    }

    /// <summary>via를 차례로 지나 world로 간다.</summary>
    public void GoVia(IEnumerable<Transform> via, Vector3 world, float walkSpeed, Action arrive = null)
    {
        Go(world, walkSpeed, arrive);
        foreach (Transform t in via) route.Enqueue(t.position);
        if (route.Count == 0) return;
        route.Enqueue(world);
        SetTarget(route.Dequeue());
    }

    void SetTarget(Vector3 world)
    {
        target = world;
        target.y = transform.position.y;
        bestDist = float.MaxValue;
        stuck = 0f;
        side = 0;
    }

    public IEnumerator WalkTo(Vector3 world, float walkSpeed)
    {
        Go(world, walkSpeed);
        int mine = token;
        while (walking && token == mine) yield return null;
    }

    public void Stop()
    {
        token++;
        walking = false;
        onArrive = null;
        route.Clear();
    }

    public void Face(Vector3 world, float rate = 8f)
    {
        Vector3 d = world - transform.position;
        if (d.x * d.x + d.z * d.z < 0.0001f) return;
        FaceYaw(Mathf.Atan2(d.x, d.z) * Mathf.Rad2Deg, rate);
    }

    public void FaceYaw(float yaw, float rate = 8f)
    {
        wantYaw = yaw;
        turnRate = rate;
        turning = true;
    }

    public void Place(Vector3 world)
    {
        Stop();
        world.y = transform.position.y;
        transform.position = world;
    }

    public void Show()
    {
        gameObject.SetActive(true);
    }

    public void Hide()
    {
        Stop();
        turning = false;
        if (bag) bag.SetActive(false);
        gameObject.SetActive(false);
    }

    public void ShowBag()
    {
        if (bag) bag.SetActive(true);
    }

    /// <summary>사과 반응: 몸은 그대로 두고 고개만 움직인다. nod면 끄덕, 아니면 살짝 돌린다.</summary>
    public void React(bool nod)
    {
        if (!look) look = GetComponent<StreetNpc>();
        if (!look) return;
        if (nod) look.Nod();
        else look.Glance();
    }

    void Update()
    {
        float dt = Time.deltaTime;

        if (walking)
        {
            Vector3 p = transform.position;
            Vector3 d = target - p;
            d.y = 0f;
            float dist = d.magnitude;
            if (dist < bestDist - 0.005f)
            {
                bestDist = dist;
                stuck = 0f;
            }
            else
            {
                stuck += dt;
            }

            bool passing = route.Count > 0;
            if (dist < (passing ? 0.3f : 0.05f) || stuck > Bal.G("Npc_StuckSec", 2.5f))
            {
                if (passing)
                {
                    SetTarget(route.Dequeue());
                }
                else
                {
                    walking = false;
                    Action a = onArrive;
                    onArrive = null;
                    a?.Invoke();
                }
            }
            else
            {
                heading = Steer(p, d / dist);
                Vector3 step = Block(p, heading * Mathf.Min(dist, speed * dt));
                transform.position = p + step;
                TurnToward(Mathf.Atan2(heading.x, heading.z) * Mathf.Rad2Deg, 8f, dt);
            }
        }

        if (turning && !walking)
        {
            TurnToward(wantYaw, turnRate, dt);
            if (Mathf.Abs(Mathf.DeltaAngle(transform.eulerAngles.y, wantYaw)) < 0.5f) turning = false;
        }
    }

    // 앞길에 가장 가까운 사람을 고르고, 그 사람을 Npc_AvoidGap만큼 비켜 지나가도록 방향을 꺾는다
    Vector3 Steer(Vector3 p, Vector3 dir)
    {
        float reach = Bal.G("Npc_AvoidLook", 1.2f), gap = Bal.G("Npc_AvoidGap", 0.62f);
        var right = new Vector3(dir.z, 0f, -dir.x);
        float along = reach, lateral = 0f;
        bool hit = false;

        foreach (NpcMover o in everyone)
        {
            if (o == this) continue;
            if (o.walking && Vector3.Dot(o.heading, dir) > 0.5f) continue;   // 같은 쪽으로 가는 사람은 따라간다
            Consider(o.transform.position - p, dir, right, gap, ref along, ref lateral, ref hit);
        }
        if (PlayerController.I) Consider(PlayerController.I.transform.position - p, dir, right, gap, ref along, ref lateral, ref hit);

        if (!hit)
        {
            side = 0;
            return dir;
        }
        if (side == 0) side = lateral > 0f ? -1 : 1;   // 상대가 오른쪽이면 왼쪽으로
        float shift = side * gap + lateral;
        if (shift * side <= 0f) return dir;
        float k = Mathf.Clamp(shift / Mathf.Max(along, 0.2f), -2f, 2f);
        return (dir + right * k).normalized;
    }

    static void Consider(Vector3 to, Vector3 dir, Vector3 right, float gap, ref float along, ref float lateral, ref bool hit)
    {
        to.y = 0f;
        float a = Vector3.Dot(to, dir);
        if (a <= 0.01f || a >= along) return;
        float l = Vector3.Dot(to, right);
        if (Mathf.Abs(l) >= gap) return;
        along = a;
        lateral = l;
        hit = true;
    }

    // 사람 쪽으로 더 다가가는 성분만 지운다. 이미 겹친 상태에서 멀어지는 걸음은 막지 않는다
    Vector3 Block(Vector3 p, Vector3 step)
    {
        float min = Bal.G("Npc_MinGap", 0.5f);
        foreach (NpcMover o in everyone)
            if (o != this) step = BlockOne(o.transform.position - p, step, min);
        if (PlayerController.I) step = BlockOne(PlayerController.I.transform.position - p, step, min);
        return step;
    }

    static Vector3 BlockOne(Vector3 to, Vector3 step, float min)
    {
        to.y = 0f;
        float dist = to.magnitude;
        if (dist < 1e-4f || dist > min + step.magnitude) return step;
        Vector3 n = to / dist;
        float toward = Vector3.Dot(step, n);
        return toward > 0f ? step - n * toward : step;
    }

    void TurnToward(float yaw, float rate, float dt)
    {
        float y = transform.eulerAngles.y;
        y += Mathf.DeltaAngle(y, yaw) * Mathf.Min(1f, dt * rate);
        transform.rotation = Quaternion.Euler(0f, y, 0f);
    }
}

/// <summary>Promise.race(작업, wait(초))에 해당. 시간이 다 되면 작업을 끊는다.</summary>
public static class StoreFlow
{
    public static IEnumerator Race(MonoBehaviour host, IEnumerator work, float sec)
    {
        bool done = false;
        Coroutine c = host.StartCoroutine(Pump(work, () => done = true));
        float t = 0f;
        while (!done && t < sec)
        {
            t += Time.deltaTime;
            yield return null;
        }
        if (!done) host.StopCoroutine(c);
    }

    static IEnumerator Pump(IEnumerator work, Action done)
    {
        while (work.MoveNext()) yield return work.Current;
        done();
    }

    /// <summary>three.js 쪽 damp와 같은 지수 감쇠.</summary>
    public static float Damp(float a, float b, float k, float dt)
    {
        return a + (b - a) * (1f - Mathf.Exp(-k * dt));
    }
}
