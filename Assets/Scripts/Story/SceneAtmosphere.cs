// 씬의 하늘, 앰비언트, 안개 값. 씬이 열릴 때 적용한다. 값은 씬 인스펙터에서 조정한다.
// 배치: Directional Light 오브젝트에 부착
using UnityEngine;
using UnityEngine.Rendering;

[DefaultExecutionOrder(-100)]
public class SceneAtmosphere : MonoBehaviour
{
    public Material skybox;
    public bool night;     // 밤은 밝기 키를 받지 않는다
    public Color ambientSky = Color.gray, ambientEquator = Color.gray, ambientGround = Color.gray;
    public bool fog;
    public Color fogColor = Color.gray;
    public float fogStart = 60f, fogEnd = 260f;

    void Awake()
    {
        if (skybox) RenderSettings.skybox = skybox;
        RenderSettings.ambientMode = AmbientMode.Trilight;
        float amb = night ? 1f : Bal.G("Light_AmbientMul", 1f);
        RenderSettings.ambientSkyColor = ambientSky * amb;
        RenderSettings.ambientEquatorColor = ambientEquator * amb;
        RenderSettings.ambientGroundColor = ambientGround * amb;
        var sun = GetComponent<Light>();
        if (sun && !night) sun.intensity *= Bal.G("Light_SunMul", 1f);
        RenderSettings.fog = fog;
        RenderSettings.fogMode = FogMode.Linear;
        RenderSettings.fogColor = fogColor;
        RenderSettings.fogStartDistance = fogStart;
        RenderSettings.fogEndDistance = fogEnd;
    }
}
