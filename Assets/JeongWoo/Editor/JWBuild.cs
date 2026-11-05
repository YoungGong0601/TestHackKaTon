using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using TMPro;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore.LowLevel;
using Object = UnityEngine.Object;

// Assets/JeongWoo 사본을 최종 게임으로 만든다. 다시 돌려도 같은 결과가 나온다. 친구 폴더는 읽지도 고치지도 않는다.
public static class JWBuild
{
    const string Root = "Assets/JeongWoo/";
    const string Art = "Assets/Art3D/";
    const string PhDir = Root + "Graybox/PH/";
    const string SystemsPath = PhDir + "Systems.prefab";
    static readonly string[] Scenes = { "JW_Home", "JW_Street", "JW_Bus", "JW_Storefront", "JW_Store" };

    static int warnings;

    public static void Warn(string text)
    {
        warnings++;
        Debug.LogWarning("JWBuild: " + text);
    }

    [UnityEditor.MenuItem("Tools/JeongWoo/사본 다시 만들기")]
    public static void All()
    {
        warnings = 0;
        EditorApplication.ExecuteMenuItem("Tools/키오스크/3D 에셋 적용");
        FoodSprites();
        JWKiosk.All();
        FillPrefabs();
        WireSystems();
        Fonts();
        JWDress.All();
        AssetDatabase.SaveAssets();
        Debug.Log($"JWBuild: 끝, 경고 {warnings}개");
    }

    // ── 빌드 ──

    [UnityEditor.MenuItem("Tools/JeongWoo/빌드 (Windows)")]
    public static void BuildWindows() => Build(BuildTarget.StandaloneWindows64, "Builds/Windows/BulgogiBurgerSet.exe");

    [UnityEditor.MenuItem("Tools/JeongWoo/빌드 (Mac)")]
    public static void BuildMac() => Build(BuildTarget.StandaloneOSX, "Builds/Mac/BulgogiBurgerSet.app");

    // 공용 Build Settings 대신 사본 씬 목록을 직접 넘긴다. 제품 이름도 빌드 동안만 바꾼다
    static void Build(BuildTarget target, string path)
    {
        string product = PlayerSettings.productName;
        PlayerSettings.productName = "불고기버거 세트 하나";
        try
        {
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = Scenes.Select(s => Root + "Scenes/" + s + ".unity").ToArray(),
                locationPathName = path,
                target = target,
                targetGroup = BuildTargetGroup.Standalone,
                options = BuildOptions.None,
            });
            var s = report.summary;
            Debug.Log($"JWBuild: {target} {s.result}, 오류 {s.totalErrors}개, {s.totalSize / 1048576} MB, {s.totalTime}");
            // CC BY 소리의 출처 표시. 빌드와 같이 내야 한다
            var folder = Path.GetDirectoryName(path);
            File.Copy(Root + "Resources/JW/Audio/SFX_CREDITS.csv", Path.Combine(folder, "SFX_CREDITS.csv"), true);
            foreach (var junk in Directory.GetDirectories(folder, "*_DoNotShip")) Directory.Delete(junk, true);
            if (Application.isBatchMode && s.result != UnityEditor.Build.Reporting.BuildResult.Succeeded) EditorApplication.Exit(1);
        }
        finally
        {
            PlayerSettings.productName = product;
            AssetDatabase.SaveAssets();
        }
    }

    // ── PH 프리팹 ──

#pragma warning disable 0649
    [Serializable] class PhMap { public PhRow[] rows; }
    [Serializable] class PhRow { public string prefab, target, model; public int look; }
#pragma warning restore 0649

    // Art3DTools.FillPlaceholders 와 같은 규칙이지만 사본 폴더만 고친다
    static void FillPrefabs()
    {
        int placed = 0, prefabs = 0;
        var map = JsonUtility.FromJson<PhMap>(File.ReadAllText(Art + "PH_Map.json"));
        foreach (var group in map.rows.GroupBy(r => r.prefab))
        {
            var path = PhDir + group.Key + ".prefab";
            if (!File.Exists(path)) { Warn("프리팹 없음 " + group.Key); continue; }
            var root = PrefabUtility.LoadPrefabContents(path);
            try
            {
                var done = new Dictionary<Transform, ShadowCastingMode>();
                foreach (var r in group)
                {
                    var t = FindTarget(root.transform, r.target);
                    if (t == null) { Warn(group.Key + ": 자리 없음 " + r.target); continue; }
                    if (!done.TryGetValue(t, out var shadows))
                    {
                        var gray = t.GetComponentInChildren<MeshRenderer>(true);
                        done[t] = shadows = gray != null ? gray.shadowCastingMode : ShadowCastingMode.On;
                        for (int i = t.childCount - 1; i >= 0; i--) Object.DestroyImmediate(t.GetChild(i).gameObject);
                    }
                    if (string.IsNullOrEmpty(r.model)) continue;
                    // 사람은 정적 메시 대신 리깅 모델을 쓴다. 머리는 몸 모델 안에 있어 자리만 비운다
                    var model = r.model;
                    string npc = null;
                    if (group.Key == "PH_NPC" && r.target.StartsWith("HeadPivot")) continue;
                    if (group.Key == "PH_NPC" && r.target.StartsWith("ReactPivot"))
                    {
                        npc = Path.GetFileNameWithoutExtension(r.model).Replace("PH_NPC__", "Npc").Replace("_Body", "");
                        model = "Models/Characters/" + npc + ".fbx";
                    }
                    var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Art + model);
                    if (asset == null) { Warn(group.Key + ": 모델 없음 " + model); continue; }
                    var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, root.scene);
                    go.transform.SetParent(t, false);
                    go.SetActive(r.look == 0);
                    if (npc != null) SetupNpc(go, npc);
                    foreach (var renderer in go.GetComponentsInChildren<Renderer>(true)) renderer.shadowCastingMode = shadows;
                    if (group.Key == "PH_Hand")
                        foreach (var c in go.GetComponentsInChildren<Transform>(true)) c.gameObject.layer = LayerMask.NameToLayer("HandModel");
                    placed++;
                }
                if (group.Key == "PH_NPC")
                {
                    if (!root.TryGetComponent(out NpcLook look)) look = root.AddComponent<NpcLook>();
                    look.visuals = group.Where(r => r.look > 0).Select(r => r.target).Distinct()
                        .Select(p => FindTarget(root.transform, p)).ToArray();
                }
                PrefabUtility.SaveAsPrefabAsset(root, path);
                prefabs++;
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
        }
        Debug.Log($"JWBuild: PH 프리팹 {prefabs}개에 모델 {placed}개");
    }

    // Idle, Walk 같은 상태 이름으로 CrossFade 한다. 클립 경로가 모델마다 달라 컨트롤러도 모델마다 만든다
    static AnimatorController NpcController(string asset)
    {
        const string dir = Root + "Graybox/Npc";
        var path = dir + "/" + asset + ".controller";
        var old = AssetDatabase.LoadAssetAtPath<AnimatorController>(path);
        if (old != null) return old;
        if (!AssetDatabase.IsValidFolder(dir)) AssetDatabase.CreateFolder(Root + "Graybox", "Npc");
        var clips = AssetDatabase.LoadAllAssetsAtPath(Art + "Models/Characters/" + asset + ".fbx").OfType<AnimationClip>()
            .Where(c => !c.name.StartsWith("__preview__"))
            .ToDictionary(c => c.name.Split('|').Last());
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

    static void SetupNpc(GameObject go, string asset)
    {
        go.transform.localRotation = Quaternion.Euler(0f, 180f, 0f);   // 리깅 FBX 는 -Z 를 보고 PH_NPC 앞은 +Z 다
        var animator = go.AddComponent<Animator>();
        animator.runtimeAnimatorController = NpcController(asset);
        animator.applyRootMotion = false;
        var grip = go.GetComponentsInChildren<Transform>(true).FirstOrDefault(t => t.name == asset + "_Socket_PhoneGrip");
        if (grip == null) return;   // 62본은 내장 폰을 쓴다
        // 소켓 스케일이 비균일해 부모 뼈에 붙이고, 정적 FBX 와 축이 달라 회전을 보정한다
        var phone = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Art + "Models/Characters/NpcSmartphone.fbx"), go.scene);
        phone.name = asset + "_Phone";
        phone.transform.SetParent(grip.parent, false);
        phone.transform.localPosition = grip.localPosition;
        phone.transform.localRotation = grip.localRotation * new Quaternion(0f, 0.70710678f, -0.70710678f, 0f);
    }

    static Transform FindTarget(Transform root, string target) => root.Find(target) ?? root.GetComponentsInChildren<Transform>(true)
        .FirstOrDefault(c => AnimationUtility.CalculateTransformPath(c, root).EndsWith("/" + target));

    // ── Systems ──

    static void WireSystems()
    {
        var root = PrefabUtility.LoadPrefabContents(SystemsPath);
        try
        {
            var game = root.GetComponentInChildren<GameState>(true);
            var so = new SerializedObject(game);
            so.FindProperty("pipeline").objectReferenceValue = AssetDatabase.LoadAssetAtPath<RenderPipelineAsset>(Root + "Settings/JW_PC_RPAsset.asset");
            so.ApplyModifiedPropertiesWithoutUndo();
            PrefabUtility.SaveAsPrefabAsset(root, SystemsPath);
        }
        finally { PrefabUtility.UnloadPrefabContents(root); }
    }

    // ── 키오스크 음식 그림 ──

    static void FoodSprites()
    {
        foreach (var path in Directory.GetFiles(Root + "Resources/JW/Food").Where(p => !p.EndsWith(".meta")).Select(p => p.Replace('\\', '/')))
        {
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            if (importer.textureType == TextureImporterType.Sprite && importer.spriteImportMode == SpriteImportMode.Single) continue;
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.alphaIsTransparency = true;
            importer.SaveAndReimport();
        }
    }

    // ── 글꼴 ──

    // HUD 글꼴은 Windows 맑은 고딕을 실행 중에 찾아서 맥에서는 글자가 안 나온다. 프로젝트에 넣은 Pretendard로 바꾼다
    static void Fonts()
    {
        const string fontPath = Root + "UI/Fonts/JW_Pretendard SDF.asset";
        var font = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(fontPath);
        if (font == null)
        {
            var source = AssetDatabase.LoadAssetAtPath<Font>(Root + "Fonts/Pretendard-Regular.otf");
            font = TMP_FontAsset.CreateFontAsset(source, 90, 9, GlyphRenderMode.SDFAA, 2048, 2048, AtlasPopulationMode.Dynamic, true);
            font.name = "JW_Pretendard SDF";
            AssetDatabase.CreateAsset(font, fontPath);
            font.atlasTexture.name = font.name + " Atlas";
            font.material.name = font.name + " Material";
            AssetDatabase.AddObjectToAsset(font.atlasTexture, font);
            AssetDatabase.AddObjectToAsset(font.material, font);
            var so = new SerializedObject(font);
            so.FindProperty("m_ClearDynamicDataOnBuild").boolValue = true;
            so.ApplyModifiedPropertiesWithoutUndo();
            AssetDatabase.SaveAssets();
        }
        var outline = AssetDatabase.LoadAssetAtPath<Material>(Root + "UI/Fonts/Hud_MalgunOS SDF Outline.mat");
        outline.SetTexture("_MainTex", font.atlasTexture);
        EditorUtility.SetDirty(outline);

        int changed = 0;
        void Swap(IEnumerable<TMP_Text> texts)
        {
            foreach (var t in texts)
            {
                if (t.font == null || !t.font.name.StartsWith("Hud_Malgun")) { Title(t); continue; }
                bool withOutline = t.fontSharedMaterial != null && t.fontSharedMaterial.name.Contains("Outline");
                t.font = font;
                t.fontSharedMaterial = withOutline ? outline : font.material;
                Title(t);
                changed++;
            }
        }
        foreach (var path in Directory.GetFiles(Root, "*.prefab", SearchOption.AllDirectories).Select(p => p.Replace('\\', '/')))
        {
            var root = PrefabUtility.LoadPrefabContents(path);
            try
            {
                var texts = root.GetComponentsInChildren<TMP_Text>(true);
                if (texts.Length == 0) continue;
                int before = changed;
                Swap(texts);
                if (changed != before) PrefabUtility.SaveAsPrefabAsset(root, path);
            }
            finally { PrefabUtility.UnloadPrefabContents(root); }
        }
        foreach (var name in Scenes)
        {
            var scene = EditorSceneManager.OpenScene(Root + "Scenes/" + name + ".unity", OpenSceneMode.Single);
            int before = changed;
            Swap(scene.GetRootGameObjects().SelectMany(g => g.GetComponentsInChildren<TMP_Text>(true)));
            if (changed != before) EditorSceneManager.SaveScene(scene);
        }
        Debug.Log($"JWBuild: 글꼴 {changed}곳");
    }

    static void Title(TMP_Text t)
    {
        if (t.text != null && t.text.Contains("불고기 세트 하나")) t.text = t.text.Replace("불고기 세트 하나", "불고기버거 세트 하나");
    }
}
