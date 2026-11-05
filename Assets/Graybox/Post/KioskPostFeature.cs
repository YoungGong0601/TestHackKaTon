// 자체 제작 화면 후처리. URP 기본 Vignette, Film Grain, Depth Of Field 대신 쓴다.
// 눈치 값은 PostState로 받고, 수치는 전부 ConfigTable Post_ 키에서 쓰는 순간에 읽는다.
// 배치: PC_Renderer, Mobile_Renderer의 Renderer Features에 등록, shader = Assets/Graybox/Post/KioskPost.shader
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.RenderGraphModule.Util;
using UnityEngine.Rendering.Universal;

public class KioskPostFeature : ScriptableRendererFeature
{
    [SerializeField] Shader shader;

    Material material;
    KioskPostPass pass;

    public override void Create()
    {
        if (shader == null) return;
        material = CoreUtils.CreateEngineMaterial(shader);
        pass = new KioskPostPass(material) { renderPassEvent = RenderPassEvent.AfterRenderingPostProcessing };
    }

    public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
    {
        if (pass == null) return;
        ref var cam = ref renderingData.cameraData;
        // 화면을 그리는 본 카메라만. 키오스크 RT 카메라는 Post Processing이 꺼져 있다
        if (cam.cameraType != CameraType.Game || cam.renderType != CameraRenderType.Base || !cam.postProcessEnabled) return;
        renderer.EnqueuePass(pass);
    }

    protected override void Dispose(bool disposing) => CoreUtils.Destroy(material);
}

class KioskPostPass : ScriptableRenderPass
{
    const int Down = 0, Up = 1, Plain = 2, Blur = 3;

    static readonly int Spread = Shader.PropertyToID("_Spread");
    static readonly int PostTime = Shader.PropertyToID("_PostTime");
    static readonly int Aspect = Shader.PropertyToID("_Aspect");
    static readonly int Dim = Shader.PropertyToID("_Dim");
    static readonly int Sat = Shader.PropertyToID("_Sat");
    static readonly int Grain = Shader.PropertyToID("_Grain");
    static readonly int Ca = Shader.PropertyToID("_Ca");
    static readonly int Tint = Shader.PropertyToID("_Tint");
    static readonly int ShadowColor = Shader.PropertyToID("_ShadowColor");
    static readonly int Depth = Shader.PropertyToID("_Depth");
    static readonly int Corner = Shader.PropertyToID("_Corner");
    static readonly int Bottom = Shader.PropertyToID("_Bottom");
    static readonly int FieldAspect = Shader.PropertyToID("_FieldAspect");
    static readonly int SoftWide = Shader.PropertyToID("_SoftWide");
    static readonly int SoftCore = Shader.PropertyToID("_SoftCore");
    static readonly int StrengthWide = Shader.PropertyToID("_StrengthWide");
    static readonly int StrengthCore = Shader.PropertyToID("_StrengthCore");
    static readonly int WobbleAmp = Shader.PropertyToID("_WobbleAmp");
    static readonly int WobbleFreq = Shader.PropertyToID("_WobbleFreq");
    static readonly int WobbleSpeed = Shader.PropertyToID("_WobbleSpeed");
    static readonly int BlurCenter = Shader.PropertyToID("_BlurCenter");
    static readonly int BlurEdge = Shader.PropertyToID("_BlurEdge");
    static readonly int BlurStart = Shader.PropertyToID("_BlurStart");
    static readonly int LensHole = Shader.PropertyToID("_LensHole");
    static readonly int LensTex = Shader.PropertyToID("_LensTex");
    static readonly int LensRim = Shader.PropertyToID("_LensRim");
    static readonly int LensShade = Shader.PropertyToID("_LensShade");
    static readonly int NearTex = Shader.PropertyToID("_NearTex");
    static readonly int MidTex = Shader.PropertyToID("_MidTex");
    static readonly int FarTex = Shader.PropertyToID("_FarTex");
    static readonly int BlitTexture = Shader.PropertyToID("_BlitTexture");
    static readonly int BlitScaleBias = Shader.PropertyToID("_BlitScaleBias");
    static readonly int SmudgeSoft = Shader.PropertyToID("_SmudgeSoft");
    static readonly int SmudgeContrast = Shader.PropertyToID("_SmudgeContrast");
    static readonly int SmudgeDrift = Shader.PropertyToID("_SmudgeDrift");

    // 단계 값: 평온, 심장(Nunchi_HeartAt), 떨림(TrembleAt), 이명(RingAt), 최대(Nunchi_Max)
    static readonly string[] DepthKeys = StageKeys("Post_ShadowDepth");
    static readonly string[] WideKeys = StageKeys("Post_ShadowWide");
    static readonly string[] CoreKeys = StageKeys("Post_ShadowCore");
    static readonly string[] CenterKeys = StageKeys("Post_BlurCenter");
    static readonly string[] EdgeKeys = StageKeys("Post_BlurEdge");

    static string[] StageKeys(string k) => new[] { k + "Calm", k + "Heart", k + "Tremble", k + "Ring", k + "Max" };

    readonly Material material;
    float level;
    int levelFrame = -1;

    class CompositeData
    {
        public TextureHandle source, near, mid, far;
        public Material material;
        public int shaderPass;
        public readonly MaterialPropertyBlock props = new();
    }

    public KioskPostPass(Material material)
    {
        this.material = material;
        requiresIntermediateTexture = true;
    }

    static float Stage(string[] keys, float g, float calm, float heart, float tremble, float ring, float max)
    {
        float a = Bal.G("Nunchi_HeartAt", 40f), b = Bal.G("Nunchi_TrembleAt", 60f), c = Bal.G("Nunchi_RingAt", 80f), m = Bal.G("Nunchi_Max", 100f);
        float v0 = Bal.G(keys[0], calm), v1 = Bal.G(keys[1], heart), v2 = Bal.G(keys[2], tremble), v3 = Bal.G(keys[3], ring), v4 = Bal.G(keys[4], max);
        if (g <= a) return Mathf.Lerp(v0, v1, g / Mathf.Max(a, 0.001f));
        if (g <= b) return Mathf.Lerp(v1, v2, (g - a) / Mathf.Max(b - a, 0.001f));
        if (g <= c) return Mathf.Lerp(v2, v3, (g - b) / Mathf.Max(c - b, 0.001f));
        return Mathf.Lerp(v3, v4, (g - c) / Mathf.Max(m - c, 0.001f));
    }

    // 쿵쿵 두 번 뛰는 파형. 소리가 나면 그 재생 위치에 맞춘다
    static float HeartPulse()
    {
        float period = Mathf.Max(0.2f, Bal.G("Post_HeartPeriod", 0.826f));
        float clock = PostState.HeartTime >= 0f ? PostState.HeartTime : Time.unscaledTime;
        float p = Mathf.Repeat(clock - Bal.G("Post_HeartOffset", 0.05f), period);
        float dub = Bal.G("Post_HeartDub", 0.34f);
        float k = Bal.G("Post_HeartDecay", 9f);
        float first = Mathf.Exp(-p * k);
        float second = p >= dub ? Mathf.Exp(-(p - dub) * k) * Bal.G("Post_HeartDubAmount", 0.6f) : 0f;
        return Mathf.Clamp01(first + second);
    }

    void UpdateLevel()
    {
        if (levelFrame == Time.frameCount) return;
        levelFrame = Time.frameCount;
        float rate = Bal.G("Post_LevelDamp", 3f);
        level = Mathf.Lerp(level, PostState.Nunchi, 1f - Mathf.Exp(-rate * Time.unscaledDeltaTime));
    }

    /// <summary>재질 값을 채우고 번짐이 필요하면 true.</summary>
    bool Fill(float aspect)
    {
        UpdateLevel();
        float g = level, max = Bal.G("Nunchi_Max", 100f), s = Mathf.Clamp01(g / Mathf.Max(max, 0.001f));
        float heartAt = Bal.G("Nunchi_HeartAt", 40f);
        float beat = Mathf.Clamp01((g - heartAt) / Mathf.Max(max - heartAt, 0.001f));
        float pulse = HeartPulse() * beat;

        var profile = GameState.I != null ? GameState.I.Profile : null;
        bool vision = profile != null && profile.visionBlur;

        material.SetFloat(Spread, Bal.G("Post_BlurSpread", 1.4f));
        material.SetFloat(PostTime, Time.unscaledTime);
        material.SetFloat(Aspect, aspect);

        material.SetFloat(Dim, Mathf.Lerp(Bal.G("Post_Dim", 0.92f), Bal.G("Post_DimMax", 0.8f), s));
        material.SetFloat(Sat, Mathf.Lerp(Bal.G("Post_Sat", 0.74f), Bal.G("Post_SatMax", 0.45f), s));
        material.SetFloat(Grain, Bal.G("Post_Grain", 0.07f) + s * Bal.G("Post_GrainAdd", 0.04f));
        material.SetFloat(Ca, Bal.G("Post_Ca", 0.0012f) + s * Bal.G("Post_CaAdd", 0.003f));
        material.SetVector(Tint, new Vector4(Bal.G("Post_TintR", 1f), Bal.G("Post_TintG", 0.98f), Bal.G("Post_TintB", 0.95f), 1f));
        material.SetVector(ShadowColor, new Vector4(Bal.G("Post_ShadowR", 0.1f), Bal.G("Post_ShadowG", 0.07f), Bal.G("Post_ShadowB", 0.05f), 1f));

        material.SetFloat(Depth, Stage(DepthKeys, g, 0.02f, 0.16f, 0.28f, 0.36f, 0.44f) + pulse * Bal.G("Post_HeartDepth", 0.07f));
        material.SetFloat(Corner, Bal.G("Post_ShadowCorner", 0.6f));
        material.SetFloat(Bottom, Bal.G("Post_ShadowBottom", 0.12f));
        material.SetFloat(FieldAspect, Bal.G("Post_ShadowAspect", 1.3f));
        material.SetFloat(SoftWide, Bal.G("Post_ShadowSoftWide", 0.3f));
        material.SetFloat(SoftCore, Bal.G("Post_ShadowSoftCore", 0.14f));
        material.SetFloat(StrengthWide, Stage(WideKeys, g, 0.16f, 0.42f, 0.65f, 0.72f, 0.8f));
        material.SetFloat(StrengthCore, Stage(CoreKeys, g, 0.08f, 0.38f, 0.7f, 0.8f, 0.9f));
        material.SetFloat(WobbleAmp, Bal.G("Post_WobbleAmp", 0.16f));
        material.SetFloat(WobbleFreq, Bal.G("Post_WobbleFreq", 2.2f));
        material.SetFloat(WobbleSpeed, Bal.G("Post_WobbleSpeed", 0.22f));

        // 평온 값은 시야 번짐 인물의 몫, 그 위 증가분은 눈치의 몫
        float calmC = Bal.G(CenterKeys[0], 0.1f), calmE = Bal.G(EdgeKeys[0], 0.55f);
        float center = Stage(CenterKeys, g, 0.1f, 0.14f, 0.2f, 0.3f, 0.45f) - (vision ? 0f : calmC);
        float edge = Stage(EdgeKeys, g, 0.55f, 0.65f, 0.78f, 0.9f, 1f) - (vision ? 0f : calmE);
        material.SetFloat(BlurCenter, center);
        material.SetFloat(BlurEdge, edge);
        material.SetFloat(BlurStart, Bal.G("Post_BlurStart", 0.35f));

        Vector3 lens = PostState.Lens;
        material.SetVector(LensHole, new Vector4(lens.x, lens.y, lens.z, 0f));
        material.SetFloat(LensRim, Bal.G("Post_LensRim", 0.5f));
        material.SetFloat(LensShade, Bal.G("Post_LensShade", 0.7f));
        material.SetTexture(LensTex, PostState.LensTexture != null ? PostState.LensTexture : Texture2D.blackTexture);

        // 얼룩 글자 재질(Readable의 번진 쪽)이 읽는 전역 값
        Shader.SetGlobalFloat(SmudgeSoft, Bal.G("Post_SmudgeSoft", 0.5f));
        Shader.SetGlobalFloat(SmudgeContrast, Bal.G("Post_SmudgeContrast", 0.55f));
        Shader.SetGlobalFloat(SmudgeDrift, Bal.G("Post_SmudgeDrift", 0.05f));

        return center > 0.001f || edge > 0.001f;
    }

    public override void RecordRenderGraph(RenderGraph renderGraph, ContextContainer frameData)
    {
        var resources = frameData.Get<UniversalResourceData>();
        if (resources.isActiveTargetBackBuffer) return;

        TextureHandle source = resources.activeColorTexture;
        TextureDesc desc = source.GetDescriptor(renderGraph);
        desc.msaaSamples = MSAASamples.None;
        desc.depthBufferBits = DepthBits.None;
        desc.clearBuffer = false;
        desc.filterMode = FilterMode.Bilinear;
        desc.wrapMode = TextureWrapMode.Clamp;

        bool blur = Fill((float)desc.width / Mathf.Max(desc.height, 1));

        TextureHandle near = TextureHandle.nullHandle, mid = TextureHandle.nullHandle, far = TextureHandle.nullHandle;
        if (blur)
        {
            near = Level(renderGraph, desc, 2, "KioskPost Near");
            mid = Level(renderGraph, desc, 4, "KioskPost Mid");
            TextureHandle d8 = Level(renderGraph, desc, 8, "KioskPost D8");
            TextureHandle d16 = Level(renderGraph, desc, 16, "KioskPost D16");
            TextureHandle u8 = Level(renderGraph, desc, 8, "KioskPost U8");
            far = Level(renderGraph, desc, 4, "KioskPost Far");
            Step(renderGraph, source, near, Down, "KioskPost Down 2");
            Step(renderGraph, near, mid, Down, "KioskPost Down 4");
            Step(renderGraph, mid, d8, Down, "KioskPost Down 8");
            Step(renderGraph, d8, d16, Down, "KioskPost Down 16");
            Step(renderGraph, d16, u8, Up, "KioskPost Up 8");
            Step(renderGraph, u8, far, Up, "KioskPost Up 4");
        }

        desc.name = "KioskPost Color";
        TextureHandle target = renderGraph.CreateTexture(desc);

        using (var builder = renderGraph.AddRasterRenderPass<CompositeData>("KioskPost Composite", out var data))
        {
            data.source = source;
            data.near = near;
            data.mid = mid;
            data.far = far;
            data.material = material;
            data.shaderPass = blur ? Blur : Plain;
            builder.UseTexture(source);
            if (blur)
            {
                builder.UseTexture(near);
                builder.UseTexture(mid);
                builder.UseTexture(far);
            }
            builder.SetRenderAttachment(target, 0, AccessFlags.WriteAll);
            builder.SetRenderFunc(static (CompositeData d, RasterGraphContext ctx) =>
            {
                d.props.Clear();
                d.props.SetTexture(BlitTexture, d.source);
                d.props.SetVector(BlitScaleBias, new Vector4(1f, 1f, 0f, 0f));
                if (d.shaderPass == Blur)
                {
                    d.props.SetTexture(NearTex, d.near);
                    d.props.SetTexture(MidTex, d.mid);
                    d.props.SetTexture(FarTex, d.far);
                }
                ctx.cmd.DrawProcedural(Matrix4x4.identity, d.material, d.shaderPass, MeshTopology.Triangles, 3, 1, d.props);
            });
        }

        resources.cameraColor = target;
    }

    static TextureHandle Level(RenderGraph graph, TextureDesc desc, int div, string name)
    {
        desc.width = Mathf.Max(1, desc.width / div);
        desc.height = Mathf.Max(1, desc.height / div);
        desc.name = name;
        return graph.CreateTexture(desc);
    }

    void Step(RenderGraph graph, TextureHandle from, TextureHandle to, int shaderPass, string name)
    {
        graph.AddBlitPass(new RenderGraphUtils.BlitMaterialParameters(from, to, material, shaderPass), name);
    }
}
