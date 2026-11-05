// 키오스크 상태값. 원본 flow.js newK.
using System.Collections.Generic;
using System.Linq;

public sealed class CartLine
{
    public string item, combo, side, drink;
    public bool sizeUp;
    public int price;
}

public sealed class DraftOrder
{
    public string item, combo, side = "fries_r", drink = "cola";
    public bool sizeUp;
}

public sealed class KioskInfo
{
    public string title, mean;
    public bool qr, skip;
    public string[] lines;
}

public sealed class KioskState
{
    public string screen = "idle", tab = "SIGNATURE", place, phone = "", toast, cardMsg, view = "kiosk";
    public int slide, memberErrs;
    public bool memberErr, ad, classicSeen;
    public float toastUntil, adAt, adUntil;
    public DraftOrder draft;
    public KioskInfo info;
    public readonly List<CartLine> cart = new List<CartLine>();
    public int Total => cart.Sum(l => l.price);
}
