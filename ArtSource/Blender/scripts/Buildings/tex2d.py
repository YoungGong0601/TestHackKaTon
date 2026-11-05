"""건물 그룹 2D 텍스처 (Pillow). Blender 스크립트(bld.py)가 venv 파이썬으로 실행한다.

사용: python -I tex2d.py job.json
job = [{"out": 경로(.jpg/.png), "size": [w, h], "mode": "RGB"|"RGBA", "seed": n,
        "items": [{"rect": [x, y, w, h], "kind": ..., ...}]}]
rect 는 Pillow 좌표(왼쪽 위 원점, 픽셀).
"""
import json, math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HOME = os.path.expanduser("~")
FONT = {
    "black": f"{HOME}/Library/Fonts/Pretendard-Black.otf",
    "xbold": f"{HOME}/Library/Fonts/Pretendard-ExtraBold.otf",
    "bold": f"{HOME}/Library/Fonts/Pretendard-Bold.otf",
    "semi": f"{HOME}/Library/Fonts/Pretendard-SemiBold.otf",
    "med": f"{HOME}/Library/Fonts/Pretendard-Medium.otf",
    "nseb": f"{HOME}/Library/Fonts/NanumSquareEB.ttf",
    "nsb": f"{HOME}/Library/Fonts/NanumSquareB.ttf",
    "brush": f"{HOME}/Library/Fonts/Cafe24Dangdanghae-v2.0.ttf",
    "myungjo": "/System/Library/Fonts/Supplemental/AppleMyungjo.ttf",
}
R = random.Random(1)


def rgb(c, a=255):
    c = c.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16), a)


def mix(c1, c2, t):
    return tuple(int(c1[i] * (1 - t) + c2[i] * t) for i in range(len(c1)))


# ---------------------------------------------------------------- 글자

def text_img(txt, font, size, fill, stroke=0, stroke_fill=None):
    f = ImageFont.truetype(FONT.get(font, font), max(4, int(size)))
    l, t, r, b = f.getbbox(txt, stroke_width=stroke)
    im = Image.new("RGBA", (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), txt, font=f, fill=fill, stroke_width=stroke,
                            stroke_fill=stroke_fill)
    return im


def put_text(img, txt, box, font="black", fill="#ffffff", align="c", squeeze=0.62, stroke=0,
             stroke_fill=None, rot=0):
    """box 안에 글자를 맞춘다. 넓으면 가로로 눌러(간판식 장평) 맞추고 그래도 넓으면 축소."""
    if not txt:
        return
    x, y, w, h = [int(v) for v in box]
    fill = rgb(fill) if isinstance(fill, str) else fill
    sf = rgb(stroke_fill) if isinstance(stroke_fill, str) else stroke_fill
    t = text_img(txt, font, h * 1.3, fill, int(stroke * 1.3), sf)
    s = h / t.height
    tw, th = t.width * s, h
    sx = 1.0
    if tw > w:
        sx = max(squeeze, w / tw)
        if tw * sx > w:
            k = w / (tw * sx)
            s *= k
            th *= k
    t = t.resize((max(1, int(t.width * s * sx)), max(1, int(t.height * s))), Image.LANCZOS)
    if rot:
        t = t.rotate(rot, expand=True, resample=Image.BICUBIC)
    px = x + (w - t.width) // 2 if align == "c" else (x if align == "l" else x + w - t.width)
    py = y + (h - t.height) // 2
    img.alpha_composite(t, (int(px), int(py))) if img.mode == "RGBA" else img.paste(t, (int(px), int(py)), t)


# ---------------------------------------------------------------- 노화 (먼지, 빗물 자국, 탈색)

def age(im, amt=0.25, fade=0.0, streaks=True, seed=0):
    rnd = np.random.default_rng(seed)
    a = np.asarray(im.convert("RGBA")).astype(np.float32) / 255
    h, w = a.shape[:2]
    rgbv = a[..., :3]
    if fade:
        lum = rgbv.mean(axis=2, keepdims=True)
        rgbv = rgbv * (1 - fade) + (lum * 0.85 + 0.12) * fade
    yy = np.linspace(0, 1, h)[:, None, None]
    dust = amt * (0.35 * np.clip(1 - yy * 4, 0, 1) + 0.6 * np.clip((yy - 0.75) * 4, 0, 1))
    dirt = np.array([0.24, 0.21, 0.17])
    rgbv = rgbv * (1 - dust) + dirt * dust
    if streaks:
        m = np.zeros((h, w), np.float32)
        for _ in range(int(w / 18) + 4):
            x0 = int(rnd.uniform(0, w))
            ww = int(rnd.uniform(1, max(2, w * 0.012)))
            ln = int(rnd.uniform(0.2, 0.9) * h)
            y0 = int(rnd.uniform(0, 0.3) * h)
            g = np.linspace(1, 0, ln) ** 1.5 * rnd.uniform(0.3, 1)
            m[y0:y0 + ln, x0:x0 + ww] = np.maximum(m[y0:y0 + ln, x0:x0 + ww], g[:min(ln, h - y0), None])
        m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))) / 255
        rgbv = rgbv * (1 - m[..., None] * amt * 0.8) + dirt * m[..., None] * amt * 0.8
    sp = rnd.random((h, w)) < 0.002 * amt * 4
    rgbv[sp] = rgbv[sp] * 0.6 + 0.12
    noise = rnd.normal(0, 0.012, (h, w, 1))
    rgbv = np.clip(rgbv + noise, 0, 1)
    a[..., :3] = rgbv
    return Image.fromarray((a * 255).astype(np.uint8), "RGBA")


def screws(d, x, y, w, h, r=4, inset=10, col=(150, 150, 145, 255)):
    for px in (x + inset, x + w - inset):
        for py in (y + inset, y + h - inset):
            d.ellipse((px - r, py - r, px + r, py + r), fill=col, outline=(60, 55, 50, 255))
            d.ellipse((px - r + 2, py + r - 3, px + r - 2, py + r + 1), fill=(110, 70, 40, 120))


# ---------------------------------------------------------------- 종류별 그리기

def k_sign(c, it):
    """플렉스/갈바 간판 면: 배경, 큰 상호, 아래 작은 품목·전화."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    bg = rgb(it["bg"])
    for y in range(h):  # 위가 살짝 밝은 조명 그라데이션
        d.line([(0, y), (w, y)], fill=mix(mix(bg, (255, 255, 255, 255), 0.08), mix(bg, (0, 0, 0, 255), 0.1), y / h))
    band = it.get("band")
    if band:
        d.rectangle((0, int(h * 0.8), w, h), fill=rgb(band))
    if it.get("panels", True):
        for x in range(int(w / 6), w, int(w / 6)):
            d.line([(x, 0), (x, h)], fill=mix(bg, (0, 0, 0, 255), 0.18), width=2)
    fg = it.get("fg", "#ffffff")
    main_h = h * (0.56 if (it.get("sub") or it.get("tel")) else 0.68)
    cy = h * (0.42 if (it.get("sub") or it.get("tel")) else 0.5)
    if it.get("logo"):
        r = main_h * 0.5
        lx = w * 0.12
        d.ellipse((lx - r, cy - r, lx + r, cy + r), fill=rgb(it.get("logo_bg", fg)))
        put_text(c, it["logo"], (lx - r * 0.8, cy - r * 0.62, r * 1.6, r * 1.24), "black", it["bg"])
    put_text(c, it["text"], (w * 0.1, cy - main_h / 2, w * 0.8, main_h), it.get("font", "black"), fg,
             stroke=int(h * 0.03) if it.get("stroke") else 0, stroke_fill=it.get("stroke"))
    sub_col = it["bg"] if band else fg
    if it.get("sub"):
        put_text(c, it["sub"], (w * 0.05, h * 0.83, w * 0.45, h * 0.13), "bold", sub_col, align="l")
    if it.get("tel"):
        put_text(c, it["tel"], (w * 0.55, h * 0.83, w * 0.4, h * 0.13), "bold", sub_col, align="r")
    screws(d, 0, 0, w, h, r=max(3, h // 60), inset=max(8, h // 22))
    return age(c, it.get("dirt", 0.22), it.get("fade", 0.12), seed=it.get("seed", 0))


def k_plate_addr(c, it):
    """도로명주소 건물번호판 (남색 바탕, 흰 글자)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 10, fill=rgb("#173f86"))
    d.rounded_rectangle((h * 0.05, h * 0.05, w - h * 0.05, h - h * 0.05), radius=h // 12,
                        outline=rgb("#e8eef5"), width=max(2, h // 40))
    put_text(c, it["road"], (w * 0.07, h * 0.16, w * 0.5, h * 0.42), "bold", "#ffffff", align="l")
    put_text(c, it.get("en", ""), (w * 0.07, h * 0.62, w * 0.5, h * 0.2), "med", "#dfe6f2", align="l")
    put_text(c, it["num"], (w * 0.58, h * 0.12, w * 0.36, h * 0.76), "bold", "#ffffff", align="r")
    return age(c, 0.18, 0.15, streaks=False, seed=3)


def k_plate(c, it):
    """일반 명판/작은 안내판: 배경 + 글자 한두 줄."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, w, h), fill=rgb(it["bg"]))
    if it.get("border"):
        d.rectangle((h * 0.06, h * 0.06, w - h * 0.06, h - h * 0.06), outline=rgb(it["border"]), width=max(2, h // 30))
    lines = it["lines"]
    n = len(lines)
    for i, ln in enumerate(lines):
        size = it.get("sizes", [0.6] * n)[i]
        top = h * (0.5 - size / 2) if n == 1 else h * (0.12 + i * 0.8 / n)
        put_text(c, ln, (w * 0.06, top, w * 0.88, h * size if n == 1 else h * 0.8 / n * 0.85),
                 it.get("font", "bold"), it.get("fg", "#222222"), align=it.get("align", "c"))
    if it.get("screws", True):
        screws(d, 0, 0, w, h, r=max(2, h // 30), inset=max(6, h // 10))
    return age(c, it.get("dirt", 0.2), it.get("fade", 0.1), streaks=it.get("streaks", True), seed=it.get("seed", 5))


def k_vsign(c, it):
    """세로 돌출 간판: 색 블록마다 세로 글자."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    blocks = it["blocks"]
    bh = h / len(blocks)
    for i, (col, txt) in enumerate(blocks):
        y0 = int(i * bh)
        d.rectangle((0, y0, w, int(y0 + bh) - 4), fill=rgb(col))
        d.rectangle((0, int(y0 + bh) - 4, w, int(y0 + bh)), fill=(30, 30, 30, 255))
        n = len(txt)
        ch = min(bh * 0.86 / n, w * 0.8)
        for j, ch_ in enumerate(txt):
            cy = y0 + bh * (j + 0.5) / n
            put_text(c, ch_, (w * 0.12, cy - ch / 2, w * 0.76, ch), "black", it.get("fg", "#f1ece0"))
    return age(c, 0.25, 0.15, seed=7)


def k_listing(c, it):
    """부동산 유리창 매물 전단 묶음 (전세/월세/매매/급매)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, w, h), fill=(0, 0, 0, 0) if c.mode == "RGBA" else rgb("#2a2c2c"))
    rnd = random.Random(it.get("seed", 11))
    kinds = [("전세", "#b03a2e"), ("월세", "#2a5a8c"), ("매매", "#222222"), ("급매", "#c0221a")]
    rows = [["투룸 1억2천", "즉시입주", "주차가능"], ["원룸 500/45", "풀옵션", "역세권 5분"],
            ["빌라 3억5천", "3층 남향", "올수리"], ["상가 임대", "1층 15평", "권리금 없음"],
            ["쓰리룸 2억", "엘리베이터", "신축"], ["원룸 300/35", "관리비 5만", "여성전용"]]
    cols, rws = it.get("grid", [4, 3])
    cw, rh = w / cols, h / rws
    for i in range(cols):
        for j in range(rws):
            x0 = i * cw + cw * 0.06 + rnd.uniform(-4, 4)
            y0 = j * rh + rh * 0.05 + rnd.uniform(-4, 4)
            pw, ph = cw * 0.88, rh * 0.9
            paper = mix(rgb("#f3efe4"), rgb("#e5d9b9"), rnd.uniform(0, 0.7))
            d.rectangle((x0, y0, x0 + pw, y0 + ph), fill=paper)
            k, kc = rnd.choice(kinds)
            if k == "급매":
                d.rectangle((x0, y0, x0 + pw, y0 + ph * 0.24), fill=rgb("#d42a1c"))
                put_text(c, "급매!!", (x0 + pw * 0.05, y0 + ph * 0.02, pw * 0.9, ph * 0.2), "black", "#fff4d0")
            else:
                put_text(c, k, (x0 + pw * 0.05, y0 + ph * 0.03, pw * 0.6, ph * 0.2), "black", kc, align="l")
            r = rnd.choice(rows)
            for n, ln in enumerate(r):
                put_text(c, ln, (x0 + pw * 0.06, y0 + ph * (0.3 + n * 0.2), pw * 0.88, ph * 0.15),
                         "brush" if rnd.random() < 0.5 else "bold", "#262626", align="l")
            d.rectangle((x0 + pw * 0.4, y0 - 4, x0 + pw * 0.6, y0 + 6), fill=(225, 220, 190, 200))  # 테이프
    return c


def k_poster(c, it):
    """종이 포스터/전단: 머리 띠 + 여러 줄."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    paper = rgb(it.get("bg", "#f1ece0"))
    d.rectangle((0, 0, w, h), fill=paper)
    if it.get("head"):
        d.rectangle((0, 0, w, h * 0.22), fill=rgb(it.get("head_bg", "#b4291f")))
        put_text(c, it["head"], (w * 0.06, h * 0.03, w * 0.88, h * 0.16), "black", it.get("head_fg", "#fff6e0"))
    lines = it.get("lines", [])
    top = 0.27 if it.get("head") else 0.08
    lh = (0.9 - top) / max(1, len(lines))
    for i, ln in enumerate(lines):
        put_text(c, ln, (w * 0.07, h * (top + i * lh), w * 0.86, h * lh * 0.78), it.get("font", "bold"),
                 it.get("fg", "#2a2622"), align=it.get("align", "c"))
    return age(c, it.get("dirt", 0.18), it.get("fade", 0.25), seed=it.get("seed", 13))


def k_sticker(c, it):
    """작은 스티커 (24시 열쇠 등)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((1, 1, w - 2, h - 2), radius=h // 8, fill=rgb(it["bg"]))
    put_text(c, it["text"], (w * 0.08, h * 0.1, w * 0.84, h * 0.48), "black", it["fg"])
    put_text(c, it.get("tel", "010-555-0100"), (w * 0.1, h * 0.62, w * 0.8, h * 0.26), "bold", it["fg"])
    return age(c, 0.25, 0.3, streaks=False, seed=it.get("seed", 17))


def k_vinyl(c, it):
    """유리창 시트지 글자 (투명 바탕)."""
    w, h = c.size
    lines = it["lines"]
    for i, ln in enumerate(lines):
        put_text(c, ln, (w * 0.02, h * i / len(lines) + h * 0.05 / len(lines), w * 0.96, h / len(lines) * 0.9),
                 it.get("font", "black"), it.get("fg", "#ffffff"), align=it.get("align", "c"))
    return c


def k_interior(c, it):
    """창문 안쪽 카드: 커튼/블라인드/어두운 방 등 (variant). office=True 면 학원·병원·사무실."""
    if it.get("office"):
        return k_office(c, it)
    w, h = c.size
    d = ImageDraw.Draw(c)
    v = it.get("v", 0)
    rnd = random.Random(100 + v)
    room = mix(rgb("#3b3631"), rgb("#57524a"), rnd.random())
    for y in range(h):
        d.line([(0, y), (w, y)], fill=mix(mix(room, (0, 0, 0, 255), 0.35), room, y / h))
    if v % 2 == 0:  # 천장 등 반사
        d.ellipse((w * 0.35, -h * 0.05, w * 0.65, h * 0.08), fill=(200, 196, 180, 255))
    kind = v % 6
    cur = rgb(rnd.choice(["#d8cfbf", "#c9b79c", "#b9c2c4", "#e2dccf", "#a7907a", "#c4c9b0", "#e8e4dc"]))
    if kind in (0, 1):  # 커튼 양쪽
        gap = rnd.uniform(0.05, 0.4)
        for side in (0, 1):
            x0 = 0 if side == 0 else w * (0.5 + gap / 2)
            x1 = w * (0.5 - gap / 2) if side == 0 else w
            for x in range(int(x0), int(x1)):
                s = 0.82 + 0.18 * math.sin(x / w * 40 + side)
                d.line([(x, 0), (x, h)], fill=mix((0, 0, 0, 255), cur, s))
    elif kind == 2:  # 수평 블라인드
        bl = rgb(rnd.choice(["#d9d6cc", "#bfb8a8", "#e4e0d8"]))
        down = rnd.uniform(0.4, 1.0)
        for y in range(0, int(h * down), 6):
            d.rectangle((0, y, w, y + 4), fill=bl)
            d.line([(0, y + 4), (w, y + 4)], fill=mix(bl, (0, 0, 0, 255), 0.35))
    elif kind == 3:  # 롤 블라인드 반쯤
        d.rectangle((0, 0, w, h * rnd.uniform(0.3, 0.7)), fill=cur)
        d.line([(0, h * 0.02), (w, h * 0.02)], fill=(90, 90, 90, 255), width=4)
    elif kind == 4:  # 빨래 건조대
        d.line([(0, h * 0.3), (w, h * 0.3)], fill=(170, 170, 170, 255), width=3)
        x = 6
        while x < w - 20:
            cw = rnd.randint(20, 46)
            col = rgb(rnd.choice(["#e9e6de", "#4a5f7d", "#b8423a", "#d9c06a", "#7c8a6a", "#f0f0f0"]))
            d.rectangle((x, h * 0.3, x + cw, h * 0.3 + rnd.randint(40, 110)), fill=col)
            x += cw + rnd.randint(3, 10)
    else:  # 박스/화분이 보이는 어두운 방
        for _ in range(4):
            bx = rnd.uniform(0, w * 0.8)
            bw = rnd.uniform(30, 70)
            bh2 = rnd.uniform(30, 80)
            d.rectangle((bx, h - bh2, bx + bw, h), fill=mix(rgb("#8a6e4a"), (0, 0, 0, 255), rnd.uniform(0, 0.4)))
        d.ellipse((w * 0.1, h * 0.55, w * 0.3, h * 0.75), fill=rgb("#3e5a32"))
    if rnd.random() < 0.5:  # 창틀 뒤 방충망 결
        a = np.asarray(c).astype(np.int16)
        a[::3, :, :3] -= 12
        a[:, ::3, :3] -= 12
        c = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), c.mode)
    return c


def k_office(c, it):
    """상업 층 창 안: 밝은 천장 + 형광등, 게시판, 대기 의자 등받이, 한쪽으로 모인 버티컬 블라인드."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    rnd = random.Random(200 + it.get("v", 0))
    d.rectangle((0, 0, w, h), fill=mix(rgb("#d6d3c9"), rgb("#c6cdce"), rnd.random()))
    d.rectangle((0, 0, w, h * 0.12), fill=rgb("#ecebe5"))
    for k in range(2):
        x0 = w * (0.12 + 0.46 * k)
        d.rectangle((x0, h * 0.035, x0 + w * 0.3, h * 0.075), fill=(252, 252, 244, 255))
    d.rectangle((0, h * 0.8, w, h), fill=rgb("#8f8a80"))
    bx = w * rnd.uniform(0.08, 0.5)
    d.rectangle((bx, h * 0.28, bx + w * 0.32, h * 0.52), fill=rgb("#b98d5a"))
    for _ in range(6):
        px, py = bx + rnd.uniform(0.02, 0.25) * w, h * rnd.uniform(0.3, 0.42)
        d.rectangle((px, py, px + w * 0.05, py + h * 0.08), fill=rgb(rnd.choice(["#f4f1ea", "#fbe9a6", "#dfe9f2", "#f2d4d4"])))
    off = w * 0.4 * (rnd.random() < 0.5)
    for k in range(4):
        cx = w * (0.06 + k * 0.12) + off
        d.rounded_rectangle((cx, h * 0.6, cx + w * 0.09, h * 0.8), radius=6, fill=rgb(rnd.choice(["#3d5a80", "#5b6770", "#6e3b3b"])))
    bw = w * rnd.uniform(0.22, 0.45)
    x0 = 0 if rnd.random() < 0.5 else w - bw
    for x in range(int(x0), int(x0 + bw), 9):
        d.rectangle((x, 0, x + 7, h), fill=rgb("#e8e6df"))
        d.line([(x + 7, 0), (x + 7, h)], fill=rgb("#b5b2a8"))
    return c


def shelf_row(d, x0, y0, x1, y1, rnd, pal):
    x = x0
    while x < x1 - 8:
        bw = rnd.uniform(10, 34)
        bh = rnd.uniform(0.45, 0.95) * (y1 - y0)
        col = rgb(rnd.choice(pal))
        d.rectangle((x, y1 - bh, min(x1, x + bw), y1), fill=col)
        d.rectangle((x + 2, y1 - bh + 2, min(x1, x + bw) - 2, y1 - bh + 6), fill=mix(col, (255, 255, 255, 255), 0.35))
        x += bw + rnd.uniform(1, 4)


def k_shop(c, it):
    """가게 안쪽 벽 (얕은 실내 뒤 카드): kind=hair/realty/pharm/food/hard/laundry/stairs/empty."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    kind = it.get("shop", "empty")
    rnd = random.Random(sum(map(ord, kind)))   # hash() 는 실행마다 달라진다
    wall = rgb({"hair": "#d8d0c4", "realty": "#cfcabd", "pharm": "#e8ebe6", "food": "#d9c7a6",
                "hard": "#6b665c", "laundry": "#c9cbc6", "stairs": "#8f8a80", "empty": "#7d7a74"}.get(kind, "#999999"))
    d.rectangle((0, 0, w, h), fill=wall)
    d.rectangle((0, h * 0.86, w, h), fill=mix(wall, (40, 35, 30, 255), 0.55))  # 걸레받이/바닥 경계
    if kind == "hair":
        for x in range(30, w - 150, 260):
            d.rectangle((x, h * 0.12, x + 170, h * 0.62), fill=rgb("#7d8a8e"))  # 거울
            d.rectangle((x + 12, h * 0.15, x + 60, h * 0.58), fill=rgb("#a6b4b7"))
            d.rectangle((x - 10, h * 0.62, x + 190, h * 0.66), fill=rgb("#efe9df"))  # 선반
            cx = x + 85    # 유압 의자: 등받이(하이라이트) + 팔걸이 + 크롬 기둥 + 받침
            d.rounded_rectangle((cx - 42, h * 0.55, cx + 42, h * 0.76), radius=14, fill=rgb("#3a2f2c"))
            d.rounded_rectangle((cx - 34, h * 0.57, cx - 22, h * 0.74), radius=6, fill=rgb("#6e5d57"))
            for ax in (cx - 52, cx + 42):
                d.rounded_rectangle((ax, h * 0.66, ax + 10, h * 0.77), radius=3, fill=rgb("#262120"))
            d.rectangle((cx - 6, h * 0.76, cx + 6, h * 0.83), fill=rgb("#c8c8c4"))
            d.line([(cx - 3, h * 0.76), (cx - 3, h * 0.83)], fill=rgb("#f2f2ee"), width=2)
            d.ellipse((cx - 36, h * 0.815, cx + 36, h * 0.86), fill=rgb("#b5b5b0"))
            d.ellipse((x + 160, h * 0.6, x + 176, h * 0.64), fill=rgb("#c23b3b"))
        d.rectangle((w * 0.82, h * 0.1, w * 0.97, h * 0.5), fill=rgb("#f3efe6"))
        put_text(c, "가격표", (w * 0.83, h * 0.12, w * 0.13, h * 0.07), "black", "#7d3a52")
        for i, ln in enumerate(["커트 12,000", "파마 40,000~", "염색 35,000~", "드라이 8,000"]):
            put_text(c, ln, (w * 0.835, h * (0.21 + i * 0.07), w * 0.12, h * 0.05), "bold", "#333333", align="l")
    elif kind == "realty":
        d.rectangle((w * 0.05, h * 0.1, w * 0.55, h * 0.55), fill=rgb("#e9e3d1"))  # 지도
        for _ in range(40):
            x = rnd.uniform(w * 0.06, w * 0.54)
            y = rnd.uniform(h * 0.11, h * 0.54)
            d.line([(x, y), (x + rnd.uniform(-90, 90), y + rnd.uniform(-60, 60))], fill=rgb("#b8ae95"), width=2)
        put_text(c, "은행동 지도", (w * 0.06, h * 0.11, w * 0.2, h * 0.06), "bold", "#3a3a3a", align="l")
        d.rectangle((w * 0.62, h * 0.12, w * 0.9, h * 0.32), fill=rgb("#f5f1e6"))
        put_text(c, "공인중개사 등록증", (w * 0.63, h * 0.14, w * 0.26, h * 0.05), "bold", "#333333")
        d.rectangle((w * 0.1, h * 0.62, w * 0.5, h * 0.7), fill=rgb("#6a4e36"))  # 책상
        d.rectangle((w * 0.62, h * 0.4, w * 0.95, h * 0.86), fill=rgb("#8a8478"))  # 캐비닛
        for y in range(4):
            d.line([(w * 0.62, h * (0.4 + y * 0.115)), (w * 0.95, h * (0.4 + y * 0.115))], fill=rgb("#5b564d"), width=3)
    elif kind == "hard":   # 철물점: 타공판 공구, 감긴 호스, 페인트 통, 빗자루
        d.rectangle((w * 0.02, h * 0.08, w * 0.62, h * 0.55), fill=rgb("#b59a6e"))
        for yy in range(int(h * 0.1), int(h * 0.54), 14):
            for xx in range(int(w * 0.03), int(w * 0.61), 14):
                d.ellipse((xx - 1, yy - 1, xx + 1, yy + 1), fill=(90, 72, 50, 255))
        for k in range(10):
            x, y = w * (0.05 + k * 0.055), h * rnd.uniform(0.12, 0.2)
            col = rgb(rnd.choice(["#c0392b", "#e0a526", "#2f5f96", "#3e7a58", "#2d2a24"]))
            if k % 3 == 0:     # 망치
                d.rectangle((x, y, x + 6, y + h * 0.2), fill=rgb("#8a6a3e"))
                d.rectangle((x - 14, y, x + 20, y + 14), fill=rgb("#5a5a5a"))
            elif k % 3 == 1:   # 드라이버
                d.rectangle((x, y, x + 10, y + h * 0.09), fill=col)
                d.rectangle((x + 3, y + h * 0.09, x + 7, y + h * 0.2), fill=rgb("#a8a8a8"))
            else:              # 톱
                d.polygon([(x, y), (x + 26, y), (x + 20, y + h * 0.24), (x + 6, y + h * 0.24)], fill=rgb("#b8bcbf"))
                d.rectangle((x, y - 8, x + 26, y + 10), fill=col)
        for k, col in enumerate(("#2f7d4a", "#3d6fb0", "#c9a227")):
            cx, cy, r = w * (0.7 + k * 0.09), h * 0.25, h * 0.1
            for t in range(4):
                d.ellipse((cx - r + t * 4, cy - r + t * 4, cx + r - t * 4, cy + r - t * 4), outline=rgb(col), width=5)
        d.rectangle((0, h * 0.6, w, h * 0.62), fill=rgb("#2d2a24"))
        x = 10
        while x < w * 0.74:
            cw = rnd.uniform(40, 60)
            ch = cw * 1.1
            d.rectangle((x, h * 0.86 - ch, x + cw, h * 0.86), fill=rgb("#b8bcbf"))
            d.rectangle((x, h * 0.86 - ch * 0.75, x + cw, h * 0.86 - ch * 0.25),
                        fill=rgb(rnd.choice(["#e9e6de", "#c0392b", "#2f5f96", "#e0a526", "#3e7a58"])))
            d.ellipse((x, h * 0.86 - ch - 6, x + cw, h * 0.86 - ch + 6), fill=rgb("#d0d3d5"))
            x += cw + rnd.uniform(4, 12)
        for k in range(4):
            x = w * (0.8 + k * 0.045)
            d.line([(x, h * 0.35), (x + 8, h * 0.72)], fill=rgb("#c9a46a"), width=6)
            d.polygon([(x - 10, h * 0.72), (x + 26, h * 0.72), (x + 34, h * 0.86), (x - 16, h * 0.86)],
                      fill=rgb(rnd.choice(["#d9b45a", "#c0392b", "#3d6fb0"])))
    elif kind in ("pharm", "laundry", "food"):
        pal = {"pharm": ["#e3e6e2", "#c6d6d9", "#d9c7b3", "#a8c0a6", "#f2f2ee", "#c94a3a"],
               "laundry": ["#2d3340", "#5a3a36", "#6f6250", "#a39c8e", "#3e4a42", "#e9e6de"],
               "food": ["#c0392b", "#e8d7b0", "#f0c040", "#7a4a2a", "#e7e2d4"]}[kind]
        if kind == "laundry":
            d.line([(0, h * 0.14), (w, h * 0.14)], fill=rgb("#8e8e88"), width=5)
            x = -10
            while x < w:
                cw = rnd.uniform(40, 70)
                d.polygon([(x + cw / 2 - 6, h * 0.15), (x, h * 0.22), (x + 4, h * rnd.uniform(0.7, 0.85)),
                           (x + cw - 4, h * 0.8), (x + cw, h * 0.22), (x + cw / 2 + 6, h * 0.15)],
                          fill=rgb(rnd.choice(pal)))
                d.polygon([(x, h * 0.2), (x + cw, h * 0.2), (x + cw, h * 0.75), (x, h * 0.75)], fill=(205, 212, 218, 50))
                x += cw * rnd.uniform(0.62, 0.86)
        elif kind == "food":
            d.rectangle((0, h * 0.06, w, h * 0.3), fill=rgb("#f4ead2"))
            menu = it.get("menu", ["떡볶이 4,000", "김밥 3,000", "순대 4,500", "튀김 1,000", "어묵 1,000", "라면 4,000"])
            for i, m in enumerate(menu):
                put_text(c, m, (w * (0.02 + i * 0.163), h * 0.1, w * 0.15, h * 0.12), "black", "#7a2a12")
            d.rectangle((w * 0.05, h * 0.55, w * 0.95, h * 0.86), fill=rgb("#b9b4aa"))  # 스테인리스 조리대
            for x0 in ((0.1, 0.4) if it.get("pans", True) else ()):
                d.ellipse((w * x0, h * 0.5, w * (x0 + 0.24), h * 0.6), fill=rgb("#b4321e"))  # 떡볶이 판
            d.rectangle((w * 0.7, h * 0.46, w * 0.9, h * 0.56), fill=rgb("#d6a64a"))
        else:
            for row in range(3):
                y0 = h * (0.1 + row * 0.25)
                d.rectangle((0, y0 + h * 0.2, w, y0 + h * 0.215), fill=rgb("#d5d9d6" if kind == "pharm" else "#2d2a24"))
                shelf_row(d, 6, y0, w - 6, y0 + h * 0.2, rnd, pal)
        if kind == "pharm":
            d.rectangle((w * 0.3, h * 0.62, w * 0.7, h * 0.86), fill=rgb("#f2f2ee"))
            put_text(c, "조제실", (w * 0.42, h * 0.65, w * 0.16, h * 0.06), "bold", "#1f7a4c")
    elif kind == "stairs":
        for i in range(10):
            y = h * (0.86 - i * 0.075)
            x = w * (0.15 + i * 0.05)
            d.rectangle((x, y, w * 0.85, y + h * 0.075), fill=mix(rgb("#9a958a"), (40, 40, 40, 255), i * 0.05))
            d.line([(x, y), (w * 0.85, y)], fill=rgb("#c8c2b4"), width=3)
        d.line([(w * 0.1, h * 0.55), (w * 0.62, h * 0.05)], fill=rgb("#3a3a3a"), width=8)
        d.rectangle((w * 0.88, h * 0.2, w * 0.98, h * 0.5), fill=rgb("#b8b4a8"))  # 우편함
    else:  # 비어 있는 점포
        d.rectangle((0, 0, w, h), fill=rgb("#5d5a55"))
        for _ in range(6):
            x = rnd.uniform(0, w * 0.9)
            d.rectangle((x, h * 0.7, x + rnd.uniform(40, 120), h * 0.86), fill=rgb("#8a7558"))
    sh = Image.new("L", c.size, 0)  # 위·옆 어둡게
    sd = ImageDraw.Draw(sh)
    for i in range(40):
        sd.rectangle((i * 2, i * 2, w - i * 2, h - i), outline=int(150 - i * 3.7))
    blk = Image.new(c.mode, c.size, (10, 9, 8, 255) if c.mode == "RGBA" else (10, 9, 8))
    c = Image.composite(blk, c, sh.filter(ImageFilter.GaussianBlur(12)))
    return age(c, 0.1, 0.0, streaks=False, seed=19)


def k_fill(c, it):
    c.paste(rgb(it["color"])[:3] if c.mode == "RGB" else rgb(it["color"]), (0, 0, c.size[0], c.size[1]))
    return c


def k_stripes(c, it):
    """이발소 회전등 줄무늬 (가로로 이어지는 사선)."""
    w, h = c.size
    a = np.zeros((h, w, 4), np.uint8)
    yy, xx = np.mgrid[0:h, 0:w]
    t = ((xx / w + yy / h * it.get("turns", 1.5)) * 3) % 1.0
    cols = [rgb("#c8202a"), rgb("#f4f1ea"), rgb("#1f4fa0"), rgb("#f4f1ea")]
    idx = (t * 4).astype(int) % 4
    for i, col in enumerate(cols):
        a[idx == i] = col
    return Image.fromarray(a, "RGBA").filter(ImageFilter.GaussianBlur(1.2))


def k_apt(c, it):
    """먼 아파트 정면 타일 (가로 1칸 x 2층)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, w, h), fill=rgb("#c9c8c0"))
    rnd = random.Random(it.get("seed", 3))
    for fl in range(2):
        y0 = fl * h / 2
        d.rectangle((0, y0 + h * 0.4, w, y0 + h * 0.5), fill=rgb("#dedcd4"))  # 슬래브 띠
        for bx in range(2):
            x0 = bx * w / 2 + w * 0.04
            gw = w / 2 - w * 0.08
            col = rgb(rnd.choice(["#3e464c", "#4c555b", "#5a6166", "#353c41", "#6b6e68"]))
            d.rectangle((x0, y0 + h * 0.06, x0 + gw, y0 + h * 0.38), fill=col)  # 베란다 유리
            for k in range(1, 4):
                d.line([(x0 + gw * k / 4, y0 + h * 0.06), (x0 + gw * k / 4, y0 + h * 0.38)], fill=rgb("#d8d6ce"), width=4)
            if rnd.random() < 0.6:
                d.rectangle((x0 + gw * 0.05, y0 + h * 0.07, x0 + gw * rnd.uniform(0.3, 0.6), y0 + h * 0.3),
                            fill=rgb(rnd.choice(["#d8cfbf", "#b9c2c4", "#e2dccf"])))
            d.rectangle((x0, y0 + h * 0.3, x0 + gw, y0 + h * 0.31), fill=rgb("#9a9a94"))  # 난간
    return age(c, 0.15, 0.0, streaks=True, seed=21)


def k_grime(c, it):
    """외벽 덮개용 그을음/빗물 자국 (RGBA, 개구부는 투명)."""
    w, h = c.size
    rnd = np.random.default_rng(it.get("seed", 1))
    m = np.zeros((h, w), np.float32)
    yy = np.linspace(0, 1, h)[:, None]
    m += 0.55 * np.clip((yy - 0.9) / 0.1, 0, 1) ** 1.5  # 바닥 튐
    m += 0.25 * np.clip((0.05 - yy) / 0.05, 0, 1)  # 옥상 난간 아래
    def streak(x0, x1, y0, length, k=1.0):
        x0, x1 = int(x0 * w), int(x1 * w)
        y0i = int(y0 * h)
        ln = int(length * h)
        for _ in range(max(2, (x1 - x0) // 6)):
            x = int(rnd.uniform(x0, x1))
            ww = int(rnd.uniform(1, 6))
            ll = int(ln * rnd.uniform(0.3, 1.0))
            g = (np.linspace(1, 0, max(1, ll)) ** 1.3) * rnd.uniform(0.15, 0.6) * k
            y1 = min(h, y0i + ll)
            m[y0i:y1, x:x + ww] = np.maximum(m[y0i:y1, x:x + ww], g[:y1 - y0i, None])
    for s in it.get("sills", []):  # 창대 아래 (x0, x1, y 정규화, 아래로)
        streak(s[0], s[1], s[2], s[3] if len(s) > 3 else 0.12)
    for s in it.get("drips", []):  # 실외기·배관 아래
        streak(s[0], s[1], s[2], s[3] if len(s) > 3 else 0.2, 1.3)
    streak(0, 1, 0.0, 0.06, 0.7)
    lo = rnd.random((h // 32 + 1, w // 32 + 1)).astype(np.float32)
    lo = np.asarray(Image.fromarray((lo * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255
    m = m + 0.12 * lo
    m = np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.5))) / 255
    m = np.clip(m * it.get("strength", 0.85), 0, 1)
    for o in it.get("holes", []):  # 개구부는 투명
        x0, y0, x1, y1 = int(o[0] * w), int(o[1] * h), int(o[2] * w), int(o[3] * h)
        m[y0:y1, x0:x1] = 0
    a = np.zeros((h, w, 4), np.uint8)
    a[..., 0], a[..., 1], a[..., 2] = 52, 46, 38
    a[..., 3] = (m * 255).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def k_awning(c, it):
    """차양 천: 세로 줄무늬 (+ 앞 드림은 물결 끝, 글자)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    a, b = rgb(it["cols"][0]), rgb(it["cols"][1])
    n = it.get("n", 14)
    for k in range(n):
        d.rectangle((k * w / n, 0, (k + 1) * w / n, h), fill=a if k % 2 == 0 else b)
    if it.get("text"):
        put_text(c, it["text"], (w * 0.2, h * 0.12, w * 0.6, h * 0.5), "black", it.get("fg", "#ffffff"))
    for k in range(int(h / 9)):  # 천 결
        d.line([(0, k * 9), (w, k * 9)], fill=(0, 0, 0, 14))
    c = age(c, 0.35, 0.3, seed=it.get("seed", 23))
    if it.get("valance"):
        al = Image.new("L", c.size, 255)
        ad = ImageDraw.Draw(al)
        sc = w / n
        for k in range(n):
            ad.ellipse((k * sc, h * 0.72, (k + 1) * sc, h * 1.28), fill=0)
            ad.rectangle((k * sc, h * 0.72, (k + 1) * sc, h * 1.0), fill=0)
            ad.pieslice((k * sc, h * 0.44, (k + 1) * sc, h), 0, 180, fill=255)
        c.putalpha(al)
    return c


def k_mailbox(c, it):
    """공동 우편함 앞면 (스테인리스 칸 + 호수)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    d.rectangle((0, 0, w, h), fill=rgb("#8e9094"))
    cols, rows = it.get("grid", [4, 2])
    nums = it.get("nums", [])
    cw, rh = w / cols, h / rows
    for j in range(rows):
        for i in range(cols):
            x0, y0 = i * cw + 4, j * rh + 4
            for yy in range(int(y0), int(y0 + rh - 8)):
                t = (yy - y0) / (rh - 8)
                d.line([(x0, yy), (x0 + cw - 8, yy)], fill=mix(rgb("#c9cbcd"), rgb("#9da0a4"), t))
            d.rectangle((x0 + cw * 0.12, y0 + rh * 0.18, x0 + cw * 0.8, y0 + rh * 0.26), fill=rgb("#2a2b2d"))
            d.rectangle((x0 + cw * 0.25, y0 + rh * 0.45, x0 + cw * 0.62, y0 + rh * 0.62), fill=rgb("#f2efe6"))
            k = j * cols + i
            if k < len(nums):
                put_text(c, nums[k], (x0 + cw * 0.27, y0 + rh * 0.46, cw * 0.33, rh * 0.15), "bold", "#222222")
            d.ellipse((x0 + cw * 0.78, y0 + rh * 0.5, x0 + cw * 0.86, y0 + rh * 0.58), fill=rgb("#3a3a3a"))
            if (i + j) % 3 == 0:  # 꽂힌 전단
                d.rectangle((x0 + cw * 0.15, y0 + rh * 0.1, x0 + cw * 0.55, y0 + rh * 0.2), fill=rgb("#e0c94a"))
    return age(c, 0.25, 0.0, seed=29)


def k_keypad(c, it):
    """공동현관 번호키."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=w // 10, fill=rgb("#26282b"))
    d.rectangle((w * 0.12, h * 0.06, w * 0.88, h * 0.2), fill=rgb("#1d3b52"))
    put_text(c, "호출", (w * 0.2, h * 0.08, w * 0.6, h * 0.1), "bold", "#9fd3ff")
    keys = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for k, t in enumerate(keys):
        i, j = k % 3, k // 3
        x0, y0 = w * (0.1 + i * 0.28), h * (0.26 + j * 0.16)
        d.rounded_rectangle((x0, y0, x0 + w * 0.24, y0 + h * 0.12), radius=6, fill=rgb("#4a4d52"))
        put_text(c, t, (x0, y0 + h * 0.015, w * 0.24, h * 0.09), "bold", "#e8e8e8")
    return age(c, 0.15, 0.0, streaks=False, seed=31)


def k_aptfront(c, it):
    """먼 아파트 정면 (층 x 칸 발코니, 커튼·불 켜진 창·빨래·실외기, 1층 필로티, 위 브랜드)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    rnd = random.Random(it.get("seed", 3))
    nf, nb = it.get("floors", 15), it.get("bays", 12)
    top, base = it.get("top", 0.04), it.get("base", 0.06)
    wall = rgb(it.get("wall", "#d6d3c9"))
    d.rectangle((0, 0, w, h), fill=wall)
    fh = h * (1 - top - base) / nf
    bw = w / nb
    for f in range(nf):
        y0 = h * top + f * fh
        for b in range(nb):
            x0 = b * bw
            gx0, gx1, gy0, gy1 = x0 + bw * 0.06, x0 + bw * 0.94, y0 + fh * 0.1, y0 + fh * 0.8
            d.rectangle((gx0, gy0, gx1, gy1), fill=rgb(rnd.choice(["#3e464c", "#4c555b", "#5a6166", "#353c41", "#6b6e68", "#2f363b"])))
            r = rnd.random()
            if r < 0.4:
                cw = rnd.uniform(0.25, 0.6) * (gx1 - gx0)
                d.rectangle((gx0, gy0, gx0 + cw, gy1), fill=rgb(rnd.choice(["#d8cfbf", "#b9c2c4", "#e2dccf", "#c9b79c", "#e8e4dc"])))
            elif r < 0.5:
                d.rectangle((gx0 + 2, gy0 + 2, gx1 - 2, gy1 - 2), fill=rgb(rnd.choice(["#e9dcae", "#f1e6c4", "#dfe6e8"])))
            elif r < 0.6:
                xx = gx0 + 4
                while xx < gx1 - 10:
                    ww = rnd.uniform(5, 12)
                    d.rectangle((xx, gy0 + (gy1 - gy0) * 0.25, xx + ww, gy0 + (gy1 - gy0) * rnd.uniform(0.5, 0.8)),
                                fill=rgb(rnd.choice(["#e9e6de", "#4a5f7d", "#b8423a", "#d9c06a", "#f0f0f0"])))
                    xx += ww + rnd.uniform(1, 4)
            for k in range(1, 4):
                xk = gx0 + (gx1 - gx0) * k / 4
                d.line([(xk, gy0), (xk, gy1)], fill=rgb("#d8d6ce"), width=max(1, int(bw * 0.02)))
            d.rectangle((gx0, gy0, gx1, gy1), outline=rgb("#e4e2da"), width=max(1, int(bw * 0.025)))
            d.rectangle((gx0, gy0 + (gy1 - gy0) * 0.62, gx1, gy0 + (gy1 - gy0) * 0.66), fill=rgb("#a7a69e"))
            if rnd.random() < 0.22:
                ax = gx0 + (gx1 - gx0) * rnd.uniform(0.05, 0.6)
                d.rectangle((ax, gy1 - fh * 0.2, ax + bw * 0.25, gy1), fill=rgb("#e6e4dc"))
                d.ellipse((ax + bw * 0.03, gy1 - fh * 0.18, ax + bw * 0.14, gy1 - fh * 0.03), fill=rgb("#55585a"))
        d.rectangle((0, y0 + fh * 0.84, w, y0 + fh * 0.98), fill=mix(wall, (255, 255, 255, 255), 0.25))
    yb = h * (1 - base)
    d.rectangle((0, yb, w, h), fill=rgb("#3a3b3a"))
    for b in range(nb + 1):
        d.rectangle((b * bw - bw * 0.05, yb, b * bw + bw * 0.05, h), fill=mix(wall, (0, 0, 0, 255), 0.1))
    d.rectangle((w * 0.45, yb + (h - yb) * 0.2, w * 0.55, h), fill=rgb("#8a9aa0"))
    d.rectangle((0, 0, w, h * top), fill=mix(wall, (255, 255, 255, 255), 0.15))
    put_text(c, it.get("brand", "은행골 푸른마을"), (w * 0.3, h * top * 0.15, w * 0.4, h * top * 0.7), "black", it.get("brand_col", "#2c6e49"))
    return age(weather(c, nf, h * top, fh, it.get("seed", 3)), 0.3, 0.05, seed=it.get("seed", 3))


def weather(c, nf, y_top, fh, seed, slab=True):
    """먼 외벽 노화: 층마다 약한 색 차이, 슬래브 아래 빗물 줄, 모서리 때, 큰 얼룩, 미세 노이즈."""
    w, h = c.size
    rs = np.random.default_rng(seed + 50)
    a = np.asarray(c.convert("RGB")).astype(np.float32) / 255
    for f in range(nf):
        y0, y1 = int(y_top + f * fh), int(y_top + (f + 1) * fh)
        a[y0:y1] *= 1 + rs.uniform(-0.035, 0.035)
    m = np.zeros((h, w), np.float32)
    for f in range(nf):
        ys = int(y_top + f * fh + fh * (0.98 if slab else 0.5))
        for _ in range(int(w / (9 if slab else 30))):
            x, ww = int(rs.uniform(0, w)), int(rs.uniform(1, 4))
            ln = max(2, int(fh * rs.uniform(0.15, 0.9)))
            y1 = min(h, ys + ln)
            g = np.linspace(1, 0, ln) ** 1.4 * rs.uniform(0.2, 0.7)
            m[ys:y1, x:x + ww] = np.maximum(m[ys:y1, x:x + ww], g[:y1 - ys, None])
    xx = np.linspace(0, 1, w)[None, :]
    m = np.maximum(m, 0.55 * np.clip(1 - np.minimum(xx, 1 - xx) / 0.035, 0, 1))
    lo = rs.random((h // 48 + 1, w // 48 + 1)).astype(np.float32)
    lo = np.asarray(Image.fromarray((lo * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    m = np.clip(m + 0.18 * lo, 0, 1)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
    k = m[..., None] * 0.45
    a = a * (1 - k) + np.array([0.22, 0.2, 0.17], np.float32) * k + rs.normal(0, 0.02, (h, w, 1))
    return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "RGB").convert("RGBA")


def k_aptside(c, it):
    """아파트 옆 벽 (동 번호, 브랜드, 계단실 창 한 줄)."""
    w, h = c.size
    d = ImageDraw.Draw(c)
    wall = rgb(it.get("wall", "#d6d3c9"))
    d.rectangle((0, 0, w, h), fill=wall)
    nf, top, base = it.get("floors", 15), it.get("top", 0.04), it.get("base", 0.06)
    fh = h * (1 - top - base) / nf
    for f in range(nf):
        y0 = h * top + f * fh
        if y0 + fh * 0.7 > h * 0.05 and y0 + fh * 0.2 < h * 0.245:
            continue   # 동 번호·브랜드 글자 뒤 (위 4개 층)
        d.rectangle((w * 0.44, y0 + fh * 0.2, w * 0.56, y0 + fh * 0.7), fill=rgb("#4a5157"))
        d.rectangle((w * 0.44, y0 + fh * 0.2, w * 0.56, y0 + fh * 0.7), outline=rgb("#e4e2da"), width=3)
    d.rectangle((0, h * (1 - base), w, h), fill=rgb("#3a3b3a"))
    put_text(c, it.get("num", "101"), (w * 0.12, h * 0.06, w * 0.76, h * 0.09), "black", it.get("brand_col", "#2c6e49"))
    put_text(c, it.get("brand", "푸른마을"), (w * 0.2, h * 0.16, w * 0.6, h * 0.035), "black", it.get("brand_col", "#2c6e49"))
    for k in range(5):  # 녹색 띠 장식
        d.rectangle((0, h * (0.22 + k * 0.004), w, h * (0.222 + k * 0.004)), fill=rgb("#7fae8c"))
    return age(weather(c, nf, h * top, fh, it.get("seed", 9), slab=False), 0.35, 0.05, seed=it.get("seed", 9))


KINDS = {k[2:]: v for k, v in globals().items() if k.startswith("k_")}


def run(job):
    W, H = job["size"]
    mode = job.get("mode", "RGB")
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0) if mode == "RGBA" else (60, 58, 55, 255))
    for i, it in enumerate(job["items"]):
        x, y, w, h = [int(v) for v in it["rect"]]
        cm = "RGBA"
        c = Image.new(cm, (w, h), (0, 0, 0, 0))
        it.setdefault("seed", i * 7 + job.get("seed", 0))
        c = KINDS[it["kind"]](c, it)
        img.alpha_composite(c.convert("RGBA"), (x, y))
    os.makedirs(os.path.dirname(job["out"]), exist_ok=True)
    if job["out"].lower().endswith(".jpg"):
        img.convert("RGB").save(job["out"], quality=90)
    else:
        img.save(job["out"], optimize=True)
    print("tex2d:", job["out"], len(job["items"]))


if __name__ == "__main__":
    for j in json.load(open(sys.argv[1], encoding="utf-8")):
        run(j)
