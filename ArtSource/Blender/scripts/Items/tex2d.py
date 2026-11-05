# Items 2D 텍스처 (Pillow): 메모(손글씨), 카드 앞/뒤(+노멀), IC칩, 렌즈 지문
# 실행: venv/bin/python tex2d.py <name|all> <out_dir>
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HOME = os.path.expanduser("~")
FONTS = os.path.join(os.environ.get("K3D_CACHE", "/Users/jeongwoo/Documents/Github/TestHackKaTon/ArtSource/_cache"), "fonts")
PEN = os.path.join(FONTS, "NanumPenScript-Regular.ttf")
SQ = {w: os.path.join(HOME, "Library/Fonts", f"NanumSquare{w}.ttf") for w in ("L", "R", "B", "EB")}
MONO = "/System/Library/Fonts/Menlo.ttc"


def F(path, size, index=0):
    return ImageFont.truetype(path, size, index=index)


def fbm(w, h, scale, octaves=4, seed=0):
    """부드러운 값 노이즈 0..1."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(2, int(scale * 2 ** o))
        a = rng.random((max(2, int(s * h / w)), s)).astype(np.float32)
        im = Image.fromarray((a * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.5
    return out / tot


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def normal_from_height(hgt, strength=4.0):
    """높이(0..1) -> OpenGL 탄젠트 노멀 (Y+)."""
    gy, gx = np.gradient(hgt.astype(np.float32))
    nx, ny = -gx * strength, gy * strength
    nz = np.ones_like(nx)
    l = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    n = np.stack([nx / l, ny / l, nz / l], -1)
    return Image.fromarray(((n * 0.5 + 0.5) * 255).clip(0, 255).astype(np.uint8))


def save_ms(smooth, path):
    """MS 텍스처 (R 금속 0, G AO 1, B 0, A 스무스니스). 이름 끝 _MS → Unity 가 선형으로 들여옴."""
    ms = np.zeros(smooth.shape + (4,), np.uint8)
    ms[..., 1] = 255
    ms[..., 3] = (np.clip(smooth, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(ms, "RGBA").save(path)


def fingerprints(W, H, prints, seed, period=12.0):
    """지문 마스크 0..1. prints = (u, v(위에서부터), 반지름(가로 비율), 회전), period = 융선 간격 px (~0.5mm)."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    out = np.zeros((H, W), np.float32)
    for u, v, rad, ang in prints:
        dx, dy = xx - u * W, yy - v * H
        rr = np.hypot(dx, dy * 1.35)
        th = np.arctan2(dy, dx) + ang
        ridge = 0.5 + 0.5 * np.sin(rr * 2 * math.pi / period + 2.0 * np.sin(th * 2))
        out += ridge * np.clip(1 - rr / (rad * W), 0, 1) ** 0.7
    return np.clip(out * (0.6 + 0.6 * fbm(W, H, 12, 3, seed)), 0, 1)


# ---------------------------------------------------------------- 메모
MEMO_LINES = ["손자가 부탁한 것", "시장 입구 버거대왕", "불고기 버거 세트", "콜라 말고 사이다로", "포장", "112번 버스"]


def paper(w, h, seed, base="#efe7d3"):
    c = hexc(base)
    n1 = fbm(w, h, 3, 4, seed)
    n2 = fbm(w, h, 40, 3, seed + 1)
    px = c[None, None, :] * (0.955 + 0.06 * n1[..., None] + 0.03 * (n2[..., None] - 0.5))
    # 가장자리 누렇게 + 접힌 자국 때
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ed = np.minimum.reduce([xx, w - xx, yy, h - yy]) / (0.08 * w)
    yel = np.clip(1 - ed, 0, 1) ** 2 * (0.5 + 0.5 * n1)
    px = px * (1 - 0.07 * yel[..., None]) + np.array([8, 4, -6]) * yel[..., None]
    fold = np.exp(-((xx - w * 0.5) / (0.004 * w)) ** 2) * 0.6 + np.exp(-((yy - h * 0.5) / (0.004 * h)) ** 2) * 0.5
    px = px * (1 - 0.06 * fold[..., None] * (0.6 + 0.4 * n2[..., None]))
    # 섬유 점
    rng = np.random.default_rng(seed + 7)
    for _ in range(int(w * h / 9000)):
        x, y = rng.integers(0, w), rng.integers(0, h)
        px[y, x] *= rng.uniform(0.88, 0.97)
    return Image.fromarray(px.clip(0, 255).astype(np.uint8))


def memo(out, W=1608, H=2048):
    sx, sy = W / 512, H / 640
    im = paper(W, H, 11)
    d = ImageDraw.Draw(im, "RGBA")
    # 인쇄된 줄 + 상단 머리말 + 왼쪽 빨간 여백선 (수첩 종이)
    for s in range(86, 640, 62):
        y = s * sy
        d.line([(24 * sx, y), (W - 24 * sx, y)], fill=(130, 140, 160, 70), width=3)
    d.line([(26 * sx, 30 * sy), (W - 24 * sx, 30 * sy)], fill=(196, 96, 96, 90), width=4)
    d.text((W - 24 * sx - 520, 8 * sy), "No.         Date      .      .", font=F(SQ["R"], 34), fill=(120, 132, 160, 120))
    d.text((28 * sx, 7 * sy), "MEMO", font=F(SQ["B"], 46), fill=(120, 132, 160, 130))
    d.line([(31 * sx, 30 * sy), (31 * sx, H - 10)], fill=(205, 110, 110, 60), width=3)
    # 손글씨 (볼펜, 글자마다 흔들림 + 필압)
    ink = Image.new("L", (W, H), 0)
    di = ImageDraw.Draw(ink)
    rng = random.Random(5)
    boxes = []
    for r, s in enumerate(MEMO_LINES):
        x = 38 * sx + rng.uniform(-6, 10)
        base = (74 + r * 62) * sy
        size = 40 * sy * (1.04 if r in (2, 3) else 1.0)
        f = F(PEN, int(size))
        bold = 2 if r in (2, 3) else 1
        ang = (-1 if r % 2 else 1) * 0.008
        x0 = x
        for ch in s:
            cs = int(size * rng.uniform(0.96, 1.05))
            fc = F(PEN, cs)
            y = base + math.tan(ang) * (x - x0) + rng.uniform(-3, 3) - cs * 0.78
            di.text((x, y), ch, font=fc, fill=255, stroke_width=bold, stroke_fill=255)
            x += fc.getlength(ch) * rng.uniform(0.96, 1.02) + (2 if ch != " " else 6)
        boxes.append((x0, base - size * 0.8, x, base + size * 0.15))
    # 강조: 3번째 줄 밑줄 두 번, '사이다로' 동그라미, '포장' 체크
    x0, y0, x1, y1 = boxes[2]
    for k, off in enumerate((16, 30)):
        pts = [(x0 + t * (x1 - x0), y1 + off + 4 * math.sin(t * 9 + k)) for t in np.linspace(0, 1, 40)]
        di.line(pts, fill=230, width=5)
    x0, y0, x1, y1 = boxes[3]
    cx0 = x0 + (x1 - x0) * 0.47
    pts = []
    for t in np.linspace(0.15, 2 * math.pi + 0.6, 90):
        rx, ry = (x1 - cx0) / 2 + 26, (y1 - y0) / 2 + 22
        pts.append(((cx0 + x1) / 2 + rx * math.cos(t) + 3 * math.sin(3 * t), (y0 + y1) / 2 + ry * math.sin(t) - 6))
    di.line(pts, fill=220, width=5)
    x0, y0, x1, y1 = boxes[4]
    di.line([(x1 + 40, y0 + 60), (x1 + 62, y0 + 92), (x1 + 120, y0 + 10)], fill=235, width=7, joint="curve")
    x0, y0, x1, y1 = boxes[5]
    # 작은 하트 (손주 낙서)
    hx, hy = x1 + 90, (y0 + y1) / 2
    hp = [(hx + 26 * 16 * math.sin(t) ** 3 / 16, hy - 26 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16)
          for t in np.linspace(0, 2 * math.pi, 60)]
    di.line(hp, fill=220, width=5)
    ink = ink.filter(ImageFilter.GaussianBlur(0.9))
    a = np.asarray(ink, np.float32) / 255
    dens = 0.78 + 0.22 * fbm(W, H, 60, 2, 3)  # 볼펜 잉크 농도 얼룩
    a = (a * dens).clip(0, 1)
    px = np.asarray(im, np.float32)
    inkc = hexc("#2b3a58")
    px = px * (1 - a[..., None] * 0.92) + inkc * a[..., None] * 0.92
    im = Image.fromarray(px.clip(0, 255).astype(np.uint8))
    # 위쪽 찢긴 섬유 + 왼쪽 아래 손때
    d = ImageDraw.Draw(im, "RGBA")
    rng2 = np.random.default_rng(3)
    for x in range(0, W, 3):
        d.line([(x, 0), (x + rng2.integers(-2, 3), rng2.integers(4, 22))], fill=(250, 247, 238, 120))
    sm = fbm(W, H, 6, 3, 9)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    g = np.exp(-(((xx - 0.1 * W) / (0.12 * W)) ** 2 + ((yy - 0.93 * H) / (0.09 * H)) ** 2)) * sm
    px = np.asarray(im, np.float32) * (1 - 0.1 * g[..., None])
    Image.fromarray(px.clip(0, 255).astype(np.uint8)).save(os.path.join(out, "memo.png"))
    # 뒷면: 무지 종이 + 접힌 자국. 앞 글씨는 게임이 런타임에 바꾸므로 비친 잉크는 굽지 않음
    paper(W // 2, H // 2, 12).save(os.path.join(out, "memo_back.png"))


# ---------------------------------------------------------------- 카드 (85.6 x 54 mm, 2048 x 1292)
CW, CH = 2048, 1292
PXMM = CW / 85.6
NUM = "9420 1183 5507 2841"


def mm(v):
    return int(round(v * PXMM))


def card(out):
    rng = np.random.default_rng(21)
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    base = hexc("#566e62")
    grad = 1.06 - 0.16 * (xx / CW * 0.6 + yy / CH * 0.4)
    n = fbm(CW, CH, 5, 3, 2)
    px = base * (grad * (0.97 + 0.05 * n))[..., None]
    # 기요셰 물결 무늬 (얇은 선)
    wav = np.zeros((CH, CW), np.float32)
    for k in range(26):
        yc = CH * (0.2 + k * 0.03) + 60 * np.sin(xx / CW * 6.0 + k * 0.35) + 25 * np.sin(xx / CW * 17 + k)
        wav += np.exp(-((yy - yc) / 1.6) ** 2)
    wav *= np.clip((xx / CW - 0.35) * 2.2, 0, 1)
    px = px * (1 - 0.0 * wav[..., None]) + (hexc("#e8e2d2") - px) * (0.07 * wav[..., None])
    # 큰 원 모티프 (오른쪽)
    r = np.hypot(xx - CW * 0.86, yy - CH * 0.38)
    ring = np.exp(-((r - CH * 0.42) / 6) ** 2) + np.exp(-((r - CH * 0.34) / 4) ** 2) * 0.7
    px += (hexc("#e8e2d2") - px) * 0.06 * ring[..., None]
    im = Image.fromarray(px.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    cream = (232, 226, 210, 255)
    # 로고: 빨간 둥근 사각 + 시장 차양 3줄
    lx, ly, ls = mm(5.5), mm(5.2), mm(7.6)
    d.rounded_rectangle([lx, ly, lx + ls, ly + ls], radius=mm(1.8), fill=(165, 60, 48, 255))
    for k in range(3):
        y = ly + mm(1.6) + k * mm(1.75)
        d.arc([lx + mm(1.2), y - mm(1.0), lx + ls - mm(1.2), y + mm(1.6)], 200, 340, fill=cream, width=mm(0.55))
    d.text((lx + ls + mm(2.0), ly - mm(0.6)), "시장은행", font=F(SQ["EB"], mm(6.0)), fill=cream)
    d.text((lx + ls + mm(2.2), ly + mm(6.0)), "SIJANG BANK", font=F(SQ["B"], mm(2.2)), fill=(232, 226, 210, 200))
    # 체크 라벨
    tx = CW - mm(27)
    d.rounded_rectangle([tx, mm(5.6), tx + mm(22), mm(11.4)], radius=mm(2.6), outline=cream, width=mm(0.35))
    d.text((tx + mm(2.4), mm(6.4)), "체크 CHECK", font=F(SQ["B"], mm(2.9)), fill=cream)
    # 칩 자리 (홈 테두리 그림자) + 비접촉 표시
    cx0, cy0, cw, ch = mm(9.6), mm(19.2), mm(11.6), mm(9.4)
    d.rounded_rectangle([cx0 - 6, cy0 - 6, cx0 + cw + 6, cy0 + ch + 6], radius=mm(1.6), outline=(30, 40, 35, 140), width=6)
    ax, ay = cx0 + cw + mm(4.0), cy0 + ch / 2
    for k in range(4):
        rr = mm(1.3 + k * 1.25)
        d.arc([ax - rr, ay - rr, ax + rr, ay + rr], -55, 55, fill=(232, 226, 210, 230), width=mm(0.45))
    # 이름·유효기간·국내전용
    d.text((mm(8.0), CH - mm(8.6)), "KIM CHEOLSU", font=F(MONO, mm(3.0), 1), fill=(222, 222, 214, 255))
    d.text((mm(40), CH - mm(13.4)), "VALID\nTHRU", font=F(SQ["B"], mm(1.25)), fill=(232, 226, 210, 220), spacing=2)
    d.text((mm(44), CH - mm(13.9)), "08/29", font=F(MONO, mm(2.6), 1), fill=(222, 222, 214, 255))
    d.rounded_rectangle([CW - mm(22), CH - mm(10.5), CW - mm(5), CH - mm(5)], radius=mm(1.2), fill=(232, 226, 210, 235))
    d.text((CW - mm(20.4), CH - mm(10.0)), "국내전용", font=F(SQ["EB"], mm(3.2)), fill=(86, 110, 98, 255))
    # 엠보 번호 (은박 팁핑) — 높이맵도 같이
    hmap = Image.new("L", (CW, CH), 0)
    dh = ImageDraw.Draw(hmap)
    fn = F(MONO, mm(4.6), 1)
    x, y = mm(8.0), CH - mm(19.6)
    for ch_ in NUM:
        if ch_ != " ":
            dh.text((x, y), ch_, font=fn, fill=255)
        x += mm(3.55) if ch_ != " " else mm(2.2)
    hm = hmap.filter(ImageFilter.GaussianBlur(2.2))
    ha = np.asarray(hm, np.float32) / 255
    sh = np.roll(np.roll(ha, 4, 0), 4, 1)  # 엠보 아래쪽 그림자
    px = np.asarray(im, np.float32)
    px *= (1 - 0.35 * np.clip(sh - ha, 0, 1))[..., None]
    silver = np.array([214, 214, 206], np.float32) * (0.9 + 0.12 * fbm(CW, CH, 30, 2, 5))[..., None]
    t = np.clip(ha * 1.6 - 0.25, 0, 1)[..., None]
    # 은박 닳음: 군데군데 벗겨져 녹색 플라스틱이 드러남 (벗겨진 곳은 쓸려서 살짝 밝음)
    foil = np.clip((fbm(CW, CH, 90, 3, 13) - 0.3) * 4.0, 0, 1)[..., None]
    px = px * (1 - t * foil) + silver * t * foil
    px = px + (255 - px) * 0.14 * t * (1 - foil)
    # 마모: 잔 스크래치 + 모서리 닳음
    sc = Image.new("L", (CW, CH), 0)
    ds = ImageDraw.Draw(sc)
    for _ in range(260):
        x0, y0 = rng.integers(0, CW), rng.integers(0, CH)
        ang, ln = rng.uniform(0, math.pi), rng.uniform(20, 260)
        ds.line([(x0, y0), (x0 + ln * math.cos(ang), y0 + ln * math.sin(ang))], fill=int(rng.integers(40, 130)), width=1)
    sca = np.asarray(sc, np.float32)[..., None] / 255
    ed = np.minimum.reduce([xx, CW - xx, yy, CH - yy])
    rub = np.clip(1 - ed / mm(1.4), 0, 1)[..., None] * (0.5 + 0.5 * n[..., None])
    # 모서리 쓸림 (지갑 칸에 넣고 뺄 때 네 귀가 제일 많이 닳음)
    # 둥근 모서리 외곽선까지의 거리(SDF)로 R3.18 테두리를 따라 1.6mm 띠만 쓸리게
    cr = mm(3.18)
    qx, qy = np.abs(xx - CW / 2) - (CW / 2 - cr), np.abs(yy - CH / 2) - (CH / 2 - cr)
    din = cr - np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) - np.minimum(np.maximum(qx, qy), 0)
    inq = np.clip((np.minimum(qx, qy) + mm(2.5)) / mm(2.5), 0, 1)   # 네 귀 구역
    corner = (np.clip(1 - din / mm(1.6), 0, 1) * inq)[..., None] * (0.4 + 0.6 * fbm(CW, CH, 40, 2, 14)[..., None])
    rub = np.maximum(rub, corner)
    px = px + (255 - px) * (0.18 * sca + 0.26 * rub)
    Image.fromarray(px.clip(0, 255).astype(np.uint8)).save(os.path.join(out, "card_front.png"))
    # 노멀: 엠보 + 미세 표면결 (이름 끝 _Normal → Unity 가 노멀맵·선형으로 들여옴)
    hh = ha * 1.0 + 0.015 * fbm(CW, CH, 200, 2, 8) - 0.05 * sca[..., 0]
    normal_from_height(hh, 9.0).save(os.path.join(out, "card_front_Normal.png"))
    # MS (R 금속 0, G AO 1, A 스무스니스): 코팅 0.66, 잔기스·지문·모서리 쓸림은 무광, 남은 은박은 반짝
    fp_front = fingerprints(CW, CH, ((0.80, 0.80, 0.055, 0.5), (0.70, 0.88, 0.045, -0.4)), 31)
    sm_f = 0.66 + 0.04 * (fbm(CW, CH, 7, 3, 15) - 0.5) - 0.28 * sca[..., 0] - 0.2 * fp_front - 0.18 * rub[..., 0]
    sm_f = sm_f * (1 - t[..., 0]) + (0.5 + 0.28 * foil[..., 0]) * t[..., 0]
    save_ms(sm_f, os.path.join(out, "card_front_MS.png"))

    # ------------------------------------------------ 뒷면
    px = base * (0.96 + 0.05 * n)[..., None] * 1.04
    im = Image.fromarray(px.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im, "RGBA")
    # 마그네틱 띠 (윗변 5.5mm 부터 12.7mm)
    d.rectangle([0, mm(5.5), CW, mm(18.2)], fill=(22, 22, 24, 255))
    # 서명란 (연한 무늬) + 서명 + CVC
    sx0, sy0, sx1, sy1 = mm(5.5), mm(22.5), mm(59), mm(31.5)
    sp = Image.new("RGBA", (sx1 - sx0, sy1 - sy0), (238, 236, 226, 255))
    dp = ImageDraw.Draw(sp, "RGBA")
    pat = F(SQ["R"], mm(1.3))
    for yy0 in range(0, sy1 - sy0, mm(1.6)):
        for xx0 in range(-mm(4) * ((yy0 // mm(1.6)) % 2), sx1 - sx0, mm(9)):
            dp.text((xx0, yy0), "시장은행", font=pat, fill=(160, 186, 170, 120))
    im.paste(sp, (sx0, sy0))
    d.text((sx0 + mm(4), sy0 + mm(0.2)), "김철수", font=F(PEN, mm(7.2)), fill=(28, 30, 45, 235))
    d.rectangle([sx1 + mm(1.5), sy0, sx1 + mm(11), sy1], fill=(246, 244, 236, 255))
    d.text((sx1 + mm(3.0), sy0 + mm(2.6)), "713", font=F(MONO, mm(3.2), 2), fill=(30, 30, 30, 255))
    d.text((sx0, sy0 - mm(2.6)), "AUTHORIZED SIGNATURE · 서명하지 않은 카드는 사용할 수 없습니다", font=F(SQ["R"], mm(1.35)), fill=(232, 226, 210, 220))
    # 홀로그램 스티커
    hx0, hy0, hs = CW - mm(13.4), mm(21.8), mm(10.5)
    holo = np.zeros((hs, hs, 3), np.float32)
    gy, gx = np.mgrid[0:hs, 0:hs].astype(np.float32) / hs
    ph = (gx * 3.2 + gy * 2.1 + 0.25 * np.sin(gx * 20) * np.sin(gy * 17)) * 2 * math.pi
    for i, o in enumerate((0, 2.1, 4.2)):
        holo[..., i] = 175 + 70 * np.sin(ph + o)
    hol = Image.fromarray(holo.clip(0, 255).astype(np.uint8))
    mk = Image.new("L", (hs, hs), 0)
    ImageDraw.Draw(mk).rounded_rectangle([0, 0, hs - 1, hs - 1], radius=mm(1.2), fill=255)
    im.paste(hol, (hx0, hy0), mk)
    d = ImageDraw.Draw(im, "RGBA")
    d.ellipse([hx0 + mm(2.4), hy0 + mm(2.4), hx0 + hs - mm(2.4), hy0 + hs - mm(2.4)], outline=(255, 255, 255, 120), width=mm(0.4))
    # 안내문 (아주 작은 글씨, 실제 1.3mm)
    small = F(SQ["R"], mm(1.4))
    lines = ["· 이 카드는 시장은행 체크카드이며 회원 본인 외에는 사용할 수 없습니다.",
             "· 카드를 분실·도난당한 경우 즉시 고객센터로 신고하여 주십시오.",
             "· 카드 이용 시 결제계좌 잔액 범위 안에서만 승인됩니다. (국내전용)",
             "· 자기띠와 IC칩이 손상되지 않도록 자석·휴대폰 가까이 두지 마십시오."]
    for i, s in enumerate(lines):
        d.text((mm(5.5), mm(34.2) + i * mm(2.15)), s, font=small, fill=(232, 226, 210, 230))
    d.text((mm(5.5), CH - mm(7.6)), "고객센터 1599-0000   분실신고 1599-0011   www.sijangbank.kr", font=F(SQ["B"], mm(1.8)), fill=(232, 226, 210, 255))
    d.text((CW - mm(20), CH - mm(7.8)), "시장은행", font=F(SQ["EB"], mm(2.6)), fill=(232, 226, 210, 255))
    # 엠보 뒷자국 (좌우 반전, 오목)
    back_h = np.asarray(hm.transpose(Image.FLIP_LEFT_RIGHT), np.float32) / 255
    px = np.asarray(im, np.float32)
    bsh = np.roll(np.roll(back_h, -3, 0), -3, 1)
    px *= (1 - 0.18 * np.clip(bsh - back_h, 0, 1) - 0.06 * back_h)[..., None]
    px = px + (255 - px) * (0.16 * sca[:, ::-1] + 0.26 * rub)
    # 자기띠 긁힘: 단말기에 긁을 때 생긴 가로줄 (판독 헤드 자리에 몰림)
    sw = Image.new("L", (CW, CH), 0)
    dsw = ImageDraw.Draw(sw)
    for _ in range(420):
        y0 = rng.normal(mm(10.0), mm(2.4)) if rng.random() < 0.7 else rng.uniform(mm(5.6), mm(18.1))
        y0 = float(np.clip(y0, mm(5.6), mm(18.1)))
        x0 = rng.uniform(-200, CW)
        dsw.line([(x0, y0), (x0 + rng.uniform(150, 1400), y0 + rng.uniform(-1.5, 1.5))], fill=int(rng.integers(30, 120)), width=1)
    swa = np.asarray(sw.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    px = px + (255 - px) * 0.22 * swa[..., None]
    Image.fromarray(px.clip(0, 255).astype(np.uint8)).save(os.path.join(out, "card_back.png"))
    stripe = np.zeros((CH, CW), np.float32)
    stripe[mm(5.5):mm(18.2), :] = 0.06
    normal_from_height(-back_h * 0.6 + stripe + 0.012 * fbm(CW, CH, 200, 2, 9), 9.0).save(os.path.join(out, "card_back_Normal.png"))
    # MS 뒷면: 자기띠 광택 필름, 서명란 무광 종이, 홀로그램 반짝, 검지 지문 (앞 엄지 자리의 반대편)
    fp_back = fingerprints(CW, CH, ((0.20, 0.80, 0.07, 0.9), (0.36, 0.30, 0.05, 0.2)), 33)
    sm_b = 0.6 + 0.04 * (fbm(CW, CH, 7, 3, 16) - 0.5)
    sm_b[mm(5.5):mm(18.2), :] = 0.74
    sm_b[sy0:sy1, sx0:sx1] = 0.3
    sm_b[sy0:sy1, sx1 + mm(1.5):sx1 + mm(11)] = 0.34
    sm_b[hy0:hy0 + hs, hx0:hx0 + hs] = 0.85
    sm_b -= 0.45 * swa + 0.26 * sca[:, ::-1, 0] + 0.2 * fp_back + 0.18 * rub[..., 0]
    save_ms(sm_b, os.path.join(out, "card_back_MS.png"))


def chip(out, W=580, H=470):
    """IC칩 접점 (금도금, 8분할)."""
    g = hexc("#d8b96a") * (0.92 + 0.12 * fbm(W, H, 8, 3, 4))[..., None]
    im = Image.fromarray(g.clip(0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    dark = (96, 76, 36)
    lw = 9
    d.rounded_rectangle([3, 3, W - 4, H - 4], radius=46, outline=dark, width=6)
    d.line([(W * 0.5, 0), (W * 0.5, H * 0.3)], fill=dark, width=lw)
    d.line([(W * 0.5, H * 0.7), (W * 0.5, H)], fill=dark, width=lw)
    d.rounded_rectangle([W * 0.32, H * 0.3, W * 0.68, H * 0.7], radius=26, outline=dark, width=lw)
    for y in (H * 0.27, H * 0.5, H * 0.73):
        d.line([(0, y), (W * 0.32, y)], fill=dark, width=lw)
        d.line([(W * 0.68, y), (W, y)], fill=dark, width=lw)
    im.save(os.path.join(out, "chip.png"))


def lens(out, S=1024):
    """렌즈 유리 얼룩: RGB 거의 흰색, A = 기본 투명도 + 지문/닦은 자국."""
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
    a = np.full((S, S), 0.10, np.float32)
    n = fbm(S, S, 6, 4, 31)
    a += 0.05 * np.clip(n - 0.45, 0, 1) * 3
    # 지문 소용돌이 (아래쪽 가장자리 = 손잡이 근처, 위쪽 하나)
    for (cx, cy, rad, ang) in ((0.30, 0.18, 0.09, 0.4), (0.62, 0.12, 0.08, -0.3), (0.78, 0.74, 0.07, 1.1)):
        dx, dy = xx - cx, yy - cy
        rr = np.hypot(dx * 1.0, dy * 1.35)
        th = np.arctan2(dy, dx) + ang
        ridge = 0.5 + 0.5 * np.sin(rr * S * 0.55 + 2.0 * np.sin(th * 2))
        mask = np.clip(1 - rr / rad, 0, 1) ** 0.7
        a += 0.16 * ridge * mask
    # 닦은 자국 (호 모양 줄)
    for k in range(5):
        cy = 0.35 + k * 0.08
        band = np.exp(-((yy - cy - 0.15 * np.sin(xx * 3 + k)) / 0.012) ** 2) * (0.5 + 0.5 * fbm(S, S, 25, 2, 40 + k))
        a += 0.035 * band
    a = np.clip(a, 0, 0.42)
    rgb = np.ones((S, S, 3), np.float32) * (0.93 + 0.05 * n[..., None])
    img = np.concatenate([rgb, a[..., None]], -1)
    Image.fromarray((img * 255).astype(np.uint8), "RGBA").save(os.path.join(out, "lens_smudge.png"))


if __name__ == "__main__":
    which, out = sys.argv[1], sys.argv[2]
    os.makedirs(out, exist_ok=True)
    fns = {"memo": memo, "card": card, "chip": chip, "lens": lens}
    for k, f in fns.items():
        if which in (k, "all"):
            f(out)
            print("tex2d:", k)
