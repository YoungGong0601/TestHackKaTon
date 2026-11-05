# StoreProps 라벨/표지 텍스처 (Pillow). 실행: venv/bin/python -I labels.py <Asset> <out.png>
import sys, os, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, PngImagePlugin, JpegImagePlugin  # noqa: F401 (플러그인 등록)

HOME = os.path.expanduser("~")
EB = HOME + "/Library/Fonts/NanumSquareEB.ttf"
B = HOME + "/Library/Fonts/NanumSquareB.ttf"
R = HOME + "/Library/Fonts/NanumSquareR.ttf"
MJ = "/System/Library/Fonts/Supplemental/AppleMyungjo.ttf"
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

RED, CREAM, BROWN = (181, 39, 28), (241, 228, 200), (74, 44, 24)
rng = random.Random(7)


def F(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def ctext(d, xy, s, font, fill, anchor="mm", spacing=0):
    d.text(xy, s, font=font, fill=fill, anchor=anchor)


def fit(d, s, path, size, maxw):
    f = F(path, size)
    while d.textlength(s, font=f) > maxw and size > 8:
        size -= 2
        f = F(path, size)
    return f


def age(im, amount=1.0, yellow=0.0, seed=1):
    """오래된 인쇄물: 미세 얼룩, 누렇게 바램, 모서리 손때."""
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    h, w = a.shape[:2]
    r = np.random.default_rng(seed)
    low = r.random((max(2, h // 64), max(2, w // 64))).astype(np.float32)
    low = np.asarray(Image.fromarray((low * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    fine = r.random((h, w)).astype(np.float32)
    a *= (1 - 0.06 * amount * low[..., None]) * (1 - 0.035 * amount * fine[..., None])
    if yellow:
        a = a * (1 - yellow) + a * np.array([1.0, 0.96, 0.82]) * yellow
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / (0.06 * min(w, h))
    a *= (0.9 + 0.1 * np.clip(edge, 0, 1))[..., None] ** amount
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def rrect(d, box, r, fill=None, outline=None, width=1):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


# ------------------------------------------------------------ 픽토그램

def pic_bin(d, cx, cy, s, c):
    d.polygon([(cx - .32 * s, cy - .28 * s), (cx + .32 * s, cy - .28 * s), (cx + .25 * s, cy + .45 * s), (cx - .25 * s, cy + .45 * s)], fill=c)
    d.rectangle((cx - .4 * s, cy - .42 * s, cx + .4 * s, cy - .33 * s), fill=c)
    d.rectangle((cx - .1 * s, cy - .5 * s, cx + .1 * s, cy - .42 * s), fill=c)
    for k in (-1, 0, 1):
        d.line((cx + k * .13 * s, cy - .18 * s, cx + k * .11 * s, cy + .35 * s), fill=(255, 255, 255), width=max(2, int(s * .05)))


def pic_food(d, cx, cy, s, c):
    d.chord((cx - .45 * s, cy - .35 * s, cx + .45 * s, cy + .45 * s), 0, 180, fill=c)
    d.rectangle((cx - .2 * s, cy + .38 * s, cx + .2 * s, cy + .46 * s), fill=c)
    for k, hgt in ((-.2, .35), (0, .48), (.2, .3)):
        d.ellipse((cx + k * s - .09 * s, cy - hgt * s, cx + k * s + .09 * s, cy - hgt * s + .22 * s), fill=c)
    d.polygon([(cx + .36 * s, cy - .48 * s), (cx + .26 * s, cy - .3 * s), (cx + .46 * s, cy - .3 * s)], fill=c)
    d.ellipse((cx + .26 * s, cy - .36 * s, cx + .46 * s, cy - .16 * s), fill=c)


def pic_cup(d, cx, cy, s, c):
    d.polygon([(cx - .3 * s, cy - .25 * s), (cx + .3 * s, cy - .25 * s), (cx + .22 * s, cy + .48 * s), (cx - .22 * s, cy + .48 * s)], fill=c)
    d.rectangle((cx - .36 * s, cy - .36 * s, cx + .36 * s, cy - .25 * s), fill=c)
    d.line((cx + .05 * s, cy - .36 * s, cx + .2 * s, cy - .7 * s, cx + .38 * s, cy - .7 * s), fill=c, width=max(3, int(s * .07)))


def pic_ext(d, cx, cy, s, c):
    d.rounded_rectangle((cx - .2 * s, cy - .25 * s, cx + .2 * s, cy + .5 * s), int(.15 * s), fill=c)
    d.rectangle((cx - .06 * s, cy - .38 * s, cx + .06 * s, cy - .25 * s), fill=c)
    d.polygon([(cx - .06 * s, cy - .4 * s), (cx + .32 * s, cy - .5 * s), (cx + .32 * s, cy - .42 * s), (cx + .06 * s, cy - .34 * s)], fill=c)
    d.line((cx - .06 * s, cy - .32 * s, cx - .34 * s, cy - .22 * s, cx - .38 * s, cy + .2 * s), fill=c, width=max(3, int(s * .06)))


def pic_slip(d, cx, cy, s, c):
    """미끄러지는 사람."""
    w = max(4, int(s * .085))
    d.ellipse((cx + .02 * s, cy - .5 * s, cx + .2 * s, cy - .32 * s), fill=c)
    d.line((cx + .08 * s, cy - .3 * s, cx - .1 * s, cy + .05 * s), fill=c, width=w + 4)
    d.line((cx + .02 * s, cy - .2 * s, cx + .3 * s, cy - .32 * s), fill=c, width=w)
    d.line((cx + .0 * s, cy - .16 * s, cx - .3 * s, cy - .3 * s), fill=c, width=w)
    d.line((cx - .1 * s, cy + .05 * s, cx + .28 * s, cy + .12 * s, cx + .42 * s, cy - .02 * s), fill=c, width=w)
    d.line((cx - .1 * s, cy + .05 * s, cx - .22 * s, cy + .32 * s), fill=c, width=w)
    d.line((cx - .5 * s, cy + .42 * s, cx + .5 * s, cy + .42 * s), fill=c, width=max(3, w // 2))
    for k in range(3):
        d.arc((cx + (.1 + k * .14) * s, cy + .28 * s, cx + (.22 + k * .14) * s, cy + .36 * s), 180, 360, fill=c, width=max(2, w // 3))


def pic_palm(d, cx, cy, s, c):
    """미는 손바닥."""
    d.rounded_rectangle((cx - .26 * s, cy - .05 * s, cx + .24 * s, cy + .42 * s), int(.14 * s), fill=c)
    for k, (dx, top) in enumerate(((-.2, -.36), (-.07, -.46), (.06, -.44), (.18, -.3))):
        d.rounded_rectangle((cx + dx * s - .055 * s, cy + top * s, cx + dx * s + .055 * s, cy + .05 * s), int(.055 * s), fill=c)
    d.line((cx - .24 * s, cy + .18 * s, cx - .42 * s, cy - .02 * s), fill=c, width=max(4, int(.11 * s)))


# ------------------------------------------------------------ 에셋별

def trash_station():
    W, H = 2048, 1024
    im = Image.new("RGB", (W, H), (236, 234, 228))
    d = ImageDraw.Draw(im)
    specs = [("일반쓰레기", "휴지 · 포장지 · 기타", (70, 74, 80), pic_bin),
             ("음식물", "남은 음식 · 음료 · 얼음", (214, 122, 36), pic_food),
             ("컵·빨대", "뚜껑과 빨대는 분리해 주세요", (36, 98, 168), pic_cup)]
    for i, (t, sub, col, pic) in enumerate(specs):  # 680x340 x3 (0.24 x 0.12 m)
        x0 = i * 682
        rrect(d, (x0 + 6, 6, x0 + 674, 334), 26, fill=(246, 245, 240), outline=col, width=10)
        rrect(d, (x0 + 22, 22, x0 + 232, 318), 20, fill=col)
        pic(d, x0 + 127, 160, 170, (255, 255, 255))
        f = fit(d, t, EB, 92, 410)
        ctext(d, (x0 + 452, 128), t, f, (32, 30, 28))
        ctext(d, (x0 + 452, 218), sub, fit(d, sub, B, 34, 410), (88, 84, 78))
        d.polygon([(x0 + 420, 304), (x0 + 484, 304), (x0 + 452, 262)], fill=col)  # ▲ 위 투입구를 가리킴
    # 상단 띠 (2048x200 -> 0.98 x 0.096 m)
    d.rectangle((0, 348, W, 548), fill=RED)
    d.rectangle((0, 356, W, 362), fill=CREAM)
    d.rectangle((0, 534, W, 540), fill=CREAM)
    ctext(d, (700, 448), "다 드신 트레이는 위에 올려 주세요", F(EB, 84), CREAM)
    ctext(d, (1660, 432), "분리배출에 협조해 주셔서", F(B, 44), CREAM)
    ctext(d, (1660, 484), "감사합니다 · 버거대왕", F(B, 44), CREAM)
    # 트레이 반납 스티커 (680x400 -> 0.2 x 0.118 m)
    rrect(d, (6, 560, 674, 960), 30, fill=CREAM, outline=RED, width=12)
    for k in range(4):
        rrect(d, (90 + k * 10, 640 + k * 26, 300 - k * 10, 662 + k * 26), 8, fill=(120, 70, 40))
    ctext(d, (470, 700), "트레이", F(EB, 96), RED)
    ctext(d, (470, 812), "반납", F(EB, 96), RED)
    ctext(d, (340, 910), "TRAY RETURN", F(B, 40), BROWN)
    # 주의 스티커 (680x400) - 손 끼임
    rrect(d, (700, 560, 1368, 960), 30, fill=(250, 214, 64), outline=(30, 28, 26), width=10)
    ctext(d, (1034, 660), "손 조심", F(EB, 100), (30, 28, 26))
    ctext(d, (1034, 790), "투입구에 손을 넣지 마세요", fit(d, "투입구에 손을 넣지 마세요", B, 46, 600), (30, 28, 26))
    # 덮개 '미세요 / PUSH' 손바닥 데칼 (300x300 -> 0.05 x 0.05 m)
    rrect(d, (1400, 580, 1700, 880), 34, fill=(238, 236, 230))
    pic_palm(d, 1550, 690, 150, (40, 40, 44))
    ctext(d, (1550, 808), "미세요", F(EB, 62), (40, 40, 44))
    ctext(d, (1550, 856), "PUSH", F(B, 30), (90, 90, 94))
    return age(im, 1.0, 0.08, 3)


def ext_sign():
    W, H = 1024, 512  # 0.24 x 0.12 m
    im = Image.new("RGB", (W, H), (198, 34, 26))
    d = ImageDraw.Draw(im)
    rrect(d, (14, 14, W - 14, H - 14), 22, outline=(250, 244, 236), width=8)
    pic_ext(d, 200, 250, 300, (250, 244, 236))
    ctext(d, (640, 222), "소화기", F(EB, 196), (252, 248, 240))
    ctext(d, (640, 380), "FIRE EXTINGUISHER", F(EB, 52), (252, 248, 240))
    return age(im, 1.2, 0.05, 5)


def wet_floor():
    W, H = 512, 1024  # 0.27 x 0.54 m
    Y = (238, 190, 40)
    im = Image.new("RGB", (W, H), Y)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 150), fill=(28, 26, 24))
    ctext(d, (W // 2, 78), "주 의", F(EB, 104), Y)
    tri = [(W // 2, 190), (W - 40, 560), (40, 560)]
    d.polygon(tri, fill=(28, 26, 24))
    d.polygon([(W // 2, 245), (W - 92, 528), (92, 528)], fill=Y)
    pic_slip(d, W // 2, 430, 210, (28, 26, 24))
    ctext(d, (W // 2, 660), "미끄럼", F(EB, 132), (28, 26, 24))
    ctext(d, (W // 2, 800), "주의", F(EB, 132), (28, 26, 24))
    ctext(d, (W // 2, 905), "바닥이 젖어 미끄럽습니다", fit(d, "바닥이 젖어 미끄럽습니다", B, 40, 440), (40, 36, 30))
    ctext(d, (W // 2, 968), "CAUTION  WET FLOOR", fit(d, "CAUTION  WET FLOOR", EB, 44, 440), (40, 36, 30))
    im = age(im, 1.6, 0.0, 9)
    # 바닥 쪽 신발 자국/먼지
    a = np.asarray(im).astype(np.float32)
    yy = np.linspace(0, 1, H)[:, None, None]
    a *= 1 - 0.18 * np.clip((yy - 0.8) / 0.2, 0, 1)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def napkin():
    W, H = 512, 256  # 0.08 x 0.04 m
    im = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(im)
    rrect(d, (6, 6, W - 6, H - 6), 24, outline=RED, width=8)
    ctext(d, (W // 2, 96), "냅킨", F(EB, 110), RED)
    ctext(d, (W // 2, 176), "NAPKIN", F(EB, 34), BROWN)
    ctext(d, (W // 2, 218), "필요한 만큼만 사용해 주세요", fit(d, "필요한 만큼만 사용해 주세요", B, 30, 440), BROWN)
    return age(im, 1.4, 0.1, 11)


def plant_ribbon():
    W, H = 256, 1024  # 리본 2줄 (각 0.05 x 0.40 m)
    im = Image.new("RGB", (W, H), (168, 22, 30))
    a = np.asarray(im).astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W]
    sheen = 0.88 + 0.16 * np.sin(yy / 23.0 + xx / 40.0) ** 2   # 공단 광택 주름
    a *= sheen[..., None]
    a = a * 0.8 + np.array([214, 120, 130]) * 0.2 * (yy / H)[..., None]  # 위쪽은 덜, 아래로 햇빛 바램
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    gold = (236, 196, 96)
    for x0, chars, f, top, step in ((0, "祝開業", F(MJ, 96), 150, 230),
                                    (128, "큰길시장상인회일동", F(SD, 78, 6), 70, 104)):
        d.line((x0 + 8, 0, x0 + 8, H), fill=gold, width=3)
        d.line((x0 + 119, 0, x0 + 119, H), fill=gold, width=3)
        for i, ch in enumerate(chars):
            ctext(d, (x0 + 64, top + i * step), ch, f, gold)
    return age(im, 1.0, 0.0, 13)


if __name__ == "__main__":
    asset, out = sys.argv[1], sys.argv[2]
    fn = {"StoreTrashStation": trash_station, "StoreExtinguisherSign": ext_sign, "StoreWetFloorSign": wet_floor,
          "StoreNapkinDispenser": napkin, "StorePlant": plant_ribbon}[asset]
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fn().save(out)
    print("labels:", out)
