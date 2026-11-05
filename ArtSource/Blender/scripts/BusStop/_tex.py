#!/usr/bin/env python3
"""버스정류장 그룹 2D 텍스처 (Pillow + numpy).

사용: python -I _tex.py <Asset> <ART 루트(Assets/Art3D)> <CACHE>
- 에셋 PNG -> <ART>/Textures/<Asset>/T_<Asset>_*.png
- 데칼 배치표(아틀라스 UV 사각형, 실제 크기 m) -> <CACHE>/busstop/<Asset>.json
글자 내용·색은 프로토타입(prototype_app.js 모듈 Kd) 그대로.
"""
import sys, os, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ASSET, ART, CACHE = sys.argv[1], sys.argv[2], sys.argv[3]
OUT = os.path.join(ART, "Textures", ASSET)
LAY = os.path.join(CACHE, "busstop")
os.makedirs(OUT, exist_ok=True)
os.makedirs(LAY, exist_ok=True)
HOME = os.path.expanduser("~")
FD = {"eb": HOME + "/Library/Fonts/NanumSquareEB.ttf", "b": HOME + "/Library/Fonts/NanumSquareB.ttf",
      "r": HOME + "/Library/Fonts/NanumSquareR.ttf", "l": HOME + "/Library/Fonts/NanumSquareL.ttf",
      "bhs": CACHE + "/fonts/BlackHanSans-Regular.ttf", "pen": CACHE + "/fonts/NanumPenScript-Regular.ttf",
      "doh": CACHE + "/fonts/DoHyeon-Regular.ttf"}
_fc = {}
random.seed(14208)
RNG = np.random.default_rng(14208)

# 프로토타입 색
K = (255, 138, 30)          # BIS 주황 LED
YEL = (255, 210, 74)        # 112 강조
GRN = (127, 208, 138)       # BIS 헤더
BLU = (127, 178, 216)       # BIS 상단선
NAVY = (44, 93, 143)        # #2c5d8f 노선 112 / 정류장 이름판
GREEN = (62, 122, 88)       # #3e7a58 노선 2413
RED = (180, 41, 31)         # #b4291f 노선 7
PAPER = (230, 227, 216)     # #e6e3d8 노선도 바탕
ROUTES = [("112", NAVY, "간선", ["은행골 입구", "동사무소", "우체국", "시장 입구", "종합병원"]),
          ("2413", GREEN, "지선", ["은행골 입구", "차고지", "체육공원", "구청", "역 앞"]),
          ("7", RED, "마을", ["은행골 입구", "중학교", "종합병원", "터미널", "시청"])]
# 촘촘한 노선도용 (프로토타입 정류장 사이에 실제처럼 정류장을 더 끼움)
LONG = {
    "112": ["은행골차고지", "은행골 입구", "은행골아파트", "동사무소", "새마을금고", "우체국", "중앙초교",
            "시장 입구", "시장 공영주차장", "삼거리", "보건소", "종합병원", "종합병원 응급실", "구 터미널"],
    "2413": ["은행골 입구", "은행골 경로당", "차고지", "산림욕장 입구", "체육공원", "구민회관", "구청",
             "구청 별관", "법원 사거리", "역 앞", "역 광장", "환승센터"],
    "7": ["은행골 입구", "중학교", "은행골 성당", "약수터 입구", "종합병원", "재래시장 뒷길", "터미널",
          "시청 별관", "시청"],
}


def F(k, size):
    key = (k, max(6, int(size)))
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FD[k], key[1])
    return _fc[key]


def T(d, xy, s, k, size, fill, anchor="la", max_w=None, **kw):
    """글자 쓰기 (max_w 를 넘으면 줄여서 맞춤). 쓴 폭을 돌려준다."""
    f = F(k, size)
    if max_w:
        while d.textlength(s, font=f) > max_w and size > 7:
            size *= 0.94
            f = F(k, size)
    d.text(xy, s, font=f, fill=fill, anchor=anchor, **kw)
    return d.textlength(s, font=f)


def fbm(h, w, scale=64.0, octv=5, seed=0):
    """값 노이즈 fBm (0..1)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for _ in range(octv):
        gh, gw = max(2, int(h / scale) + 2), max(2, int(w / scale) + 2)
        g = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
        out += np.asarray(g.resize((w, h), Image.BICUBIC), np.float32) / 255 * amp
        tot += amp
        amp *= 0.5
        scale = max(1.0, scale / 2)
    return np.clip(out / tot, 0, 1)


def arr(im):
    return np.asarray(im.convert("RGB"), np.float32) / 255


def img(a, mode="RGB"):
    return Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), mode)


def weather(im, amount=0.25, seed=1, fade=0.08):
    """인쇄물 바램·얼룩·먼지 (흰 종이에 빛바램 + 가장자리 때)."""
    a = arr(im)
    h, w = a.shape[:2]
    n = fbm(h, w, max(h, w) / 6, 5, seed)
    spots = np.clip((fbm(h, w, 60, 3, seed + 7) - 0.7) * 2.5, 0, 1)
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.clip(1 - np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / (0.06 * min(h, w)), 0, 1)
    a = a * (1 - fade) + fade * np.array([0.93, 0.91, 0.84])          # 햇빛 바램
    dirt = np.clip(amount * (0.35 * n + 0.5 * spots + 0.6 * edge * n), 0, 0.6)[..., None]
    a = a * (1 - dirt) + dirt * np.array([0.33, 0.29, 0.22])
    return img(a)


def save(im, name):
    p = os.path.join(OUT, f"T_{ASSET}_{name}.png")
    im.save(p, optimize=True)
    print("tex:", p, im.size)
    return p


def bus_icon(d, cx, cy, s, fg, bg):
    """버스 정면 픽토그램 (s = 높이 px)."""
    w = s * 0.78
    d.rounded_rectangle((cx - w / 2, cy - s / 2, cx + w / 2, cy + s * 0.38), radius=s * 0.12, fill=fg)
    d.rounded_rectangle((cx - w * 0.4, cy - s * 0.36, cx + w * 0.4, cy + s * 0.02), radius=s * 0.05, fill=bg)
    d.rectangle((cx - w * 0.3, cy - s * 0.46, cx + w * 0.3, cy - s * 0.41), fill=bg)
    for sx in (-1, 1):
        d.ellipse((cx + sx * w * 0.3 - s * 0.055, cy + s * 0.15, cx + sx * w * 0.3 + s * 0.055, cy + s * 0.26), fill=bg)
        d.rounded_rectangle((cx + sx * w * 0.33 - s * 0.07, cy + s * 0.36, cx + sx * w * 0.33 + s * 0.07, cy + s * 0.5),
                            radius=s * 0.02, fill=fg)
        d.rectangle((cx + sx * (w / 2 + s * 0.02) - s * 0.025, cy - s * 0.32, cx + sx * (w / 2 + s * 0.02) + s * 0.025,
                     cy - s * 0.12), fill=fg)


def qr(d, x, y, size, seed=3):
    """QR 코드 모양 (실제 코드 아님)."""
    n = 25
    m = size / n
    rng = random.Random(seed)
    d.rectangle((x - m, y - m, x + size + m, y + size + m), fill=(255, 255, 255))
    for i in range(n):
        for j in range(n):
            if rng.random() < 0.5:
                d.rectangle((x + i * m, y + j * m, x + (i + 1) * m, y + (j + 1) * m), fill=(20, 20, 20))
    for fx, fy in ((0, 0), (n - 7, 0), (0, n - 7)):
        X, Y = x + fx * m, y + fy * m
        d.rectangle((X, Y, X + 7 * m, Y + 7 * m), fill=(20, 20, 20))
        d.rectangle((X + m, Y + m, X + 6 * m, Y + 6 * m), fill=(255, 255, 255))
        d.rectangle((X + 2 * m, Y + 2 * m, X + 5 * m, Y + 5 * m), fill=(20, 20, 20))


def logo(d, cx, cy, s, text=True, dark=False):
    """버거대왕 로고 (프로토타입 Rn: 왕관 + 번 + 글자). s = 배율 (1 = 프로토타입 px)."""
    P = lambda x, y: (cx + x * s, cy + y * s)
    d.pieslice((cx - 62 * s, cy - 52 * s, cx + 62 * s, cy + 36 * s), 180, 360, fill=(217, 138, 43))
    d.rectangle((*P(-60, -6), *P(60, 10)), fill=(107, 58, 30))
    d.rounded_rectangle((*P(-58, 12), *P(58, 34)), radius=8 * s, fill=(217, 138, 43))
    d.polygon([P(-30, -48), P(-34, -82), P(-14, -62), P(0, -90), P(14, -62), P(34, -82), P(30, -48)], fill=(240, 198, 58))
    if text:
        T(d, P(0, 72), "버거대왕", "bhs", 54 * s, (58, 36, 22) if dark else (200, 41, 31), anchor="mm")


# ------------------------------------------------------------------ 데칼 아틀라스

class Atlas:
    """선반 패킹 데칼 아틀라스. add(key, w_m, h_m, ppm, draw) -> draw(d, im, W, H) 로 그림."""

    def __init__(self, size=2048):
        self.S = size
        self.im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        self.x = self.y = 4
        self.row = 0
        self.rects = {}

    def add(self, key, w_m, h_m, ppm, draw, wrap=False):
        W, H = max(8, int(w_m * ppm)), max(8, int(h_m * ppm))
        if self.x + W + 4 > self.S:
            self.x, self.y, self.row = 4, self.y + self.row + 6, 0
        if self.y + H > self.S:
            raise RuntimeError(f"atlas full at {key}")
        tile = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw(ImageDraw.Draw(tile), tile, W, H)
        self.im.alpha_composite(tile, (self.x, self.y))
        S = self.S
        # UV: v 는 아래에서 위로
        self.rects[key] = {"uv": [self.x / S, 1 - (self.y + H) / S, (self.x + W) / S, 1 - self.y / S],
                           "w": w_m, "h": h_m}
        self.x += W + 6
        self.row = max(self.row, H)

    def save(self, extra=None):
        p = save(self.im, "Decals")
        data = {"decals": self.rects}
        data.update(extra or {})
        json.dump(data, open(os.path.join(LAY, ASSET + ".json"), "w"), ensure_ascii=False, indent=1)
        return p


def sticker_bg(im, W, H, col=(250, 250, 246), rad=0.06, wear=0.35, seed=0):
    """스티커 바탕 (둥근 모서리 + 바램 + 가장자리 들뜸)."""
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W - 1, H - 1), radius=int(min(W, H) * rad), fill=col + (255,))
    return d


def finish_sticker(im, wear=0.3, seed=0, tear=0.0):
    """스티커 마감: 바램/때 + (tear>0 이면) 찢긴 가장자리 알파."""
    a = np.asarray(im, np.float32) / 255
    h, w = a.shape[:2]
    rgb = np.asarray(weather(img(a[..., :3]), wear, seed, 0.1), np.float32) / 255
    al = a[..., 3]
    if tear > 0:
        n = fbm(h, w, 12, 4, seed + 3)
        yy, xx = np.mgrid[0:h, 0:w]
        e = np.minimum(np.minimum(xx, w - 1 - xx), np.minimum(yy, h - 1 - yy)) / (tear * min(h, w))
        al = al * (e + (n - 0.5) * 1.6 > 0.55)
        holes = fbm(h, w, 30, 3, seed + 9) > 0.7 + 0.25 * (1 - tear)
        al = al * ~holes
    out = np.dstack([rgb, al])
    im.paste(img(out, "RGBA"))


# ------------------------------------------------------------------ BIS

def led_board(rows, header, name, W=2048, H=846, GX=224, GY=92, sharp=True):
    """주황 LED 도트 전광판. sharp=True: 돋보기(lens) 글자 / False: 돋보기 밖(base) = 막대 + 흐림 (프로토타입 ye())."""
    SS = 8
    u = SS
    lo = Image.new("RGB", (GX * SS, GY * SS), 0)
    d = ImageDraw.Draw(lo)
    T(d, (4 * u, 10 * u), header if sharp else "은행골 입구", "eb", 15 * u, GRN, anchor="lm", max_w=150 * u)
    d.rectangle((0, 0, GX * u, 1 * u - 1), fill=BLU)                    # 상단 파란 선 (#7fb2d8)
    d.rectangle((2 * u, 19 * u, (GX - 2) * u, 20 * u - 1), fill=(60, 90, 120))
    for i, (num, dest, eta) in enumerate(rows):
        cy = (32.5 + i * 23) * u
        if sharp:
            T(d, (4 * u, cy), num, "eb", 22 * u, YEL if num == "112" else K, anchor="lm", max_w=54 * u)
            T(d, (62 * u, cy), dest, "eb", 20 * u, K, anchor="lm", max_w=88 * u)
            T(d, ((GX - 4) * u, cy), eta, "eb", 20 * u, K, anchor="rm", max_w=68 * u)
            continue
        x = 4                                                          # 글자 자리 막대 (프로토타입과 같은 의사난수 폭)
        for j in range(9):
            w = GX * (0.04 + (j * 37 + i * 11) % 7 * 0.012)
            if x + w > GX - 4:
                break
            d.rectangle((x * u, cy - 5 * u, (x + w) * u, cy + 5 * u), fill=K)
            x += w + GX * 0.035
    small = np.asarray(lo.resize((GX, GY), Image.BOX), np.float32) / 255
    cov = small.max(2)
    on = cov > 0.33
    col = small / np.maximum(cov, 1e-3)[..., None]
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    cx, cy = xs / (W / GX), ys / (H / GY)
    ix, iy = np.clip(cx.astype(int), 0, GX - 1), np.clip(cy.astype(int), 0, GY - 1)
    r = np.sqrt((cx - ix - 0.5) ** 2 + (cy - iy - 0.5) ** 2)
    dot = np.clip((0.40 - r) / 0.09, 0, 1)[..., None]
    core = np.clip((0.22 - r) / 0.22, 0, 1)[..., None]
    lit = on[iy, ix][..., None]
    c = col[iy, ix]
    led = np.where(lit, c * dot + core * 0.35 * (1 - c) * dot, 0)
    off = np.where(lit, 0, np.array([0.11, 0.06, 0.028]) * dot)
    glow = np.asarray(img(led).filter(ImageFilter.GaussianBlur(W / GX * 0.9)), np.float32) / 255
    bg = np.array([0.03, 0.026, 0.022]) * (0.8 + 0.4 * fbm(H, W, 200, 3, 5))[..., None]
    out = bg + off + led + glow * 0.55
    for x in range(0, GX, 32):                                           # LED 모듈 이음매
        out[:, int(x * W / GX)] *= 0.45
    for y in range(0, GY, 16):
        out[int(y * H / GY), :] *= 0.45
    im = img(out)
    return save(im if sharp else im.filter(ImageFilter.GaussianBlur(W * 9 / 768)), name)


def make_bis():
    rows0 = [["2413", "은행골", "곧 도착"], ["112", "시장입구", "6분"], ["7", "종합병원", "11분"]]
    rows1 = [["112", "시장입구", "곧 도착"], ["7", "종합병원", "9분"], ["2413", "은행골", "14분"]]
    for rows, nm in ((rows0, "Display"), (rows1, "Display_After")):
        led_board(rows, "은행골 입구 도착 안내", nm)
        led_board(rows, "은행골 입구 도착 안내", nm + "_Base", sharp=False)   # 돋보기 밖 (막대 + 흐림)
    A = Atlas(1024)

    def top(d, im, W, H):                                               # 상단 베젤 인쇄 글자
        T(d, (6, H / 2), "버스도착안내", "eb", H * 0.62, (236, 236, 232, 255), anchor="lm")
        T(d, (W - 6, H / 2), "BIS · 은행골구", "b", H * 0.5, (200, 205, 210, 255), anchor="rm")
    A.add("bezel_label", 0.62, 0.032, 1500, top)

    def pole(d, im, W, H):                                              # 기둥 고장신고 스티커
        sticker_bg(im, W, H)
        d.rectangle((0, 0, W, H * 0.22), fill=NAVY + (255,))
        T(d, (W / 2, H * 0.11), "버스정보안내기", "eb", H * 0.11, (255, 255, 255, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.34), "고장 신고", "b", H * 0.09, (30, 30, 30, 255), anchor="mm")
        T(d, (W / 2, H * 0.5), "☎ 120", "eb", H * 0.15, (200, 30, 30, 255), anchor="mm")
        T(d, (W / 2, H * 0.68), "은행골구청 교통행정과", "r", H * 0.065, (40, 40, 40, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.8), "관리번호 BIS-14208", "b", H * 0.065, (40, 40, 40, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.91), "02-2600-1234", "r", H * 0.06, (40, 40, 40, 255), anchor="mm")
        finish_sticker(im, 0.45, 2)
    A.add("pole_sticker", 0.085, 0.13, 2600, pole)

    def danger(d, im, W, H):                                            # 감전주의
        sticker_bg(im, W, H, (250, 205, 20), 0.04)
        d.polygon([(W / 2, H * 0.06), (W * 0.9, H * 0.62), (W * 0.1, H * 0.62)], fill=(20, 20, 20, 255))
        d.polygon([(W / 2, H * 0.16), (W * 0.8, H * 0.56), (W * 0.2, H * 0.56)], fill=(250, 205, 20, 255))
        d.polygon([(W * 0.53, H * 0.2), (W * 0.42, H * 0.42), (W * 0.52, H * 0.4), (W * 0.46, H * 0.55),
                   (W * 0.6, H * 0.33), (W * 0.5, H * 0.35)], fill=(20, 20, 20, 255))
        T(d, (W / 2, H * 0.74), "위험", "eb", H * 0.14, (20, 20, 20, 255), anchor="mm")
        T(d, (W / 2, H * 0.89), "감전주의", "b", H * 0.11, (20, 20, 20, 255), anchor="mm")
        finish_sticker(im, 0.5, 4)
    A.add("danger", 0.06, 0.075, 2600, danger)

    def maker(d, im, W, H):                                             # 제조사 명판 (작은 글씨)
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius=6, fill=(180, 182, 184, 255))
        d.rounded_rectangle((3, 3, W - 4, H - 4), radius=5, outline=(90, 90, 92, 255), width=2)
        for i, s in enumerate(["버스정보안내단말기 (LED 양면형)", "모델 KBIS-L1600D  ·  AC 220V 60Hz",
                               "제조 2019. 04  ·  S/N 14208-0172", "(주)한빛교통정보"]):
            T(d, (12, 10 + i * H * 0.23), s, "b", H * 0.15, (40, 40, 40, 255), anchor="la", max_w=W - 24)
        finish_sticker(im, 0.5, 6)
    A.add("maker_plate", 0.12, 0.05, 2600, maker)
    A.save()


# ------------------------------------------------------------------ 표지판

def make_sign():
    # 머리판 0.50 x 0.56 m (양면 공용)
    W, H = 1024, 1147
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((W * 0.27, H * 0.05, W * 0.73, H * 0.43), radius=40, fill=(245, 245, 240))
    bus_icon(d, W / 2, H * 0.235, H * 0.26, NAVY, (245, 245, 240))
    T(d, (W / 2, H * 0.395), "BUS STOP", "eb", 34, NAVY, anchor="mm")
    T(d, (W / 2, H * 0.53), "은행골 입구", "eb", 150, (245, 245, 240), anchor="mm", max_w=W * 0.92)
    T(d, (W / 2, H * 0.63), "Eunhaenggol Entrance", "b", 56, (205, 220, 235), anchor="mm", max_w=W * 0.9)
    d.rectangle((0, H * 0.71, W, H), fill=(245, 245, 240))
    T(d, (W * 0.06, H * 0.79), "정류소 번호", "b", 46, (60, 60, 60), anchor="lm")
    T(d, (W * 0.94, H * 0.79), "14-208", "eb", 96, NAVY, anchor="rm")
    T(d, (W * 0.06, H * 0.91), "다음 정류장  ▶  동사무소 · 차고지 · 중학교", "b", 40, (60, 60, 60), anchor="lm",
      max_w=W * 0.88)
    save(weather(im, 0.22, 11, 0.12), "Head")

    # 노선판 0.50 x 0.86 m (작은 글씨, M_Dyn)
    W, H = 1190, 2048
    ppm = W / 0.5                                                      # px / m
    im = Image.new("RGB", (W, H), (244, 243, 238))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 110), fill=(40, 44, 50))
    T(d, (W / 2, 55), "이 정류장을 지나는 버스", "eb", 58, (245, 245, 240), anchor="mm")
    y = 150
    times = {"112": ("05:30", "23:10", "8~12분"), "2413": ("05:50", "22:40", "15~20분"), "7": ("06:10", "21:30", "25~30분")}
    for num, col, kind, _ in ROUTES:
        stops = LONG[num]
        d.rounded_rectangle((30, y, W - 30, y + 560), radius=18, fill=(255, 255, 255), outline=(200, 200, 196), width=3)
        d.rounded_rectangle((50, y + 26, 380, y + 190), radius=16, fill=col)
        T(d, (215, y + 108), num, "eb", 140, (255, 255, 255), anchor="mm", max_w=300)
        T(d, (410, y + 62), kind + "버스", "eb", 50, col, anchor="lm")
        T(d, (410, y + 128), stops[-1] + " 방면", "b", 46, (40, 40, 40), anchor="lm", max_w=W - 460)
        f, fs = "r", 26                                                  # 실제 약 11mm 글씨
        line, ly = "", y + 230
        for i, s in enumerate(stops):
            part = ("● " if s == "은행골 입구" else "") + s + ("  →  " if i < len(stops) - 1 else "")
            if d.textlength(line + part, font=F(f, fs)) > W - 140:
                T(d, (70, ly), line, f, fs, (35, 35, 35), anchor="la")
                line, ly = "", ly + 40
            line += part
        T(d, (70, ly), line, f, fs, (35, 35, 35), anchor="la")
        ry, x0, x1 = y + 372, 90, W - 110                              # 노선 띠 그림 (점 + 아주 작은 이름 ≈ 7 mm)
        d.line((x0, ry, x1 + 30, ry), fill=col, width=8)
        d.polygon([(x1 + 30, ry - 14), (x1 + 52, ry), (x1 + 30, ry + 14)], fill=col)
        for i, s in enumerate(stops):
            x = x0 + (x1 - x0) * i / (len(stops) - 1)
            here = s == "은행골 입구"
            r = 11 if here else 8
            d.ellipse((x - r, ry - r, x + r, ry + r), fill=(255, 255, 255), outline=(220, 40, 30) if here else col,
                      width=4)
            T(d, (x, ry + 18 + (i % 2) * 26), s, "b" if here else "r", 17, (220, 40, 30) if here else (60, 60, 60),
              anchor="mt", max_w=(x1 - x0) / (len(stops) - 1) * 1.8)
        a, b, c = times[num]
        T(d, (70, y + 470), f"첫차 {a}   막차 {b}   배차간격 {c}", "b", 28, (90, 90, 90), anchor="la")
        T(d, (70, y + 512), "※ 교통 상황에 따라 도착 시간이 달라질 수 있습니다.", "r", 22, (120, 120, 120), anchor="la")
        y += 600
    T(d, (W / 2, H - 70), "버스 이용 문의 ☎ 120  ·  은행골구청 교통행정과 02-2600-1234", "r", 24, (80, 80, 80),
      anchor="mm", max_w=W - 60)
    T(d, (W / 2, H - 32), "정류소 번호 14-208  ·  분실물 센터 1577-0287", "r", 22, (110, 110, 110), anchor="mm")
    im = weather(im, 0.28, 12, 0.1)
    save(im, "Routes")
    save(im.filter(ImageFilter.GaussianBlur(9)), "Routes_Base")       # 돋보기 밖 (11 mm 글씨가 뭉개짐)

    A = Atlas(1024)

    def flyer(txt, sub, col, seed):
        def f(d, im, W, H):
            sticker_bg(im, W, H, (246, 244, 236), 0.0)
            d.rectangle((0, 0, W, H * 0.3), fill=col + (255,))
            T(d, (W / 2, H * 0.15), txt, "bhs", H * 0.2, (255, 255, 255, 255), anchor="mm", max_w=W * 0.92)
            for i, s in enumerate(sub):
                T(d, (W / 2, H * (0.42 + i * 0.13)), s, "b", H * 0.085, (30, 30, 30, 255), anchor="mm", max_w=W * 0.9)
            for i in range(7):                                       # 전화번호 뜯는 띠
                x = i * W / 7
                d.line((x, H * 0.78, x, H), fill=(150, 150, 150, 255), width=2)
                if i % 3 != 1:
                    T(d, (x + W / 14, H * 0.89), "010-4821-77" + str(10 + i), "r", W / 7 * 0.13,
                      (40, 40, 40, 255), anchor="mm")
            finish_sticker(im, 0.6, seed, tear=0.06)
        return f
    A.add("flyer_room", 0.15, 0.21, 2400, flyer("원룸 · 투룸", ["즉시 입주 가능", "보증금 300 / 월 35", "은행골 역세권 도보 5분"],
                                               (200, 40, 40), 21))
    A.add("flyer_job", 0.15, 0.21, 2400, flyer("주5일 알바", ["시급 10,030원 이상", "편의점 · 물류 단기", "어르신 환영"],
                                              (30, 110, 60), 22))

    def tape(d, im, W, H):                                            # 테이프 자국
        for i in range(5):
            x, y = random.uniform(0, W * 0.7), random.uniform(0, H * 0.8)
            d.rectangle((x, y, x + W * 0.28, y + H * 0.16), fill=(225, 220, 200, 150))
        finish_sticker(im, 0.8, 23, tear=0.2)
    A.add("tape", 0.12, 0.12, 2000, tape)

    def plate(d, im, W, H):                                           # 기둥 관리번호
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius=8, fill=(240, 240, 236, 255))
        T(d, (W / 2, H * 0.32), "버스정류소 표지", "b", H * 0.2, (40, 40, 40, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.68), "관리번호 14-208-S1", "eb", H * 0.22, NAVY + (255,), anchor="mm", max_w=W * 0.9)
        finish_sticker(im, 0.4, 24)
    A.add("pole_plate", 0.1, 0.045, 2600, plate)
    A.save()


# ------------------------------------------------------------------ 노선도

def make_routemap():
    W, H = 1506, 2048                                   # 1.00 x 1.36 m
    ppm = W / 1.0
    im = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, int(H * 0.1)), fill=NAVY)
    T(d, (W / 2, H * 0.04), "노선 안내", "eb", 96, (241, 238, 226), anchor="mm")
    T(d, (W / 2, H * 0.08), "은행골 입구 (14-208)  ·  Bus Route Map", "b", 34, (200, 215, 232), anchor="mm")
    # 노선별 굽이진 노선선 + 정류장
    ty = H * 0.13
    for num, col, kind, _ in ROUTES:
        stops = LONG[num]
        T(d, (60, ty + 6), num, "eb", 78, col, anchor="lt")
        T(d, (60 + d.textlength(num, font=F("eb", 78)) + 24, ty + 26), f"{kind}  ·  {stops[0]} ↔ {stops[-1]}", "b", 30,
          (60, 60, 60), anchor="lt", max_w=W - 400)
        per = 7
        rows = [stops[i:i + per] for i in range(0, len(stops), per)]
        y0 = ty + 178
        for ri, row in enumerate(rows):
            yy = y0 + ri * 112
            sgn = -1 if ri % 2 else 1                                  # 홀수 줄 = 오른쪽(곡선 끝)부터 왼쪽으로
            xs = [W * (0.5 + sgn * (i * 0.8 / (per - 1) - 0.4)) for i in range(len(row))]
            d.line((min(xs) - 10, yy, max(xs) + 10, yy), fill=col, width=12)
            if ri < len(rows) - 1:                                     # 다음 줄로 꺾임
                ex = xs[-1]
                d.arc((ex - 56, yy, ex + 56, yy + 112), 270 if ri % 2 == 0 else 90, 90 if ri % 2 == 0 else 270,
                      fill=col, width=12)
            for i, (x, s) in enumerate(zip(xs, row)):
                hot = s == "시장 입구"
                here = s == "은행골 입구"
                rr = 17 if (hot or here) else 13
                d.ellipse((x - rr, yy - rr, x + rr, yy + rr), fill=(247, 244, 234), outline=col, width=6)
                turn = i == len(row) - 1 and ri < len(rows) - 1             # 곡선이 나가는 정류장: 이름을 곡선 안쪽으로
                lx, anc = (x + 16 * sgn, "rt" if sgn > 0 else "lt") if turn else (x, "mt")
                T(d, (lx, yy + 30), s, "eb" if hot else "b", 24, RED if hot else (51, 51, 51), anchor=anc,
                  max_w=W * 0.125)
                if here:
                    d.polygon([(x - 18, yy - 58), (x + 18, yy - 58), (x, yy - 24)], fill=(220, 40, 30))
                    T(d, (x + 26, yy - 44), "현위치", "eb", 24, (220, 40, 30), anchor="lm")
        ty = y0 + (len(rows) - 1) * 112 + 96
        d.line((50, ty - 20, W - 50, ty - 20), fill=(190, 186, 172), width=2)
    # 아래: 주변 지도 + 시간표/요금/안내
    my = ty
    mh = H - my - 222
    mx0, mx1 = 50, int(W * 0.56)
    d.rectangle((mx0, my, mx1, my + mh), fill=(236, 233, 222), outline=(150, 146, 134), width=3)
    T(d, (mx0 + 14, my + 12), "주변 지도", "eb", 34, (40, 40, 40), anchor="lt")
    rng = random.Random(5)
    for i in range(14):                                                # 블록(건물)
        bx = rng.uniform(mx0 + 20, mx1 - 160)
        by = rng.uniform(my + 70, my + mh - 110)
        d.rectangle((bx, by, bx + rng.uniform(70, 150), by + rng.uniform(50, 100)), fill=(214, 209, 194))
    d.rectangle((mx0, my + mh * 0.55, mx1, my + mh * 0.55 + 46), fill=(250, 250, 248))   # 큰길
    d.rectangle((mx0 + (mx1 - mx0) * 0.6, my + 50, mx0 + (mx1 - mx0) * 0.6 + 34, my + mh), fill=(250, 250, 248))
    T(d, (mx0 + 30, my + mh * 0.55 + 23), "은행골로", "b", 24, (110, 110, 110), anchor="lm")
    labels = [("은행골아파트", 0.2, 0.25), ("동사무소", 0.75, 0.3), ("은행골 경로당", 0.25, 0.8),
              ("새마을금고", 0.8, 0.78), ("약국", 0.56, 0.36), ("편의점", 0.42, 0.72)]
    for s, fx, fy in labels:
        T(d, (mx0 + (mx1 - mx0) * fx, my + mh * fy), s, "b", 24, (70, 70, 70), anchor="mm")
    px, py = mx0 + (mx1 - mx0) * 0.38, my + mh * 0.55 - 8
    d.ellipse((px - 18, py - 18, px + 18, py + 18), fill=(220, 40, 30))
    T(d, (px, py - 26), "현위치", "eb", 26, (220, 40, 30), anchor="mb")
    d.polygon([(mx1 - 50, my + 30), (mx1 - 64, my + 70), (mx1 - 36, my + 70)], fill=(40, 40, 40))
    T(d, (mx1 - 50, my + 92), "N", "eb", 24, (40, 40, 40), anchor="mm")
    d.line((mx0 + 20, my + mh - 24, mx0 + 170, my + mh - 24), fill=(40, 40, 40), width=4)
    T(d, (mx0 + 180, my + mh - 24), "100m", "r", 22, (40, 40, 40), anchor="lm")
    rx = mx1 + 40
    T(d, (rx, my + 10), "운행 시간", "eb", 34, (40, 40, 40), anchor="lt")
    tt = [("노선", "첫차", "막차", "배차"), ("112", "05:30", "23:10", "8~12분"), ("2413", "05:50", "22:40", "15~20분"),
          ("7", "06:10", "21:30", "25~30분")]
    for i, row in enumerate(tt):
        for j, s in enumerate(row):
            T(d, (rx + j * 140, my + 70 + i * 44), s, "eb" if i == 0 or j == 0 else "r", 26,
              ROUTES[i - 1][1] if (j == 0 and i > 0) else (40, 40, 40), anchor="la")
    fy0 = my + 246
    T(d, (rx, fy0), "요금 (교통카드 / 현금)", "eb", 30, (40, 40, 40), anchor="lt", max_w=W - rx - 40)
    for i, s in enumerate(["일반  1,500원 / 1,600원", "청소년  1,000원 / 1,100원", "어린이  550원 / 550원",
                           "※ 환승 시 거리 비례 추가 요금"]):
        T(d, (rx, fy0 + 50 + i * 34), s, "r", 25, (50, 50, 50), anchor="lt", max_w=W - rx - 40)
    # 바닥 안내 띠 + QR
    d.rectangle((0, H - 200, W, H), fill=(214, 210, 196))
    qr(d, W - 190, H - 182, 150)
    T(d, (W - 210, H - 150), "실시간 도착 정보", "eb", 24, (50, 50, 50), anchor="rt")
    T(d, (W - 210, H - 114), "QR 또는 앱에서 '14208'", "r", 22, (50, 50, 50), anchor="rt")
    for i, s in enumerate(["• 승차 시 교통카드를 단말기에 대 주세요.  하차 시에도 찍어야 환승 할인이 됩니다.",
                           "• 정류장 표지판 및 노선도 훼손 시 관계 법령에 따라 처벌받을 수 있습니다.",
                           "• 버스 이용 불편 신고 ☎ 120  ·  분실물 센터 ☎ 1577-0287  ·  은행골구청 교통행정과 02-2600-1234"]):
        T(d, (50, H - 175 + i * 52), s, "r", 24, (50, 50, 50), anchor="lt", max_w=W - 520 if i < 2 else W - 100)
    im = weather(im, 0.2, 31, 0.08)
    save(im, "Map")
    save(im.filter(ImageFilter.GaussianBlur(9)), "Map_Base")          # 돋보기 밖 (16 mm 글씨가 뭉개짐)

    A = Atlas(512)

    def lbl(d, im, W, H):
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius=5, fill=(200, 202, 204, 255))
        T(d, (W / 2, H * 0.35), "은행골구청 교통행정과", "b", H * 0.24, (40, 40, 40, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.72), "노선도 관리번호 RM-14208", "r", H * 0.2, (40, 40, 40, 255), anchor="mm", max_w=W * 0.9)
        finish_sticker(im, 0.45, 32)
    A.add("frame_label", 0.14, 0.035, 2600, lbl)

    def residue(d, im, W, H):                                         # 떼어낸 스티커 자국
        for i in range(3):
            x, y = random.uniform(0, W * 0.5), random.uniform(0, H * 0.5)
            d.rectangle((x, y, x + W * 0.45, y + H * 0.4), fill=(238, 236, 226, 170))
        finish_sticker(im, 0.9, 33, tear=0.25)
    A.add("residue", 0.1, 0.07, 2000, residue)
    A.save()


# ------------------------------------------------------------------ 승차대

def make_shelter():
    # 정류장 이름판 2.40 x 0.36 m (앞뒤 공용, 약하게 발광)
    W, H = 2048, 307
    im = Image.new("RGB", (W, H), NAVY)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((26, 34, 26 + 240, 34 + 240), radius=36, fill=(241, 238, 226))
    bus_icon(d, 146, 152, 170, NAVY, (241, 238, 226))
    T(d, (300, 118), "은행골 입구", "eb", 150, (241, 238, 226), anchor="lm", max_w=900)
    T(d, (304, 236), "Eunhaenggol Entrance", "b", 50, (200, 214, 230), anchor="lm")
    d.rectangle((1270, 40, 1274, H - 40), fill=(150, 175, 205))
    T(d, (1310, 96), "다음 정류장", "b", 40, (200, 214, 230), anchor="lm")
    T(d, (1310, 168), "▶ 동사무소", "eb", 62, (241, 238, 226), anchor="lm")
    T(d, (W - 40, 250), "14-208", "eb", 66, (223, 227, 228), anchor="rm")
    save(weather(im, 0.12, 41, 0.06), "NameSign")

    # 광고 라이트박스 포스터 2장 (안쪽: 버거대왕 / 바깥: 버스 앱 공익광고) 각 1.16 x 2.0 m
    PW, PH = 1024, 1766
    burger = Image.open(os.path.join(CACHE, "..", "_ref", "img", "burger_bulgogi.png")).convert("RGBA") \
        if os.path.exists(os.path.join(CACHE, "..", "_ref", "img", "burger_bulgogi.png")) else None
    a = Image.new("RGB", (PW, PH), (239, 227, 201))
    d = ImageDraw.Draw(a)
    g = np.linspace(0, 1, PH)[:, None, None]
    bg = np.array([239, 227, 201]) / 255 * (1 - 0.18 * g) + np.array([200, 120, 60]) / 255 * 0.18 * g
    a = img(np.broadcast_to(bg, (PH, PW, 3)).copy())
    d = ImageDraw.Draw(a)
    for i in range(18):                                                # 방사선 배경
        ang = i / 18 * math.tau
        d.line((PW / 2, 820, PW / 2 + math.cos(ang) * 900, 820 + math.sin(ang) * 900), fill=(232, 210, 170), width=30)
    d.rectangle((0, 0, PW, 300), fill=RED)
    T(d, (PW / 2, 150), "NEW", "bhs", 230, (255, 244, 216), anchor="mm")
    if burger:
        b = burger.resize((900, 900), Image.LANCZOS).filter(ImageFilter.UnsharpMask(3, 80, 2))
        sh = Image.new("RGBA", b.size, (0, 0, 0, 0))
        sh.putalpha(b.split()[3].filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.45)))
        a.paste((40, 20, 10), (PW // 2 - 450 + 10, 360 + 40), sh)
        a.paste(b, (PW // 2 - 450, 360), b)
    T(d, (PW / 2, 1335), "K-BBQ 스모키 비프", "bhs", 104, (58, 36, 22), anchor="mm", max_w=PW * 0.92)
    T(d, (PW / 2, 1440), "키오스크 전용 주문", "eb", 64, (109, 74, 46), anchor="mm")
    d.rounded_rectangle((PW * 0.2, 1478, PW * 0.8, 1552), radius=37, fill=RED)
    T(d, (PW / 2, 1515), "세트 9,400원  ·  단품 7,900원", "eb", 40, (255, 244, 216), anchor="mm", max_w=PW * 0.55)
    logo(d, PW / 2, 1652, 0.8, text=False)
    T(d, (PW / 2, 1712), "버거대왕  시장입구점", "eb", 44, (200, 41, 31), anchor="mm")
    T(d, (PW / 2, 1752), "*이미지는 연출된 것으로 실제와 다를 수 있습니다.  *일부 매장 제외", "r", 18, (110, 90, 70),
      anchor="mm")
    b2 = Image.new("RGB", (PW, PH), (232, 242, 246))
    d = ImageDraw.Draw(b2)
    d.rectangle((0, 0, PW, 520), fill=(18, 112, 140))
    T(d, (PW / 2, 150), "버스 도착 정보,", "bhs", 104, (255, 255, 255), anchor="mm")
    T(d, (PW / 2, 280), "이제 앱으로 확인하세요!", "bhs", 92, (255, 230, 120), anchor="mm", max_w=PW * 0.92)
    T(d, (PW / 2, 420), "기다림 없는 스마트 정류장", "eb", 54, (210, 235, 240), anchor="mm")
    d.rounded_rectangle((PW / 2 - 190, 600, PW / 2 + 190, 1260), radius=60, fill=(30, 34, 40))
    d.rounded_rectangle((PW / 2 - 165, 650, PW / 2 + 165, 1210), radius=26, fill=(250, 250, 250))
    for i, (n, t) in enumerate([("0000", "3분"), ("000", "7분"), ("00", "12분")]):      # 예시 값 (실제 노선 아님)
        yy = 720 + i * 130
        d.rounded_rectangle((PW / 2 - 145, yy - 50, PW / 2 + 145, yy + 50), radius=16, fill=(232, 242, 246))
        T(d, (PW / 2 - 125, yy), n, "eb", 56, [NAVY, RED, GREEN][i], anchor="lm")
        T(d, (PW / 2 + 125, yy), t, "eb", 44, (30, 30, 30), anchor="rm")
    T(d, (PW / 2, 1120), "OO 정류장", "b", 34, (90, 90, 90), anchor="mm")
    for i, s in enumerate(["① 앱 설치", "② 정류장 검색", "③ 실시간 확인"]):
        T(d, (PW * (0.2 + i * 0.3), 1340), s, "eb", 44, (18, 112, 140), anchor="mm", max_w=PW * 0.28)
    qr(d, PW / 2 - 110, 1420, 220, 7)
    T(d, (PW / 2, 1690), "은행골구 · 버스정보시스템(BIS)", "eb", 40, (40, 40, 40), anchor="mm")
    T(d, (PW / 2, 1740), "데이터 요금이 발생할 수 있습니다", "r", 22, (110, 110, 110), anchor="mm")
    poster = Image.new("RGB", (PW * 2, PH))
    poster.paste(weather(a, 0.08, 42, 0.05), (0, 0))
    poster.paste(weather(b2, 0.08, 43, 0.05), (PW, 0))
    save(poster, "AdPoster")

    # 유리 (RGB 색조 + 알파 = 먼지/손자국/물자국), 월드 UV 2.5 m 타일 기준
    S = 1024
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    z = (1 - yy / S) * 2.5                                             # 높이 m (UV v=z/2.5)
    dust = fbm(S, S, 120, 5, 51)
    bottom = np.clip((0.75 - z) / 0.5, 0, 1) ** 1.5                   # 아래쪽 흙탕물 튄 자국
    hands = np.zeros((S, S), np.float32)
    rng = np.random.default_rng(52)
    for _ in range(26):                                                # 손·어깨 기댄 자국 (0.9~1.6 m)
        cx, cz = rng.uniform(0, S), rng.uniform(0.9, 1.6)
        cy = (1 - cz / 2.5) * S
        rx, ry = rng.uniform(14, 40), rng.uniform(20, 60)
        hands += np.exp(-(((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2)) * rng.uniform(0.3, 1)
    drops = (fbm(S, S, 6, 2, 53) > 0.74) * np.clip((1.4 - z), 0, 1)       # 물방울 자국
    streak = fbm(S, S, 50, 3, 54)
    streak = np.asarray(Image.fromarray((streak * 255).astype(np.uint8)).resize((S // 16, S)).resize((S, S)),
                        np.float32) / 255
    al = 0.07 + 0.05 * dust + 0.28 * bottom * (0.5 + dust) + 0.1 * np.clip(hands, 0, 1) \
        + 0.08 * drops + 0.05 * np.clip(streak - 0.55, 0, 1) * 4
    rgb = np.dstack([0.80 + 0.06 * dust, 0.86 + 0.04 * dust, 0.84 + 0.03 * dust])
    rgb = rgb * (1 - 0.35 * bottom[..., None]) + 0.35 * bottom[..., None] * np.array([0.55, 0.5, 0.42])
    save(img(np.dstack([rgb, np.clip(al, 0, 0.6)]), "RGBA"), "Glass")

    # 지붕 폴리카보네이트 (트윈월 골 + 낙엽/먼지) 월드 UV 2.5 m
    flute = (np.sin(xx / S * 2.5 / 0.016 * math.tau) > 0.92).astype(np.float32)
    back = np.clip((yy / S - 0.55) / 0.45, 0, 1)                      # 뒤(낮은 쪽) 먼지 고임
    ral = 0.36 + 0.1 * flute + 0.25 * back * fbm(S, S, 60, 4, 55) + 0.12 * fbm(S, S, 200, 4, 56)
    rrgb = np.dstack([0.78 - 0.2 * back, 0.80 - 0.22 * back, 0.80 - 0.26 * back]) * (0.92 + 0.08 * flute[..., None])
    save(img(np.dstack([rrgb, np.clip(ral, 0, 0.85)]), "RGBA"), "Roof")

    # 데칼 아틀라스
    A = Atlas(2048)

    def nosmoke(d, im, W, H):
        sticker_bg(im, W, H, (252, 252, 250), 0.05)
        cx, cy, r = W / 2, H * 0.3, W * 0.3
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(215, 25, 25, 255))
        d.ellipse((cx - r * 0.8, cy - r * 0.8, cx + r * 0.8, cy + r * 0.8), fill=(255, 255, 255, 255))
        d.rectangle((cx - r * 0.6, cy - r * 0.08, cx + r * 0.45, cy + r * 0.1), fill=(60, 60, 60, 255))
        d.rectangle((cx + r * 0.3, cy - r * 0.08, cx + r * 0.45, cy + r * 0.1), fill=(230, 120, 40, 255))
        d.line((cx - r * 0.6, cy + r * 0.6, cx + r * 0.6, cy - r * 0.6), fill=(215, 25, 25, 255), width=int(r * 0.2))
        T(d, (W / 2, H * 0.64), "금연구역", "bhs", H * 0.12, (215, 25, 25, 255), anchor="mm")
        T(d, (W / 2, H * 0.76), "버스정류소 10m 이내", "eb", H * 0.05, (30, 30, 30, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.84), "위반 시 과태료 10만원", "b", H * 0.045, (30, 30, 30, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.92), "국민건강증진법 제9조 · 은행골구청", "r", H * 0.032, (60, 60, 60, 255), anchor="mm",
          max_w=W * 0.9)
        finish_sticker(im, 0.35, 61)
    A.add("nosmoke", 0.2, 0.28, 1500, nosmoke)

    def bell(d, im, W, H):
        sticker_bg(im, W, H, (250, 200, 20), 0.08)
        T(d, (W / 2, H * 0.22), "비상벨", "bhs", H * 0.22, (30, 30, 30, 255), anchor="mm")
        T(d, (W / 2, H * 0.5), "위급할 때 누르세요", "eb", H * 0.1, (30, 30, 30, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.68), "112 경찰 상황실 연결", "b", H * 0.085, (180, 20, 20, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.86), "허위 신고 시 처벌받을 수 있습니다", "r", H * 0.06, (40, 40, 40, 255), anchor="mm",
          max_w=W * 0.9)
        finish_sticker(im, 0.4, 62)
    A.add("bell", 0.16, 0.12, 1500, bell)

    def donor(d, im, W, H):                                           # 벤치 기증 명판 (황동)
        g = np.linspace(0, 1, W)[None, :, None]
        base = np.array([0.62, 0.48, 0.22]) * (0.85 + 0.25 * np.sin(g * 9) ** 2)
        im.paste(img(np.dstack([np.broadcast_to(base, (H, W, 3)), np.ones((H, W))]), "RGBA"))
        d = ImageDraw.Draw(im)
        d.rectangle((3, 3, W - 4, H - 4), outline=(80, 56, 20, 255), width=3)
        T(d, (W / 2, H * 0.34), "이 의자는 은행골 새마을금고에서", "b", H * 0.24, (60, 40, 14, 255), anchor="mm",
          max_w=W * 0.9)
        T(d, (W / 2, H * 0.7), "기증하였습니다.  2019. 5.", "b", H * 0.24, (60, 40, 14, 255), anchor="mm", max_w=W * 0.9)
        finish_sticker(im, 0.5, 63)
    A.add("donor", 0.18, 0.04, 2600, donor)

    def manage(d, im, W, H):
        d.rounded_rectangle((0, 0, W - 1, H - 1), radius=6, fill=(236, 236, 232, 255))
        d.rectangle((0, 0, W, H * 0.3), fill=NAVY + (255,))
        T(d, (W / 2, H * 0.15), "버스승차대 관리 안내", "eb", H * 0.18, (255, 255, 255, 255), anchor="mm", max_w=W * 0.9)
        for i, s in enumerate(["관리번호 GB-14-208", "은행골구청 교통행정과 02-2600-1234", "파손·고장 신고 ☎ 120"]):
            T(d, (W / 2, H * (0.45 + i * 0.2)), s, "b", H * 0.13, (40, 40, 40, 255), anchor="mm", max_w=W * 0.92)
        finish_sticker(im, 0.45, 64)
    A.add("manage", 0.16, 0.08, 2000, manage)

    def adinfo(d, im, W, H):
        T(d, (W / 2, H / 2), "광고문의 02-2600-7788  (주)은행골애드", "b", H * 0.6, (220, 220, 220, 255), anchor="mm",
          max_w=W * 0.98)
    A.add("adinfo", 0.28, 0.02, 2600, adinfo)

    def binlabel(txt, sub, col):
        def f(d, im, W, H):
            sticker_bg(im, W, H, col, 0.08)
            T(d, (W / 2, H * 0.4), txt, "eb", H * 0.34, (255, 255, 255, 255), anchor="mm", max_w=W * 0.9)
            T(d, (W / 2, H * 0.78), sub, "b", H * 0.18, (240, 240, 240, 255), anchor="mm", max_w=W * 0.9)
            finish_sticker(im, 0.45, 65)
        return f
    A.add("bin_general", 0.2, 0.08, 2000, binlabel("일반쓰레기", "종량제 봉투 X", (70, 74, 78)))
    A.add("bin_recycle", 0.2, 0.08, 2000, binlabel("재활용", "캔 · 병 · 페트", (30, 110, 170)))

    def dumping(d, im, W, H):
        sticker_bg(im, W, H, (252, 252, 248), 0.05)
        d.rectangle((0, 0, W, H * 0.3), fill=(200, 30, 30, 255))
        T(d, (W / 2, H * 0.15), "쓰레기 무단투기 금지", "eb", H * 0.16, (255, 255, 255, 255), anchor="mm", max_w=W * 0.92)
        for i, s in enumerate(["가정·사업장 쓰레기를 버리지 마세요", "적발 시 과태료 100만원 이하", "은행골구청 청소행정과"]):
            T(d, (W / 2, H * (0.45 + i * 0.2)), s, "b", H * 0.11, (30, 30, 30, 255), anchor="mm", max_w=W * 0.92)
        finish_sticker(im, 0.5, 66)
    A.add("dumping", 0.22, 0.12, 2000, dumping)

    def ginkgo(seed):
        def f(d, im, W, H):
            r = random.Random(seed)
            cx, cy = W / 2, H * 0.92
            pts = []
            notch = r.uniform(0.15, 0.3)
            for i in range(41):
                t = i / 40
                ang = math.radians(200 + t * 140)
                rr = H * 0.75 * (1 - notch * math.exp(-((t - 0.5) / 0.04) ** 2)) * (0.96 + 0.06 * r.random())
                pts.append((cx + math.cos(ang) * rr * 0.95, cy + math.sin(ang) * rr))
            col = [(232, 190, 40), (220, 170, 30), (205, 160, 60), (170, 130, 50)][seed % 4]
            d.polygon([(cx, cy)] + pts, fill=col + (255,))
            for i in range(14):
                ang = math.radians(205 + i * 9.5)
                d.line((cx, cy, cx + math.cos(ang) * H * 0.68, cy + math.sin(ang) * H * 0.68),
                       fill=tuple(int(c * 0.85) for c in col) + (255,), width=2)
            d.line((cx, cy, cx + W * 0.04, H), fill=(120, 100, 40, 255), width=4)
            finish_sticker(im, 0.5, seed)
        return f
    for i in range(4):
        A.add(f"leaf{i}", 0.07, 0.065, 1500, ginkgo(70 + i))

    def frit(d, im, W, H):                                            # 충돌 방지 점 띠 (유리 눈높이)
        for x in range(8, W, 22):
            d.ellipse((x, H * 0.2, x + 12, H * 0.2 + 12), fill=(235, 238, 240, 210))
        T(d, (W / 2, H * 0.78), "은행골 입구  BUS STOP  14-208", "b", H * 0.32, (235, 238, 240, 200), anchor="mm")
    A.add("frit", 2.0, 0.05, 1000, frit)

    def gum(d, im, W, H):                                             # 낙서
        T(d, (W * 0.05, H * 0.5), "민수♥지영", "pen", H * 0.7, (40, 40, 60, 230), anchor="lm")
        finish_sticker(im, 0.2, 67)
    A.add("graffiti", 0.22, 0.06, 1500, gum)

    def tape(d, im, W, H):
        for i in range(6):
            x, y = random.uniform(0, W * 0.75), random.uniform(0, H * 0.85)
            d.rectangle((x, y, x + W * 0.25, y + H * 0.13), fill=(228, 222, 200, 160))
        finish_sticker(im, 0.8, 68, tear=0.2)
    A.add("tape", 0.18, 0.18, 1500, tape)

    def flyer(d, im, W, H):
        sticker_bg(im, W, H, (246, 244, 236), 0.0)
        d.rectangle((0, 0, W, H * 0.28), fill=(220, 120, 20, 255))
        T(d, (W / 2, H * 0.14), "무료 건강 강좌", "bhs", H * 0.15, (255, 255, 255, 255), anchor="mm", max_w=W * 0.9)
        for i, s in enumerate(["어르신 스마트폰 교실", "키오스크 사용법 배워요!", "매주 화 · 목 오후 2시", "은행골 복지관 3층"]):
            T(d, (W / 2, H * (0.38 + i * 0.11)), s, "b", H * 0.065, (30, 30, 30, 255), anchor="mm", max_w=W * 0.9)
        T(d, (W / 2, H * 0.86), "문의 02-2600-5050", "eb", H * 0.07, (200, 30, 30, 255), anchor="mm")
        finish_sticker(im, 0.55, 69, tear=0.07)
    A.add("flyer", 0.21, 0.297, 1500, flyer)
    A.save()


{"BusStopBIS": make_bis, "BusStopSign": make_sign, "BusStopRouteMap": make_routemap,
 "BusShelter": make_shelter}[ASSET]()
