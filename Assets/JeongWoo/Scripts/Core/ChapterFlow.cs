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

}
