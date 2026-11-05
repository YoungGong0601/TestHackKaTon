using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;
using static DressKit;

// 버스와 차가 달리는 도로를 끝까지 잇고 공사 안내판 앞에 라바콘을 둔다. 다시 돌려도 된다.
// 연장분은 Env 프리팹 하나로 묶어 씬에는 인스턴스 하나만 들어간다.
public static class DressStreetEnds
{
    const float BuildingGap = 12f;   // 건물 줄은 도로 끝보다 이만큼 앞에서 멈춘다

    public static void All()
    {
        var env = Find(Open("R1_Stop"), "Env");   // Open 이 씬을 통째로 바꾸니 묶음은 그 뒤에 만든다
        var root = Root("Env_StopEnds");
        Extend(env, root, -152f, 197f);
        Cones(root);
        SaveEnv(root);
        foreach (var name in new[] { "R1_Stop", "R4_Stop" })
        {
            var s = Open(name);
            PutEnv(s, "Env_StopEnds");
            // 도로 한가운데 선 고층 건물로 끝을 막는다. 버스가 파고들지 않게 앞면을 도착점 너머로 민다
            Face(Find(s, "Env/BuildingBackdrop_4"), -140f, true);
            Face(Find(s, "Env/BuildingBackdrop_5"), 185f, false);
            Save(s);
        }

        env = Find(Open("R1_Storefront"), "Env");
        root = Root("Env_StorefrontEnds");
        Extend(env, root, -140f, 140f);
        SaveEnv(root);
        foreach (var name in new[] { "R1_Storefront", "R4_Storefront" })
        {
            var s = Open(name);
            PutEnv(s, "Env_StorefrontEnds");
            Save(s);
        }
    }

    static void Extend(Transform env, Transform root, float lo, float hi)
    {
        foreach (var row in Rows(env, @"^(Street)?(Road|Curb|Sidewalk)(Far)?[EW]?\d*$", 3)) Tile(row, root, 12f, lo, hi);
        foreach (var row in Rows(env, @"^(Street)?UtilityPole\d*$", 2)) Tile(row, root, 25f, lo, hi);
        foreach (var row in Rows(env, @"^(Street)?Wires\d*$", 2)) Tile(row, root, 25f, lo, hi - 25f);   // 전선은 자기 전주에서 +X 로 뻗는다
        foreach (var row in Rows(env, @"^StreetLight$", 3)) Tile(row, root, 25f, lo, hi);
        foreach (var row in Rows(env, @"^(Building(Villa|Salon|RealEstate|ShopRow)|Neighbor\w+|Far(Salon|RealEstate)|ShopRow\d)$", 3))
        {
            Buildings(row.Reverse(), root, row.Min(t => Box(t).min.x), lo + BuildingGap, -1f);
            Buildings(row, root, row.Max(t => Box(t).max.x), hi - BuildingGap, 1f);
        }
    }

    // 한 줄(같은 z)의 물건을 x 순서로
    static IEnumerable<Transform[]> Rows(Transform env, string pattern, int min) =>
        env.Cast<Transform>().Where(t => Regex.IsMatch(t.name, pattern))
            .GroupBy(t => Mathf.Round(t.position.z * 10f)).Where(g => g.Count() >= min)
            .Select(g => g.OrderBy(t => t.position.x).ToArray());

    static void Tile(Transform[] row, Transform root, float step, float lo, float hi)
    {
        for (float x = row[0].position.x - step; x >= lo; x -= step) Copy(row[0], root, x);
        for (float x = row[^1].position.x + step; x <= hi; x += step) Copy(row[^1], root, x);
    }

    // 폭이 제각각이라 앞 건물 끝에 이어 붙인다. 있는 건물을 돌아가며 쓴다
    static void Buildings(IEnumerable<Transform> order, Transform root, float edge, float limit, float dir)
    {
        var cycle = order.ToArray();
        for (int i = 0; (limit - edge) * dir > 0f; i++)
        {
            var t = cycle[i % cycle.Length];
            var b = Box(t);
            Copy(t, root, edge + dir * b.extents.x + t.position.x - b.center.x);
            edge += dir * b.size.x;
        }
    }

    static void Copy(Transform t, Transform root, float x)
    {
        var go = (GameObject)PrefabUtility.InstantiatePrefab(PrefabUtility.GetCorrespondingObjectFromSource(t.gameObject), root);
        go.name = t.name;
        go.transform.SetPositionAndRotation(new Vector3(x, t.position.y, t.position.z), t.rotation);
        go.transform.localScale = t.lossyScale;
    }

    static Bounds Box(Transform t)
    {
        var rs = t.GetComponentsInChildren<Renderer>();
        var b = rs[0].bounds;
        foreach (var r in rs) b.Encapsulate(r.bounds);
        return b;
    }

    static void Face(Transform t, float x, bool east)
    {
        var b = Box(t);
        t.position += Vector3.right * (x - (east ? b.max.x : b.min.x));
        Keep(t);
    }

    // 안내판의 플레이어 쪽에 한 줄. 동쪽 줄은 z 33.8 위로 행인이 지나가니 비운다
    static void Cones(Transform root)
    {
        var cone = new Item { model = "Models/Street/StreetTrafficCone.fbx", name = "Cone" };
        float[] yaw = { 8f, -14f, 21f, -5f, 13f };
        int i = 0;
        foreach (var p in new[] {
            new Vector3(-8.3f, 0f, 31.5f), new Vector3(-8.3f, 0f, 32.5f), new Vector3(-8.3f, 0f, 33.5f), new Vector3(-8.3f, 0f, 34.5f),
            new Vector3(40.3f, 0f, 31.4f), new Vector3(40.3f, 0f, 32.3f), new Vector3(40.3f, 0f, 33.2f) })
            Place(cone, root, p, Quaternion.Euler(0f, yaw[i++ % yaw.Length], 0f));
        Blocker(root, "Col_Cones_W", new Vector3(-8.3f, 1f, 33f), new Vector3(0.4f, 2f, 3.4f));
        Blocker(root, "Col_Cones_E", new Vector3(40.3f, 1f, 32.3f), new Vector3(0.4f, 2f, 2.2f));
    }
}
