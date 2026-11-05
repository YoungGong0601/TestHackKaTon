// 3회차 영화관 키오스크. 프리팹 Assets/UI/Kiosk/R3/Pack_R3.prefab 루트(KioskScreens와 같은 오브젝트).
// 화면 id: movie hall seat sms pay done
// 버튼 id: bg(화면 전체, 맨 뒤) voice(화면마다) movie0~2 | hall0~2 | seat_<행>_<열> next | key0~9 keyDEL
// 표시 키: seat: pick, on_<행>_<열> | sms: typed sec
// 뜻풀이는 hall 화면의 레이어 KioskReveal 자식 Canvas에 프리팹 글자로 둔다(T16).
using System.Collections;
using UnityEngine;

public class R3CinemaPack : KioskPack
{
    const int Rows = 4, Cols = 6;

    string now, code, typed = "";
    int seatR = -1, seatC;
    float left;
    bool listening;
    PayPoint pay;
    KioskScreens scr;

    public override string FirstScreen => "movie";
    public override bool CanGiveUp => now != "done";

    public override void OnEnter()
    {
        seatR = -1;
        To(FirstScreen);
        if (pay) return;
        pay = Ctl.Pay;
        pay.Approved += OnApproved;
        pay.Empty += OnEmpty;
    }

    void OnDestroy()
    {
        if (!pay) return;
        pay.Approved -= OnApproved;
        pay.Empty -= OnEmpty;
    }

    public override void OnPress(string id)
    {
        if (id == "bg") { Blank(); return; }
        if (id == "voice") { Voice(); return; }
        if (id == "next") { if (seatR >= 0) StartSms(); else Refuse("좌석 미선택"); return; }
        if (id.StartsWith("movie")) { To("hall"); return; }
        if (id.StartsWith("hall")) { To("seat"); DrawSeat(); return; }
        if (id.StartsWith("seat_")) { var p = id.Split('_'); PickSeat(int.Parse(p[1]), int.Parse(p[2])); return; }
        if (id == "keyDEL") { Delete(); return; }
        if (id.StartsWith("key")) Digit(id.Substring(3));
    }

    public override void OnTick(float dt)
    {
        if (now != "sms") return;
        left -= dt;
        Screen("sms").Text("sec", Mathf.Max(0, Mathf.CeilToInt(left)).ToString());
        if (left <= 0f) Retry();
    }

    /// <summary>"다음에 볼게요". 표 없이 키오스크를 떠난다.</summary>
    public void Leave()
    {
        Hud.I.SideNote(null);
        Ctl.Finish();
    }

    // ---- 3-4 좌석 ----

    void PickSeat(int r, int c)
    {
        seatR = r; seatC = c;
        DrawSeat();
    }

    void DrawSeat()
    {
        var s = Screen("seat");
        for (int r = 0; r < Rows; r++)
            for (int c = 0; c < Cols; c++)
                s.Show($"on_{r}_{c}", r == seatR && c == seatC);
        s.Text("pick", seatR < 0 ? "" : $"{(char)('A' + seatR)}{seatC + 1}");
    }

    // ---- 3-8 문자 번호 ----

    void StartSms()
    {
        To("sms");
        NewCode();
    }

    void NewCode()
    {
        code = Random.Range(100000, 1000000).ToString();
        typed = "";
        left = Bal.G("R3_SmsLimitSec", 30f);
        Hud.I.SideNote(code);   // 임시 T17
        Ctl.Sfx("phone_notify", 0.9f);
        DrawSms();
    }

    void Digit(string d)
    {
        typed += d;
        DrawSms();
        if (typed.Length < 6) return;
        if (typed != code) { Retry(); return; }
        Hud.I.SideNote(null);
        To("pay");
    }

    void Delete()
    {
        if (typed.Length == 0) { Refuse("번호 입력"); return; }
        typed = typed.Substring(0, typed.Length - 1);
        DrawSms();
    }

    void Retry()
    {
        NewCode();
        Ctl.Toast("다시 입력하세요");
    }

    void DrawSms() => Screen("sms").Text("typed", typed.PadRight(6, '_'));

    // ---- 3-5 음성 상담 ----

    void Voice()
    {
        Ctl.Toast("듣는 중");
        if (!listening) StartCoroutine(Listen());
    }

    IEnumerator Listen()
    {
        listening = true;
        yield return new WaitForSeconds(Bal.G("R3_VoiceListenSec", 1.5f));
        Ctl.Sfx("kiosk_error", 0.8f);
        Ctl.Say(null, "죄송합니다. 다시 말씀해 주세요.", "k_again");
        listening = false;
    }

    // ---- 3-9 결제 ----

    void OnEmpty() => Ctl.Toast(now == "pay" ? "카드 결제" : "결제 전");

    void OnApproved()
    {
        if (now != "pay") { Ctl.Toast("결제 전"); return; }
        To("done");
        Ctl.Sfx("receipt_print", 0.8f);
        Ctl.Finish();
    }

    void Blank()
    {
        Refuse(now switch
        {
            "movie" => "영화 미선택",
            "hall" => "상영관 미선택",
            "seat" => "좌석 미선택",
            "sms" => "번호 입력",
            "pay" => "카드 결제",
            _ => "발권 완료",
        });
    }

    void To(string id) { now = id; Ctl.Go(id); }
    void Refuse(string text) { Ctl.Sfx("kiosk_error", 0.8f); Ctl.Toast(text); }
    KioskScreen Screen(string id) => (scr ? scr : scr = GetComponent<KioskScreens>()).Get(id);
}
