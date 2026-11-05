// 시험용 API. 사람 입력 없이 버튼, 틈, 포스터, 영수증을 조작한다.
// 배치: kiosk = 같은 오브젝트의 KioskController
using System.Linq;
using UnityEngine;

public class KioskBot : MonoBehaviour
{
    public static KioskBot I { get; private set; }

    [SerializeField] KioskController kiosk;

    void Awake() => I = this;

    KioskFlow Flow => kiosk.Flow;

    public string Screen => Flow.K.screen;
    public string View => Flow.K.view;
    public float Timer => Flow.K.timer;
    public int CartCount => Flow.K.cart.Count;
    public bool Ad => Flow.K.ad;
    public bool CanTear => Flow.K.canTear;
    public bool Active => kiosk.Active;
    public bool Busy => kiosk.Busy;

    public string[] Ids() => kiosk.Screens.Buttons().Select(b => b.id).ToArray();

    /// <summary>지금 화면의 버튼을 id로 누른다. 없으면 false.</summary>
    public bool Press(string id)
    {
        var b = kiosk.Screens.Find(id);
        return b && Flow.Touch(kiosk.Screens.Uv(b), true);
    }

    public bool Slot(string id) => Flow.Slot(id, true);
    public bool LiftPoster() => Flow.Spot("cover");
    public bool TakeReceipt() => Flow.TakeReceipt();
    public void SetNunchi(float v) { if (kiosk.Nunchi) kiosk.Nunchi.Value = v; }
    public void SetTimer(float sec) => Flow.K.timer = sec;
}
