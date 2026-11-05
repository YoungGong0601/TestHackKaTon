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
    const float AlleyDepth = 3f;     // 건물 사이 틈을 정면에서 이만큼 안쪽에서 막는다

    // 벽 폭과 옥상 높이 (Buildings/*.py 의 W, HT). 렌더러 경계는 실외기까지 넣어 실제보다 넓다
    static readonly Dictionary<string, Vector2> Hull = new()
    {
        ["BuildingShopRow"] = new(15f, 9.8f), ["BuildingSalon"] = new(11.5f, 9.85f),
        ["BuildingRealEstate"] = new(12f, 12.6f), ["BuildingVilla"] = new(12.2f, 11.6f),
    };

    public static void All()
    {
        var env = Find(Open("R1_Stop"), "Env");   // Open 이 씬을 통째로 바꾸니 묶음은 그 뒤에 만든다
        var root = Root("Env_StopEnds");
        Extend(env, root, -152f, 197f);
        Clear(env, root);
        Alleys(env, root);
        Cones(root);
        SaveEnv(root);
        foreach (var name in new[] { "R1_Stop", "R4_Stop" })
        {
            var s = Open(name);
            PutEnv(s, "Env_StopEnds");
            Slots(Find(s, "Env/Close_Street"));
            // 도로 한가운데 선 고층 건물로 끝을 막는다. 버스가 파고들지 않게 앞면을 도착점 너머로 민다
            Face(Find(s, "Env/BuildingBackdrop_4"), -140f, true);
            Face(Find(s, "Env/BuildingBackdrop_5"), 185f, false);
            Save(s);
        }

        env = Find(Open("R1_Storefront"), "Env");
        root = Root("Env_StorefrontEnds");
        Extend(env, root, -140f, 140f);
        Clear(env, root);
        Alleys(env, root);
        SaveEnv(root);
        foreach (var name in new[] { "R1_Storefront", "R4_Storefront" })
        {
            var s = Open(name);
            PutEnv(s, "Env_StorefrontEnds");
            Slots(Find(s, "Env/Close_Street"));
            Off(s, "Environment/Building_Upper", "Environment/Store_Ceiling");   // 옆 건물 정면, 매장 천장과 같은 면에서 지글거린다
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

    // 친구가 Close_Street 에 먼저 세운 자리는 비운다. 겹치면 면이 지글거리고 건물이 서로를 뚫는다
    static void Clear(Transform env, Transform root)
    {
        var taken = env.Find("Close_Street").Cast<Transform>().Where(t => t.GetComponentInChildren<Renderer>()).ToArray();
        foreach (var t in root.Cast<Transform>().ToArray())
            if (taken.Any(o => Clash(o, t))) Object.DestroyImmediate(t.gameObject);
    }

    // 같은 자리의 같은 모델(도로 판은 납작해 높이로 못 가른다)과 서로 뚫는 건물만 친다. 전선은 경계 상자가 길어 쉽게 걸린다
    static bool Clash(Transform a, Transform b)
    {
        Bounds p = Box(a), q = Box(b);
        Mesh m = a.GetComponentInChildren<MeshFilter>().sharedMesh, n = b.GetComponentInChildren<MeshFilter>().sharedMesh;
        if (m == n && (p.center - q.center).sqrMagnitude < 0.01f) return true;
        var d = Vector3.Min(p.max, q.max) - Vector3.Max(p.min, q.min);
        return Hull.ContainsKey(m.name) && Hull.ContainsKey(n.name) && d.x > 0.5f && d.z > 0.5f;
    }

    // Close_Street 는 프리팹이 풀린 복사본이라 FBX 를 다시 내보내면 재질 순서가 어긋난다. 모델 순서로 맞춘다
    static void Slots(Transform street)
    {
        foreach (var r in street.GetComponentsInChildren<MeshRenderer>(true))
        {
            var mesh = r.GetComponent<MeshFilter>().sharedMesh;
            var model = AssetDatabase.LoadAssetAtPath<GameObject>(AssetDatabase.GetAssetPath(mesh));
            var source = model ? model.GetComponentsInChildren<MeshRenderer>(true).FirstOrDefault(m => m.GetComponent<MeshFilter>().sharedMesh == mesh) : null;
            if (source) r.sharedMaterials = source.sharedMaterials;
        }
    }

    // 건물 사이 좁은 틈으로 하늘이 세로 띠로 비친다. 낮은 쪽 옥상 높이까지 벽으로 막는다
    public static void Alleys(Transform env, Transform root)
    {
        foreach (var old in root.Cast<Transform>().Where(t => t.name == "AlleyWall").ToArray()) Object.DestroyImmediate(old.gameObject);
        var plaster = AssetDatabase.LoadAssetAtPath<Material>(Art + "Materials/M_Tile_Buildings_Plaster.mat");
        var hulls = env.GetComponentsInChildren<MeshFilter>().Concat(root.GetComponentsInChildren<MeshFilter>()).Distinct()
            .Where(f => f.sharedMesh && Hull.ContainsKey(f.sharedMesh.name));
        foreach (var row in hulls.GroupBy(f => (Mathf.RoundToInt(f.transform.eulerAngles.y / 90f) % 4, Mathf.RoundToInt(Vector3.Dot(f.transform.position, f.transform.forward) / 3f))))
        {
            var line = row.OrderBy(f => Vector3.Dot(f.transform.position, f.transform.right)).ToArray();
            foreach (var (a, b) in line.Zip(line.Skip(1), (a, b) => (a, b)))
            {
                var t = a.transform;
                var (ha, hb) = (Hull[a.sharedMesh.name], Hull[b.sharedMesh.name]);
                float lo = Vector3.Dot(t.position, t.right) + ha.x / 2f, hi = Vector3.Dot(b.transform.position, t.right) - hb.x / 2f;
                if (hi - lo < 0.02f || hi - lo > 2f) continue;
                float top = Mathf.Min(ha.y, hb.y);
                var wall = GameObject.CreatePrimitive(PrimitiveType.Cube);
                wall.name = "AlleyWall";
                wall.transform.SetParent(root, true);
                wall.transform.SetPositionAndRotation(
                    t.right * ((lo + hi) / 2f) + t.forward * (Vector3.Dot(t.position, t.forward) - AlleyDepth) + Vector3.up * (t.position.y + top / 2f - 0.25f), t.rotation);
                wall.transform.localScale = new Vector3(hi - lo + 0.8f, top + 0.45f, 0.1f);   // 양쪽 벽 안으로 넣는다. R1, R4 건물 위치가 조금 다르다
                wall.GetComponent<Renderer>().sharedMaterial = plaster;
            }
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
