using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEngine;
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
            if (name == "R1_Store") Wear(s, "NPCs/NPC_Elder", 9);
            // 화장실 문과 겹치지 않게 벽의 키오스크 포스터 위로 옮긴다. 그 인쇄물의 글자는 Readable 이 아니라 80대에도 읽히기 때문이다
            var poster = Find(s, "Room/PH_Poster");
            poster.position = new Vector3(0.75f, 2.28f, poster.position.z);
            poster.localScale = Vector3.one * 0.9f;
            Keep(poster);
            Save(s);
        }
    }

    static void Wear(UnityEngine.SceneManagement.Scene s, string path, int look)
    {
        var t = Find(s, path);
        if (t == null) return;
        t.GetComponent<NpcPose>().look = look;
        Keep(t.GetComponent<NpcPose>());
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
                var model = AssetDatabase.LoadAssetAtPath<GameObject>(Art + "Models/Characters/" + asset + ".fbx");
                if (model == null)
                {
                    Warn("모델 없음 " + asset);
                    return;   // 번호가 밀리면 안 되니 더 넣지 않는다
                }
                var go = (GameObject)PrefabUtility.InstantiatePrefab(model, root.scene);
                go.name = asset;
                go.transform.SetParent(visual, false);
                go.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);   // 리깅 FBX 는 -Z 를 본다
                var animator = go.AddComponent<Animator>();
                animator.runtimeAnimatorController = Controller(asset);
                animator.applyRootMotion = false;
                Phone(go, asset);
                foreach (var t in go.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = root.layer;
                go.SetActive(false);
            }
            PrefabUtility.SaveAsPrefabAsset(root, path);
        }
        finally { PrefabUtility.UnloadPrefabContents(root); }
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
