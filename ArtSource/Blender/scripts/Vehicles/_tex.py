"""차량 그룹 2D 텍스처 (Pillow). Blender 스크립트가 venv 파이썬으로 실행한다.
사용: python _tex.py <출력폴더>
번호판·타이어 옆면 글자·유리 먼지·스티커·배달통 인쇄·자전거 데칼을 만든다 (번호는 모두 가상)."""
import sys, os, math, random
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)
HOME = os.path.expanduser("~")
F_EB = HOME + "/Library/Fonts/NanumSquareEB.ttf"
F_B = HOME + "/Library/Fonts/NanumSquareB.ttf"
F_R = HOME + "/Library/Fonts/NanumSquareR.ttf"
F_HAN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "_cache", "fonts", "BlackHanSans-Regular.ttf")
if not os.path.exists(F_HAN):
    F_HAN = F_EB


def font(path, size):
    return ImageFont.truetype(path, size)


def text_img(text, path, size, fill, squeeze=1.0):
    """글자 한 줄을 투명 이미지로 (가로 압축 squeeze)."""
    f = font(path, size)
    l, t, r, b = f.getbbox(text)
    im = Image.new("RGBA", (r - l + 8, b - t + 8), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - l, 4 - t), text, font=f, fill=fill)
    if squeeze != 1.0:
        im = im.resize((max(1, int(im.width * squeeze)), im.height), Image.LANCZOS)
    return im


def paste_center(dst, im, cx, cy):
    dst.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2)))


def grime(im, amount=0.08, seed=1):
    """얼룩·먼지 (가장자리 쪽이 더 더럽다)."""
    rnd = np.random.default_rng(seed)
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    n = rnd.random((h // 8 + 1, w // 8 + 1)).astype(np.float32)
    n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)).astype(np.float32) / 255
    yy, xx = np.mgrid[0:h, 0:w]
    edge = np.minimum(np.minimum(xx, w - 1 - xx) / w, np.minimum(yy, h - 1 - yy) / h)
    e = np.clip(1 - edge * 12, 0, 1)
    d = (amount * (0.6 * n + 0.8 * e))[..., None]
    dirt = np.array([92, 84, 70], np.float32)
    a[..., :3] = a[..., :3] * (1 - d) + dirt * d
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------ 번호판
def plate_car(path, num_a, letter, num_b, band=True, w=1024, h=216):
    """자동차 번호판 520x110mm. band=True: 2020년식 태극 홀로그램 띠."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, h - 3), radius=18, fill=(244, 244, 238, 255), outline=(40, 40, 40, 255), width=5)
    x0 = 14
    if band:
        bw = 74
        d.rounded_rectangle((10, 10, 10 + bw, h - 11), radius=10, fill=(28, 62, 140, 255))
        cx, cy, r = 10 + bw / 2, h * 0.40, 22
        d.pieslice((cx - r, cy - r, cx + r, cy + r), 180, 360, fill=(200, 36, 48, 255))
        d.pieslice((cx - r, cy - r, cx + r, cy + r), 0, 180, fill=(30, 80, 170, 255))
        d.ellipse((cx - r, cy - r / 2, cx, cy + r / 2), fill=(200, 36, 48, 255))
        d.ellipse((cx, cy - r / 2, cx + r, cy + r / 2), fill=(30, 80, 170, 255))
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(240, 240, 240, 255), width=2)
        paste_center(im, text_img("KOR", F_EB, 26, (240, 240, 240, 255)), cx, h * 0.78)
        x0 = 10 + bw + 8
    txt = text_img(f"{num_a}{letter} {num_b}", F_EB, 210, (22, 22, 24, 255), squeeze=0.72)
    s = min((w - x0 - 30) / txt.width, (h - 34) / txt.height)
    txt = txt.resize((int(txt.width * s), int(txt.height * s)), Image.LANCZOS)
    paste_center(im, txt, (x0 + w - 12) / 2, h / 2 + 2)
    for bx in (0.30, 0.70):
        cx = x0 + (w - x0) * bx
        d.ellipse((cx - 9, 16, cx + 9, 34), fill=(170, 170, 165, 255), outline=(90, 90, 90, 255), width=2)
    grime(im, 0.10, seed=len(num_b)).save(path)


def plate_moto(path, w=512, h=280):
    """이륜차 번호판 (2줄)."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((2, 2, w - 3, h - 3), radius=16, fill=(244, 244, 238, 255), outline=(40, 40, 40, 255), width=5)
    top = text_img("서울 중구", F_EB, 74, (22, 22, 24, 255), squeeze=0.85)
    paste_center(im, top, w / 2, h * 0.24)
    bot = text_img("바 5821", F_EB, 150, (22, 22, 24, 255), squeeze=0.78)
    s = min((w - 40) / bot.width, 1.0)
    bot = bot.resize((int(bot.width * s), int(bot.height * s)), Image.LANCZOS)
    paste_center(im, bot, w / 2, h * 0.66)
    grime(im, 0.16, seed=7).save(path)


# ------------------------------------------------------------------ 타이어 옆면 글자 (흰=볼록 글자)
def tire_ring(path, size_txt, r_rim, r_tire, n=1024):
    im = Image.new("L", (n, n), 0)
    c = n / 2
    k = c / r_tire  # m -> px
    r_mid = (r_rim + 0.58 * (r_tire - r_rim)) * k
    lines = [(size_txt, 0.0, 34), ("TUBELESS  RADIAL", 180.0, 22), ("MADE IN KOREA", 95.0, 16), ("M+S", 270.0, 20)]
    for txt, ang0, pt in lines:
        f = font(F_EB, int(pt * n / 1024 * (r_tire - r_rim) / 0.11))
        widths = [f.getlength(ch) for ch in txt]
        total = sum(widths)
        a = math.radians(ang0) - total / r_mid / 2
        for ch, wch in zip(txt, widths):
            a_c = a + wch / r_mid / 2
            g = Image.new("L", (int(wch) + 8, pt * 3), 0)
            ImageDraw.Draw(g).text((4, 0), ch, font=f, fill=255)
            g = g.rotate(-math.degrees(a_c), resample=Image.BICUBIC, expand=True)
            x = c + r_mid * math.sin(a_c)
            y = c - r_mid * math.cos(a_c)
            im.paste(255, (int(x - g.width / 2), int(y - g.height / 2)), g)
            a += wch / r_mid
    # 테두리 링 2줄 (림 쪽 / 트레드 쪽)
    d = ImageDraw.Draw(im)
    for rr in (r_rim + 0.18 * (r_tire - r_rim), r_rim + 0.86 * (r_tire - r_rim)):
        R = rr * k
        d.ellipse((c - R, c - R, c + R, c + R), outline=150, width=3)
    im.filter(ImageFilter.GaussianBlur(0.8)).save(path)


# ------------------------------------------------------------------ 유리 (RGB 틴트 + A 불투명도, 먼지/물자국)
def glass(path, tint, alpha, n=1024, seed=3):
    rnd = np.random.default_rng(seed)
    a = np.zeros((n, n, 4), np.float32)
    a[..., :3] = tint
    a[..., 3] = alpha
    im = Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8), "RGBA")
    dust = Image.new("RGBA", (n, n), (0, 0, 0, 0))  # 별도 층에 그려 합성 (직접 그리면 유리 알파를 덮어써 구멍이 난다)
    d = ImageDraw.Draw(dust)
    for _ in range(120):  # 먼지 점 (어두운 썬팅 위에서 튀지 않게 옅게)
        x, y = rnd.random(2) * n
        r = rnd.random() * 2.0 + 0.4
        v = int(90 + rnd.random() * 30)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(v, v - 4, v - 10, int(6 + rnd.random() * 8)))
    for _ in range(4):  # 흘러내린 자국
        x = rnd.random() * n
        y0 = rnd.random() * n
        L = rnd.random() * 220 + 60
        d.line((x, y0, x + rnd.normal() * 6, y0 + L), fill=(120, 116, 106, 12), width=int(3 + rnd.random() * 5))
    im = Image.alpha_composite(im, dust.filter(ImageFilter.GaussianBlur(0.6)))
    # 이음매 없는 타일: 반 이동 후 평균
    arr = np.asarray(im).astype(np.float32)
    rolled = np.roll(np.roll(arr, n // 2, 0), n // 2, 1)
    yy, xx = np.mgrid[0:n, 0:n] / n
    m = (np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy)) * 6).clip(0, 1)[..., None]
    arr = arr * m + rolled * (1 - m)
    Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA").save(path)


# ------------------------------------------------------------------ 스티커
def sticker_beginner(path, w=600, h=300):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((4, 4, w - 5, h - 5), radius=30, fill=(250, 214, 20, 255), outline=(30, 30, 30, 255), width=8)
    t = text_img("초보운전", F_HAN, 150, (20, 20, 20, 255))
    paste_center(im, t, w / 2, h * 0.42)
    t = text_img("양해 부탁드립니다", F_EB, 40, (40, 40, 40, 255))
    paste_center(im, t, w / 2, h * 0.80)
    # 햇빛에 바랜 색 + 모서리 들뜸
    arr = np.asarray(im).astype(np.float32)
    arr[..., :3] = arr[..., :3] * 0.86 + 255 * 0.10
    im = Image.fromarray(arr.clip(0, 255).astype(np.uint8), "RGBA")
    grime(im, 0.12, seed=5).save(path)


def sticker_parking(path, w=400, h=300):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((3, 3, w - 4, h - 4), radius=20, fill=(246, 246, 240, 255), outline=(40, 120, 70, 255), width=10)
    d.rectangle((14, 14, w - 15, 90), fill=(40, 120, 70, 255))
    paste_center(im, text_img("은행골아파트", F_EB, 46, (255, 255, 255, 255)), w / 2, 52)
    paste_center(im, text_img("입주민 차량", F_EB, 44, (30, 30, 30, 255)), w / 2, 140)
    paste_center(im, text_img("103동 - 0417", F_HAN, 56, (200, 40, 40, 255)), w / 2, 220)
    grime(im, 0.10, seed=9).save(path)


# ------------------------------------------------------------------ 배달통 (버거대왕 패러디, 실제 상표 아님)
def burger_logo(d, cx, cy, s, text=True):
    """프로토타입 Rn() 로고: 빵·패티·왕관 + '버거대왕'."""
    def P(x, y):
        return (cx + x * s, cy + y * s)
    d.pieslice([*P(-62, -52), *P(62, 36)], 180, 360, fill=(217, 138, 43, 255))
    d.rectangle([*P(-60, -6), *P(60, 10)], fill=(107, 58, 30, 255))
    d.rounded_rectangle([*P(-58, 12), *P(58, 34)], radius=8 * s, fill=(217, 138, 43, 255))
    d.polygon([P(-30, -48), P(-34, -82), P(-14, -62), P(0, -90), P(14, -62), P(34, -82), P(30, -48)], fill=(240, 198, 58, 255))


def box_print(path, back=False, w=1024, h=1024):
    im = Image.new("RGBA", (w, h), (181, 39, 28, 255))
    d = ImageDraw.Draw(im)
    d.rectangle((0, h * 0.86, w, h), fill=(241, 228, 200, 255))  # 아래 크림 띠
    for x in range(0, w, 60):  # 반사 테이프 사선
        d.polygon([(x, h * 0.88), (x + 30, h * 0.88), (x + 10, h * 0.98), (x - 20, h * 0.98)], fill=(200, 200, 196, 255))
    if not back:
        burger_logo(d, w / 2, h * 0.30, 3.2)
        paste_center(im, text_img("버거대왕", F_HAN, 190, (241, 228, 200, 255)), w / 2, h * 0.58)
        paste_center(im, text_img("DELIVERY  딜리버리", F_EB, 58, (240, 198, 58, 255)), w / 2, h * 0.72)
    else:
        # 위 0.34h 는 뚜껑 이음선·걸쇠·자물쇠가 덮는다 -> 글자는 그 아래, 0.58h 아래 줄은 반사판(가장자리) 안쪽 폭
        paste_center(im, text_img("배달앱", F_HAN, 190, (241, 228, 200, 255)), w / 2, h * 0.445)
        paste_center(im, text_img("주문 전용", F_HAN, 136, (241, 228, 200, 255)), w / 2, h * 0.625)
        paste_center(im, text_img("전화 주문 받지 않습니다", F_EB, 50, (240, 198, 58, 255)), w / 2, h * 0.775)
    # 긁힘
    rnd = np.random.default_rng(11 if back else 12)
    d = ImageDraw.Draw(im, "RGBA")
    for _ in range(70):
        x, y = rnd.random(2) * [w, h]
        L = rnd.random() * 90 + 10
        a = rnd.random() * math.pi
        d.line((x, y, x + math.cos(a) * L, y + math.sin(a) * L * 0.3), fill=(235, 225, 215, int(40 + rnd.random() * 80)), width=1 + int(rnd.random() * 2))
    grime(im, 0.22, seed=13).save(path)


def bike_decal(path, w=1024, h=128):
    """체인 케이스 데칼 (투명 바탕 + 크림색 글자, 8:1). '새싹' 을 영문보다 크게. 굽지 않는 쿼드에 알파 클립으로 붙는다."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    col = (238, 230, 205, 255)
    a, b = text_img("새싹", F_HAN, 120, col), text_img("CITY 26", F_HAN, 92, col)
    gap = 44
    s = min((w - 24) / (a.width + gap + b.width), (h - 6) / a.height, 1.0)
    a = a.resize((int(a.width * s), int(a.height * s)), Image.LANCZOS)
    b = b.resize((int(b.width * s), int(b.height * s)), Image.LANCZOS)
    x0 = (w - a.width - gap * s - b.width) / 2
    paste_center(im, a, x0 + a.width / 2, h / 2)
    paste_center(im, b, x0 + a.width + gap * s + b.width / 2, h / 2 + (a.height - b.height) * 0.18)
    grime(im, 0.10, seed=21).save(path)


plate_car(os.path.join(OUT, "plate_sedan.png"), "123", "가", "4568", band=True)
plate_car(os.path.join(OUT, "plate_hatch.png"), "45", "나", "7019", band=False)
plate_moto(os.path.join(OUT, "plate_moto.png"))
tire_ring(os.path.join(OUT, "tire_sedan.png"), "205/55R16  91V", 0.203, 0.316)
tire_ring(os.path.join(OUT, "tire_hatch.png"), "165/60R14  75H", 0.178, 0.277)
tire_ring(os.path.join(OUT, "tire_moto.png"), "90/90-10  50J", 0.127, 0.215)
glass(os.path.join(OUT, "glass_front.png"), (0.10, 0.12, 0.13), 0.30, seed=3)
glass(os.path.join(OUT, "glass_tint.png"), (0.02, 0.025, 0.03), 0.84, seed=4)
sticker_beginner(os.path.join(OUT, "sticker_beginner.png"))
sticker_parking(os.path.join(OUT, "sticker_parking.png"))
box_print(os.path.join(OUT, "box_side.png"))
box_print(os.path.join(OUT, "box_back.png"), back=True)
bike_decal(os.path.join(OUT, "bike_decal.png"))
print("TEX_OK", OUT)
