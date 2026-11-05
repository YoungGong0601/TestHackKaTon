# Home 그룹 2D 텍스처 (Pillow). 사용: venv/bin/python tex2d.py <이름> <출력폴더>
# Blender 스크립트가 hk.tex(이름) 으로 호출한다. 결과는 PNG/JPG (원자적 저장).
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONTS = os.path.join(os.environ.get("K3D_CACHE", os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")), "_cache")), "fonts")
SD = "/System/Library/Fonts/AppleSDGothicNeo.ttc"
SD_I = {"r": 0, "m": 2, "sb": 4, "b": 6, "eb": 14, "h": 16}
MYEONG = "/System/Library/Fonts/Supplemental/AppleMyungjo.ttf"
NSQ = os.path.expanduser("~/Library/Fonts/NanumSquareEB.ttf")
_AV = "/System/Library/AssetsV2/com_apple_MobileAsset_Font7/"
XING = _AV + "aa99d0b2bad7f797f38b49d46cde28fd4b58876e.asset/AssetData/Xingkai.ttc"      # 行楷 TC (index 1)
GUNG = _AV + "f879347736afb6e4e0880bcede9df92492c0f040.asset/AssetData/Gungseouche.ttf"  # 궁서체
BP = os.path.join(os.environ.get("K3D_CACHE", os.path.join(os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")), "_cache")), "ph_backplates")                 # Poly Haven(CC0) 배경 사진


def F(kind, size):
    """글꼴: sd-b, sd-h, black(블랙한산스), pen(나눔펜), dohyeon, myeong, nsq."""
    if kind.startswith("sd"):
        return ImageFont.truetype(SD, size, index=SD_I[kind.split("-")[1]])
    if kind == "xing" and os.path.exists(XING):
        return ImageFont.truetype(XING, size, index=1)
    if kind == "gung" and os.path.exists(GUNG):
        return ImageFont.truetype(GUNG, size)
    path = {"black": os.path.join(FONTS, "BlackHanSans-Regular.ttf"),
            "pen": os.path.join(FONTS, "NanumPenScript-Regular.ttf"),
            "dohyeon": os.path.join(FONTS, "DoHyeon-Regular.ttf"),
            "myeong": MYEONG, "nsq": NSQ}.get(kind, MYEONG)
    if not os.path.exists(path):
        return ImageFont.truetype(SD, size, index=SD_I["h"])
    return ImageFont.truetype(path, size)


def text(d, xy, s, font, fill, anchor="mm", maxw=None, spacing=0):
    """가운데 정렬 텍스트, maxw 를 넘으면 글꼴을 줄인다."""
    if maxw:
        while d.textlength(s, font=font) > maxw and font.size > 8:
            font = font.font_variant(size=font.size - 2)
    d.text(xy, s, font=font, fill=fill, anchor=anchor)
    return font


def noise(h, w, scale, seed=0, octaves=4):
    """값 노이즈 (0..1)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(1, int(scale * 2 ** o))
        g = rng.random((s + 1, s + 1)).astype(np.float32)
        g[-1, :] = g[0, :]
        g[:, -1] = g[:, 0]
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        out += np.asarray(im, np.float32) / 255 * amp
        tot += amp
        amp *= 0.5
    return out / tot


def paper_grain(im, amount=10, seed=1):
    a = np.asarray(im.convert("RGB"), np.float32)
    n = noise(a.shape[0], a.shape[1], 24, seed, 3) - 0.5
    f = np.random.default_rng(seed).normal(0, 1, a.shape[:2]).astype(np.float32)
    a += (n * amount * 1.6 + f * amount * 0.35)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def aged(im, strength=0.25, seed=3):
    """누렇게 바래고 가장자리가 어두운 종이."""
    a = np.asarray(im.convert("RGB"), np.float32)
    h, w = a.shape[:2]
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    e = np.minimum(np.minimum(x, w - 1 - x) / w, np.minimum(y, h - 1 - y) / h)
    edge = np.clip(1 - e / 0.08, 0, 1) ** 2
    blot = noise(h, w, 3, seed, 4)
    yel = np.array([236, 214, 160], np.float32)
    k = (strength * (0.4 + 0.6 * blot) + edge * strength * 0.8)[..., None]
    a = a * (1 - k * 0.35) + yel * k * 0.35
    a *= (1 - edge * strength * 0.25)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def rr(d, box, r, **kw):
    d.rounded_rectangle(box, r, **kw)


def save(im, path):
    tmp = path + ".tmp" + os.path.splitext(path)[1]
    if path.endswith(".jpg"):
        im.convert("RGB").save(tmp, quality=92)
    else:
        im.save(tmp)
    os.replace(tmp, path)


# ---------------------------------------------------------------- 문 전단지 아틀라스
def flyer(w, h, bg, fg, title, sub, phone, small, accent, seed, title_font="black"):
    im = Image.new("RGB", (w, h), bg)
    d = ImageDraw.Draw(im)
    # 인쇄 그라데이션 + 흰 테두리 (자석 전단지)
    rr(d, (14, 14, w - 14, h - 14), 26, outline=accent, width=6)
    text(d, (w / 2, h * 0.30), title, F(title_font, int(h * 0.26)), fg, maxw=w * 0.86)
    text(d, (w / 2, h * 0.53), sub, F("sd-b", int(h * 0.075)), fg, maxw=w * 0.84)
    rr(d, (w * 0.12, h * 0.63, w * 0.88, h * 0.82), 18, fill=accent)
    text(d, (w / 2, h * 0.725), phone, F("black", int(h * 0.13)), bg, maxw=w * 0.72)
    text(d, (w / 2, h * 0.9), small, F("sd-sb", int(h * 0.05)), fg, maxw=w * 0.84)
    return paper_grain(im, 6, seed)


def door_flyers(out):
    W = 2048
    im = Image.new("RGB", (W, W), (230, 226, 214))
    fw, fh = 1024, 630
    items = [
        ((215, 198, 74), (34, 34, 34), "24시 열쇠", "도어락 · 현관문 · 금고 · 자동차", "☎ 555-0100", "연중무휴 · 출장 30분 내 도착", (34, 34, 34)),
        ((180, 41, 31), (248, 232, 200), "중화 반점", "짜장면 · 짬뽕 · 탕수육 · 군만두", "☎ 555-0100", "배달 환영 · 2만원 이상 군만두 서비스", (248, 210, 90)),
        ((216, 120, 42), (255, 255, 255), "치킨 배달", "후라이드 · 양념 · 반반 · 순살", "☎ 555-0100", "한 마리 16,000원 · 콜라 서비스", (110, 40, 10)),
    ]
    for i, (bg, fg, t, s, p, sm, ac) in enumerate(items):
        f = flyer(fw, fh, bg, fg, t, s, p, sm, ac, 10 + i)
        im.paste(f, ((i % 2) * fw, (i // 2) * fh))
    # 가스 점검 안내 (종이 스티커)
    g = Image.new("RGB", (fw, fh), (232, 228, 216))
    d = ImageDraw.Draw(g)
    d.rectangle((0, 0, fw, fh * 0.2), fill=(40, 70, 130))
    text(d, (fw / 2, fh * 0.1), "도시가스 안전 점검", F("sd-h", 64), (240, 240, 240), maxw=fw * 0.9)
    text(d, (fw / 2, fh * 0.36), "가스 점검", F("black", 150), (51, 51, 68))
    text(d, (fw * 0.08, fh * 0.56), "점검일 :  11월", F("sd-b", 46), (51, 51, 68), anchor="lm")
    d.text((fw * 0.47, fh * 0.56), "12일 (목) 오전", font=F("pen", 70), fill=(30, 40, 150), anchor="lm")
    text(d, (fw * 0.08, fh * 0.68), "부재 시 아래 번호로 연락 바랍니다.", F("sd-m", 38), (51, 51, 68), anchor="lm")
    text(d, (fw / 2, fh * 0.83), "☎ 555-0100", F("black", 80), (40, 70, 130))
    text(d, (fw / 2, fh * 0.95), "한빛도시가스 고객센터", F("sd-sb", 30), (90, 90, 100))
    g = aged(paper_grain(g, 8, 21), 0.3, 22)
    im.paste(g, (fw, fh))
    # 할아버지 손글씨 메모 (노란 메모지 + 테이프)
    m = Image.new("RGB", (640, 768), (246, 232, 160))
    d = ImageDraw.Draw(m)
    for y in range(170, 768, 86):
        d.line((30, y, 610, y), fill=(200, 170, 120), width=2)
    pen = F("pen", 92)
    lines = ["나가기 전에!", "가스 밸브 잠금", "지갑 · 열쇠", "약 먹었나?", "불고기 세트"]
    for i, s in enumerate(lines):
        d.text((48 + (i % 2) * 8, 150 + i * 86), s, font=pen, fill=(28, 34, 90), anchor="ls")
    d.line((40, 158, 360, 162), fill=(170, 30, 30), width=5)
    m = aged(paper_grain(m, 7, 31), 0.35, 32)
    im.paste(m, (0, 1280))
    # 테이프 조각 (반투명 느낌의 색)
    t = Image.new("RGB", (400, 120), (226, 214, 170))
    t = paper_grain(t, 10, 41)
    im.paste(t, (700, 1300))
    save(im, out)


# ---------------------------------------------------------------- 현관 인쇄물 아틀라스 (사진3 + 시계판 + 달력)
def clock_face(s):
    im = Image.new("RGB", (s, s), (226, 218, 196))
    d = ImageDraw.Draw(im)
    c = s / 2
    d.ellipse((4, 4, s - 4, s - 4), fill=(236, 230, 212), outline=(120, 110, 90), width=4)
    for i in range(60):
        a = i * math.pi / 30
        r0 = c * (0.86 if i % 5 else 0.80)
        w = 7 if i % 5 == 0 else 3
        d.line((c + math.sin(a) * r0, c - math.cos(a) * r0, c + math.sin(a) * c * 0.92, c - math.cos(a) * c * 0.92),
               fill=(40, 36, 30), width=w)
    f = F("sd-b", int(s * 0.1))
    for i in range(1, 13):
        a = i * math.pi / 6
        text(d, (c + math.sin(a) * c * 0.66, c - math.cos(a) * c * 0.66), str(i), f, (45, 40, 34))
    text(d, (c, c * 0.62), "한빛", F("sd-h", int(s * 0.05)), (150, 40, 30))
    text(d, (c, c * 1.42), "QUARTZ", F("sd-sb", int(s * 0.035)), (90, 84, 74))
    return aged(paper_grain(im, 5, 51), 0.35, 52)


def calendar(w, h):
    im = Image.new("RGB", (w, h), (236, 230, 215))
    d = ImageDraw.Draw(im)
    # 위: 산수화 풍경 (은행 달력)
    ph = int(h * 0.36)
    land = old_photo("fish_hoek_IMG_0028.jpg", (0, 420, 5292, 420 + int(5292 * ph / w)), w, ph, 61, border=0.0, fade=0.0)
    im.paste(land, (0, 0))
    d.rectangle((0, ph, w, ph + int(h * 0.006)), fill=(165, 60, 48))
    text(d, (w * 0.18, h * 0.43), "11", F("black", int(h * 0.09)), (61, 55, 46))
    text(d, (w * 0.42, h * 0.415), "NOVEMBER", F("sd-b", int(h * 0.024)), (61, 55, 46))
    text(d, (w * 0.42, h * 0.445), "2026", F("sd-sb", int(h * 0.022)), (120, 110, 96))
    text(d, (w * 0.82, h * 0.43), "입동 7일 · 소설 22일", F("sd-m", int(h * 0.016)), (120, 110, 96))
    days = ["일", "월", "화", "수", "목", "금", "토"]
    cw = w * 0.13
    x0 = w * 0.1
    col = lambda i: (177, 58, 46) if i == 0 else (53, 89, 140) if i == 6 else (61, 55, 46)
    fd = F("sd-b", int(h * 0.022))
    for i, s in enumerate(days):
        text(d, (x0 + i * cw, h * 0.49), s, fd, col(i))
    fn = F("sd-b", int(h * 0.038))
    fl = F("sd-r", int(h * 0.0125))
    for n in range(1, 31):
        r, c = divmod(n - 1, 7)
        y = h * (0.545 + r * 0.075)
        text(d, (x0 + c * cw, y), str(n), fn, col(c))
        lunar = n + 21 if n + 21 <= 30 else n + 21 - 30
        mo = "9." if n + 21 <= 30 else "10."
        text(d, (x0 + c * cw + cw * 0.28, y + h * 0.026), mo + str(lunar), fl, (140, 132, 118))
    # 오늘(5일) 빨간 펜 동그라미
    cx, cy = x0 + 4 * cw, h * 0.545
    for k in range(3):
        d.ellipse((cx - 46 - k, cy - 38 - k, cx + 44 + k, cy + 40 + k), outline=(190, 30, 30), width=4)
    d.text((x0 + 3 * cw - 20, h * 0.545 + h * 0.035), "병원", font=F("pen", int(h * 0.03)), fill=(30, 40, 140), anchor="mm")
    d.rectangle((0, h * 0.925, w, h), fill=(165, 60, 48))
    text(d, (w / 2, h * 0.952), "시장은행", F("black", int(h * 0.038)), (244, 239, 226))
    text(d, (w / 2, h * 0.983), "고객과 함께 걸어온 50년 · ☎ 1588-0000", F("sd-sb", int(h * 0.013)), (244, 230, 210))
    return aged(paper_grain(im, 5, 63), 0.25, 64)


SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
       "8": "abcdefg", "9": "abcdfg"}


def seg7(d, x, y, s, hg, col):
    """필름 카메라 날짜 각인용 7세그먼트 숫자."""
    w, t = hg * 0.5, hg * 0.13
    for ch in s:
        if ch == "'":
            d.rectangle((x, y, x + t, y + t * 2.4), fill=col)
            x += t * 2.6
            continue
        if ch == " ":
            x += w * 0.7
            continue
        bx = {"a": (x, y, x + w, y + t), "g": (x, y + hg / 2 - t / 2, x + w, y + hg / 2 + t / 2),
              "d": (x, y + hg - t, x + w, y + hg), "f": (x, y, x + t, y + hg / 2), "b": (x + w - t, y, x + w, y + hg / 2),
              "e": (x, y + hg / 2, x + t, y + hg), "c": (x + w - t, y + hg / 2, x + w, y + hg)}
        for sg in SEG[ch]:
            d.rectangle(bx[sg], fill=col)
        x += w + t * 1.8


def backplate(name):
    """Poly Haven(CC0) HDRI 배경 사진 '<hdri>_IMG_<n>.jpg'. 캐시에 없으면 받는다."""
    p = os.path.join(BP, name)
    if not os.path.exists(p):
        import urllib.request
        hdri, img = name[:-4].split("_IMG_")
        os.makedirs(BP, exist_ok=True)
        urllib.request.urlretrieve("https://dl.polyhaven.org/file/ph-assets/HDRIs/extra/Backplates/"
                                   f"{hdri}/jpg_pretty/IMG_{img}.jpg", p + ".part")
        os.replace(p + ".part", p)
    return p


def old_photo(src, box, w, h, seed, stamp=None, border=0.04, fade=1.0):
    """Poly Haven(CC0) 사진 일부를 바랜 컬러 인화지로: 채도/대비 낮춤, 누런 변색, 그레인, 흰 테두리, 날짜 각인."""
    bw = int(min(w, h) * border)
    pw, ph = w - 2 * bw, h - 2 * bw
    im = Image.open(backplate(src)).convert("RGB").crop(box).resize((pw, ph), Image.LANCZOS)
    a = np.asarray(im, np.float32) / 255
    g = a.mean(axis=2, keepdims=True)
    a = g + (a - g) * (1 - 0.35 * fade)
    a = 0.07 * fade + a * (1 - 0.13 * fade)
    a = a * (np.array([1.0, 0.95, 0.83]) * fade + (1 - fade))
    yy, xx = np.mgrid[0:ph, 0:pw].astype(np.float32)
    a *= (1 - 0.22 * fade * (((xx / pw - 0.5) * 2) ** 2 + ((yy / ph - 0.5) * 2) ** 2) / 2)[..., None]
    a += np.random.default_rng(seed).normal(0, 0.022, a.shape[:2])[..., None]
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    if stamp:
        lay = Image.new("RGB", im.size, (0, 0, 0))
        dl = ImageDraw.Draw(lay)
        hg = ph * 0.05
        seg7(dl, pw * 0.70, ph * 0.80, stamp, hg, (255, 120, 36))
        core = np.asarray(lay.filter(ImageFilter.GaussianBlur(hg * 0.03)), np.float32)
        halo = np.asarray(lay.filter(ImageFilter.GaussianBlur(hg * 0.25)), np.float32)
        k = core.max(axis=2, keepdims=True) / 255 * 0.85
        a2 = np.asarray(im, np.float32) * (1 - k) + core * 0.95 + halo * 0.18
        im = Image.fromarray(np.clip(a2, 0, 255).astype(np.uint8))
    out = Image.new("RGB", (w, h), (236, 232, 220))
    out.paste(im, (bw, bw))
    return aged(paper_grain(out, 3, seed), 0.22 * fade, seed + 1) if fade else out


def hanji(w, h, seed, base=(232, 222, 198)):
    """한지: 섬유결 + 가는 섬유 가닥."""
    a = np.ones((h, w, 3), np.float32) * np.array(base, np.float32)
    a += (noise(h, w, 30, seed, 4) - 0.5)[..., None] * 20
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    rng = random.Random(seed)
    for _ in range(int(w * h / 900)):
        x, y, an, ln = rng.random() * w, rng.random() * h, rng.random() * math.pi, rng.uniform(5, 26)
        c = tuple(int(v * rng.uniform(0.9, 0.97)) for v in base)
        d.line((x, y, x + math.cos(an) * ln, y + math.sin(an) * ln), fill=c, width=1)
    return im


def ink(im, draw_fn, col=(24, 20, 18), bleed=1.0, alpha=0.95):
    """먹/인주: 마스크에 그리고 살짝 번지게."""
    m = Image.new("L", im.size, 0)
    draw_fn(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(bleed))
    k = np.asarray(m, np.float32)[..., None] / 255 * alpha
    a = np.asarray(im, np.float32)
    return Image.fromarray(np.clip(a * (1 - k) + np.array(col, np.float32) * k, 0, 255).astype(np.uint8))


def gahun(w, h, seed=81):
    """가훈 액자: 한지에 家和萬事成 (행서) + 서명 + 낙관."""
    im = hanji(w, h, seed)
    f = F("xing", int(h * 0.15))

    def body(d):
        for i, ch in enumerate("家和萬事成"):
            d.text((w * 0.56, h * (0.12 + i * 0.165)), ch, font=f, fill=255, anchor="mm")
    im = ink(im, body, bleed=1.1)
    fs = F("gung", int(h * 0.036))

    def sign(d):
        for i, ch in enumerate("무인년봄운곡"):
            d.text((w * 0.25, h * (0.34 + i * 0.045)), ch, font=fs, fill=255, anchor="mm")
    im = ink(im, sign, bleed=0.6)
    sx, sy, ss = w * 0.25, h * 0.68, w * 0.06
    fz = F("myeong", int(ss * 0.8))

    def seal(d):
        d.rectangle((sx - ss, sy - ss, sx + ss, sy + ss), outline=255, width=max(2, int(ss * 0.12)))
        for k, ch in enumerate("雲谷"):
            d.text((sx, sy - ss * 0.45 + k * ss * 0.9), ch, font=fz, fill=255, anchor="mm")
    im = ink(im, seal, col=(178, 40, 34), bleed=0.5, alpha=0.85)
    return aged(im, 0.3, seed + 2)


def certificate(w, h, seed=91):
    """표창장 (A4): 금색 테두리, 명조 본문, 붉은 직인."""
    im = Image.new("RGB", (w, h), (241, 237, 224))
    d = ImageDraw.Draw(im)
    m = int(w * 0.045)
    gold = (168, 132, 62)
    i1 = w // 45
    d.rectangle((m, m, w - m, h - m), outline=gold, width=max(3, w // 110))
    d.rectangle((m + i1, m + i1, w - m - i1, h - m - i1), outline=gold, width=max(1, w // 300))
    for cx in (m + i1, w - m - i1):
        for cy in (m + i1, h - m - i1):
            r = w // 40
            d.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=gold)
    fm = lambda k: F("myeong", int(h * k))
    ic = (40, 36, 32)
    d.text((w * 0.13, h * 0.09), "제 98-127 호", font=fm(0.022), fill=ic, anchor="lm")
    d.text((w / 2, h * 0.2), "표 창 장", font=fm(0.075), fill=(30, 28, 26), anchor="mm", stroke_width=max(1, h // 400),
           stroke_fill=(30, 28, 26))
    d.text((w * 0.52, h * 0.31), "성 명 :  김 영 수", font=fm(0.03), fill=ic, anchor="lm")
    for i, ln in enumerate(("위 사람은 평소 맡은 바 직무에 성실히", "근무하여 왔으며 특히 30년간 회사",
                            "발전에 이바지한 공이 크므로 이에", "표창합니다.")):
        d.text((w * 0.13, h * (0.42 + i * 0.065)), ln, font=fm(0.032), fill=ic, anchor="lm")
    d.text((w / 2, h * 0.73), "1998년  5월  1일", font=fm(0.03), fill=ic, anchor="mm")
    d.text((w / 2, h * 0.82), "한빛운수주식회사", font=fm(0.034), fill=(30, 28, 26), anchor="mm")
    d.text((w / 2, h * 0.875), "대표이사   박 정 호", font=fm(0.036), fill=(30, 28, 26), anchor="mm")
    sx, sy, ss = w * 0.8, h * 0.87, w * 0.055
    fz = F("myeong", int(ss * 0.62))

    def seal(dd):
        dd.rectangle((sx - ss, sy - ss, sx + ss, sy + ss), outline=255, width=max(2, int(ss * 0.1)))
        for k, ch in enumerate(("代表", "理事")):
            dd.text((sx, sy - ss * 0.42 + k * ss * 0.84), ch, font=fz, fill=255, anchor="mm")
    im = ink(im, seal, col=(186, 36, 30), bleed=0.6, alpha=0.8)
    return aged(paper_grain(im, 4, seed), 0.3, seed + 1)


def floor_grime(out):
    """현관 타일 얼룩 데칼 (RGBA): 신발 밑창 자국, 흙먼지, 모서리 먼지 띠."""
    W, H = 1024, 1024
    rng = random.Random(5)
    al = noise(H, W, 5, 21, 5) ** 2 * 120
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    e = np.minimum(np.minimum(xx, W - 1 - xx), np.minimum(yy, H - 1 - yy)) / W
    al += np.clip(1 - e / 0.05, 0, 1) ** 1.5 * 150 * (0.5 + noise(H, W, 9, 22, 3))
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for _ in range(26):  # 밑창 자국 (발볼+뒤꿈치 타원, 문 쪽을 향함)
        x, y, a = rng.uniform(0.15, 0.85) * W, rng.uniform(0.1, 0.9) * H, rng.uniform(-0.5, 0.5)
        for (dy, rx, ry) in ((-70, 42, 60), (60, 34, 40)):
            cx, cy = x + math.sin(a) * dy, y + math.cos(a) * dy
            d.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), outline=int(rng.uniform(60, 120)), width=rng.randint(3, 7))
    al += np.asarray(m.filter(ImageFilter.GaussianBlur(3)), np.float32) * (0.4 + noise(H, W, 14, 23, 3))
    al = np.clip(al * (0.55 + 0.6 * noise(H, W, 3, 24, 2)), 0, 200)
    col = np.ones((H, W, 3), np.float32) * np.array([74, 64, 52], np.float32)
    col += (noise(H, W, 40, 25, 3) - 0.5)[..., None] * 30
    rgba = np.dstack([np.clip(col, 0, 255), al]).astype(np.uint8)
    save(Image.fromarray(rgba, "RGBA"), out)


def entry_prints(out):
    S = 2048
    im = Image.new("RGB", (S, S), (220, 214, 200))
    # 큰 액자: 운해 일출 사진 (옛 인화, 날짜 각인) / 작은 액자: 가훈, 표창장 (얼굴 그림 없음)
    im.paste(old_photo("cape_hill_IMG_0258.jpg", (160, 0, 5156, 3543), 1024, 725, 71, "'98 5 5"), (0, 0))
    im.paste(gahun(512, 683), (1040, 0))
    im.paste(certificate(472, 614), (1568, 0))
    im.paste(clock_face(1000), (12, 1036))
    cal = calendar(708, 1022)
    im.paste(cal, (1240, 1024))
    save(im, out)


# ---------------------------------------------------------------- 약 봉투 (앞 | 뒤)
def medbag(out):
    W, H = 1024, 1260
    im = Image.new("RGB", (W * 2, H), (240, 237, 228))
    d = ImageDraw.Draw(im)
    g = (44, 110, 73)
    # 앞면
    d.rectangle((0, 0, W, 70), fill=g)
    text(d, (W / 2, 210), "약 봉 투", F("black", 150), g)
    text(d, (W * 0.12, 360), "성명 :", F("sd-b", 46), (60, 60, 60), anchor="lm")
    d.text((W * 0.33, 362), "김 영 수", font=F("pen", 92), fill=(30, 40, 120), anchor="lm")
    text(d, (W * 0.7, 360), "님", F("sd-b", 46), (60, 60, 60), anchor="lm")
    d.line((W * 0.3, 395, W * 0.68, 395), fill=(120, 120, 120), width=2)
    text(d, (W / 2, 500), "아침 저녁 식후", F("sd-h", 96), (40, 40, 40))
    text(d, (W / 2, 630), "30분", F("sd-h", 110), (40, 40, 40))
    text(d, (W * 0.12, 745), "1일 2회 · 3일분", F("sd-b", 48), (70, 70, 70), anchor="lm")
    d.text((W * 0.68, 750), "✓", font=F("sd-b", 70), fill=(30, 40, 120), anchor="lm")
    text(d, (W * 0.12, 815), "조제일자 2026. 11. 02", F("sd-m", 40), (90, 90, 90), anchor="lm")
    d.rectangle((W * 0.1, 880, W * 0.9, 1130), outline=(119, 119, 119), width=4)
    text(d, (W / 2, 955), "새봄 약국", F("sd-h", 92), g)
    text(d, (W / 2, 1040), "약사 이 정 미  ·  ☎ 02-555-0123", F("sd-m", 36), (80, 80, 80))
    text(d, (W / 2, 1092), "서울시 ○○구 시장길 12", F("sd-r", 32), (100, 100, 100))
    text(d, (W / 2, 1195), "약은 약사에게, 진료는 의사에게", F("sd-sb", 38), g)
    # 뒷면
    o = W
    d.rectangle((o, 0, o + W, 70), fill=g)
    text(d, (o + W / 2, 170), "복약 안내", F("sd-h", 80), g)
    rows = ["혈압약 (아침)", "소화제 (식후)", "관절약 (저녁)", "위장약 (식후)"]
    for i, s in enumerate(rows):
        y = 300 + i * 120
        d.rectangle((o + 90, y - 40, o + W - 90, y + 40), outline=(160, 160, 160), width=2)
        text(d, (o + 130, y), s, F("sd-b", 50), (60, 60, 60), anchor="lm")
        text(d, (o + W - 130, y), "1정", F("sd-b", 50), (60, 60, 60), anchor="rm")
    text(d, (o + W / 2, 860), "※ 직사광선을 피해 보관하세요.", F("sd-m", 40), (90, 90, 90))
    text(d, (o + W / 2, 930), "※ 어린이 손이 닿지 않는 곳에 두세요.", F("sd-m", 40), (90, 90, 90))
    text(d, (o + W / 2, 1150), "새봄 약국", F("sd-h", 70), g)
    im = aged(paper_grain(im, 6, 81), 0.18, 82)
    save(im, out)


# ---------------------------------------------------------------- 라디오 앞판 / 인터폰 / 스위치 라벨
def radio(out):
    W, H = 1024, 576
    im = Image.new("RGB", (W, H), (88, 74, 60))
    d = ImageDraw.Draw(im)
    # 스피커 그릴 (왼쪽)
    d.rectangle((40, 40, 470, 536), fill=(52, 46, 40))
    for y in range(60, 520, 18):
        for x in range(60 + (y // 18 % 2) * 9, 456, 18):
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(18, 16, 14))
    # 다이얼 창 (오른쪽)
    d.rectangle((520, 70, 984, 260), fill=(216, 200, 140))
    for i, (lab, vals) in enumerate((("FM", [88, 92, 96, 100, 104, 108]), ("AM", [53, 60, 70, 90, 120, 160]))):
        y = 120 + i * 90
        text(d, (548, y), lab, F("sd-b", 30), (60, 50, 40), anchor="lm")
        for k, v in enumerate(vals):
            x = 610 + k * 70
            d.line((x, y + 18, x, y + 34), fill=(60, 50, 40), width=3)
            text(d, (x, y), str(v), F("sd-sb", 26), (60, 50, 40))
    d.line((760, 80, 760, 250), fill=(200, 40, 30), width=5)
    text(d, (750, 330), "SANGRAN  2-BAND RADIO", F("sd-b", 32), (210, 196, 160))
    text(d, (620, 450), "VOLUME", F("sd-sb", 24), (200, 186, 150))
    text(d, (880, 450), "TUNING", F("sd-sb", 24), (200, 186, 150))
    save(paper_grain(im, 6, 91), out)


def intercom(out):
    W = 1024
    im = Image.new("RGB", (W, W), (226, 222, 210))
    d = ImageDraw.Draw(im)
    labels = [("통화", (60, 120, 70)), ("문열림", (170, 60, 50)), ("경비실", (60, 80, 140)), ("인터폰", (90, 90, 90))]
    for i, (s, c) in enumerate(labels):
        x, y = (i % 2) * 512, (i // 2) * 256
        rr(d, (x + 30, y + 40, x + 482, y + 216), 40, fill=(236, 233, 224), outline=(150, 146, 136), width=6)
        text(d, (x + 256, y + 128), s, F("sd-h", 96), c)
    d.rectangle((0, 512, W, W), fill=(200, 196, 186))
    text(d, (W / 2, 620), "현관 · 거실", F("pen", 120), (30, 40, 120))
    text(d, (W / 2, 820), "분 전 반", F("sd-h", 110), (70, 70, 70))
    text(d, (W / 2, 930), "누전 차단기 · 안전 점검", F("sd-sb", 52), (90, 90, 90))
    save(paper_grain(im, 4, 95), out)


# ---------------------------------------------------------------- 타일 (벽지·천장지·현관 매트)
def height_to_normal(hgt, strength):
    gy, gx = np.gradient(hgt)
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(hgt)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    return Image.fromarray(((n * 0.5 + 0.5) * 255).astype(np.uint8))


def tileable_noise(n, scale, seed, octaves=4):
    return noise(n, n, scale, seed, octaves)


def wallpaper(outdir, name, base, motif=True, seed=1):
    N = 2048
    rng = np.random.default_rng(seed)
    fib = tileable_noise(N, 64, seed, 3)
    fine = rng.normal(0, 1, (N, N)).astype(np.float32)
    fine = np.asarray(Image.fromarray(((fine * 0.15 + 0.5).clip(0, 1) * 255).astype(np.uint8)).filter(
        ImageFilter.GaussianBlur(0.8)), np.float32) / 255
    # 가로 섬유결 (실크벽지 엠보)
    weave = np.asarray(Image.fromarray(((rng.random((N, N // 6)) * 255)).astype(np.uint8)).resize((N, N), Image.BILINEAR),
                       np.float32) / 255
    h = fib * 0.5 + fine * 0.6 + weave * 0.35
    col = np.ones((N, N, 3), np.float32) * np.array(base, np.float32)
    if motif:
        m = Image.new("L", (N, N), 0)
        d = ImageDraw.Draw(m)
        step = 128
        for yy in range(0, N + step, step):
            for xx in range((yy // step % 2) * step // 2, N + step, step):
                for k in range(6):
                    a = k * math.pi / 3
                    cx, cy = xx + math.sin(a) * 16, yy - math.cos(a) * 16
                    d.ellipse((cx - 6, cy - 6, cx + 6, cy + 6), fill=255)
                d.ellipse((xx - 4, yy - 4, xx + 4, yy + 4), fill=180)
        mm = np.asarray(m.filter(ImageFilter.GaussianBlur(1.5)), np.float32) / 255
        h += mm * 0.8
        col -= mm[..., None] * np.array([14, 12, 8], np.float32)
    # 1.06m 폭 이음매 (텍스처 가장자리)
    seam = np.zeros(N, np.float32)
    seam[:3] = 1
    seam[-2:] = 0.6
    col -= seam[None, :, None] * 18
    h -= seam[None, :] * 0.6
    blot = tileable_noise(N, 2, seed + 5, 3)
    col *= (0.94 + 0.08 * blot)[..., None]
    col += (fine - 0.5)[..., None] * 10
    save(Image.fromarray(np.clip(col, 0, 255).astype(np.uint8)), os.path.join(outdir, name + "_diff.jpg"))
    save(height_to_normal(h, 1.5), os.path.join(outdir, name + "_nor.png"))
    r = np.clip(0.78 + (fib - 0.5) * 0.15 - (h - h.mean()) * 0.05, 0, 1)
    save(Image.fromarray((r * 255).astype(np.uint8)), os.path.join(outdir, name + "_rough.png"))


def doormat(out):
    W, H = 1440, 840
    im = Image.new("RGB", (W, H), (90, 80, 68))
    a = np.asarray(im, np.float32).copy()
    rng = np.random.default_rng(7)
    fib = rng.normal(0, 1, (H, W)).astype(np.float32)
    a += fib[..., None] * 14
    for y in range(0, H, 12):
        a[y:y + 4] *= 0.78
    bw = 70
    a[:bw] = a[:bw] * 0.65 + np.array([122, 109, 88]) * 0.35
    a[-bw:] = a[-bw:] * 0.65 + np.array([122, 109, 88]) * 0.35
    a[:, :bw] = a[:, :bw] * 0.65 + np.array([122, 109, 88]) * 0.35
    a[:, -bw:] = a[:, -bw:] * 0.65 + np.array([122, 109, 88]) * 0.35
    wear = noise(H, W, 3, 9, 3)
    a *= (0.85 + 0.25 * wear)[..., None]
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    text(d, (W / 2, H / 2), "WELCOME", F("sd-h", 150), (112, 100, 82))
    save(im, out)


JOBS = {
    "door_flyers.png": door_flyers,
    "entry_prints.png": entry_prints,
    "medbag.png": medbag,
    "radio.png": radio,
    "intercom.png": intercom,
    "doormat.jpg": doormat,
    "floor_grime.png": floor_grime,
    "wallpaper": lambda o: wallpaper(os.path.dirname(o), "wallpaper", (214, 202, 172), True, 1),
    "ceilpaper": lambda o: wallpaper(os.path.dirname(o), "ceilpaper", (226, 222, 208), False, 2),
}

if __name__ == "__main__":
    name, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    JOBS[name](os.path.join(outdir, name))
    print("tex2d ok", name)
