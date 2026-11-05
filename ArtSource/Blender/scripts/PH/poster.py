"""PH_Poster 의 글자 없는 인쇄면. 글자는 Readable 이 그린다.
_cache/venv/bin/python poster.py -> Assets/Art3D/Textures/PH_Poster/*.png"""
import os
import numpy as np
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "..", "Assets", "Art3D", "Textures", "PH_Poster")
os.makedirs(OUT, exist_ok=True)
RED, CREAM, GOLD, INK = (178, 38, 30), (247, 241, 228), (226, 170, 60), (60, 34, 26)


def paper(w, h, base, seed):
    """인쇄지: 큰 얼룩과 잔 입자를 살짝 얹는다."""
    r = np.random.default_rng(seed)
    big = np.asarray(Image.fromarray((r.random((h // 64, w // 64)) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), np.float32) / 255
    px = np.array(base, np.float32)[None, None] * (0.97 + 0.04 * big[..., None]) + r.normal(0, 1.2, (h, w, 1))
    return Image.fromarray(px.clip(0, 255).astype(np.uint8))


def crown(d, cx, cy, s, fill):
    """이름 없이 왕관만. 버거대왕 쪽 인쇄물과 같은 인상을 준다."""
    pts = [(-1, 0.55), (-1, -0.45), (-0.5, 0.05), (0, -0.65), (0.5, 0.05), (1, -0.45), (1, 0.55)]
    d.polygon([(cx + x * s, cy + y * s) for x, y in pts], fill=fill)
    for x, y in ((-1, -0.55), (0, -0.78), (1, -0.55)):
        d.ellipse((cx + x * s - s * 0.11, cy + y * s - s * 0.11, cx + x * s + s * 0.11, cy + y * s + s * 0.11), fill=fill)


def poster():
    w, h = 1024, 1464  # 0.7 x 1.0 m. 글자는 가운데 0.56 x 0.22 m 라 그 자리는 비운다
    im = paper(w, h, CREAM, 3)
    d = ImageDraw.Draw(im)
    top, bot = int(h * 0.2), int(h * 0.885)
    d.rectangle((0, 0, w, top), fill=RED)
    d.rectangle((0, top, w, top + 14), fill=GOLD)
    crown(d, w / 2, top * 0.52, 118, CREAM)
    d.rectangle((0, bot, w, h), fill=RED)
    d.rectangle((0, bot - 14, w, bot), fill=GOLD)
    for k in range(3):  # 아래쪽 띠 무늬
        x = w / 2 + (k - 1) * 150
        d.ellipse((x - 34, (bot + h) / 2 - 34, x + 34, (bot + h) / 2 + 34), fill=CREAM)
    d.rectangle((24, 24, w - 24, h - 24), outline=INK, width=4)
    im.save(os.path.join(OUT, "T_PH_Poster_Paper.png"))


poster()
