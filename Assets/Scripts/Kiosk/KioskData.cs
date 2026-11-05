// 메뉴 데이터. 원본 src/kiosk/data.js 그대로. name은 화면 글자, mean은 돋보기로만 보이는 뜻.
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

public sealed class MenuItem
{
    public string id, name, mean, tag, desc, kind;
    public int price, kcal;
    public MenuItem(string id, string name, string mean, int price, int kcal, string kind, string tag = "", string desc = "")
    {
        this.id = id; this.name = name; this.mean = mean; this.price = price; this.kcal = kcal; this.kind = kind; this.tag = tag; this.desc = desc;
    }
}

public sealed class ComboDef
{
    public string id, name, mean, sub;
    public int add;
    public ComboDef(string id, string name, string mean, int add, string sub) { this.id = id; this.name = name; this.mean = mean; this.add = add; this.sub = sub; }
}

public static class KioskData
{
    /// <summary>1회차에 고르는 말. 4회차 뒷사람이 같은 말을 한다.</summary>

    public static readonly string[] Tabs = { "SIGNATURE", "PREMIUM", "CLASSIC", "SIDE", "BEVERAGE", "DESSERT" };

    static MenuItem B(string id, string name, string mean, int price, int kcal, string tag, string desc) => new MenuItem(id, name, mean, price, kcal, "burger", tag, desc);
    static MenuItem X(string id, string name, string mean, int price, int kcal, string kind) => new MenuItem(id, name, mean, price, kcal, kind);

    public static readonly Dictionary<string, MenuItem[]> Menu = new Dictionary<string, MenuItem[]>
    {
        ["SIGNATURE"] = new[]
        {
            B("crown3", "크라운 트리플 스택", "고기 세 장 버거", 11900, 1120, "BEST", "Triple Flame Grilled"),
            B("truffle", "앵거스 트러플 오 그라탕", "버섯향 소고기 버거", 12400, 980, "NEW", "Limited Reserve"),
            B("kgrill", "더 그랜드 K-그릴 플래티넘", "구운 소고기 버거", 10900, 890, "", "Char Broiled Edition"),
            B("habanero", "하바네로 인페르노 비프", "아주 매운 버거", 9900, 760, "HOT", "Scoville 8,000"),
            B("avocado", "아보카도 슈프림 그릴드", "아보카도 버거", 10400, 720, "", "Fresh Cut Daily"),
            B("smokehouse", "로열 스모크 하우스", "훈제 고기 버거", 11200, 930, "", "Hickory Reserve"),
            B("buttermilk", "버터밀크 크런치 XL", "닭고기 버거", 9400, 840, "", "Southern Style"),
            B("mushtower", "왕관 머쉬룸 타워", "버섯 버거", 10100, 790, "", "Wild Forest"),
            B("plant", "비욘드 크라운 플랜트", "콩고기 버거", 9800, 610, "ECO", "Zero Animal"),
        },
        ["PREMIUM"] = new[]
        {
            B("wagyu", "와규 크라운 리저브", "일본 소 버거", 14900, 1040, "NEW", "A5 Blend Patty"),
            B("lobster", "랍스터 비스크 쉬림프", "새우 버거", 13900, 820, "", "Ocean Edition"),
            B("brisket", "12H 브리스킷 멜트", "오래 삶은 고기 버거", 13400, 1010, "", "Low and Slow"),
            B("gorgon", "고르곤졸라 앤 허니", "꿀 치즈 버거", 12900, 870, "", "Sweet Blue Cheese"),
            B("katsu", "돈카츠 프리미엄 소스", "돈가스 버거", 11900, 910, "", "Panko Crust"),
            B("crownmax", "크라운 맥시멈", "제일 큰 버거", 15900, 1380, "BEST", "Maximum Stack"),
        },
        ["CLASSIC"] = new[]
        {
            B("royal", "오리지널 로열 패티", "고기 버거", 5400, 620, "", "Since 1998"),
            B("mushroom", "스모키 BBQ 더블 머쉬룸", "버섯 버거", 6900, 740, "BEST", "Smoky Double"),
            B("chicken", "크리스피 K-치킨", "닭고기 버거", 5600, 610, "", "Crispy Fillet"),
            B("bulgogi2", "K-BBQ 스모키 비프 더블", "불고기 두 장 버거", 7900, 860, "", "Double Patty"),
            B("bulgogi", "K-BBQ 스모키 비프", "불고기 버거", 6900, 590, "", "Sweet Soy Glaze"),
            B("shrimp", "코리안 쉬림프 크런치", "새우 버거", 5900, 570, "", "Whole Shrimp"),
            B("cheese", "더블 치즈 멜트", "치즈 버거", 6100, 680, "", "American Melt"),
            B("kids", "크라운 주니어", "작은 버거", 3900, 380, "", "Junior Size"),
            B("fish", "씨 크리스피 필레", "생선 버거", 5400, 520, "", "Sea Fillet"),
        },
        ["SIDE"] = new[]
        {
            X("fries_r", "프렌치 프라이 R", "감자튀김 보통", 2000, 320, "side"),
            X("fries_l", "프렌치 프라이 L", "감자튀김 큰 것", 2500, 460, "side"),
            X("nugget", "크라운 너겟 4PC", "닭 튀김 네 개", 2800, 290, "side"),
            X("coleslaw", "시그니처 슬로", "양배추 샐러드", 2000, 140, "side"),
            X("cheesestick", "모짜 스틱 2PC", "치즈 막대 튀김", 2900, 310, "side"),
            X("onion", "어니언 링 6PC", "양파 튀김", 2700, 340, "side"),
        },
        ["BEVERAGE"] = new[]
        {
            X("cola", "제로 콜라", "콜라", 2000, 0, "drink"),
            X("cider", "라임 스파클링", "사이다", 2000, 140, "drink"),
            X("cola_full", "오리지널 콜라", "콜라", 2000, 150, "drink"),
            X("orange", "선셋 오렌지 에이드", "오렌지 음료", 2500, 170, "drink"),
            X("tea", "아이스 얼그레이", "찬 홍차", 2500, 40, "drink"),
            X("americano", "아메리카노 ICE", "찬 커피", 2000, 10, "drink"),
            X("shake", "바닐라 쉐이크", "우유 음료", 3000, 380, "drink"),
            X("water", "미네랄 워터", "생수", 1500, 0, "drink"),
        },
        ["DESSERT"] = new[]
        {
            X("cone", "소프트 콘", "아이스크림", 1200, 180, "dessert"),
            X("pie", "애플 턴오버", "사과 파이", 1800, 240, "dessert"),
            X("sundae", "카라멜 선데", "컵 아이스크림", 2400, 310, "dessert"),
            X("churro", "시나몬 스틱 3PC", "계피 과자", 2200, 280, "dessert"),
        },
    };

    public static readonly ComboDef[] Combos =
    {
        new ComboDef("single", "SINGLE", "단품", 0, "A la carte"),
        new ComboDef("combo", "COMBO", "세트", 2000, "Side + Beverage"),
        new ComboDef("large", "LARGE COMBO", "큰 세트", 2800, "Side L + Beverage L"),
    };

    public static readonly (string id, int add)[] SideOpts = { ("fries_r", 0), ("fries_l", 500), ("nugget", 800), ("coleslaw", 0), ("cheesestick", 900), ("onion", 700) };
    public static readonly (string id, int add)[] DrinkOpts = { ("cola", 0), ("cola_full", 0), ("cider", 0), ("orange", 500), ("tea", 500), ("americano", 0), ("shake", 1000), ("water", 0) };

    static readonly Dictionary<string, string> Pictures = new Dictionary<string, string>
    {
        ["kgrill"] = "burger_bulgogi", ["bulgogi"] = "burger_bulgogi",
        ["crown3"] = "burger_double", ["wagyu"] = "burger_double", ["crownmax"] = "burger_double", ["bulgogi2"] = "burger_double", ["mushtower"] = "burger_double",
        ["habanero"] = "burger_bacon", ["smokehouse"] = "burger_bacon", ["brisket"] = "burger_bacon", ["mushroom"] = "burger_bacon",
        ["buttermilk"] = "burger_chicken", ["katsu"] = "burger_chicken", ["chicken"] = "burger_chicken", ["fish"] = "burger_chicken",
        ["lobster"] = "burger_shrimp", ["shrimp"] = "burger_shrimp",
        ["fries_r"] = "fries", ["fries_l"] = "fries", ["onion"] = "fries", ["coleslaw"] = "fries",
        ["nugget"] = "nuggets", ["cheesestick"] = "nuggets", ["churro"] = "nuggets",
        ["cola"] = "cola", ["cola_full"] = "cola", ["tea"] = "cola",
        ["cider"] = "cider", ["orange"] = "cider", ["water"] = "cider",
        ["americano"] = "coffee", ["shake"] = "softcone", ["cone"] = "softcone", ["sundae"] = "softcone", ["pie"] = "softcone",
    };
    public static string Picture(string id) => Pictures.TryGetValue(id, out var p) ? p : "burger_cheese";

    /// <summary>업셀 화면의 콤보 사진.</summary>
    public static string ComboPicture(string id) => id switch
    {
        "bulgogi2" => "combo_bulgogi2",
        "cheese" => "combo_cheese",
        "shrimp" => "combo_shrimp",
        "crown3" or "crownmax" or "wagyu" => "combo_triple",
        _ => "combo_bulgogi",
    };

    static Dictionary<string, MenuItem> all;
    public static MenuItem ById(string id)
    {
        if (id == null) return null;
        all ??= Menu.Values.SelectMany(v => v).ToDictionary(i => i.id);
        return all.TryGetValue(id, out var it) ? it : null;
    }
    public static ComboDef Combo(string id) => Combos.FirstOrDefault(c => c.id == id);
    public static string Won(int n) => n.ToString("N0", CultureInfo.InvariantCulture) + "원";
    /// <summary>돋보기 뜻 풀이 표기</summary>
    public static string Mean(string s) => $"({s})";
}
