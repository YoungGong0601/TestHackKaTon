using System.Collections;
using TMPro;
using UnityEngine;
using UnityEngine.InputSystem;

// HUD 위 회차 공통 화면 요소. 정적 입구(Round, Choice, Ending)가 이것을 쓴다. 부착: HUD 루트
// 배치: lidTop, lidBottom = Lid_Top, Lid_Bottom (검정 Image, 가로 전체, 눈치와 HUD 글자 위, Fade 아래)
// 배치: sideNote = SideNote (왼쪽 위 작은 글자)
// 배치: choiceGroup = Choice (화면 중앙 아래 CanvasGroup, 처음 alpha 0), choiceRows = 자식 Row_0..3 RectTransform, choiceLabels = 각 Row의 글자
// 배치: giveUp = GiveUp (오른쪽 아래 버튼, 처음 꺼짐), giveUpLabel = 자식 글자
// 배치: endGroup = End (전체 화면 검정 CanvasGroup, 맨 위, 처음 꺼짐), endStat, endSource, endTitle = 자식 글자
public class RoundUi : MonoBehaviour
{
    public static RoundUi I { get; private set; }

    [SerializeField] RectTransform lidTop;
    [SerializeField] RectTransform lidBottom;
    [SerializeField] TMP_Text sideNote;
    [SerializeField] CanvasGroup choiceGroup;
    [SerializeField] RectTransform[] choiceRows = new RectTransform[0];
    [SerializeField] TMP_Text[] choiceLabels = new TMP_Text[0];
    [SerializeField] RectTransform giveUp;
    [SerializeField] TMP_Text giveUpLabel;
    [SerializeField] CanvasGroup endGroup;
    [SerializeField] TMP_Text endStat;
    [SerializeField] TMP_Text endSource;
    [SerializeField] TMP_Text endTitle;
    [SerializeField] GameObject endStatImage, endTitleImage;   // 서울알림체 글자 그림. TMP는 투명으로 남아 문구 기록만 맡는다
    [SerializeField] UnityEngine.UI.Image endNumber;    // 배치: End/Stat_Image/Number (Filled 세로)
    [SerializeField] CanvasGroup endCopy;               // 배치: End/Stat_Image/Stat
    [SerializeField] CanvasGroup endResult;             // 배치: End/Result (처음 꺼짐, 고정 글자는 서울알림체 그림)
    [SerializeField] TMP_Text[] endValues = new TMP_Text[0];   // 배치: Result 안 값 글자 6개, 걸린 시간부터 차례로
    [SerializeField] CanvasGroup endFoot;               // 배치: End/Stat_Image/Source, End/Restart를 묶은 EndFoot

    public int ChoiceSlots => choiceRows.Length;
    public bool ChoiceOpen { get; private set; }
    public bool GiveUpShown => giveUp != null && giveUp.gameObject.activeSelf;

    /// <summary>이번 클릭이 HUD 버튼 몫이라 키오스크가 받으면 안 될 때.</summary>
    public bool Blocks => ChoiceOpen || (GiveUpShown && Over(giveUp));

    void Awake()
    {
        if (I != null && I != this) return;
        I = this;
    }

    public void SideNote(string text)
    {
        if (sideNote != null) sideNote.text = Hud.Mark(text ?? "");
    }

    // 0 뜸, 1 감음. 아래위 눈꺼풀이 가운데서 만난다
    public void Lids(float k)
    {
        if (lidTop == null || lidBottom == null) return;
        float h = k * 0.52f;
        lidTop.anchorMin = new Vector2(0f, 1f - h);
        lidTop.anchorMax = Vector2.one;
        lidBottom.anchorMin = Vector2.zero;
        lidBottom.anchorMax = new Vector2(1f, h);
        lidTop.offsetMin = lidTop.offsetMax = lidBottom.offsetMin = lidBottom.offsetMax = Vector2.zero;
        lidTop.gameObject.SetActive(k > 0f);
        lidBottom.gameObject.SetActive(k > 0f);
    }

    public void GiveUp(string label)
    {
        if (giveUp == null) return;
        giveUp.gameObject.SetActive(label != null);
        if (giveUpLabel != null && label != null) giveUpLabel.text = label;
    }

    public bool GiveUpClicked() => GiveUpShown && Clicked && Over(giveUp);

    public void ChoiceShow(string[] labels)
    {
        ChoiceOpen = labels != null;
        if (choiceGroup != null) choiceGroup.alpha = ChoiceOpen ? 1f : 0f;
        for (int i = 0; i < choiceRows.Length; i++)
        {
            bool on = ChoiceOpen && i < labels.Length;
            choiceRows[i].gameObject.SetActive(on);
            if (on) choiceLabels[i].text = labels[i];
        }
    }

    // 포인터 아래 줄 번호. 없으면 -1. 고를 수 있는 줄은 살짝 커진다
    public int ChoiceHover()
    {
        int hit = -1;
        for (int i = 0; i < choiceRows.Length; i++)
        {
            var row = choiceRows[i];
            if (!row.gameObject.activeSelf) continue;
            bool over = Over(row);
            row.localScale = Vector3.one * (over ? 1.06f : 1f);
            if (over) hit = i;
        }
        return hit;
    }

    public void End(bool on)
    {
        if (endGroup == null) return;
        endGroup.gameObject.SetActive(on);
        endGroup.alpha = on ? 1f : 0f;
        if (endStat != null) endStat.text = "";
        if (endSource != null) endSource.text = "";
        if (endTitle != null) endTitle.text = "";
        if (endStatImage != null) endStatImage.SetActive(false);
        if (endTitleImage != null) endTitleImage.SetActive(false);
        if (endResult != null) endResult.gameObject.SetActive(false);
    }

    /// <summary>통계를 걷고 같은 배경 위에 결산을 띄운다. 항목은 프로토타입 결과 화면과 같다.</summary>
    public IEnumerator EndResult()
    {
        if (!endResult) yield break;
        var st = GameState.I.Stats;
        string[] rows =
        {
            Clock((st.endTime >= 0f ? st.endTime : Time.time) - st.startTime),
            $"{st.touches}번",
            $"{st.wrong}번",
            $"{st.sorry}번",
            $"{st.resets}번",
            st.memoOk ? "예" : "아니오",
        };
        for (int i = 0; i < rows.Length && i < endValues.Length; i++) endValues[i].text = rows[i];
        float sec = Bal.G("End_CopySec", 0.6f);
        yield return Run(sec, k => { if (endCopy) endCopy.alpha = 1f - k; if (endFoot) endFoot.alpha = 1f - k; });
        if (endStatImage != null) endStatImage.SetActive(false);
        if (endTitleImage != null) endTitleImage.SetActive(false);
        endResult.gameObject.SetActive(true);
        endResult.alpha = 0f;
        yield return Run(sec, k => endResult.alpha = k);
    }

    static string Clock(float sec)
    {
        int s = Mathf.Max(0, Mathf.RoundToInt(sec)), m = s / 60;
        return m > 0 ? $"{m}분 {s % 60}초" : $"{s}초";
    }

    public void EndStat(string stat, string source)
    {
        if (endStatImage != null) endStatImage.SetActive(true);
        if (endStat != null) endStat.text = stat;
        if (endSource != null) endSource.text = source;
    }

    /// <summary>화면이 서서히 밝아지고 숫자가 아래에서 차오른 뒤 카피와 출처가 나온다.</summary>
    public IEnumerator EndReveal()
    {
        float fade = Bal.G("End_FadeSec", 1f), fill = Bal.G("End_FillSec", 1.2f), copy = Bal.G("End_CopySec", 0.6f);
        if (endNumber) endNumber.fillAmount = 0f;
        if (endCopy) endCopy.alpha = 0f;
        if (endFoot) endFoot.alpha = 0f;
        yield return Run(fade, k => endGroup.alpha = k);
        yield return Run(fill, k => { if (endNumber) endNumber.fillAmount = k; });
        yield return Run(copy, k => { if (endCopy) endCopy.alpha = k; if (endFoot) endFoot.alpha = k; });
    }

    static IEnumerator Run(float sec, System.Action<float> set)
    {
        for (float t = 0f; t < sec; t += Time.unscaledDeltaTime)
        {
            float k = t / sec;
            set(k * k * (3f - 2f * k));
            yield return null;
        }
        set(1f);
    }

    public void EndTitle(string title)
    {
        if (endTitleImage != null) endTitleImage.SetActive(true);
        if (endTitle != null) endTitle.text = title;
    }

    public static bool Clicked
    {
        get
        {
            var mouse = Mouse.current;
            return mouse != null && mouse.leftButton.wasPressedThisFrame;
        }
    }

    // 키오스크 포인터는 떨림과 지연이 든 자리, 그 밖에는 실제 마우스
    static Vector2 Pointer()
    {
        var pc = PlayerController.I;
        if (pc != null && pc.CurrentMode == PlayerController.Mode.Cursor && HandRig.I != null)
        {
            var p = HandRig.I.Ptr01();
            return new Vector2(p.x * Screen.width, p.y * Screen.height);
        }
        var mouse = Mouse.current;
        return mouse != null ? mouse.position.ReadValue() : Vector2.zero;
    }

    static bool Over(RectTransform rect)
    {
        var canvas = rect.GetComponentInParent<Canvas>();
        var cam = canvas != null && canvas.renderMode != RenderMode.ScreenSpaceOverlay ? canvas.worldCamera : null;
        return RectTransformUtility.RectangleContainsScreenPoint(rect, Pointer(), cam);
    }
}
