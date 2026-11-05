// 상태를 배치된 화면에 옮긴다. 켜고 끄기와 글자 값만. 원본 screens.js의 S 함수에 해당.
using System.Linq;
using UnityEngine;
using UnityEngine.UI;
using static KioskData;

public sealed class KioskPresenter
{
    readonly KioskScreens scr;
    readonly KioskState K;

    public KioskPresenter(KioskScreens scr, KioskState K) { this.scr = scr; this.K = K; }

    string PlaceLabel => K.place == "dine" ? "DINE-IN" : "TAKE-OUT";

    // 회색 자리(Img)에 음식 그림을 넣는다
    static void Put(Component owner, string file, string slotName = "Img")
    {
        var slot = owner.transform.Find(slotName);
        if (!slot || !slot.TryGetComponent(out Image image)) return;
        image.sprite = Resources.Load<Sprite>("JW/Food/" + file);
        image.color = Color.white;
        image.preserveAspect = true;
    }

    public void Redraw()
    {
        scr.Show(K.screen);
        var s = scr.Current;
        if (s)
        {
            Draw(s, K.screen);
            if (s.backdrop) Draw(s.backdrop, s.backdrop.id);
        }
        scr.SetInfo(K.info);
        scr.SetToast(K.toast);
    }

    void Draw(KioskScreen s, string id)
    {
        s.Text("place", PlaceLabel);
        switch (id)
        {
            case "idle": for (int i = 0; i < 3; i++) s.Show("slide" + i, K.slide % 3 == i); break;
            case "member": Member(s); break;
            case "menu": Menu(s); break;
            case "option": Option(s); break;
            case "side": Grid(s, SideOpts, K.draft?.side, "side"); break;
            case "drink": Grid(s, DrinkOpts, K.draft?.drink, "drink"); break;
            case "cart": Cart(s); break;
            case "pay": s.Text("total", "총 결제 금액 " + Won(K.Total)); break;
            case "card":
                s.Show("msg_box", K.cardMsg != null);
                s.Text("msg", K.cardMsg ?? "");
                s.Text("total", "결제 금액 " + Won(K.Total));
                break;
            case "paying": s.Fill("bar", K.payProgress); break;
            case "done": s.Text("number", (K.demoNo ?? GameState.I.Order.number).ToString()); break;
        }
    }

    void Member(KioskScreen s)
    {
        string d = (K.phone + "________").Substring(0, 8);
        s.Text("phone", $"010 - {d.Substring(0, 4)} - {d.Substring(4)}");
        s.Show("err", K.memberErr);
        s.Show("skip_dark", K.memberErrs >= 3);
    }

    void Menu(KioskScreen s)
    {
        foreach (var t in Tabs) s.Show("tab_on_" + t, K.tab == t);
        var list = KioskData.Menu[K.tab];
        s.Text("count", $"{list.Length} ITEMS");
        for (int i = 0; i < s.cells.Length; i++)
        {
            var c = s.cells[i];
            if (i >= list.Length) { c.gameObject.SetActive(false); continue; }
            var it = list[i];
            c.Bind("item_" + it.id);
            c.Text("name", it.name);
            c.Text("mean", Mean(it.mean));
            c.Text("price", Won(it.price));
            c.Text("kcal", $"{it.kcal}kcal");
            c.Text("desc", it.desc);
            c.Text("tag", it.tag);
            c.Show("tag_box", it.tag != "");
            Put(c, Picture(it.id));
        }
        s.Show("ad", K.ad);
        int n = K.cart.Count;
        s.Text("item_count", $"{n} ITEM");
        s.Text("total", Won(K.Total));
        s.Show("checkout_off", n == 0);
        for (int i = 0; i < 3; i++) s.Show("thumb" + i, i < n);
    }

    void Option(KioskScreen s)
    {
        var it = ById(K.draft?.item);
        if (it == null) return;
        s.Text("name", it.name);
        s.Text("desc", it.desc);
        s.Text("price", $"{Won(it.price)}  {it.kcal}kcal");
        s.Text("mean", Mean(it.mean));
        Put(s, Picture(it.id));
        for (int i = 0; i < s.cells.Length && i < Combos.Length; i++)
        {
            var o = Combos[i];
            var c = s.cells[i];
            Put(c, Picture(it.id));
            c.Bind("opt_" + o.id);
            c.Text("name", o.name);
            c.Text("sub", o.sub);
            c.Text("price", Won(it.price + o.add));
            c.Text("add", o.add > 0 ? "+" + Won(o.add) : "");
            c.Text("mean", Mean(o.mean));
        }
    }

    void Grid(KioskScreen s, (string id, int add)[] opts, string sel, string key)
    {
        for (int i = 0; i < s.cells.Length; i++)
        {
            var c = s.cells[i];
            if (i >= opts.Length) { c.gameObject.SetActive(false); continue; }
            var (id, add) = opts[i];
            var it = ById(id);
            c.Bind($"{key}_{id}");
            c.Text("name", it.name);
            c.Text("add", add > 0 ? "+" + Won(add) : "+0원");
            c.Text("mean", Mean(it.mean));
            c.Show("on", sel == id);
            Put(c, Picture(id));
        }
    }

    void Cart(KioskScreen s)
    {
        for (int i = 0; i < s.cells.Length; i++)
        {
            var c = s.cells[i];
            if (i >= K.cart.Count) { c.gameObject.SetActive(false); continue; }
            var l = K.cart[i];
            var it = ById(l.item);
            string opts = l.combo != null && l.combo != "single"
                ? $"{Combo(l.combo).name} / {ById(l.side)?.name} / {ById(l.drink)?.name}{(l.sizeUp ? " / SIZE UP" : "")}"
                : l.combo == "single" ? "SINGLE" : "";
            c.Bind("del_" + i);
            c.Text("name", it.name);
            c.Text("opts", opts);
            c.Text("price", Won(l.price));
            c.Text("mean", Mean(l.drink != null ? $"{it.mean}, {ById(l.drink).mean}" : it.mean));
            Put(c, Picture(l.item), "Art");
        }
        s.Show("empty", !K.cart.Any());
        s.Show("promo", K.cart.Count <= 2);
        s.Text("total", Won(K.Total));
        s.Show("checkout_off", !K.cart.Any());
    }
}
