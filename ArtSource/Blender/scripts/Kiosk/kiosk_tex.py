"""키오스크 2D 텍스처 (Pillow). venv 파이썬으로 실행: kiosk_tex.py <K3D_ROOT> <K3D_CACHE>
LAYOUT 은 kiosk.py(Blender)도 import 해서 같은 좌표를 쓴다 (PIL 은 함수 안에서만 import)."""
import os, sys, json, math, random

# ---- 공통 배치 (Blender 좌표: X 오른쪽, Z 위, 정면 = -Y, 미터) ----
LAYOUT = dict(
    W=0.60, D=0.11, Z0=0.34, Z1=1.80,           # 본체
    FY=-0.057,                                   # 전면 브러시드 판 앞면 y
    SCR=(0.0, 1.385, 0.42, 0.7467),              # 화면 중심 x,z, 폭, 높이
    BEZ=(0.47, 0.805),                           # 검은 테두리(유리) 크기
    PANEL=(0.0, 0.66, 0.54, 0.585),              # 하단 조작부 판 (동적 텍스처)
    MODS={'barcode': (-0.145, 0.862), 'receipt': (-0.145, 0.708), 'ic': (0.142, 0.838), 'member': (0.0, 0.79)},
    MOD=(0.122, 0.04, 0.008),                    # 슬롯 모듈 베젤 폭, 높이, 돌출
    NFC=(-0.145, 0.578, 0.078, 0.056),
    CALL=(-0.235, 0.915),
    TERM=(0.16, 0.555, 0.118, 0.20, 0.05, -0.24),  # 단말기 중심 x,z, 폭, 높이, 두께, 기울기
    GRILLE=(-0.166, 0.411),
    HEADER=(1.85, 0.63, 0.10),
)
P_W, P_H = 1890, 2048          # 조작부 텍스처
SCR_W, SCR_H = 1080, 1920


def panel_px(x, z):
    cx, cz, w, h = LAYOUT['PANEL']
    return (x - (cx - w / 2)) / w * P_W, ((cz + h / 2) - z) / h * P_H


def main(root, cache, only=()):
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
    import numpy as np
    rnd = random.Random(7)
    out = os.path.join(root, "Assets", "Art3D", "Textures", "Kiosk")
    src = os.path.join(cache, "kiosk_src")
    os.makedirs(out, exist_ok=True)
    os.makedirs(src, exist_ok=True)
    IMG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_ref", "img"))
    FD = os.path.join(cache, "fonts")
    HOME = os.path.expanduser("~/Library/Fonts")
    SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
    FONTS = {'r': (SD, 0), 'm': (SD, 2), 'sb': (SD, 4), 'b': (SD, 6),
             'eb': (os.path.join(HOME, "NanumSquareEB.ttf"), 0), 'sqb': (os.path.join(HOME, "NanumSquareB.ttf"), 0),
             'bhs': (os.path.join(FD, "BlackHanSans-Regular.ttf"), 0), 'pen': (os.path.join(FD, "NanumPenScript-Regular.ttf"), 0),
             'dh': (os.path.join(FD, "DoHyeon-Regular.ttf"), 0)}
    _fc = {}

    def F(k, s):
        s = max(6, int(round(s)))
        if (k, s) not in _fc:
            p, i = FONTS[k]
            _fc[(k, s)] = ImageFont.truetype(p, s, index=i)
        return _fc[(k, s)]

    def T(d, xy, s, k, size, fill, anchor="ls", maxw=None):
        f = F(k, size)
        if maxw:
            while d.textlength(s, font=f) > maxw and size > 8:
                size -= 1
                f = F(k, size)
        d.text(xy, s, font=f, fill=fill, anchor=anchor)

    def hexc(h, a=255):
        h = h.lstrip('#')
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), a)

    def grad(w, h, c0, c1, horiz=False):
        t = np.linspace(0, 1, w if horiz else h)[None, :, None] if horiz else np.linspace(0, 1, h)[:, None, None]
        a, b = np.array(hexc(c0), float), np.array(hexc(c1), float)
        arr = a + (b - a) * t
        arr = np.broadcast_to(arr, (h, w, 4)).astype(np.uint8)
        return Image.fromarray(np.ascontiguousarray(arr), "RGBA")

    def radial(w, h, cx, cy, stops, r):
        yy, xx = np.mgrid[0:h, 0:w]
        t = np.clip(np.hypot(xx - cx, yy - cy) / r, 0, 1)
        arr = np.zeros((h, w, 4))
        ps = [s[0] for s in stops]
        for ch in range(4):
            arr[..., ch] = np.interp(t, ps, [hexc(s[1])[ch] for s in stops])
        return Image.fromarray(arr.astype(np.uint8), "RGBA")

    def photo(name, box, img, shadow=True):
        p = os.path.join(IMG, name)
        ph = Image.open(p).convert("RGBA")
        x, y, w, h = box
        s = min(w / ph.width, h / ph.height)
        ph = ph.resize((max(1, int(ph.width * s)), max(1, int(ph.height * s))), Image.LANCZOS)
        px, py = int(x + (w - ph.width) / 2), int(y + (h - ph.height) / 2)
        if shadow:
            sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).ellipse([px + ph.width * .12, py + ph.height * .86, px + ph.width * .88, py + ph.height * .98], fill=(40, 10, 5, 110))
            img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(max(2, ph.width // 40))))
        img.alpha_composite(ph, (px, py))

    def crown(d, cx, cy, n, fill=(240, 198, 58, 255)):
        d.polygon([(cx - n, cy + n * .5), (cx - n * 1.1, cy - n * .55), (cx - n * .45, cy), (cx, cy - n * .8),
                   (cx + n * .45, cy), (cx + n * 1.1, cy - n * .55), (cx + n, cy + n * .5)], fill=fill)

    def logo(img, cx, cy, s, text=None, alpha=255):
        # 버거 + 왕관 (패러디 브랜드, 실제 로고와 무관)
        L = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        def P(x, y):
            return (cx + x * s, cy + y * s)
        d.pieslice([P(-62, -52), P(62, 36)], 180, 360, fill=(217, 138, 43, alpha))
        d.rectangle([P(-60, -6), P(60, 10)], fill=(107, 58, 30, alpha))
        d.rounded_rectangle([P(-58, 12), P(58, 34)], radius=8 * s, fill=(217, 138, 43, alpha))
        d.polygon([P(-30, -48), P(-34, -82), P(-14, -62), P(0, -90), P(14, -62), P(34, -82), P(30, -48)], fill=(240, 198, 58, alpha))
        for sx in (-22, -6, 12, 26):
            d.ellipse([P(sx - 3, -34), P(sx + 3, -30)], fill=(255, 236, 190, alpha))
        if text:
            T(d, P(0, 72), "버거대왕", 'eb', 50 * s, text, "mm")
        img.alpha_composite(L)

    def rays(img, cx, cy, n, col, r=2600):
        L = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        for i in range(n):
            a = i / n * 6.2832
            b = a + 3.1416 / n
            d.polygon([(cx, cy), (cx + math.cos(a) * r, cy + math.sin(a) * r), (cx + math.cos(b) * r, cy + math.sin(b) * r)], fill=col)
        img.alpha_composite(L)

    def qr(d, x, y, n, dark=(42, 26, 16, 255)):
        d.rectangle([x, y, x + n, y + n], fill=(255, 255, 255, 255))
        s, r = 25, (n - 16) / 25
        o = 12345
        for a in range(s):
            for b in range(s):
                o = (o * 1103515245 + 12345) & 2147483647
                if (o >> 16) & 1:
                    d.rectangle([x + 8 + a * r, y + 8 + b * r, x + 8 + (a + 1) * r, y + 8 + (b + 1) * r], fill=dark)
        for a, b in ((0, 0), (s - 7, 0), (0, s - 7)):
            X, Y = x + 8 + a * r, y + 8 + b * r
            d.rectangle([X - r, Y - r, X + 8 * r, Y + 8 * r], fill=(255, 255, 255, 255))
            d.rectangle([X, Y, X + 7 * r, Y + 7 * r], fill=dark)
            d.rectangle([X + r, Y + r, X + 6 * r, Y + 6 * r], fill=(255, 255, 255, 255))
            d.rectangle([X + 2 * r, Y + 2 * r, X + 5 * r, Y + 5 * r], fill=dark)

    def prints(img, n, box, rng, col=(70, 55, 40), a=24, rmin=12, rmax=26, s=1.0):
        # 지문 (동심 타원 호)
        L = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        x0, y0, x1, y1 = box
        for _ in range(n):
            cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
            R = rng.uniform(rmin, rmax) * s
            rot = rng.uniform(0, 3)
            for k in np.arange(3 * s, R, 2.6 * s):
                pts = []
                for t in np.linspace(.3, 5.9, 26):
                    ex, ey = math.cos(t) * k, math.sin(t) * k * 1.35 + k * .15
                    pts.append((cx + ex * math.cos(rot) - ey * math.sin(rot), cy + ex * math.sin(rot) + ey * math.cos(rot)))
                d.line(pts, fill=(*col, a), width=max(1, int(s)))
        img.alpha_composite(L.filter(ImageFilter.GaussianBlur(0.6 * s)))

    def grime(img, rng, dust=300, scratch=40, s=1.0, dcol=(90, 75, 55), scol=(255, 255, 255)):
        L = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        w, h = img.size
        for _ in range(dust):
            x, y, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(.6, 2.4) * s
            d.ellipse([x - r, y - r, x + r, y + r], fill=(*dcol, int(rng.uniform(10, 36))))
        for _ in range(scratch):
            x, y = rng.uniform(0, w), rng.uniform(0, h)
            d.line([(x, y), (x + rng.uniform(-90, 90) * s, y + rng.uniform(-30, 30) * s)], fill=(*scol, int(rng.uniform(14, 34))), width=1)
        img.alpha_composite(L)

    def paper(img, rng, fade=0.06, warm=(255, 244, 222), edge=True):
        # 인쇄물 노화: 바램 + 종이결 + 가장자리 마모
        a = np.asarray(img).astype(np.float32)
        w = np.array(warm, np.float32)
        a[..., :3] = a[..., :3] * (1 - fade) + w * fade
        n = np.asarray(Image.effect_noise(img.size, 22).filter(ImageFilter.GaussianBlur(0.7))).astype(np.float32) - 128
        a[..., :3] += n[..., None] * 0.10
        if edge:
            h, wd = a.shape[:2]
            yy, xx = np.mgrid[0:h, 0:wd]
            dd = np.minimum(np.minimum(xx, wd - 1 - xx), np.minimum(yy, h - 1 - yy)).astype(np.float32)
            m = np.clip(1 - dd / 6.0, 0, 1) * (0.5 + 0.5 * (np.asarray(Image.effect_noise(img.size, 60)) / 255.0))
            a[..., :3] = a[..., :3] * (1 - m[..., None] * 0.35) + 245 * m[..., None] * 0.35
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")

    FINE = "본 이미지는 연출된 것으로 실제와 다를 수 있습니다. 일부 매장 제외. 알레르기 유발 성분과 원산지 정보는 매장 내 게시물을 참고해 주십시오. 쇠고기(호주산, 뉴질랜드산) 닭고기(국내산, 브라질산) 쌀(국내산) 멤버십 약관 제12조에 따라 적립은 익영업일에 반영됩니다. 제휴 할인 중복 불가."

    def wrap(d, s, x, y, maxw, lh, k, size, fill, maxlines=99):
        f = F(k, size)
        line, n = "", 0
        for c in s:
            if d.textlength(line + c, font=f) > maxw:
                d.text((x, y), line, font=f, fill=fill)
                y += lh
                n += 1
                line = "" if c == " " else c
                if n >= maxlines:
                    return y
            else:
                line += c
        d.text((x, y), line, font=f, fill=fill)
        return y + lh

    RED, CREAM, GOLD, BROWN, MID, SOFT = "#c8291f", "#fff6e6", "#f0c63a", "#3a2416", "#6b4a30", "#8d7a64"

    # ================= 화면: 대기(attract) =================
    def attract():
        S = 2
        W, H = SCR_W * S, SCR_H * S
        im = radial(W, H, 540 * S, 860 * S, [(0, "#e2483a"), (.6, "#b3201a"), (1, "#6e0f0a")], 1200 * S)
        rays(im, 540 * S, 870 * S, 22, (255, 220, 170, 16))
        logo(im, 540 * S, 250 * S, 1.6 * S)
        d = ImageDraw.Draw(im)
        T(d, (540 * S, 430 * S), "K-BBQ SMOKY", 'eb', 112 * S, hexc(CREAM), "ms", 980 * S)
        T(d, (540 * S, 556 * S), "FESTA", 'eb', 132 * S, hexc(GOLD), "ms")
        T(d, (540 * S, 616 * S), "한정 수량 11.30까지", 'b', 36 * S, hexc("#ffdcc4"), "ms")
        photo("burger_bulgogi.png", (110 * S, 650 * S, 860 * S, 860 * S), im)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([700 * S, 700 * S, 1010 * S, 820 * S], radius=60 * S, fill=hexc(GOLD))
        T(d, (855 * S, 778 * S), "NEW 5,900원~", 'eb', 40 * S, hexc("#7a120c"), "ms")
        d.rectangle([0, 1530 * S, W, H], fill=hexc(CREAM))
        d.rectangle([0, 1530 * S, W, 1542 * S], fill=hexc(RED))
        # 손가락 아이콘 + 안내
        hx, hy = 262 * S, 1590 * S
        d.ellipse([hx - 20 * S, hy - 20 * S, hx + 20 * S, hy + 20 * S], outline=hexc(RED, 150), width=3 * S)
        d.rounded_rectangle([hx - 6 * S, hy - 8 * S, hx + 6 * S, hy + 26 * S], radius=6 * S, fill=hexc(BROWN))
        d.rounded_rectangle([hx - 6 * S, hy + 10 * S, hx + 24 * S, hy + 40 * S], radius=10 * S, fill=hexc(BROWN))
        T(d, (300 * S, 1622 * S), "화면을 손으로 누르세요", 'b', 46 * S, hexc(BROWN), "ls")
        T(d, (540 * S, 1722 * S), "TOUCH TO ORDER", 'eb', 112 * S, hexc(RED), "ms", 1000 * S)
        T(d, (540 * S, 1772 * S), "터치하여 주문", 'sb', 34 * S, hexc(SOFT), "ms")
        T(d, (540 * S, 1822 * S), "카드 전용 CARD ONLY   현금 불가 NO CASH", 'b', 28 * S, hexc(MID), "ms")
        wrap(d, FINE, 28 * S, 1848 * S, (SCR_W - 56) * S, 22 * S, 'm', 16 * S, hexc("#a5947c"), 2)
        im = im.resize((SCR_W, SCR_H), Image.LANCZOS)
        im.convert("RGB").save(os.path.join(out, "T_Kiosk_Screen_Attract.png"), optimize=True)

    # ================= 화면: 메뉴 =================
    ART = {'triple': 'burger_double.png', 'truffle': 'burger_cheese.png', 'double': 'burger_bacon.png', 'spicy': 'burger_bacon.png',
           'green': 'burger_chicken.png', 'chicken': 'burger_chicken.png', 'mushroom': 'burger_cheese.png'}
    ITEMS = [("크라운 트리플 스택", "Triple Flame Grilled", 11900, 1120, "triple", "BEST"),
             ("앵거스 트러플 오 그라탕", "Limited Reserve", 12400, 980, "truffle", "NEW"),
             ("더 그랜드 K-그릴 플래티넘", "Char Broiled Edition", 10900, 890, "double", ""),
             ("하바네로 인페르노 비프", "Scoville 8,000", 9900, 760, "spicy", "HOT"),
             ("아보카도 슈프림 그릴드", "Fresh Cut Daily", 10400, 720, "green", ""),
             ("로열 스모크 하우스", "Hickory Reserve", 11200, 930, "double", ""),
             ("버터밀크 크런치 XL", "Southern Style", 9400, 840, "chicken", ""),
             ("왕관 머쉬룸 타워", "Wild Forest", 10100, 790, "mushroom", ""),
             ("비욘드 크라운 플랜트", "Zero Animal", 9800, 610, "green", "ECO")]

    def won(v):
        return f"{v:,}원"

    def header(im, d, S, sub):
        g = grad(SCR_W * S, 132 * S, "#d3322a", "#b5211a")
        im.alpha_composite(g, (0, 0))
        d.rectangle([0, 128 * S, SCR_W * S, 132 * S], fill=(0, 0, 0, 30))
        logo(im, 82 * S, 92 * S, .72 * S)
        T(d, (150 * S, 76 * S), "버거대왕", 'eb', 46 * S, hexc("#fffdf8"), "ls")
        T(d, (152 * S, 106 * S), "CROWN SELF ORDER", 'b', 19 * S, hexc("#ffd9c8"), "ls")
        T(d, (410 * S, 84 * S), sub, 'eb', 26 * S, hexc("#fff0da"), "ls")
        for i, s in enumerate(["KO", "EN", "中", "日"]):
            x = (640 + i * 64) * S
            d.rounded_rectangle([x, 44 * S, x + 56 * S, 88 * S], radius=4 * S, fill=(255, 255, 255, 72 if i == 0 else 20), outline=(255, 255, 255, 100), width=2 * S)
            T(d, (x + 28 * S, 75 * S), s, 'b', 22 * S, (255, 255, 255, 255), "ms")

    def menu():
        S = 2
        W, H = SCR_W * S, SCR_H * S
        im = Image.new("RGBA", (W, H), hexc(CREAM))
        d = ImageDraw.Draw(im)
        header(im, d, S, "DINE-IN")
        im.alpha_composite(grad(W, 210 * S, "#7f150e", "#d1362b", horiz=True), (0, 132 * S))
        d = ImageDraw.Draw(im)
        T(d, (36 * S, 214 * S), "K-BBQ SMOKY FESTA", 'eb', 62 * S, hexc(CREAM), "ls", 640 * S)
        T(d, (36 * S, 266 * S), "세트 주문 시 라지 업그레이드 800원", 'b', 32 * S, hexc(GOLD), "ls", 640 * S)
        T(d, (36 * S, 310 * S), "11.30까지 일부 매장 한정", 'm', 22 * S, hexc("#ffd5bf"), "ls")
        photo("cola.png", (840 * S, 150 * S, 200 * S, 180 * S), im)
        photo("burger_bulgogi.png", (680 * S, 140 * S, 230 * S, 200 * S), im)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 342 * S, W, 446 * S], fill=hexc("#fffdf8"))
        tabs = ["SIGNATURE", "PREMIUM", "CLASSIC", "SIDE", "BEVERAGE", "DESSERT"]
        for i, t in enumerate(tabs):
            x = i * 180 * S
            if i == 0:
                d.rounded_rectangle([x + 3 * S, 346 * S, x + 177 * S, 446 * S], radius=8 * S, fill=hexc(RED))
            T(d, (x + 90 * S, 408 * S), t, 'eb', 28 * S, hexc("#fffdf8") if i == 0 else hexc(MID), "ms", 164 * S)
        d.rectangle([0, 442 * S, W, 447 * S], fill=hexc(RED))
        d.rectangle([0, 447 * S, W, 503 * S], fill=hexc("#f4e6cb"))
        for i, t in enumerate(["ALL", "NEW", "BEST", "LOW CAL", "SPICY"]):
            T(d, ((34 + i * 138) * S, 484 * S), t, 'eb' if i == 0 else 'sb', 24 * S, hexc(RED) if i == 0 else hexc(SOFT), "ls")
        T(d, (1050 * S, 484 * S), "9 ITEMS", 'sb', 22 * S, hexc(SOFT), "rs")
        for k, (nm, en, pr, kc, art, tag) in enumerate(ITEMS):
            x, y = (18 + k % 3 * 352) * S, (518 + k // 3 * 378) * S
            w, h = 340 * S, 366 * S
            sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
            ImageDraw.Draw(sh).rounded_rectangle([x, y + 5 * S, x + w, y + h + 5 * S], radius=8 * S, fill=(70, 40, 15, 46))
            im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7 * S)))
            d = ImageDraw.Draw(im)
            d.rounded_rectangle([x, y, x + w, y + h], radius=8 * S, fill=hexc("#fffdf8"))
            d.rounded_rectangle([x, y, x + w, y + 196 * S], radius=8 * S, fill=hexc("#fbf0dc"))
            d.rectangle([x, y + 180 * S, x + w, y + 196 * S], fill=hexc("#fbf0dc"))
            photo(ART[art], (x + 22 * S, y + 6 * S, w - 44 * S, 186 * S), im)
            d = ImageDraw.Draw(im)
            if tag:
                d.rounded_rectangle([x, y + 10 * S, x + 84 * S, y + 46 * S], radius=4 * S, fill=hexc(BROWN if tag == "NEW" else RED))
                T(d, (x + 42 * S, y + 37 * S), tag, 'eb', 22 * S, (255, 255, 255, 255), "ms")
            if len(nm) > 11 and nm.rfind(" ", 0, 13) > 0:
                c = nm.rfind(" ", 0, 13)
                T(d, (x + 16 * S, y + 238 * S), nm[:c], 'eb', 30 * S, hexc(BROWN), "ls", w - 28 * S)
                T(d, (x + 16 * S, y + 274 * S), nm[c + 1:], 'eb', 30 * S, hexc(BROWN), "ls", w - 28 * S)
            else:
                T(d, (x + 16 * S, y + 252 * S), nm, 'eb', 30 * S, hexc(BROWN), "ls", w - 28 * S)
            T(d, (x + 16 * S, y + 304 * S), en, 'm', 19 * S, hexc(SOFT), "ls")
            T(d, (x + 16 * S, y + 348 * S), won(pr), 'eb', 34 * S, hexc(RED), "ls")
            T(d, (x + w - 14 * S, y + 346 * S), f"{kc}kcal", 'm', 20 * S, hexc(SOFT), "rs")
        d.rectangle([0, 1656 * S, W, H], fill=hexc(BROWN))
        d.rectangle([0, 1656 * S, W, 1662 * S], fill=hexc(RED))
        T(d, (30 * S, 1712 * S), "MY ORDER", 'eb', 32 * S, hexc(CREAM), "ls")
        T(d, (30 * S, 1752 * S), "0 ITEM", 'sb', 26 * S, hexc("#d7c3a4"), "ls")
        T(d, (760 * S, 1712 * S), "TOTAL", 'b', 26 * S, hexc("#d7c3a4"), "ls")
        T(d, (1050 * S, 1746 * S), "0원", 'eb', 56 * S, hexc(GOLD), "rs")
        d.rounded_rectangle([30 * S, 1778 * S, 280 * S, 1866 * S], radius=6 * S, fill=hexc("#5a4230"), outline=hexc("#8a6f55"), width=2 * S)
        T(d, (155 * S, 1836 * S), "HOME", 'eb', 34 * S, hexc(CREAM), "ms")
        d.rounded_rectangle([292 * S, 1778 * S, 1050 * S, 1866 * S], radius=6 * S, fill=hexc("#6e5a48"))
        T(d, (671 * S, 1838 * S), "CHECK OUT", 'eb', 44 * S, hexc("#a3917e"), "ms")
        wrap(d, FINE, 30 * S, 1878 * S, (SCR_W - 60) * S, 19 * S, 'm', 15 * S, hexc("#9f8a70"), 2)
        im = im.resize((SCR_W, SCR_H), Image.LANCZOS)
        im.convert("RGB").save(os.path.join(out, "T_Kiosk_Screen_Menu.png"), optimize=True)

    # ================= 하단 조작부 판 (동적, 돋보기용 Lens 버전 포함) =================
    def picto(d, kind, cx, cy, s, col):
        # 아주 작은 픽토그램 (s = 픽셀/mm)
        w = max(1, int(.5 * s))
        if kind == "SCAN":
            for i in range(7):
                x = cx - 3.4 * s + i * 1.1 * s
                d.rectangle([x, cy - 2.4 * s, x + (0.35 if i % 3 else 0.7) * s, cy + 2.4 * s], fill=col)
        elif kind == "PRINT":
            d.rectangle([cx - 2.6 * s, cy - 3 * s, cx + 2.6 * s, cy + 3 * s], outline=col, width=w)
            for i in range(3):
                d.line([(cx - 1.6 * s, cy - 1.4 * s + i * 1.4 * s), (cx + 1.6 * s, cy - 1.4 * s + i * 1.4 * s)], fill=col, width=w)
        elif kind in ("CARD", "MEMBER"):
            d.rounded_rectangle([cx - 3.6 * s, cy - 2.3 * s, cx + 3.6 * s, cy + 2.3 * s], radius=.6 * s, outline=col, width=w)
            if kind == "CARD":
                d.rectangle([cx - 2.6 * s, cy - 1.0 * s, cx - 1.0 * s, cy + .4 * s], fill=col)
            else:
                d.line([(cx - 3.6 * s, cy - .9 * s), (cx + 3.6 * s, cy - .9 * s)], fill=col, width=w * 2)
        elif kind == "TAP":
            for i in range(3):
                r = (1.4 + i * 1.3) * s
                d.arc([cx - r - 2 * s, cy - r, cx + r - 2 * s, cy + r], -50, 50, fill=col, width=w)
        elif kind == "CALL":
            d.pieslice([cx - 2.5 * s, cy - 2.8 * s, cx + 2.5 * s, cy + 2.2 * s], 180, 360, fill=col)
            d.rectangle([cx - 2.5 * s, cy - .4 * s, cx + 2.5 * s, cy + 1.6 * s], fill=col)
            d.ellipse([cx - .7 * s, cy + 1.7 * s, cx + .7 * s, cy + 3.1 * s], fill=col)

    def panel():
        S = 3500.0 / 1000  # px/mm
        rng = random.Random(11)
        im = grad(P_W, P_H, "#46413b", "#2d2a26")
        a = np.asarray(im).astype(np.float32)
        n = np.asarray(Image.effect_noise((P_W, P_H), 30).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) - 128
        a[..., :3] += n[..., None] * 0.08
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        L = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        # 모듈/단말기 주변 접촉 그림자
        mw, mh, _ = LAYOUT['MOD']
        def shadow_rect(cx, cz, w, h, grow, alpha):
            x0, y0 = panel_px(cx - w / 2 - grow, cz + h / 2 + grow)
            x1, y1 = panel_px(cx + w / 2 + grow, cz - h / 2 - grow * 1.6)
            d.rounded_rectangle([x0, y0, x1, y1], radius=int(10 * S), fill=(0, 0, 0, alpha))
        for k, (x, z) in LAYOUT['MODS'].items():
            shadow_rect(x, z - 0.002, mw, mh, 0.004, 120)
        nx, nz, nw, nh = LAYOUT['NFC']
        shadow_rect(nx, nz - 0.002, nw, nh, 0.003, 110)
        tx, tz = LAYOUT['TERM'][:2]
        shadow_rect(tx, tz - 0.01, 0.09, 0.15, 0.01, 130)
        cx, cz = LAYOUT['CALL']
        shadow_rect(cx, cz - 0.002, 0.046, 0.046, 0.003, 120)
        gx, gz = LAYOUT['GRILLE']
        shadow_rect(gx, gz, 0.162, 0.034, 0.002, 70)
        im.alpha_composite(L.filter(ImageFilter.GaussianBlur(10)))
        # 카드로 긁힌 자국 (영수증/바코드 슬롯 주변 = 엉뚱한 데 카드를 넣으려던 흔적)
        L = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(L)
        for k in ("receipt", "barcode", "member"):
            x, z = LAYOUT['MODS'][k]
            px, py = panel_px(x, z)
            for _ in range(70):
                sx = px + rng.uniform(-.06, .06) * 3500
                sy = py + rng.choice([-1, 1]) * rng.uniform(.021, .035) * 3500
                d.line([(sx, sy), (sx + rng.uniform(-40, 40), sy + rng.uniform(-6, 6))], fill=(230, 225, 215, int(rng.uniform(18, 60))), width=1)
        tpx, tpy = panel_px(tx, tz - 0.11)
        for _ in range(40):
            sx, sy = tpx + rng.uniform(-150, 150), tpy + rng.uniform(-30, 40)
            d.line([(sx, sy), (sx + rng.uniform(-30, 30), sy + rng.uniform(-8, 8))], fill=(230, 225, 215, int(rng.uniform(15, 45))), width=1)
        im.alpha_composite(L)
        grime(im, rng, dust=900, scratch=160, s=2.0)
        prints(im, 40, (P_W * .08, P_H * .1, P_W * .92, P_H * .6), rng, col=(255, 255, 255), a=10, s=2.0)
        # 하단 걷어차인 먼지
        g = grad(P_W, int(P_H * .25), "#000000", "#2a2018")
        ga = np.asarray(g).copy()
        ga[..., 3] = np.linspace(0, 70, ga.shape[0])[:, None].astype(np.uint8)
        im.alpha_composite(Image.fromarray(ga, "RGBA"), (0, int(P_H * .75)))
        logo(im, *panel_px(0.0, 0.50), 1.1, alpha=40)
        base = im.copy()
        d = ImageDraw.Draw(base)
        LBL = (185, 176, 162, 255)
        labels = [("SCAN", -0.145, 0.862 - 0.031), ("PRINT", -0.145, 0.708 - 0.031), ("MEMBER", 0.0, 0.79 - 0.031),
                  ("CARD", 0.142, 0.735), ("TAP", -0.145, 0.578 - 0.039), ("CALL", -0.235, 0.915 - 0.03)]
        for txt, x, z in labels:
            px, py = panel_px(x, z)
            tw = d.textlength(txt, font=F('b', 6 * S))
            picto(d, txt, px - tw / 2 - 6 * S, py - 2.2 * S, S, LBL)
            T(d, (px + 4 * S, py), txt, 'b', 6 * S, LBL, "ms")
            d.polygon([(px - 2 * S, py - 7.2 * S), (px + 2 * S, py - 7.2 * S), (px, py - 9.4 * S)], fill=LBL)
        T(d, panel_px(-0.145, 0.448), "고객센터 1588-0000", 'sb', 4.6 * S, (160, 152, 140, 255), "ms")
        T(d, panel_px(0.0, 0.392), "CROWN SELF ORDER  KS-2150F", 'm', 3.2 * S, (120, 114, 104, 255), "ms")
        base.convert("RGB").save(os.path.join(out, "T_Kiosk_Panel.png"), optimize=True)
        # 돋보기 버전: 노란 쪽지로 한국어 뜻
        lens = base.copy()
        d = ImageDraw.Draw(lens)
        notes = [("바코드 읽는 곳", -0.145, 0.862 - 0.052), ("영수증 나오는 곳", -0.145, 0.708 - 0.052),
                 ("멤버십 카드 (사용 안 함)", 0.0, 0.79 - 0.052), ("카드 구멍은 위쪽 종이 뒤", 0.142, 0.714),
                 ("휴대폰 갖다 대는 곳", -0.145, 0.578 - 0.06), ("직원 호출", -0.235, 0.915 - 0.051)]
        for txt, x, z in notes:
            px, py = panel_px(x, z)
            f = F('eb', 6.5 * S)
            tw = d.textlength(txt, font=f)
            d.rectangle([px - tw / 2 - 10, py - 7.5 * S, px + tw / 2 + 10, py + 2.5 * S], fill=(255, 243, 180, 255), outline=(58, 36, 22, 255), width=3)
            d.text((px, py), txt, font=f, fill=(42, 26, 16, 255), anchor="ms")
        lens.convert("RGB").save(os.path.join(out, "T_Kiosk_Panel_Lens.png"), optimize=True)

    # ================= 단말기 LCD (동적) =================
    def lcd():
        W, H = 512, 292
        im = grad(W, H, "#2f5876", "#1f3a52")
        d = ImageDraw.Draw(im)
        T(d, (W / 2, 82), "K-PAY", 'eb', 64, (232, 242, 246, 255), "ms")
        T(d, (W / 2, 150), "READY", 'b', 46, (232, 242, 246, 255), "ms")
        T(d, (W / 2, 214), "IC카드를 넣어 주세요", 'b', 34, (200, 222, 234, 255), "ms")
        d.rectangle([60, 240, W - 60, 250], fill=(159, 196, 216, 255))
        a = np.asarray(im).astype(np.float32)
        a[::3, :, :3] *= 0.9  # LCD 픽셀 줄
        im = Image.fromarray(a.astype(np.uint8), "RGBA")
        im.convert("RGB").save(os.path.join(out, "T_Kiosk_TerminalLcd.png"), optimize=True)

    # ================= 상단 라이트박스 간판 =================
    def header_sign():
        W, H = 2048, 289
        im = grad(W, H, "#d8362c", "#a81d16")
        # 라이트박스 LED 핫스팟
        hot = radial(W, H, W / 2, H * .45, [(0, "#ffffff"), (1, "#000000")], W * .6)
        ha = np.asarray(hot).astype(np.float32)[..., 0] / 255
        a = np.asarray(im).astype(np.float32)
        a[..., :3] *= (0.86 + 0.22 * ha[..., None])
        for i in range(9):
            x = (i + .5) / 9 * W
            yy, xx = np.mgrid[0:H, 0:W]
            a[..., :3] *= 1 + 0.035 * np.exp(-((xx - x) ** 2) / (2 * 90 ** 2))[..., None]
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
        logo(im, 150, 205, 1.55)
        d = ImageDraw.Draw(im)
        T(d, (290, 196), "버거대왕", 'eb', 158, hexc("#fff6e6"), "ls")
        T(d, (W - 70, 186), "셀프 주문  SELF ORDER", 'eb', 78, hexc("#fff6e6"), "rs")
        im.convert("RGB").save(os.path.join(out, "T_Kiosk_Header.png"), optimize=True)

    # ================= 유리 지문/얼룩 (알파) =================
    def glass():
        bw, bh = LAYOUT['BEZ']
        sw, sh = LAYOUT['SCR'][2:]
        W = 1024
        H = int(round(W * bh / bw))
        rng = random.Random(5)
        A = Image.new("L", (W, H), 9)
        d = ImageDraw.Draw(A)
        sx0, sy0 = (bw - sw) / 2 / bw * W, (bh - sh) / 2 / bh * H
        sx1, sy1 = W - sx0, H - sy0
        # 손가락 문지른 자국 (스와이프)
        for _ in range(26):
            x, y = rng.uniform(sx0, sx1), rng.uniform(sy0 + (sy1 - sy0) * .25, sy1)
            L = Image.new("L", (W, H), 0)
            ld = ImageDraw.Draw(L)
            ln = rng.uniform(30, 160)
            ang = rng.uniform(-0.6, 0.6) + (math.pi / 2 if rng.random() < .5 else 0)
            ld.line([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)], fill=int(rng.uniform(14, 30)), width=int(rng.uniform(10, 22)))
            A = ImageChops.add(A, L.filter(ImageFilter.GaussianBlur(5)))
        # 지문: 화면 하단(주문 버튼)과 메뉴 영역에 몰림
        L = Image.new("L", (W, H), 0)
        ld = ImageDraw.Draw(L)
        def fp(cx, cy, R, a):
            rot = rng.uniform(0, 3)
            for k in np.arange(2, R, 2.2):
                pts = []
                for t in np.linspace(.2, 6.0, 30):
                    ex, ey = math.cos(t) * k, math.sin(t) * k * 1.4 + k * .2
                    pts.append((cx + ex * math.cos(rot) - ey * math.sin(rot), cy + ex * math.sin(rot) + ey * math.cos(rot)))
                ld.line(pts, fill=a, width=1)
        for _ in range(70):
            zone = rng.random()
            if zone < .45:
                cx, cy = rng.uniform(sx0 + 40, sx1 - 40), rng.uniform(sy0 + (sy1 - sy0) * .82, sy1 - 10)
            elif zone < .85:
                cx, cy = rng.uniform(sx0 + 30, sx1 - 30), rng.uniform(sy0 + (sy1 - sy0) * .28, sy0 + (sy1 - sy0) * .8)
            else:
                cx, cy = rng.uniform(0, W), rng.uniform(0, H)
            fp(cx, cy, rng.uniform(9, 16), int(rng.uniform(40, 80)))
        A = ImageChops.add(A, L.filter(ImageFilter.GaussianBlur(0.7)))
        # 먼지 + 미세 스크래치
        d = ImageDraw.Draw(A)
        for _ in range(500):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            d.point((x, y), fill=int(rng.uniform(40, 110)))
        for _ in range(12):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            d.line([(x, y), (x + rng.uniform(-60, 60), y + rng.uniform(-14, 14))], fill=60, width=1)
        rgb = Image.new("RGB", (W, H), (236, 238, 240))
        im = rgb.copy()
        im.putalpha(A)
        im.save(os.path.join(out, "T_Kiosk_Glass.png"), optimize=True)

    # ================= 종이 아틀라스 (포스터/스티커/점검중) =================
    def poster_festa(w, h):
        im = grad(w, h, "#d4342a", "#7a120c")
        logo(im, w / 2, h * .1, w / 620)
        d = ImageDraw.Draw(im)
        T(d, (w / 2, h * .24), "불고기", 'bhs', w * .19, hexc("#fff4de"), "ms")
        T(d, (w / 2, h * .345), "페스타", 'bhs', w * .23, hexc(GOLD), "ms")
        photo("burger_bulgogi.png", (w * .06, h * .36, w * .88, h * .36), im)
        d = ImageDraw.Draw(im)
        d.rectangle([0, h * .72, w, h * .85], fill=hexc(GOLD))
        T(d, (w / 2, h * .815), "1+1 쿠폰", 'bhs', w * .16, hexc("#7a120c"), "ms")
        T(d, (w / 2, h * .9), "앱 전용 11.30까지", 'b', w * .062, hexc("#ffdcc4"), "ms")
        wrap(d, FINE[:120], w * .06, h * .93, w * .88, w * .03, 'm', w * .024, hexc("#e8a99a"), 3)
        return im

    def poster_triple(w, h):
        im = Image.new("RGBA", (w, h), hexc("#fff3d9"))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w, h * .3], fill=hexc(RED))
        T(d, (w / 2, h * .15), "NEW", 'bhs', w * .2, (255, 255, 255, 255), "ms")
        T(d, (w / 2, h * .255), "크라운 트리플", 'bhs', w * .11, (255, 255, 255, 255), "ms")
        photo("burger_double.png", (w * .04, h * .3, w * .92, h * .52), im)
        d = ImageDraw.Draw(im)
        T(d, (w / 2, h * .9), "11,900원", 'bhs', w * .14, hexc(BROWN), "ms")
        T(d, (w / 2, h * .96), "세트 +2,000원 · 매장 사정에 따라 조기 품절", 'm', w * .036, hexc(MID), "ms")
        return im

    def poster_refill(w, h):
        im = grad(w, h, "#f0b72f", "#e27a1f")
        d = ImageDraw.Draw(im)
        T(d, (w / 2, h * .19), "무료 리필", 'bhs', w * .19, hexc(BROWN), "ms")
        T(d, (w / 2, h * .27), "앱 회원 한정, 일부 음료 제외", 'b', w * .058, hexc(BROWN), "ms")
        photo("cola.png", (w * .12, h * .31, w * .76, h * .6), im)
        d = ImageDraw.Draw(im)
        T(d, (w / 2, h * .955), "리필은 1회, 매장 내 취식 시", 'm', w * .05, hexc(BROWN), "ms")
        return im

    def cover_front(w, h):
        im = grad(w, h, "#fff3d9", "#f6dcae")
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, w, h * .24], fill=hexc(RED))
        crown(d, w * .12, h * .12, h * .07)
        T(d, (w * .22, h * .17), "왕관페이", 'eb', h * .13, (255, 255, 255, 255), "ls")
        T(d, (w * .06, h * .5), "30% 할인", 'bhs', h * .17, hexc(RED), "ls")
        T(d, (w * .06, h * .64), "첫 결제 시 즉시 적용", 'b', h * .075, hexc(BROWN), "ls")
        T(d, (w * .06, h * .74), "앱 설치, 본인 인증, 계좌 연결 필요", 'm', h * .05, hexc(MID), "ls")
        T(d, (w * .06, h * .93), "※ 최대 3,000원 · 1인 1회 · 타 쿠폰 중복 불가", 'm', h * .04, hexc(SOFT), "ls")
        photo("burger_double.png", (w * .66, h * .5, w * .32, h * .36), im)
        prints(im, 4, (w * .1, h * .3, w * .9, h * .8), random.Random(3), a=20, s=1.4)
        return im

    def cover_back(w, h, front):
        # 종이 뒷면: 회색 종이 + 앞면 인쇄가 좌우 반전으로 비침 + 테이프 쪽 진한 띠
        im = Image.new("RGBA", (w, h), hexc("#d9d2c2"))
        ghost = front.transpose(Image.FLIP_LEFT_RIGHT).convert("L").point(lambda v: 255 - v)
        g = Image.new("RGBA", (w, h), (120, 60, 50, 0))
        g.putalpha(ghost.point(lambda v: int(v * 0.12)))
        im.alpha_composite(g)
        d = ImageDraw.Draw(im)
        d.rectangle([w - w * .14, 0, w, h], fill=(120, 100, 80, 56))
        return im

    def pop_new(w, h):
        im = Image.new("RGBA", (w, h), (200, 41, 31, 255))
        d = ImageDraw.Draw(im)
        T(d, (w / 2, h * .52), "NEW", 'bhs', w * .3, hexc("#fff4de"), "ms")
        T(d, (w / 2, h * .72), "행사 중", 'bhs', w * .15, hexc(GOLD), "ms")
        r = w * .06
        d.ellipse([w / 2 - r, h * .14 - r, w / 2 + r, h * .14 + r], fill=hexc(GOLD))
        return im

    def card_only(w, h):
        im = Image.new("RGBA", (w, h), hexc("#fff8e1"))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, h * 1.3, h], fill=hexc(RED))
        # 지폐에 금지 표시
        cx, cy, r = h * .65, h / 2, h * .36
        d.rectangle([cx - r * .8, cy - r * .45, cx + r * .8, cy + r * .45], outline=(255, 255, 255, 255), width=max(2, int(h * .05)))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 255), width=max(2, int(h * .07)))
        d.line([(cx - r * .7, cy - r * .7), (cx + r * .7, cy + r * .7)], fill=(255, 255, 255, 255), width=max(2, int(h * .07)))
        T(d, (h * 1.5, h * .5), "카드 전용", 'eb', h * .42, hexc(RED), "lm")
        T(d, (h * 1.5 + d.textlength("카드 전용 ", font=F('eb', h * .42)), h * .52), "CARD ONLY", 'b', h * .3, hexc(BROWN), "lm")
        T(d, (w - h * .2, h * .5), "현금 불가  NO CASH", 'eb', h * .34, hexc(BROWN), "rm")
        return im

    def jumgum(w, h):
        im = Image.new("RGBA", (w, h), hexc("#f6f3ea"))
        d = ImageDraw.Draw(im)
        d.rectangle([w * .04, h * .05, w * .96, h * .95], outline=hexc("#b52a22"), width=int(w * .012))
        T(d, (w / 2, h * .5), "점검 중", 'bhs', h * .36, hexc("#b52a22"), "ms")
        T(d, (w / 2, h * .66), "불편을 드려 죄송합니다", 'b', h * .065, hexc("#3a2a20"), "ms")
        # 손글씨 (매직)
        T(d, (w * .54, h * .86), "옆 기계 이용해 주세요!!", 'pen', h * .13, (30, 60, 150, 235), "ms")
        ax, ay = w * .14, h * .83
        d.line([(ax - w * .06, ay), (ax + w * .04, ay - h * .01)], fill=(30, 60, 150, 235), width=int(h * .012))
        d.line([(ax + w * .04, ay - h * .01), (ax + w * .015, ay - h * .045)], fill=(30, 60, 150, 235), width=int(h * .012))
        d.line([(ax + w * .04, ay - h * .01), (ax + w * .012, ay + h * .025)], fill=(30, 60, 150, 235), width=int(h * .012))
        return im

    def paper_back(w, h):
        return Image.new("RGBA", (w, h), hexc("#e9e4d8"))

    def atlas():
        S = 2560  # px/m
        # 위치 고정 배치 (px): 이름, 폭m, 높이m, x, y
        items = [("festa", .25, .56, 0, 0), ("triple", .20, .30, 652, 0), ("refill", .17, .24, 1176, 0), ("back", .04, .04, 1623, 0),
                 ("pop", .13, .13, 1623, 114), ("cover_f", .205, .17, 1176, 626), ("cover_b", .205, .17, 1176, 1073),
                 ("cardonly", .24, .026, 1176, 1520), ("jumgum", .297, .21, 0, 1446)]
        A = Image.new("RGBA", (2048, 2048), (233, 228, 216, 255))
        uv = {}
        rng = random.Random(9)
        imgs = {}
        for name, wm, hm, x, y in items:
            w, h = int(wm * S), int(hm * S)
            assert x + w <= 2048 and y + h <= 2048, name
            if name == "festa":
                im = poster_festa(w, h)
            elif name == "triple":
                im = poster_triple(w, h)
            elif name == "refill":
                im = poster_refill(w, h)
            elif name == "cover_f":
                im = cover_front(w, h)
            elif name == "cover_b":
                im = cover_back(w, h, imgs.get("cover_f_raw") or cover_front(w, h))
            elif name == "pop":
                im = pop_new(w, h)
            elif name == "cardonly":
                im = card_only(w, h)
            elif name == "jumgum":
                im = jumgum(w, h)
            else:
                im = paper_back(w, h)
            if name == "cover_f":
                imgs["cover_f_raw"] = im.copy()
            im = paper(im, rng, fade=0.05 if name != "jumgum" else 0.0, edge=name not in ("back",))
            grime(im, rng, dust=int(w * h / 4000), scratch=int(w * h / 30000), s=1.2)
            # 경계 번짐 방지: 가장자리 늘려 패딩
            A.paste(im.resize((w + 2 * 4, h + 2 * 4), Image.NEAREST), (x - 4 if x else 0, y - 4 if y else 0))
            A.paste(im, (x, y))
            uv[name] = [x / 2048, 1 - (y + h) / 2048, (x + w) / 2048, 1 - y / 2048]
        A.convert("RGB").save(os.path.join(out, "T_Kiosk_Paper_BaseColor.jpg"), quality=92)
        # 종이 노멀: 섬유 + 구김 + 접힌 자국
        hgt = np.asarray(Image.effect_noise((2048, 2048), 40).filter(ImageFilter.GaussianBlur(1.0))).astype(np.float32) / 255 * 0.6
        L = Image.new("L", (2048, 2048), 0)
        d = ImageDraw.Draw(L)
        for name, (u0, v0, u1, v1) in uv.items():
            x0, x1 = u0 * 2048, u1 * 2048
            y0, y1 = (1 - v1) * 2048, (1 - v0) * 2048
            for _ in range(4 if name != "back" else 0):
                ax, ay = rng.uniform(x0, x1), rng.uniform(y0, y1)
                d.line([(ax, ay), (ax + rng.uniform(-300, 300), ay + rng.uniform(-300, 300))], fill=int(rng.uniform(40, 90)), width=3)
            if name == "jumgum":  # A4 를 3등분 접었던 자국
                for t in (1 / 3, 2 / 3):
                    d.line([(x0, y0 + (y1 - y0) * t), (x1, y0 + (y1 - y0) * t)], fill=150, width=4)
        hgt += np.asarray(L.filter(ImageFilter.GaussianBlur(3))).astype(np.float32) / 255 * 2.0
        gx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * 0.5
        gy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * 0.5
        k = 1.6
        nx, ny, nz = -gx * k, gy * k, np.ones_like(hgt)
        ln = np.sqrt(nx * nx + ny * ny + nz * nz)
        nm = np.stack([nx / ln, ny / ln, nz / ln], -1) * 0.5 + 0.5
        Image.fromarray((nm * 255).astype(np.uint8), "RGB").save(os.path.join(out, "T_Kiosk_Paper_Normal.jpg"), quality=92)
        json.dump(uv, open(os.path.join(src, "paper_atlas.json"), "w"), indent=1)

    # ================= 베이크 입력용 데칼 =================
    def terminal_print():
        # 단말기 앞면 인쇄 (로컬 앞면 0.118 x 0.2 m 전체 = 0..1)
        w, h = 944, 1600
        s = w / 118.0  # px/mm
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        def P(xmm, zmm):  # 단말기 중심 기준 mm (z 위)
            return w / 2 + xmm * s, h / 2 - zmm * s
        T(d, P(-46, 88), "K-PAY", 'eb', 7 * s, (225, 230, 235, 255), "ls")
        T(d, P(46, 88), "KP-200", 'm', 3.2 * s, (150, 155, 160, 255), "rs")
        d.rounded_rectangle([*P(-38, 77), *P(38, 33)], radius=int(2 * s), outline=(120, 124, 128, 255), width=int(.8 * s))
        keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
        for i, k in enumerate(keys):
            cx, cz = -28 + (i % 3) * 28, 20 - (i // 3) * 18.5
            T(d, P(cx, cz - 2.6), k, 'b', 7.5 * s, (236, 232, 222, 255), "ms")
        for (cx, lab) in ((-28, "취소"), (0, "정정"), (28, "확인")):
            T(d, P(cx, -56 - 2), lab, 'b', 4.4 * s, (250, 248, 240, 255), "ms")
        T(d, P(0, -78), "▼ IC CARD", 'b', 4.0 * s, (200, 200, 200, 255), "ms")
        im.save(os.path.join(src, "src_terminal.png"))

    def small_decals():
        # NFC 패드 아이콘, 호출 버튼 종 아이콘, 뒷면 정격 라벨
        im = Image.new("RGBA", (512, 368), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i in range(4):
            r = 40 + i * 34
            d.arc([180 - r, 170 - r, 180 + r, 170 + r], -48, 48, fill=(235, 238, 240, 255), width=14)
        T(d, (256, 345), "삼성페이 · 애플페이 · 교통카드", 'b', 26, (235, 238, 240, 255), "ms")
        im.save(os.path.join(src, "src_nfc.png"))
        im = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        picto(d, "CALL", 128, 118, 26, (255, 246, 230, 255))
        im.save(os.path.join(src, "src_bell.png"))
        im = Image.new("RGBA", (800, 460), hexc("#c9ccd0"))
        d = ImageDraw.Draw(im)
        d.rectangle([6, 6, 794, 454], outline=(60, 60, 60, 255), width=4)
        rows = ["제품명: 셀프 주문 키오스크", "모델명: KS-2150F", "정격입력: AC 220V~ 60Hz 1.2A", "소비전력: 180 W",
                "제조자: (주)크라운시스템", "제조연월: 2023. 03", "제조국: 대한민국", "S/N: KS2150F-23031187"]
        for i, r in enumerate(rows):
            T(d, (30, 58 + i * 46), r, 'b', 30, (40, 40, 40, 255), "ls")
        d.ellipse([600, 40, 760, 200], outline=(40, 40, 40, 255), width=10)
        T(d, (680, 140), "KC", 'eb', 70, (40, 40, 40, 255), "ms")
        for i in range(48):
            x = 560 + i * 4.6
            d.rectangle([x, 300, x + (i * 7 % 3 + 1), 400], fill=(30, 30, 30, 255))
        T(d, (680, 436), "R-R-CRW-KS2150F", 'm', 22, (40, 40, 40, 255), "ms")
        im.save(os.path.join(src, "src_rating.png"))

    def smudge():
        # 손 닿는 금속면용 회색조 마스크 (지문/문지름/흠집), 박스 투영으로 반복
        W = 2048
        rng = random.Random(21)
        im = Image.new("RGBA", (W, W), (0, 0, 0, 255))
        L = Image.new("L", (W, W), 0)
        d = ImageDraw.Draw(L)
        for _ in range(60):
            x, y = rng.uniform(0, W), rng.uniform(0, W)
            ln, ang = rng.uniform(60, 260), rng.uniform(0, 6.28)
            d.line([(x, y), (x + math.cos(ang) * ln, y + math.sin(ang) * ln)], fill=int(rng.uniform(40, 90)), width=int(rng.uniform(16, 40)))
        L = L.filter(ImageFilter.GaussianBlur(14))
        P = Image.new("L", (W, W), 0)
        pd = ImageDraw.Draw(P)
        for _ in range(110):
            cx, cy, R, rot = rng.uniform(0, W), rng.uniform(0, W), rng.uniform(14, 26), rng.uniform(0, 3)
            for k in np.arange(3, R, 2.6):
                pts = [(cx + math.cos(t) * k * math.cos(rot) - (math.sin(t) * k * 1.35) * math.sin(rot),
                        cy + math.cos(t) * k * math.sin(rot) + (math.sin(t) * k * 1.35) * math.cos(rot)) for t in np.linspace(.3, 5.9, 24)]
                pd.line(pts, fill=int(rng.uniform(90, 160)), width=2)
        P = P.filter(ImageFilter.GaussianBlur(0.8))
        S2 = Image.new("L", (W, W), 0)
        sd = ImageDraw.Draw(S2)
        for _ in range(500):
            x, y = rng.uniform(0, W), rng.uniform(0, W)
            sd.line([(x, y), (x + rng.uniform(-120, 120), y + rng.uniform(-25, 25))], fill=int(rng.uniform(80, 200)), width=1)
        R = ImageChops.lighter(ImageChops.lighter(L, P), Image.new("L", (W, W), 0))
        rgb = Image.merge("RGB", (R, S2, Image.new("L", (W, W), 0)))  # R: 얼룩/지문, G: 흠집
        rgb.save(os.path.join(src, "src_smudge.png"))

    # ================= Kiosk_B 화면: 점검/오류 (동적, 가운데는 '점검 중' 종이에 가려짐) =================
    def screen_off():
        W, H = SCR_W, SCR_H
        im = grad(W, H, "#14233a", "#070c16")
        d = ImageDraw.Draw(im)
        logo(im, W / 2, 190, 0.9, alpha=70)
        d.ellipse([W / 2 - 46, 330, W / 2 + 46, 422], outline=(255, 196, 64, 255), width=8)
        T(d, (W / 2, 400), "!", 'eb', 72, (255, 196, 64, 255), "ms")
        T(d, (W / 2, 520), "시스템 점검 중", 'eb', 82, (236, 240, 246, 255), "ms")
        T(d, (W / 2, 584), "SYSTEM MAINTENANCE", 'b', 40, (150, 170, 196, 255), "ms")
        T(d, (W / 2, 660), "오류 코드 E-1042 : 결제 모듈 응답 없음", 'sb', 34, (255, 150, 130, 255), "ms")
        T(d, (W / 2, 1560), "잠시 후 다시 이용해 주세요", 'b', 50, (220, 228, 238, 255), "ms")
        T(d, (W / 2, 1626), "다른 키오스크 또는 카운터를 이용해 주시기 바랍니다", 'm', 32, (150, 166, 190, 255), "ms")
        for i in range(12):  # 멈춘 로딩 원
            a = i / 12 * 6.2832
            r = 7 + (i % 12) * 0.6
            x, y = W / 2 + math.cos(a) * 42, 1740 + math.sin(a) * 42
            d.ellipse([x - r, y - r, x + r, y + r], fill=(200, 210, 225, 40 + i * 16))
        T(d, (W / 2, 1880), "KS-2150F  v3.2.1  2026-11-05 09:12:44  재시작 대기 중...", 'm', 22, (96, 110, 132, 255), "ms")
        a = np.asarray(im).astype(np.float32)
        a[..., :3] *= 0.62  # 백라이트 절반 (흐린 화면)
        Image.fromarray(a.astype(np.uint8), "RGBA").convert("RGB").save(os.path.join(out, "T_Kiosk_Screen_Off.png"), optimize=True)

    # ================= 영수증 (KioskReceipt, 동적) 80 x 250 mm, 8 px/mm =================
    def receipt():
        W, H = 640, 2000
        rng = random.Random(4)
        im = Image.new("RGBA", (W, H), (246, 244, 237, 255))
        d = ImageDraw.Draw(im)
        INK = (43, 38, 34, 255)
        y = [24]

        def line(s, size=24, k='m', anchor="ms", x=W / 2, dy=None):
            y[0] += int(size * 0.8)  # 글자 높이만큼 먼저 내리고 기준선에 쓴다
            T(d, (x, y[0]), s, k, size, INK, anchor)
            y[0] += int(size * 0.55) if dy is None else dy

        def row(a, b, size=24, k='m'):
            y[0] += int(size * 0.8)
            T(d, (36, y[0]), a, k, size, INK, "ls")
            T(d, (W - 36, y[0]), b, k, size, INK, "rs")
            y[0] += int(size * 0.65)

        def dash():
            y[0] += 14
            for x in range(36, W - 36, 14):
                d.line([(x, y[0]), (x + 7, y[0])], fill=INK, width=2)
            y[0] += 18

        line("버거대왕", 72, 'eb', dy=26)
        line("시장입구점", 32, 'b', dy=24)
        line("사업자 214-86-13579   대표 왕대길", 19)
        line("서울 중구 시장길 27, 1층   TEL 02-2265-0274", 19)
        line("2026-11-05 (목) 11:42:07    키오스크 01", 21, dy=16)
        dash()
        line("주문번호", 42, 'b', dy=24)
        line("274", 190, 'eb', dy=30)
        line("[ 매장 식사 ]", 30, 'b', dy=24)
        dash()
        row("메뉴", "수량      금액", 22, 'b')
        dash()
        row("K-BBQ 스모키 비프 세트", "1    7,800", 25, 'b')
        row("  └ 프렌치 프라이 R", "", 22)
        row("  └ 제로 콜라", "", 22)
        dash()
        row("합계 금액", "7,800", 30, 'eb')
        row("(과세 물품 7,091  부가세 709)", "", 19)
        dash()
        line("신용카드 승인", 36, 'eb', dy=26)
        for a, b in (("카드 종류", "시장은행"), ("카드 번호", "5412-75**-****-2841"), ("할부", "일시불"),
                     ("승인 번호", "30129874"), ("승인 일시", "2026-11-05 11:42:31"), ("결제 금액", "7,800원")):
            row(a, b, 22)
        dash()
        line("번호가 불리면 카운터로 오세요", 30, 'b', dy=40)
        x = 70  # 바코드
        while x < W - 70:
            bw = rng.choice((2, 2, 3, 5))
            d.rectangle([x, y[0], x + bw, y[0] + 110], fill=INK)
            x += bw + rng.choice((2, 3, 4))
        y[0] += 116
        line("274-20261105-0142", 20, dy=40)
        line("이용해 주셔서 감사합니다", 28, 'b', dy=30)
        line("* 교환·환불은 영수증 지참 시 7일 이내 가능", 18)
        line("* 감열지 영수증은 시간이 지나면 글자가 흐려집니다", 18)
        # 감열 인쇄 농도 얼룩 + 종이 결
        a = np.asarray(im).astype(np.float32)
        ink = (a[..., 0] < 200).astype(np.float32)
        fade = np.asarray(Image.effect_noise((W, H), 50).filter(ImageFilter.GaussianBlur(18))).astype(np.float32) / 255
        a[..., :3] += (ink * (fade - 0.35) * 70)[..., None]
        n = np.asarray(Image.effect_noise((W, H), 18).filter(ImageFilter.GaussianBlur(0.6))).astype(np.float32) - 128
        a[..., :3] += n[..., None] * 0.06
        Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").convert("RGB").save(
            os.path.join(root, "Assets", "Art3D", "Textures", "KioskReceipt", "T_KioskReceipt_Paper.png"), optimize=True)

    os.makedirs(os.path.join(root, "Assets", "Art3D", "Textures", "KioskReceipt"), exist_ok=True)
    jobs = dict(attract=attract, menu=menu, panel=panel, lcd=lcd, header=header_sign, glass=glass, atlas=atlas,
                terminal=terminal_print, decals=small_decals, smudge=smudge, screen_off=screen_off, receipt=receipt)
    for k in (only or jobs):
        jobs[k]()
    print("kiosk_tex: done ->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])  # 뒤에 이름을 주면 그 텍스처만 (예: receipt screen_off)
