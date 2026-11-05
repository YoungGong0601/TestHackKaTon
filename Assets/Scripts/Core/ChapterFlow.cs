using System;
using System.Collections.Generic;
using UnityEngine;

[Serializable]
public class ChapterEntry
{
    public string sceneName;
    public CharacterProfile profile;
    public string spawnId;
    public bool hasKiosk;   // F5 디버그 키가 찾아가는 챕터
}

// 진행 순서. 챕터 추가는 이 목록에 항목을 넣는 것으로 끝난다
[CreateAssetMenu(menuName = "Kiosk/Chapter Flow")]
public class ChapterFlow : ScriptableObject
{
    public List<ChapterEntry> chapters = new();
    public List<CharacterProfile> speakers = new();   // 조작하지 않는 화자(손주 등). speakerKey와 displayName만 쓴다

#if UNITY_EDITOR
    void OnValidate()
    {
        var scenes = new HashSet<string>();
        foreach (var s in UnityEditor.EditorBuildSettings.scenes)
            if (s.enabled) scenes.Add(System.IO.Path.GetFileNameWithoutExtension(s.path));
        for (int i = 0; i < chapters.Count; i++)
        {
            var c = chapters[i];
            if (c.profile == null) Debug.LogWarning($"ChapterFlow {i}: profile 없음", this);
            if (!scenes.Contains(c.sceneName)) Debug.LogWarning($"ChapterFlow {i}: Build Settings에 씬 {c.sceneName} 없음", this);
            if (chapters.FindIndex(o => o.sceneName == c.sceneName) != i) Debug.LogWarning($"ChapterFlow {i}: 씬 {c.sceneName} 중복, 그 씬에서 바로 시작하면 앞 챕터로 잡힘", this);
        }
    }
#endif
}
