// 2회차 카페 키오스크. 프리팹 Assets/UI/Kiosk/R2/Pack_R2.prefab 루트(KioskScreens와 같은 오브젝트).
// 화면 id: menu shot ice coupon point pay cardout done
// 버튼 id: bg(화면 전체, 맨 뒤) tab_0~4 item_<품목> slot0~2 cart_del0~1 cart_close next | shot0 shot1 | ice0~2 | coupon_none | point_skip
// 표시 키: menu cart_total cart_count count cart_list row0 row1 row0_name row0_price | 칸 name en price kcal on tag tag_box | shot, ice cup_name | done number
// 흐름: 2잔을 담고 다음, 음료마다 shot과 ice, 그 뒤 coupon point pay cardout done. 쪽지와 다른 메뉴도 막지 않고 수령 때 판정한다
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class R2CafePack : KioskPack
{
    const int Cups = 2;
    const string Answer1 = "americano", Answer2 = "icetea";

    sealed class Item
    {
        public string id, name, en, art, tag;
        public int price, kcal;
        public bool drink;
        public Item(string id, string name, string en, int price, int kcal, string art, bool drink = true, string tag = "")
        {
            this.id = id; this.name = name; this.en = en; this.price = price; this.kcal = kcal; this.art = art; this.drink = drink; this.tag = tag;
        }
    }

    class Cup { public Item item; public string shot, ice; }

    static readonly Item[][] Tabs =
    {
        new[]
        {
            new Item("americano", "아메리카노", "Iced Americano", 4500, 10, "food_coffee", true, "BEST"),
            new Item("latte", "카페라떼", "Caffe Latte", 5000, 180, "food_latte"),
            new Item("vanilla", "바닐라 라떼", "Vanilla Latte", 5500, 240, "food_latte"),
            new Item("cappuccino", "카푸치노", "Cappuccino", 5000, 150, "food_latte"),
            new Item("coldbrew", "콜드브루", "Cold Brew", 5000, 15, "food_coffee"),
            new Item("espresso", "에스프레소", "Espresso", 3500, 5, "food_coffee"),
        },
        new[]
        {
            new Item("choco", "초코 라떼", "Choco Latte", 5500, 320, "food_shake"),
            new Item("strawberry", "딸기 라떼", "Strawberry Latte", 5800, 300, "food_shake"),
            new Item("lemonade", "레몬 에이드", "Lemonade", 5000, 170, "food_tea"),
            new Item("grapefruit", "자몽 에이드", "Grapefruit Ade", 5200, 180, "food_tea"),
            new Item("milk", "우유", "Fresh Milk", 3500, 130, "food_shake"),
            new Item("smoothie", "요거트 스무디", "Yogurt Smoothie", 5800, 340, "food_shake"),
        },
        new[]
        {
            new Item("icetea", "아이스티", "Peach Iced Tea", 4500, 120, "food_tea", true, "BEST"),
            new Item("earlgrey", "얼그레이", "Earl Grey", 4500, 5, "food_tea"),
            new Item("chamomile", "캐모마일", "Chamomile", 4500, 5, "food_tea"),
            new Item("yuja", "유자차", "Yuja Tea", 5000, 160, "food_tea"),
            new Item("green", "녹차", "Green Tea", 4500, 5, "food_tea"),
            new Item("peppermint", "페퍼민트", "Peppermint", 4500, 5, "food_tea"),
        },
        new[]
        {
            new Item("cheesecake", "치즈 케이크", "Cheese Cake", 6000, 380, "icon_cake", false),
            new Item("choco_cake", "초코 케이크", "Chocolate Cake", 6200, 420, "icon_cake", false),
            new Item("sundae", "아이스크림", "Soft Ice Cream", 3500, 210, "food_sundae", false),
            new Item("stick", "시나몬 스틱", "Cinnamon Stick", 2800, 200, "food_stick", false),
            new Item("cookie", "버터 쿠키", "Butter Cookie", 2500, 180, "food_stick", false),
            new Item("financier", "피낭시에", "Financier", 3000, 190, "food_stick", false),
        },
        new[]
        {
            new Item("season_brew", "시즌 콜드브루", "Season Cold Brew", 5500, 20, "food_coffee", true, "NEW"),
            new Item("season_latte", "밤 라떼", "Chestnut Latte", 6000, 280, "food_latte", true, "NEW"),
            new Item("season_tea", "홍시 티", "Persimmon Tea", 5500, 150, "food_tea", true, "NEW"),
            new Item("season_shake", "고구마 쉐이크", "Sweet Potato Shake", 6200, 360, "food_shake"),
            new Item("season_ice", "단호박 아이스크림", "Pumpkin Ice Cream", 4000, 230, "food_sundae", false),
            new Item("season_cake", "밤 케이크", "Chestnut Cake", 6500, 400, "icon_cake", false),
        },
    };

    // 배치: slots = MY ORDER 칸 Image 3개, cupArt = americano, latte, 그 밖 순서의 잔 그림, emptyArt = 빈 칸 그림
    [SerializeField] Image[] slots = new Image[0];
    [SerializeField] Sprite[] cupArt = new Sprite[0];
    [SerializeField] Sprite emptyArt;
    // 배치: art = 품목 그림(이름으로 찾는다), tabOn = Tab_On, rowArt = 담은 목록 칸의 그림 2개
    [SerializeField] Sprite[] art = new Sprite[0];
    [SerializeField] RectTransform tabOn;
    [SerializeField] Image[] rowArt = new Image[0];

    readonly List<Cup> cart = new List<Cup>();
    readonly Stack<(string screen, int cup)> trail = new Stack<(string, int)>();   // 이전 버튼이 돌아갈 화면들
    int cup, tab;
    string now;
    const string MyPhone = "01055550147";   // 포스트잇 쪽지에 적힌 가상 번호
    bool leaving, listOpen, pulled, popApp, popPoint;
    string phone = "";
    float fogAt;
    PayPoint pay;
    KioskScreens scr;
    KioskHardware hw;

    KioskScreens Scr => scr ? scr : scr = GetComponent<KioskScreens>();

    public override string FirstScreen => "menu";
    public override bool CanGiveUp => false;   // 다 차면 버튼 없이 비켜난다
    public override bool Timed => !leaving && !Paid && (now != FirstScreen || cart.Count > 0);

    /// <summary>알바생에게 물어봐야 켜진다. 꺼져 있으면 주문하기가 막힌다.</summary>
    public bool Unlocked { get; set; }
    public event System.Action Blocked;
    /// <summary>메뉴를 담을 때마다.</summary>
    public event System.Action Added;

    /// <summary>결제까지 끝나서 키오스크를 떠났다. false면 눈치로 비켜난 것.</summary>
    public bool Paid { get; private set; }

    public override void OnEnter()
    {
        cart.Clear();
        cup = 0;
        tab = 0;
        leaving = false;
        listOpen = false;
        popApp = popPoint = false;
        Paid = false;
        PostState.EyeFogStart = -1f;
        fogAt = NextFog();
        Refresh();
        To(FirstScreen);
        trail.Clear();
        Refresh();
        hw = Ctl.GetComponent<KioskHardware>();
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

    // 결제 창에 가기 전에 다 차면 비켜난다(공통 규칙)
    public override void OnTick(float dt)
    {
        EyeFog();
        if (now == "pay" || now == "cardout" || now == "done") return;
        if (Ctl.Nunchi.Running && Ctl.Nunchi.Value >= Bal.G("Nunchi_Max", 100f)) Leave();
    }

    static float NextFog() => Time.time + Bal.G("Age40_BlurEverySec", 27f) * Random.Range(0.74f, 1.3f);

    // 40대는 키오스크를 보는 동안 가끔 눈이 흐려진다. 후처리가 시작 시각을 보고 알아서 끝낸다
    void EyeFog()
    {
        if (GameState.I.Profile.handLook != 1 || Time.time < fogAt) return;
        PostState.EyeFogStart = Time.time;
        fogAt = NextFog();
    }

    // 큰 수락은 앱으로 보낼 뿐 넘어가지 않는다. 작은 거절로만 닫힌다
    void Pop(string id)
    {
        now = id;
        Ctl.Sfx("kiosk_popup", 0.8f);
        Ctl.Go(id);
    }

    void PopNo()
    {
        Ctl.Sfx("kiosk_tap", 0.8f);
        if (now == "pop_app") { now = "menu"; NextDrink(-1); }
        else { now = "coupon"; To("pay"); }
    }

    void Key(string k)
    {
        if (k == "del") { if (phone.Length > 0) phone = phone.Substring(0, phone.Length - 1); }
        else if (k == "ok")
        {
            if (phone != MyPhone)
            {
                phone = "";
                Refuse("번호 확인");
            }
            else
            {
                Ctl.Sfx("kiosk_ok", 0.5f);
                Ctl.Toast("적립 완료");
                now = "coupon";
                To("pay");
                return;
            }
        }
        else if (phone.Length < MyPhone.Length) phone += k;
        Ctl.Sfx("kiosk_tap", 0.6f);
        ShowPhone();
    }

    void ShowPhone()
    {
        string p = phone;
        if (p.Length > 7) p = p.Substring(0, 3) + "-" + p.Substring(3, 4) + "-" + p.Substring(7);
        else if (p.Length > 3) p = p.Substring(0, 3) + "-" + p.Substring(3);
        Scr.Get("pop_point").Text("phone", p);
    }

    // 처음 화면으로. 담은 잔을 비운다. 눈치는 그대로
    public override void OnTimeout()
    {
        Ctl.Say("kiosk", "처음 화면으로 돌아갑니다.", "k_home");
        Ctl.Sfx("kiosk_error", 0.3f);
        cart.Clear();
        cup = 0;
        tab = 0;
        listOpen = false;
        popApp = popPoint = false;
        To(FirstScreen);
        trail.Clear();
        Refresh();
    }

    public void Leave()
    {
        if (leaving || Ctl.Busy) return;
        leaving = true;
        GameState.I.Stats.resets++;
        Ctl.Finish(Bal.G("Nunchi_FullLeaveSec", 0.2f));
    }

    public override void OnPress(string id)
    {
        if (leaving) return;
        if (id.StartsWith("tab_")) { tab = int.Parse(id.Substring(4)); Ctl.Sfx("kiosk_tap", 0.6f); Refresh(); return; }
        if (id.StartsWith("item_")) { Add(id.Substring(5)); return; }
        if (id.StartsWith("cart_del")) { Remove(id[8] - '0'); return; }
        if (id.StartsWith("key_")) { Key(id.Substring(4)); return; }
        switch (id)
        {
            case "slot0": case "slot1": case "slot2":
                if (cart.Count == 0) { Refuse("빈 칸"); return; }
                listOpen = true;
                Ctl.Sfx("kiosk_popup", 0.6f);
                Refresh();
                break;
            case "cart_close": listOpen = false; Refresh(); break;
            case "next" when !Unlocked && cart.Count > 0: Blocked?.Invoke(); break;
            case "next" when cart.Count == Cups && !popApp: popApp = true; Pop("pop_app"); break;
            case "next": if (cart.Count == Cups) NextDrink(-1); else Refuse(cart.Count == 0 ? "메뉴 미선택" : "2잔 미선택"); break;
            case "shot0": case "shot1": cart[cup].shot = id == "shot1" ? "샷 추가" : null; ToIce(); break;
            case "ice0": cart[cup].ice = "얼음 적게"; NextDrink(cup); break;
            case "ice1": cart[cup].ice = null; NextDrink(cup); break;
            case "ice2": cart[cup].ice = "얼음 많이"; NextDrink(cup); break;
            case "coupon_none" when !popPoint: popPoint = true; phone = ""; ShowPhone(); Pop("pop_point"); break;
            case "coupon_none": To("pay"); break;
            case "point_skip": To("pay"); break;
            case "pop_yes": Refuse("앱 설치 후 이용 가능"); break;
            case "pop_no": PopNo(); break;
            case "back": Back(); break;
            case "bg": Blank(); break;
        }
    }

    static Item Find(string id)
    {
        foreach (var list in Tabs) foreach (var i in list) if (i.id == id) return i;
        return null;
    }

    // 같은 음료를 두 잔 담아도 된다. 빼는 것은 MY ORDER 목록에서
    void Add(string id)
    {
        if (cart.Count >= Cups) { Refuse("2잔까지 선택"); return; }
        var it = Find(id);
        if (it == null) return;
        cart.Add(new Cup { item = it });
        Ctl.Sfx("kiosk_ok", 0.5f);
        Refresh();
        Ctl.Toast($"{it.name} {cart.Count}잔째");
        Added?.Invoke();
    }

    void Remove(int i)
    {
        if (i < 0 || i >= cart.Count) return;
        cart.RemoveAt(i);
        if (cart.Count == 0) listOpen = false;
        Ctl.Sfx("kiosk_tap", 0.8f);
        Refresh();
    }

    Sprite Art(string name)
    {
        foreach (var s in art) if (s && s.name == name) return s;
        return null;
    }

    void Refresh()
    {
        var menu = Scr.Get("menu");
        if (!menu) return;
        var items = Tabs[tab];
        if (tabOn) tabOn.anchoredPosition = new Vector2(3f + tab * 216f, tabOn.anchoredPosition.y);
        menu.Text("count", $"{items.Length} ITEMS");
        for (int i = 0; i < menu.cells.Length; i++)
        {
            var c = menu.cells[i];
            if (i >= items.Length) { c.gameObject.SetActive(false); continue; }
            var it = items[i];
            c.Bind("item_" + it.id);
            c.Text("name", it.name);
            c.Text("en", it.en);
            c.Text("price", KioskData.Won(it.price));
            c.Text("kcal", $"{it.kcal}kcal");
            c.Text("tag", it.tag);
            c.Show("tag_box", it.tag != "");
            c.Show("on", cart.Exists(l => l.item == it));
            var photo = c.transform.Find("Deco_Card/Photo");
            if (photo && photo.TryGetComponent(out Image image)) { image.sprite = Art(it.art); image.preserveAspect = true; }
        }
        for (int i = 0; i < slots.Length; i++)
        {
            if (!slots[i]) continue;
            bool has = i < cart.Count;
            slots[i].sprite = has ? Art(cart[i].item.art) : emptyArt;
            slots[i].color = has ? Color.white : new Color(1f, 1f, 1f, 0.25f);
            slots[i].preserveAspect = true;
        }
        int total = 0;
        foreach (var c in cart) total += c.item.price + (c.shot != null ? Bal.I("R2_ShotPrice", 500) : 0);
        menu.Text("cart_total", KioskData.Won(total));
        menu.Text("cart_count", $"{cart.Count} ITEM");
        menu.Show("cart_list", listOpen);
        for (int i = 0; i < Cups; i++)
        {
            bool has = i < cart.Count;
            menu.Show("row" + i, has);
            if (!has) continue;
            menu.Text($"row{i}_name", cart[i].item.name);
            menu.Text($"row{i}_price", KioskData.Won(cart[i].item.price));
            if (i < rowArt.Length && rowArt[i]) { rowArt[i].sprite = Art(cart[i].item.art); rowArt[i].preserveAspect = true; }
        }
    }

    void NextDrink(int from)
    {
        for (int i = from + 1; i < cart.Count; i++)
        {
            if (!cart[i].item.drink) continue;
            cup = i;
            Label("shot");
            To("shot");
            Ctl.Toast(cart[cup].item.name);
            return;
        }
        var lines = new List<string>();
        foreach (var c in cart)
        {
            string s = c.item.name;
            if (c.shot != null) s += " " + c.shot;
            if (c.ice != null) s += " " + c.ice;
            lines.Add(s);
        }
        GameState.I.Order.item = string.Join("\n", lines);
        To("coupon");
    }

    void ToIce()
    {
        Label("ice");
        To("ice");
        Ctl.Toast(cart[cup].item.name);
    }

    void Label(string screen) => Scr.Get(screen).Text("cup_name", cart[cup].item.name);

    void Blank()
    {
        Refuse(now switch
        {
            "done" => "주문 완료",
            "pay" => "카드 결제",
            "cardout" => "카드 제거",
            "menu" => "메뉴 미선택",
            _ => "항목 미선택",
        });
    }

    void OnEmpty()
    {
        if (now == "cardout") { pulled = true; return; }
        Ctl.Toast(now == "pay" ? "카드 결제" : "결제 전");
    }

    public override bool Hit(Collider col)
    {
        if (now != "cardout" || !col.GetComponentInParent<PayPoint>()) return false;
        pulled = true;
        return true;
    }

    void OnApproved()
    {
        if (now != "pay") { Ctl.Toast("결제 전"); return; }
        HandRig.I.Equip(ItemId.None);
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.In);
        StartCoroutine(CardOut());
    }

    // 카드를 뺄 때까지 멈춘다. 재촉만 하고 넘어가지 않는다
    IEnumerator CardOut()
    {
        pulled = false;
        To("cardout");
        Ctl.Say("kiosk", "카드를 제거해 주세요.", "k_cardout");
        float beep = Time.time + Bal.G("Kiosk_CardOutBeepSec", 3f);
        while (!pulled)
        {
            if (Time.time >= beep)
            {
                beep = Time.time + Bal.G("Kiosk_CardOutBeepSec", 3f);
                Ctl.Sfx("kiosk_error", 0.3f);
                Ctl.Toast("카드 제거");
            }
            yield return null;
        }
        if (hw) hw.CardAt("ic", Ctl.Out, KioskCard.Move.Out);
        Ctl.Sfx("card_insert", 0.5f, 1.25f);
        Paid = true;
        To("done");
        Scr.Get("done").Text("number", GameState.I.Order.number.ToString());
        yield return new WaitForSeconds(Bal.G("R2_DoneShowSec", 2.5f));
        Ctl.Finish();
    }

    void To(string id)
    {
        if (now != null && now != id) trail.Push((now, cup));
        now = id;
        Ctl.Go(id);
    }

    // 바로 앞 화면으로. 담은 잔과 고른 값은 그대로 둔다
    void Back()
    {
        if (trail.Count == 0) return;
        var step = trail.Pop();
        cup = step.cup;
        if (step.screen == "shot" || step.screen == "ice") Label(step.screen);
        now = step.screen;
        Ctl.Go(now);
        Refresh();
    }
    void Refuse(string text) { GameState.I.Stats.wrong++; Ctl.Sfx("kiosk_error", 0.8f); Ctl.Toast(text); }
}
