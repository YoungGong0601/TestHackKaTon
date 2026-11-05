using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
using UnityEngine.SceneManagement;
using static DressKit;

// 1번 몫: 새 인물을 PH_NPC 에 더하고, 매장 손님 모습과 포스터 인쇄면을 입힌다. 다시 돌려도 된다.
public static class DressStore
{
    const string Prefabs = "Assets/Graybox/PH/";
    const string Npc = "Assets/Graybox/Npc/";

    // 순서가 곧 look 번호다. 0~8 은 프리팹에 있고 9 어르신, 10 카페 직원, 11 신입 사원, 12~14 행인이다
    static readonly string[] Added = { "NpcElder", "NpcCafeStaff", "NpcRookie", "NpcClerkWoman", "NpcAjummaB", "NpcStudentB" };

    public static void All()
    {
        Art3DTools.Apply();   // 배치 모드에서는 새 FBX 의 재질이 자동으로 연결되지 않는다
        People();
        Printed();
        foreach (var name in new[] { "R1_Store", "R4_Store" })
        {
            var s = Open(name);
            // 할아버지 모습(5)은 어르신 장면과 겹쳐 손님에게 쓰지 않는다
            Wear(s, "NPCs/NPC_SeatOld", 13);
            Wear(s, "NPCs/NPC_Wait2", 12);
            Wear(s, "NPCs/NPC_Queue4", 14);
            if (name == "R1_Store") Elder(s);
            else Blur(s);
            // 화장실 문과 겹치지 않게 벽의 키오스크 포스터 위로 옮긴다. 그 인쇄물의 글자는 Readable 이 아니라 80대에도 읽히기 때문이다
            var poster = Find(s, "Room/PH_Poster");
            poster.position = new Vector3(0.75f, 2.28f, poster.position.z);
            poster.localScale = Vector3.one * 0.9f;
            Keep(poster);
            Save(s);
        }
        // 비워 두면 이름 해시로 고르고 인물 수에 따라 바뀐다. 손님이 어르신이나 직원이 되지 않게 전부 정한다
        var cafe = Open("R2_Cafe");
        Wear(cafe, "NPCs/NPC_Staff", 10);
        Wear(cafe, "NPCs/NPC_Cook", 10);
        Rookie(cafe);
        string[] guests = { "Queue0", "Queue1", "Queue2", "Queue3", "Queue4", "Wait0", "Wait1", "Wait2", "Eater" };
        int[] looks = { 0, 12, 6, 4, 14, 13, 2, 3, 1 };
        for (int i = 0; i < guests.Length; i++) Wear(cafe, "NPCs/NPC_" + guests[i], looks[i]);
        Save(cafe);
        Corridor();
    }

    // 문을 열면 보이는 복도가 비어 있어 이웃집 문과 생활 소품을 둔다. 집 안 벽지가 복도 쪽으로 드러난 문 둘레도 덮는다
    static void Corridor()
    {
        var s = Open("R1_Home");
        var old = s.GetRootGameObjects().FirstOrDefault(g => g.name == "CorridorProps");
        if (old != null) Object.DestroyImmediate(old);
        var root = new GameObject("CorridorProps").transform;
        const float Floor = -0.135f, Rail = 3.72f;
        var door = Find(s, "PH_Door_Home");
        foreach (var part in new[] { door.Find("Visual").GetChild(0), door.Find("Hinge").GetChild(0) })
            foreach (var x in new[] { -6.6f, -3.3f, 3.3f, 6.6f })
            {
                var go = (GameObject)PrefabUtility.InstantiatePrefab(PrefabUtility.GetCorrespondingObjectFromOriginalSource(part.gameObject), root);
                go.transform.SetPositionAndRotation(part.position + new Vector3(x, 0f, 0.1f), part.rotation);   // 우리 집 문은 벽(z 2.47)보다 안쪽이다
                go.transform.localScale = part.lossyScale;
            }
        Prop(root, "Models/Store/StorePlant.fbx", new Vector3(-1.35f, Floor, Rail), 30f);
        Prop(root, "Models/Store/StorePlant.fbx", new Vector3(4.6f, Floor, Rail), 200f);
        Prop(root, "Models/Vehicles/Bicycle.fbx", new Vector3(2.0f, Floor, Rail + 0.03f), 90f);
        Prop(root, "Models/Store/StoreExtinguisher.fbx", new Vector3(1.5f, Floor, 2.68f), 180f);
        var wall = AssetDatabase.LoadAssetAtPath<Material>(Art + "Materials/M_Tile_LayoutHome_CorridorWall.mat");
        Panel(root, wall, new Vector3(-0.8f, 1.19f, 2.48f), new Vector3(0.56f, 2.66f, 0.01f));
        Panel(root, wall, new Vector3(0.8f, 1.19f, 2.48f), new Vector3(0.56f, 2.66f, 0.01f));
        Panel(root, wall, new Vector3(0f, 2.275f, 2.48f), new Vector3(1.04f, 0.49f, 0.01f));
        Save(s);
    }

    static void Prop(Transform root, string model, Vector3 pos, float yaw) =>
        Place(new Item { model = model, name = Path.GetFileNameWithoutExtension(model) }, root, pos, Quaternion.Euler(0f, yaw, 0f));

    static void Panel(Transform root, Material mat, Vector3 pos, Vector3 size)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = "DoorWall";
        Object.DestroyImmediate(go.GetComponent<Collider>());
        go.transform.SetParent(root, false);
        go.transform.position = pos;
        go.transform.localScale = size;
        go.GetComponent<Renderer>().sharedMaterial = mat;
    }

    static void Wear(Scene s, string path, int look)
    {
        var t = Find(s, path);
        if (t == null) return;
        t.GetComponent<NpcPose>().look = look;
        Keep(t.GetComponent<NpcPose>());
    }

    // NPC_Rookie 는 프리팹 연결이 풀린 복사본이라 PH_NPC 의 새 모습이 없다. 모델을 직접 붙이고 그 순서를 쓴다
    static void Rookie(Scene s)
    {
        var t = Find(s, "NPCs/NPC_Rookie");
        var visual = t.Find("ReactPivot/Visual");
        if (visual.Find("NpcRookie") == null) Add(visual, "NpcRookie", s);
        t.GetComponent<NpcPose>().look = visual.Find("NpcRookie").GetSiblingIndex();
    }

    // 키오스크 앞 어르신. 서 있기만 하면 뻣뻣해 화면을 두드리게 하고, 4회차 주인공과 같은 사람이라 지팡이를 짚는다
    static void Elder(Scene s)
    {
        Wear(s, "NPCs/NPC_Elder", 9);
        var elder = Find(s, "NPCs/NPC_Elder");
        var pose = elder.GetComponent<NpcPose>();
        pose.pose = "Tap";
        Keep(pose);
        Off(s, "NPCs/NPC_Elder/ReactPivot/Arm_Pivot");   // 지폐 넣는 동작을 뺐고 몸에 제 팔이 있다
        var pivot = elder.Find("ReactPivot");
        if (pivot.Find("PH_Cane") != null) return;
        var cane = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Prefabs + "PH_Cane.prefab"), pivot);
        cane.transform.localPosition = new Vector3(-0.28f, 0f, 0.12f);   // Tap 은 오른손이라 왼쪽에 둔다
        var bottom = cane.GetComponentsInChildren<Renderer>().Min(r => r.bounds.min.y);
        cane.transform.position += Vector3.up * (elder.position.y - bottom);
    }

    // 4회차 글씨는 돋보기 없이 번진다. 구운 글씨도 SignBlur 레이어로 옮긴다(Docs/BLUR_LIST.md). 간판은 번지지 않는다
    static void Blur(Scene s)
    {
        foreach (var r in s.GetRootGameObjects().SelectMany(g => g.GetComponentsInChildren<Renderer>(true)))
            if (Regex.IsMatch(r.name, @"^(StoreMenuBoard_Panel\w|StorePosters_\w+_Print|PH_Kiosk__(WingL|WingR|Cover))$") || (r.name == "Paper" && r.transform.parent.parent.name == "Wing_R2"))
            {
                r.gameObject.layer = LayerMask.NameToLayer("SignBlur");
                Keep(r.gameObject);
            }
    }

    static void People()
    {
        var path = Prefabs + "PH_NPC.prefab";
        var root = PrefabUtility.LoadPrefabContents(path);
        try
        {
            var visual = root.transform.Find("ReactPivot/Visual");
            foreach (var asset in Added)
            {
                if (visual.Find(asset) != null) continue;
                if (Add(visual, asset, root.scene) == null) return;   // 번호가 밀리면 안 되니 더 넣지 않는다
            }
            PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally { PrefabUtility.UnloadPrefabContents(root); }
    }

    static GameObject Add(Transform visual, string asset, Scene scene)
    {
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "Models/Characters/" + asset + ".fbx");
        if (model == null)
        {
            Warn("모델 없음 " + asset);
            return null;
        }
        var go = (GameObject)PrefabUtility.InstantiatePrefab(model, scene);
        go.name = asset;
        go.transform.SetParent(visual, false);
        go.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);   // 리깅 FBX 는 -Z 를 본다
        var animator = go.AddComponent<Animator>();
        animator.runtimeAnimatorController = Controller(asset);
        animator.applyRootMotion = false;
        Phone(go, asset);
        foreach (var t in go.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = visual.gameObject.layer;
        go.SetActive(false);
        return go;
    }

    // 상태 이름으로 CrossFade 한다. 클립 경로가 모델마다 달라 컨트롤러도 모델마다 만든다. JWBuild.NpcController 와 같은 규칙이다
    static AnimatorController Controller(string asset)
    {
        var path = Npc + asset + ".controller";
        var old = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
        if (old != null) return old;
        var clips = AssetDatabase.LoadAllAssetsAtPath(Art + "Models/Characters/" + asset + ".fbx").OfType<AnimationClip>()
            .Where(c => !c.name.StartsWith("__preview__")).ToDictionary(c => c.name.Split('|').Last());
        bool rig62 = clips.ContainsKey("Idle_Neutral");
        if (rig62)   // 62본 Idle 은 다리가 벌어진 자세다
        {
            clips["Idle"] = clips["Idle_Neutral"];
            clips.Remove("Idle_Neutral");
            clips["Tap"] = clips["PointScreen"];
        }
        var controller = AnimatorController.CreateAnimatorControllerAtPath(path);
        var machine = controller.layers[0].stateMachine;
        foreach (var c in clips.OrderBy(p => p.Key != "Idle"))   // 처음 넣은 Idle 이 기본 상태
        {
            var state = machine.AddState(c.Key);
            state.motion = c.Value;
            if (c.Key == "Walk" && !rig62) state.speed = 0.8f;   // 31본 보폭이 게임 속도보다 빠르다
        }
        return controller;
    }

    static void Phone(GameObject go, string asset)
    {
        var grip = go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == asset + "_Socket_PhoneGrip");
        if (grip == null) return;   // 62본은 내장 폰을 쓴다
        // 소켓 스케일이 비균일해 부모 뼈에 붙이고, 정적 FBX 와 축이 달라 회전을 보정한다
        var phone = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Art + "Models/Characters/NpcSmartphone.fbx"), go.scene);
        phone.name = asset + "_Phone";
        phone.transform.SetParent(grip.parent, false);
        phone.transform.localPosition = grip.localPosition;
        phone.transform.localRotation = grip.localRotation * new Quaternion(0f, 0.70710678f, -0.70710678f, 0f);
    }

    // 글자는 Readable 이 그리니 판에 인쇄면만 입힌다
    static void Printed()
    {
        var path = Art + "Materials/M_PH_Poster_Paper.mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null)
        {
            m = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            AssetDatabase.CreateAsset(m, path);
        }
        m.SetTexture("_BaseMap", AssetDatabase.LoadAssetAtPath<Texture2D>(Art + "Textures/PH_Poster/T_PH_Poster_Paper.png"));
        m.SetFloat("_Smoothness", 0.25f);
        EditorUtility.SetDirty(m);
        var file = Prefabs + "PH_Poster.prefab";
        var root = PrefabUtility.LoadPrefabContents(file);
        try
        {
            root.transform.Find("Visual/Panel").GetComponent<Renderer>().sharedMaterial = m;
            PrefabUtility.SaveAsPrefabAsset(root, file);
        }
        finally { PrefabUtility.UnloadPrefabContents(root); }
    }
}
