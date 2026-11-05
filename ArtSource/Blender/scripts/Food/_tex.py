# 음식/포장 2D 인쇄 텍스처 (Pillow). venv 파이썬으로 실행: _cache/venv/bin/python _tex.py
# 결과: $K3D_CACHE/food_tex/*.png  (Blender 스크립트가 머티리얼 입력으로 씀)
import os, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CACHE = os.environ.get("K3D_CACHE") or "/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/_cache"
OUT = os.path.join(CACHE, "food_tex")
os.makedirs(OUT, exist_ok=True)
PH = os.path.join(CACHE, "ph_index")
FN = {
    "black": os.path.join(PH, "Pretendard-Black.otf"),
    "xbold": os.path.join(PH, "Pretendard-ExtraBold.otf"),
    "bold": os.path.join(PH, "Pretendard-Bold.otf"),
    "med": os.path.join(PH, "Pretendard-Medium.otf"),
    "reg": os.path.join(PH, "Pretendard-Regular.otf"),
    "han": os.path.join(CACHE, "fonts", "BlackHanSans-Regular.ttf"),
    "dohyeon": os.path.join(CACHE, "fonts", "DoHyeon-Regular.ttf"),
    "pen": os.path.join(CACHE, "fonts", "NanumPenScript-Regular.ttf"),
}
RED, CREAM, BROWN, GOLD = "#b5271c", "#f1e4c8", "#4a2c18", "#e2a72e"


def font(k, size):
    return ImageFont.truetype(FN[k], int(size))


def text(d, xy, s, k, size, fill, anchor="mm", **kw):
    d.text(xy, s, font=font(k, size), fill=fill, anchor=anchor, **kw)


def logo(scale, dark=False, show_text=True, tc=None, bun="#d98a2b", patty="#6b3a1e", crown="#f0c63a"):
    """프로토타입 Rn(): 왕관 얹은 버거 + '버거대왕'. 4배 그려서 줄여 안티앨리어싱."""
    S = scale * 4
    W, H = int(230 * S), int(200 * S)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = W / 2, 95 * S
    P = lambda x, y: (ox + x * S, oy + y * S)
    d.pieslice([P(-62, -52), P(62, 36)], 180, 360, fill=bun)
    d.rectangle([P(-60, -6), P(60, 10)], fill=patty)
    d.rounded_rectangle([P(-58, 12), P(58, 34)], radius=8 * S, fill=bun)
    d.polygon([P(-30, -48), P(-34, -82), P(-14, -62), P(0, -90), P(14, -62), P(34, -82), P(30, -48)], fill=crown)
    if show_text:
        c = tc or ("#3a2416" if dark else "#c8291f")
        d.text(P(0, 72), "버거대왕", font=font("black", 50 * S), fill=c, anchor="mm")
    return im.resize((W // 4, H // 4), Image.LANCZOS)


def paper_noise(w, h, base, amt=10, seed=1, fibers=True):
    rng = np.random.default_rng(seed)
    b = np.array(Image.new("RGB", (1, 1), base))[0, 0].astype(np.float32)
    n = rng.normal(0, 1, (h // 4 + 1, w // 4 + 1)).astype(np.float32)
    n = np.array(Image.fromarray(((n * 40) + 128).clip(0, 255).astype(np.uint8)).resize((w, h), Image.BICUBIC),
                 np.float32) / 128 - 1
    f = rng.normal(0, 1, (h, w)).astype(np.float32) * 0.35
    a = b[None, None, :] + (n[..., None] * amt + f[..., None] * amt * 0.6)
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8), "RGB")
    if fibers:
        d = ImageDraw.Draw(im, "RGBA")
        r = random.Random(seed)
        for _ in range(int(w * h / 900)):
            x, y = r.random() * w, r.random() * h
            L, ang = r.uniform(3, 14), r.uniform(0, math.pi)
            c = r.choice([(0, 0, 0, 14), (255, 255, 255, 18)])
            d.line([(x, y), (x + L * math.cos(ang), y + L * math.sin(ang))], fill=c, width=1)
    return im


def paste(dst, src, cx, cy):
    dst.alpha_composite(src, (int(cx - src.width / 2), int(cy - src.height / 2))) if dst.mode == "RGBA" else \
        dst.paste(src, (int(cx - src.width / 2), int(cy - src.height / 2)), src)


def tint(src, color):
    """RGBA 이미지를 단색으로 (알파 유지)."""
    c = Image.new("RGBA", src.size, color)
    c.putalpha(src.getchannel("A"))
    return c


def grease(im, n, seed, size=(20, 90), col=(150, 100, 30)):
    r = random.Random(seed)
    w, h = im.size
    layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for _ in range(n):
        x, y, s = r.random() * w, r.random() * h, r.uniform(*size)
        for k in range(5):
            dx, dy, ss = r.uniform(-s, s) * .4, r.uniform(-s, s) * .4, s * r.uniform(.4, .9)
            d.ellipse([x + dx - ss, y + dy - ss * r.uniform(.6, 1), x + dx + ss, y + dy + ss], fill=(*col, r.randint(18, 38)))
    layer = layer.filter(ImageFilter.GaussianBlur(6))
    base = im.convert("RGBA")
    base.alpha_composite(layer)
    return base.convert(im.mode)


def crumbs(im, n, seed, area=None):
    r = random.Random(seed)
    d = ImageDraw.Draw(im, "RGBA")
    w, h = im.size
    x0, y0, x1, y1 = area or (0, 0, w, h)
    for _ in range(n):
        x, y, s = r.uniform(x0, x1), r.uniform(y0, y1), r.uniform(1.5, 5)
        c = r.choice([(196, 140, 70, 230), (150, 95, 45, 230), (232, 200, 130, 220), (240, 230, 200, 200)])
        d.ellipse([x - s, y - s * .7, x + s, y + s * .8], fill=c)


def burger_art(n):
    """프로토타입 na()+s0.bulgogi 를 따라 그린 불고기 버거 일러스트 (RGBA, 폭 n)."""
    S = 3
    N = n * S
    W, H = int(N * 1.2), int(N * 0.95)
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    e, t = W / 2, H * 0.86
    r = random.Random(7)
    d.ellipse([e - N * .62, t - N * .03, e + N * .62, t + N * .1], fill=(60, 30, 10, 70))
    s = N * .15  # 아래 빵
    d.rounded_rectangle([e - N / 2, t - s, e + N / 2, t], radius=s * .5, fill="#d8923f")
    d.rectangle([e - N * .46, t - s, e + N * .46, t - s * .84], fill="#e9b265")
    t -= s
    rr = N * .125  # 불고기 패티 (글레이즈)
    pts = [(e - N * .5, t - rr * .3)] + [(e - N * .5 + N * c / 18, t - rr + math.sin(c / 18 * 19) * rr * .09) for c in range(19)] + \
          [(e + N * .5, t - rr * .3), (e + N * .47, t), (e - N * .47, t)]
    d.polygon(pts, fill="#4a2414")
    for _ in range(90):
        x, y = e + r.uniform(-.47, .47) * N, t - r.uniform(0, 1) * rr
        q = r.uniform(1, N * .012)
        d.ellipse([x - q, y - q, x + q, y + q], fill=r.choice(["#2a140a", "#7c4a2a", "#1f0e07"]))
    for _ in range(9):
        x, y, q = e + r.uniform(-.42, .42) * N, t - rr * r.uniform(.5, .9), N * r.uniform(.02, .05)
        d.ellipse([x - q, y - N * .006, x + q, y + N * .006], fill="#c89a6a")
    for _ in range(6):
        x = e + r.uniform(-.4, .4) * N
        d.rounded_rectangle([x, t - rr * .2, x + N * .022, t + rr * r.uniform(.4, .9)], radius=N * .01, fill="#3a1608")
    t -= rr * .92
    pts = [(e - N * .54, t)] + [(e - N * .54 + N * 1.08 * k / 26, t + math.sin(k / 26 * 34) * N * .022 + (N * .016 if k % 2 else -N * .016)) for k in range(27)] + \
          [(e + N * .5, t - N * .05), (e - N * .5, t - N * .05)]
    d.polygon(pts, fill="#7fb53a")
    t -= N * .04
    for sx in (-.28, .02, .3):
        d.ellipse([e + sx * N - N * .13, t - N * .034, e + sx * N + N * .13, t + N * .01], outline="#f5ebf5", width=int(N * .016))
    t -= N * .02
    rt = N * .38  # 위 빵
    top = [(e + N * .51 * math.cos(a), t - rt * 1.0 * math.sin(a) ** 0.8) for a in np.linspace(0, math.pi, 40)]
    d.polygon(top + [(e - N * .51, t + N * .02), (e + N * .51, t + N * .02)], fill="#d38a3c")
    d.ellipse([e - N * .35, t - rt * .82, e + N * .05, t - rt * .5], fill="#e6ac5c")
    for _ in range(46):
        a = r.uniform(.25, math.pi - .25)
        x, y = e + N * .46 * math.cos(a) * r.uniform(.2, 1), t - rt * .95 * math.sin(a) * r.uniform(.55, .98)
        d.ellipse([x - N * .0125, y - N * .0065, x + N * .0125, y + N * .0065], fill="#f6e8c6")
    return im.resize((W // S, H // S), Image.LANCZOS)


def qr(n, px, seed=3):
    r = random.Random(seed)
    m = [[r.random() < .5 for _ in range(n)] for _ in range(n)]
    for (a, b) in ((0, 0), (0, n - 7), (n - 7, 0)):
        for i in range(7):
            for j in range(7):
                m[a + i][b + j] = i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4)
    im = Image.new("RGB", (n * px + 4 * px, n * px + 4 * px), "white")
    d = ImageDraw.Draw(im)
    for i in range(n):
        for j in range(n):
            if m[i][j]:
                d.rectangle([(j + 2) * px, (i + 2) * px, (j + 3) * px - 1, (i + 3) * px - 1], fill="#1a1410")
    return im


# ---------------------------------------------------------------- 컵 (원통 전개, u=0.5 가 정면)
def cup(kind):
    W, H = 2400, 1440
    band, name, en = (RED, "콜라", "COLA") if kind == "cola" else ("#2f7d4f", "사이다", "CIDER")
    im = paper_noise(W, H, "#f4ead6", 6, seed=11).convert("RGBA")
    d = ImageDraw.Draw(im)
    y0, y1 = int(H * .20), int(H * .74)
    d.rectangle([0, y0, W, y1], fill=band)
    d.rectangle([0, y0 - 26, W, y0 - 16], fill=band)
    d.rectangle([0, y1 + 16, W, y1 + 26], fill=band)
    # 정면: 로고 (크림색 글씨)
    paste(im, logo(3.1, tc="#fbf1dc"), W * .5, (y0 + y1) / 2 - 4)
    # 양옆: 음료 이름 (프로토타입 x0 처럼 두 번)
    for cx in (W * .18, W * .82):
        text(d, (cx, (y0 + y1) / 2 - 60), name, "black", 230, "#fffaf0")
        text(d, (cx, (y0 + y1) / 2 + 120), en, "xbold", 74, "#fffaf0")
    # 뒤(이음매 근처) 작은 글씨
    text(d, (W * .04, H * .5), "", "reg", 20, "#000")
    small = ["재질: 종이(PE 코팅)  ·  용량 16oz(473ml)", "제조: (주)왕컵산업  ·  1회용 종이컵", "뜨거운 음료에 사용하지 마세요"]
    for i, s in enumerate(small):
        text(d, (W * 0.0 + 230, y0 + 70 + i * 46), s, "med", 30, "#fbf1dc", anchor="lm")
        text(d, (W - 230, y0 + 70 + i * 46), s, "med", 30, "#fbf1dc", anchor="rm")
    # 위/아래 띠 글씨
    for i in range(3):
        text(d, (W * (i + .5) / 3, H * .125), "BURGER DAEWANG  ·  SINCE 1998", "bold", 36, band)
        text(d, (W * (i + .5) / 3 + W / 6, H * .80), "왕의 맛 그대로  ·  버거대왕", "bold", 38, band)
    # 분리배출 마크 (뒤쪽 이음매 옆)
    cx, cy = W * .07, H * .90
    d.ellipse([cx - 44, cy - 44, cx + 44, cy + 44], outline=band, width=6)
    text(d, (cx, cy - 8), "종이컵", "xbold", 24, band)
    text(d, (cx, cy + 18), "분리배출", "med", 18, band)
    # 주문 스티커 (정면 왼쪽 아래, 비스듬히)
    st = Image.new("RGBA", (360, 170), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle([4, 4, 356, 166], 14, fill=(252, 251, 246, 255), outline=(200, 196, 186, 255), width=2)
    text(sd, (180, 40), "주문 274", "bold", 34, "#222")
    text(sd, (180, 102), f"{name}(M)", "black", 62, "#111")
    text(sd, (180, 148), "얼음 보통 · 11:42", "med", 22, "#444")
    st = st.rotate(-4, expand=True, resample=Image.BICUBIC)
    sh = tint(st, (0, 0, 0, 60)).filter(ImageFilter.GaussianBlur(5))
    paste(im, sh, W * .5 + 4, H * .895 + 5)
    paste(im, st, W * .5, H * .895)
    im.convert("RGB").save(os.path.join(OUT, f"cup_{kind}.png"))


LID_S, LID_BTN = 0.06, (("콜라", -126), ("사이다", -90), ("기타", -54))  # 뚜껑 윗면 6cm = 1024px, 음료 표시 버튼 (이름, 각도)


def lid(kind):
    """뚜껑 음료 표시 버튼 테두리 + 이름 (투명 배경, 위에서 본 평면 투영). 주문한 음료 버튼은 눌린 자국."""
    N = 1024
    im = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    P = lambda x, y: ((x / LID_S + .5) * N, (.5 - y / LID_S) * N)
    r = .0042 / LID_S * N
    for nm, deg in LID_BTN:
        a = math.radians(deg)
        cx, cy = P(.0195 * math.cos(a), .0195 * math.sin(a))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(120, 128, 126, 190), width=4)
        if nm == ("콜라" if kind == "cola" else "사이다"):
            d.ellipse([cx - r * .82, cy - r * .82, cx + r * .82, cy + r * .82], outline=(90, 96, 94, 150), width=6)
        text(d, P(.0263 * math.cos(a), .0263 * math.sin(a)), nm, "bold", 40, (105, 112, 110, 215))
    im.save(os.path.join(OUT, f"lid_{kind}.png"))


# ---------------------------------------------------------------- 감자튀김 상자 (앞/뒤)
def fries():
    W, H = 1000, 1150
    for side in ("front", "back"):
        im = paper_noise(W, H, RED, 7, seed=21 if side == "front" else 22).convert("RGBA")
        d = ImageDraw.Draw(im)
        g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        for x in range(W):  # 가장자리 어둡게
            a = int(40 * abs(x / W - .5) * 2)
            gd.line([(x, 0), (x, H)], fill=(60, 0, 0, a))
        im.alpha_composite(g)
        d.rectangle([0, H - 70, W, H - 58], fill=GOLD)
        if side == "front":
            paste(im, logo(2.9, tc="#fbf1dc"), W / 2, H * .53)
            text(d, (W / 2, H * .80), "프렌치 프라이", "black", 92, "#fbf1dc")
            text(d, (W / 2, H * .87), "FRENCH FRIES", "xbold", 40, GOLD)
        else:
            text(d, (W / 2, H * .45), "사이드는", "han", 110, "#fbf1dc")
            text(d, (W / 2, H * .56), "왕의 친구", "han", 130, GOLD)
            for i, s in enumerate(["프렌치 프라이 R · 320kcal", "원산지: 감자(미국산) · 식용유(대두)", "갓 튀겨 바삭할 때 드세요"]):
                text(d, (W / 2, H * .70 + i * 40), s, "med", 30, "#fbf1dc")
        im.convert("RGB").save(os.path.join(OUT, f"fries_{side}.png"))


# ---------------------------------------------------------------- 포장지 패턴 (타일) + 체크 패널
def wrapper():
    W = 1024
    im = paper_noise(W, W, "#f5ecd8", 5, seed=31).convert("RGBA")
    mark = tint(logo(.95, show_text=False), RED)
    word = Image.new("RGBA", (300, 70), (0, 0, 0, 0))
    text(ImageDraw.Draw(word), (150, 35), "버거대왕", "black", 52, RED)
    cells = 4
    for i in range(cells):
        for j in range(cells):
            item = mark if (i + j) % 2 == 0 else word
            x = (j + .5 + (.5 if i % 2 else 0)) * W / cells
            y = (i + .5) * W / cells
            it = item.rotate(-18, expand=True, resample=Image.BICUBIC)
            for dx in (-W, 0, W):
                for dy in (-W, 0, W):
                    paste(im, it, x + dx, y + dy)
    im.convert("RGB").save(os.path.join(OUT, "wrap_pattern.png"))
    # 윗면 체크 패널 (직원이 '불고기'에 체크)
    P = Image.new("RGBA", (900, 520), (0, 0, 0, 0))
    d = ImageDraw.Draw(P)
    d.rounded_rectangle([6, 6, 894, 514], 30, fill=(246, 238, 220, 255), outline=RED, width=10)
    text(d, (450, 70), "버거대왕", "black", 64, RED)
    items = ["불고기", "치즈", "치킨", "새우", "더블", "기타"]
    for k, s in enumerate(items):
        cx, cy = 150 + (k % 3) * 280, 210 + (k // 3) * 140
        d.rectangle([cx - 90, cy - 30, cx - 34, cy + 26], outline=BROWN, width=7)
        text(d, (cx - 18, cy), s, "black", 54, BROWN, anchor="lm")
    pen = [(65, 190), (82, 214), (95, 233), (128, 168), (152, 140)]
    d.line(pen, fill="#1d2a8a", width=14, joint="curve")
    text(d, (450, 470), "K-BBQ 스모키 비프", "bold", 34, BROWN)
    P.save(os.path.join(OUT, "wrap_panel.png"))


# ---------------------------------------------------------------- 쟁반 깔지 (가로 0.40 x 세로 0.29)
def liner():
    W, H = 2048, 1484
    im = paper_noise(W, H, "#f1e4c8", 6, seed=41).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle([28, 28, W - 28, H - 28], outline=RED, width=14)
    d.rectangle([52, 52, W - 52, H - 52], outline=RED, width=3)
    # 왼쪽 헤드라인 + 버거
    text(d, (110, 150), "왕의 맛, 그대로.", "han", 150, RED, anchor="lm")
    text(d, (116, 270), "K-BBQ 스모키 비프", "black", 76, BROWN, anchor="lm")
    text(d, (118, 345), "달콤한 간장 불고기 소스 · 아삭한 양상추 · 생양파", "med", 38, BROWN, anchor="lm")
    paste(im, burger_art(760), 520, 860)
    d.ellipse([820, 470, 1010, 660], fill=GOLD)
    text(d, (915, 540), "세트", "black", 54, "#fff")
    text(d, (915, 600), "7,900원", "xbold", 38, "#fff")
    # 오른쪽 앱 주문 홍보
    x0, y0 = 1180, 150
    d.rounded_rectangle([x0, y0, W - 110, y0 + 560], 36, fill=RED)
    text(d, (x0 + 50, y0 + 80), "APP ORDER", "black", 70, "#fbf1dc", anchor="lm")
    text(d, (x0 + 50, y0 + 170), "앱으로 주문하면", "bold", 50, "#fbf1dc", anchor="lm")
    text(d, (x0 + 50, y0 + 235), "기다림 없이 픽업!", "bold", 50, GOLD, anchor="lm")
    text(d, (x0 + 50, y0 + 320), "첫 주문 10% 할인 쿠폰", "med", 36, "#fbf1dc", anchor="lm")
    q = qr(25, 9)
    paste(im, q.convert("RGBA"), W - 110 - 150, y0 + 400)
    text(d, (x0 + 50, y0 + 470), "QR 찍고 바로 설치", "med", 32, "#fbf1dc", anchor="lm")
    # 매장 안내 (현실 비판 포인트)
    y = 790
    d.rounded_rectangle([x0, y, W - 110, y + 300], 24, outline=BROWN, width=5)
    text(d, (x0 + 40, y + 60), "매장 이용 안내", "black", 52, BROWN, anchor="lm")
    for i, s in enumerate(["· 주문은 키오스크에서만 가능합니다", "· 카드 결제 전용 매장입니다 (현금 불가)", "· 주문번호가 화면에 뜨면 픽업대로 오세요",
                           "· 다 드신 쟁반은 반납대에 놓아 주세요"]):
        text(d, (x0 + 40, y + 125 + i * 44), s, "med", 33, BROWN, anchor="lm")
    paste(im, logo(1.45), W - 290, H - 260)
    text(d, (110, H - 140), "원산지: 쇠고기(호주산), 돼지고기(국내산), 양상추(국내산), 감자(미국산)", "reg", 26, BROWN, anchor="lm")
    text(d, (110, H - 100), "알레르기: 밀, 대두, 우유, 계란, 쇠고기, 토마토  ·  고객센터 1588-0000", "reg", 26, BROWN, anchor="lm")
    im = grease(im, 9, 5, (25, 80))
    crumbs(im, 70, 9)
    im.convert("RGB").save(os.path.join(OUT, "tray_liner.png"))


# ---------------------------------------------------------------- 종이백 (앞/옆 잉크, 알파)
def bag():
    W, H = 1040, 1200
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    paste(im, logo(2.6, dark=True, tc="#3a2416"), W / 2, H * .36)
    text(d, (W / 2, H * .66), "BURGER DAEWANG", "black", 58, "#3a2416")
    d.line([(W * .3, H * .71), (W * .7, H * .71)], fill="#3a2416", width=4)
    text(d, (W / 2, H * .76), "맛있게 드세요", "bold", 46, "#3a2416")
    text(d, (W / 2, H * .92), "뜨거운 음식이 들어 있습니다. 바닥을 받쳐 들어 주세요.", "med", 26, "#3a2416")
    im.save(os.path.join(OUT, "bag_front.png"))
    S = Image.new("RGBA", (600, 1200), (0, 0, 0, 0))
    d = ImageDraw.Draw(S)
    cx, cy = 300, 700
    tri = [(cx + 95 * math.cos(math.radians(90 + k * 120)), cy - 95 * math.sin(math.radians(90 + k * 120))) for k in range(3)]
    for k in range(3):  # 분리배출 삼각 화살표
        a, b = tri[k], tri[(k + 1) % 3]
        m = (a[0] + (b[0] - a[0]) * .78, a[1] + (b[1] - a[1]) * .78)
        d.line([(a[0] + (b[0] - a[0]) * .12, a[1] + (b[1] - a[1]) * .12), m], fill="#3a2416", width=13)
        ux, uy = (b[0] - a[0]) / 190, (b[1] - a[1]) / 190
        d.polygon([(m[0] + ux * 30, m[1] + uy * 30), (m[0] - uy * 20, m[1] + ux * 20), (m[0] + uy * 20, m[1] - ux * 20)], fill="#3a2416")
    text(d, (cx, cy + 14), "종이", "black", 40, "#3a2416")
    text(d, (cx, cy + 150), "분리배출", "black", 52, "#3a2416")
    text(d, (cx, cy + 200), "재활용 가능한 종이백입니다", "med", 30, "#3a2416")
    text(d, (cx, 260), "버거대왕", "black", 72, "#3a2416")
    S.save(os.path.join(OUT, "bag_side.png"))


# ---------------------------------------------------------------- 진동벨 번호 스티커 (M_Dyn 기본값) + 윗면 인쇄
def arc_text(im, s, k, size, fill, cx, cy, r, center_deg, bottom=True):
    """원호를 따라 글자를 한 자씩 회전해 찍는다 (bottom=True: 아래 호, 바깥에서 읽힘)."""
    f = font(k, size)
    ws = [f.getlength(ch) for ch in s]
    span = math.degrees(sum(ws) / r)
    a = center_deg + (-span / 2 if bottom else span / 2)  # 왼쪽 끝에서 시작
    for ch, w in zip(s, ws):
        da = math.degrees(w / r)
        mid = a + da / 2 if bottom else a - da / 2
        if ch.strip():
            g = Image.new("RGBA", (int(size * 1.6), int(size * 1.6)), (0, 0, 0, 0))
            ImageDraw.Draw(g).text((g.width / 2, g.height / 2), ch, font=f, fill=fill, anchor="mm")
            g = g.rotate((mid - 270) if bottom else (mid - 90), resample=Image.BICUBIC)
            paste(im, g, cx + r * math.cos(math.radians(mid)), cy - r * math.sin(math.radians(mid)))
        a = a + da if bottom else a - da


def pager():
    """진동벨 (지름 0.096m 윗면 = 1024px). 가운데 번호 스티커(M_Dyn 기본값) + 윗면 인쇄(로고, 원호 글씨)."""
    N = 1024
    im = Image.new("RGBA", (N, N), (250, 248, 242, 255))
    d = ImageDraw.Draw(im)
    d.ellipse([18, 18, N - 18, N - 18], outline=RED, width=26)
    d.ellipse([70, 70, N - 70, N - 70], outline=(200, 190, 175, 255), width=4)
    paste(im, logo(1.6), N / 2, 230)
    text(d, (N / 2, 560), "274", "black", 380, "#1d140e")
    text(d, (N / 2, 790), "진동벨 번호", "bold", 62, "#4a2c18")
    text(d, (N / 2, 870), "울리면 픽업대로 와주세요", "med", 44, "#4a2c18")
    im.convert("RGB").save(os.path.join(OUT, "pager_sticker.png"))
    P = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    ink = (238, 230, 216, 255)
    lg = tint(logo(.78, show_text=False), ink)
    paste(P, lg, N / 2, 150)  # 스티커(반지름 272px) 와 윗면 가장자리(반지름 469px) 사이
    arc_text(P, "사용 후 반납해 주세요 · RETURN PLEASE", "bold", 33, ink, N / 2, N / 2, 372, 270, bottom=True)
    arc_text(P, "버거대왕", "black", 40, ink, N / 2, N / 2, 368, 145, bottom=False)
    arc_text(P, "진동벨", "black", 40, ink, N / 2, N / 2, 368, 35, bottom=False)
    P.save(os.path.join(OUT, "pager_print.png"))


if __name__ == "__main__":
    cup("cola"); cup("cider"); lid("cola"); lid("cider"); fries(); wrapper(); liner(); bag(); pager()
    print("food_tex ok", OUT)
