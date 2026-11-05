"""Street 그룹 2D 텍스처 (Pillow + numpy). venv python 으로 실행:  python -I _textures.py <출력폴더>
아틀라스 PNG + 같은 이름 .json (영역 이름 -> UV 사각형 [u0, v0, u1, v1], v 는 아래가 0) 을 만든다."""
import os, sys, json, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tex")
CACHE = os.path.abspath(os.path.join(OUT, ".."))
os.makedirs(OUT, exist_ok=True)
HOME = os.path.expanduser("~")
F = {
    "eb": HOME + "/Library/Fonts/NanumSquareEB.ttf", "b": HOME + "/Library/Fonts/NanumSquareB.ttf",
    "r": HOME + "/Library/Fonts/NanumSquareR.ttf", "l": HOME + "/Library/Fonts/NanumSquareL.ttf",
    "han": CACHE + "/fonts/BlackHanSans-Regular.ttf", "pen": CACHE + "/fonts/NanumPenScript-Regular.ttf",
    "do": CACHE + "/fonts/DoHyeon-Regular.ttf", "jua": CACHE + "/fonts/Jua-Regular.ttf",
}
R = random.Random(20261105)


def font(k, s):
    return ImageFont.truetype(F[k], int(s))


def text(d, xy, s, k, size, fill, anchor="mm", maxw=None, sx=1.0):
    """가운데 정렬 텍스트. maxw 를 넘으면 가로로 줄인다(프로토타입 Mt 와 같은 방식)."""
    if "·" in s and k in ("han", "do", "jua", "pen"):
        k = "eb"  # 이 폰트들에는 가운뎃점이 없다
    f = font(k, size)
    w = d.textlength(s, font=f)
    scale = min(1.0, maxw / w) if maxw else 1.0
    scale *= sx
    if abs(scale - 1) < 1e-3:
        d.text(xy, s, font=f, fill=fill, anchor=anchor)
        return
    # 가로 압축: 따로 그려서 붙인다
    bb = d.textbbox((0, 0), s, font=f, anchor="lt")
    tw, th = bb[2] + 4, bb[3] + 8
    im = Image.new("L", (int(tw), int(th)), 0)
    ImageDraw.Draw(im).text((2, 2), s, font=f, fill=255, anchor="lt")
    nw = max(1, int(tw * scale))
    im = im.resize((nw, int(th)), Image.LANCZOS)
    base = d._image
    col = Image.new("RGBA", im.size, fill if isinstance(fill, tuple) else ImageColorRGB(fill))
    x, y = xy
    if anchor[0] == "m":
        x -= nw / 2
    elif anchor[0] == "r":
        x -= nw
    if anchor[1] == "m":
        y -= (bb[3] + bb[1]) / 2 + 2
    base.paste(col, (int(x), int(y)), im)


def ImageColorRGB(c):
    from PIL import ImageColor
    return ImageColor.getrgb(c)


def noise(w, h, scale, seed, octaves=4):
    """부드러운 값 노이즈 0..1."""
    rng = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gw, gh = max(2, int(w / scale * 2 ** o) + 2), max(2, int(h / scale * 2 ** o) + 2)
        g = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
        acc += np.asarray(g.resize((w, h), Image.BICUBIC), np.float32) / 255 * amp
        tot += amp
        amp *= 0.5
    return acc / tot


def weather(im, amt=0.3, seed=1, fade=0.0, scratches=20, spots=40):
    """색 바램 + 위아래 때 + 긁힘 + 얼룩 (스티커/표지판 공통)."""
    im = im.convert("RGBA")
    a = np.asarray(im, np.float32) / 255
    h, w = a.shape[:2]
    rgb = a[..., :3]
    yy = np.linspace(0, 1, h)[:, None, None]          # 0 = 위, 1 = 아래
    if fade:  # 햇빛 바램: 위쪽일수록 강하게
        lum = rgb.mean(-1, keepdims=True)
        f = np.clip(fade * (1.35 - 0.7 * yy), 0, 1)
        rgb = rgb * (1 - f) + (lum * 0.6 + rgb * 0.4 + 0.12) * f
    n = noise(w, h, max(w, h) / 3, seed)
    grad = np.linspace(0, 1, h)[:, None] ** 2.2
    dirt = np.clip((n * 0.7 + grad * 0.8 - 0.35) * amt * 1.6, 0, 0.75)[..., None]
    rgb = rgb * (1 - dirt) + np.array([0.27, 0.24, 0.19]) * dirt
    # 빗물 때 줄: 위에서 흘러내린 가는 세로 줄 (아래로 갈수록 진함)
    rs = np.random.default_rng(seed + 11)
    cols = np.asarray(Image.fromarray((rs.random((1, max(4, w // 5))) * 255).astype(np.uint8)).resize(
        (w, 1), Image.BICUBIC), np.float32)[0] / 255
    st = np.clip((cols - 0.62) * 3.0, 0, 1)[None, :] * (0.35 + 0.65 * noise(w, h, max(8, h / 3), seed + 12, 2))
    st = (st * np.clip(yy[..., 0] * 1.4, 0, 1) * amt * 0.55)[..., None]
    rgb = rgb * (1 - st) + np.array([0.30, 0.27, 0.22]) * st
    fine = noise(w, h, 6, seed + 7, 2)[..., None]
    rgb = rgb * (0.94 + 0.1 * fine)
    a[..., :3] = np.clip(rgb, 0, 1)
    im = Image.fromarray((a * 255).astype(np.uint8), "RGBA")
    alpha = im.getchannel("A")
    d = ImageDraw.Draw(im, "RGBA")  # 섞어 그리기 (알파 덮어쓰기 금지)
    rr = random.Random(seed)
    for _ in range(scratches // 3):   # 긁힘: 적고 짧게, 모서리와 아래쪽에 몰림
        side = rr.random()
        if side < 0.5:
            x, y = rr.random() * w, h * (1 - 0.22 * rr.random() ** 1.5)
        elif side < 0.8:
            x, y = (rr.random() ** 2 * 0.12 if rr.random() < 0.5 else 1 - rr.random() ** 2 * 0.12) * w, rr.random() * h
        else:
            x, y = rr.random() * w, h * 0.1 * rr.random() ** 2
        ang = rr.uniform(-0.5, 0.5) + (math.pi / 2 if rr.random() < 0.3 else 0)
        L = rr.uniform(0.01, 0.05) * w
        d.line([(x, y), (x + math.cos(ang) * L, y + math.sin(ang) * L)],
               fill=(225, 222, 214, int(rr.uniform(25, 65))), width=1)
    for _ in range(spots):
        x, y, r = rr.random() * w, rr.random() * h, rr.uniform(1, 4) * w / 512
        d.ellipse([x - r, y - r, x + r, y + r], fill=(60, 52, 40, int(rr.uniform(30, 90))))
    im.putalpha(alpha)
    return im


def paper(w, h, col=(244, 242, 236), seed=0):
    im = Image.new("RGBA", (w, h), col + (255,))
    a = np.asarray(im, np.float32)
    n = noise(w, h, 40, seed, 3)
    a[..., :3] *= (0.95 + 0.06 * n)[..., None]
    # 접힌 자국
    for fx in (0.5,):
        x = int(w * fx)
        a[:, x - 2:x + 2, :3] *= 0.9
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def tape(im, box, seed):
    """투명 테이프 조각."""
    d = ImageDraw.Draw(im, "RGBA")
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(235, 228, 200, 70))
    d.line([(x0, y0), (x1, y0)], fill=(255, 255, 255, 60), width=2)


# ------------------------------------------------------------------ 아틀라스
class Atlas:
    def __init__(self, name, size, bg=(128, 128, 128, 255)):
        self.name, self.size = name, size
        self.im = Image.new("RGBA", (size, size), bg)
        self.rects = {}
        self.x = self.y = self.row = 0

    def add(self, key, item, pad=8):
        w, h = item.size
        if self.x + w + pad > self.size:
            self.x, self.y, self.row = 0, self.y + self.row + pad, 0
        assert self.y + h <= self.size, f"{self.name}: 공간 부족 ({key})"
        # 가장자리 번짐 방지: 테두리 픽셀을 pad 만큼 늘려 붙인다
        ext = item.resize((w + 2 * pad // 2, h + 2 * pad // 2))
        self.im.paste(ext, (max(0, self.x - pad // 2), max(0, self.y - pad // 2)))
        self.im.paste(item, (self.x, self.y))
        S = float(self.size)
        self.rects[key] = [self.x / S, 1 - (self.y + h) / S, (self.x + w) / S, 1 - self.y / S]
        self.x += w + pad
        self.row = max(self.row, h)

    def save(self, alpha=False):
        p = os.path.join(OUT, self.name + ".png")
        (self.im if alpha else self.im.convert("RGB")).save(p, optimize=True)
        json.dump(self.rects, open(os.path.join(OUT, self.name + ".json"), "w"), indent=1)
        print("tex", p, len(self.rects))


def flyer_room(w=400, h=566, seed=1):
    im = paper(w, h, (246, 244, 238), seed)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 92], fill=(196, 38, 36))
    text(d, (w / 2, 48), "급매물 직거래", "han", 54, (255, 248, 230), maxw=w - 30)
    text(d, (w / 2, 150), "원룸 · 투룸", "han", 62, (30, 30, 30), maxw=w - 30)
    text(d, (w / 2, 212), "전세 / 월세", "eb", 40, (196, 38, 36), maxw=w - 40)
    for i, s in enumerate(["보증금 500 / 월 35", "풀옵션 · 즉시입주", "시장 도보 3분", "반려동물 가능"]):
        text(d, (w / 2, 262 + i * 34), s, "b", 25, (40, 40, 40), maxw=w - 40)
    # 떼어가는 전화번호 띠
    n = 8
    tw = w / n
    for i in range(n):
        x = i * tw
        if i == 3:
            continue  # 하나는 뜯겨 나감
        d.line([(x, 410), (x, h)], fill=(150, 150, 150), width=1)
        t = Image.new("RGBA", (int(h - 420), int(tw)), (0, 0, 0, 0))
        text(ImageDraw.Draw(t), (t.size[0] / 2, t.size[1] / 2), "010-5557-3921", "b", 17, (20, 20, 20),
             maxw=t.size[0] - 8)
        t = t.rotate(90, expand=True)
        im.paste(t, (int(x + (tw - t.size[0]) / 2), 418), t)
    d.rectangle([3 * tw, 410, 4 * tw, h], fill=(0, 0, 0, 0))
    d.line([(0, 410), (w, 410)], fill=(120, 120, 120), width=2)
    im = weather(im, 0.35, seed, fade=0.1, scratches=6, spots=12)
    tape(im, (w / 2 - 50, 0, w / 2 + 50, 22), seed)
    return im


def flyer_move(w=400, h=566, seed=2):
    im = paper(w, h, (252, 228, 92), seed)
    d = ImageDraw.Draw(im)
    text(d, (w / 2, 70), "용달 이사", "han", 84, (20, 20, 20), maxw=w - 20)
    d.rectangle([20, 128, w - 20, 132], fill=(20, 20, 20))
    for i, s in enumerate(["1톤 화물 · 소형이사", "원룸이사 전문", "짐 보관 · 폐가구 수거", "당일 · 야간 가능"]):
        text(d, (w / 2, 172 + i * 44), s, "eb", 32, (40, 30, 20), maxw=w - 40)
    d.rounded_rectangle([24, 360, w - 24, 460], 14, fill=(190, 30, 30))
    text(d, (w / 2, 410), "010-5552-8417", "han", 50, (255, 245, 220), maxw=w - 60)
    text(d, (w / 2, 505), "친절 · 정직 · 저렴", "do", 36, (60, 40, 20), maxw=w - 40)
    im = weather(im, 0.4, seed, fade=0.25, scratches=8, spots=15)
    tape(im, (10, 10, 90, 34), seed)
    tape(im, (w - 90, h - 34, w - 10, h - 10), seed + 1)
    return im


def flyer_dog(w=400, h=566, seed=3):
    im = paper(w, h, (248, 248, 246), seed)
    d = ImageDraw.Draw(im)
    text(d, (w / 2, 52), "강아지를 찾습니다", "han", 50, (200, 30, 30), maxw=w - 24)
    # 흑백 사진 (복사기 느낌)
    ph = Image.new("RGB", (300, 210), (150, 150, 150))
    pd = ImageDraw.Draw(ph)
    pd.rectangle([0, 0, 300, 210], fill=(120, 118, 112))
    pd.ellipse([70, 40, 240, 200], fill=(232, 232, 230))
    pd.ellipse([110, 20, 200, 110], fill=(240, 240, 238))
    pd.ellipse([95, 40, 130, 100], fill=(210, 210, 208))
    pd.ellipse([180, 40, 215, 100], fill=(210, 210, 208))
    pd.ellipse([135, 58, 147, 70], fill=(30, 30, 30))
    pd.ellipse([163, 58, 175, 70], fill=(30, 30, 30))
    pd.ellipse([148, 78, 162, 88], fill=(40, 40, 40))
    ph = ph.filter(ImageFilter.GaussianBlur(1.6))
    pa = np.asarray(ph, np.float32)
    pa = pa.mean(-1, keepdims=True).repeat(3, -1) * 0.9 + 25 + np.random.default_rng(3).normal(0, 9, pa.shape)
    ph = Image.fromarray(np.clip(pa, 0, 255).astype(np.uint8))
    im.paste(ph, (50, 92))
    for i, s in enumerate(["말티즈 / 흰색 / 5살", "이름: 복실이 (빨간 목줄)", "11월 2일 시장 입구에서", "잃어버렸습니다"]):
        text(d, (w / 2, 330 + i * 32), s, "b", 24, (30, 30, 30), maxw=w - 40)
    text(d, (w / 2, 470), "사례금 드립니다", "han", 40, (200, 30, 30), maxw=w - 40)
    text(d, (w / 2, 520), "010-5559-0264", "eb", 34, (20, 20, 20), maxw=w - 40)
    im = weather(im, 0.3, seed, fade=0.05, scratches=5, spots=10)
    tape(im, (w / 2 - 60, 0, w / 2 + 60, 24), seed)
    return im


def flyer_academy(w=400, h=566, seed=4):
    im = paper(w, h, (240, 246, 250), seed)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 130], fill=(36, 84, 150))
    text(d, (w / 2, 45), "수학 · 영어", "han", 54, (255, 255, 255), maxw=w - 30)
    text(d, (w / 2, 102), "보습학원 신규모집", "eb", 34, (255, 230, 120), maxw=w - 30)
    for i, s in enumerate(["초 · 중등 내신 대비", "소수정예 6명", "1:1 오답 관리", "무료 레벨테스트"]):
        d.ellipse([40, 166 + i * 50, 58, 184 + i * 50], fill=(36, 84, 150))
        text(d, (70, 176 + i * 50), s, "b", 28, (30, 30, 40), anchor="lm", maxw=w - 90)
    d.rounded_rectangle([30, 400, w - 30, 470], 10, outline=(36, 84, 150), width=4)
    text(d, (w / 2, 436), "02) 555-0181", "han", 42, (36, 84, 150), maxw=w - 70)
    text(d, (w / 2, 510), "시장 입구 2층 (약국 위)", "r", 24, (60, 60, 70), maxw=w - 40)
    im = weather(im, 0.35, seed, fade=0.2, scratches=6, spots=8)
    tape(im, (w - 100, 4, w - 6, 28), seed)
    return im


def notice_no_ads(w=520, h=300, seed=5):
    im = Image.new("RGBA", (w, h), (238, 238, 232, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 74], fill=(200, 36, 30))
    text(d, (w / 2, 38), "광고물 부착 금지", "han", 50, (255, 255, 255), maxw=w - 30)
    text(d, (w / 2, 120), "이곳은 광고물 부착 금지 구역입니다", "b", 27, (30, 30, 30), maxw=w - 30)
    text(d, (w / 2, 165), "위반 시 옥외광고물법에 따라", "r", 24, (40, 40, 40), maxw=w - 30)
    text(d, (w / 2, 200), "과태료가 부과됩니다", "b", 24, (200, 36, 30), maxw=w - 30)
    text(d, (w / 2, 260), "은행골구청장", "eb", 28, (30, 30, 30), maxw=w - 30)
    return weather(im, 0.45, seed, fade=0.3, scratches=30, spots=30)


def pole_plate(w=240, h=400, seed=6):
    im = Image.new("RGBA", (w, h), (206, 208, 204, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, w - 6, h - 6], outline=(40, 40, 40), width=4)
    text(d, (w / 2, 46), "은행골", "eb", 46, (20, 20, 20), maxw=w - 30)
    text(d, (w / 2, 110), "23L", "han", 70, (20, 20, 20), maxw=w - 30)
    text(d, (w / 2, 172), "4", "han", 60, (20, 20, 20))
    # 바코드
    x = 30
    rr = random.Random(seed)
    while x < w - 30:
        bw = rr.choice([2, 2, 3, 5])
        d.rectangle([x, 220, x + bw - 1, 300], fill=(15, 15, 15))
        x += bw + rr.choice([2, 3, 4])
    text(d, (w / 2, 322), "9812 4471 03", "r", 22, (20, 20, 20))
    text(d, (w / 2, 365), "고장신고 123", "b", 24, (20, 20, 20), maxw=w - 30)
    return weather(im, 0.5, seed, fade=0.2, scratches=25, spots=25)


def hv_warning(w=360, h=260, seed=7):
    im = Image.new("RGBA", (w, h), (248, 246, 240, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 86], fill=(206, 32, 28))
    text(d, (w / 2, 45), "위험", "han", 66, (255, 255, 255))
    text(d, (w / 2, 128), "고압전기 22,900V", "eb", 36, (20, 20, 20), maxw=w - 26)
    text(d, (w / 2, 182), "감전주의 · 오르지 마십시오", "b", 26, (206, 32, 28), maxw=w - 26)
    d.rectangle([4, 4, w - 4, h - 4], outline=(30, 30, 30), width=3)
    return weather(im, 0.5, seed, fade=0.25, scratches=15, spots=20)


def hazard_band(w=1024, h=240, seed=8):
    """노랑/검정 사선 반사띠 (원기둥에 감는다)."""
    im = Image.new("RGBA", (w, h), (232, 188, 22, 255))
    d = ImageDraw.Draw(im)
    step = 120
    for x in range(-h, w + h, step):
        d.polygon([(x, h), (x + 60, h), (x + 60 + h, 0), (x + h, 0)], fill=(22, 22, 20, 255))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    return weather(im, 0.7, seed, fade=0.15, scratches=60, spots=40)


def transformer_label(w=420, h=300, seed=9):
    im = Image.new("RGBA", (w, h), (176, 180, 178, 255))
    d = ImageDraw.Draw(im)
    text(d, (w / 2, 120), "50", "han", 210, (24, 24, 24))
    d.rectangle([60, 228, w - 60, 290], fill=(220, 220, 214))
    text(d, (w / 2, 246), "주상변압기 50kVA", "b", 22, (20, 20, 20), maxw=w - 140)
    text(d, (w / 2, 274), "22.9kV / 220-380V  2009", "r", 18, (20, 20, 20), maxw=w - 140)
    return weather(im, 0.6, seed, fade=0.2, scratches=40, spots=50)


def sticker(w, h, bg, lines, seed, k="han"):
    im = Image.new("RGBA", (w, h), bg + (255,))
    d = ImageDraw.Draw(im)
    n = len(lines)
    for i, (s, col, size) in enumerate(lines):
        text(d, (w / 2, h * (i + 0.5) / n), s, k, size, col, maxw=w - 12)
    return weather(im, 0.4, seed, fade=0.35, scratches=10, spots=10)


def residue(w=300, h=200, seed=10):
    """찢어진 전단 자국 (흰 종이 조각 + 테이프)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rr = random.Random(seed)
    for _ in range(7):
        x, y = rr.uniform(0, w * 0.8), rr.uniform(0, h * 0.8)
        pts = [(x + rr.uniform(0, 60), y + rr.uniform(0, 40)) for _ in range(6)]
        d.polygon(pts, fill=(226, 222, 210, 255))
    for _ in range(3):
        x, y = rr.uniform(0, w * 0.7), rr.uniform(0, h * 0.8)
        d.rectangle([x, y, x + 70, y + 18], fill=(214, 204, 168, 200))
    return weather(im, 0.5, seed, scratches=0, spots=20)


def light_plate(w=260, h=360, seed=11):
    im = Image.new("RGBA", (w, h), (240, 240, 236, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 80], fill=(30, 76, 140))
    text(d, (w / 2, 42), "가로등", "han", 50, (255, 255, 255))
    text(d, (w / 2, 140), "시장로", "eb", 44, (20, 20, 20), maxw=w - 20)
    text(d, (w / 2, 205), "7-12", "han", 64, (20, 20, 20))
    d.line([(20, 255), (w - 20, 255)], fill=(30, 76, 140), width=3)
    text(d, (w / 2, 290), "고장신고", "b", 26, (30, 30, 30))
    text(d, (w / 2, 330), "☎ 120", "eb", 32, (30, 76, 140))
    return weather(im, 0.45, seed, fade=0.25, scratches=20, spots=20)


# ------------------------------------------------------------------ 표지판 면
def sign_crosswalk(s=512, seed=12):
    """지시표지 322 횡단보도: 파란 정사각형 + 흰 테두리 + 보행자/줄무늬."""
    im = Image.new("RGBA", (s, s), (235, 235, 235, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, s - 4, s - 4], 36, fill=(250, 250, 250))
    d.rounded_rectangle([22, 22, s - 22, s - 22], 26, fill=(16, 78, 160))
    # 횡단보도 줄무늬 (원근 사다리꼴)
    for i in range(6):
        x0 = 96 + i * 56
        d.polygon([(x0, 420), (x0 + 30, 420), (x0 + 22, 372), (x0 + 2, 372)], fill=(255, 255, 255))
    # 걷는 사람
    cx = 250
    d.ellipse([cx - 30, 70, cx + 30, 130], fill=(255, 255, 255))
    d.polygon([(cx - 28, 140), (cx + 26, 140), (cx + 34, 250), (cx - 20, 252)], fill=(255, 255, 255))
    d.line([(cx - 10, 248), (cx - 64, 350)], fill=(255, 255, 255), width=34)
    d.line([(cx + 20, 248), (cx + 70, 345)], fill=(255, 255, 255), width=34)
    d.line([(cx - 22, 160), (cx - 74, 236)], fill=(255, 255, 255), width=26)
    d.line([(cx + 24, 160), (cx + 78, 226)], fill=(255, 255, 255), width=26)
    for p in [(cx - 64, 350), (cx + 70, 345), (cx - 74, 236), (cx + 78, 226)]:
        d.ellipse([p[0] - 15, p[1] - 15, p[0] + 15, p[1] + 15], fill=(255, 255, 255))
    return weather(im, 0.35, seed, fade=0.12, scratches=40, spots=40)


def sign_market(w=512, h=220, seed=13):
    im = Image.new("RGBA", (w, h), (240, 240, 240, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([3, 3, w - 3, h - 3], 22, fill=(250, 250, 250))
    d.rounded_rectangle([14, 14, w - 14, h - 14], 16, fill=(30, 98, 150))
    text(d, (w * 0.42, h * 0.42), "시장 입구", "han", 92, (255, 255, 255), maxw=w * 0.66)
    text(d, (w * 0.42, h * 0.78), "Market Entrance", "b", 26, (220, 232, 240), maxw=w * 0.6)
    ax = w * 0.86
    d.polygon([(ax - 50, h * 0.42 - 22), (ax + 4, h * 0.42 - 22), (ax + 4, h * 0.42 - 50), (ax + 56, h * 0.42),
               (ax + 4, h * 0.42 + 50), (ax + 4, h * 0.42 + 22), (ax - 50, h * 0.42 + 22)], fill=(255, 255, 255))
    return weather(im, 0.35, seed, fade=0.15, scratches=30, spots=30)


def sign_back_sticker(w=200, h=120, seed=14):
    return sticker(w, h, (236, 236, 230), [("관리번호", (30, 30, 30), 26), ("B-112-07", (30, 30, 30), 34)], seed, "eb")


def noparking_face(s=512, seed=15):
    im = Image.new("RGBA", (s, s), (226, 224, 216, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([6, 6, s - 6, s - 6], outline=(150, 150, 146), width=6)
    cx, cy, r = s / 2, 200, 150
    text(d, (cx, cy + 6), "P", "han", 230, (28, 64, 128))
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(186, 36, 30), width=30)
    d.line([(cx - r * 0.7, cy - r * 0.7), (cx + r * 0.7, cy + r * 0.7)], fill=(186, 36, 30), width=30)
    text(d, (cx, 412), "주차금지", "han", 104, (186, 36, 30), maxw=s - 50)
    text(d, (cx, 478), "차량 출입구 · 24시간", "eb", 34, (40, 40, 40), maxw=s - 60)
    return weather(im, 0.55, seed, fade=0.35, scratches=60, spots=50)


def noparking_hand(w=360, h=220, seed=16):
    """손글씨 경고문 (코팅지)."""
    im = paper(w, h, (250, 250, 246), seed)
    d = ImageDraw.Draw(im)
    text(d, (w / 2, 70), "차 대지 마세요!!", "pen", 72, (200, 20, 20), maxw=w - 20)
    text(d, (w / 2, 150), "견인 조치 합니다", "pen", 58, (20, 20, 120), maxw=w - 20)
    return weather(im, 0.4, seed, fade=0.2, scratches=10, spots=10)


# ------------------------------------------------------------------ 의류수거함
def bin_main(w=820, h=500, seed=20):
    im = Image.new("RGBA", (w, h), (216, 210, 191, 255))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([10, 10, w - 10, h - 10], 18, outline=(47, 90, 67), width=10)
    text(d, (w / 2, h * 0.34), "의류 수거함", "han", 150, (47, 90, 67), maxw=w * 0.86)
    d.line([(70, h * 0.58), (w - 70, h * 0.58)], fill=(47, 90, 67), width=5)
    text(d, (w / 2, h * 0.74), "헌옷 · 신발 · 가방", "eb", 70, (60, 60, 56), maxw=w * 0.8)
    text(d, (w / 2, h * 0.89), "이불 · 커튼 · 담요", "b", 36, (90, 90, 84), maxw=w * 0.7)
    return weather(im, 0.5, seed, fade=0.3, scratches=50, spots=50)


def bin_hopper(w=520, h=170, seed=21):
    im = Image.new("RGBA", (w, h), (238, 214, 60, 255))
    d = ImageDraw.Draw(im)
    text(d, (w * 0.42, h / 2), "넣는 곳", "han", 96, (30, 30, 30), maxw=w * 0.6)
    ax, ay = w * 0.84, h / 2
    d.polygon([(ax - 30, ay - 50), (ax + 30, ay - 50), (ax + 30, ay), (ax + 55, ay), (ax, ay + 60),
               (ax - 55, ay), (ax - 30, ay)], fill=(30, 30, 30))
    return weather(im, 0.5, seed, fade=0.3, scratches=30, spots=20)


def bin_items(w=460, h=600, seed=22):
    im = Image.new("RGBA", (w, h), (244, 242, 234, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 90], fill=(47, 90, 67))
    text(d, (w / 2, 46), "수거 품목 안내", "han", 52, (255, 255, 255), maxw=w - 30)
    y = 130
    for s, c in [("○ 헌옷 · 속옷 · 양말", (30, 30, 30)), ("○ 신발 · 가방 · 모자", (30, 30, 30)),
                 ("○ 이불 · 커튼 · 담요", (30, 30, 30))]:
        text(d, (30, y), s, "b", 32, c, anchor="lm", maxw=w - 50)
        y += 56
    d.line([(20, y), (w - 20, y)], fill=(160, 160, 150), width=2)
    y += 44
    for s in ["× 솜이불 · 베개 · 방석", "× 카펫 · 인형 · 쓰레기"]:
        text(d, (30, y), s, "b", 32, (190, 34, 30), anchor="lm", maxw=w - 50)
        y += 56
    d.rectangle([0, h - 110, w, h], fill=(220, 216, 200))
    text(d, (w / 2, h - 76), "수거 문의", "eb", 30, (40, 40, 40))
    text(d, (w / 2, h - 34), "010-5553-1182", "han", 44, (47, 90, 67), maxw=w - 40)
    return weather(im, 0.5, seed, fade=0.3, scratches=40, spots=40)


def bin_warning(w=460, h=300, seed=23):
    im = Image.new("RGBA", (w, h), (250, 248, 240, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 84], fill=(200, 34, 30))
    text(d, (w / 2, 44), "쓰레기 무단투기 금지", "han", 48, (255, 255, 255), maxw=w - 26)
    text(d, (w / 2, 130), "적발 시 과태료 100만원 이하", "eb", 30, (30, 30, 30), maxw=w - 26)
    text(d, (w / 2, 178), "CCTV 촬영 중", "eb", 34, (200, 34, 30), maxw=w - 26)
    text(d, (w / 2, 246), "은행골구청 자원순환과", "b", 26, (60, 60, 60), maxw=w - 26)
    return weather(im, 0.5, seed, fade=0.35, scratches=40, spots=30)


def bin_permit(w=300, h=120, seed=24):
    return sticker(w, h, (230, 230, 226), [("은행골동 허가", (30, 30, 30), 30), ("제 2019-23호", (30, 30, 30), 34)],
                   seed, "eb")


def recycle_mark(s=200, seed=25):
    im = Image.new("RGBA", (s, s), (47, 90, 67, 255))
    d = ImageDraw.Draw(im)
    c = s / 2
    for k in range(3):
        a0 = k * 120 + 20
        d.arc([30, 30, s - 30, s - 30], a0, a0 + 80, fill=(240, 240, 230), width=18)
        a = math.radians(a0 + 80)
        x, y = c + math.cos(a) * (c - 39), c + math.sin(a) * (c - 39)
        t = a + math.pi / 2
        d.polygon([(x + math.cos(t) * 22, y + math.sin(t) * 22), (x + math.cos(a) * 20, y + math.sin(a) * 20),
                   (x - math.cos(a) * 20, y - math.sin(a) * 20)], fill=(240, 240, 230))
    return weather(im, 0.4, seed, fade=0.3, scratches=10, spots=10)


# ------------------------------------------------------------------ 가로휴지통
def can_label(w, h, bg, title, sub, seed, fg=(255, 255, 255)):
    im = Image.new("RGBA", (w, h), bg + (255,))
    d = ImageDraw.Draw(im)
    text(d, (w / 2, h * 0.38), title, "han", h * 0.42, fg, maxw=w - 30)
    text(d, (w / 2, h * 0.78), sub, "eb", h * 0.2, fg, maxw=w - 30)
    return weather(im, 0.45, seed, fade=0.3, scratches=30, spots=25)


def can_notice(w=420, h=260, seed=33):
    im = Image.new("RGBA", (w, h), (246, 244, 236, 255))
    d = ImageDraw.Draw(im)
    text(d, (w / 2, 50), "깨끗한 거리", "han", 54, (40, 110, 70), maxw=w - 20)
    text(d, (w / 2, 115), "음료는 비우고 버려주세요", "eb", 28, (30, 30, 30), maxw=w - 26)
    text(d, (w / 2, 160), "담배꽁초 투입 금지", "eb", 28, (196, 34, 30), maxw=w - 26)
    text(d, (w / 2, 220), "은행골구청", "b", 26, (60, 60, 60))
    return weather(im, 0.5, seed, fade=0.3, scratches=30, spots=30)


# ------------------------------------------------------------------ 보행신호등 (동적 면 기본 텍스처)
def _led_mask(mask, s, pitch, glow_col, off_col, on=True):
    """마스크를 LED 점 배열로 바꾼다."""
    m = np.asarray(mask.resize((s, s)), np.float32) / 255
    yy, xx = np.mgrid[0:s, 0:s]
    cx = (xx % pitch) - pitch / 2 + 0.5
    cy = (yy % pitch) - pitch / 2 + 0.5
    dot = np.clip(1 - np.sqrt(cx ** 2 + cy ** 2) / (pitch * 0.42), 0, 1) ** 0.6
    gx = (xx // pitch) * pitch + pitch // 2
    gy = (yy // pitch) * pitch + pitch // 2
    lit = m[np.clip(gy, 0, s - 1), np.clip(gx, 0, s - 1)]
    out = np.zeros((s, s, 3), np.float32)
    base = np.array(off_col, np.float32) / 255
    col = np.array(glow_col, np.float32) / 255
    out[:] = base * (0.35 + 0.65 * dot[..., None])
    if on:
        out = out * (1 - lit[..., None]) + col * (dot[..., None] * lit[..., None])
        glow = Image.fromarray((lit * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(pitch * 0.9))
        g = np.asarray(glow, np.float32)[..., None] / 255
        out += col * g * 0.35
    return out


def signal_lamp(kind, on=True, s=512):
    """빨간 서 있는 사람 / 초록 걷는 사람 램프 (원형 렌즈)."""
    mk = Image.new("L", (s, s), 0)
    d = ImageDraw.Draw(mk)
    c = s / 2
    if kind == "red":
        d.ellipse([c - 34, 90, c + 34, 158], fill=255)
        d.rounded_rectangle([c - 52, 168, c + 52, 300], 18, fill=255)
        d.rectangle([c - 44, 296, c - 10, 430], fill=255)
        d.rectangle([c + 10, 296, c + 44, 430], fill=255)
        d.rectangle([c - 72, 172, c - 50, 290], fill=255)
        d.rectangle([c + 50, 172, c + 72, 290], fill=255)
        glow, off = (255, 50, 30), (40, 18, 16)
    else:
        d.ellipse([c - 30, 86, c + 34, 150], fill=255)
        d.polygon([(c - 30, 162), (c + 34, 162), (c + 30, 300), (c - 26, 300)], fill=255)
        d.line([(c - 4, 296), (c - 74, 420)], fill=255, width=40)
        d.line([(c + 12, 296), (c + 82, 412)], fill=255, width=40)
        d.line([(c - 20, 176), (c - 84, 262)], fill=255, width=30)
        d.line([(c + 26, 176), (c + 86, 252)], fill=255, width=30)
        glow, off = (40, 255, 170), (14, 34, 28)
    px = _led_mask(mk, s, 12, glow, off, on)
    yy, xx = np.mgrid[0:s, 0:s]
    rr = np.sqrt((xx - c) ** 2 + (yy - c) ** 2) / c
    lens = np.clip((1 - rr) * 30, 0, 1)[..., None]
    out = px * lens + np.array([0.02, 0.02, 0.022]) * (1 - lens)
    # 렌즈 위 먼지/반사
    out += np.clip(0.06 - rr[..., None] * 0.05, 0, 1) * lens * 0.5
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


SEG = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc", "7": "abc",
       "8": "abcdefg", "9": "abcdfg"}


def countdown(num="15", on=True, w=384, h=512):
    mk = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mk)
    dw, dh, t = 140, 360, 30
    for k, ch in enumerate(num):
        x0, y0 = 36 + k * (dw + 32), 76
        segs = {"a": (x0 + t, y0, x0 + dw - t, y0 + t), "d": (x0 + t, y0 + dh - t, x0 + dw - t, y0 + dh),
                "g": (x0 + t, y0 + dh / 2 - t / 2, x0 + dw - t, y0 + dh / 2 + t / 2),
                "f": (x0, y0 + t, x0 + t, y0 + dh / 2 - t / 2), "b": (x0 + dw - t, y0 + t, x0 + dw, y0 + dh / 2 - t / 2),
                "e": (x0, y0 + dh / 2 + t / 2, x0 + t, y0 + dh - t),
                "c": (x0 + dw - t, y0 + dh / 2 + t / 2, x0 + dw, y0 + dh - t)}
        for sname in SEG[ch]:
            d.rectangle(segs[sname], fill=255)
    s = max(w, h)
    big = Image.new("L", (s, s), 0)
    big.paste(mk, ((s - w) // 2, (s - h) // 2))
    px = _led_mask(big, s, 10, (60, 255, 150), (16, 26, 22), on)
    im = Image.fromarray((np.clip(px, 0, 1) * 255).astype(np.uint8))
    return im.crop(((s - w) // 2, (s - h) // 2, (s - w) // 2 + w, (s - h) // 2 + h))


def pushbutton_face(w=320, h=520, seed=40):
    im = Image.new("RGBA", (w, h), (236, 190, 24, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w, 96], fill=(30, 30, 30))
    text(d, (w / 2, 34), "음향신호기", "han", 44, (255, 220, 40), maxw=w - 20)
    text(d, (w / 2, 76), "시각장애인용", "b", 24, (230, 230, 230))
    text(d, (w / 2, 132), "버튼을 누르세요", "eb", 32, (30, 30, 30), maxw=w - 20)
    # 버튼 자리 (모델의 버튼이 들어갈 원)
    d.ellipse([w / 2 - 70, 200, w / 2 + 70, 340], fill=(40, 40, 40))
    d.ellipse([w / 2 - 58, 212, w / 2 + 58, 328], fill=(70, 70, 70))
    # 점자
    for i in range(8):
        for j in range(3):
            if (i * 3 + j) % 4 != 1:
                x, y = 54 + i * 28 + (j % 2) * 8, 372 + j * 10
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(60, 50, 10))
    # 스피커 구멍
    for i in range(6):
        for j in range(3):
            x, y = w / 2 - 75 + i * 30, 424 + j * 26
            d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(28, 28, 28))
    return weather(im, 0.55, seed, fade=0.3, scratches=40, spots=40)


# ------------------------------------------------------------------ 도로 도색 타일 (아스팔트 위에 칠한 도료)
def tnoise(n, cells, seed):
    """이음매 없는(타일링) 값 노이즈 0..1."""
    g = np.tile(np.random.default_rng(seed).random((cells, cells)), (3, 3))
    im = Image.fromarray((g * 255).astype(np.uint8)).resize((3 * n, 3 * n), Image.BICUBIC)
    return np.asarray(im, np.float32)[n:2 * n, n:2 * n] / 255


def asphalt_base(src, n=2048):
    """기본 노면: clean_asphalt 는 너무 고르다 -> 골재 대비를 키우고 조금 밝히고, 타일 안에서 아주 약한 얼룩."""
    a = np.asarray(Image.open(os.path.join(src, "clean_asphalt_diff_2k.jpg")).convert("RGB").resize((n, n),
                   Image.LANCZOS), np.float32) / 255
    lo = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
    a = lo + (a - lo) * 2.6                                               # 골재 알갱이
    m = 1 + 0.07 * (tnoise(n, 4, 81) - 0.5) + 0.05 * (tnoise(n, 11, 82) - 0.5)
    warm = (tnoise(n, 5, 83) - 0.5)[..., None] * np.array([0.03, 0.01, -0.02])
    a = a * 1.14 * m[..., None] + warm
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "asphalt_base_diff.jpg"),
                                                                    quality=92)


def road_oil(w=1024, h=160, seed=91):
    """차로 가운데 기름 얼룩 띠 (6 m x 0.9 m, U 방향 이음매 없음). RGBA, 알파 = 얼룩 세기."""
    rng = random.Random(seed)
    v = np.linspace(-1, 1, h)[:, None]
    prof = np.exp(-(v / 0.45) ** 2)                                       # 가운데 진하고 가장자리 흐림
    along = np.tile(tnoise(w, 9, seed)[:1], (h, 1))                    # U 방향 이음매 없는 노이즈만 쓴다
    al = prof * (0.10 + 0.22 * along) * (0.7 + 0.6 * tnoise(w, 26, seed + 1)[:h])
    spot = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(spot)
    for _ in range(700):                                                  # 떨어진 기름 방울 (1~6 cm)
        x = rng.random() * w
        y = h / 2 + rng.gauss(0, h * 0.15)
        r = rng.uniform(0.8, 3.2) * (1 + 2.0 * rng.random() ** 8)
        for xx in (x - w, x, x + w):                                      # 가장자리 넘어가면 반대편에도
            d.ellipse([xx - r * 1.4, y - r, xx + r * 1.4, y + r], fill=int(rng.uniform(40, 130)))
    spot = np.asarray(spot.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    al = np.clip(al + spot * 0.55, 0, 0.75)
    col = np.array([0.075, 0.068, 0.06]) * (0.8 + 0.4 * tnoise(w, 34, seed + 2)[:h])[..., None]
    rgba = np.dstack([np.clip(col, 0, 1), al])
    Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "road_oil.png"))


def road_paint():
    """기본 노면(clean_asphalt)의 골재 굴곡을 따라 도료가 닳은 흰 도료 타일 (노랑은 _tex_ground.paint_yellow)."""
    src = os.path.join(CACHE, "polyhaven", "clean_asphalt")
    asphalt_base(src)
    diff = np.asarray(Image.open(os.path.join(OUT, "asphalt_base_diff.jpg")).convert("RGB").resize((1024, 1024),
                                                                                                Image.LANCZOS),
                      np.float32) / 255
    nor = Image.open(os.path.join(src, "clean_asphalt_nor_gl_2k.jpg")).convert("RGB").resize((1024, 1024),
                                                                                           Image.LANCZOS)
    rough = np.asarray(Image.open(os.path.join(src, "clean_asphalt_rough_2k.jpg")).convert("L").resize((1024, 1024),
                                                                                                    Image.LANCZOS),
                       np.float32) / 255
    lum = diff.mean(-1)
    lum_n = (lum - lum.mean()) / (lum.std() + 1e-6)
    big = noise(1024, 1024, 220, 51, 5)  # 큰 마모 얼룩 (타이어 자국)
    mid = noise(1024, 1024, 40, 52, 4)
    # 패인 곳(어두운 골재 틈) + 큰 얼룩에서 도료가 벗겨진다
    wear = np.clip((-lum_n - 0.9) * 0.6, 0, 1) + np.clip((big - 0.62) * 4.0, 0, 1) * np.clip((mid - 0.35) * 3, 0, 1)
    wear = np.clip(wear, 0, 1)[..., None]
    paint = np.array([0.86, 0.85, 0.80]) * (0.88 + 0.12 * mid[..., None]) * (0.92 + 0.08 * np.clip(lum_n, -2, 2)[..., None] / 2)
    grime = np.clip(noise(1024, 1024, 120, 53, 4) - 0.45, 0, 1)[..., None] * 0.35
    paint = paint * (1 - grime) + np.array([0.42, 0.40, 0.37]) * grime
    col = paint * (1 - wear) + diff * 1.05 * wear
    Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "roadpaint_diff.png"))
    # 노멀은 아스팔트 그대로(도료가 표면을 따라감), 조금 약하게
    na = np.asarray(nor, np.float32) / 255 * 2 - 1
    na[..., :2] *= 0.7
    na /= np.linalg.norm(na, axis=-1, keepdims=True)
    Image.fromarray(((na * 0.5 + 0.5) * 255).astype(np.uint8)).save(os.path.join(OUT, "roadpaint_nor.png"))
    rg = 0.55 * (1 - wear[..., 0]) + rough * wear[..., 0]
    Image.fromarray((np.clip(rg, 0, 1) * 255).astype(np.uint8)).save(os.path.join(OUT, "roadpaint_rough.png"))
    print("tex roadpaint")


def main():
    # 전신주 데칼 아틀라스
    a = Atlas("T_StreetUtilityPole_Decals", 2048)
    a.add("flyer_room", flyer_room())
    a.add("flyer_move", flyer_move())
    a.add("flyer_dog", flyer_dog())
    a.add("flyer_academy", flyer_academy())
    a.add("hazard", hazard_band())
    a.add("notice", notice_no_ads())
    a.add("plate", pole_plate())
    a.add("hv", hv_warning())
    a.add("trans", transformer_label())
    a.add("st_loan", sticker(300, 140, (250, 230, 40), [("대출 상담", (20, 20, 20), 52), ("010-5551-7733", (200, 20, 20), 34)], 30))
    a.add("st_key", sticker(240, 140, (210, 40, 34), [("열쇠", (255, 255, 255), 64), ("24시 출장", (255, 240, 200), 30)], 31))
    a.add("residue", residue())
    a.save(alpha=True)

    a = Atlas("T_StreetLight_Decals", 1024)
    a.add("plate", light_plate())
    a.add("st_loan", sticker(300, 140, (250, 230, 40), [("대출 상담", (20, 20, 20), 52), ("010-5551-7733", (200, 20, 20), 34)], 34))
    a.add("st_key", sticker(240, 140, (210, 40, 34), [("열쇠", (255, 255, 255), 64), ("24시 출장", (255, 240, 200), 30)], 35))
    a.add("st_piano", sticker(260, 120, (240, 240, 236), [("피아노 조율", (30, 60, 120), 44), ("02) 555-0122", (30, 30, 30), 28)], 36, "eb"))
    a.add("residue", residue(300, 200, 37))
    a.save(alpha=True)

    a = Atlas("T_StreetSignPole_Faces", 1024)
    a.add("crosswalk", sign_crosswalk())
    a.add("market", sign_market())
    a.add("back", sign_back_sticker())
    a.add("st_loan", sticker(220, 110, (250, 230, 40), [("대출 상담", (20, 20, 20), 40), ("010-5551-7733", (200, 20, 20), 26)], 38))
    a.save()

    a = Atlas("T_StreetNoParking_Face", 1024)
    a.add("face", noparking_face())
    a.add("hand", noparking_hand())
    a.save()

    a = Atlas("T_StreetClothingBin_Decals", 2048)
    a.add("main", bin_main())
    a.add("hopper", bin_hopper())
    a.add("items", bin_items())
    a.add("warning", bin_warning())
    a.add("permit", bin_permit())
    a.add("recycle", recycle_mark())
    a.add("st_loan", sticker(300, 140, (250, 230, 40), [("대출 상담", (20, 20, 20), 52), ("010-5551-7733", (200, 20, 20), 34)], 26))
    a.save()

    a = Atlas("T_StreetTrashCan_Decals", 1024)
    a.add("general", can_label(380, 150, (70, 74, 78), "일반쓰레기", "종이 · 휴지 · 비닐", 31))
    a.add("recycle", can_label(380, 150, (30, 96, 160), "재활용", "캔 · 병 · 페트병", 32))
    a.add("notice", can_notice())
    a.add("st_key", sticker(200, 110, (210, 40, 34), [("열쇠", (255, 255, 255), 50), ("24시 출장", (255, 240, 200), 24)], 39))
    a.save()

    a = Atlas("T_StreetCrosswalkSignal_Box", 1024)
    a.add("face", pushbutton_face())
    a.add("plate", sticker(260, 110, (236, 236, 230), [("신호등 관리번호", (30, 30, 30), 26), ("시장-112-3", (30, 30, 30), 34)], 41, "eb"))
    a.save()
    # 동적 면 기본 텍스처 (켜짐/꺼짐)
    signal_lamp("red", True).save(os.path.join(OUT, "T_StreetCrosswalkSignal_RedOn.png"))
    signal_lamp("red", False).save(os.path.join(OUT, "T_StreetCrosswalkSignal_RedOff.png"))
    signal_lamp("green", True).save(os.path.join(OUT, "T_StreetCrosswalkSignal_GreenOn.png"))
    signal_lamp("green", False).save(os.path.join(OUT, "T_StreetCrosswalkSignal_GreenOff.png"))
    countdown("15", True).save(os.path.join(OUT, "T_StreetCrosswalkSignal_Count.png"))
    countdown("88", False).save(os.path.join(OUT, "T_StreetCrosswalkSignal_CountOff.png"))

    road_paint()
    road_oil()
    open(os.path.join(OUT, ".done"), "w").write("ok")


if __name__ == "__main__":
    main()
