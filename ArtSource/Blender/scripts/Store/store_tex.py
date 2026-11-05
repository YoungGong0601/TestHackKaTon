"""매장(store_arch) 2D 텍스처 생성 (Pillow). 사용: venv/bin/python store_tex.py <출력폴더>
메뉴판/주문번호판/포스터/사인/라벨/천장 타일을 그린다. 이름·가격은 프로토타입 키오스크 메뉴 데이터(ch 모듈) 기준."""
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

OUT = sys.argv[1] if len(sys.argv) > 1 else "store_tex"
os.makedirs(OUT, exist_ok=True)
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))           # ArtSource
IMG = os.path.join(ROOT, "_ref", "img")
FONTS = os.path.join(ROOT, "_cache", "fonts")
NANUM = os.path.expanduser("~/Library/Fonts")

RED, CREAM, BROWN, MUSTARD = "#b5271c", "#f1e4c8", "#4a2c18", "#e2a72e"
random.seed(7)
np.random.seed(7)


def F(kind, size):
    p = {"black": os.path.join(FONTS, "BlackHanSans-Regular.ttf"),
         "dohyeon": os.path.join(FONTS, "DoHyeon-Regular.ttf"),
         "jua": os.path.join(FONTS, "Jua-Regular.ttf"),
         "pen": os.path.join(FONTS, "NanumPenScript-Regular.ttf"),
         "eb": os.path.join(NANUM, "NanumSquareEB.ttf"),
         "b": os.path.join(NANUM, "NanumSquareB.ttf"),
         "r": os.path.join(NANUM, "NanumSquareR.ttf"),
         "l": os.path.join(NANUM, "NanumSquareL.ttf"),
         "ga": os.path.join(FONTS, "GothicA1-Black.ttf")}[kind]
    return ImageFont.truetype(p, int(size))


def save(im, name):
    im.convert("RGB").save(os.path.join(OUT, name), quality=94) if name.endswith(".jpg") else im.save(os.path.join(OUT, name))


def T(d, xy, s, font, fill, anchor="mm", **kw):
    d.text(xy, s, font=font, fill=fill, anchor=anchor, **kw)


def fit(s, kind, size, maxw):
    f = F(kind, size)
    w = f.getlength(s)
    if w > maxw:
        f = F(kind, size * maxw / w)
    return f


def photo(name, h):
    if name == "fries.jpg":
        return fries_img(h)
    im = Image.open(os.path.join(IMG, name)).convert("RGBA")
    if name.endswith(".jpg"):  # 흰 배경 제거
        a = np.asarray(im).astype(np.int16)
        m = (a[..., :3].min(-1) > 238)
        a[..., 3] = np.where(m, 0, 255)
        im = Image.fromarray(a.astype(np.uint8), "RGBA").filter(ImageFilter.SMOOTH)
    bb = im.getbbox()
    im = im.crop(bb)
    return im.resize((int(im.width * h / im.height), int(h)), Image.LANCZOS)


def fries_img(h):
    """감자튀김 사진(정사각 jpg)을 빨간 종이 상자에 담은 RGBA."""
    w = int(h * 0.8)
    im = Image.new("RGBA", (w, int(h)), (0, 0, 0, 0))
    src = Image.open(os.path.join(IMG, "fries.jpg")).convert("RGBA").resize((w, int(h * 0.62)), Image.LANCZOS)
    m = Image.new("L", src.size, 0)
    md = ImageDraw.Draw(m)
    md.ellipse([0, 0, src.width, src.height * 1.6], fill=255)
    im.paste(src, (0, int(h * 0.02)), m.filter(ImageFilter.GaussianBlur(3)))
    d = ImageDraw.Draw(im)
    top, bot = h * 0.38, h * 0.99
    d.polygon([(w * 0.04, top), (w * 0.96, top), (w * 0.84, bot), (w * 0.16, bot)], fill="#c62f22")
    d.polygon([(w * 0.04, top), (w * 0.5, top + h * 0.1), (w * 0.96, top)], fill="#a4241a")
    lg = logo(int(h * 0.36), text=False)
    im.alpha_composite(lg, (int(w / 2 - h * 0.18), int(h * 0.52)))
    return im


def paste_shadow(base, im, xy, blur=18, off=(0, 14), alpha=0.45):
    sh = Image.new("RGBA", im.size, (40, 20, 5, 0))
    sh.putalpha(im.split()[3].point(lambda v: int(v * alpha)))
    pad = blur * 3
    big = Image.new("RGBA", (im.width + pad * 2, im.height + pad * 2), (0, 0, 0, 0))
    big.paste(sh, (pad, pad))
    big = big.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(big, (int(xy[0] - pad + off[0]), int(xy[1] - pad + off[1])))
    base.alpha_composite(im, (int(xy[0]), int(xy[1])))


def grain(im, amt=6, seed=0):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    rng = np.random.default_rng(seed)
    a += rng.normal(0, amt, a.shape[:2])[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB")


def age(im, fade=0.0, dirt=0.0, seed=1, vignette=0.0, yellow=0.0):
    """인쇄물 노화: 색 바램, 얼룩, 가장자리 때, 누렇게 변색."""
    rng = np.random.default_rng(seed)
    a = np.asarray(im.convert("RGB")).astype(np.float32) / 255
    h, w = a.shape[:2]
    if fade:
        a = a * (1 - fade) + fade * 0.92
    if yellow:
        a = a * (1 - yellow * np.array([0.0, 0.05, 0.22]))
    if dirt:
        n = rng.random((max(2, h // 64), max(2, w // 64))).astype(np.float32)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
        a = a * (1 - dirt * 0.25 * n[..., None])
    if vignette:
        yy, xx = np.mgrid[0:h, 0:w]
        dx = np.minimum(xx, w - 1 - xx) / (0.08 * w)
        dy = np.minimum(yy, h - 1 - yy) / (0.08 * h)
        e = np.clip(np.minimum(dx, dy), 0, 1)
        a = a * (1 - vignette * (1 - e[..., None]) * np.array([0.55, 0.6, 0.7]))
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "RGB")


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


# ---------------------------------------------------------------- 로고 (버거대왕: 왕관 쓴 버거, 패러디 · 실제 브랜드 형태 아님)

def logo(size, text=True, dark=False):
    """정사각 RGBA 로고. 프로토타입 Rn() 형태를 다듬은 것."""
    S = size
    im = Image.new("RGBA", (S, S * (2 if text else 1)) if False else (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = S / 2, S * 0.56
    k = S / 260
    # 왕관
    crown = [(-34, -50), (-40, -92), (-17, -68), (0, -102), (17, -68), (40, -92), (34, -50)]
    d.polygon([(cx + x * k, cy + y * k) for x, y in crown], fill="#f0c63a", outline="#b8861c", width=max(1, int(3 * k)))
    for x, y in ((-40, -92), (0, -102), (40, -92)):
        d.ellipse([cx + (x - 6) * k, cy + (y - 6) * k, cx + (x + 6) * k, cy + (y + 6) * k], fill="#f0c63a")
    # 윗빵
    d.chord([cx - 72 * k, cy - 62 * k, cx + 72 * k, cy + 30 * k], 180, 360, fill="#d98a2b", outline="#9a5414", width=max(1, int(3 * k)))
    for i in range(9):
        x = -44 + i * 11
        y = -36 - math.sin(i * 0.8) * 9 + (i % 2) * 6
        d.ellipse([cx + (x - 4) * k, cy + (y - 2) * k, cx + (x + 4) * k, cy + (y + 2) * k], fill="#f6dfa8")
    # 상추, 패티, 아랫빵
    lett = [(cx + x * k, cy + (-14 + (7 if (x // 12) % 2 else -1)) * k) for x in range(-78, 80, 12)]
    d.polygon(lett + [(cx + 78 * k, cy - 18 * k), (cx - 78 * k, cy - 18 * k)], fill="#6fa23a")
    rrect(d, [cx - 76 * k, cy - 10 * k, cx + 76 * k, cy + 10 * k], 9 * k, fill="#5a2d14")
    d.polygon([(cx - 70 * k, cy - 8 * k), (cx + 70 * k, cy - 8 * k), (cx + 46 * k, cy + 4 * k), (cx + 10 * k, cy - 1 * k),
               (cx - 30 * k, cy + 6 * k)], fill="#f2b630")
    rrect(d, [cx - 70 * k, cy + 13 * k, cx + 70 * k, cy + 38 * k], 12 * k, fill="#d98a2b", outline="#9a5414", width=max(1, int(3 * k)))
    if text:
        f = F("black", 54 * k)
        T(d, (cx, cy + 74 * k), "버거대왕", f, "#3a2416" if dark else "#c8291f", stroke_width=int(5 * k), stroke_fill="#f1e4c8")
    return im


def logo_wide(w, h, color="#c8291f", sub=True, stroke="#f1e4c8"):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    lg = logo(int(h * 1.05), text=False)
    im.alpha_composite(lg, (0, int(-h * 0.08)))
    d = ImageDraw.Draw(im)
    f = fit("버거대왕", "black", h * 0.62, w - h * 1.05)
    T(d, (h * 1.0, h * 0.5), "버거대왕", f, color, anchor="lm", stroke_width=int(h * 0.03), stroke_fill=stroke)
    return im


# ---------------------------------------------------------------- 메뉴판 (라이트박스 3장, 1.25 x 0.72 m)
MW, MH = 2048, 1180


def won(v):
    return f"{v:,}"


def menu_header(d, title, eng):
    d.rectangle([0, 0, MW, 170], fill=RED)
    d.rectangle([0, 170, MW, 180], fill=MUSTARD)
    f = F("black", 108)
    x = 60
    for i, wd in enumerate(title.split(" · ")):
        if i:
            d.ellipse([x + 14, 84, x + 34, 104], fill=MUSTARD)
            x += 48
        T(d, (x, 92), wd, f, CREAM, anchor="lm")
        x += f.getlength(wd)
    T(d, (x + 34, 112), eng, F("eb", 44), "#f6c9a8", anchor="lm")


def menu_bg():
    im = Image.new("RGBA", (MW, MH), CREAM)
    a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:MH, 0:MW]
    g = 1 - 0.06 * ((xx - MW / 2) / MW) ** 2 * 4 - 0.04 * (yy / MH)
    a[..., :3] *= g[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def badge(d, xy, text, fill):
    f = F("ga", 40)
    w = f.getlength(text) + 36
    rrect(d, [xy[0], xy[1], xy[0] + w, xy[1] + 58], 29, fill=fill)
    T(d, (xy[0] + w / 2, xy[1] + 30), text, f, "#fff")


def item_cell(im, d, x, y, w, h, ph, name, mean, price, combo=None, tag=None, tagc=RED):
    rrect(d, [x, y, x + w, y + h], 22, fill="#fbf4e3", outline="#e1cfaa", width=3)
    p = photo(ph, h * 0.62)
    if p.width > w * 0.9:
        p = p.resize((int(w * 0.9), int(p.height * w * 0.9 / p.width)), Image.LANCZOS)
    paste_shadow(im, p, (x + (w - p.width) / 2, y + 14), blur=10, off=(0, 8), alpha=0.35)
    T(d, (x + w / 2, y + h * 0.71), name, fit(name, "eb", 40, w - 30), BROWN)
    T(d, (x + w / 2, y + h * 0.80), mean, F("r", 24), "#8a6a4a")
    if combo:
        T(d, (x + 24, y + h * 0.91), "단품 " + won(price), F("eb", 34), BROWN, anchor="lm")
        T(d, (x + w - 24, y + h * 0.91), "세트 " + won(combo), F("eb", 34), RED, anchor="rm")
    else:
        T(d, (x + w / 2, y + h * 0.91), won(price), F("eb", 40), RED)
    if tag:
        badge(d, (x + 16, y + 14), tag, tagc)


def fineprint(d, s, y=MH - 30):
    T(d, (MW / 2, y), s, F("r", 21), "#7b6047")


def menu_a():
    im = menu_bg()
    d = ImageDraw.Draw(im)
    menu_header(d, "대표 메뉴", "SIGNATURE")
    # 히어로
    rrect(d, [40, 210, 900, MH - 70], 30, fill="#3a2214")
    p = photo("burger_double.png", 560)
    paste_shadow(im, p, (470 - p.width / 2, 300), blur=24, off=(0, 20))
    badge(d, (70, 236), "BEST", RED)
    T(d, (470, 940), "크라운 트리플 스택", F("black", 76), CREAM)
    T(d, (470, 1012), "Triple Flame Grilled · 고기 세 장 버거", F("b", 30), "#d9b98a")
    T(d, (330, 1068), "단품 11,900", F("eb", 46), CREAM)
    T(d, (640, 1068), "세트 13,900", F("eb", 46), MUSTARD)
    items = [("burger_bacon.png", "앵거스 트러플 오 그라탕", "Limited Reserve", 12400, 14400, "NEW", "#2f7d4f"),
             ("burger_double.png", "더 그랜드 K-그릴 플래티넘", "Char Broiled Edition", 10900, 12900, None, None),
             ("burger_cheese.png", "하바네로 인페르노 비프", "Scoville 8,000", 9900, 11900, "HOT", "#d6442f"),
             ("burger_bacon.png", "와규 크라운 리저브", "A5 Blend Patty", 14900, 16900, "NEW", "#2f7d4f")]
    for i, (ph, n, e, pr, cb, tg, tc) in enumerate(items):
        x = 930 + (i % 2) * 550
        y = 210 + (i // 2) * 450
        item_cell(im, d, x, y, 530, 430, ph, n, e, pr, cb, tg, tc)
    fineprint(d, "세트 = 버거 + 프렌치 프라이 R + 음료 R  ·  사진은 연출된 이미지로 실제와 다를 수 있습니다  ·  주문은 키오스크에서 가능합니다")
    return im


def menu_b():
    im = menu_bg()
    d = ImageDraw.Draw(im)
    menu_header(d, "버거", "CLASSIC BURGER")
    items = [("burger_bulgogi.png", "K-BBQ 스모키 비프", "불고기 버거 · Sweet Soy Glaze", 5900, 7900, None, None),
             ("burger_double.png", "K-BBQ 스모키 비프 더블", "불고기 두 장 버거", 7900, 9900, None, None),
             ("burger_double.png", "오리지널 로열 패티", "고기 버거 · Since 1998", 5400, 7400, None, None),
             ("burger_bacon.png", "스모키 BBQ 더블 머쉬룸", "버섯 버거", 6900, 8900, "BEST", RED),
             ("burger_chicken.png", "크리스피 K-치킨", "닭고기 버거", 5600, 7600, None, None),
             ("burger_shrimp.png", "코리안 쉬림프 크런치", "새우 버거", 5900, 7900, None, None),
             ("burger_cheese.png", "더블 치즈 멜트", "치즈 버거", 6100, 8100, None, None),
             ("burger_chicken.png", "씨 크리스피 필레", "생선 버거", 5400, 7400, None, None)]
    cw, ch = 482, 455
    for i, (ph, n, e, pr, cb, tg, tc) in enumerate(items):
        x = 40 + (i % 4) * (cw + 12)
        y = 205 + (i // 4) * (ch + 14)
        item_cell(im, d, x, y, cw, ch, ph, n, e, pr, cb, tg, tc)
    fineprint(d, "세트 변경 +2,000원 · 라지 세트 +2,800원  ·  원산지: 쇠고기(호주산), 닭고기(국내산), 새우(베트남산)  ·  알레르기 정보는 키오스크 [정보] 메뉴 참고")
    return im


def menu_c():
    im = menu_bg()
    d = ImageDraw.Draw(im)
    menu_header(d, "사이드 · 음료 · 디저트", "SIDE & DRINK")
    items = [("fries.jpg", "프렌치 프라이", "R 2,000  ·  L 2,500", 2000, None),
             ("nuggets.png", "크라운 너겟 4PC", "닭 튀김 네 개", 2800, None),
             ("fries.jpg", "프렌치 프라이 L", "감자튀김 큰 것", 2500, None),
             ("softcone.png", "소프트 콘", "아이스크림", 1200, None),
             ("cola.png", "제로 콜라", "콜라 · R", 2000, None),
             ("cider.png", "라임 스파클링", "사이다 · R", 2000, None),
             ("coffee.png", "아메리카노 ICE", "찬 커피", 2000, None),
             ("cola.png", "오리지널 콜라", "콜라 · R", 2000, None)]
    cw, ch = 482, 455
    for i, (ph, n, e, pr, cb) in enumerate(items):
        x = 40 + (i % 4) * (cw + 12)
        y = 205 + (i // 4) * (ch + 14)
        item_cell(im, d, x, y, cw, ch, ph, n, e, pr, cb)
    fineprint(d, "음료 사이즈 업 +500원 · 리필 불가  ·  1회용 컵은 매장 내 사용이 제한됩니다  ·  디저트는 키오스크 [후식] 탭에서 주문")
    return im


# ---------------------------------------------------------------- 주문번호판 (M_Dyn 기본 화면, 1.25 x 0.56 m)

def order_board(w=2000, h=896, ready=(269, 271, 272, 274), call=(268,)):
    im = Image.new("RGB", (w, h), "#17100b")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.2], fill="#2a1a10")
    d.rectangle([w / 2, 0, w, h * 0.2], fill=RED)
    T(d, (w * 0.25, h * 0.1), "준비 중", F("black", h * 0.12), "#e9cf9d")
    T(d, (w * 0.75, h * 0.1), "호출", F("black", h * 0.12), CREAM)
    d.rectangle([w / 2 - 3, h * 0.2, w / 2 + 3, h * 0.92], fill="#6b5a44")
    f = F("black", h * 0.17)
    for i, n in enumerate(ready[:6]):
        T(d, (w * (0.13 + (i % 2) * 0.24), h * (0.38 + (i // 2) * 0.22)), str(n), f, "#ffb445")
    for n in call[-1:]:
        T(d, (w * 0.75, h * 0.53), str(n), F("black", h * 0.36), "#ff5a3a")
        T(d, (w * 0.75, h * 0.78), "번 고객님, 픽업대로 와주세요", F("b", h * 0.05), "#f0d9b0")
    d.rectangle([0, h * 0.92, w, h], fill="#0e0905")
    T(d, (w * 0.02, h * 0.96), "주문번호는 영수증 상단에 있습니다 · 호출 후 10분이 지나면 다시 조리될 수 있습니다", F("r", h * 0.032), "#9c8466", anchor="lm")
    # 픽셀 격자 느낌 (LCD)
    a = np.asarray(im).astype(np.float32)
    a[::3, :, :] *= 0.9
    a[:, ::3, :] *= 0.94
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# ---------------------------------------------------------------- 포스터

def poster_kiosk(w=1200, h=1700):
    im = Image.new("RGBA", (w, h), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, h * 0.09], fill=RED)
    T(d, (w / 2, h * 0.045), "NOTICE · 안내", F("ga", h * 0.04), CREAM)
    T(d, (w / 2, h * 0.2), "주문은", F("black", w * 0.15), BROWN)
    T(d, (w / 2, h * 0.32), "키오스크에서", F("black", w * 0.15), RED)
    d.rectangle([w * 0.1, h * 0.4, w * 0.9, h * 0.41], fill=RED)
    T(d, (w / 2, h * 0.455), "빠르고 간편합니다", F("eb", w * 0.075), BROWN)
    # 키오스크 + 손가락 픽토그램
    kx, ky = w / 2, h * 0.68
    rrect(d, [kx - 150, ky - 230, kx + 150, ky + 200], 28, fill=BROWN)
    rrect(d, [kx - 120, ky - 200, kx + 120, ky + 60], 12, fill="#fff7e6")
    for i in range(3):
        for j in range(2):
            rrect(d, [kx - 105 + j * 110, ky - 185 + i * 80, kx - 10 + j * 110, ky - 120 + i * 80], 8, fill=[RED, MUSTARD, "#2f7d4f"][(i + j) % 3])
    rrect(d, [kx - 60, ky + 110, kx + 60, ky + 125], 6, fill="#1a120c")
    hand = [(kx + 70, ky - 40), (kx + 92, ky - 40), (kx + 92, ky + 30), (kx + 150, ky + 30), (kx + 170, ky + 140), (kx + 70, ky + 150), (kx + 50, ky + 40)]
    d.polygon(hand, fill="#f3c9a0", outline=BROWN, width=6)
    T(d, (w / 2, h * 0.88), "카운터에서는 주문을 받지 않습니다", F("b", w * 0.045), "#6a4a30")
    T(d, (w / 2, h * 0.93), "현금 결제 불가 · 카드 / 간편결제 전용", F("r", w * 0.036), "#6a4a30")
    lg = logo_wide(int(w * 0.36), int(h * 0.04))
    im.alpha_composite(lg, (int(w * 0.32), int(h * 0.955)))
    return age(im, fade=0.06, dirt=0.4, seed=3, vignette=0.25, yellow=0.08)


def poster_new(w=1200, h=1700):
    im = Image.new("RGBA", (w, h), RED)
    d = ImageDraw.Draw(im)
    d.ellipse([w * 0.04, h * 0.2, w * 0.96, h * 0.85], fill="#d6442f")
    for i in range(24):
        a = i / 24 * math.tau
        d.polygon([(w / 2, h * 0.53), (w / 2 + math.cos(a) * w, h * 0.53 + math.sin(a) * w),
                   (w / 2 + math.cos(a + 0.08) * w, h * 0.53 + math.sin(a + 0.08) * w)], fill="#c33522")
    p = photo("burger_bacon.png", h * 0.42)
    paste_shadow(im, p, (w / 2 - p.width / 2, h * 0.33), blur=30, off=(0, 26))
    T(d, (w / 2, h * 0.12), "왕이 돌아왔다", F("black", w * 0.13), CREAM, stroke_width=8, stroke_fill="#7a1a10")
    badge(d, (w * 0.08, h * 0.22), "NEW", "#2f7d4f")
    T(d, (w / 2, h * 0.83), "와규 크라운 리저브", F("black", w * 0.09), CREAM)
    T(d, (w / 2, h * 0.9), "A5 Blend Patty  ·  단품 14,900원", F("eb", w * 0.048), "#ffd9a8")
    T(d, (w / 2, h * 0.965), "한정 판매 · 매장 사정에 따라 조기 품절될 수 있습니다", F("r", w * 0.028), "#f7c9b0")
    return age(im, fade=0.12, dirt=0.3, seed=4, vignette=0.2)


def poster_bulgogi(w=1200, h=1700):
    im = Image.new("RGBA", (w, h), "#2b1a10")
    d = ImageDraw.Draw(im)
    for i in range(0, h, 6):
        d.line([(0, i), (w, i)], fill=(43 + (i // 6) % 3, 26, 16))
    T(d, (w / 2, h * 0.09), "K-BBQ", F("black", w * 0.11), MUSTARD)
    T(d, (w / 2, h * 0.19), "스모키 비프 세트", F("black", w * 0.1), CREAM)
    p = photo("burger_bulgogi.png", h * 0.36)
    paste_shadow(im, p, (w * 0.08, h * 0.3), blur=26, off=(0, 22))
    q = photo("fries.jpg", h * 0.22)
    paste_shadow(im, q, (w * 0.62, h * 0.44), blur=20)
    c = photo("cola.png", h * 0.24)
    paste_shadow(im, c, (w * 0.7, h * 0.27), blur=20)
    rrect(d, [w * 0.12, h * 0.75, w * 0.88, h * 0.86], 30, fill=RED)
    T(d, (w / 2, h * 0.805), "세트 7,900원", F("black", w * 0.09), CREAM)
    T(d, (w / 2, h * 0.91), "Sweet Soy Glaze · 달콤한 간장 소스", F("b", w * 0.04), "#d9b98a")
    T(d, (w / 2, h * 0.955), "* 세트 음료 변경은 키오스크 [옵션] 에서 선택", F("r", w * 0.026), "#9c8466")
    return age(im, fade=0.05, dirt=0.35, seed=5, vignette=0.3)


def poster_fries(w=1200, h=1700):
    im = Image.new("RGBA", (w, h), BROWN)
    d = ImageDraw.Draw(im)
    T(d, (w / 2, h * 0.1), "사이드는", F("black", w * 0.12), CREAM)
    T(d, (w / 2, h * 0.2), "왕의 친구", F("black", w * 0.12), MUSTARD)
    p = photo("fries.jpg", h * 0.38)
    paste_shadow(im, p, (w * 0.06, h * 0.32), blur=24)
    q = photo("nuggets.png", h * 0.26)
    paste_shadow(im, q, (w * 0.5, h * 0.48), blur=24)
    T(d, (w / 2, h * 0.84), "프렌치 프라이 2,000원 · 너겟 2,800원", F("eb", w * 0.05), CREAM)
    T(d, (w / 2, h * 0.9), "세트로 바꾸면 더 든든하게", F("b", w * 0.045), "#d9b98a")
    return age(im, fade=0.15, dirt=0.4, seed=6, vignette=0.3, yellow=0.05)


def poster_dessert(w=1200, h=1700):
    im = Image.new("RGBA", (w, h), "#f4d9d0")
    d = ImageDraw.Draw(im)
    d.ellipse([w * 0.1, h * 0.22, w * 0.9, h * 0.75], fill="#f7e6df")
    T(d, (w / 2, h * 0.1), "후식은", F("black", w * 0.12), RED)
    T(d, (w / 2, h * 0.19), "소프트 콘", F("black", w * 0.13), BROWN)
    p = photo("softcone.png", h * 0.48)
    paste_shadow(im, p, (w / 2 - p.width / 2, h * 0.25), blur=24)
    rrect(d, [w * 0.25, h * 0.79, w * 0.75, h * 0.88], 30, fill=RED)
    T(d, (w / 2, h * 0.835), "1,200원", F("black", w * 0.1), CREAM)
    T(d, (w / 2, h * 0.93), "아메리카노 ICE 와 함께 3,000원", F("b", w * 0.045), BROWN)
    return age(im, fade=0.2, dirt=0.3, seed=8, vignette=0.2, yellow=0.06)


def poster_coupon(w=1000, h=1440):
    im = Image.new("RGBA", (w, h), MUSTARD)
    d = ImageDraw.Draw(im)
    T(d, (w / 2, h * 0.11), "앱 전용", F("black", w * 0.2), BROWN)
    T(d, (w / 2, h * 0.23), "QR 찍고 500원 할인", F("black", w * 0.085), BROWN)
    q0, qs = w * 0.24, w * 0.52
    d.rectangle([q0 - 20, h * 0.3 - 20, q0 + qs + 20, h * 0.3 + qs + 20], fill="#fff")
    n = 25
    c = qs / n
    rng = random.Random(11)
    for i in range(n):
        for j in range(n):
            finder = any(i0 <= i < i0 + 7 and j0 <= j < j0 + 7 for i0, j0 in ((0, 0), (0, n - 7), (n - 7, 0)))
            if finder:
                ii, jj = [(i - i0, j - j0) for i0, j0 in ((0, 0), (0, n - 7), (n - 7, 0)) if i0 <= i < i0 + 7 and j0 <= j < j0 + 7][0]
                on = ii in (0, 6) or jj in (0, 6) or (2 <= ii <= 4 and 2 <= jj <= 4)
            else:
                on = rng.random() < 0.48
            if on:
                d.rectangle([q0 + j * c, h * 0.3 + i * c, q0 + (j + 1) * c, h * 0.3 + (i + 1) * c], fill="#1d1712")
    T(d, (w / 2, h * 0.76), "버거대왕 앱 설치 → 회원가입 →", F("b", w * 0.045), BROWN)
    T(d, (w / 2, h * 0.8), "본인인증 → 쿠폰함 → 바코드 제시", F("b", w * 0.045), BROWN)
    T(d, (w / 2, h * 0.87), "* 키오스크 주문 시에만 사용 가능 · 타 쿠폰과 중복 불가", F("r", w * 0.032), "#5a3c22")
    T(d, (w / 2, h * 0.905), "* 1인 1회 · 이벤트 기간 내 · 일부 메뉴 제외", F("r", w * 0.032), "#5a3c22")
    lg = logo_wide(int(w * 0.4), int(h * 0.05))
    im.alpha_composite(lg, (int(w * 0.3), int(h * 0.93)))
    return age(im, fade=0.18, dirt=0.5, seed=9, vignette=0.35, yellow=0.04)


def logo_panel(w=2000, h=1200):
    im = Image.new("RGBA", (w, h), "#3b2214")
    a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.sqrt(((xx - w / 2) / w) ** 2 + ((yy - h * 0.45) / h) ** 2)
    a[..., :3] *= (1.25 - r * 0.9)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    lg = logo(int(h * 0.8), text=True)
    im.alpha_composite(lg, (int(w / 2 - h * 0.4), int(h * 0.02)))
    d = ImageDraw.Draw(im)
    T(d, (w / 2, h * 0.9), "SINCE 1998 · 시장입구점", F("eb", h * 0.05), "#d9b98a")
    return im


# ---------------------------------------------------------------- 사인 / 라벨 아틀라스

class Atlas:
    """한 장에 여러 사인을 그리고 UV 사각형(0-1, 아래 원점)을 기록."""

    def __init__(self, name, w, h, bg=(0, 0, 0, 0)):
        self.name, self.w, self.h = name, w, h
        self.im = Image.new("RGBA", (w, h), bg)
        self.rects = {}

    def add(self, key, img, x, y):
        self.im.alpha_composite(img.convert("RGBA"), (x, y))
        self.rects[key] = (x / self.w, 1 - (y + img.height) / self.h, (x + img.width) / self.w, 1 - y / self.h)

    def save(self):
        save(self.im.convert("RGB"), self.name)
        with open(os.path.join(OUT, self.name + ".uv"), "w") as f:
            for k, r in self.rects.items():
                f.write(k + " " + " ".join(f"{v:.6f}" for v in r) + "\n")


def sign(w, h, bg, lines, border=None, r=0):
    im = Image.new("RGBA", (w, h), bg)
    d = ImageDraw.Draw(im)
    if border:
        rrect(d, [6, 6, w - 7, h - 7], r, outline=border, width=max(3, h // 40))
    for s, kind, size, col, y in lines:
        T(d, (w / 2, h * y), s, fit(s, kind, h * size, w * 0.9), col)
    return im


def exit_sign(w=920, h=340):
    im = Image.new("RGBA", (w, h), "#12a050")
    d = ImageDraw.Draw(im)
    # 달리는 사람 + 문 (비상구 픽토그램 단순화)
    rrect(d, [40, 40, 300, 300], 12, fill="#f2fff4")
    d.rectangle([70, 70, 180, 300], fill="#12a050")
    k = 1.0
    d.ellipse([200, 70, 245, 115], fill="#12a050")
    d.line([(222, 120), (196, 200)], fill="#12a050", width=26)
    d.line([(196, 200), (240, 240), (232, 290)], fill="#12a050", width=22)
    d.line([(196, 200), (160, 250), (120, 255)], fill="#12a050", width=22)
    d.line([(215, 140), (260, 175), (285, 160)], fill="#12a050", width=18)
    d.line([(215, 140), (170, 150), (150, 190)], fill="#12a050", width=18)
    T(d, (610, 175), "비상구", F("black", 170), "#f2fff4")
    return im


def restroom(w=600, h=200):
    im = Image.new("RGBA", (w, h), CREAM)
    d = ImageDraw.Draw(im)
    for cx, col, skirt in ((70, "#2b5c9a", False), (160, RED, True)):
        d.ellipse([cx - 18, 30, cx + 18, 66], fill=col)
        if skirt:
            d.polygon([(cx - 34, 150), (cx + 34, 150), (cx + 16, 74), (cx - 16, 74)], fill=col)
        else:
            rrect(d, [cx - 24, 74, cx + 24, 140], 8, fill=col)
        d.rectangle([cx - 14, 140, cx - 4, 178], fill=col)
        d.rectangle([cx + 4, 140, cx + 14, 178], fill=col)
    T(d, (395, 92), "화장실", F("black", 92), BROWN)
    T(d, (395, 162), "RESTROOM", F("eb", 34), "#7b6047")
    return im


def clock_face(s=512):
    im = Image.new("RGBA", (s, s), "#f2eee2")
    d = ImageDraw.Draw(im)
    c = s / 2
    for i in range(60):
        a = i / 60 * math.tau
        L = 30 if i % 5 == 0 else 12
        wd = 10 if i % 5 == 0 else 3
        d.line([(c + math.sin(a) * (c - 18), c - math.cos(a) * (c - 18)),
                (c + math.sin(a) * (c - 18 - L), c - math.cos(a) * (c - 18 - L))], fill="#2a2520", width=wd)
    f = F("eb", 44)
    for i in range(1, 13):
        a = i / 12 * math.tau
        T(d, (c + math.sin(a) * (c - 82), c - math.cos(a) * (c - 82)), str(i), f, "#2a2520")
    T(d, (c, c + 90), "버거대왕", F("black", 30), RED)
    hh, mm = 11 + 42 / 60, 42
    for ang, L, wd in ((hh / 12 * math.tau, c * 0.5, 16), (mm / 60 * math.tau, c * 0.74, 10)):
        d.line([(c, c), (c + math.sin(ang) * L, c - math.cos(ang) * L)], fill="#2a2520", width=wd)
    d.line([(c, c), (c + math.sin(2.1) * c * 0.8, c - math.cos(2.1) * c * 0.8)], fill=RED, width=4)
    d.ellipse([c - 14, c - 14, c + 14, c + 14], fill="#2a2520")
    return age(im, fade=0.05, yellow=0.1, dirt=0.3, seed=12)


def shell_signs():
    A = Atlas("shell_signs.png", 2048, 1024)
    A.add("exit", exit_sign(920, 340), 0, 0)
    A.add("restroom", restroom(600, 200), 940, 0)
    A.add("cctv", sign(420, 300, "#f6d33c", [("CCTV", "ga", 0.3, "#1b1b1b", 0.27), ("24시간 녹화 중", "eb", 0.16, "#1b1b1b", 0.6),
                                             ("방범용 · 매장 관리자", "r", 0.09, "#3b3b3b", 0.85)], border="#1b1b1b", r=20), 940, 220)
    A.add("clock", clock_face(512), 1536, 0)
    A.add("wait", sign(700, 300, (0, 0, 0, 0), []), 0, 360)
    # 바닥 대기선 스티커 (발자국 + 문구)
    st = Image.new("RGBA", (700, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(st)
    rrect(d, [0, 0, 699, 299], 40, fill=MUSTARD)
    rrect(d, [14, 14, 685, 285], 30, outline=BROWN, width=8)
    for fx in (110, 200):
        d.ellipse([fx - 32, 60, fx + 32, 190], fill=BROWN)
        d.ellipse([fx - 26, 200, fx + 26, 250], fill=BROWN)
    T(d, (450, 120), "이곳에서", F("black", 84), BROWN)
    T(d, (450, 215), "기다려 주세요", F("black", 70), BROWN)
    st = age(st, dirt=0.9, fade=0.1, seed=13).convert("RGBA")
    st.putalpha(Image.new("L", (700, 300), 0))
    mask = Image.new("L", (700, 300), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 699, 299], 40, fill=255)
    st.putalpha(mask)
    A.add("wait", st, 0, 360)
    A.add("ac", sign(420, 160, "#f4f2ec", [("냉난방 중", "eb", 0.34, "#2b5c9a", 0.38), ("문을 꼭 닫아 주세요", "b", 0.2, "#3b3b3b", 0.75)], border="#2b5c9a", r=14), 940, 540)
    A.save()


def counter_signs():
    A = Atlas("counter_signs.png", 2048, 2048)
    pk = Image.new("RGBA", (1000, 320), RED)
    d = ImageDraw.Draw(pk)
    T(d, (330, 160), "픽업", F("black", 200), CREAM)
    d.rectangle([600, 60, 606, 260], fill="#f1c9a0")
    T(d, (800, 120), "PICK-UP", F("ga", 70), CREAM)
    T(d, (800, 215), "주문 받는 곳", F("eb", 56), "#ffd9a8")
    A.add("pickup", pk, 0, 0)
    # 키오스크 주문 아크릴 안내
    ko = Image.new("RGBA", (480, 340), "#fdf8ee")
    d = ImageDraw.Draw(ko)
    d.rectangle([0, 0, 480, 80], fill=RED)
    T(d, (240, 42), "키오스크 주문", F("black", 54), CREAM)
    T(d, (240, 140), "주문은 키오스크에서", F("eb", 40), BROWN)
    T(d, (240, 192), "해 주세요", F("eb", 40), BROWN)
    d.polygon([(40, 270), (110, 230), (110, 255), (200, 255), (200, 285), (110, 285), (110, 310)], fill=RED)
    T(d, (330, 272), "카운터 주문 불가", F("b", 30), "#6a4a30")
    A.add("kiosk", ko, 1020, 0)
    cash = sign(600, 260, "#ffffff", [("현금 없는 매장", "black", 0.3, RED, 0.3), ("카드 · 간편결제만 가능합니다", "eb", 0.14, "#2a2520", 0.62),
                                       ("CASHLESS STORE", "ga", 0.11, "#6a6a6a", 0.85)], border=RED, r=18)
    A.add("cashless", age(cash, dirt=0.4, seed=21, yellow=0.06), 0, 340)
    # POS 화면 (직원용, 정적)
    pos = Image.new("RGBA", (640, 420), "#1f2a33")
    d = ImageDraw.Draw(pos)
    d.rectangle([0, 0, 640, 46], fill="#0f161c")
    T(d, (14, 23), "POS 01 · 버거대왕 시장입구점", F("b", 22), "#cfe0ea", anchor="lm")
    T(d, (626, 23), "11:42", F("eb", 24), "#cfe0ea", anchor="rm")
    cols = ["#b5271c", "#2f7d4f", "#e2a72e", "#3a6ea5", "#6a3a22", "#7a4b9a"]
    names = ["버거", "세트", "사이드", "음료", "디저트", "할인", "포장", "매장", "재출력", "취소", "현금", "카드"]
    for i, n in enumerate(names):
        x, y = 14 + (i % 4) * 116, 62 + (i // 4) * 108
        rrect(d, [x, y, x + 106, y + 96], 10, fill=cols[i % 6])
        T(d, (x + 53, y + 48), n, F("eb", 26), "#fff")
    rrect(d, [484, 62, 626, 380], 8, fill="#0f161c")
    T(d, (555, 90), "주문 내역", F("b", 20), "#cfe0ea")
    for i, s in enumerate(["268 왕더블", "269 스모키", "271 프라이", "272 치킨"]):
        T(d, (494, 128 + i * 34), s, F("r", 18), "#9fb6c4", anchor="lm")
    T(d, (555, 360), "합계 0원", F("eb", 22), "#ffb445")
    A.add("pos", pos, 0, 620)
    # 카드 단말기 LCD
    lcd = Image.new("RGBA", (300, 150), "#9fb38a")
    d = ImageDraw.Draw(lcd)
    T(d, (150, 50), "IC 카드를", F("eb", 36), "#22301c")
    T(d, (150, 100), "꽂아 주세요", F("eb", 36), "#22301c")
    A.add("lcd", lcd, 660, 620)
    # 직원 호출 벨 금지 / 와이파이 스티커
    wifi = sign(400, 200, "#ffffff", [("FREE Wi-Fi", "ga", 0.24, "#3a6ea5", 0.3), ("ID: BURGERDAEWANG_5G", "b", 0.12, "#2a2520", 0.6),
                                      ("PW: 키오스크에 있음", "b", 0.12, "#2a2520", 0.8)], border="#3a6ea5", r=16)
    A.add("wifi", age(wifi, dirt=0.3, seed=22), 980, 620)
    # 카운터 정면 띠 (로고 반복)
    band = Image.new("RGBA", (2048, 160), RED)
    lg = logo_wide(560, 140, color=CREAM, stroke=BROWN)
    for x in range(40, 2048, 700):
        band.alpha_composite(lg, (x, 10))
    A.add("band", band, 0, 1100)
    # 영업시간/알레르기 안내 (작은 글씨)
    note = Image.new("RGBA", (500, 360), "#fffdf6")
    d = ImageDraw.Draw(note)
    T(d, (250, 40), "알레르기 유발 성분 안내", F("eb", 32), BROWN)
    for i, s in enumerate(["밀 · 대두 · 우유 · 계란 · 쇠고기 · 닭고기", "새우 · 토마토 · 돼지고기 · 조개류(굴)",
                           "자세한 정보는 키오스크 [정보] 버튼을", "눌러 확인하시기 바랍니다.", "매장 내 1회용품 사용 제한"]):
        T(d, (250, 100 + i * 50), s, F("r", 24), "#4a3a2a")
    A.add("allergy", age(note, dirt=0.4, yellow=0.1, seed=23), 1400, 620)
    A.save()


def kitchen_signs():
    A = Atlas("kitchen_signs.png", 2048, 2048)
    so = Image.new("RGBA", (800, 300), "#f4f2ec")
    d = ImageDraw.Draw(so)
    d.rectangle([0, 0, 800, 120], fill="#1d1d1f")
    T(d, (400, 62), "STAFF ONLY", F("ga", 86), "#f4f2ec")
    T(d, (400, 190), "관계자 외 출입금지", F("black", 74), RED)
    T(d, (400, 262), "Employees Only", F("b", 30), "#555")
    A.add("staff", age(so, dirt=0.4, seed=31, yellow=0.05), 0, 0)
    # 음료 디스펜서 맛 표시 (백라이트)
    dr = Image.new("RGBA", (1376, 512), "#111")
    d = ImageDraw.Draw(dr)
    cols = ["#b5271c", "#2f7d4f", "#e2a72e", "#6a3a22"]
    names = ["콜라", "사이다", "오렌지", "아이스티"]
    subs = ["COLA", "LIME SODA", "ORANGE", "ICED TEA"]
    cw = 1376 / 4
    for i, (c, n, s) in enumerate(zip(cols, names, subs)):
        x = i * cw
        d.rectangle([x + 6, 0, x + cw - 6, 512], fill=c)
        for k in range(0, 512, 4):
            d.line([(x + 6, k), (x + cw - 6, k)], fill=tuple(min(255, int(int(c[j:j + 2], 16) * (1.15 - k / 512 * 0.35))) for j in (1, 3, 5)))
        T(d, (x + cw / 2, 210), n, fit(n, "black", 110, cw - 40), "#fff")
        T(d, (x + cw / 2, 330), s, fit(s, "ga", 40, cw - 40), "#ffffffcc")
        d.ellipse([x + cw / 2 - 40, 390, x + cw / 2 + 40, 470], outline="#fff", width=6)
    A.add("drinks", dr, 0, 320)
    # 튀김기 타이머 2개
    for i, s in enumerate(("2:41", "0:58")):
        t = Image.new("RGBA", (320, 140), "#1d1b19")
        d = ImageDraw.Draw(t)
        rrect(d, [10, 10, 310, 130], 10, fill="#120808")
        T(d, (160, 72), s, F("dohyeon", 110), "#ff4a2e")
        A.add("timer%d" % i, t, 820 + i * 340, 0)
    # 주방 모니터 (KDS)
    k = Image.new("RGBA", (840, 520), "#20252a")
    d = ImageDraw.Draw(k)
    d.rectangle([0, 0, 840, 50], fill="#11161a")
    T(d, (14, 25), "KDS · 주방 주문 현황", F("b", 24), "#d9e4e4", anchor="lm")
    T(d, (826, 25), "대기 4", F("eb", 24), "#ffb445", anchor="rm")
    orders = [("268", ["왕더블 x1", "프라이 R x1", "제로 콜라 x1"], "#b5271c", "06:12"),
              ("269", ["스모키 콤보 x2", "어니언 링 x2"], "#2f7d4f", "04:40"),
              ("271", ["프라이 R x1"], "#3a6ea5", "02:05"),
              ("272", ["치킨 콤보 x1", "사이다 x1"], "#3a6ea5", "00:51")]
    for i, (n, lines, c, tm) in enumerate(orders):
        x = 10 + i * 207
        rrect(d, [x, 62, x + 197, 508], 8, fill="#2e353b")
        d.rectangle([x, 62, x + 197, 110], fill=c)
        T(d, (x + 12, 86), n, F("eb", 34), "#fff", anchor="lm")
        T(d, (x + 186, 86), tm, F("b", 22), "#fff", anchor="rm")
        for j, s in enumerate(lines):
            T(d, (x + 12, 140 + j * 40), s, F("b", 24), "#d9e4e4", anchor="lm")
        T(d, (x + 98, 480), "완료", F("eb", 26), "#9fb6c4")
    A.add("kds", k, 0, 860)
    # 경고 스티커 / 청소 일지 / 박스 인쇄
    A.add("hot", sign(360, 200, "#f6d33c", [("고온 주의", "black", 0.34, "#1b1b1b", 0.38), ("기름에 손대지 마세요", "eb", 0.14, "#1b1b1b", 0.74)], border="#1b1b1b", r=12), 860, 860)
    A.add("ice", sign(360, 120, "#e9eef2", [("ICE MAKER", "ga", 0.36, "#2b5c9a", 0.38), ("제빙기 · 손 넣지 마세요", "b", 0.2, "#333", 0.78)]), 1240, 860)
    log = Image.new("RGBA", (420, 600), "#fbfaf4")
    d = ImageDraw.Draw(log)
    T(d, (210, 40), "주방 청소 점검표", F("eb", 34), "#222")
    for i in range(12):
        y = 90 + i * 42
        d.line([(20, y), (400, y)], fill="#999", width=2)
        T(d, (40, y + 21), f"{i + 1}일", F("r", 20), "#444")
        if i < 9:
            T(d, (250 + (i % 3) * 30, y + 21), "확인", F("pen", 34), "#2b4c9a")
    A.add("log", age(log, dirt=0.6, yellow=0.15, seed=33), 860, 1100)
    for i, (t1, t2, c) in enumerate((("포장봉투 L", "버거대왕 · 500매", RED), ("16oz 컵", "1,000EA", "#3a6ea5"),
                                       ("냅킨", "2겹 · 5,000매", "#2f7d4f"), ("버거 포장지", "왁스 코팅", "#6a3a22"))):
        b = Image.new("RGBA", (380, 260), "#c8a274")
        d = ImageDraw.Draw(b)
        d.rectangle([0, 0, 380, 40], fill="#b48d5f")
        T(d, (190, 110), t1, F("black", 64), c)
        T(d, (190, 190), t2, F("eb", 34), "#3a2a1a")
        A.add("box%d" % i, age(b, dirt=0.7, seed=40 + i), 1300 + (i % 2) * 380, 1100 + (i // 2) * 270)
    A.add("hood", sign(500, 120, "#d8dadc", [("후드 필터 주 1회 세척", "eb", 0.3, "#222", 0.5)]), 0, 1400)
    A.save()


# ---------------------------------------------------------------- 천장 텍스 타일 (600mm, T-bar)

def ceiling():
    n = 1024  # = 2.4 m (600mm 타일 4x4, 타일마다 색 차이; 얼룩은 반복이 보여서 넣지 않음)
    rng = np.random.default_rng(5)
    base = np.full((n, n), 0.88, np.float32)
    # 미세 요철 + 핀홀
    noise = rng.normal(0, 1, (n, n)).astype(np.float32)
    big = np.asarray(Image.fromarray(((rng.random((32, 32)) * 255).astype(np.uint8))).resize((n, n), Image.BICUBIC)).astype(np.float32) / 255
    h = 0.5 + 0.08 * noise + 0.15 * big
    holes = rng.random((n, n)) < 0.012
    h[holes] -= 0.6
    fiss = np.asarray(Image.fromarray(((rng.random((n // 6, n // 6)) > 0.93) * 255).astype(np.uint8)).resize((n, n), Image.NEAREST)).astype(np.float32) / 255
    h -= 0.25 * fiss * (rng.random((n, n)) > 0.5)
    col = np.stack([base, base * 0.985, base * 0.95], -1)
    col *= (0.96 + 0.04 * big)[..., None]
    col[holes] *= 0.55
    # 타일마다 밝기·누런 정도가 조금씩 다름 (변색)
    c = n // 4
    for i in range(4):
        for j in range(4):
            k, y = rng.uniform(0.965, 1.015), rng.uniform(0.0, 0.035)
            col[i * c:(i + 1) * c, j * c:(j + 1) * c] *= np.array([k, k * (1 - y * 0.5), k * (1 - y * 1.6)])
    # T-bar (흰 도장 금속) 와 그림자
    tb = 10
    for k in range(0, n, c):
        for sl in (np.s_[k:k + tb, :], np.s_[:, k:k + tb]):
            col[sl] = (0.93, 0.93, 0.92)
            h[sl] = 1.0
    for k in range(0, n, c):
        h[k + tb:k + tb + 3, :] -= 0.3
        h[:, k + tb:k + tb + 3] -= 0.3
    col = np.roll(col, -tb // 2, (0, 1))
    h = np.roll(h, -tb // 2, (0, 1))
    Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "ceiling_diff.jpg"), quality=92)
    gy, gx = np.gradient(h)
    nx, ny = -gx * 6, gy * 6
    nz = np.ones_like(nx)
    l = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    nm = np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5
    Image.fromarray((nm * 255).astype(np.uint8)).save(os.path.join(OUT, "ceiling_nor.png"))
    r = np.full((n, n), 0.92, np.float32)
    for k in range(0, n, c):
        r[k:k + tb, :] = 0.45
        r[:, k:k + tb] = 0.45
    r = np.roll(r, -tb // 2, (0, 1))
    Image.fromarray((r * 255).astype(np.uint8)).save(os.path.join(OUT, "ceiling_rough.png"))


if __name__ == "__main__":
    save(menu_a(), "menu_a.png")
    save(menu_b(), "menu_b.png")
    save(menu_c(), "menu_c.png")
    save(order_board(), "orderboard.png")
    save(poster_kiosk(), "poster_kiosk.png")
    save(poster_new(), "poster_new.png")
    save(poster_bulgogi(), "poster_bulgogi.png")
    save(poster_fries(), "poster_fries.png")
    save(poster_dessert(), "poster_dessert.png")
    save(poster_coupon(), "poster_coupon.png")
    save(logo_panel(), "logo_panel.png")
    save(sign(440, 240, RED, [("소화기", "black", 0.42, "#fff", 0.42), ("FIRE EXTINGUISHER", "ga", 0.12, "#ffd9d0", 0.8)]), "sign_ext.png")
    shell_signs()
    counter_signs()
    kitchen_signs()
    ceiling()
    open(os.path.join(OUT, ".done"), "w").write("ok")
    print("store_tex:", OUT)
