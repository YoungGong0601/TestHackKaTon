using UnityEngine;
using UnityEngine.SceneManagement;

// 씬 로드. 공용 Build Settings를 고치지 않으려고 에디터에서는 경로로 바로 연다. 빌드는 JWBuild가 넘긴 씬 목록을 쓴다
public static class JWScenes
{
    public static AsyncOperation Load(string scene, LoadSceneMode mode)
    {
#if UNITY_EDITOR
        return UnityEditor.SceneManagement.EditorSceneManager.LoadSceneAsyncInPlayMode($"Assets/JeongWoo/Scenes/{scene}.unity", new LoadSceneParameters(mode));
#else
        return SceneManager.LoadSceneAsync(scene, mode);
#endif
    }
}
