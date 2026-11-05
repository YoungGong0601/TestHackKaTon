# 가게 외관(Storefront) 그룹 2D 텍스처 (포스터·스티커·간판·유리 얼룩). venv Python(Pillow) 으로 실행.
#   python tex.py [door|facade|ac|all]
# 출력: $K3D_ROOT/Assets/Art3D/Textures/<Asset>/T_<Asset>_<Name>.png|jpg
import os, sys, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

ROOT = os.environ.get("K3D_ROOT") or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
TEX = os.path.join(ROOT, "Assets", "Art3D", "Textures")
REF = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")), "_ref", "img") + os.sep
FC = os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")), "_cache", "fonts") + os.sep
UF = os.path.expanduser("~/Library/Fonts/")
F = {"han": FC + "BlackHanSans-Regular.ttf", "pen": FC + "NanumPenScript-Regular.ttf", "do": FC + "DoHyeon-Regular.ttf",
     "black": UF + "Pretendard-Black.otf", "xb": UF + "Pretendard-ExtraBold.otf", "bold": UF + "Pretendard-Bold.otf",
     "med": UF + "Pretendard-Medium.otf", "reg": UF + "Pretendard-Regular.otf"}
RED, CREAM, BROWN, MUSTARD = "#b5271c", "#f1e4c8", "#4a2c18", "#e2a72e"


def font(k, s):
    return ImageFont.truetype(F[k], int(s))


def save(im, asset, name, jpg=False):
    d = os.path.join(TEX, asset)
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f"T_{asset}_{name}." + ("jpg" if jpg else "png"))
    (im.convert("RGB").save(p, quality=92) if jpg else im.save(p, optimize=True))
    print("tex:", p, im.size)
    return p


def text(d, xy, s, f, fill, anchor="mm", spacing=0, **kw):
    """가운데 정렬 텍스트 (spacing=자간 px)."""
    if not spacing:
        d.text(xy, s, font=f, fill=fill, anchor=anchor, **kw)
        return
    w = sum(f.getlength(c) for c in s) + spacing * (len(s) - 1)
    x = xy[0] - w / 2 if anchor[0] == "m" else xy[0]
    for c in s:
        d.text((x, xy[1]), c, font=f, fill=fill, anchor="l" + anchor[1], **kw)
        x += f.getlength(c) + spacing


def fit(s, k, w, h):
    """w×h 상자에 맞는 최대 글꼴."""
    size = h
    while size > 6:
        f = font(k, size)
        b = f.getbbox(s)
        if b[2] - b[0] <= w and b[3] - b[1] <= h:
            return f
        size *= 0.94
    return font(k, 6)


def logo(d, cx, cy, sc, wordmark=True, dark=False):
    """프로토타입 Rn(): 왕관 + 버거(윗빵·패티·아랫빵) + 아래 '버거대왕' 워드마크. 버거킹 로고와 다른 패러디."""
    P = lambda x, y: (cx + x * sc, cy + y * sc)
    d.pieslice([P(-62, -52), P(62, 36)], 180, 360, fill="#d98a2b")
    d.rectangle([P(-60, -6), P(60, 10)], fill="#6b3a1e")
    d.rounded_rectangle([P(-58, 12), P(58, 34)], radius=8 * sc, fill="#d98a2b")
    d.polygon([P(-30, -48), P(-34, -82), P(-14, -62), P(0, -90), P(14, -62), P(34, -82), P(30, -48)], fill="#f0c63a")
    for x, y in ((-34, -82), (0, -90), (34, -82)):
        d.ellipse([P(x - 4, y - 4), P(x + 4, y + 4)], fill="#f0c63a")
    for i in range(7):  # 참깨
        x, y = -40 + i * 13, -30 + (i % 2) * 9
        d.ellipse([P(x - 3, y - 1.6), P(x + 3, y + 1.6)], fill="#f3dfb0")
    if wordmark:
        d.text(P(0, 72), "버거대왕", font=font("han", 50 * sc), fill="#3a2416" if dark else "#c8291f", anchor="mm")


def grain(im, amt=10, seed=0):
    """인쇄물 미세 노이즈."""
    rng = np.random.default_rng(seed)
    a = np.asarray(im).astype(np.int16)
    n = rng.normal(0, amt, a.shape[:2])[..., None]
    a[..., :3] = np.clip(a[..., :3] + n, 0, 255)
    return Image.fromarray(a.astype(np.uint8), im.mode)


def fade(im, k=0.12, tint=(250, 244, 225)):
    """햇빛 바램: 채도/대비를 조금 낮추고 누렇게."""
    base = Image.new(im.mode, im.size, tint + ((255,) if im.mode == "RGBA" else ()))
    out = Image.blend(im, base, k)
    if im.mode == "RGBA":
        out.putalpha(im.getchannel("A"))
    return out


def wear(im, seed=1, scratches=40, dirt=0.25):
    """스크래치·모서리 때·아래쪽 먼지."""
    rng = random.Random(seed)
    w, h = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for _ in range(scratches):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        a = rng.uniform(0, math.pi)
        l = rng.uniform(0.01, 0.06) * w
        d.line([(x, y), (x + math.cos(a) * l, y + math.sin(a) * l)], fill=(255, 255, 255, rng.randint(25, 70)), width=1)
    g = np.linspace(0, 1, h) ** 3 * dirt * 255
    dirt_a = np.repeat(g[:, None], w, 1)
    noise = np.asarray(Image.effect_noise((w, h), 60).filter(ImageFilter.GaussianBlur(3))) / 255.0
    dl = Image.fromarray(np.clip(dirt_a * (0.4 + noise), 0, 255).astype(np.uint8))
    dirt_layer = Image.new("RGBA", im.size, (90, 78, 60, 0))
    dirt_layer.putalpha(dl)
    ov = Image.alpha_composite(ov, dirt_layer)
    base = im.convert("RGBA")
    out = Image.alpha_composite(base, ov)
    if im.mode == "RGBA":
        out.putalpha(im.getchannel("A"))
        return out
    return out.convert(im.mode)


def photo(name, size):
    im = Image.open(REF + name).convert("RGBA")
    return im.resize((size, size), Image.LANCZOS)


def shadow_paste(base, im, xy, blur=14, off=(0, 10), alpha=110):
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").point(lambda v: v * alpha // 255))
    sh = sh.filter(ImageFilter.GaussianBlur(blur))
    base.alpha_composite(sh, (xy[0] + off[0], xy[1] + off[1]))
    base.alpha_composite(im, xy)


# ------------------------------------------------------------------ door
def door_icon(pull, S=600):
    """빨간 원 안 크림색 픽토그램 190px (4배로 그려 줄임). 오른쪽 세로 막대 = 옆에서 본 문짝."""
    big = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    P = lambda x, y: (S / 2 + x * S / 2, S / 2 + y * S / 2)
    R = lambda x0, y0, x1, y1, r=0.0, **kw: d.rounded_rectangle([P(x0, y0), P(x1, y1)], radius=r * S / 2, **kw)
    d.ellipse([0, 0, S - 1, S - 1], fill=RED)
    R(0.50, -0.9, 0.66, 0.9, fill=CREAM)                       # 문짝 단면
    if pull:
        R(0.30, -0.36, 0.52, -0.26, fill=CREAM); R(0.30, 0.26, 0.52, 0.36, fill=CREAM)   # 손잡이 받침
        R(0.20, -0.44, 0.32, 0.44, 0.05, fill=CREAM)            # 손잡이 바
        d.polygon([P(-0.08, -0.14), P(-0.08, 0.22), P(-0.9, 0.46), P(-0.9, 0.06)], fill=CREAM)   # 팔
        R(-0.14, -0.22, 0.38, 0.26, 0.13, fill=CREAM, outline=RED, width=10)   # 주먹
        for y in (-0.08, 0.04, 0.15):
            d.line([P(0.16, y), P(0.37, y)], fill=RED, width=10)  # 손가락 마디
        R(0.0, -0.34, 0.32, -0.17, 0.08, fill=CREAM, outline=RED, width=10)    # 엄지
        d.polygon([P(0.22, -0.68), P(-0.30, -0.68), P(-0.30, -0.84), P(-0.70, -0.58), P(-0.30, -0.32), P(-0.30, -0.48),
                   P(0.22, -0.48)], fill=CREAM)                 # 문에서 멀어지는(몸 쪽) 화살표
    else:
        d.polygon([P(0.30, 0.10), P(0.30, 0.32), P(-0.9, 0.46), P(-0.9, 0.24)], fill=CREAM)       # 팔 (가늘게)
        R(0.16, -0.70, 0.46, 0.32, 0.14, fill=CREAM)            # 문에 댄 손바닥 + 곧게 편 손가락 (문과 틈)
        d.line([P(0.20, -0.04), P(0.02, -0.30)], fill=CREAM, width=int(0.15 * S / 2))   # 엄지
        d.ellipse([P(-0.06, -0.38), P(0.10, -0.22)], fill=CREAM)
        for y in (-0.46, -0.24):
            d.line([P(0.24, y), P(0.42, y)], fill=RED, width=9)  # 손가락 마디
        d.polygon([P(-0.56, 0.66), P(0.0, 0.66), P(0.0, 0.52), P(0.40, 0.74), P(0.0, 0.96), P(0.0, 0.82),
                   P(-0.56, 0.82)], fill=CREAM)                 # 문 쪽 화살표
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, S - 1, S - 1], fill=255)
    big.putalpha(ImageChops.multiply(big.getchannel("A"), mask))
    return big.resize((190, 190), Image.LANCZOS)


def sticker(top, sub, arrow, seed):
    """'당기세요 PULL' 류 문 스티커 1024×512 (실물 17×8.5cm)."""
    W, H = 1024, 512
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 14, W - 14, H - 14], radius=46, outline=RED, width=26)
    d.rounded_rectangle([52, 52, W - 52, H - 52], radius=24, outline=RED, width=5)
    f = fit(top, "han", W - 330, 210)
    text(d, (W / 2 + 115, H * 0.43), top, f, RED)
    text(d, (W / 2 + 115, H * 0.78), sub, font("black", 92), BROWN, spacing=38)
    # 손 픽토그램 (옆에서 본 문짝 + 손잡이): 당기기 = 주먹으로 쥐고 문에서 멀어지는 화살표, 밀기 = 손바닥으로 문 쪽 화살표
    ic = door_icon(arrow == "in")
    im.paste(ic.convert("RGB"), (165 - 95, int(H * 0.5) - 95), ic)
    im = fade(grain(im, 6, seed), 0.10)
    im = wear(im, seed, 70, 0.10)
    # 손때 (손잡이 쪽 오른 아래)
    sm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sm).ellipse([W * 0.62, H * 0.45, W * 1.05, H * 1.1], fill=60)
    sm = sm.filter(ImageFilter.GaussianBlur(60))
    im = Image.composite(Image.new("RGB", (W, H), (120, 100, 80)), im, sm)
    return im


def door():
    A = "StoreGlassDoor"
    save(sticker("당기세요", "PULL", "in", 3), A, "PullSticker")
    save(sticker("미세요", "PUSH", "out", 4), A, "PushSticker")
    # 손끼임 주의 (노랑 원형, 8cm)
    W = 512
    im = Image.new("RGBA", (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse([6, 6, W - 6, W - 6], fill="#f2c318", outline="#1d1d1b", width=18)
    text(d, (W / 2, W * 0.30), "손끼임", font("black", 92), "#1d1d1b")
    text(d, (W / 2, W * 0.50), "주의", font("black", 120), "#c4161c")
    text(d, (W / 2, W * 0.70), "문을 천천히", font("bold", 46), "#1d1d1b")
    text(d, (W / 2, W * 0.80), "닫아주세요", font("bold", 46), "#1d1d1b")
    save(wear(fade(im, 0.15), 5, 30, 0.15), A, "Caution")
    # 유리 얼룩: RGB=유리 색, A=불투명도 (기본 0.10 + 손자국·먼지)
    W, H = 1024, 2048
    a = np.full((H, W), 0.10, np.float32)
    rng = np.random.default_rng(7)
    def blob(cx, cy, rx, ry, v, rot=0):
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        x, y = xx - cx, yy - cy
        c, s = math.cos(rot), math.sin(rot)
        u, w = (x * c + y * s) / rx, (-x * s + y * c) / ry
        return v * np.exp(-(u * u + w * w) * 2.2)
    def hand(cx, cy, sc, rot, v):
        out = blob(cx, cy, 42 * sc, 52 * sc, v, rot)
        for k in range(4):
            ang = rot - 0.55 + k * 0.33
            fx, fy = cx + math.sin(ang) * 85 * sc, cy - math.cos(ang) * 85 * sc
            out += blob(fx, fy, 11 * sc, 30 * sc, v * 0.9, ang)
        out += blob(cx - 60 * sc, cy - 10 * sc, 12 * sc, 26 * sc, v * 0.8, rot - 1.0)
        return out
    # 손잡이(오른쪽, 0.9~1.4m) 주변 손자국. 유리 높이 ≈ 2.0m (V 0→1 = 아래→위)
    for i in range(9):
        cx = rng.uniform(0.62, 0.95) * W
        cy = H * (1 - rng.uniform(0.38, 0.66))
        a += hand(cx, cy, rng.uniform(0.7, 1.0), rng.uniform(-0.6, 0.4), rng.uniform(0.04, 0.09))
    for i in range(4):  # 아이 손
        a += hand(rng.uniform(0.2, 0.8) * W, H * (1 - rng.uniform(0.28, 0.4)), 0.5, rng.uniform(-0.4, 0.4), 0.05)
    a += blob(0.3 * W, H * 0.88, 30, 22, 0.06)  # 강아지 코
    yy = np.linspace(0, 1, H)[:, None]
    a += np.clip((yy - 0.82) / 0.18, 0, 1) ** 1.5 * 0.16  # 아래쪽 먼지 띠
    n = np.asarray(Image.effect_noise((W, H), 90).filter(ImageFilter.GaussianBlur(10)), np.float32) / 255
    a += (n - 0.5) * 0.04
    # 닦은 자국 (호)
    st = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(st)
    for i in range(6):
        cx, cy, r = rng.uniform(0.2, 0.8) * W, rng.uniform(0.3, 0.8) * H, rng.uniform(150, 400)
        sd.arc([cx - r, cy - r, cx + r, cy + r], rng.uniform(0, 180), rng.uniform(200, 340), fill=40, width=int(rng.uniform(20, 60)))
    a += np.asarray(st.filter(ImageFilter.GaussianBlur(14)), np.float32) / 255 * 0.5
    a = np.clip(a, 0.06, 0.5)
    rgb = np.empty((H, W, 3), np.float32)
    rgb[:] = (196, 210, 204)
    dirt = np.clip((a - 0.1) * 2.5, 0, 1)[..., None]
    rgb = rgb * (1 - dirt * 0.25) + np.array((214, 206, 190)) * dirt * 0.25
    img = Image.fromarray(np.dstack([rgb, a[..., None] * 255]).astype(np.uint8), "RGBA")
    save(img, A, "GlassSmudge")


# ------------------------------------------------------------------ facade
def poster_new():
    W, H = 1024, 1480
    im = Image.new("RGBA", (W, H), RED)
    d = ImageDraw.Draw(im)
    d.ellipse([W * 0.04, H * 0.24, W * 0.96, H * 0.24 + W * 0.92], fill="#d6442f")
    for i in range(24):  # 방사형 빛
        a0 = i * 15
        d.pieslice([W * -0.3, H * 0.0, W * 1.3, H * 1.0], a0, a0 + 6, fill=(214, 68, 47, 255))
    d.ellipse([W * 0.08, H * 0.26, W * 0.92, H * 0.26 + W * 0.84], fill="#e05a3a")
    text(d, (W / 2, H * 0.085), "왕이 돌아왔다", font("han", 128), CREAM)
    text(d, (W / 2, H * 0.165), "NEW · 기간 한정", font("black", 54), "#f7c64a", spacing=6)
    b = photo("burger_double.png", 760)
    shadow_paste(im, b, (int(W / 2 - 380), int(H * 0.30)))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([W * 0.08, H * 0.80, W * 0.92, H * 0.95], radius=30, fill=CREAM)
    text(d, (W / 2, H * 0.845), "스모키 킹 세트", font("han", 96), RED)
    text(d, (W / 2, H * 0.915), "9,300원  (단품 7,400원)", font("black", 50), BROWN)
    d.ellipse([W * 0.70, H * 0.22, W * 0.96, H * 0.22 + W * 0.26], fill="#f7c64a")
    text(d, (W * 0.83, H * 0.22 + W * 0.10), "더블", font("han", 70), RED)
    text(d, (W * 0.83, H * 0.22 + W * 0.17), "패티", font("han", 58), RED)
    logo(d, W * 0.13, H * 0.235, 0.9, wordmark=False)
    return im


def poster_bulgogi():
    W, H = 1024, 1480
    im = Image.new("RGBA", (W, H), "#f4e8cf")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, H * 0.2], fill="#7a2a14")
    text(d, (W / 2, H * 0.07), "한국인의 입맛 그대로", font("black", 62), CREAM)
    text(d, (W / 2, H * 0.145), "K-BBQ 스모키 비프 세트", fit("K-BBQ 스모키 비프 세트", "han", W * 0.9, 112), "#f7c64a")  # 키오스크 메뉴명과 같게
    for r in range(4):  # 배경 무늬
        d.ellipse([W * (0.1 - r * 0.05), H * (0.28 - r * 0.03), W * (0.9 + r * 0.05), H * (0.28 - r * 0.03) + W * (0.8 + r * 0.1)],
                  outline=(226, 167, 46, 120), width=4)
    b = photo("burger_bulgogi.png", 700)
    shadow_paste(im, b, (int(W * 0.06), int(H * 0.27)))
    c = photo("cola.png", 420)
    shadow_paste(im, c, (int(W * 0.62), int(H * 0.36)))
    fr = Image.open(REF + "fries.jpg").convert("RGB").resize((300, 300))
    m = Image.new("L", (300, 300), 0)
    ImageDraw.Draw(m).ellipse([10, 10, 290, 290], fill=255)
    fr.putalpha(m.filter(ImageFilter.GaussianBlur(4)))
    shadow_paste(im, fr, (int(W * 0.66), int(H * 0.60)))
    d = ImageDraw.Draw(im)
    d.rectangle([0, H * 0.79, W, H], fill=RED)
    text(d, (W * 0.36, H * 0.845), "불고기 버거 + 감자튀김 + 콜라", fit("불고기 버거 + 감자튀김 + 콜라", "bold", W * 0.66, 50), CREAM)
    text(d, (W * 0.36, H * 0.92), "7,900원", font("han", 130), "#ffffff")  # 단품 5,900 + 세트 2,000
    d.ellipse([W * 0.72, H * 0.80, W * 0.96, H * 0.80 + W * 0.24], fill="#f7c64a")
    text(d, (W * 0.84, H * 0.80 + W * 0.09), "BEST", font("black", 56), RED)
    text(d, (W * 0.84, H * 0.80 + W * 0.155), "1위", font("han", 64), RED)
    return im


def poster_fries():
    W, H = 1024, 1480
    im = Image.new("RGBA", (W, H), BROWN)
    d = ImageDraw.Draw(im)
    text(d, (W / 2, H * 0.09), "사이드는", font("han", 120), CREAM)
    text(d, (W / 2, H * 0.18), "왕의 친구", font("han", 150), "#f7c64a")
    fr = Image.open(REF + "fries.jpg").convert("RGB").resize((560, 560))
    m = Image.new("L", (560, 560), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, 560, 560], radius=60, fill=255)
    fr.putalpha(m)
    shadow_paste(im, fr, (int(W * 0.06), int(H * 0.30)))
    for i, (n, sz, x, y) in enumerate((("nuggets.png", 380, 0.58, 0.28), ("cola.png", 420, 0.55, 0.50))):
        shadow_paste(im, photo(n, sz), (int(W * x), int(H * y)))
    d = ImageDraw.Draw(im)
    rows = (("프렌치 프라이 R", "2,300원"), ("치킨 너겟 4조각", "2,900원"), ("제로 콜라 M", "2,200원"))
    for i, (a, b) in enumerate(rows):
        y = H * (0.76 + i * 0.07)
        d.text((W * 0.08, y), a, font=font("bold", 54), fill=CREAM, anchor="lm")
        d.text((W * 0.92, y), b, font=font("black", 54), fill="#f7c64a", anchor="rm")
        d.line([(W * 0.08, y + 34), (W * 0.92, y + 34)], fill=(241, 228, 200, 90), width=2)
    return im


def poster_kiosk():
    W, H = 720, 1020
    im = Image.new("RGBA", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    text(d, (W / 2, H * 0.14), "주문은", font("han", 104), BROWN)
    text(d, (W / 2, H * 0.27), "키오스크에서", font("han", 104), BROWN)
    d.rectangle([W * 0.1, H * 0.35, W * 0.9, H * 0.36], fill=RED)
    text(d, (W / 2, H * 0.42), "빠르고 간편합니다", font("bold", 46), BROWN)
    # 키오스크 그림
    kx, ky = W / 2, H * 0.63
    d.rounded_rectangle([kx - 85, ky - 120, kx + 85, ky + 120], radius=14, fill="#2b2b2b")
    d.rectangle([kx - 70, ky - 105, kx + 70, ky + 40], fill="#e9f1f5")
    for r in range(3):
        for c in range(3):
            d.rectangle([kx - 62 + c * 43, ky - 96 + r * 44, kx - 26 + c * 43, ky - 62 + r * 44], fill=(RED, MUSTARD, "#7aa35a")[(r + c) % 3])
    d.rectangle([kx - 30, ky + 62, kx + 30, ky + 68], fill="#777")
    d.ellipse([kx + 60, ky - 20, kx + 130, ky + 50], fill="#f7d3a8")  # 손가락
    d.rectangle([kx + 88, ky + 30, kx + 150, ky + 140], fill="#f7d3a8")
    text(d, (W / 2, H * 0.86), "1. 메뉴 선택  2. 결제  3. 번호 확인", font("med", 30), BROWN)
    logo(d, W / 2, H * 0.94, 0.42, wordmark=False)
    return im


def hours_vinyl():
    W, H = 1024, 600
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((40, 70), "OPEN", font=font("black", 96), fill="white", anchor="lm")
    d.text((W - 40, 70), "10:00", font=font("black", 96), fill="white", anchor="rm")
    d.text((40, 200), "CLOSE", font=font("black", 96), fill="white", anchor="lm")
    d.text((W - 40, 200), "22:00", font=font("black", 96), fill="white", anchor="rm")
    d.line([(40, 280), (W - 40, 280)], fill="white", width=6)
    d.text((40, 350), "연중무휴", font=font("bold", 70), fill="white", anchor="lm")
    d.text((40, 450), "라스트오더 21:30", font=font("med", 56), fill="white", anchor="lm")
    d.text((40, 540), "버거대왕 시장입구점", font=font("med", 44), fill="white", anchor="lm")
    return im


def card_only():
    W, H = 800, 520
    im = Image.new("RGBA", (W, H), "#ffffff")
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 120], fill="#1f2a44")
    text(d, (W / 2, 62), "현금 없는 매장", font("han", 84), "#ffffff")
    text(d, (W / 2, 210), "CARD ONLY", font("black", 110), "#1f2a44", spacing=4)
    text(d, (W / 2, 318), "카드 · 간편결제만 가능합니다", font("bold", 44), "#333")
    text(d, (W / 2, 380), "현금 결제 불가 / 지폐 교환 불가", font("med", 36), RED)
    for i, s in enumerate(("신용카드", "체크카드", "모바일페이", "교통카드")):
        x = 70 + i * 170
        d.rounded_rectangle([x, 430, x + 150, 490], radius=10, outline="#1f2a44", width=3)
        text(d, (x + 75, 460), s, font("bold", 26), "#1f2a44")
    return wear(im, 8, 30, 0.12)


def qr_coupon():
    W, H = 640, 800
    im = Image.new("RGBA", (W, H), MUSTARD)
    d = ImageDraw.Draw(im)
    text(d, (W / 2, H * 0.11), "앱 전용", font("han", 120), BROWN)
    text(d, (W / 2, H * 0.24), "QR 찍고 500원 할인", font("black", 50), BROWN)
    q = 25
    s = int(W * 0.5 / q)
    x0, y0 = int(W / 2 - q * s / 2), int(H * 0.32)
    d.rectangle([x0 - 20, y0 - 20, x0 + q * s + 20, y0 + q * s + 20], fill="white")
    rng = random.Random(11)
    for r in range(q):
        for c in range(q):
            fin = (r < 7 and c < 7) or (r < 7 and c >= q - 7) or (r >= q - 7 and c < 7)
            if fin:
                rr, cc = r % (q - 7) if r >= 7 else r, c % (q - 7) if c >= 7 else c
                on = rr in (0, 6) or cc in (0, 6) or (2 <= rr <= 4 and 2 <= cc <= 4)
            else:
                on = rng.random() < 0.48
            if on:
                d.rectangle([x0 + c * s, y0 + r * s, x0 + c * s + s - 1, y0 + r * s + s - 1], fill="#1b1b1b")
    text(d, (W / 2, H * 0.89), "회원가입 후 사용 가능 · 1인 1회", font("med", 30), BROWN)
    return wear(fade(im, 0.18), 9, 25, 0.1)


def cctv():
    W, H = 600, 340
    im = Image.new("RGBA", (W, H), "#f2c318")
    d = ImageDraw.Draw(im)
    d.rectangle([10, 10, W - 10, H - 10], outline="#1b1b1b", width=12)
    d.rounded_rectangle([40, 70, 170, 150], radius=12, fill="#1b1b1b")
    d.polygon([(170, 90), (215, 70), (215, 150), (170, 130)], fill="#1b1b1b")
    d.rectangle([90, 150, 110, 230], fill="#1b1b1b")
    text(d, (400, 110), "CCTV", font("black", 110), "#1b1b1b")
    text(d, (400, 215), "24시간 녹화중", font("black", 56), "#c4161c")
    text(d, (W / 2, 290), "개인정보보호법에 따라 운영됩니다", font("med", 26), "#1b1b1b")
    return wear(fade(im, 0.2), 10, 20, 0.1)


def help_wanted():
    """손글씨 알바 구함 메모 (A4, 테이프)."""
    W, H = 700, 990
    im = Image.new("RGBA", (W, H), "#fbfaf4")
    d = ImageDraw.Draw(im)
    for y in range(140, H - 60, 62):
        d.line([(40, y), (W - 40, y)], fill="#cfd8e6", width=2)
    p = font("pen", 120)
    d.text((W / 2, 120), "알바 구함", font=p, fill="#c41e1e", anchor="mm")
    lines = ["- 주말 오전 (9시~2시)", "- 시급 협의", "- 성실하신 분", "- 경력 무관 ^^", "", "문의: 매장 내 점장"]
    for i, s in enumerate(lines):
        d.text((70, 250 + i * 98), s, font=font("pen", 78), fill="#1d2a7a", anchor="lm")
    d.polygon([(W / 2 - 90, -10), (W / 2 + 90, -10), (W / 2 + 85, 50), (W / 2 - 95, 46)], fill=(235, 230, 200, 200))
    return wear(im, 12, 15, 0.08)


def band():
    """충돌방지 띠 (반복, 2048×96)."""
    W, H = 2048, 96
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 6, W, H - 6], fill=(181, 39, 28, 235))
    for i in range(3):
        x = i * W / 3 + 40
        logo(d, x + 30, H / 2 + 14, 0.38, wordmark=False)
        d.text((x + 90, H / 2), "BURGER DAEWANG · 버거대왕", font=font("black", 40), fill=CREAM, anchor="lm")
    return im


def proj_sign():
    """돌출간판 면 (0.62×2.4m). 빨강 바탕 + 로고 + 세로 '버거대왕'."""
    W, H = 512, 2048
    im = Image.new("RGB", (W, H), RED)
    d = ImageDraw.Draw(im)
    d.rectangle([14, 14, W - 14, H - 14], outline=CREAM, width=10)
    logo(d, W / 2, H * 0.12, W / 210, wordmark=False)
    for i, ch in enumerate("버거대왕"):
        d.text((W / 2, H * (0.33 + i * 0.165)), ch, font=font("han", W * 0.66), fill=CREAM, anchor="mm")
    return grain(im, 4, 13)


def upper_sign(s, sub, bg, fg, seed, accent=None):
    W, H = 2048, 330
    im = Image.new("RGB", (W, H), bg)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 16], fill=accent or fg)
    d.rectangle([0, H - 16, W, H], fill=accent or fg)
    f = fit(s, "han", W * 0.62, H * 0.62)
    d.text((W * 0.38, H * 0.52), s, font=f, fill=fg, anchor="mm")
    y = H * 0.32
    for line in sub:
        d.text((W * 0.95, y), line, font=font("bold", 52), fill=fg, anchor="rm")
        y += 78
    return wear(fade(grain(im, 5, seed), 0.14), seed, 60, 0.35)


def window_vinyl(lines):
    """2층 학원 창문 레터링 (흰 시트 글자, 알파)."""
    W, H = 1024, 680
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = H * 0.22
    for s, k, sz in lines:
        d.text((W / 2, y), s, font=font(k, sz), fill=(255, 255, 255, 255), anchor="mm")
        y += sz * 1.25
    return im


def room(kind, seed):
    """위층 창 한 칸(2.4×1.6m) 너머 방 + 유리 반사. 불투명 창유리 텍스처로 쓴다.
    거리(눈높이)에서 올려다보면 창 너머로는 천장만 보이므로 천장을 원근으로 그린다 (깊이 t=0.47~4.3m)."""
    W, H = 2048, 1366  # 2배로 그려 줄임
    im = Image.new("RGB", (W, H), (40, 40, 42))
    d = ImageDraw.Draw(im)
    rng = random.Random(seed)
    def pj(x, t, D=8.0):
        k = D / (D + t)
        return (W / 2 + x * k * W / 2.4, (5.1 - 5.4 * k) / 1.6 * H)
    def cq(x0, x1, t0, t1, **kw):
        d.polygon([pj(x0, t0), pj(x1, t0), pj(x1, t1), pj(x0, t1)], **kw)
    def ceiling(base, line, lit):
        cq(-4, 4, 0.3, 5, fill=base)
        for i in range(10):  # 텍스 천장 600mm 격자
            t = 0.3 + i * 0.6
            d.line([pj(-4, t), pj(4, t)], fill=line, width=3)
        for j in range(-6, 7):
            d.line([pj(j * 0.6, 0.3), pj(j * 0.6, 5)], fill=line, width=3)
        for x in (-1.2, 0.6):  # 형광등 매입등 600×1200
            for t in (0.9, 2.1, 3.3):
                cq(x, x + 1.2, t, t + 0.6, fill=(92, 92, 88) if not lit else (255, 252, 238), outline=(150, 150, 146), width=5)
                for k in (1, 2):
                    d.line([pj(x + 0.4 * k, t), pj(x + 0.4 * k, t + 0.6)], fill=(76, 76, 72) if not lit else (225, 225, 215), width=4)
    if kind == "Class":   # 학원 교실: 불 켜진 형광등 + 천장형 에어컨
        ceiling((206, 205, 198), (176, 175, 168), True)
        cq(-0.42, 0.42, 2.55, 3.15, fill=(232, 232, 228), outline=(160, 160, 158), width=4)
        cq(-0.3, 0.3, 2.66, 3.04, fill=(196, 198, 198))
        for k in range(5):
            cq(-0.27, 0.27, 2.69 + k * 0.07, 2.72 + k * 0.07, fill=(150, 152, 152))
        tint = (1.0, 1.0, 0.97)
    elif kind == "Blinds":  # 치과: 흰 블라인드를 2/3 내림, 아래로 밝은 천장
        ceiling((200, 202, 200), (172, 174, 172), True)
        y1 = H * rng.uniform(0.58, 0.7)
        for y in range(0, int(y1), 26):
            d.rectangle([0, y, W, y + 19], fill=(222, 222, 216))
            d.rectangle([0, y + 15, W, y + 19], fill=(176, 176, 170))
        d.rectangle([0, y1, W, y1 + 22], fill=(196, 196, 190))
        for x in (W * 0.18, W * 0.82):
            d.line([(x, 0), (x, y1 + 140)], fill=(240, 240, 236), width=4)
            d.rounded_rectangle([x - 9, y1 + 140, x + 9, y1 + 175], radius=8, fill=(236, 236, 230))
        tint = (0.98, 1.0, 1.0)
    elif kind == "Curtain":  # 불 꺼진 방 + 반쯤 친 베이지 커튼
        ceiling((70, 68, 64), (58, 56, 52), False)
        gap0, gap1 = W * rng.uniform(0.36, 0.44), W * rng.uniform(0.56, 0.66)
        for x in range(0, W, 4):
            if gap0 < x < gap1:
                continue
            v = 0.72 + 0.28 * math.sin(x / 38.0 + rng.random() * 0.3) * (0.6 + 0.4 * math.sin(x / 9.0))
            c = tuple(int(cv * v) for cv in (196, 176, 146))
            d.line([(x, 60), (x, H)], fill=c, width=4)
        d.rectangle([0, 0, W, 64], fill=(150, 140, 122))
        tint = (1.0, 0.98, 0.95)
    else:  # Empty: 임대 층, 불 꺼진 콘크리트 천장 + 뜯긴 텍스 + 늘어진 전선
        cq(-4, 4, 0.3, 5, fill=(92, 90, 86))
        for i in range(10):
            t = 0.3 + i * 0.6
            d.line([pj(-4, t), pj(4, t)], fill=(70, 68, 64), width=3)
        for j in range(-6, 7):
            d.line([pj(j * 0.6, 0.3), pj(j * 0.6, 5)], fill=(70, 68, 64), width=3)
        for _ in range(7):  # 뜯긴 칸
            x, t = rng.randint(-5, 4) * 0.6, 0.3 + rng.randint(0, 6) * 0.6
            cq(x, x + 0.6, t, t + 0.6, fill=(28, 27, 26))
        for x in (-0.9, 0.9):  # 등 빠진 형광등 받침 + 늘어진 전선
            cq(x - 0.06, x + 0.06, 1.0, 2.3, fill=(150, 150, 146))
            a, b = pj(x, 1.6), pj(x + 0.2, 1.6)
            d.line([a, (a[0] + 30, a[1] + 120), (b[0] + 10, b[1] + 160)], fill=(20, 20, 20), width=6)
        n = np.asarray(Image.effect_noise((W // 8, H // 8), 60).resize((W, H), Image.BILINEAR), np.float32) / 255
        im = Image.fromarray(np.clip(np.asarray(im, np.float32) * (0.8 + 0.4 * n[..., None]), 0, 255).astype(np.uint8))
        tint = (0.96, 0.97, 0.97)
    a = np.asarray(im, np.float32) * np.array(tint) * np.array((0.80, 0.86, 0.88))   # 유리 색
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    m = 0.10 + 0.20 * (1 - yy / H) + 0.08 * np.exp(-(((xx - yy * 0.6 - W * rng.uniform(0.2, 0.6)) / (W * 0.12)) ** 2))
    a = a * (1 - m[..., None]) + np.array((176, 192, 206)) * m[..., None]   # 하늘 반사
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((1024, 683), Image.LANCZOS)
    return grain(out, 4, seed).convert("RGB")


def shop_backdrop(kind):
    """옆 가게 유리 안쪽 진열 (흐릿한 상품)."""
    W, H = 1024, 512
    im = Image.new("RGB", (W, H), "#d4cab2")
    d = ImageDraw.Draw(im)
    rng = random.Random(21 if kind == "rice" else 22)
    if kind == "rice":
        d.rectangle([0, H * 0.62, W, H], fill="#8c6c48")
        for r in range(3):
            for c in range(10):
                x, y = 30 + c * W / 10.5, H * (0.40 + r * 0.12)
                d.rounded_rectangle([x, y, x + W / 13, y + H * 0.08], radius=10,
                                    fill=["#e8d9c0", "#d35f6a", "#7a9c5a", "#e6c35a", "#f3efe6"][(c + r) % 5])
        d.rectangle([W * 0.05, H * 0.08, W * 0.4, H * 0.3], fill="#efe6d0")
        text(d, (W * 0.225, H * 0.19), "오늘 만든 떡", font("pen", 70), "#7a2a14")
    else:
        d.rectangle([0, 0, W, H], fill="#e8ece8")
        for r in range(5):
            y = H * (0.12 + r * 0.18)
            d.rectangle([0, y + 52, W, y + 58], fill="#9aa4a0")
            for c in range(46):
                hgt = rng.uniform(22, 50)
                col = tuple(int(v) for v in np.array([rng.uniform(80, 240) for _ in range(3)]))
                d.rectangle([c * W / 46 + 2, y + 52 - hgt, (c + 1) * W / 46 - 3, y + 52], fill=col)
    return im.filter(ImageFilter.GaussianBlur(2.2))


def facade():
    A = "StorefrontFacade"
    save(fade(grain(poster_new(), 5, 1), 0.08).convert("RGB"), A, "PosterNew", jpg=True)
    save(fade(grain(poster_bulgogi(), 5, 2), 0.08).convert("RGB"), A, "PosterBulgogi", jpg=True)
    save(fade(grain(poster_fries(), 5, 3), 0.10).convert("RGB"), A, "PosterFries", jpg=True)
    save(fade(grain(poster_kiosk(), 5, 4), 0.12).convert("RGB"), A, "PosterKiosk", jpg=True)
    save(hours_vinyl(), A, "VinylHours")
    save(card_only().convert("RGB"), A, "StickerCardOnly", jpg=True)
    save(qr_coupon().convert("RGB"), A, "StickerCoupon", jpg=True)
    save(cctv().convert("RGB"), A, "StickerCCTV", jpg=True)
    save(help_wanted().convert("RGB"), A, "NoteHelpWanted", jpg=True)
    save(band(), A, "VinylBand")
    save(proj_sign(), A, "ProjSign", jpg=True)
    save(upper_sign("일등 영어학원", ["초·중·고 내신 / 수능", "TEL. 02-123-4567"], "#2f6d6a", "#f2f0e4", 31), A, "SignAcademy", jpg=True)
    save(upper_sign("튼튼 치과", ["임플란트 · 교정 · 충치", "토요일 진료"], "#e4dfcf", "#31353a", 32, "#3d7fb0"), A, "SignDental", jpg=True)
    save(upper_sign("2030 당구장", ["4층 · 중대 8 대대 4", "24시 영업"], "#7b3d7a", "#f2eadf", 33), A, "SignBilliards", jpg=True)
    save(upper_sign("왕할머니 떡집", ["시장 입구 40년", "떡 · 한과 · 식혜"], "#2f6b48", "#f4eed8", 34), A, "SignRiceCake", jpg=True)
    save(upper_sign("큰길 약국", ["처방조제 · 일반의약품", "휴일지킴이 약국"], "#e9e6dc", "#28663f", 35, "#28663f"), A, "SignPharmacy", jpg=True)
    save(window_vinyl([("영어 · 수학 전문", "black", 96), ("초 · 중 · 고 내신대비", "bold", 70), ("상담 환영", "bold", 70)]), A, "VinylAcademy")
    save(window_vinyl([("임플란트", "black", 110), ("교정 · 미백", "bold", 84)]), A, "VinylDental")
    save(window_vinyl([("당구", "han", 200), ("BILLIARDS", "black", 70)]), A, "VinylBilliards")
    for i, k in enumerate(("Class", "Blinds", "Curtain", "Empty")):
        save(room(k, 60 + i), A, "Room" + k, jpg=True)
    save(shop_backdrop("rice"), A, "BackdropRiceCake", jpg=True)
    save(shop_backdrop("pharm"), A, "BackdropPharmacy", jpg=True)
    # 매장 유리 얼룩 (매장 폭 11.6m × 3.1m 를 한 장에)
    W, H = 2048, 1024
    rng = np.random.default_rng(5)
    a = np.full((H, W), 0.08, np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    def ux(x):  # 월드 x(m) -> px
        return (x + 6.05) / 11.6 * W
    def vz(z):  # 높이(m) -> px (위가 0)
        return (1 - z / 3.1) * H
    for i in range(26):  # 문 주변 손자국
        cx = ux(rng.choice([rng.uniform(0.2, 0.85), rng.uniform(1.95, 2.6)]))
        cy = vz(rng.uniform(0.85, 1.5))
        a += 0.06 * np.exp(-(((xx - cx) / 9) ** 2 + ((yy - cy) / 22) ** 2))
    for i in range(10):  # 아이 손
        a += 0.05 * np.exp(-(((xx - ux(rng.uniform(-5.5, 5.2))) / 6) ** 2 + ((yy - vz(rng.uniform(0.5, 0.95))) / 14) ** 2))
    a += np.clip((yy / H - 0.86) / 0.14, 0, 1) ** 1.4 * 0.14
    # 빗물 자국 (위에서 아래로 가는 줄)
    st = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(st)
    for i in range(160):
        x = rng.uniform(0, W)
        y0 = rng.uniform(0, H * 0.3)
        l = rng.uniform(40, 260)
        sd.line([(x, y0), (x + rng.uniform(-3, 3), y0 + l)], fill=int(rng.uniform(20, 60)), width=int(rng.uniform(1, 3)))
    a += np.asarray(st.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255 * 0.25
    n = np.asarray(Image.effect_noise((W, H), 90).filter(ImageFilter.GaussianBlur(8)), np.float32) / 255
    a = np.clip(a + (n - 0.5) * 0.04, 0.05, 0.45)
    rgb = np.empty((H, W, 3), np.float32)
    rgb[:] = (190, 206, 202)
    save(Image.fromarray(np.dstack([rgb, a[..., None] * 255]).astype(np.uint8), "RGBA"), A, "GlassSmudge")
    # 창턱 아래 빗물 때 (알파, 위→아래로 옅어짐)
    W, H = 512, 1024
    rng = np.random.default_rng(9)
    a = np.zeros((H, W), np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    for i in range(70):
        x = int(rng.uniform(0, W))
        w = int(rng.uniform(2, 14))
        l = rng.uniform(0.2, 1.0)
        col = np.clip(1 - yy / l, 0, 1) ** 1.6 * rng.uniform(0.15, 0.5)
        a[:, max(0, x - w):x + w] += col
    a += np.clip(1 - yy / 0.12, 0, 1) * 0.35
    a = np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    rgb = np.empty((H, W, 3), np.float32)
    rgb[:] = (52, 44, 36)
    save(Image.fromarray(np.dstack([rgb, np.clip(a, 0, 0.8)[..., None] * 255]).astype(np.uint8), "RGBA"), A, "Streaks")
    # 4층 '임대 문의' 현수막 (창문 안쪽)
    W, H = 1024, 680
    im = Image.new("RGB", (W, H), (246, 244, 238))
    d = ImageDraw.Draw(im)
    text(d, (W / 2, H * 0.36), "임  대", font("han", 300), (200, 28, 28))
    text(d, (W / 2, H * 0.80), "문의 010-1234-5678", font("black", 84), (30, 30, 30))
    save(wear(fade(im, 0.25), 14, 30, 0.2), A, "BannerRent", jpg=True)
    # 발매트 인쇄 (붉은 테두리 + 어서오세요)
    W, H = 1024, 680
    im = Image.new("RGB", (W, H), (58, 56, 54))
    d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H - 40], outline=(150, 40, 30), width=30)
    text(d, (W / 2, H * 0.42), "어서오세요", font("han", 150), (196, 150, 70))
    text(d, (W / 2, H * 0.67), "WELCOME", font("black", 80), (170, 160, 150), spacing=20)
    save(im, A, "DoorMatPrint", jpg=True)


# ------------------------------------------------------------------ AC
def ac():
    A = "StorefrontAC"
    W, H = 1024, 512
    im = Image.new("RGB", (W, H), (226, 224, 216))
    d = ImageDraw.Draw(im)
    # 왼쪽: 정격 명판 (은색) 0..512
    d.rectangle([0, 0, 511, H], fill=(196, 198, 200))
    d.rectangle([12, 12, 499, H - 12], outline=(60, 60, 60), width=4)
    d.text((30, 40), "바람누리 인버터 실외기", font=font("black", 40), fill=(30, 30, 30), anchor="lm")
    rows = [("모델명", "BN-C072HS"), ("정격전압", "단상 220V~ 60Hz"), ("냉방능력", "7,200 W"), ("소비전력", "2,150 W"),
            ("냉매", "R-410A  1.35 kg"), ("제조년월", "2014. 06"), ("제조번호", "406KA0213")]
    for i, (k, v) in enumerate(rows):
        y = 100 + i * 52
        d.text((30, y), k, font=font("bold", 30), fill=(40, 40, 40), anchor="lm")
        d.text((200, y), v, font=font("med", 30), fill=(40, 40, 40), anchor="lm")
        d.line([(24, y + 26), (488, y + 26)], fill=(120, 120, 120), width=1)
    # 오른쪽 위: 경고 (노랑) 512..1024 × 0..256
    d.rectangle([512, 0, W, 255], fill=(240, 196, 30))
    d.polygon([(560, 210), (620, 60), (680, 210)], fill=(20, 20, 20))
    d.polygon([(578, 198), (620, 92), (662, 198)], fill=(240, 196, 30))
    d.text((620, 180), "!", font=font("black", 80), fill=(20, 20, 20), anchor="mb")
    d.text((870, 80), "경 고", font=font("black", 62), fill=(20, 20, 20), anchor="mm")
    d.text((870, 150), "팬 회전 중 손 넣지 마세요", font=font("bold", 30), fill=(20, 20, 20), anchor="mm")
    d.text((870, 200), "점검 시 전원 차단", font=font("bold", 30), fill=(20, 20, 20), anchor="mm")
    # 오른쪽 아래: 앞판 브랜드 로고 512..1024 × 256..512
    d.rectangle([512, 256, W, H], fill=(226, 224, 216))
    d.text((768, 360), "바람누리", font=font("han", 110), fill=(70, 90, 120), anchor="mm")
    d.text((768, 450), "INVERTER", font=font("black", 46), fill=(70, 90, 120), anchor="mm")
    im = wear(fade(grain(im, 5, 41), 0.18), 41, 50, 0.3)
    save(im, A, "Labels")


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("door", "all"):
        door()
    if what in ("facade", "all"):
        facade()
    if what in ("ac", "all"):
        ac()
