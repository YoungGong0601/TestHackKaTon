"""CityBus 2D 텍스처 (Pillow): 노선 LED 표지(동적 자리표시) + 데칼 아틀라스(광고·번호판·스티커).

실행: <venv>/bin/python CityBus_tex.py <출력폴더>   (CityBus.py 가 자동으로 부른다)
결과: T_CityBus_RouteSign.png (2048x384, M_Dyn), T_CityBus_Decals.png (2048x2048 RGBA, 알파 클립)
아틀라스 영역(px, 좌상단 기준)은 REGIONS 에 있고 CityBus.py 가 같은 값을 쓴다.
"""
import os, sys, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

HOME = os.path.expanduser("~")
HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.abspath(os.path.join(HERE, "..", "..", ".."))           # ArtSource
FONTS = os.path.join(ART, "_cache", "fonts")
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"                      # index 6 Bold, 14 ExtraBold
NSQ_EB = os.path.join(HOME, "Library/Fonts/NanumSquareEB.ttf")
NSQ_B = os.path.join(HOME, "Library/Fonts/NanumSquareB.ttf")
BHS = os.path.join(FONTS, "BlackHanSans-Regular.ttf")
DOH = os.path.join(FONTS, "DoHyeon-Regular.ttf")
BURGER = os.path.join(ART, "_ref", "img", "burger_bulgogi.png")

# 데칼 아틀라스 영역 (x0, y0, x1, y1)
REGIONS = {
    "ad_burger": (0, 0, 2048, 512),
    "ad_civic": (0, 512, 2048, 1024),
    "plate": (0, 1024, 512, 1280),
    "placard": (512, 1024, 1024, 1280),
    "company": (1024, 1024, 2048, 1280),
    "lowfloor": (0, 1280, 256, 1536),
    "cng": (256, 1280, 512, 1536),
    "board": (512, 1280, 1024, 1536),
    "alight": (1024, 1280, 1536, 1536),
    "lean": (1536, 1280, 1792, 1536),
    "hand": (1792, 1280, 2048, 1536),
}


def font(path, size, index=0):
    return ImageFont.truetype(path, int(size), index=index)


def fit(text, path, max_w, max_h, index=0):
    """max_w x max_h 안에 들어가는 가장 큰 폰트."""
    s = int(max_h)
    while s > 6:
        f = font(path, s, index)
        b = f.getbbox(text)
        if b[2] - b[0] <= max_w and b[3] - b[1] <= max_h:
            return f
        s -= 2
    return font(path, 6, index)


def text(d, xy, s, f, fill, anchor="mm", **kw):
    d.text(xy, s, font=f, fill=fill, anchor=anchor, **kw)


def grain(im, amount=6, seed=1):
    """인쇄물 미세 노이즈."""
    rng = np.random.default_rng(seed)
    a = np.asarray(im).astype(np.int16)
    n = rng.normal(0, amount, a.shape[:2])[..., None]
    a[..., :3] = np.clip(a[..., :3] + n, 0, 255)
    return Image.fromarray(a.astype(np.uint8), im.mode)


def fade(im, k=0.12, warm=(255, 240, 210)):
    """햇빛 바램: 채도/대비를 조금 낮추고 따뜻한 빛으로."""
    a = np.asarray(im).astype(np.float32)
    rgb = a[..., :3]
    g = rgb.mean(-1, keepdims=True)
    rgb = rgb * (1 - k) + (g * 0.6 + np.array(warm) * 0.4) * k
    a[..., :3] = rgb
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), im.mode)


# ---------------------------------------------------------------- 노선 LED (동적)

def route_sign(path, num="112", line1="시장입구", line2="↔ 종합병원", cols=256, rows=48, cell=8, blur=False):
    """LED 도트 매트릭스. cols x rows 해상도로 글자를 찍고 점마다 둥근 LED 를 그린다."""
    lit = Image.new("L", (cols, rows), 0)
    d = ImageDraw.Draw(lit)
    fn = fit(num, NSQ_EB, cols * 0.34, rows * 0.86)
    text(d, (cols * 0.19, rows * 0.5), num, fn, 255)
    f1 = fit(line1, SD, cols * 0.56, rows * 0.40, 14)
    f2 = fit(line2, SD, cols * 0.56, rows * 0.40, 14)
    text(d, (cols * 0.69, rows * 0.27), line1, f1, 255)
    text(d, (cols * 0.69, rows * 0.74), line2, f2, 255)
    m = (np.asarray(lit) > 110)
    W, H = cols * cell, rows * cell
    on = Image.new("RGB", (W, H), (0, 0, 0))
    do = ImageDraw.Draw(on)
    off = Image.new("RGB", (W, H), (10, 9, 8))
    df = ImageDraw.Draw(off)
    r = cell * 0.36
    for y in range(rows):
        for x in range(cols):
            cx, cy = x * cell + cell / 2, y * cell + cell / 2
            box = (cx - r, cy - r, cx + r, cy + r)
            if m[y, x]:
                c = (255, 168, 40) if x < cols * 0.37 else (255, 140, 30)
                do.ellipse(box, fill=c)
            else:
                df.ellipse(box, fill=(26, 22, 18))
    if blur:   # 할아버지 눈에 번호가 번져 보이는 버전: 번호 칸의 불빛만 흐리고 LED 판은 그대로
        bx = (0, 0, int(W * 0.37), H)
        on.paste(on.crop(bx).filter(ImageFilter.GaussianBlur(cell * 2.2)).point(lambda v: min(255, int(v * 1.8))), bx[:2])
    glow = on.filter(ImageFilter.GaussianBlur(cell * 0.9))
    a = np.asarray(off).astype(np.float32) + np.asarray(on).astype(np.float32) + np.asarray(glow).astype(np.float32) * 0.55
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(path)


# ---------------------------------------------------------------- 데칼 아틀라스

def crown(d, cx, cy, s, fill=(240, 198, 58)):
    pts = [(-30, -48), (-34, -82), (-14, -62), (0, -90), (14, -62), (34, -82), (30, -48)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in pts], fill=fill)


def logo(im, cx, cy, s, dark=False):
    """버거대왕 로고 (프로토타입 캔버스 로고를 그대로 옮김: 번 + 패티 + 왕관 + 글자)."""
    d = ImageDraw.Draw(im)
    crown(d, cx, cy, s)
    d.chord((cx - 62 * s, cy - 52 * s, cx + 62 * s, cy + 36 * s), 180, 360, fill=(217, 138, 43))
    d.rectangle((cx - 60 * s, cy - 6 * s, cx + 60 * s, cy + 10 * s), fill=(107, 58, 30))
    d.rounded_rectangle((cx - 58 * s, cy + 12 * s, cx + 58 * s, cy + 34 * s), 8 * s, fill=(217, 138, 43))
    f = font(BHS, 50 * s)
    text(d, (cx, cy + 72 * s), "버거대왕", f, (58, 36, 22) if dark else (200, 41, 31))


def ad_burger(W=2048, H=512):
    im = Image.new("RGBA", (W, H), (246, 236, 214, 255))
    d = ImageDraw.Draw(im)
    # 배경: 크림 -> 오른쪽 따뜻한 오렌지 그라데이션
    for x in range(W):
        t = x / W
        d.line([(x, 0), (x, H)], fill=(int(247 - 8 * t), int(236 - 40 * t), int(214 - 90 * t), 255))
    # 왼쪽 빨간 원 + 방사선
    cx, cy = 300, 270
    for i in range(24):
        a0 = i * math.pi * 2 / 24
        d.polygon([(cx, cy), (cx + 700 * math.cos(a0), cy + 700 * math.sin(a0)),
                   (cx + 700 * math.cos(a0 + 0.13), cy + 700 * math.sin(a0 + 0.13))], fill=(236, 214, 170, 255))
    d.ellipse((cx - 235, cy - 235, cx + 235, cy + 235), fill=(196, 44, 30, 255))
    b = Image.open(BURGER).convert("RGBA").resize((470, 470), Image.LANCZOS)
    sh = Image.new("RGBA", b.size, (0, 0, 0, 0))
    sh.putalpha(b.getchannel("A").point(lambda v: int(v * 0.45)))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)), (cx - 235 + 14, cy - 235 + 22))
    im.alpha_composite(b, (cx - 235, cy - 245))
    # 신메뉴 배지
    d.ellipse((470, 40, 640, 210), fill=(240, 198, 58, 255), outline=(150, 30, 20, 255), width=6)
    text(d, (555, 108), "신메뉴", font(BHS, 46), (150, 30, 20))
    text(d, (555, 158), "NEW", font(NSQ_EB, 36), (150, 30, 20))
    # 본문
    text(d, (690, 118), "시장 입구에서 만나는", font(SD, 54, 14), (110, 60, 30), anchor="lm")
    text(d, (684, 250), "불고기 버거 세트", fit("불고기 버거 세트", BHS, 860, 150), (88, 40, 18), anchor="lm")
    d.rounded_rectangle((690, 372, 1530, 440), 34, fill=(88, 40, 18, 255))
    text(d, (1110, 406), "키오스크로 주문하면 더 빠르고 간편하게!", font(SD, 40, 14), (255, 243, 214))
    # 로고 + 가격
    logo(im, 1810, 120, 1.05, dark=False)
    d = ImageDraw.Draw(im)
    text(d, (1810, 236), "시장입구점", font(SD, 30, 14), (110, 60, 30))
    text(d, (1810, 330), "6,900원", font(BHS, 84), (196, 44, 30))
    text(d, (1810, 398), "(세트 기준 · 음료 변경 가능)", font(SD, 24, 6), (110, 70, 40))
    # 작은 글씨
    text(d, (690, 488), "※ 이미지는 연출된 것으로 실제와 다를 수 있습니다.  ※ 일부 매장 제외.", font(SD, 22, 2), (120, 90, 60), anchor="lm")
    text(d, (2010, 488), "매일 10:00 - 22:00", font(SD, 24, 6), (120, 90, 60), anchor="rm")
    return fade(grain(im, 5, 2), 0.10)


def person(d, x, y, s, col, cane=False):
    d.ellipse((x - 26 * s, y - 150 * s, x + 26 * s, y - 98 * s), fill=col)
    d.rounded_rectangle((x - 34 * s, y - 92 * s, x + 34 * s, y + 10 * s), 22 * s, fill=col)
    d.rectangle((x - 30 * s, y, x - 6 * s, y + 90 * s), fill=col)
    d.rectangle((x + 6 * s, y, x + 30 * s, y + 90 * s), fill=col)
    if cane:
        d.line((x + 58 * s, y - 40 * s, x + 70 * s, y + 92 * s), fill=col, width=int(9 * s))
        d.line((x + 30 * s, y - 60 * s, x + 58 * s, y - 40 * s), fill=col, width=int(14 * s))


def ginkgo(d, cx, cy, r, fill):
    d.pieslice((cx - r, cy - r * 0.6, cx + r, cy + r * 1.4), 205, 335, fill=fill)
    d.polygon([(cx - 7, cy + r * 0.3), (cx + 7, cy + r * 0.3), (cx + 4, cy + r * 0.85), (cx - 4, cy + r * 0.85)], fill=fill)
    d.polygon([(cx - 14, cy - r * 0.62), (cx + 14, cy - r * 0.62), (cx, cy - r * 0.1)], fill=(232, 240, 252, 255))


def ad_civic(W=2048, H=512):
    im = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(238 - 20 * t), int(246 - 12 * t), 255, 255))
    d.rectangle((0, 0, 560, H), fill=(32, 78, 140, 255))
    # 키오스크 + 어르신 픽토그램
    d.rounded_rectangle((300, 90, 470, 430), 18, fill=(235, 242, 250, 255))
    d.rectangle((318, 112, 452, 300), fill=(120, 190, 240, 255))
    for i in range(3):
        for j in range(2):
            d.rectangle((328 + j * 64, 122 + i * 58, 382 + j * 64, 170 + i * 58), fill=(250, 250, 250, 255))
    d.rectangle((350, 330, 420, 342), fill=(60, 60, 60, 255))
    person(d, 170, 330, 1.55, (255, 214, 120, 255), cane=True)
    text(d, (630, 120), "어르신 디지털 배움터", font(BHS, 104), (24, 60, 120), anchor="lm")
    text(d, (634, 250), "키오스크 · 스마트폰 사용법 무료 교육", font(SD, 64, 14), (40, 40, 48), anchor="lm")
    text(d, (634, 340), "매주 화 · 목 오후 2시  |  은행골 주민센터 2층 교육장", font(SD, 40, 6), (70, 80, 96), anchor="lm")
    d.rounded_rectangle((634, 395, 1250, 465), 35, fill=(24, 60, 120, 255))
    text(d, (942, 430), "신청 · 문의  ☎ 02-120", font(SD, 40, 14), (255, 255, 255))
    ginkgo(d, 1840, 230, 120, (226, 178, 30, 255))
    text(d, (1840, 400), "은행골구", font(BHS, 64), (24, 60, 120))
    text(d, (1290, 430), "누구나 쉽게, 천천히 배워요", font(SD, 36, 6), (90, 100, 120), anchor="lm")
    return fade(grain(im, 4, 3), 0.14)


def plate(W=512, H=256):
    im = Image.new("RGBA", (W, H), (238, 196, 34, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, W - 7, H - 7), 18, outline=(30, 26, 20, 255), width=8)
    for x in (70, W - 70):
        d.ellipse((x - 11, 26, x + 11, 48), fill=(150, 150, 140, 255), outline=(80, 70, 40, 255), width=3)
    top = Image.new("L", (W, H), 0)
    dt = ImageDraw.Draw(top)
    text(dt, (W / 2, 62), "서울 74", fit("서울 74", SD, 230, 64, 14), 255)
    text(dt, (W / 2, 168), "사 3112", fit("사 3112", SD, 470, 150, 14), 255)
    im.paste((24, 22, 18, 255), (0, 0), top)
    # 볼트 주변 녹물, 아래 먼지
    a = np.asarray(im).astype(np.float32)
    yy = np.linspace(0, 1, H)[:, None]
    a[..., :3] *= (1 - 0.18 * yy ** 3)[..., None]
    return grain(Image.fromarray(a.astype(np.uint8), "RGBA"), 7, 4)


def placard(W=512, H=256):
    im = Image.new("RGBA", (W, H), (240, 236, 222, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 54), fill=(28, 92, 170, 255))
    text(d, (20, 28), "간선", font(SD, 34, 14), (255, 255, 255), anchor="lm")
    text(d, (W - 18, 28), "시민교통", font(SD, 26, 6), (220, 230, 245), anchor="rm")
    text(d, (W / 2, 136), "112", fit("112", NSQ_EB, 300, 120), (28, 92, 170))
    text(d, (W / 2, 222), "시장입구 ↔ 종합병원", font(SD, 34, 14), (40, 40, 40))
    im = fade(im, 0.25, (255, 230, 170))
    return grain(im, 6, 5)


def company(W=1024, H=256):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    text(d, (30, 128), "시민교통(주)", fit("시민교통(주)", NSQ_EB, 640, 140), (250, 250, 248, 255), anchor="lm")
    d.rectangle((706, 78, 714, 178), fill=(250, 250, 248, 255))
    text(d, (740, 128), "112-07", fit("112-07", NSQ_B, 260, 80), (250, 250, 248, 255), anchor="lm")
    return im


def wheelchair(d, cx, cy, s, col):
    d.ellipse((cx - 14 * s, cy - 78 * s, cx + 14 * s, cy - 50 * s), fill=col)
    d.line((cx - 6 * s, cy - 44 * s, cx - 10 * s, cy + 6 * s), fill=col, width=int(16 * s))
    d.line((cx - 10 * s, cy + 6 * s, cx + 30 * s, cy + 6 * s), fill=col, width=int(14 * s))
    d.line((cx + 30 * s, cy + 6 * s, cx + 46 * s, cy + 46 * s), fill=col, width=int(14 * s))
    d.line((cx - 8 * s, cy - 22 * s, cx + 26 * s, cy - 22 * s), fill=col, width=int(12 * s))
    d.arc((cx - 58 * s, cy - 24 * s, cx + 22 * s, cy + 56 * s), 60, 300, fill=col, width=int(11 * s))


def sticker_lowfloor(S=256):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, S - 6, S - 6), 26, fill=(26, 92, 172, 255), outline=(255, 255, 255, 255), width=6)
    wheelchair(d, S / 2 - 6, S / 2 - 6, 1.35, (255, 255, 255, 255))
    text(d, (S / 2, S - 38), "저상버스", font(BHS, 40), (255, 255, 255))
    return im


def sticker_cng(S=256):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = S / 2
    d.polygon([(c, 8), (S - 8, c), (c, S - 8), (8, c)], fill=(255, 255, 255, 255))
    d.polygon([(c, 24), (S - 24, c), (c, S - 24), (24, c)], fill=(20, 96, 170, 255))
    text(d, (c, c), "CNG", font(NSQ_EB, 64), (255, 255, 255))
    return im


def sticker_door(label, sub, col, W=512, H=256):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((6, 6, W - 6, H - 6), 40, fill=col + (255,), outline=(255, 255, 255, 255), width=8)
    text(d, (W / 2, H * 0.42), label, font(BHS, 104), (255, 255, 255))
    text(d, (W / 2, H * 0.80), sub, font(SD, 34, 6), (255, 255, 255))
    return im


def sticker_lean(S=256):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((6, 6, S - 6, S - 6), fill=(255, 255, 255, 255), outline=(206, 38, 30, 255), width=18)
    text(d, (S / 2, S * 0.38), "문에", font(SD, 54, 14), (30, 30, 30))
    text(d, (S / 2, S * 0.62), "기대지 마세요", fit("기대지 마세요", SD, S * 0.66, 40, 14), (206, 38, 30))
    return im


def sticker_hand(S=256):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(S / 2, 10), (S - 10, S - 40), (10, S - 40)], fill=(250, 204, 20, 255), outline=(20, 20, 20, 255))
    d.line([(S / 2, 22), (S - 26, S - 50), (26, S - 50), (S / 2, 22)], fill=(20, 20, 20, 255), width=10, joint="curve")
    text(d, (S / 2, S * 0.56), "!", font(NSQ_EB, 96), (20, 20, 20))
    d.rounded_rectangle((20, S - 46, S - 20, S - 4), 10, fill=(20, 20, 20, 255))
    text(d, (S / 2, S - 25), "손 끼임 주의", font(SD, 28, 14), (250, 204, 20))
    return im


def decals(path):
    at = Image.new("RGBA", (2048, 2048), (0, 0, 0, 0))
    items = {
        "ad_burger": ad_burger(), "ad_civic": ad_civic(), "plate": plate(), "placard": placard(),
        "company": company(), "lowfloor": sticker_lowfloor(), "cng": sticker_cng(),
        "board": sticker_door("앞문 승차", "교통카드를 찍어 주세요", (34, 128, 72)),
        "alight": sticker_door("뒷문 하차", "내리실 때도 카드를 찍어 주세요", (200, 62, 40)),
        "lean": sticker_lean(), "hand": sticker_hand(),
    }
    for k, im in items.items():
        x0, y0, x1, y1 = REGIONS[k]
        assert im.size == (x1 - x0, y1 - y0), (k, im.size)
        at.alpha_composite(im, (x0, y0))
    at.save(path, optimize=True)


# ---------------------------------------------------------------- 유리 먼지 (월드 UV 1.5m 타일)

def _tile_noise(S, sx, sy, rng):
    """주기 경계(이음매 없는) 가우시안 필터 노이즈 0..1. sx/sy = 가로/세로 흐림(px)."""
    fy, fx = np.fft.fftfreq(S)[:, None], np.fft.fftfreq(S)[None, :]
    g = np.exp(-2 * np.pi ** 2 * (fx ** 2 * sx ** 2 + fy ** 2 * sy ** 2))
    r = np.real(np.fft.ifft2(np.fft.fft2(rng.normal(size=(S, S))) * g))
    return (r - r.min()) / (r.max() - r.min())


def glass_dirt(path, S=1024, seed=7):
    """RGB = 유리 색(먼지 낀 곳은 밝은 회갈색), A = 상대 불투명도(0.8~1, 머티리얼 알파와 곱함).
    먼지막 + 세로 빗물 줄 + 마른 물방울 자국 + 손·머리 기름 얼룩."""
    rng = np.random.default_rng(seed)
    dust = np.clip((_tile_noise(S, 45, 45, rng) * 0.6 + _tile_noise(S, 9, 9, rng) * 0.4 - 0.5) / 0.3, 0, 1) ** 1.6
    streak = np.clip((_tile_noise(S, 1.6, 70, rng) - 0.58) / 0.2, 0, 1) * np.clip(_tile_noise(S, 30, 30, rng) * 1.6 - 0.4, 0, 1)
    spots = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(spots)
    for _ in range(260):                       # 마른 물방울: 가장자리가 진한 고리
        x, y, r = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(1.0, 4.0) * (1 + 1.5 * (rng.random() < 0.06))
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                bb = (x + ox - r, y + oy - r, x + ox + r, y + oy + r * 1.15)
                d.ellipse(bb, fill=25, outline=110, width=1)
    spots = np.asarray(spots.filter(ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    smudge = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(smudge)
    for _ in range(9):                         # 손바닥·이마 기름 얼룩 (지문 결은 고리로)
        x, y, r = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(25, 70)
        for k in range(int(r / 5)):
            rr = r * (1 - k / (r / 5))
            for ox in (-S, 0, S):
                for oy in (-S, 0, S):
                    d.ellipse((x + ox - rr, y + oy - rr * 0.8, x + ox + rr, y + oy + rr * 0.8), outline=70 + k * 6, width=2)
    smudge = np.asarray(smudge.filter(ImageFilter.GaussianBlur(3)), np.float32) / 255
    f = np.clip(dust * 0.42 + streak * 0.36 + spots * 0.5 + smudge * 0.5, 0, 1)
    base, dirt = np.array([40, 48, 54], np.float32), np.array([150, 142, 128], np.float32)
    rgb = base + (dirt - base) * (f[..., None] * 0.7)
    a = 0.8 + 0.2 * f
    im = np.dstack([rgb, a * 255]).clip(0, 255).astype(np.uint8)
    Image.fromarray(im, "RGBA").save(path, optimize=True)


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else HERE
    os.makedirs(out, exist_ok=True)
    route_sign(os.path.join(out, "T_CityBus_RouteSign.png"))
    for nm, bl in (("2413", False), ("2413_Blur", True)):   # 놓치는 버스 (초록 지선 2413) 자리표시
        route_sign(os.path.join(out, f"T_CityBus_RouteSign_{nm}.png"), "2413", "은행골 입구", "↔ 차고지", blur=bl)
    decals(os.path.join(out, "T_CityBus_Decals.png"))
    glass_dirt(os.path.join(out, "T_CityBus_GlassDirt.png"))
    print("CityBus_tex: ok", out)
