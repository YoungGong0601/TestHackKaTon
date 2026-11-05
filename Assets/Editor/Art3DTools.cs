using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Rendering.Universal.ShaderGUI;
using UnityEngine;
using UnityEngine.Rendering;
using Object = UnityEngine.Object;

// Blender 내보내기(Assets/Art3D)를 Unity 에 맞춘다. 원본은 ArtSource/Blender/scripts/k3d.py.
// - 임포트 설정: 텍스처(노멀·MS 는 선형), 모델(리깅 여부는 같은 이름의 JSON)
// - 3D 에셋 적용: JSON → URP/Lit 머티리얼 · FBX 머티리얼 연결. Models 의 JSON 이 바뀌면 자동 실행
// - PH 프리팹에 모델 넣기: 모델링목록.md 대로 PH_ 프리팹의 Visual 을 Models/PH 모델로 바꾼다 (PH_Map.json)
public class Art3DTools : AssetPostprocessor
{
    const string Art = "Assets/Art3D/";
    const string ModelsDir = Art + "Models";
    const string TexturesDir = Art + "Textures";
    const string MaterialsDir = Art + "Materials";

    // ── JSON 형식 (notes 는 문자열 또는 객체라 읽지 않는다) ──
#pragma warning disable 0649 // JsonUtility 가 채운다
    [Serializable] class ModelJson { public bool rigged; public MatJson[] materials; }
    [Serializable] class MatJson
    {
        public string name;
        public float[] baseColor, emission; // 선형
        public float metallic, smoothness, emissionStrength, alphaClip;
        public bool occlusion, transparent, dynamic, doubleSided;
        public Maps maps;
    }
    [Serializable] class Maps { public string BaseColor, Normal, MS, Emission; } // Art3D 기준 상대 경로
    [Serializable] class PhMap { public PhRow[] rows; }
    [Serializable] class PhRow { public string prefab, target, model; public int look; } // model 이 비면 회색 메시만 지운다
#pragma warning restore 0649

    // ── 임포트 설정 ──

    void OnPreprocessTexture()
    {
        if (!assetPath.StartsWith(TexturesDir + "/")) return;
        var ti = (TextureImporter)assetImporter;
        var name = Path.GetFileNameWithoutExtension(assetPath);
        bool normal = name.EndsWith("_Normal"), ms = name.EndsWith("_MS");
        ti.textureType = normal ? TextureImporterType.NormalMap : TextureImporterType.Default;
        ti.sRGBTexture = !normal && !ms; // 노멀·MS 는 데이터라 선형, BaseColor·Emission 은 sRGB
        ti.wrapMode = TextureWrapMode.Repeat;
        ti.alphaIsTransparency = !normal && !ms; // MS 의 A 는 매끈함이라 색을 번지게 하면 안 된다
        ti.maxTextureSize = 2048;
        ti.mipmapEnabled = true;
        ti.anisoLevel = 4;
    }

    void OnPreprocessModel()
    {
        if (!assetPath.StartsWith(ModelsDir + "/")) return;
        var mi = (ModelImporter)assetImporter;
        var json = Path.ChangeExtension(assetPath, ".json");
        bool rigged = File.Exists(json) && Read<ModelJson>(json).rigged;
        mi.importCameras = false;
        mi.importLights = false;
        mi.isReadable = false;
        mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription; // 실제 머티리얼은 적용 단계에서 연결
        mi.bakeAxisConversion = rigged; // 리깅 FBX 는 Apply Transform 없이 나온다
        mi.animationType = rigged ? ModelImporterAnimationType.Generic : ModelImporterAnimationType.None;
        mi.importAnimation = rigged;
    }

    // 캐릭터 클립(Idle · Walk · Phone …)은 모두 반복 재생
    void OnPreprocessAnimation()
    {
        if (!assetPath.StartsWith(ModelsDir + "/")) return;
        var mi = (ModelImporter)assetImporter;
        var clips = mi.defaultClipAnimations;
        foreach (var c in clips) c.loopTime = true;
        mi.clipAnimations = clips;
    }

    static bool scheduled;

    // Models 의 JSON 이 들어오거나 바뀌면 임포트가 끝난 뒤 한 번 적용한다.
    // 적용은 JSON 을 쓰지 않으므로 다시 불리지 않는다.
    static void OnPostprocessAllAssets(string[] imported, string[] deleted, string[] moved, string[] movedFrom)
    {
        if (scheduled || !imported.Concat(moved).Any(p => p.EndsWith(".json") && p.StartsWith(ModelsDir + "/"))) return;
        scheduled = true;
        EditorApplication.delayCall += () => { scheduled = false; Apply(); };
    }

    // ── 3D 에셋 적용 ──

    static int warnings;

    [UnityEditor.MenuItem("Tools/키오스크/3D 에셋 적용")]
    public static void Apply()
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode) return;
        var lit = Shader.Find("Universal Render Pipeline/Lit");
        if (lit == null) throw new Exception("URP Lit 셰이더를 찾을 수 없습니다");
        warnings = 0;
        int mats = 0, linked = 0;
        EnsureFolder(MaterialsDir);
        foreach (var path in Directory.GetFiles(ModelsDir, "*.json", SearchOption.AllDirectories).Select(p => p.Replace('\\', '/')))
        {
            var byName = new Dictionary<string, Material>();
            foreach (var j in Read<ModelJson>(path).materials ?? new MatJson[0])
            {
                byName[j.name] = MakeMaterial(j, lit);
                mats++;
            }
            if (Link(Path.ChangeExtension(path, ".fbx"), byName)) linked++;
        }
        AssetDatabase.SaveAssets();
        Debug.Log($"키오스크: 3D 에셋 적용 — 머티리얼 {mats}개, FBX 연결 갱신 {linked}개, 경고 {warnings}개");
    }

    // JSON 머티리얼 → Assets/Art3D/Materials/<name>.mat. 매번 JSON 값으로 덮어쓴다.
    static Material MakeMaterial(MatJson j, Shader lit)
    {
        var path = MaterialsDir + "/" + j.name + ".mat";
        var m = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (m == null) m = new Material(lit);
        m.shader = lit;
        var maps = j.maps ?? new Maps();
        var c = j.baseColor;
        // JSON 색은 선형이고 SetColor 는 sRGB 값을 받는다 → .gamma
        m.SetColor("_BaseColor", c != null && c.Length >= 4 ? new Color(c[0], c[1], c[2], c[3]).gamma : Color.white);
        m.SetTexture("_BaseMap", Tex(maps.BaseColor));
        m.SetTexture("_BumpMap", Tex(maps.Normal));
        var ms = Tex(maps.MS); // R 금속 · G AO · A 매끈함. 있으면 metallic/smoothness 는 1.0 배율
        m.SetTexture("_MetallicGlossMap", ms);
        m.SetTexture("_OcclusionMap", j.occlusion ? ms : null); // URP 는 .g 를 읽는다
        m.SetFloat("_Metallic", j.metallic);
        m.SetFloat("_Smoothness", j.smoothness);

        var e = j.emission;
        bool glow = e != null && e.Length >= 3 && j.emissionStrength > 0;
        m.SetTexture("_EmissionMap", glow ? Tex(maps.Emission) : null);
        m.SetColor("_EmissionColor", glow ? (new Color(e[0], e[1], e[2]) * j.emissionStrength).gamma : Color.black);
        m.globalIlluminationFlags = !glow ? MaterialGlobalIlluminationFlags.EmissiveIsBlack
            : j.dynamic ? MaterialGlobalIlluminationFlags.RealtimeEmissive // 런타임에 바뀌는 화면은 굽지 않는다
            : MaterialGlobalIlluminationFlags.BakedEmissive;

        m.SetFloat("_Surface", j.transparent ? 1 : 0);
        m.SetFloat("_Blend", 0); // Alpha
        m.SetFloat("_BlendModePreserveSpecular", 0); // SrcAlpha/OneMinusSrcAlpha. 1 이면 유리 반사가 더 산다
        m.SetFloat("_AlphaClip", j.alphaClip > 0 ? 1 : 0);
        m.SetFloat("_Cutoff", j.alphaClip > 0 ? j.alphaClip : 0.5f);
        m.SetFloat("_Cull", j.doubleSided ? 0 : 2);
        // 키워드 · 블렌드 · ZWrite · 렌더 큐 · 그림자 패스는 URP 인스펙터와 같은 함수로 맞춘다
        BaseShaderGUI.SetMaterialKeywords(m, LitGUI.SetMaterialKeywords);

        if (!AssetDatabase.Contains(m)) AssetDatabase.CreateAsset(m, path);
        else EditorUtility.SetDirty(m);
        return m;
    }

    static Texture Tex(string rel)
    {
        if (string.IsNullOrEmpty(rel)) return null;
        var t = AssetDatabase.LoadAssetAtPath<Texture>(Art + rel);
        if (t == null) Warn("텍스처 없음 " + Art + rel);
        return t;
    }

    // FBX 머티리얼을 JSON 머티리얼에 연결한다. 바뀐 게 있을 때만 다시 임포트한다.
    static bool Link(string fbx, Dictionary<string, Material> byName)
    {
        if (!(AssetImporter.GetAtPath(fbx) is ModelImporter mi))
        {
            Warn("FBX 없음 " + fbx);
            return false;
        }
        var map = mi.GetExternalObjectMap();
        // FBX 머티리얼 이름 = 아직 FBX 안에 있는 것 + 이미 연결된 것
        var names = AssetDatabase.LoadAllAssetsAtPath(fbx).OfType<Material>().Select(x => x.name)
            .Concat(map.Keys.Where(k => k.type == typeof(Material)).Select(k => k.name)).Distinct().ToList();
        bool changed = false;
        foreach (var n in names)
        {
            if (!byName.TryGetValue(n, out var mat))
            {
                Warn(fbx + " 의 머티리얼 " + n + " 이 JSON 에 없습니다");
                continue;
            }
            var id = new AssetImporter.SourceAssetIdentifier(typeof(Material), n);
            if (map.TryGetValue(id, out var cur) && cur == mat) continue;
            mi.AddRemap(id, mat);
            changed = true;
        }
        if (changed) mi.SaveAndReimport();
        return changed;
    }

    // ── PH 프리팹 ──

    // 모델링목록.md 규칙: Visual 아래 회색 메시만 지우고 모델을 넣는다. Visual 밖(앵커 · 콜라이더 · 글자)은 건드리지 않는다.
    // 다시 눌러도 된다. 찾지 못한 프리팹이나 자리는 건너뛰고 경고만 남긴다.
    [UnityEditor.MenuItem("Tools/키오스크/PH 프리팹에 모델 넣기")]
    public static void FillPlaceholders() => Fill(null);

    // 여러 컴퓨터가 서로의 프리팹을 저장하지 않도록 그 맵 파일에 나오는 프리팹만 고친다.
    // Unity -batchmode -quit -projectPath . -executeMethod Art3DTools.FillMap -phmap PH_Map_Cafe.json -logFile -
    public static void FillMap()
    {
        var args = Environment.GetCommandLineArgs();
        Fill(Art + args[Array.IndexOf(args, "-phmap") + 1]);
    }

    // PH_Map.json 은 사본도 읽으니 그대로 두고 새 행은 PH_Map_<묶음>.json 에 쓴다.
    // 뒤 파일의 빈 model 행은 그 자리의 앞선 행을 지운다.
    static List<PhRow> Rows()
    {
        var rows = new List<PhRow>();
        foreach (var path in Directory.GetFiles(Art, "PH_Map*.json").OrderBy(p => p, StringComparer.Ordinal))
            foreach (var r in Read<PhMap>(path).rows)
            {
                if (string.IsNullOrEmpty(r.model)) rows.RemoveAll(x => x.prefab == r.prefab && x.target == r.target);
                rows.Add(r);
            }
        return rows;
    }

    static void Fill(string only)
    {
        if (EditorApplication.isPlayingOrWillChangePlaymode) return;
        Apply(); // 첫 임포트 뒤 스크립트 컴파일로 자동 적용이 끊길 수 있어 여기서도 맞춘다
        warnings = 0;
        int placed = 0, prefabs = 0;
        var names = only == null ? null : Read<PhMap>(only).rows.Select(r => r.prefab).ToHashSet();
        foreach (var group in Rows().Where(r => names == null || names.Contains(r.prefab)).GroupBy(r => r.prefab))
        {
            var path = AssetDatabase.FindAssets(group.Key + " t:Prefab").Select(AssetDatabase.GUIDToAssetPath)
                .FirstOrDefault(p => p.StartsWith("Assets/Graybox/") && Path.GetFileNameWithoutExtension(p) == group.Key); // 사본 Assets/JeongWoo 는 JWBuild 가 맡는다
            if (path == null)
            {
                Warn("프리팹 없음 " + group.Key);
                continue;
            }
            var root = PrefabUtility.LoadPrefabContents(path);
            try
            {
                var done = new Dictionary<Transform, ShadowCastingMode>(); // 비운 자리와 회색 메시의 그림자 설정
                foreach (var r in group)
                {
                    var t = FindTarget(root.transform, r.target);
                    if (t == null)
                    {
                        Warn(group.Key + ": 자리 없음 " + r.target);
                        continue;
                    }
                    if (!done.TryGetValue(t, out var shadows))
                    {
                        var gray = t.GetComponentInChildren<MeshRenderer>(true);
                        done[t] = shadows = gray != null ? gray.shadowCastingMode : ShadowCastingMode.On; // 손은 그림자를 끈다
                        for (int i = t.childCount - 1; i >= 0; i--) Object.DestroyImmediate(t.GetChild(i).gameObject);
                    }
                    if (string.IsNullOrEmpty(r.model)) continue;
                    var asset = AssetDatabase.LoadAssetAtPath<GameObject>(Art + r.model);
                    if (asset == null)
                    {
                        Warn(group.Key + ": 모델 없음 " + r.model);
                        continue;
                    }
                    var go = (GameObject)PrefabUtility.InstantiatePrefab(asset, root.scene);
                    go.transform.SetParent(t, false);
                    go.SetActive(r.look == 0);
                    foreach (var renderer in go.GetComponentsInChildren<Renderer>(true)) renderer.shadowCastingMode = shadows;
                    // 손 모델은 돋보기 카메라에서 빠져야 한다. Systems 의 레이어 설정은 지운 회색 메시에만 걸려 있었다
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
        Debug.Log($"키오스크: PH 프리팹 {prefabs}개에 모델 {placed}개를 넣었습니다. 경고 {warnings}개");
    }

    // 경로 끝이 target 인 자식 (HeadPivot/Visual 의 실제 경로는 ReactPivot/HeadPivot/Visual)
    static Transform FindTarget(Transform root, string target) => root.Find(target) ?? root.GetComponentsInChildren<Transform>(true)
        .FirstOrDefault(c => AnimationUtility.CalculateTransformPath(c, root).EndsWith("/" + target));

    // ── 기본 도구 ──

    static T Read<T>(string path)
    {
        try { return JsonUtility.FromJson<T>(File.ReadAllText(path)); }
        catch (Exception e) { throw new Exception(path + " 를 읽을 수 없습니다: " + e.Message); }
    }

    static void Warn(string message)
    {
        warnings++;
        Debug.LogWarning("키오스크: " + message);
    }

    static void EnsureFolder(string path)
    {
        path = path.Replace('\\', '/');
        if (AssetDatabase.IsValidFolder(path)) return;
        var parent = Path.GetDirectoryName(path).Replace('\\', '/');
        EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
    }
}
