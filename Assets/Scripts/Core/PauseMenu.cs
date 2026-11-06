using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

// Esc 일시정지. 시간과 소리를 멈추고 커서를 꺼내 메뉴를 띄운다. 시작 화면과 씬 전환 중에는 뜨지 않는다
// 시간이 멈춰도 Update는 돌므로 입력을 읽는 곳은 On을 보고 멈춘다. 멈춤을 따라야 하는 실시간 연출은 Dt를 쓴다
// 배치: HUD 루트에 붙인다. panel = Pause (맨 위 자식, 처음 꺼짐), window = 그 자식 Window
// 배치: buttons = Window 자식 Resume, Restart, Quit Image (이 순서)
public class PauseMenu : MonoBehaviour
{
    static bool open;
    static int closedFrame = -1;

    /// <summary>메뉴가 떠 있거나 이번 프레임에 닫혔다. 메뉴를 닫은 클릭이 게임으로 새지 않게 닫힌 프레임까지 참이다.</summary>
    public static bool On => open || Time.frameCount == closedFrame;

    /// <summary>일시정지 중에는 0인 실시간 간격. 연출 진행에 쓴다.</summary>
    public static float Dt => open ? 0f : Time.unscaledDeltaTime;

    [SerializeField] GameObject panel;
    [SerializeField] Transform window;
    [SerializeField] Image[] buttons;
    [SerializeField] Color idle = new Color32(0xe2, 0xde, 0xd3, 255);
    [SerializeField] Color hover = new Color32(0xd2, 0xcd, 0xc0, 255);

    float speed = 1f;
    CursorLockMode cursorLock;
    bool cursorShown;

    void OnDisable()
    {
        if (open) Close();
    }

    void Update()
    {
        var kb = Keyboard.current;
        if (kb != null && kb.escapeKey.wasPressedThisFrame)
        {
            if (open) Close();
            else if (CanOpen) Open();
            return;
        }
        if (!open) return;

        var mouse = Mouse.current;
        if (mouse == null) return;
        var at = mouse.position.ReadValue();
        int over = -1;
        for (int i = 0; i < buttons.Length; i++)
        {
            bool hit = RectTransformUtility.RectangleContainsScreenPoint(buttons[i].rectTransform, at, null);
            buttons[i].color = hit ? hover : idle;
            if (hit) over = i;
        }
        if (over >= 0 && mouse.leftButton.wasPressedThisFrame) Press(over);
    }

    static bool CanOpen
    {
        get
        {
            var g = GameState.I;
            return Hud.I != null && !Hud.I.TitleOpen && g != null && !g.Booting && !g.Loading;
        }
    }

    void Open()
    {
        open = true;
        speed = Time.timeScale;
        Time.timeScale = 0f;
        AudioListener.pause = true;
        cursorLock = Cursor.lockState;
        cursorShown = Cursor.visible;
        Cursor.lockState = CursorLockMode.None;
        Cursor.visible = true;
        foreach (var b in buttons) b.color = idle;
        panel.SetActive(true);
        Hud.I.PopIn(window);
    }

    void Close()
    {
        open = false;
        closedFrame = Time.frameCount;
        panel.SetActive(false);
        Time.timeScale = speed;
        AudioListener.pause = false;
        Cursor.lockState = cursorLock;
        Cursor.visible = cursorShown;
    }

    void Press(int index)
    {
        Close();
        if (index == 1 && GameState.I != null) GameState.I.Restart();
        else if (index == 2) Quit();
    }

    static void Quit()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }
}
