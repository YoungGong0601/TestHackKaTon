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

// R 씬에 3D 를 입히는 공용 도구. 사본의 JWDress 도구를 옮겼다. 여러 컴퓨터가 함께 쓰니 고치지 말고 자기 파일(Dress<씬묶음>.cs)에서 부른다.
// 배경은 Assets/Art3D/Env 프리팹으로 묶고 씬에는 인스턴스 하나만 둔다. 씬 파일 변경을 줄이려는 것이다.
// 레이아웃 좌표: Store, Storefront, Street 는 Unity = (bx, bz, by), Y = 180 - rotZ (Pos, Yaw). Home 은 Unity = (-bx, bz, -by), Y = -rotZ.
public static class DressKit
{
    public const string Art = "Assets/Art3D/";
    public const string Env = Art + "Env/";

#pragma warning disable 0649
    [Serializable] public class Layout { public Item[] items; public LightDef[] lights; }
    [Serializable] public class Item { public string model, name; public float[] pos, rotXYZ; public float rotZ; public string[] hide; }
    [Serializable] public class LightDef { public string name, type; public float[] pos, dir, color; public float intensity, range, spotAngle; public bool shadows; }
#pragma warning restore 0649

    public static Layout Read(string name) => JsonUtility.FromJson<Layout>(File.ReadAllText("Assets/JeongWoo/Layouts/" + name + ".json"));

    public static Scene Open(string name) => EditorSceneManager.OpenScene("Assets/Scenes/" + name + ".unity", OpenSceneMode.Single);

    public static void Save(Scene s)
    {
        EditorSceneManager.MarkSceneDirty(s);
        EditorSceneManager.SaveScene(s);
    }

    public static void Warn(string text) => Debug.LogWarning("꾸미기: " + text);

    // 프리팹 인스턴스는 기록하지 않으면 다시 열 때 값이 사라진다
    public static void Keep(Object o)
    {
        if (PrefabUtility.IsPartOfPrefabInstance(o)) PrefabUtility.RecordPrefabInstancePropertyModifications(o);
    }

    public static Transform Find(Scene s, string path)
    {
        var parts = path.Split(new[] { '/' }, 2);
        foreach (var r in s.GetRootGameObjects())
        {
            if (r.name != parts[0]) continue;
            var t = parts.Length == 1 ? r.transform : r.transform.Find(parts[1]);
            if (t != null) return t;
        }
        Warn($"{s.name} 에 {path} 없음");
        return null;
    }

    // 회색 메시만 끈다. 콜라이더는 Visual 밖이라 살아 있다
    public static void Off(Scene s, params string[] paths)
    {
        foreach (var p in paths)
        {
            var t = Find(s, p + "/Visual");
            if (t == null) continue;
            t.gameObject.SetActive(false);
            Keep(t.gameObject);
        }
    }

    public static void Move(Scene s, string path, Vector3 pos)
    {
        var t = Find(s, path);
        if (t == null) return;
        t.position = pos;
        Keep(t);
    }

    // PH_NPC 인스턴스의 모습 번호. 순서는 PH_Map*.json 의 look 이다
    public static void Look(Scene s, string path, int look)
    {
        var t = Find(s, path);
        if (t == null) return;
        var c = t.GetComponent<NpcLook>();
        if (c == null) { Warn(path + " 에 NpcLook 없음"); return; }
        c.look = look;
        Keep(c);
    }

    // 프리팹 메뉴가 닿지 않는 씬 전용 자리(Bus3, Walker, Watcher, Arm_Pivot, Tray_Pass 등)에 모델을 넣는다.
    // 자리의 자식을 지우고 넣으며 다시 돌려도 된다. clear 가 false 면 더한다. 프리팹 인스턴스 안의 자식은 지울 수 없으니 그런 자리는 Off 를 쓴다
    public static GameObject Model(Scene s, string path, string model, bool clear = true)
    {
        var t = Find(s, path);
        if (t == null) return null;
        var gray = t.GetComponentInChildren<MeshRenderer>(true);
        var shadows = gray != null ? gray.shadowCastingMode : ShadowCastingMode.On;
        if (clear)
            for (int i = t.childCount - 1; i >= 0; i--) Object.DestroyImmediate(t.GetChild(i).gameObject);
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Art + model);
        if (asset == null) { Warn("모델 없음 " + model); return null; }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, t);
        foreach (var r in go.GetComponentsInChildren<Renderer>(true)) r.shadowCastingMode = shadows;
        foreach (var c in go.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = t.gameObject.layer;
        return go;
    }

    public static Transform Root(string name) => new GameObject(name).transform;

    public static GameObject Place(Item it, Transform parent, Vector3 pos, Quaternion rot)
    {
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Art + it.model);
        if (asset == null) { Warn("모델 없음 " + it.model); return null; }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, parent);
        go.name = it.name;
        // FBX 루트에 자기 위치가 있는 모델이 있다. 레이아웃 자리는 그 위에 얹는 값이다
        go.transform.SetPositionAndRotation(pos + rot * asset.transform.localPosition, rot * asset.transform.localRotation);
        if (it.hide != null && it.hide.Length > 0)
            foreach (var t in go.GetComponentsInChildren<Transform>(true))
                if (it.hide.Contains(t.name)) t.gameObject.SetActive(false);
        return go;
    }

    public static Vector3 Pos(Item it) => new(it.pos[0], it.pos[2], it.pos[1]);
    public static Quaternion Yaw(Item it) => Quaternion.Euler(0f, 180f - it.rotZ, 0f);

    // Root 로 만든 묶음을 Assets/Art3D/Env/<이름>.prefab 으로 저장하고 임시 오브젝트를 지운다
    public static void SaveEnv(Transform root)
    {
        PrefabUtility.SaveAsPrefabAsset(root.gameObject, Env + root.name + ".prefab");
        Object.DestroyImmediate(root.gameObject);
    }

    // 씬에 Env 프리팹 인스턴스 하나를 둔다. 다시 돌려도 하나만 남는다
    public static GameObject PutEnv(Scene s, string name, Vector3 pos = default)
    {
        var old = s.GetRootGameObjects().FirstOrDefault(g => g.name == name);
        if (old != null) Object.DestroyImmediate(old);
        var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Env + name + ".prefab");
        if (asset == null) { Warn("Env 프리팹 없음 " + name); return null; }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, s);
        go.transform.position = pos;
        return go;
    }

    // 보이지 않는 상자. 모델 전체 크기로 만든다
    public static void Solid(GameObject go)
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
    public static void Pole(GameObject go, float width = 0.3f)
    {
        var col = go.AddComponent<BoxCollider>();
        col.center = Vector3.up;
        col.size = new Vector3(width, 2f, width);
    }

    public static void Blocker(Transform parent, string name, Vector3 center, Vector3 size)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        go.transform.position = center;
        go.AddComponent<BoxCollider>().size = size;
    }

    public static void LayoutLights(Transform parent, IEnumerable<LightDef> defs)
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

    public static Material Sky() => AssetDatabase.LoadAssetAtPath<Material>(Env + "Sky_Overcast.mat");
    public static Material Fence() => AssetDatabase.LoadAssetAtPath<Material>(Env + "Fence_Construction.mat");

    // 씬 하나를 눈으로 볼 수 있게 플레이 없이 PNG 로 찍는다. 카메라는 위치와 바라보는 곳을 준다
    public static void Shot(Scene s, Vector3 from, Vector3 to, string png, int w = 1280, int h = 720)
    {
        var go = new GameObject("DressKitShot");
        SceneManager.MoveGameObjectToScene(go, s);
        var cam = go.AddComponent<Camera>();
        cam.transform.SetPositionAndRotation(from, Quaternion.LookRotation(to - from));
        cam.fieldOfView = 66f;
        var rt = new RenderTexture(w, h, 24);
        cam.targetTexture = rt;
        cam.Render();
        RenderTexture.active = rt;
        var tex = new Texture2D(w, h, TextureFormat.RGB24, false);
        tex.ReadPixels(new Rect(0, 0, w, h), 0, 0);
        File.WriteAllBytes(png, tex.EncodeToPNG());
        RenderTexture.active = null;
        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(tex);
        Object.DestroyImmediate(go);
    }
}
