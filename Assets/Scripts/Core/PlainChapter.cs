using System.Collections;
using UnityEngine;

// Director 없이 넣는 챕터의 최소 진행: 암전을 풀고 조작을 넘기고, exit를 쓰면 다음 챕터로 간다
// 배치: exit = 챕터를 끝내는 Interactable
public class PlainChapter : MonoBehaviour
{
    [SerializeField] Interactable exit;

    void OnEnable() => exit.onUse.AddListener(Finish);
    void OnDisable() => exit.onUse.RemoveListener(Finish);

    IEnumerator Start()
    {
        while (Hud.I.TitleOpen) yield return null;
        yield return Hud.I.Fade(0f, Bal.G("Chapter_FadeInSec", 1f));
        PlayerController.I.Freeze(false);
    }

    void Finish() => GameState.I.CompleteChapter();
}
