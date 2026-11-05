using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

// 사본 씬을 Layouts/*.json(Blender 배치)대로 꾸민다. 움직이는 물체와 콜라이더는 씬의 것을 그대로 쓰고 모델은 보이기만 한다.
// 유리선 안쪽은 Store 씬, 바깥은 Storefront 씬이 그린다. 두 씬은 문을 지날 때 같이 떠 있다.
// 좌표: Store, Storefront, Street 는 Unity = (bx, bz, by), Y = 180 - rotZ. Home 은 Unity = (-bx, bz, -by), Y = -rotZ.
static class JWDress
{
    const string Root = "Assets/JeongWoo/";
    const string Art = "Assets/Art3D/";
    const string Mats = Root + "Graybox/Materials/";

#pragma warning disable 0649
    [Serializable] class Layout { public Item[] items; public LightDef[] lights; }
    [Serializable] class Item { public string model, name; public float[] pos, rotXYZ; public float rotZ; public string[] hide; }
    [Serializable] class LightDef { public string name, type; public float[] pos, dir, color; public float intensity, range, spotAngle; public bool shadows; }
#pragma warning restore 0649

    public static void All()
    {
        Home();
        Street();
        Bus();
        Storefront();
        Store();
    }

    // ── 도구 ──

    static Layout Read(string name) => JsonUtility.FromJson<Layout>(File.ReadAllText(Root + "Layouts/" + name + ".json"));

    static Scene Open(string name) => EditorSceneManager.OpenScene(Root + "Scenes/" + name + ".unity", OpenSceneMode.Single);

    static void Save(Scene s)
    {
        EditorSceneManager.MarkSceneDirty(s);
        EditorSceneManager.SaveScene(s);
    }

    // 프리팹 인스턴스는 기록하지 않으면 다시 열 때 값이 사라진다
    static void Keep(Object o)
    {
        if (PrefabUtility.IsPartOfPrefabInstance(o)) PrefabUtility.RecordPrefabInstancePropertyModifications(o);
    }

    static Transform Find(Scene s, string path)
    {
        var parts = path.Split(new[] { '/' }, 2);
        foreach (var r in s.GetRootGameObjects())
        {
            if (r.name != parts[0]) continue;
            var t = parts.Length == 1 ? r.transform : r.transform.Find(parts[1]);
            if (t != null) return t;
        }
        JWBuild.Warn($"{s.name} 에 {path} 없음");
        return null;
    }

    // 회색 메시만 끈다. 콜라이더는 Visual 밖이라 살아 있다
    static void Off(Scene s, params string[] paths)
    {
        foreach (var p in paths)
        {
            var t = Find(s, p + "/Visual");
            if (t == null) continue;
            t.gameObject.SetActive(false);
            Keep(t.gameObject);
        }
    }

    static void ShadowOnly(Scene s, params string[] paths)
    {
        foreach (var p in paths)
        {
            var t = Find(s, p);
            if (t == null) continue;
            var r = t.GetComponent<Renderer>();
            r.shadowCastingMode = ShadowCastingMode.ShadowsOnly;
            Keep(r);
        }
    }

    static void Move(Scene s, string path, Vector3 pos)
    {
        var t = Find(s, path);
        if (t == null) return;
        t.position = pos;
        Keep(t);
    }

    static void Npc(Scene s, string path, int look, string pose)
    {
        var t = Find(s, path);
        if (t == null) return;
        var c = t.GetComponent<NpcLook>();
        c.look = look;
        c.pose = pose;
        Keep(c);
    }

    static Transform Group(Scene s, string name, Transform parent = null)
    {
        var old = parent != null ? parent.Find(name)?.gameObject : s.GetRootGameObjects().FirstOrDefault(g => g.name == name);
        if (old != null) Object.DestroyImmediate(old);
        var go = new GameObject(name);
        SceneManager.MoveGameObjectToScene(go, s);
        if (parent != null) go.transform.SetParent(parent, false);
        return go.transform;
    }

    static GameObject Place(Item it, Transform parent, Vector3 pos, Quaternion rot)
    {
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Art + it.model);
        if (asset == null)
        {
            JWBuild.Warn("모델 없음 " + it.model);
            return null;
        }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, parent);
        go.name = it.name;
        // FBX 루트에 자기 위치가 있는 모델이 있다. 레이아웃 자리는 그 위에 얹는 값이다
        go.transform.SetPositionAndRotation(pos + rot * asset.transform.localPosition, rot * asset.transform.localRotation);
        if (it.hide != null && it.hide.Length > 0)
            foreach (var t in go.GetComponentsInChildren<Transform>(true))
                if (it.hide.Contains(t.name)) t.gameObject.SetActive(false);
        return go;
    }

    static Vector3 Pos(Item it) => new(it.pos[0], it.pos[2], it.pos[1]);
    static Quaternion Yaw(Item it) => Quaternion.Euler(0f, 180f - it.rotZ, 0f);

    // 보이지 않는 상자. 모델 전체 크기로 만든다
    static void Solid(GameObject go)
    {
        var inv = go.transform.worldToLocalMatrix;
        var b = new Bounds();
        bool first = true;
        foreach (var f in go.GetComponentsInChildren<MeshFilter>(true))
        {
            if (f.sharedMesh == null) continue;
            var m = inv * f.transform.localToWorldMatrix;
            var mb = f.sharedMesh.bounds;
            for (int i = 0; i < 8; i++)
            {
                var c = mb.center + Vector3.Scale(mb.extents, new Vector3((i & 1) * 2 - 1, (i >> 1 & 1) * 2 - 1, (i >> 2 & 1) * 2 - 1));
                var p = m.MultiplyPoint3x4(c);
                if (first) b = new Bounds(p, Vector3.zero);
                else b.Encapsulate(p);
                first = false;
            }
        }
        var col = go.AddComponent<BoxCollider>();
        col.center = b.center;
        col.size = b.size;
    }

    // 기둥처럼 아래만 막는 상자
    static void Pole(GameObject go, float width = 0.3f)
    {
        var col = go.AddComponent<BoxCollider>();
        col.center = Vector3.up;
        col.size = new Vector3(width, 2f, width);
    }

    static void Blocker(Transform parent, string name, Vector3 center, Vector3 size)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.position = center;
        go.AddComponent<BoxCollider>().size = size;
    }

    static void LayoutLights(Transform parent, IEnumerable<LightDef> defs)
    {
        foreach (var d in defs)
        {
            var go = new GameObject(d.name);
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3(d.pos[0], d.pos[2], d.pos[1]);
            var l = go.AddComponent<Light>();
            l.type = d.type == "Spot" ? LightType.Spot : LightType.Point;
            if (l.type == LightType.Spot)
            {
                go.transform.rotation = Quaternion.LookRotation(new Vector3(d.dir[0], d.dir[2], d.dir[1]), Vector3.forward);
                l.spotAngle = d.spotAngle;
            }
            l.color = new Color(d.color[0], d.color[1], d.color[2]);
            l.intensity = d.intensity;
            l.range = d.range;
            l.shadows = d.shadows ? LightShadows.Soft : LightShadows.None;
        }
    }

    static Light SetLight(Transform t, Vector3? pos, Vector3? dir, float intensity, float range, float spot, Color color, bool shadows)
    {
        var l = t.GetComponent<Light>();
        if (pos.HasValue) t.position = pos.Value;
        if (dir.HasValue) t.rotation = Quaternion.LookRotation(dir.Value, Vector3.forward);
        l.intensity = intensity;
        if (range > 0f) l.range = range;
        if (spot > 0f) l.spotAngle = spot;
        l.color = color;
        l.shadows = shadows ? LightShadows.Soft : LightShadows.None;
        return l;
    }

    static Transform NewLight(Transform parent, string name, LightType type)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.AddComponent<Light>().type = type;
        return go.transform;
    }

    static void Probe(Transform parent, Vector3 pos, Vector3 size, Vector3 center, bool box, int res = 128)
    {
        var go = new GameObject("ReflectionProbe");
        go.transform.SetParent(parent, false);
        go.transform.position = pos;
        var p = go.AddComponent<ReflectionProbe>();
        p.mode = ReflectionProbeMode.Realtime;
        p.refreshMode = ReflectionProbeRefreshMode.OnAwake;
        p.timeSlicingMode = ReflectionProbeTimeSlicingMode.NoTimeSlicing;
        p.size = size;
        p.center = center;
        p.boxProjection = box;
        p.resolution = res;
    }

    static Material Sky()
    {
        const string path = Mats + "Sky_Overcast.mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null)
        {
            m = new Material(AssetDatabase.LoadAssetAtPath<Material>(Mats + "Sky_Gray.mat"));
            AssetDatabase.CreateAsset(m, path);
        }
        m.SetTexture("_MainTex", AssetDatabase.LoadAssetAtPath<Texture>(Mats + "sky_overcast.jpg"));
        m.SetColor("_Tint", new Color(0.5f, 0.5f, 0.5f));
        m.SetFloat("_Exposure", 1f);
        EditorUtility.SetDirty(m);
        return m;
    }

    static void Fog(FogMode mode, Color color, float density, float start = 0f, float end = 0f)
    {
        RenderSettings.fog = true;
        RenderSettings.fogMode = mode;
        RenderSettings.fogColor = color;
        RenderSettings.fogDensity = density;
        RenderSettings.fogStartDistance = start;
        RenderSettings.fogEndDistance = end;
    }

    // ── Home ──

    static void Home()
    {
        var s = Open("JW_Home");
        var env = Group(s, "Env");
        var skip = new HashSet<string> { "HomeDoorFrame", "HomeDoor", "HomeShoes", "HomeCane" };   // PH 프리팹이 움직이는 물체
        foreach (var it in Read("Home").items)
        {
            if (skip.Contains(it.name)) continue;
            var pos = new Vector3(-it.pos[0], it.pos[2], -it.pos[1]);
            var rot = it.rotXYZ != null && it.rotXYZ.Length == 3
                ? Quaternion.AngleAxis(-it.rotXYZ[2], Vector3.up) * Quaternion.AngleAxis(it.rotXYZ[1], Vector3.forward) * Quaternion.AngleAxis(it.rotXYZ[0], Vector3.right)
                : Quaternion.Euler(0f, -it.rotZ, 0f);
            Place(it, env, pos, rot);
        }

        Off(s, "Room/Ceiling", "Room/Wall_Left", "Room/Wall_Right", "Room/Wall_Back", "Room/Wall_Door_L", "Room/Wall_Door_R", "Room/Wall_Door_Top",
            "Room/Floor_Lino", "Room/Floor_Tile", "Room/Floor_Outside", "Room/OutsideBackdrop", "ShoeCabinet", "Bulb");

        var shoes = Find(s, "PH_ShoeRack");
        shoes.rotation = Quaternion.Euler(0f, -9.17f, 0f);
        Keep(shoes);
        var cane = Find(s, "LeanCane");
        cane.rotation = Quaternion.Euler(0f, 0f, -6.59f);
        Keep(cane);

        var lights = Find(s, "Lights");
        SetLight(lights.Find("Bulb_Spot"), new Vector3(0f, 2.2f, 1.25f), new Vector3(0f, -0.999f, -0.05f), 2.4f, 5f, 150f, new Color(1f, 0.769f, 0.529f), true);
        SetLight(lights.Find("Fill_Mid"), new Vector3(0f, 2.05f, -0.3f), null, 0.9f, 5.5f, 0f, new Color(1f, 0.722f, 0.471f), false);
        SetLight(lights.Find("Fill_Back"), new Vector3(0.2f, 1.9f, -1.9f), null, 0.6f, 4f, 0f, new Color(1f, 0.69f, 0.447f), false);
        var glow = lights.Find("DoorGlow").GetComponent<Light>();
        glow.intensity = 2.6f;
        glow.shadows = LightShadows.Soft;
        lights.Find("OutsideFill").gameObject.SetActive(false);
        foreach (var name in new[] { "WindowCool", "CorridorLamp", "CorridorSkyFill", "OvercastSun" })
        {
            var old = lights.Find(name);
            if (old != null) Object.DestroyImmediate(old.gameObject);
        }
        SetLight(NewLight(lights, "WindowCool", LightType.Point), new Vector3(0.68f, 1.78f, 1.75f), null, 0.9f, 3.2f, 0f, new Color(0.663f, 0.769f, 0.878f), false);
        SetLight(NewLight(lights, "CorridorLamp", LightType.Point), new Vector3(0f, 2.2f, 3.2f), null, 1.2f, 4.5f, 0f, new Color(0.949f, 0.945f, 0.925f), true);
        SetLight(NewLight(lights, "CorridorSkyFill", LightType.Spot), new Vector3(0f, 2f, 4.9f), new Vector3(0f, -0.305f, -0.952f), 1f, 6f, 120f, new Color(0.812f, 0.863f, 0.918f), true);
        SetLight(NewLight(lights, "OvercastSun", LightType.Directional), null, new Vector3(-0.3f, -0.841f, 0.45f), 0.8f, 0f, 0f, new Color(0.863f, 0.89f, 0.933f), true);

        Fog(FogMode.Linear, new Color(0.72f, 0.76f, 0.82f), 0.01f, 25f, 320f);
        RenderSettings.skybox = Sky();
        Probe(env, new Vector3(0f, 1.1f, 0.4f), new Vector3(1.96f, 2.45f, 5.25f), new Vector3(0f, 0f, -0.675f), true, 256);
        Save(s);
    }

    // ── Street ──

    // 큰길 모델을 parent 아래에 놓는다. Bus 씬 창밖에도 같은 거리를 쓴다
    static void StreetItems(Transform parent, bool colliders)
    {
        var skip = new HashSet<string> { "BusShelter", "BusStopBIS", "CityBus_112", "NpcStudentMan", "NpcAjumma", "NpcYoungWoman", "NpcOfficeMan", "NpcOldMan" };
        foreach (var it in Read("Street").items)
        {
            if (skip.Contains(it.name)) continue;
            if (it.name == "CarHatch" && it.pos[0] > 20f) continue;   // 건너편 차선을 달리는 차와 겹친다
            if (!colliders && it.name == "BusStopRouteMap") continue;   // 버스 창밖에는 승차대가 없어 판만 뜬다
            if (it.name == "BusStopSign") it.pos[1] = 34.85f;        // 행인 경로 밖으로
            if (it.name == "BusStopRouteMap") it.pos[1] = 32.151f;   // PH 승차대 뒷유리 앞
            if (it.name == "StreetTrashCan") it.pos[1] = 34.65f;
            var go = Place(it, parent, Pos(it), Yaw(it));
            if (go == null) continue;
            if (it.name == "StreetGround")
                foreach (var r in go.GetComponentsInChildren<Renderer>(true)) r.shadowCastingMode = ShadowCastingMode.Off;
            if (!colliders) continue;
            if (it.name is "CarSedan" or "CarHatch" or "DeliveryScooter" or "Bicycle" or "StreetTrashCan" or "StreetClothingBin") Solid(go);
            if (it.name is "StreetUtilityPole" or "StreetLight" or "BusStopSign" or "StreetBollard" or "StreetNoParking") Pole(go);
        }
    }

    static Material Fence()
    {
        const string path = Mats + "Fence_Construction.mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null)
        {
            m = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            AssetDatabase.CreateAsset(m, path);
        }
        m.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture>(Mats + "Fence_Construction.png"));
        m.SetFloat("_Smoothness", 0.2f);
        EditorUtility.SetDirty(m);
        return m;
    }

    static void StreetSun(Scene s, string path)
    {
        var sun = Find(s, path).GetComponent<Light>();
        sun.color = new Color(0.875f, 0.902f, 0.933f);
        sun.intensity = 1.15f;
    }

    static void StreetAir()
    {
        Fog(FogMode.ExponentialSquared, new Color(0.604f, 0.639f, 0.671f), 0.0125f);
        RenderSettings.ambientMode = AmbientMode.Trilight;
        RenderSettings.ambientSkyColor = new Color(0.769f, 0.808f, 0.847f);
        RenderSettings.ambientEquatorColor = new Color(0.682f, 0.714f, 0.745f);
        RenderSettings.ambientGroundColor = new Color(0.361f, 0.353f, 0.337f);
        RenderSettings.skybox = Sky();
    }

    static void Street()
    {
        var s = Open("JW_Street");
        var env = Group(s, "Env");
        StreetItems(env, true);
        Blocker(env, "Col_ShelterGlass", new Vector3(30f, 1.2f, 33.03f), new Vector3(0.1f, 2.4f, 2.16f));
        Blocker(env, "Col_ShelterAd", new Vector3(36.6f, 1.2f, 32.78f), new Vector3(0.1f, 2.4f, 1.5f));

        Off(s, "Bounds/Facade_E", "Bounds/Facade_W", "Bounds/Wall_Alley_W", "Bounds/Wall_Alley_E", "Bounds/Wall_Alley_End",
            "World/Far_Block", "World/Road_End_W", "World/Road_End_E", "World/Floor_Alley", "World/Floor_Road", "World/Floor_Sidewalk", "World/Floor_FarSidewalk");

        var fence = Fence();
        foreach (var path in new[] { "Bounds/Fence_W/Visual/Wall", "Bounds/Fence_E/Visual/Wall" })
        {
            var r = Find(s, path).GetComponent<Renderer>();
            r.sharedMaterial = fence;
            Keep(r);
        }

        // 난간 모델은 85.4m 이고 Rail_E 자리는 80.4m 다. 모델에 맞게 루트를 줄이고 콜라이더 길이는 그대로 유지한다
        var rail = Find(s, "World/Rail_E");
        rail.localScale = new Vector3(0.94145f, 1f, 1f);
        Keep(rail);
        var railBox = rail.GetComponent<BoxCollider>();
        railBox.size = new Vector3(85.4f, railBox.size.y, railBox.size.z);
        Keep(railBox);

        Npc(s, "Npcs/Student", 3, "Phone");
        Npc(s, "Npcs/Worker", 6, "Idle");

        StreetSun(s, "Directional Light");
        Find(s, "Fill Light").GetComponent<Light>().intensity = 0.2f;
        StreetAir();
        Probe(env, new Vector3(31f, 3f, 33f), new Vector3(400f, 100f, 400f), Vector3.zero, false);
        Save(s);
    }

    // ── Bus ──

    static void Bus()
    {
        var s = Open("JW_Bus");
        var outside = Group(s, "Env_Outside");
        StreetItems(outside, false);
        outside.position = new Vector3(-31.75f, 0.14f, -37f);   // 정류장이 버스 원점에 온다. 처음 창밖은 방금 탄 정류장이다

        Find(s, "Outside_Ground").GetComponent<Renderer>().enabled = false;
        foreach (var l in Find(s, "Ceiling Lights").GetComponentsInChildren<Light>()) l.intensity = 0.25f;   // 천장과 0.45m 라 0.5면 하얗게 날아간다
        var director = new SerializedObject(Find(s, "Director").GetComponent<BusDirector>());
        director.FindProperty("outside").objectReferenceValue = outside;
        director.ApplyModifiedPropertiesWithoutUndo();

        StreetSun(s, "Directional Light");
        Fog(FogMode.ExponentialSquared, new Color(0.604f, 0.639f, 0.671f), 0.0125f);
        RenderSettings.skybox = Sky();
        Save(s);
    }

    // ── Storefront, Store ──

    static readonly Color FogColor = new(0.63f, 0.65f, 0.69f);   // 하늘 사진의 지평선 색. 길 끝이 하늘로 이어진다

    static void StoreAir()
    {
        Fog(FogMode.Linear, FogColor, 0.01f, 34f, 110f);
        RenderSettings.skybox = Sky();
        RenderSettings.reflectionIntensity = 0.6f;
    }

    static bool Outside(string n) => new[] { "StorefrontFacade", "StorefrontAC", "Sidewalk", "Curb", "Road", "ShopRow", "FarSalon", "FarRealEstate", "Backdrop",
        "Neighbor", "Market", "StreetLight", "UtilityPole", "Wires", "TrashCan", "Bicycle", "DeliveryScooter", "Drain", "ParkedCar" }.Any(n.StartsWith);

    static void Storefront()
    {
        var s = Open("JW_Storefront");
        var env = Group(s, "Env");
        foreach (var it in Read("Storefront").items)
        {
            if (!Outside(it.name)) continue;
            var go = Place(it, env, Pos(it), Yaw(it));
            if (go == null) continue;
            if (it.name == "DeliveryScooter")
                foreach (var t in go.GetComponentsInChildren<Transform>(true))
                    if (t.name == "DeliveryScooter_Stand") t.localEulerAngles = new Vector3(-70f, 0f, 0f);
            if (it.name is "TrashCan" or "Bicycle" or "DeliveryScooter" or "ParkedCar") Solid(go);
            if (it.name.StartsWith("StreetLight") || it.name.StartsWith("UtilityPole")) Pole(go);
        }

        Off(s, "Environment/Building_East", "Environment/Building_West", "Environment/Shop_West", "Environment/Shop_East",
            "Environment/Across_1", "Environment/Across_2", "Environment/Across_3", "Environment/Across_4", "Environment/Street_EndWest", "Environment/Street_EndEast",
            "Environment/Floor_Sidewalk", "Environment/Floor_Road", "Environment/Floor_Store", "Environment/Store_BackWall", "Environment/Curb", "PH_Storefront");
        // 해가 매장 안으로 새지 않게 천장과 위층은 그림자만 남긴다. StoreShell 천장은 한 장 면이라 해를 못 막는다
        ShadowOnly(s, "Environment/Store_Ceiling/Visual/Wall", "Environment/Building_Upper/Visual/Wall");
        var sign = Find(s, "PH_Storefront/Sign");
        sign.gameObject.SetActive(false);
        Keep(sign.gameObject);

        // 레이아웃 보도가 씬보다 1.6m 좁다
        Move(s, "PH_Bus", new Vector3(-6f, -0.14f, -9.6f));
        Move(s, "BusStop", new Vector3(-4.3f, 0f, -7.4f));
        Move(s, "PlayerSpawn", new Vector3(-2.4f, 0f, -7.3f));
        Move(s, "Bounds/Bound_Road", new Vector3(0f, 4f, -9.075f));
        var signLook = Find(s, "PH_Storefront/Anchor_SignLook");
        signLook.localPosition = new Vector3(0.55f, 3.77f, -0.16f);
        Keep(signLook);

        Npc(s, "NPC_Eater", 2, "SitIdle");
        var eater = Find(s, "NPC_Eater/ReactPivot");
        eater.localPosition = new Vector3(-0.0073f, 0.0463f, 0.1334f);
        Keep(eater);

        var sun = Find(s, "Directional Light").GetComponent<Light>();
        sun.color = new Color(0.941f, 0.925f, 0.894f);
        SetLight(NewLight(env, "CanopyWarm", LightType.Point), new Vector3(1f, 2.6f, -5f), null, 2.2f, 5f, 0f, new Color(1f, 0.851f, 0.659f), false);
        StoreAir();
        RenderSettings.ambientEquatorColor = new Color(0.615f, 0.628f, 0.632f);
        RenderSettings.ambientGroundColor = new Color(0.38f, 0.366f, 0.342f);
        Probe(env, new Vector3(0f, 2f, -6f), new Vector3(120f, 40f, 60f), Vector3.zero, false);
        Save(s);
    }

    static void Store()
    {
        var s = Open("JW_Store");
        var lay = Read("Store");
        var shared = Group(s, "Env_Shared", Find(s, "Room"));   // 거리: 문으로 들어오면 Storefront 것이 보이므로 미리 불러올 때 꺼진다
        var inside = Group(s, "Env_Interior");
        var street = new[] { "Sidewalk", "Curb", "Road", "ShopRow", "Backdrop", "StreetLight" };
        var room = new[] { "StoreShell", "StoreKitchen", "StoreCounter", "StorePosters", "StoreMenuBoard", "Booth", "HighChair", "Plant", "TrashStation", "ExtinguisherSign", "Extinguisher", "WetFloorSign", "Tray" };
        foreach (var it in lay.items)
        {
            if (street.Any(it.name.StartsWith)) { Place(it, shared, Pos(it), Yaw(it)); continue; }
            bool tableProp = it.name.EndsWith("_Napkin") || it.name.EndsWith("_Straw");
            if (!tableProp && !room.Any(it.name.StartsWith)) continue;   // 나머지는 PH 프리팹과 NPC 가 맡는다
            if (it.name == "WetFloorSign") it.pos = new[] { -0.3f, -3.3f, 0f };   // 손님 경로 밖으로
            var go = Place(it, inside, Pos(it), Yaw(it));
            if (go == null) continue;
            if (it.name.StartsWith("HighChair") || it.name is "WetFloorSign" or "TrashStation" or "Extinguisher") Solid(go);
        }

        var director = new SerializedObject(Find(s, "Director").GetComponent<StoreDirector>());
        var list = director.FindProperty("sharedRoom");
        for (int i = list.arraySize - 1; i >= 0; i--)
            if (list.GetArrayElementAtIndex(i).objectReferenceValue == null) list.DeleteArrayElementAtIndex(i);
        list.arraySize++;
        list.GetArrayElementAtIndex(list.arraySize - 1).objectReferenceValue = shared.gameObject;
        director.ApplyModifiedPropertiesWithoutUndo();

        Off(s, "Room/Floor", "Room/Ceiling", "Room/Wall_Back", "Room/Wall_West", "Room/Wall_East", "Room/Floor_Outside",
            "Counter/Wall_Partition", "Counter/PH_Counter", "Counter/Kitchen_Bench", "Counter/Kitchen_Fryer", "Counter/Kitchen_Hood", "Counter/Bulkhead",
            "Tables/Booth0", "Tables/Booth1", "Tables/Booth2");

        foreach (var seat in new[] { "Tables/Seat0_A", "Tables/Seat1_A", "Tables/Seat2_A" })
        {
            var t = Find(s, seat);
            t.rotation = Quaternion.Euler(0f, 180f, 0f);   // PH_Seat 등받이가 +Z 라 앞줄 의자는 돌린다
            Keep(t);
        }

        // 손에 드는 영수증
        var sheet = Find(s, "Receipt_View/Visual/Sheet");
        var paper = sheet.parent.Find("PH_ReceiptSheet");
        if (paper != null) Object.DestroyImmediate(paper.gameObject);
        var model = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Art + "Models/PH/PH_ReceiptSheet.fbx"), sheet.parent);
        model.name = "PH_ReceiptSheet";
        model.transform.localPosition = sheet.localPosition;
        foreach (var t in model.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = sheet.gameObject.layer;
        foreach (var r in model.GetComponentsInChildren<Renderer>(true)) r.shadowCastingMode = ShadowCastingMode.Off;
        sheet.GetComponent<Renderer>().enabled = false;

        Npc(s, "NPCs/NPC_Staff", 8, "SitPhone");
        Npc(s, "NPCs/NPC_Cook", 8, "Idle");
        Npc(s, "NPCs/NPC_Eater", 2, "SitIdle");
        Npc(s, "NPCs/NPC_Queue0", 7, "Impatient");
        Npc(s, "NPCs/NPC_Queue1", 1, "Watch");
        Npc(s, "NPCs/NPC_Queue2", 4, "Phone");
        Npc(s, "NPCs/NPC_Queue3", 0, "Idle");
        Npc(s, "NPCs/NPC_Queue4", 2, "Idle");
        Npc(s, "NPCs/NPC_Wait0", 6, "Phone");
        Npc(s, "NPCs/NPC_Wait1", 3, "Watch");
        Npc(s, "NPCs/NPC_Wait2", 5, "Watch");
        var staff = Find(s, "NPCs/NPC_Staff");
        staff.SetPositionAndRotation(new Vector3(-3.6782f, 0.01f, 2.5228f), Quaternion.Euler(0f, 61.35f, 0f));   // 카운터 스툴
        Keep(staff);
        var cook = Find(s, "NPCs/NPC_Cook");
        cook.rotation = Quaternion.Euler(0f, 270f, 0f);
        Keep(cook);
        var eater = Find(s, "NPCs/NPC_Eater/ReactPivot");
        eater.localPosition = new Vector3(-0.0073f, 0.0463f, 0.1534f);
        Keep(eater);

        // 레이아웃에 있는 앉은 손님. 코드가 쓰지 않는 사람이라 PH_NPC 를 하나 더 놓는다
        var old = Find(s, "NPCs").Find("NPC_SeatOld");
        if (old != null) Object.DestroyImmediate(old.gameObject);
        var seated = lay.items.FirstOrDefault(i => i.name == "Seat_NpcOldMan");
        if (seated != null)
        {
            var npc = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Root + "Graybox/PH/PH_NPC.prefab"), Find(s, "NPCs"));
            npc.name = "NPC_SeatOld";
            npc.transform.SetPositionAndRotation(Pos(seated), Yaw(seated));
            Npc(s, "NPCs/NPC_SeatOld", 5, "SitIdle");
        }

        var lights = Group(s, "Lights");
        LayoutLights(lights, lay.lights.Where(l => l.type != "Directional"));
        StoreAir();
        Probe(inside, new Vector3(-0.25f, 1.5f, 0.2f), new Vector3(11.5f, 3.1f, 8f), Vector3.zero, true);
        Save(s);
    }
}
