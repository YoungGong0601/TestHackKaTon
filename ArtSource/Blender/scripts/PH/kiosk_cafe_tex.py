"""PH_KioskCafe 텍스처 (Pillow). 실행: <k3d.PY> kiosk_cafe_tex.py <저장소>. PH/kiosk_cafe.py 가 부른다.
결과는 Textures/PH_KioskCafe 에만 쓰고 공유 텍스처는 읽기만 한다. 종이 아틀라스는 T_Kiosk_Paper_BaseColor 와 칸이 같아
메시 UV 를 고치지 않는다. 메뉴 이름 맞추기 퍼즐이 있어 포스터에 음료 이름을 쓰지 않는다."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO = sys.argv[1]
TEX = os.path.join(REPO, "Assets", "Art3D", "Textures")
OUT = os.path.join(TEX, "PH_KioskCafe")
FONT = os.path.join(REPO, "ArtSource", "_cache", "fonts", "Pretendard-{}.otf")
LOGO = os.path.join(REPO, "Assets", "UI", "Kiosk", "Art", "logo_cafe.png")
COFFEE = os.path.join(REPO, "ArtSource", "_ref", "img", "coffee.png")
GREEN, DARK, CREAM, GOLD, BROWN = (31, 91, 69), (20, 61, 47), (246, 238, 220), (224, 184, 108), (74, 48, 34)
# Controls 아틀라스(1024)에 구워진 실제 상표 글자: NFC 패드 앞뒤 삼성페이 등, 단말기 앞뒤 K-PAY
BRAND_TEXT = ((758, 661, 818, 673), (758, 744, 818, 755), (100, 998, 128, 1009), (164, 897, 177, 925))


def text(d, xy, s, weight, size, fill, anchor="mm"):
    d.text(xy, s, font=ImageFont.truetype(FONT.format(weight), size), fill=fill, anchor=anchor)


def gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    a = np.array(top, float) * (1 - t) + np.array(bottom, float) * t
    return Image.fromarray(np.ascontiguousarray(np.broadcast_to(a, (h, w, 3))).astype(np.uint8))


def badge(size):
    """logo_cafe.png 는 흰 원판 위 초록 원두다. 원판을 크림으로 바꾼다."""
    a = np.asarray(Image.open(LOGO).convert("RGBA"), float).copy()
    t = ((255 - a[..., :1]) / (255 - GREEN[0])).clip(0, 1)
    a[..., :3] = t * np.array(GREEN) + (1 - t) * np.array(CREAM)
    return Image.fromarray(a.astype(np.uint8)).resize((size, size), Image.LANCZOS)


def coffee(im, x, y, size, shadow):
    """사진은 정사각형이고 받침 접시 아래가 세로 0.81 쯤이다."""
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).ellipse([x + size * .1, y + size * .72, x + size * .9, y + size * .86], fill=150)
    im.paste(shadow, (0, 0), sh.filter(ImageFilter.GaussianBlur(size / 40)))
    p = Image.open(COFFEE).convert("RGBA").resize((size, size), Image.LANCZOS)
    im.paste(p, (x, y), p)


def header():
    w, h = 2048, 289
    im = gradient(w, h, (40, 112, 86), DARK)
    d = ImageDraw.Draw(im)
    b = badge(215)
    im.paste(b, (50, 37), b)
    text(d, (310, 150), "숲길 커피", "ExtraBold", 168, CREAM, "lm")
    text(d, (1975, 150), "셀프 주문  SELF ORDER", "SemiBold", 78, CREAM, "rm")
    return im


def poster_left():
    w, h = 640, 1434
    im = gradient(w, h, DARK, GREEN)
    d = ImageDraw.Draw(im)
    b = badge(150)
    im.paste(b, (w // 2 - 75, 55), b)
    text(d, (320, 255), "숲길 커피", "Bold", 48, CREAM)
    text(d, (320, 385), "오늘의", "Black", 118, CREAM)
    text(d, (320, 540), "원두", "Black", 178, GOLD)
    coffee(im, 15, 570, 610, DARK)
    d.rectangle((0, 1110, w, 1262), fill=CREAM)
    text(d, (320, 1186), "갓 볶은 한 잔", "Black", 80, DARK)
    text(d, (320, 1322), "매일 아침 직접 볶습니다", "SemiBold", 40, CREAM)
    text(d, (320, 1385), "본 이미지는 연출된 것으로 실제와 다를 수 있습니다.", "Regular", 21, GOLD)
    return im


def poster_right():
    w, h = 512, 768
    im = Image.new("RGB", (w, h), CREAM)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 232), fill=GREEN)
    text(d, (256, 92), "오늘의 원두", "Black", 76, CREAM)
    text(d, (256, 176), "향이 깊은 한 잔", "Bold", 40, GOLD)
    coffee(im, 41, 205, 430, (214, 200, 174))
    text(d, (256, 640), "숲길 커피", "Black", 62, GREEN)
    text(d, (256, 708), "매장에서 바로 내립니다", "Medium", 28, BROWN)
    return im


def pop():
    """별 모양 흔들이. 안쪽 반지름이 0.84 라 글자를 가운데 80% 안에 둔다."""
    im = Image.new("RGB", (333, 333), GREEN)
    d = ImageDraw.Draw(im)
    d.ellipse((151, 42, 182, 73), fill=GOLD)
    text(d, (166, 150), "NEW", "Black", 96, CREAM)
    text(d, (166, 226), "오늘의 원두", "Bold", 40, GOLD)
    return im


def atlas():
    im = Image.new("RGB", (2048, 2048), CREAM)  # 뒷면 칸(1623, 0)은 크림 그대로
    for art, xy in ((poster_left(), (0, 0)), (poster_right(), (652, 0)), (pop(), (1623, 114))):
        im.paste(art, xy)
    a = np.asarray(im, float) + np.random.default_rng(7).normal(0, 2.5, (2048, 2048, 1))  # 종이결
    return Image.fromarray(a.clip(0, 255).astype(np.uint8))


def red_mask(im, vmin=20):
    h, s, v = (np.asarray(c, float) for c in im.convert("HSV").split())
    return (np.minimum(h, 255 - h) < 18) & (s > 60) & (v > vmin), h, s, v


def controls(name, erase=()):
    """Controls 아틀라스 사본: 호출 버튼, 스캐너 창, 슬롯, 취소 키의 빨강을 브랜드 초록 쪽으로 돌린다."""
    im = Image.open(os.path.join(TEX, "Kiosk_Controls", f"T_Kiosk_Controls_{name}.jpg")).convert("RGB")
    d = ImageDraw.Draw(im)
    for b in erase:
        d.rectangle(b, fill=im.getpixel(((b[0] + b[2]) // 2, b[3] + 2)))  # 바로 아래 바탕색
    red, h, s, v = red_mask(im)
    hsv = np.dstack((np.where(red, 112, h), np.where(red, s * .75, s), np.where(red, v * .85, v)))
    return Image.fromarray(hsv.astype(np.uint8), "HSV").convert("RGB")


os.makedirs(OUT, exist_ok=True)
header().save(os.path.join(OUT, "T_PH_KioskCafe_Header.png"), optimize=True)
atlas().save(os.path.join(OUT, "T_PH_KioskCafe_Paper_BaseColor.jpg"), quality=93, subsampling=0)
for n, erase in (("BaseColor", BRAND_TEXT), ("Emission", ())):
    p = os.path.join(OUT, f"T_PH_KioskCafe_Controls_{n}.jpg")
    controls(n, erase).save(p, quality=93, subsampling=0)
    left = int(red_mask(Image.open(p).convert("RGB"), 40)[0].sum())  # 밝기 27 아래 섬 가장자리 JPEG 번짐은 안 보인다
    print(f"kiosk_cafe_tex: {n} 보이는 빨강 {left}")
    assert left == 0, p
